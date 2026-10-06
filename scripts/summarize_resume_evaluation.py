"""Recalculate the two-cohort resume study without model access or private files."""

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from evals.corpus import digest, write_json
from evals.scoring import distribution, fraction, verify_report


def study_summary(root: Path, cohorts=(".", "controls-followup")) -> dict:
    packets, reviews, manifests = [], {}, []
    identity = None
    pairs = 0
    for name in cohorts:
        directory = root / name
        summary = verify_report(directory)
        config = json.loads((directory / "configuration.json").read_text())
        current = {k: config[k] for k in ["model", "billing_mode", "budget", "code_sha256", "catalog_sha256", "context_strategies"]}
        if identity is not None and current != identity:
            raise ValueError("Study cohorts have different inference/catalog identities")
        identity = current
        rows = [json.loads(line) for line in (directory / "investigations.jsonl").read_text().splitlines()]
        for review in map(json.loads, (directory / "reviews.jsonl").read_text().splitlines()):
            if review["run_id"] in reviews:
                raise ValueError("Repeated run ID across cohorts; do not count an attempt twice")
            reviews[review["run_id"]] = review
        packets.extend(rows)
        pairs += summary["comparison"]["pairs"]
        manifests.append({"directory": name, "investigations": len(rows), "summary_sha256": digest((directory / "summary.json").read_bytes())})
    cases = {s["id"]: s for s in json.loads((root / "scenarios.json").read_text())["scenarios"]}
    primary = [p for p in packets if p["strategy"] == "structured"]
    faults = [p for p in primary if cases[p["scenario_id"]]["expected_outcome"] == "diagnose"]
    controls = [p for p in primary if cases[p["scenario_id"]]["expected_outcome"] == "abstain"]
    diagnosed = [p for p in packets if p["result"]["status"] == "diagnosed"]
    results = [p["result"] for p in packets]
    complete = [r for r in results if not r["usage_unknown"]]
    measured = [m for p in packets for m in p["model_measurements"]]
    initial = [json.loads(s)["result"] for s in (root / "initial-aborted-cohort/investigations.jsonl").read_text().splitlines()]
    probe = json.loads((root / "method/diagnostic-probe.json").read_text())["result"]
    excluded = initial + [probe]
    subtotal = sum(r["input_tokens"] + r["output_tokens"] for r in results)
    return {
        "schema_version": 1, "inference_identity": identity, "cohorts": manifests,
        "scope": "Descriptive totals across two separately verified development cohorts sharing native captures. Accuracy uses primary fault trials only; controls and context-baseline arms are excluded from that denominator. Repeated captures are not independent fault injections.",
        "review_method": "Codex-assisted semantic review; not independent human adjudication",
        "evaluated_attempts": len(packets), "unique_scenarios": len({p["scenario_id"] for p in packets}),
        "primary_attempts": len(primary), "context_baseline_attempts": len(packets) - len(primary), "matched_context_pairs": pairs,
        "primary_fault_accuracy": fraction(sum(reviews[p["result"]["run_id"]]["root_cause"] == "correct" for p in faults), len(faults)),
        "primary_control_abstention": fraction(sum(reviews[p["result"]["run_id"]]["appropriate_abstention"] for p in controls), len(controls)),
        "emitted_diagnosis_grounding": fraction(sum(reviews[p["result"]["run_id"]]["claims_supported"] is True for p in diagnosed), len(diagnosed)),
        "unsafe_recommendations": sum(r["unsafe_recommendation"] for r in reviews.values()),
        "outside_advisory_scope": sum(not r["within_advisory_scope"] for r in reviews.values()),
        "model_calls": sum(r["model_calls"] for r in results), "diagnostic_reads": sum(r["tool_calls"] for r in results),
        "model_calls_distribution": distribution([r["model_calls"] for r in results]),
        "diagnostic_reads_distribution": distribution([r["tool_calls"] for r in results]),
        "runner_latency_seconds": distribution([r["latency_ms"] / 1000 for r in results]),
        "model_latency_seconds": distribution([m["latency_ms"] / 1000 for m in measured if "latency_ms" in m]),
        "model_latency_missing_calls": sum(r["model_calls"] for r in results) - sum("latency_ms" in m for m in measured),
        "reported_input_tokens": sum(r["input_tokens"] for r in results), "reported_output_tokens": sum(r["output_tokens"] for r in results),
        "reported_token_subtotal": subtotal, "unknown_usage_calls": sum(m.get("usage_unknown", False) for m in measured),
        "fully_reported_tokens": {k: distribution([r[field] for r in complete]) for k, field in [("input", "input_tokens"), ("output", "output_tokens")]},
        "fully_reported_total_tokens": distribution([r["input_tokens"] + r["output_tokens"] for r in complete]),
        "subscription_cost_usd": None,
        "excluded_development_and_probe_attempts": len(excluded), "total_sprint_attempts": len(packets) + len(excluded),
        "reported_sprint_token_subtotal": subtotal + sum(r["input_tokens"] + r["output_tokens"] for r in excluded),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    summary = study_summary(args.report)
    path = args.report / "study-summary.json"
    if args.write:
        write_json(path, summary)
    elif json.loads(path.read_text()) != summary:
        raise ValueError("Published study totals differ from the verified per-run records")
    print(f"Verified {summary['evaluated_attempts']} evaluated attempts across both cohorts; {summary['total_sprint_attempts']} sprint attempts including exclusions")


if __name__ == "__main__":
    main()
