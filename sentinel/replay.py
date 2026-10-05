"""Reviewed offline publication. Never copy private run directories into a site."""

from datetime import datetime
import hashlib
import json
import math
from pathlib import Path
import re
from typing import Annotated, Literal

from pydantic import Field, model_validator

from sentinel.agent.contracts import ClosedModel, Diagnosis, Evidence, Hypothesis, Incident, InvestigationStep, ToolRequest, Usage
from sentinel.agent.runner import validate_references


NUMBER = (int, float)
WINDOW = {"start": NUMBER, "end": NUMBER}
METRIC = {
    "query": str, "warnings": [str], "series_count": int,
    "values": [{"labels": {"status_code": str, "service_name": str}, "timestamp": NUMBER, "value": NUMBER}],
    "omitted_series": int, "interpretation": str,
}
SUMMARIES = {
    "inventory": {"services": [str]},
    "metric": {"service": str, "window": WINDOW, "calls": METRIC, "p95_duration_ms": METRIC,
               "minimum_counter_samples": METRIC, "interpretation": str},
    "log": {
        "service": str, "window": WINDOW, "matched_count": int, "matched_count_relation": str,
        "returned_count": int, "sample_complete": bool, "omitted_groups": int,
        "record_examples_per_group": int,
        "groups": [{"severity": (str, type(None)), "message_excerpt": str, "message_truncated": bool,
                    "message_sha256": str, "sample_count": int, "first_seen": NUMBER, "last_seen": NUMBER,
                    "records": [{"timestamp": NUMBER, "trace_id": (str, type(None))}]}],
    },
    "trace": {
        "service": str, "window": WINDOW, "limit": int, "limit_reached": bool,
        "trace_count": int, "omitted_traces": int,
        "traces": [{"trace_id": str, "start_time": NUMBER, "observed_duration_ms": NUMBER,
                    "span_count": int, "error_span_count": int, "services": [str],
                    "root_span_ids": [str], "unresolved_parent_count": int,
                    "omitted_span_count": int, "warnings": [str],
                    "spans": [{"span_id": str, "service": str, "operation": str, "start_time": NUMBER,
                               "duration_ms": NUMBER, "is_error": bool,
                               "references": [{"kind": str, "trace_id": str, "span_id": str}],
                               "attributes": {"rpc.method": str, "span.kind": str, "error": (bool, str),
                                              "otel.status_code": (int, str), "otel.status_description": str,
                                              "http.status_code": (int, str), "rpc.response.status_code": str}}]}],
    },
    "source_code": {
        "service": str, "commit": str, "limitation": str,
        "files": [{"file": str, "sha256": str, "excerpt": str, "total_lines": int,
                   "selected_lines": int, "complete": bool, "excerpt_truncated": bool}],
    },
    "configuration": {"observed_at": NUMBER, "limitation": str,
                      "flags": [{"name": str, "state": str, "default_variant": str, "has_targeting": bool,
                                 "variants": {key: NUMBER for key in ("off", "10%", "25%", "50%", "75%", "90%", "100%")}}]},
}
SOURCE_FILES = {"src/payment/charge.js", "src/payment/index.js"}
SECRET = re.compile(
    r"sk-(?:proj-)?[A-Za-z0-9_-]{20,}|gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}"
    r"|AKIA[A-Z0-9]{16}|-----BEGIN [A-Z ]*PRIVATE KEY-----|Bearer\s+[A-Za-z0-9_.-]{20,}"
    r"|eyJ[A-Za-z0-9_-]{15,}\.[A-Za-z0-9_-]{15,}\.[A-Za-z0-9_-]{15,}"
    r"|/Users/|/home/",
)


