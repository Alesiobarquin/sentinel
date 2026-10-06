"""Explicit read -> evidence -> hypothesis loop with application-side policy."""

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import json
from pathlib import Path
import time
from uuid import uuid4

from pydantic import ValidationError
from opentelemetry.trace import Status, StatusCode

from sentinel.agent.context import ContextLimit, INSTRUCTIONS, build_context, encoded_size
from sentinel.agent.contracts import Budget, Evidence, Incident, InvestigationResponse, InvestigationStep, ToolRequest, Usage
from sentinel.agent.provider import ModelError, ModelProvider, api_cost
from sentinel.observability import tracing
from sentinel.tools.audit import ToolRecorder
from sentinel.tools.http import TelemetryError


class DecisionError(ValueError):
    pass


@dataclass
class RunResult:
    run_id: str
    status: str
    reason: str
    diagnosis: dict | None
    model: str
    billing_mode: str
    model_calls: int
    tool_calls: int
    input_tokens: int
    output_tokens: int
    cached_input_tokens: int
    approximate_api_cost_usd: float | None
    usage_unknown: bool
    latency_ms: float
    evidence_ids: list[str]
    directory: str


def validate_references(step: InvestigationStep, evidence: list[Evidence]) -> None:
    available = {e.id: e for e in evidence if e.success}
    for hypothesis in step.hypotheses:
        ids = hypothesis.supporting_evidence + hypothesis.contradicting_evidence
        if any(item not in available for item in ids):
            raise DecisionError("Hypothesis cites unavailable or failed evidence")
        if set(hypothesis.supporting_evidence) & set(hypothesis.contradicting_evidence):
            raise DecisionError("The same evidence cannot support and contradict one hypothesis")
    if step.diagnosis:
        ids = step.diagnosis.evidence_ids
        if any(item not in available for item in ids):
            raise DecisionError("Diagnosis cites unavailable or failed evidence")
        kinds = {available[item].kind for item in ids}
        if len(kinds) < 2 or not kinds & {"metric", "trace", "log"}:
            raise DecisionError("Diagnosis requires at least two evidence kinds including real telemetry")


