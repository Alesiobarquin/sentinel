"""Isolated Jaeger UI JSON compatibility adapter, with explicit time units."""

from dataclasses import dataclass
import math
import re
from typing import Protocol

from sentinel.tools.common import TimeWindow, validate_limit, validate_service
from sentinel.tools.http import JsonHttpClient, TelemetryError

ATTRIBUTES = frozenset({
    "error", "error.message", "otel.status_code", "otel.status_description",
    "rpc.grpc.status_code", "rpc.response.status_code", "rpc.method",
    "http.status_code", "http.response.status_code", "db.system", "db.system.name",
    "server.address",
    "span.kind",
})


@dataclass(frozen=True)
class SpanReference:
    kind: str
    trace_id: str
    span_id: str


@dataclass(frozen=True)
class SpanSummary:
    span_id: str
    service: str
    operation: str
    start_time: float
    duration_ms: float
    is_error: bool
    references: tuple[SpanReference, ...]
    attributes: dict


@dataclass(frozen=True)
class TraceSummary:
    trace_id: str
    start_time: float
    observed_duration_ms: float
    span_count: int
    error_span_count: int
    services: tuple[str, ...]
    root_span_ids: tuple[str, ...]
    unresolved_parent_count: int
    spans: tuple[SpanSummary, ...]
    omitted_span_count: int
    warnings: tuple[str, ...]


@dataclass(frozen=True)
class TraceQueryResult:
    source: str
    service: str
    window: TimeWindow
    limit: int
    limit_reached: bool
    traces: tuple[TraceSummary, ...]


@dataclass(frozen=True)
class DependencyEdge:
    caller: str
    callee: str
    call_count: int


@dataclass(frozen=True)
class DependencyResult:
    source: str
    window: TimeWindow
    edges: tuple[DependencyEdge, ...]


class TraceProvider(Protocol):
    def services(self) -> tuple[str, ...]: ...

    def query_traces(
        self, service: str, window: TimeWindow, *, limit: int = 10,
        min_duration_ms: float = 0, span_limit: int = 5,
    ) -> TraceQueryResult: ...

    def get_service_dependencies(self, window: TimeWindow) -> DependencyResult: ...


def _identifier(value, *, trace: bool = False) -> str:
    pattern = r"(?:[0-9a-fA-F]{16}|[0-9a-fA-F]{32})" if trace else r"[0-9a-fA-F]{16}"
    if not isinstance(value, str) or not re.fullmatch(pattern, value) or int(value, 16) == 0:
        raise ValueError("Invalid trace/span identifier")
    return value.lower()


def _uint(value) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value < 2**64:
        raise ValueError("Invalid unsigned integer")
    return value


def _strings(value) -> tuple[str, ...]:
    if value is None:
        return ()
    if not isinstance(value, list) or not all(isinstance(s, str) for s in value):
        raise ValueError("Invalid warnings")
    return tuple(value)


def _data(payload: dict) -> list:
    errors = payload.get("errors")
    if errors is not None and not isinstance(errors, list):
        raise TelemetryError("Malformed Jaeger error status")
    if errors:
        raise TelemetryError("Jaeger reported a query error; partial results were not used")
    if not isinstance(payload.get("data"), list):
        raise TelemetryError("Malformed Jaeger response")
    return payload["data"]


def _span(item: dict, trace_id: str, processes: dict) -> SpanSummary:
    if not isinstance(item, dict):
        raise ValueError("Invalid span")
    if _identifier(item["traceID"], trace=True) != trace_id:
        raise ValueError("Span belongs to a different trace")
    span_id = _identifier(item["spanID"])
    process = item.get("process")
    if process is None:
        process = processes[item["processID"]]
    if not isinstance(process, dict):
        raise ValueError("Invalid span process")
    service = process["serviceName"]
    validate_service(service)
    operation = item["operationName"]
    if not isinstance(operation, str):
        raise ValueError("Invalid operation name")
    tags = item.get("tags")
    if tags is None:
        tags = []
    if not isinstance(tags, list):
        raise ValueError("Invalid span tags")
    attributes = {}
    for tag in tags:
        if not isinstance(tag, dict) or not isinstance(tag.get("key"), str) or "value" not in tag:
            raise ValueError("Invalid tag")
        key, value = tag["key"], tag["value"]
        if key in ATTRIBUTES:
            if not isinstance(value, (str, int, float, bool)) or isinstance(value, float) and not math.isfinite(value):
                raise ValueError("Invalid diagnostic attribute")
            # Jaeger can emit both legacy string and native boolean error tags.
            # Normalize only explicitly equivalent representations, preserving
            # rejection of actual contradictions and bool/number conflation.
            if key == "error" and type(value) is str and value in {"true", "false"}:
                value = value == "true"
            if key == "otel.status_code" and type(value) is str and value in {"UNSET", "OK", "ERROR"}:
                value = {"UNSET": 0, "OK": 1, "ERROR": 2}[value]
            if key in attributes and (type(attributes[key]) is not type(value) or attributes[key] != value):
                raise ValueError("Conflicting diagnostic attributes")
            attributes[key] = value
    raw_references = item.get("references")
    if raw_references is None:
        raw_references = []
    if not isinstance(raw_references, list):
        raise ValueError("Invalid span references")
    references = []
    for ref in raw_references:
        if not isinstance(ref, dict) or ref.get("refType") not in {"CHILD_OF", "FOLLOWS_FROM"}:
            raise ValueError("Unknown reference kind")
        references.append(SpanReference(ref["refType"], _identifier(ref["traceID"], trace=True), _identifier(ref["spanID"])))
    error = attributes.get("error") is True or attributes.get("error") == "true"
    status = attributes.get("otel.status_code")
    error = error or status == "ERROR" or type(status) is int and status == 2
    return SpanSummary(
        span_id, service, operation, _uint(item["startTime"]) / 1_000_000,
        _uint(item["duration"]) / 1000, bool(error), tuple(references), attributes,
    )