def project(value, shape):
    """Keep only explicitly selected fields, including at nested trust boundaries."""
    if isinstance(shape, dict):
        if not isinstance(value, dict):
            raise ValueError("Public record has an invalid object")
        return {key: project(value[key], nested) for key, nested in shape.items() if key in value}
    if isinstance(shape, list):
        if not isinstance(value, list) or len(value) > 80:
            raise ValueError("Public record has an invalid or unbounded list")
        return [project(item, shape[0]) for item in value]
    types = shape if isinstance(shape, tuple) else (shape,)
    if type(value) not in types or isinstance(value, float) and not math.isfinite(value):
        raise ValueError("Public record has an invalid scalar")
    if isinstance(value, str) and len(value) > 12_000:
        raise ValueError("Public record text exceeds its bound")
    return value


def public_summary(kind: str, summary: dict) -> dict:
    if kind not in SUMMARIES:
        raise ValueError("Evidence kind needs an explicit publication schema")
    if kind == "configuration":
        summary = {**summary, "flags": [flag for flag in summary.get("flags", []) if flag["name"] == "paymentFailure"]}
    result = project(summary, SUMMARIES[kind])
    if kind == "source_code":
        if not re.fullmatch(r"[a-f0-9]{40}", result.get("commit", "")):
            raise ValueError("Public source requires a pinned commit")
        if any(file["file"] not in SOURCE_FILES for file in result.get("files", [])):
            raise ValueError("Public source is outside the payment demo allowlist")
    return result


class Observation(ClosedModel):
    estimated_server_error_calls: float | None
    selected_service_error_spans: int = Field(ge=0)
    sampled_log_groups: int = Field(ge=0)
    sampled_warning_or_error_logs: int = Field(ge=0)
    all_reads_succeeded: bool


class PublicEvidence(ClosedModel):
    id: str = Field(pattern=r"^ev_\d{3}$")
    kind: str
    source: str
    observed_at: float
    tool: ToolRequest
    success: bool
    summary: dict
    payload_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    latency_ms: float = Field(ge=0)


class PublicStep(ClosedModel):
    number: int = Field(ge=0)
    action: Literal["read", "diagnose"]
    reason: str
    evidence_id: str | None
    model_call: int | None
    at_ms: float = Field(ge=0)
    hypotheses: list[Hypothesis]
    usage: Usage | None
    model_latency_ms: float | None


class PublicDiagnosis(Diagnosis):
    requires_human_approval: bool
    requires_human_review: bool
    remediation_execution_available: bool
    remediation_executed: bool


class Review(ClosedModel):
    run_id: str
    acknowledged_on: str
    checkpoint_acknowledged: bool
    causal_review: Literal["accepted"]
    expected_cause: str
    note: str
    limitations: list[str]
    source_hashes: dict[str, Annotated[str, Field(pattern=r"^[a-f0-9]{64}$")]]


class PublicBudget(ClosedModel):
    max_model_calls: int
    max_tool_calls: int
    max_total_tokens: int
    max_context_bytes: int
    max_response_bytes: int
    max_seconds: float


