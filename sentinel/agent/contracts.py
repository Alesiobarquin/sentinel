"""Closed contracts at the incident, tool, and model trust boundaries."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from sentinel.tools.common import TimeWindow


class ClosedModel(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, allow_inf_nan=False)


class Incident(ClosedModel):
    service: str = Field(pattern=r"^[a-zA-Z0-9][a-zA-Z0-9_.-]{0,63}$")
    symptom: str = Field(min_length=1, max_length=1500)
    start: float
    end: float
    baseline_start: float | None = None
    baseline_end: float | None = None

    @model_validator(mode="after")
    def validate_window(self):
        TimeWindow(self.start, self.end)
        if (self.baseline_start is None) != (self.baseline_end is None):
            raise ValueError("Provide both baseline boundaries or neither")
        if self.baseline_start is not None:
            TimeWindow(self.baseline_start, self.baseline_end)
            if self.baseline_end > self.start:
                raise ValueError("Baseline must end at or before the incident starts")
        elif self.start < self.end - self.start:
            raise ValueError("An equally sized preceding baseline window is required")
        return self

    def window(self, period: str) -> TimeWindow:
        if period == "incident":
            return TimeWindow(self.start, self.end)
        if self.baseline_start is not None:
            return TimeWindow(self.baseline_start, self.baseline_end)
        return TimeWindow(2 * self.start - self.end, self.start)


ToolName = Literal["services", "latency_ranking", "metrics", "logs", "traces", "dependencies",
                   "runtime_configuration", "source", "pods"]


def tool_schema(schema: dict) -> None:
    # Python validators do not automatically appear in JSON Schema. Expose the
    # same argument families to strict model output without weakening validation.
    families = [(["services", "runtime_configuration"], False, False),
                (["latency_ranking", "dependencies"], False, True),
                (["metrics", "logs", "traces"], True, True),
                (["source", "pods"], True, False)]
    schema["anyOf"] = [{
        "type": "object", "additionalProperties": False,
        "properties": {
            "name": {"type": "string", "enum": names},
            "service": {"type": "string"} if scoped else {"type": "null"},
            "period": {"type": "string", "enum": ["incident", "baseline"]} if timed else {"type": "null"},
        },
        "required": ["name", "service", "period"],
    } for names, scoped, timed in families]


class ToolRequest(ClosedModel):
    model_config = ConfigDict(json_schema_extra=tool_schema)
    name: ToolName
    service: str | None
    period: Literal["incident", "baseline"] | None

    @model_validator(mode="after")
    def shape(self):
        scoped = self.name in {"metrics", "logs", "traces", "source", "pods"}
        timed = self.name in {"latency_ranking", "metrics", "logs", "traces", "dependencies"}
        if scoped != (self.service is not None) or timed != (self.period is not None):
            raise ValueError("Tool requires service and period only where its contract specifies them")
        return self


class Hypothesis(ClosedModel):
    name: str = Field(min_length=1, max_length=200)
    explanation: str = Field(min_length=1, max_length=600)
    confidence: float = Field(ge=0, le=1, description="Ranking indicator, not calibrated probability")
    supporting_evidence: list[str] = Field(max_length=8)
    contradicting_evidence: list[str] = Field(max_length=8)
    status: Literal["active", "supported", "rejected"]


class Diagnosis(ClosedModel):
    root_cause: str = Field(min_length=1, max_length=1200)
    confidence: float = Field(ge=0, le=1)
    evidence_ids: list[str] = Field(min_length=2, max_length=10)
    affected_services: list[str] = Field(min_length=1, max_length=10)
    recommended_remediation: str = Field(min_length=1, max_length=1200)
    remediation_kind: Literal["inspect", "request_config_revert", "request_restart", "request_rollback", "escalate"]
    limitations: list[str] = Field(min_length=1, max_length=6)


class InvestigationStep(ClosedModel):
    action: Literal["read", "diagnose", "insufficient_evidence"]
    reason: str = Field(min_length=1, max_length=600)
    hypotheses: list[Hypothesis] = Field(min_length=1, max_length=4)
    tool: ToolRequest | None
    diagnosis: Diagnosis | None

    @model_validator(mode="after")
    def action_shape(self):
        if (self.action == "read") != (self.tool is not None):
            raise ValueError("Only a read decision can contain a tool request")
        if (self.action == "diagnose") != (self.diagnosis is not None):
            raise ValueError("Only a diagnosis decision can contain a diagnosis")
        return self


class ReadStep(InvestigationStep):
    action: Literal["read"]
    tool: ToolRequest
    diagnosis: None


class DiagnoseStep(InvestigationStep):
    action: Literal["diagnose"]
    tool: None
    diagnosis: Diagnosis


class AbstainStep(InvestigationStep):
    action: Literal["insufficient_evidence"]
    tool: None
    diagnosis: None


class InvestigationResponse(ClosedModel):
    # Nested unions are supported by strict function schemas; a root anyOf
    # is not. These variants expose the same action constraints as Python.
    step: ReadStep | DiagnoseStep | AbstainStep


class Budget(ClosedModel):
    max_model_calls: int = Field(default=8, ge=1, le=12)
    max_tool_calls: int = Field(default=10, ge=1, le=16)
    max_total_tokens: int = Field(default=50_000, ge=1000, le=100_000)
    max_context_bytes: int = Field(default=32_000, ge=4000, le=64_000)
    max_response_bytes: int = Field(default=12_000, ge=1000, le=24_000)
    max_output_tokens: int = Field(default=2400, ge=256, le=4096)
    max_seconds: float = Field(default=300, ge=10, le=600)
    max_api_cost_usd: float = Field(default=1, gt=0, le=1)


class Usage(ClosedModel):
    input_tokens: int = Field(ge=0)
    output_tokens: int = Field(ge=0)
    cached_input_tokens: int = Field(default=0, ge=0)

    @model_validator(mode="after")
    def cached_bounds(self):
        if self.cached_input_tokens > self.input_tokens:
            raise ValueError("Cached input cannot exceed total input")
        return self


class Evidence(ClosedModel):
    id: str
    run_id: str
    kind: str
    source: str
    observed_at: float
    tool: ToolRequest
    success: bool
    summary: dict
    payload_file: str