def summarize_trace(raw: dict, *, service: str, span_limit: int = 5) -> TraceSummary:
    validate_service(service)
    validate_limit(span_limit, 20)
    try:
        if not isinstance(raw, dict):
            raise ValueError("Invalid trace")
        trace_id = _identifier(raw["traceID"], trace=True)
        processes = raw["processes"]
        raw_spans = raw["spans"]
        if not isinstance(processes, dict) or not isinstance(raw_spans, list) or not raw_spans:
            raise ValueError("Trace has no valid spans/processes")
        spans = [_span(item, trace_id, processes) for item in raw_spans]
        ids = {span.span_id for span in spans}
        if len(ids) != len(spans):
            raise ValueError("Duplicate span identifiers")
        services = tuple(sorted({span.service for span in spans}))
        if service not in services:
            raise ValueError("Trace does not contain the requested service")
        roots = tuple(sorted(span.span_id for span in spans if not any(r.kind == "CHILD_OF" for r in span.references)))
        unresolved = sum(
            r.kind == "CHILD_OF" and (r.trace_id != trace_id or r.span_id not in ids)
            for span in spans for r in span.references
        )
        started_us = min(item["startTime"] for item in raw_spans)
        ended_us = max(item["startTime"] + item["duration"] for item in raw_spans)
        # Never sum overlapping span durations: this is the observed trace envelope.
        ranked = sorted(spans, key=lambda s: (
            not s.is_error, s.service != service,
            s.attributes.get("span.kind") not in {"server", "SERVER"}, -s.duration_ms, s.span_id,
        ))
        # Always retain the service being investigated, even when long upstream
        # failures would otherwise occupy every selected slot.
        primary = next(s for s in ranked if s.service == service)
        ranked = [primary, *(s for s in ranked if s.span_id != primary.span_id)]
        warnings = list(_strings(raw.get("warnings")))
        for item in raw_spans:
            warnings.extend(_strings(item.get("warnings")))
    except (KeyError, TypeError, ValueError, OverflowError) as exc:
        raise TelemetryError("Unsupported or malformed Jaeger trace") from exc
    return TraceSummary(
        trace_id, started_us / 1_000_000, (ended_us - started_us) / 1000, len(spans),
        sum(s.is_error for s in spans), services, roots, unresolved,
        tuple(ranked[:span_limit]), max(0, len(spans) - span_limit), tuple(dict.fromkeys(warnings)),
    )


class JaegerProvider:
    def __init__(self, url: str = "http://127.0.0.1:8080/jaeger/ui", *, client: JsonHttpClient | None = None):
        self.client = client or JsonHttpClient(url)

    def services(self) -> tuple[str, ...]:
        data = _data(self.client.get("/api/services"))
        try:
            for service in data:
                validate_service(service)
        except ValueError as exc:
            raise TelemetryError("Malformed Jaeger service list") from exc
        return tuple(sorted(set(data)))

    def query_traces(
        self, service: str, window: TimeWindow, *, limit: int = 10,
        min_duration_ms: float = 0, span_limit: int = 5,
    ) -> TraceQueryResult:
        validate_service(service)
        validate_limit(limit)
        validate_limit(span_limit, 20)
        if (
            isinstance(min_duration_ms, bool) or not isinstance(min_duration_ms, (int, float))
            or not math.isfinite(min_duration_ms) or not 0 <= min_duration_ms <= 21_600_000
        ):
            raise ValueError("Minimum trace duration must be finite, nonnegative, and at most six hours")
        if window.end * 1_000_000_000 > 2**63 - 1:
            raise ValueError("Trace timestamps exceed Jaeger's supported range")
        parameters = {
            "service": service, "start": math.floor(window.start * 1_000_000),
            "end": math.ceil(window.end * 1_000_000), "limit": limit,
        }
        if min_duration_ms:
            parameters["minDuration"] = f"{math.ceil(min_duration_ms * 1000)}us"
        data = _data(self.client.get("/api/traces", parameters))
        if len(data) > limit:
            raise TelemetryError("Jaeger returned more traces than the requested limit")
        traces = tuple(summarize_trace(t, service=service, span_limit=span_limit) for t in data)
        if len({trace.trace_id for trace in traces}) != len(traces):
            raise TelemetryError("Jaeger returned duplicate trace identifiers")
        if any(t.start_time > window.end or t.start_time + t.observed_duration_ms / 1000 < window.start for t in traces):
            raise TelemetryError("Jaeger returned a trace outside the requested window")
        return TraceQueryResult("jaeger", service, window, limit, len(traces) == limit, traces)

    def get_service_dependencies(self, window: TimeWindow) -> DependencyResult:
        if window.end * 1_000_000_000 > 2**63 - 1:
            raise ValueError("Dependency timestamps exceed Jaeger's supported range")
        data = _data(self.client.get("/api/dependencies", {
            "endTs": math.ceil(window.end * 1000),
            "lookback": math.ceil((window.end - window.start) * 1000),
        }))
        try:
            edges = []
            for item in data:
                validate_service(item["parent"])
                validate_service(item["child"])
                edges.append(DependencyEdge(item["parent"], item["child"], _uint(item["callCount"])))
            if len({(e.caller, e.callee) for e in edges}) != len(edges):
                raise ValueError("Duplicate dependency edges")
        except (KeyError, TypeError, ValueError) as exc:
            raise TelemetryError("Malformed Jaeger dependency graph") from exc
        return DependencyResult("jaeger", window, tuple(sorted(edges, key=lambda e: (e.caller, e.callee))))
