"""Native semantic tools. Models cannot choose PromQL, URLs, files, or commands."""

from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import time

from sentinel.agent.contracts import Incident, ToolRequest
from sentinel.tools.http import TelemetryError
from sentinel.tools.logs import LogSchema, OpenSearchProvider
from sentinel.tools.metrics import PrometheusProvider
from sentinel.tools.traces import JaegerProvider

TOOL_DESCRIPTIONS = {
    "services": "Discover traced service inventory; service=null, period=null.",
    "latency_ranking": "Rank server-span p95 latency in milliseconds over a fixed period; service=null.",
    "metrics": "Estimated server-span calls by status, minimum counter sample counts, and p95 duration for one service and fixed period.",
    "logs": "Group a bounded sample of recent messages with severity, IDs, trace IDs, and coverage.",
    "traces": "Read bounded distributed traces; errors first, durations, parent references, IDs, coverage.",
    "dependencies": "Aggregated trace-derived dependencies; service=null, fixed period.",
    "runtime_configuration": "Current local feature-flag defaults/variants. Not historical or proof of effective evaluation. service=null, period=null.",
    "source": "Bounded excerpts of an explicitly configured service's pinned source. period=null.",
    "pods": "Current Kubernetes pod readiness/restarts/events in a configured namespace. period=null; unavailable when unconfigured.",
}


def compact_metric(result) -> dict:
    return {
        "query": result.query, "warnings": list(result.warnings), "series_count": len(result.series),
        "values": [{"labels": s.labels, "timestamp": s.samples[-1].timestamp,
                    "value": s.samples[-1].value} for s in result.series[:30] if s.samples],
        "omitted_series": max(0, len(result.series) - 30),
    }