class Replay(ClosedModel):
    schema_version: int
    run_id: str
    recorded_at: str
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
    incident: Incident
    budget: PublicBudget
    diagnosis: PublicDiagnosis
    evidence: list[PublicEvidence]
    steps: list[PublicStep]
    baseline: Observation
    recovery: Observation
    injected_at: float
    reset_at: float
    remediation_executed_by_agent: bool
    cleanup_performed_by_developer_exercise: bool
    review: Review

    @model_validator(mode="after")
    def publication_policy(self):
        if self.schema_version != 1 or self.review.run_id != self.run_id:
            raise ValueError("Public replay version or reviewed identity is invalid")
        if not self.review.checkpoint_acknowledged or self.review.causal_review != "accepted":
            raise ValueError("Public replay requires checkpoint acknowledgment and causal review")
        if self.remediation_executed_by_agent or self.diagnosis.remediation_executed or self.diagnosis.remediation_execution_available:
            raise ValueError("This viewer publishes recommendations only")
        ids = [e.id for e in self.evidence]
        if len(set(ids)) != len(ids) or len(ids) != self.tool_calls:
            raise ValueError("Evidence identities/counts are inconsistent")
        successful = {e.id for e in self.evidence if e.success}
        if any(id not in successful for id in self.diagnosis.evidence_ids):
            raise ValueError("Diagnosis cites unavailable evidence")
        seen = set()
        for step in self.steps:
            for hypothesis in step.hypotheses:
                if any(id not in seen for id in hypothesis.supporting_evidence + hypothesis.contradicting_evidence):
                    raise ValueError("Replay hypothesis cites future evidence")
            if step.evidence_id:
                if step.evidence_id not in successful or step.evidence_id in seen:
                    raise ValueError("Replay step has invalid evidence")
                seen.add(step.evidence_id)
        if seen != successful:
            raise ValueError("Replay does not account for every successful read")
        model_steps = [s for s in self.steps if s.model_call is not None]
        if ([s.model_call for s in model_steps] != list(range(1, self.model_calls + 1))
                or any(s.usage is None for s in model_steps)
                or sum(s.usage.input_tokens for s in model_steps) != self.input_tokens
                or sum(s.usage.output_tokens for s in model_steps) != self.output_tokens
                or sum(s.usage.cached_input_tokens for s in model_steps) != self.cached_input_tokens):
            raise ValueError("Public run usage/counts are inconsistent")
        if (self.model_calls > self.budget.max_model_calls or self.tool_calls > self.budget.max_tool_calls
                or self.input_tokens + self.output_tokens > self.budget.max_total_tokens):
            raise ValueError("Published diagnosis exceeds its recorded budget")
        for e in self.evidence:
            if public_summary(e.kind, e.summary) != e.summary:
                raise ValueError("Public evidence contains an unselected field")
        body = json.dumps(self.model_dump(), allow_nan=False)
        if len(body.encode()) > 300_000 or SECRET.search(body):
            raise ValueError("Public replay exceeds its bound or contains private data")
        return self


class Records:
    def __init__(self, root: Path):
        self.root = root.resolve()
        self.hashes = {}
        self.cache = {}

    def read(self, name: str) -> bytes:
        if name not in self.cache:
            path = (self.root / name).resolve()
            if not path.is_relative_to(self.root) or not path.is_file() or path.stat().st_size > 512_000:
                raise ValueError("Missing, out-of-scope, or unbounded run record")
            body = path.read_bytes()
            self.hashes[name] = hashlib.sha256(body).hexdigest()
            self.cache[name] = body
        return self.cache[name]

    def json(self, name: str):
        return json.loads(self.read(name), parse_constant=reject_nonfinite)

    def lines(self, name: str):
        return [json.loads(line, parse_constant=reject_nonfinite) for line in self.read(name).splitlines() if line.strip()]


def reject_nonfinite(value):
    raise ValueError("Non-finite record")


def replay_records(run: Path, exercise: Path) -> tuple[Records, list, list, dict]:
    records = Records(run)
    result = records.json("result.json")
    if result.get("status") != "diagnosed" or result.get("diagnosis") is None:
        raise ValueError("Failed or inconclusive investigations cannot be published as diagnoses")
    records.json("input.json")
    events, audit = records.lines("events.jsonl"), records.lines("tools.jsonl")
    for e in events:
        if e["event"] == "evidence":
            records.read(e["payload_file"])
    for number in range(1, result["model_calls"] + 1):
        records.json(f"decision-{number:02d}.json")
    exercise_records = Records(exercise)
    report = exercise_records.json("exercise-report.json")
    if exercise_records.json("agent-result.json") != result:
        raise ValueError("Exercise belongs to a different investigation")
    records.hashes.update({"exercise-" + key: value for key, value in exercise_records.hashes.items()})
    return records, events, audit, report