class InvestigationRunner:
    def __init__(self, provider: ModelProvider, tools, *, budget: Budget | None = None,
                 output_root: Path = Path("var/investigations"), otlp_endpoint: str | None = None,
                 clock=time.monotonic, context_strategy: str = "structured"):
        if context_strategy not in {"structured", "chronological_raw"}:
            raise ValueError("Unknown context strategy")
        self.context_strategy, self.context_payloads = context_strategy, {}
        self.provider, self.tools = provider, tools
        self.budget = budget or Budget()
        self.clock = clock
        self.run_id = str(uuid4())
        self.directory = output_root / self.run_id
        self.directory.mkdir(parents=True, mode=0o700, exist_ok=False)
        self.recorder = ToolRecorder(self.directory / "tools.jsonl")
        self.trace_provider = tracing(self.directory / "spans.jsonl", otlp_endpoint)
        self.tracer = self.trace_provider.get_tracer("sentinel.investigation")
        self.evidence, self.hypotheses, self.attempted = [], [], set()
        self.model_calls = self.tool_calls = self.input_tokens = self.output_tokens = self.cached_tokens = 0
        self.cost = 0.0 if provider.billing_mode == "api" else None
        self.usage_unknown = False

    def event(self, event: str, **fields):
        with (self.directory / "events.jsonl").open("a") as stream:
            stream.write(json.dumps({"event": event, "run_id": self.run_id,
                                     "timestamp": datetime.now(timezone.utc).isoformat(), **fields}, allow_nan=False) + "\n")

    def save(self, filename: str, payload: dict):
        with (self.directory / filename).open("w") as stream:
            json.dump(payload, stream, indent=2, allow_nan=False)

    def read(self, request: ToolRequest) -> Evidence:
        key = json.dumps(request.model_dump(), sort_keys=True)
        if key in self.attempted:
            raise DecisionError("Repeated diagnostic request; no retry was performed")
        try:
            self.tools.validate(request)
        except ValueError as exc:
            self.event("policy_denied", request=request.model_dump(), reason="Service or tool scope is outside the read-only policy")
            raise DecisionError("Diagnostic request denied by application policy") from exc
        self.attempted.add(key)
        self.tool_calls += 1
        evidence_id = f"ev_{len(self.evidence) + 1:03d}"
        payload_file = evidence_id + ".json"
        with self.tracer.start_as_current_span("sentinel.tool", attributes={"tool.name": request.name}) as span:
            try:
                kind, source, raw, summary = self.recorder.invoke(
                    request.name, {"run_id": self.run_id, **request.model_dump()},
                    lambda: self.tools.execute(request), lambda r: {"kind": r[0], "source": r[1], "evidence_id": evidence_id},
                )
                self.save(payload_file, raw)
                self.context_payloads[evidence_id] = raw
                success = True
            except (TelemetryError, OSError, ValueError) as exc:
                # Error type is safe; arbitrary response bodies and credentials
                # are never copied into model context or audit messages.
                kind, source, success = "tool_failure", "sentinel", False
                summary = {"error_type": type(exc).__name__, "meaning": "This read failed; application health is unknown."}
                if isinstance(exc, TelemetryError):
                    summary["error_message"] = str(exc)[:1000]
                self.save(payload_file, summary)
                self.context_payloads[evidence_id] = summary
                span.set_status(Status(StatusCode.ERROR, "Diagnostic read failed"))
            evidence = Evidence(id=evidence_id, run_id=self.run_id, kind=kind, source=source,
                                observed_at=time.time(), tool=request, success=success, summary=summary, payload_file=payload_file)
            self.evidence.append(evidence)
            self.event("evidence", **evidence.model_dump(exclude={"run_id"}))
            span.set_attribute("evidence.id", evidence_id)
            span.set_attribute("tool.success", success)
            return evidence

    def run(self, incident: Incident) -> RunResult:
        started = self.clock()
        status, reason, diagnosis = "failed", "Investigation did not finish", None
        self.save("input.json", {"incident": incident.model_dump(), "budget": self.budget.model_dump(),
                                 "model": self.provider.model, "billing_mode": self.provider.billing_mode,
                                 "context_strategy": self.context_strategy})
        self.event("run_started", model=self.provider.model, billing_mode=self.provider.billing_mode)
        try:
            with self.tracer.start_as_current_span("sentinel.investigation", attributes={
                "run.id": self.run_id, "incident.service": incident.service, "gen_ai.request.model": self.provider.model,
                "investigation.billing_mode": self.provider.billing_mode,
            }) as root_span:
                self.read(ToolRequest(name="services", service=None, period=None))
                while True:
                    elapsed = self.clock() - started
                    if elapsed >= self.budget.max_seconds or self.model_calls >= self.budget.max_model_calls:
                        status, reason = "budget_exhausted", "Wall-time or model-call budget reached"
                        break
                    total_tokens = self.input_tokens + self.output_tokens
                    if total_tokens >= self.budget.max_total_tokens:
                        status, reason = "budget_exhausted", "Reported total-token budget reached"
                        break
                    with self.tracer.start_as_current_span("sentinel.context"):
                        context = build_context(incident, self.evidence, self.hypotheses,
                                                max_bytes=self.budget.max_context_bytes,
                                                strategy=self.context_strategy, payloads=self.context_payloads,
                                                remaining={"model_calls": self.budget.max_model_calls - self.model_calls,
                                                           "tool_calls": self.budget.max_tool_calls - self.tool_calls,
                                                           "total_tokens": self.budget.max_total_tokens - total_tokens})
                    if self.provider.billing_mode == "api":
                        # UTF-8 byte count plus schema/envelope headroom is a
                        # conservative admission estimate, not measured usage.
                        estimated_input = encoded_size(context) + len(INSTRUCTIONS.encode()) + len(json.dumps(InvestigationResponse.model_json_schema()).encode()) + 1024
                        reserved = api_cost(self.provider.model, Usage(input_tokens=estimated_input, output_tokens=self.budget.max_output_tokens))
                        if self.cost + reserved > self.budget.max_api_cost_usd:
                            status, reason = "budget_exhausted", "API cost reservation exceeds the configured cap"
                            break
                    self.model_calls += 1
                    self.save(f"context-{self.model_calls:02d}.json", context)
                    self.event("model_started", call=self.model_calls, context_bytes=encoded_size(context))
                    with self.tracer.start_as_current_span("sentinel.model") as model_span:
                        try:
                            reply = self.provider.step(INSTRUCTIONS, context, self.budget,
                                                       timeout=min(30, self.budget.max_seconds - elapsed))
                        except ModelError as exc:
                            if exc.response is not None:
                                self.save(f"response-{self.model_calls:02d}.json", exc.response)
                            if exc.usage is None:
                                self.usage_unknown = True
                            else:
                                self.input_tokens += exc.usage.input_tokens
                                self.output_tokens += exc.usage.output_tokens
                                self.cached_tokens += exc.usage.cached_input_tokens
                                if self.cost is not None:
                                    self.cost += api_cost(self.provider.model, exc.usage)
                            model_span.set_status(Status(StatusCode.ERROR, "Model request failed"))
                            self.event("model_finished", call=self.model_calls, success=False, usage_unknown=exc.usage is None,
                                       usage=exc.usage.model_dump() if exc.usage else None, response_id=exc.response_id)
                            raise
                        self.input_tokens += reply.usage.input_tokens
                        self.output_tokens += reply.usage.output_tokens
                        self.cached_tokens += reply.usage.cached_input_tokens
                        if self.cost is not None:
                            self.cost += api_cost(self.provider.model, reply.usage)
                        self.save(f"decision-{self.model_calls:02d}.json", reply.decision)
                        if reply.response is not None:
                            self.save(f"response-{self.model_calls:02d}.json", reply.response)
                        self.event("model_finished", call=self.model_calls, success=True, response_id=reply.response_id,
                                   model=reply.model, latency_ms=reply.latency_ms, usage=reply.usage.model_dump())
                        model_span.set_attribute("gen_ai.usage.input_tokens", reply.usage.input_tokens)
                        model_span.set_attribute("gen_ai.usage.output_tokens", reply.usage.output_tokens)
                        model_span.set_attribute("gen_ai.response.id", reply.response_id)
                        step = InvestigationStep.model_validate(reply.decision)
                        validate_references(step, self.evidence)
                    self.hypotheses = step.hypotheses
                    self.event("hypotheses_updated", hypotheses=[h.model_dump() for h in self.hypotheses])
                    # The subscription preview can exceed a local per-response
                    # budget. Do not execute its decision when this happens.
                    if (self.input_tokens + self.output_tokens > self.budget.max_total_tokens
                            or self.cost is not None and self.cost > self.budget.max_api_cost_usd):
                        status, reason = "budget_exhausted", "Reported model usage exceeded the run limit"
                        break
                    if self.clock() - started >= self.budget.max_seconds:
                        status, reason = "budget_exhausted", "Wall-time budget reached after the model response"
                        break
                    if step.action == "diagnose":
                        diagnosis = step.diagnosis.model_dump()
                        diagnosis["requires_human_approval"] = step.diagnosis.remediation_kind not in {"inspect", "escalate"}
                        diagnosis["requires_human_review"] = True
                        diagnosis["remediation_execution_available"] = False
                        diagnosis["remediation_executed"] = False
                        status, reason = "diagnosed", step.reason
                        break
                    if step.action == "insufficient_evidence":
                        status, reason = "insufficient_evidence", step.reason
                        break
                    if self.tool_calls >= self.budget.max_tool_calls:
                        status, reason = "budget_exhausted", "Diagnostic tool-call budget reached"
                        break
                    if self.clock() - started >= self.budget.max_seconds:
                        status, reason = "budget_exhausted", "Wall-time budget reached before the next diagnostic read"
                        break
                    self.read(step.tool)
                root_span.set_attribute("investigation.outcome", status)
                root_span.set_attribute("investigation.tool_calls", self.tool_calls)
                root_span.set_attribute("investigation.model_calls", self.model_calls)
                root_span.set_attribute("gen_ai.usage.input_tokens", self.input_tokens)
                root_span.set_attribute("gen_ai.usage.output_tokens", self.output_tokens)
        except (ValidationError, DecisionError, ContextLimit, ModelError) as exc:
            # Pydantic errors echo untrusted inputs; persist a safe reason only.
            status, reason = "failed", f"{type(exc).__name__}: invalid decision, context, or model response; inspect the local run artifacts"
            self.event("run_error", error_type=type(exc).__name__)
        except Exception as exc:
            status, reason = "failed", f"{type(exc).__name__}: unexpected investigation failure; inspect local artifacts"
            self.event("run_error", error_type=type(exc).__name__)
        finally:
            self.trace_provider.shutdown()
        result = RunResult(self.run_id, status, reason, diagnosis, self.provider.model, self.provider.billing_mode,
                           self.model_calls, self.tool_calls, self.input_tokens, self.output_tokens, self.cached_tokens,
                           round(self.cost, 8) if self.cost is not None else None, self.usage_unknown,
                           round((self.clock() - started) * 1000, 3), [e.id for e in self.evidence], str(self.directory))
        self.save("result.json", asdict(result))
        self.event("run_finished", status=status, reason=reason)
        return result
