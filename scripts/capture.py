"""Capture real, bounded evidence for the developer-only payment lab scenario."""

import argparse
from dataclasses import asdict
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from sentinel.__main__ import load_log_schema
from sentinel.tools.audit import ToolRecorder
from sentinel.tools.common import TimeWindow
from sentinel.tools.http import TelemetryError
from sentinel.tools.logs import OpenSearchProvider
from sentinel.tools.metrics import PrometheusProvider
from sentinel.tools.traces import JaegerProvider

CALLS_QUERY = (
    'traces_span_metrics_calls_total{service_name="payment",'
    'span_kind="SPAN_KIND_SERVER",span_name="oteldemo.PaymentService/Charge"}'
)
LATENCY_QUERY = (
    'histogram_quantile(0.95,sum by(service_name,le)('
    'rate(traces_span_metrics_duration_milliseconds_bucket{span_kind="SPAN_KIND_SERVER"}[2m])))'
)


def capture(phase: str, window: TimeWindow, output: Path) -> dict:
    if output.exists():
        raise ValueError("Capture already exists; choose a new --output path")
    schema = load_log_schema(str(ROOT / "infra/docker/log-schema.json"))
    recorder = ToolRecorder(ROOT / "var/audit/tool-calls.jsonl")
    metrics, traces, logs = PrometheusProvider(), JaegerProvider(), OpenSearchProvider()
    data, errors = {}, {}

    def read(key, name, arguments, action, summary, *, structured=True):
        try:
            result = recorder.invoke(name, arguments, action, summary)
            data[key] = asdict(result) if structured else result
        except (TelemetryError, ValueError, OSError) as exc:
            # Preserve independent evidence and clearly label the failed signal.
            errors[key] = {"type": type(exc).__name__, "message": str(exc)}

    bounds = asdict(window)
    read("services", "trace_services", {}, traces.services, lambda r: {"count": len(r)}, structured=False)
    read("calls", "query_metrics", {"query": CALLS_QUERY, **bounds, "step": 15},
         lambda: metrics.query_metrics(CALLS_QUERY, start=window.start, end=window.end, step=15),
         lambda r: {"series_count": len(r.series)})
    read("p95_server_span_duration_ms", "query_metrics", {"query": LATENCY_QUERY, "at": window.end},
         lambda: metrics.query_metrics(LATENCY_QUERY, at=window.end), lambda r: {"series_count": len(r.series)})
    read("traces", "query_traces", {"service": "payment", **bounds, "limit": 10, "span_limit": 10},
         lambda: traces.query_traces("payment", window, limit=10, span_limit=10),
         lambda r: {"trace_count": len(r.traces), "limit_reached": r.limit_reached})
    read("logs", "query_logs", {"service": "payment", **bounds, "index": "otel-logs*", "schema": asdict(schema), "limit": 100},
         lambda: logs.query_logs("payment", window, index_pattern="otel-logs*", schema=schema, limit=100),
         lambda r: {"returned_count": r.returned_count, "sample_complete": r.sample_complete})
    read("dependencies", "get_service_dependencies", bounds,
         lambda: traces.get_service_dependencies(window), lambda r: {"edge_count": len(r.edges)})
    flag_path = ROOT / ".cache/demo/source/src/flagd/demo.flagd.json"
    lock = json.loads((ROOT / "infra/docker/demo.lock.json").read_text())
    payload = {
        "kind": "live_telemetry_capture", "phase": phase,
        "captured_at": datetime.now(timezone.utc).isoformat(), "window": bounds,
        "demo_version": lock["version"], "demo_commit": lock["commit"],
        "payment_failure_variant_on_disk": json.loads(flag_path.read_text())["flags"]["paymentFailure"]["defaultVariant"],
        "complete": not errors, "errors": errors, "data": data,
        "coverage_notes": [
            "Trace and log results are bounded samples, not complete incident populations.",
            "Trace error counts include cross-service spans; inspect service identity.",
            "Counter samples are cumulative and may repeat across evaluation steps.",
            "P95 describes server-span histograms over two minutes, in milliseconds.",
            "The flag variant is read from disk; runtime symptoms establish whether it took effect.",
        ],
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("x", encoding="utf-8") as stream:
        stream.write(json.dumps(payload, indent=2, allow_nan=False) + "\n")
    return payload


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("phase", choices=("baseline", "incident", "recovery"))
    parser.add_argument("--seconds", type=float, default=120)
    parser.add_argument("--start", type=float)
    parser.add_argument("--end", type=float)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    try:
        end = time.time() if args.end is None else args.end
        start = end - args.seconds if args.start is None else args.start
        window = TimeWindow(start, end)
        output = args.output or ROOT / f"var/live-validation/{args.phase}-{int(end)}.json"
        payload = capture(args.phase, window, output)
        data = payload["data"]
        selected = data.get("traces", {}).get("traces", [])
        print(json.dumps({
            "path": str(output), "complete": payload["complete"], "errors": payload["errors"],
            "window": payload["window"], "flag_variant_on_disk": payload["payment_failure_variant_on_disk"],
            "traces_returned": len(selected),
            "selected_payment_error_spans": sum(s["is_error"] and s["service"] == "payment" for t in selected for s in t["spans"]),
            "logs_returned": data.get("logs", {}).get("returned_count"),
            "log_groups": [{"severity": g["severity"], "message": g["message_excerpt"], "sample_count": g["sample_count"]} for g in data.get("logs", {}).get("groups", [])],
            "dependency_edges": len(data.get("dependencies", {}).get("edges", [])),
        }, indent=2, allow_nan=False))
        return 0 if payload["complete"] else 1
    except (TelemetryError, ValueError, OSError) as exc:
        print(f"Capture: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
