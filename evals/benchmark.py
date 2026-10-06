"""Explicit, restartable evaluation execution. No judging or ground truth in prompts."""

from dataclasses import asdict
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import signal
import time

from evals.corpus import CATALOG, CorpusTools, LabCase, capture_corpus, catalog, digest, request_key, runtime, write_json
from scripts import demo
from scripts.first_investigation import model_provider
from sentinel.agent.contracts import Budget, Incident, ToolRequest
from sentinel.agent.runner import InvestigationRunner

COMPARISON = {"payment-failure", "shipping-slowdown", "healthy-payment", "ambiguous-payment"}
EVALUATION_BUDGET = Budget(max_model_calls=10, max_tool_calls=12, max_total_tokens=100_000)


def code_hash() -> str:
    digestor = hashlib.sha256()
    for root in ["sentinel", "evals", "scripts"]:
        for path in sorted((demo.ROOT / root).rglob("*.py")):
            digestor.update(str(path.relative_to(demo.ROOT)).encode())
            digestor.update(path.read_bytes())
    digestor.update(CATALOG.read_bytes())
    digestor.update((demo.ROOT / "infra/docker/source-context.json").read_bytes())
    return digestor.hexdigest()


def pause(seconds: float):
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        time.sleep(min(10, deadline - time.monotonic()))


def preparation_checks(case: dict, corpus: dict) -> dict:
    """Ground truth validates setup outside model context, never manufactures evidence."""
    def record(name, service, period):
        return corpus["records"][request_key(ToolRequest(name=name, service=service, period=period))]
    affected = case["affected_services"]
    def evidence_text(period):
        return " ".join(json.dumps(record(name, service, period).get("raw", {}))
                        for service in affected for name in ["logs", "traces"])
    text = evidence_text("incident").lower()
    markers = {"payment-failure": "invalid token", "cart-failure": "redis", "ad-failure": "getads failed",
               "shipping-slowdown": "delaying international", "catalog-lock-contention": "lock contention",
               "ad-high-cpu": "high cpu-load", "payment-bad-routing": "could not charge",
               "payment-wrong-suspect": "invalid token", "payment-process-unavailable": "could not charge",
               "ambiguous-payment": "invalid token"}
    checks = {"real_backend_marker_present": markers.get(case["id"], "") in text}
    for period in ["baseline", "incident"]:
        checks[f"{period}_reads_succeeded"] = all(record(name, service, period)["success"]
            for service in affected for name in ["metrics", "logs", "traces"])
    if case["id"] == "collector-coverage-gap":
        checks["real_incident_telemetry_empty"] = all(
            not record("logs", s, "incident")["raw"].get("groups") and
            not record("traces", s, "incident")["raw"].get("traces") for s in affected)
    if case["id"] == "healthy-payment":
        logs = record("logs", "payment", "incident")["raw"]
        traces = record("traces", "payment", "incident")["raw"]
        checks["healthy_successful_traffic_observed"] = bool(logs.get("groups")) and bool(traces.get("traces"))
        checks["no_sampled_payment_error"] = not any(
            s["is_error"] and s["service"] == "payment" for t in traces.get("traces", []) for s in t["spans"])
    if case["id"] == "ambiguous-payment":
        checks["source_and_configuration_unavailable"] = not record("source", "payment", None)["success"] and \
            not record("runtime_configuration", None, None)["success"]
    return {"checks": checks, "passed": all(checks.values()),
            "interpretation": "Preparation checks only; does not grade model diagnosis or prove complete signal coverage."}


def prepare(root: Path, *, seconds: int = 180, selected: list[str] | None = None):
    all_cases = catalog()
    if selected is not None and (not selected or not set(selected) <= {s["id"] for s in all_cases}):
        raise ValueError("Unknown or empty selected scenario set")
    if root.exists():
        raise ValueError("Use a new capture directory; existing evidence is immutable")
    root.mkdir(parents=True, mode=0o700)
    cases = [s for s in all_cases if selected is None or s["id"] in selected]
    write_json(root / "preparation.json", {"cases": [s["id"] for s in cases], "seconds": seconds,
               "catalog_sha256": digest(CATALOG.read_bytes()), "demo_commit": demo.load_lock()["commit"]})
    for number, case in enumerate(cases, 1):
        directory = root / case["id"]
        directory.mkdir()
        print(f"CAPTURE {number}/{len(cases)} {case['id']}: clean baseline", flush=True)
        before = runtime()
        # Require a new complete healthy window; exclude the previous case's
        # reset/export settling interval from the baseline.
        pause(30 + seconds + 30)
        baseline_end = time.time() - 30
        baseline_start = baseline_end - seconds
        baseline_runtime = runtime()
        if any(not v["running"] for v in baseline_runtime):
            raise ValueError("A target service is unavailable before fault setup")
        before_counts = {v["name"]: v["restart_count"] for v in before}
        if any(v["restart_count"] != before_counts[v["name"]] for v in baseline_runtime):
            write_json(directory / "baseline-restart-failure.json", {"before": before, "after": baseline_runtime})
            raise ValueError("Unexpected service restart contaminated the baseline; preparation stopped")
        with LabCase(case):
            injected_at = time.time()
            print(f"CAPTURE {case['id']}: real incident window", flush=True)
            pause(10 + seconds + 30)
            incident = Incident(service=case["service"], symptom=case["symptom"], start=injected_at + 10,
                                end=injected_at + 10 + seconds, baseline_start=baseline_start, baseline_end=baseline_end)
            corpus = capture_corpus(incident, directory, source_access=case["injection"]["source_access"])
            checks = preparation_checks(case, corpus)
            write_json(directory / "preparation-checks.json", checks)
            incident_runtime = runtime()
            stats = demo.run(["docker", "stats", "--no-stream", "--format", "{{json .}}",
                              "sentinel-demo-ad-1"]).strip()
            write_json(directory / "setup.json", {"scenario": case, "baseline_runtime": baseline_runtime,
                       "incident_runtime": incident_runtime, "injected_at": injected_at,
                       "observed_ad_resources": json.loads(stats)})
            if not checks["passed"]:
                raise ValueError(f"Real scenario preparation checks failed for {case['id']}; preserve and inspect the capture")
        reset_at = time.time()
        write_json(directory / "ready.json", {"scenario_id": case["id"], "corpus_sha256": digest((directory / "corpus.json").read_bytes()),
                   "incident": corpus["incident"], "reset_at": reset_at, "cleanup_completed": True})
        print(f"READY {case['id']}: hash-bound real telemetry, local cleanup complete", flush=True)
    write_json(root / "capture-complete.json", {"scenarios": len(cases), "completed_at": datetime.now(timezone.utc).isoformat()})


