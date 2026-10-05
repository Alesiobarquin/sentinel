"""Free deterministic fault validation. No model requests or agent remediation.

Keep evaluation setup/ground truth outside DiagnosticTools and model context.
Every fault is reset in finally; SIGKILL/power loss require make lab-reset.
"""

import argparse
from dataclasses import asdict
from datetime import datetime, timezone
import json
from pathlib import Path
import signal
import sys
import time
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts import demo
from scripts.lab_scenarios import SCENARIOS
from sentinel.agent.contracts import Incident, ToolRequest
from sentinel.agent.local import json_file, local_tools
from sentinel.tools.audit import ToolRecorder
from sentinel.tools.http import TelemetryError


def pause(seconds: int, label: str) -> None:
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        remaining = max(0, round(deadline - time.monotonic()))
        print(f"{label}: {remaining}s remaining", flush=True)
        time.sleep(min(15, max(0, deadline - time.monotonic())))


def capture(incident: Incident, output: Path) -> dict:
    output.mkdir()
    tools = local_tools(incident)
    recorder = ToolRecorder(output / "tools.jsonl")
    results = {}
    for name in ["metrics", "logs", "traces", "runtime_configuration", "source"]:
        request = ToolRequest(name=name, service=incident.service if name != "runtime_configuration" else None,
                              period="incident" if name in {"metrics", "logs", "traces"} else None)
        started = time.time()
        try:
            kind, source, raw, summary = recorder.invoke(name, request.model_dump(), lambda: tools.execute(request),
                                                       lambda r: {"kind": r[0], "source": r[1]})
            payload = {"success": True, "kind": kind, "source": source, "summary": summary, "payload": raw}
        except Exception as exc:
            payload = {"success": False, "error_type": type(exc).__name__}
            if isinstance(exc, TelemetryError):
                payload["error_message"] = str(exc)[:1000]
        payload.update(started_at=started, finished_at=time.time())
        (output / (name + ".json")).write_text(json.dumps(payload, indent=2, allow_nan=False))
        results[name] = payload
    (output / "input.json").write_text(incident.model_dump_json(indent=2))
    return results


def observations(results: dict, service: str) -> dict:
    metrics, logs, traces = (results[name] for name in ("metrics", "logs", "traces"))
    error_estimate = None
    if metrics["success"]:
        values = metrics["summary"]["calls"]["values"]
        errors = [v["value"] for v in values if v["labels"].get("status_code") == "STATUS_CODE_ERROR" and v["value"] is not None]
        error_estimate = sum(errors) if errors else None  # Absence is not zero.
    error_spans = None
    if traces["success"]:
        error_spans = sum(span["is_error"] and span["service"] == service
                          for trace in traces["payload"]["traces"] for span in trace["spans"])
    groups = logs["summary"]["groups"] if logs["success"] else []
    return {"estimated_server_error_calls": error_estimate, "selected_service_error_spans": error_spans,
            "sampled_log_groups": len(groups), "sampled_warning_or_error_logs": sum(g["sample_count"] for g in groups if str(g["severity"]).lower() in {"warn", "warning", "error", "fatal"}),
            "all_reads_succeeded": all(r["success"] for r in results.values())}


def validate(name: str, root: Path, *, seconds: int, export_delay: int) -> dict:
    fault = SCENARIOS[name]
    if demo.STATE.exists():
        raise ValueError("An existing lab fault is tracked; reset it before scenario validation")
    flags = json_file(demo.SOURCE / "src/flagd/demo.flagd.json")["flags"]
    if any(flag.get("defaultVariant") != "off" for flag in flags.values()):
        raise ValueError("Scenario validation requires an all-off feature-flag baseline; existing settings were preserved")
    directory = root / name
    directory.mkdir()
    now = time.time()
    baseline_end = now - export_delay
    baseline_start = baseline_end - seconds
    baseline_incident = Incident(service=fault.service, symptom="Baseline telemetry capture", start=baseline_start, end=baseline_end)
    baseline = capture(baseline_incident, directory / "baseline")
    injected, owner_id = False, str(uuid4())
    try:
        demo.inject_fault(name, owner_id=owner_id)
        injected = True
        injection_time = time.time()
        pause(10 + seconds + export_delay, name + " fault window")
        incident = Incident(service=fault.service, symptom=fault.symptom, start=injection_time + 10,
                            end=injection_time + 10 + seconds, baseline_start=baseline_start, baseline_end=baseline_end)
        incident_results = capture(incident, directory / "incident")
    finally:
        if injected or demo.STATE.exists():
            demo.reset_fault(owner_id=owner_id)
    reset_time = time.time()
    pause(10 + seconds + export_delay, name + " recovery window")
    recovery_incident = Incident(service=fault.service, symptom="Recovery telemetry capture", start=reset_time + 10,
                                 end=reset_time + 10 + seconds)
    recovery = capture(recovery_incident, directory / "recovery")
    report = {"scenario": name, "llm_invoked": False, "source_commit": demo.load_lock()["commit"],
              "injected_at": injection_time, "reset_at": reset_time,
              "baseline": observations(baseline, fault.service), "incident": observations(incident_results, fault.service),
              "recovery": observations(recovery, fault.service),
              "interpretation": "Deterministic fault/adapter validation. This does not measure AI diagnosis quality. Recovery samples and counter estimates may contain export lag."}
    (directory / "report.json").write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2), flush=True)
    return report


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scenario", choices=[*SCENARIOS, "all"], default="all")
    parser.add_argument("--seconds", type=int, default=90, choices=range(60, 301), metavar="60..300")
    parser.add_argument("--export-delay", type=int, default=20, choices=range(15, 61), metavar="15..60")
    args = parser.parse_args(argv)
    root = ROOT / "var/scenarios" / datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ")
    root.mkdir(parents=True)
    def stop(signum, frame):
        raise KeyboardInterrupt()
    previous_handler = signal.signal(signal.SIGTERM, stop)
    try:
        selected = list(SCENARIOS) if args.scenario == "all" else [args.scenario]
        reports = [validate(name, root, seconds=args.seconds, export_delay=args.export_delay) for name in selected]
        (root / "reports.json").write_text(json.dumps(reports, indent=2))
        return 0 if all(r[phase]["all_reads_succeeded"] for r in reports for phase in ("baseline", "incident", "recovery")) else 2
    except (ValueError, OSError, demo.DemoError) as exc:
        print(f"Scenario validation failed: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("Validation interrupted; the owned active fault was reset.", file=sys.stderr)
        return 130
    finally:
        signal.signal(signal.SIGTERM, previous_handler)


if __name__ == "__main__":
    sys.exit(main())