def build_replay(run: Path, exercise: Path, review: dict) -> dict:
    review = Review.model_validate(review)
    records, events, audit, report = replay_records(run, exercise)
    result, input = records.json("result.json"), records.json("input.json")
    if review.source_hashes != records.hashes:
        raise ValueError("Records differ from the causally reviewed snapshot")
    if Path(report["agent_result"]).name != "agent-result.json":
        raise ValueError("Invalid exercise association")
    started = datetime.fromisoformat(events[0]["timestamp"])
    evidence, public, steps, pending, finished = [], [], [], None, {}
    audit_results = [entry for entry in audit if entry["event"] == "tool_finished"]
    for event in events:
        if event["run_id"] != result["run_id"]:
            raise ValueError("Event belongs to a different investigation")
        kind = event["event"]
        at_ms = (datetime.fromisoformat(event["timestamp"]) - started).total_seconds() * 1000
        if kind == "model_finished":
            if not event["success"]:
                raise ValueError("Failed model event in a diagnosed record")
            finished[event["call"]] = event
            step = InvestigationStep.model_validate(records.json(f"decision-{event['call']:02d}.json"))
            validate_references(step, evidence)
            pending = (step, event)
            if step.action == "diagnose":
                diagnosis = result["diagnosis"]
                if step.diagnosis.model_dump() != {key: diagnosis[key] for key in Diagnosis.model_fields}:
                    raise ValueError("Final diagnosis differs from the recorded decision")
                steps.append({"number": len(steps), "action": "diagnose", "reason": step.reason,
                              "evidence_id": None, "model_call": event["call"], "at_ms": at_ms,
                              "hypotheses": [h.model_dump() for h in step.hypotheses], "usage": event["usage"],
                              "model_latency_ms": event["latency_ms"]})
        elif kind == "evidence":
            e = Evidence.model_validate({key: event[key] for key in Evidence.model_fields})
            if not e.success:
                raise ValueError("This reviewed replay requires successful evidence reads")
            if pending and pending[0].tool != e.tool:
                raise ValueError("Decision and executed read differ")
            position = len(evidence)
            audit_entry = audit_results[position]
            if audit_entry["tool"] != e.tool.name or not audit_entry["success"]:
                raise ValueError("Tool audit differs from evidence")
            public.append({**e.model_dump(include={"id", "kind", "source", "observed_at", "tool", "success"}),
                           "summary": public_summary(e.kind, e.summary), "latency_ms": audit_entry["latency_ms"],
                           "payload_sha256": records.hashes[e.payload_file]})
            step, model = pending if pending else (None, None)
            steps.append({"number": len(steps), "action": "read", "evidence_id": e.id, "at_ms": at_ms,
                          "model_call": model["call"] if model else None,
                          "reason": step.reason if step else "Discover the real traced inventory before choosing diagnostic reads.",
                          "hypotheses": [h.model_dump() for h in step.hypotheses] if step else [],
                          "usage": model["usage"] if model else None,
                          "model_latency_ms": model["latency_ms"] if model else None})
            evidence.append(e)
            pending = None
    usage = [event["usage"] for event in finished.values()]
    if (len(finished) != result["model_calls"] or len(audit_results) != result["tool_calls"]
            or sum(u["input_tokens"] for u in usage) != result["input_tokens"]
            or sum(u["output_tokens"] for u in usage) != result["output_tokens"]):
        raise ValueError("Reported run usage/counts differ from the audit")
    fields = {key: result[key] for key in ("run_id", "model", "billing_mode", "model_calls", "tool_calls",
              "input_tokens", "output_tokens", "cached_input_tokens", "approximate_api_cost_usd", "usage_unknown",
              "latency_ms", "diagnosis")}
    payload = {**fields, "schema_version": 1, "recorded_at": started.isoformat(),
               "incident": input["incident"], "budget": project(input["budget"], {
                   "max_model_calls": int, "max_tool_calls": int, "max_total_tokens": int,
                   "max_context_bytes": int, "max_response_bytes": int, "max_seconds": NUMBER}),
               "evidence": public, "steps": steps, "review": review.model_dump(),
               **{key: report[key] for key in ("baseline", "recovery", "injected_at", "reset_at",
                     "remediation_executed_by_agent", "cleanup_performed_by_developer_exercise")}}
    return Replay.model_validate(payload).model_dump()