class DiagnosticTools:
    def __init__(self, incident: Incident, *, metrics: PrometheusProvider, traces: JaegerProvider,
                 logs: OpenSearchProvider, log_schema: LogSchema, log_index: str,
                 source_root: Path | None = None, source_files: dict[str, list[str]] | None = None,
                 source_commit: str | None = None, kubernetes=None):
        self.incident, self.metrics, self.traces, self.logs = incident, metrics, traces, logs
        self.log_schema, self.log_index = log_schema, log_index
        self.source_root, self.source_files, self.source_commit = source_root, source_files or {}, source_commit
        self.kubernetes = kubernetes
        self.allowed_services = {incident.service}

    def validate(self, request: ToolRequest) -> None:
        # Allowlist discovered inventory and the user-supplied initial service only.
        if request.service is not None and request.service not in self.allowed_services:
            raise ValueError("Requested service is outside the observed inventory")

    def execute(self, request: ToolRequest) -> tuple[str, str, dict, dict]:
        self.validate(request)
        name, service = request.name, request.service
        window = self.incident.window(request.period) if request.period else None
        if name == "services":
            services = self.traces.services()
            self.allowed_services.update(services)
            raw = {"services": list(services)}
            return "inventory", "jaeger", raw, raw
        if name in {"metrics", "latency_ranking"}:
            selector = 'span_kind="SPAN_KIND_SERVER"'
            if service:
                selector += ',service_name=' + json.dumps(service)
            seconds = max(1, int(window.end - window.start))
            duration = (f'histogram_quantile(0.95, sum by (le, service_name) '
                        f'(rate(traces_span_metrics_duration_milliseconds_bucket{{{selector}}}[{seconds}s])))')
            if name == "latency_ranking":
                query = f"topk(5, {duration})"
                result = self.metrics.query_metrics(query, at=window.end)
                raw, summary = asdict(result), compact_metric(result)
            else:
                calls = f'sum by (status_code) (increase(traces_span_metrics_calls_total{{{selector}}}[{seconds}s]))'
                samples = f'min by (status_code) (count_over_time(traces_span_metrics_calls_total{{{selector}}}[{seconds}s]))'
                count_result = self.metrics.query_metrics(calls, at=window.end)
                duration_result = self.metrics.query_metrics(duration, at=window.end)
                sample_result = self.metrics.query_metrics(samples, at=window.end)
                raw = {"calls": asdict(count_result), "p95_duration_ms": asdict(duration_result),
                       "minimum_counter_samples": asdict(sample_result)}
                coverage = compact_metric(sample_result)
                coverage["interpretation"] = (
                    "Minimum raw counter samples per underlying series, grouped by status. "
                    "These are telemetry samples, not requests. Fewer than two samples cannot "
                    "support increase/rate; absence is unknown. Two or more samples do not prove complete coverage."
                )
                summary = {"calls": compact_metric(count_result), "p95_duration_ms": compact_metric(duration_result),
                           "minimum_counter_samples": coverage}
            summary.update(window=asdict(window), service=service,
                           interpretation="Span-derived estimates; null/missing values are not zero. Export delay and extrapolation apply.")
            return "metric", "prometheus", raw, summary
        if name == "logs":
            result = self.logs.query_logs(service, window, index_pattern=self.log_index, schema=self.log_schema, limit=40)
            raw = asdict(result)
            summary = {k: raw[k] for k in ("service", "window", "matched_count", "matched_count_relation", "returned_count", "sample_complete")}
            groups = sorted(raw["groups"], key=lambda g: (str(g["severity"]).lower() not in {"warn", "warning", "error", "fatal", "critical"}, -g["sample_count"]))
            summary["groups"] = [{**g, "records": g["records"][:3]} for g in groups[:5]]
            summary["omitted_groups"] = max(0, len(groups) - 5)
            summary["record_examples_per_group"] = 3
            return "log", "opensearch", raw, summary
        if name == "traces":
            result = self.traces.query_traces(service, window, limit=6, span_limit=5)
            raw = asdict(result)
            summary = {k: raw[k] for k in ("service", "window", "limit", "limit_reached")}
            selected = sorted(raw["traces"], key=lambda t: (-t["error_span_count"], -t["observed_duration_ms"], t["trace_id"]))
            summary.update(trace_count=len(selected), traces=selected[:3], omitted_traces=max(0, len(selected) - 3))
            return "trace", "jaeger", raw, summary
        if name == "dependencies":
            result = self.traces.get_service_dependencies(window)
            raw = asdict(result)
            ranked = sorted(raw["edges"], key=lambda e: (-e["call_count"], e["caller"], e["callee"]))
            summary = {"window": asdict(window), "edges": ranked[:25], "omitted_edges": max(0, len(ranked) - 25)}
            return "dependency", "jaeger", raw, summary
        if name == "runtime_configuration":
            body = self._read_source("src/flagd/demo.flagd.json", 64_000)
            try:
                flags = json.loads(body)["flags"]
                compact = [{"name": key, "state": value.get("state"), "default_variant": value.get("defaultVariant"),
                            "variants": value.get("variants"), "has_targeting": "targeting" in value}
                           for key, value in sorted(flags.items())]
            except (ValueError, KeyError, AttributeError, TypeError) as exc:
                raise TelemetryError("Runtime flag configuration is malformed") from exc
            summary = {"observed_at": time.time(), "flags": compact,
                       "limitation": "Current mounted file snapshot; targeting/evaluation and historical activation are not established by this read."}
            return "configuration", "local_runtime", {"sha256": hashlib.sha256(body.encode()).hexdigest(), **summary}, summary
        if name == "source":
            files = self.source_files.get(service)
            if not files:
                raise TelemetryError("No source-file allowlist configured for this service")
            records = []
            for filename in files[:3]:
                body = self._read_source(filename, 64_000)
                lines = body.splitlines()
                # Generic deterministic windows around feature evaluations and
                # failure handling. No scenario label or expected answer is used.
                selected = set(range(min(12, len(lines))))
                if len(lines) <= 120:
                    selected.update(range(len(lines)))
                else:
                    primary = ("flag", "getbooleanvalue", "getnumbervalue", "get_boolean_value", "get_double_value")
                    secondary = ("throw", "exception", "sleep", "delay", "spanstatus")
                    candidates = [(i, 2 if any(word in line.lower() for word in primary) else 1)
                                  for i, line in enumerate(lines) if any(word in line.lower() for word in (*primary, *secondary))]
                    for i, _ in sorted(candidates, key=lambda pair: (-pair[1], pair[0])):
                        window = set(range(max(0, i - 8), min(len(lines), i + 9)))
                        if len(selected | window) <= 140:
                            selected.update(window)
                excerpt = "\n".join(f"{i + 1}: {lines[i]}" for i in sorted(selected))
                records.append({"file": filename, "sha256": hashlib.sha256(body.encode()).hexdigest(),
                                "excerpt": excerpt[:9000], "total_lines": len(lines),
                                "selected_lines": len(selected), "complete": len(selected) == len(lines) and len(excerpt) <= 9000,
                                "excerpt_truncated": len(excerpt) > 9000})
            summary = {"service": service, "commit": self.source_commit, "files": records,
                       "limitation": "Pinned local source snapshot; not proof of the deployed image contents or current runtime execution."}
            return "source_code", "opentelemetry_demo", summary, summary
        if name == "pods":
            if self.kubernetes is None:
                raise TelemetryError("Kubernetes is not configured for this Compose investigation")
            result = self.kubernetes.pods(service)
            return "kubernetes", "kubernetes", result, result
        raise ValueError("Unknown diagnostic tool")

    def _read_source(self, relative: str, limit: int) -> str:
        if self.source_root is None:
            raise TelemetryError("Local source context is not configured")
        root = self.source_root.resolve()
        path = (root / relative).resolve()
        if not path.is_relative_to(root) or not path.is_file():
            raise TelemetryError("Configured source file is outside the pinned source root or missing")
        with path.open(encoding="utf-8") as stream:
            body = stream.read(limit + 1)
        if len(body.encode()) > limit:
            raise TelemetryError("Source file exceeds the bounded read limit")
        return body