def evaluate(root: Path, *, model: str, repeats: int = 3, wait_for_capture: bool = False,
             aggregate_token_cap: int = 4_000_000):
    if not 2 <= repeats <= 5:
        raise ValueError("Repeated evaluation requires 2..5 runs per case")
    preparation = json.loads((root / "preparation.json").read_text())
    code = code_hash()
    config = {"model": model, "billing_mode": "chatgpt", "repeats": repeats, "budget": EVALUATION_BUDGET.model_dump(),
              "comparison_cases": sorted(COMPARISON), "code_sha256": code,
              "catalog_sha256": digest(CATALOG.read_bytes()), "aggregate_token_cap": aggregate_token_cap}
    config_path = root / "configuration.json"
    if config_path.exists() and json.loads(config_path.read_text()) != config:
        raise ValueError("Configuration/source changed; start a separate evaluation cohort")
    if not config_path.exists():
        write_json(config_path, config)
    output = root / "runs.jsonl"
    rows = [json.loads(line) for line in output.read_text().splitlines()] if output.exists() else []
    completed = {(r["scenario_id"], r["strategy"], r["repeat"]) for r in rows}
    total_tokens = sum(r["result"]["input_tokens"] + r["result"]["output_tokens"] for r in rows)
    consecutive_failures = 0
    for scenario_id in preparation["cases"]:
        ready_path = root / scenario_id / "ready.json"
        waited = time.monotonic()
        while not ready_path.exists():
            if not wait_for_capture or time.monotonic() - waited > 1200:
                raise ValueError("Capture is not ready; no model request was made")
            pause(10)
        ready = json.loads(ready_path.read_text())
        incident = Incident.model_validate(ready["incident"])
        for repeat in range(1, repeats + 1):
            # Alternate order to reduce arm/order confounding. Shared immutable
            # data does not give either arm a later configuration snapshot.
            strategies = ["structured", "chronological_raw"] if scenario_id in COMPARISON else ["structured"]
            if repeat % 2 == 0:
                strategies.reverse()
            for strategy in strategies:
                if (scenario_id, strategy, repeat) in completed:
                    continue
                if code_hash() != code:
                    raise ValueError("Evaluation source changed during execution; cohort stopped")
                if total_tokens + EVALUATION_BUDGET.max_total_tokens > aggregate_token_cap:
                    raise ValueError("Aggregate token admission cap reached; completed results retained")
                tools = CorpusTools(root / scenario_id / "corpus.json", ready["corpus_sha256"])
                provider = model_provider(model)
                print(f"MODEL {scenario_id} {strategy} repeat={repeat}", flush=True)
                try:
                    result = InvestigationRunner(provider, tools, budget=EVALUATION_BUDGET,
                        output_root=root / "investigations", context_strategy=strategy).run(incident)
                finally:
                    provider.close()
                row = {"scenario_id": scenario_id, "strategy": strategy, "repeat": repeat,
                       "corpus_sha256": ready["corpus_sha256"], "configuration_sha256": digest(config_path.read_bytes()),
                       "result": asdict(result)}
                with output.open("a") as stream:
                    stream.write(json.dumps(row, allow_nan=False) + "\n")
                    stream.flush()
                total_tokens += result.input_tokens + result.output_tokens
                print(f"RESULT {result.status} calls={result.model_calls}/{result.tool_calls} tokens={result.input_tokens + result.output_tokens} elapsed={result.latency_ms/1000:.1f}s", flush=True)
                consecutive_failures = consecutive_failures + 1 if result.status == "failed" else 0
                if consecutive_failures >= 3:
                    raise ValueError("Three consecutive failed runs; stopped without retrying or hiding them")
    write_json(root / "model-complete.json", {"investigations": len(completed) + sum(1 for r in output.read_text().splitlines()) - len(rows),
               "reported_total_tokens": total_tokens, "completed_at": datetime.now(timezone.utc).isoformat()})
