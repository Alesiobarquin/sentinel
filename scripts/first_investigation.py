"""One live, capped investigation with developer-owned setup and cleanup.

Authentication and model availability are checked before injecting any fault.
This script stops after one run. Review checkpoint 2 before later product work.
"""

import argparse
from dataclasses import asdict
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import signal
import sys
import time
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts import demo
from scripts.validate_scenarios import capture, observations, pause
from sentinel.agent.contracts import Budget, Incident
from sentinel.agent.local import json_file, local_tools
from sentinel.agent.provider import DEFAULT_MODEL, OpenAIProvider
from sentinel.agent.runner import InvestigationRunner
from sentinel.auth import AuthError, CredentialStore, access_token, available_models


def model_provider(model: str) -> OpenAIProvider:
    store = CredentialStore(Path(os.getenv("SENTINEL_AUTH_DIR", str(Path.home() / ".config/sentinel"))))
    available = {item["slug"] for item in available_models(store)}
    if model not in available:
        raise ValueError("Model is unavailable to this account; run make models. No automatic upgrade is performed.")
    return OpenAIProvider(access_token(store), model=model, billing_mode="chatgpt")


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", default=os.getenv("SENTINEL_MODEL", DEFAULT_MODEL))
    parser.add_argument("--seconds", type=int, default=180, choices=range(120, 301), metavar="120..300")
    parser.add_argument("--max-model-calls", type=int, default=8)
    parser.add_argument("--max-total-tokens", type=int, default=50000)
    parser.add_argument("--preflight-only", action="store_true", help="Check authentication/configuration without model calls or fault injection")
    args = parser.parse_args(argv)
    provider, injected, owner_id = None, False, str(uuid4())
    def stop(signum, frame):
        raise KeyboardInterrupt()
    previous_handler = signal.signal(signal.SIGTERM, stop)
    try:
        budget = Budget(max_model_calls=args.max_model_calls, max_total_tokens=args.max_total_tokens)
        provider = model_provider(args.model)
        if demo.STATE.exists():
            raise ValueError("An existing lab fault is tracked. Run make lab-reset first.")
        flags = json_file(demo.SOURCE / "src/flagd/demo.flagd.json")["flags"]
        if any(flag.get("defaultVariant") != "off" for flag in flags.values()):
            raise ValueError("This reproducible exercise requires an all-off baseline; current settings were preserved")
        now = time.time()
        baseline_end, baseline_start = now - 30, now - 30 - args.seconds
        baseline_incident = Incident(service="payment", symptom="Baseline telemetry capture", start=baseline_start, end=baseline_end)
        local_tools(baseline_incident)
        if args.preflight_only:
            print("Authentication, selected model, budget, and local configuration passed. No model call or fault was performed.")
            return 0
        directory = ROOT / "var/first-investigation" / datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ")
        directory.mkdir(parents=True, mode=0o700)
        print(f"Exercise artifacts: {directory}", flush=True)
        baseline = capture(baseline_incident, directory / "baseline")
        if not all(result["success"] for result in baseline.values()):
            raise ValueError("Baseline diagnostic reads failed. Inspect the saved artifacts; no fault was injected.")
        # This reversible change belongs to the developer exercise. The agent
        # has no access to this module, its scenario name, or fault-state file.
        demo.inject_fault("payment-failure", owner_id=owner_id)
        injected = True
        injection_time = time.time()
        try:
            pause(10 + args.seconds + 30, "First investigation telemetry window")
            incident = Incident(service="payment", symptom="Payment charge requests are failing",
                                start=injection_time + 10, end=injection_time + 10 + args.seconds,
                                baseline_start=baseline_start, baseline_end=baseline_end)
            result = InvestigationRunner(provider, local_tools(incident), budget=budget,
                                         otlp_endpoint=os.getenv("SENTINEL_OTLP_TRACES_ENDPOINT", "http://127.0.0.1:4318/v1/traces")).run(incident)
            (directory / "agent-result.json").write_text(json.dumps(asdict(result), indent=2))
            print(json.dumps(asdict(result), indent=2), flush=True)
        finally:
            if injected:
                demo.reset_fault(owner_id=owner_id)
                injected = False
        reset_time = time.time()
        pause(10 + args.seconds + 30, "Developer exercise recovery window")
        recovery = capture(Incident(service="payment", symptom="Recovery telemetry capture",
                                   start=reset_time + 10, end=reset_time + 10 + args.seconds), directory / "recovery")
        report = {"agent_result": str(directory / "agent-result.json"), "baseline": observations(baseline, "payment"),
                  "injected_at": injection_time, "reset_at": reset_time,
                  "recovery": observations(recovery, "payment"), "remediation_executed_by_agent": False,
                  "cleanup_performed_by_developer_exercise": True, "manual_causal_review_required": True}
        (directory / "exercise-report.json").write_text(json.dumps(report, indent=2))
        print("Stopped after one investigation. Review docs/checkpoints/02-first-investigation.md and the actual saved diagnosis.")
        return 0 if result.status == "diagnosed" and report["recovery"]["all_reads_succeeded"] else 2
    except (AuthError, ValueError, OSError, demo.DemoError) as exc:
        print(f"First investigation: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("Exercise interrupted. Any active exercise fault will be reset.", file=sys.stderr)
        return 130
    finally:
        signal.signal(signal.SIGTERM, previous_handler)
        try:
            if injected or demo.STATE.exists():
                demo.reset_fault(owner_id=owner_id)
        finally:
            if provider:
                provider.close()


if __name__ == "__main__":
    sys.exit(main())
