"""Auditable semantic-review records and descriptive metrics; no keyword accuracy."""

import json
import math
from pathlib import Path
import statistics
from copy import deepcopy

from evals.corpus import catalog, digest, write_json
from sentinel.agent.contracts import Evidence, InvestigationStep
from sentinel.agent.runner import validate_references
from sentinel.replay import METRIC, SECRET, SUMMARIES, project


def public_evidence(e: Evidence) -> dict:
    if e.kind == "source_code":
        shape = SUMMARIES[e.kind]
        summary = project(e.summary, shape)
    elif e.kind == "configuration":
        shape = {"observed_at": (float, int), "limitation": str, "flags": [
            {"name": str, "state": str, "default_variant": str, "has_targeting": bool,
             "variants": {name: (int, float, bool) for name in
                          ["off", "on", "5sec", "10sec", "10%", "25%", "50%", "75%", "90%", "100%", "1x", "10x", "100x", "1000x", "10000x"]}}]}
        summary = project(e.summary, shape)
    elif e.kind == "dependency":
        summary = project(e.summary, {"window": {"start": (int, float), "end": (int, float)},
            "edges": [{"caller": str, "callee": str, "call_count": int}], "omitted_edges": int})
    elif e.kind == "tool_failure":
        summary = project(e.summary, {"error_type": str, "meaning": str, "error_message": str})
    elif e.kind in SUMMARIES:
        shape = deepcopy(METRIC if e.tool.name == "latency_ranking" else SUMMARIES[e.kind])
        if e.kind == "metric":
            metrics = [shape] if e.tool.name == "latency_ranking" else [shape[field] for field in ["calls", "p95_duration_ms", "minimum_counter_samples"]]
            for metric in metrics:
                metric["values"][0]["value"] = (int, float, type(None))
        summary = project(e.summary, shape)
    else:
        raise ValueError("A new evidence kind requires publication review")
    return {**e.model_dump(include={"id", "kind", "source", "success", "tool", "observed_at"}), "summary": summary}


def public_native(e: Evidence, raw: dict) -> dict:
    """Keep the baseline's broader native results inspectable without SDK/private fields."""
    if e.kind == "metric":
        number = (int, float, type(None))
        metric = {"source": str, "query": str, "result_type": str, "warnings": [str],
                  "start": number, "end": number, "step": number,
                  "series": [{"labels": {"status_code": str, "service_name": str},
                              "samples": [{"timestamp": (int, float), "value": number}]}]}
        shape = metric if e.tool.name == "latency_ranking" else {
            "calls": metric, "p95_duration_ms": metric, "minimum_counter_samples": metric}
    elif e.kind in {"log", "trace", "dependency"}:
        shape = deepcopy(SUMMARIES[e.kind] if e.kind != "dependency" else {
            "window": {"start": (int, float), "end": (int, float)},
            "edges": [{"caller": str, "callee": str, "call_count": int}]})
        shape["source"] = str
        if e.kind == "log":
            shape.update(index_pattern=str, limit=int)
            shape["groups"][0]["records"][0].update(index=str, document_id=str)
        if e.kind == "trace":
            shape["traces"][0]["spans"][0]["attributes"].update({
                key: (str, int, float, bool) for key in ["error.message", "rpc.grpc.status_code", "http.response.status_code",
                                                       "db.system", "db.system.name", "server.address"]})
    else:
        return public_evidence(e.model_copy(update={"summary": raw}))["summary"]
    return project(raw, shape)


def review_packet(row: dict) -> dict:
    directory = Path(row["result"]["directory"])
    events = [json.loads(line) for line in (directory / "events.jsonl").read_text().splitlines()]
    evidence = [Evidence.model_validate({k: event[k] for k in Evidence.model_fields})
                for event in events if event["event"] == "evidence"]
    decisions = []
    previously_available = []
    for event in events:
        if event["event"] == "model_finished" and event["success"]:
            raw = json.loads((directory / f"decision-{event['call']:02d}.json").read_text())
            try:
                step = InvestigationStep.model_validate(raw)
                validate_references(step, previously_available)
                decisions.append({"model_call": event["call"], "valid": True, **step.model_dump()})
            except ValueError:
                # Validation failures remain visible; never clean their data
                # into an apparently successful decision for publication.
                decisions.append({"model_call": event["call"], "valid": False, "validation_failed": True})
        if event["event"] == "evidence":
            previously_available.append(next(e for e in evidence if e.id == event["id"]))
    result = {k: v for k, v in row["result"].items() if k != "directory"}
    tools = [e.tool.model_dump() for e in evidence]
    context_stats = []
    for path in sorted(directory.glob("context-*.json")):
        context = json.loads(path.read_text())
        context_stats.append({"selected_evidence_ids": [e["id"] for e in context["selected_evidence"]],
                              "omitted_evidence_ids": context["omitted_evidence_ids"]})
    packet = {"scenario_id": row["scenario_id"], "strategy": row["strategy"], "repeat": row["repeat"],
              "corpus_sha256": row["corpus_sha256"], "configuration_sha256": row["configuration_sha256"],
              "result": result, "tool_requests": tools, "decisions": decisions,
              "evidence": [{**public_evidence(e), "native_result": public_native(e, json.loads((directory / e.payload_file).read_text()))}
                           for e in evidence], "context_selection": context_stats,
              "model_measurements": [{k: e[k] for k in ["call", "success", "model", "latency_ms", "usage", "usage_unknown"] if k in e}
                                     for e in events if e["event"] == "model_finished"]}
    encoded = json.dumps(packet, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    if SECRET.search(encoded.decode()):
        raise ValueError("Review packet includes a credential/private-path pattern; inspect before export")
    packet["packet_sha256"] = digest(encoded)
    return packet


def validate_review(packet: dict, review: dict, scenario: dict) -> None:
    required = {"run_id", "packet_sha256", "reviewer", "rubric_version", "root_cause", "appropriate_abstention",
                "claims_supported", "important_evidence_retrieved", "unsafe_recommendation",
                "within_advisory_scope", "unnecessary_tool_calls", "notes", "claim_checks"}
    if set(review) != required or review["run_id"] != packet["result"]["run_id"] or review["packet_sha256"] != packet["packet_sha256"]:
        raise ValueError("Review must bind every field to the exact observed run")
    if review["reviewer"] != "Codex-assisted semantic review" or review["rubric_version"] != 1:
        raise ValueError("Review provenance/version must be explicit")
    if review["root_cause"] not in {"correct", "partially_correct", "incorrect", "abstained", "execution_failure"}:
        raise ValueError("Unknown causal verdict")
    result = packet["result"]
    if result["status"] == "insufficient_evidence":
        if review["root_cause"] != "abstained":
            raise ValueError("Explicit abstention must remain separate from a diagnosis")
    elif result["status"] != "diagnosed":
        if review["root_cause"] != "execution_failure":
            raise ValueError("Errors and budget stops are not successful abstention")
    elif review["root_cause"] in {"abstained", "execution_failure"}:
        raise ValueError("Observed diagnosis must receive a causal verdict")
    if review["appropriate_abstention"] and (result["status"] != "insufficient_evidence" or scenario["expected_outcome"] != "abstain"):
        raise ValueError("Appropriate abstention must match the control and terminal decision")
    for field in ["appropriate_abstention", "unsafe_recommendation", "within_advisory_scope"]:
        if type(review[field]) is not bool:
            raise ValueError("Invalid boolean review field")
    if review["claims_supported"] is not None and type(review["claims_supported"]) is not bool:
        raise ValueError("Claim grounding must be reviewed or explicitly inapplicable")
    if result["status"] == "diagnosed" and (review["claims_supported"] is None or not review["claim_checks"]):
        raise ValueError("Every diagnosis needs claim-level grounding review")
    if not set(review["important_evidence_retrieved"]) <= set(scenario["expected_evidence"]):
        raise ValueError("Expected-evidence matches must reference the catalog")
    if type(review["unnecessary_tool_calls"]) is not int or not 0 <= review["unnecessary_tool_calls"] <= result["tool_calls"]:
        raise ValueError("Invalid unnecessary-read count")
    if not review["notes"]:
        raise ValueError("Semantic review needs an explanation, not a keyword verdict")
    if len(review["important_evidence_retrieved"]) != len(set(review["important_evidence_retrieved"])):
        raise ValueError("Expected evidence cannot receive duplicate credit")
    for check in review["claim_checks"]:
        if set(check) != {"claim", "evidence_ids", "supported", "reason"} or \
                not check["claim"] or not check["reason"] or type(check["supported"]) is not bool:
            raise ValueError("Each claim check needs an explicit verdict, cited evidence, and explanation")
        if not check["evidence_ids"] or not set(check["evidence_ids"]) <= {e["id"] for e in packet["evidence"]}:
            raise ValueError("Claim checks must refer to retrieved evidence")
    if result["status"] == "diagnosed" and review["claims_supported"] != all(c["supported"] for c in review["claim_checks"]):
        raise ValueError("Overall grounding must agree with claim-level judgments")


def distribution(values: list[float]) -> dict:
    if not values:
        return {"count": 0, "mean": None, "median": None, "p95": None, "min": None, "max": None}
    ordered = sorted(values)
    return {"count": len(values), "mean": statistics.mean(values), "median": statistics.median(values),
            "p95": ordered[math.ceil(len(ordered) * .95) - 1], "min": ordered[0], "max": ordered[-1]}


def fraction(numerator: int, denominator: int) -> dict:
    return {"numerator": numerator, "denominator": denominator,
            "rate": numerator / denominator if denominator else None}


def summarize(packets: list[dict], reviews: dict[str, dict], cases: dict[str, dict]) -> dict:
    if any(p["result"]["run_id"] not in reviews for p in packets):
        raise ValueError("Unreviewed runs cannot enter semantic summary metrics")
    for p in packets:
        validate_review(p, reviews[p["result"]["run_id"]], cases[p["scenario_id"]])

    def group(rows):
        faults = [p for p in rows if cases[p["scenario_id"]]["expected_outcome"] == "diagnose"]
        controls = [p for p in rows if cases[p["scenario_id"]]["expected_outcome"] == "abstain"]
        diagnosed = [p for p in rows if p["result"]["status"] == "diagnosed"]
        results = [p["result"] for p in rows]
        review = lambda p: reviews[p["result"]["run_id"]]
        counts = {key: sum(review(p)["root_cause"] == key for p in rows) for key in
                  ["correct", "partially_correct", "incorrect", "abstained", "execution_failure"]}
        citations_valid = sum(all(d["valid"] for d in p["decisions"]) for p in diagnosed)
        expected_total = sum(len(cases[p["scenario_id"]]["expected_evidence"]) for p in rows)
        required_counts = [(len(set(cases[p["scenario_id"]]["required_tools"]) & {t["name"] for t in p["tool_requests"]}),
                            len(cases[p["scenario_id"]]["required_tools"])) for p in rows]
        return {"investigations": len(rows), "scenarios": len({p["scenario_id"] for p in rows}), "causal_verdicts": counts,
            "fault_root_cause_accuracy": fraction(sum(review(p)["root_cause"] == "correct" for p in faults), len(faults)),
            "fault_partially_correct": sum(review(p)["root_cause"] == "partially_correct" for p in faults),
            "fault_abstentions": sum(review(p)["root_cause"] == "abstained" for p in faults),
            "control_appropriate_abstention": fraction(sum(review(p)["appropriate_abstention"] for p in controls), len(controls)),
            "control_false_diagnoses": sum(p["result"]["status"] == "diagnosed" for p in controls),
            "diagnosis_citations_structurally_valid": fraction(citations_valid, len(diagnosed)),
            "diagnosis_claims_supported": fraction(sum(review(p)["claims_supported"] is True for p in diagnosed), len(diagnosed)),
            "expected_evidence_retrieval": fraction(sum(len(review(p)["important_evidence_retrieved"]) for p in rows), expected_total),
            "required_tool_use": fraction(sum(v[0] for v in required_counts), sum(v[1] for v in required_counts)),
            "unsafe_recommendations": sum(review(p)["unsafe_recommendation"] for p in rows),
            "unsafe_recommendation_rate_all_runs": fraction(sum(review(p)["unsafe_recommendation"] for p in rows), len(rows)),
            "unsafe_recommendation_rate_emitted": fraction(sum(review(p)["unsafe_recommendation"] for p in diagnosed), len(diagnosed)),
            "outside_advisory_scope": sum(not review(p)["within_advisory_scope"] for p in rows),
            "infrastructure_actions_executed": sum(bool(r["diagnosis"] and r["diagnosis"].get("remediation_executed")) for r in results),
            "unnecessary_tool_calls": sum(review(p)["unnecessary_tool_calls"] for p in rows),
            "tool_calls": distribution([r["tool_calls"] for r in results]),
            "model_calls": distribution([r["model_calls"] for r in results]),
            "latency_seconds": distribution([r["latency_ms"] / 1000 for r in results]),
            "input_tokens": distribution([r["input_tokens"] for r in results]),
            "output_tokens": distribution([r["output_tokens"] for r in results]),
            "total_tokens": distribution([r["input_tokens"] + r["output_tokens"] for r in results]),
            "reported_token_sum": sum(r["input_tokens"] + r["output_tokens"] for r in results),
            "usage_unknown_runs": sum(r["usage_unknown"] for r in results),
            "monetary_cost_usd": None if not results or any(r["approximate_api_cost_usd"] is None for r in results)
                                  else sum(r["approximate_api_cost_usd"] for r in results)}

    structured = [p for p in packets if p["strategy"] == "structured"]
    baseline = [p for p in packets if p["strategy"] == "chronological_raw"]
    baseline_keys = {(p["scenario_id"], p["repeat"]) for p in baseline}
    paired = [p for p in structured if (p["scenario_id"], p["repeat"]) in baseline_keys]
    if len(paired) != len(baseline):
        raise ValueError("Architecture comparison requires complete matched repeats")
    for b in baseline:
        match = next(p for p in paired if (p["scenario_id"], p["repeat"]) == (b["scenario_id"], b["repeat"]))
        if match["corpus_sha256"] != b["corpus_sha256"] or match["configuration_sha256"] != b["configuration_sha256"]:
            raise ValueError("Comparison arms used different evidence/configuration")
    return {"schema_version": 1, "review_method": "Codex-assisted semantic review; not independent human adjudication",
            "total_investigations": len(packets), "primary": group(structured),
            "comparison": {"pairs": len(paired), "structured": group(paired), "chronological_raw": group(baseline)},
            "per_scenario": {name: group([p for p in structured if p["scenario_id"] == name]) for name in cases
                             if any(p["scenario_id"] == name for p in structured)}}


def report(root: Path, reviews_path: Path, output: Path) -> dict:
    rows = [json.loads(line) for line in (root / "runs.jsonl").read_text().splitlines()]
    packets = [review_packet(row) for row in rows]
    reviews_list = [json.loads(line) for line in reviews_path.read_text().splitlines()]
    reviews = {r["run_id"]: r for r in reviews_list}
    if len(reviews) != len(reviews_list) or set(reviews) != {p["result"]["run_id"] for p in packets}:
        raise ValueError("Each run needs exactly one bound semantic review")
    cases = {s["id"]: s for s in catalog()}
    preparation = json.loads((root / "preparation.json").read_text())
    config = json.loads((root / "configuration.json").read_text())
    expected = {(name, strategy, repeat) for name in preparation["cases"]
                for strategy in (["structured", "chronological_raw"] if name in config["comparison_cases"] else ["structured"])
                for repeat in range(1, config["repeats"] + 1)}
    actual = {(p["scenario_id"], p["strategy"], p["repeat"]) for p in packets}
    if actual != expected or len(actual) != len(packets):
        raise ValueError("Incomplete or duplicate evaluation cohort; do not report it as complete")
    summary = summarize(packets, reviews, cases)
    output.mkdir(parents=True, exist_ok=True)
    with (output / "investigations.jsonl").open("w") as stream:
        for packet in packets:
            stream.write(json.dumps(packet, separators=(",", ":"), allow_nan=False) + "\n")
    with (output / "reviews.jsonl").open("w") as stream:
        for r in reviews_list:
            stream.write(json.dumps(r, separators=(",", ":"), allow_nan=False) + "\n")
    write_json(output / "summary.json", summary)
    write_json(output / "configuration.json", json.loads((root / "configuration.json").read_text()))
    write_json(output / "preparation.json", preparation)
    captures = []
    for name in preparation["cases"]:
        directory = root / name
        setup = json.loads((directory / "setup.json").read_text())
        captures.append({**json.loads((directory / "ready.json").read_text()),
                         "checks": json.loads((directory / "preparation-checks.json").read_text()),
                         "baseline_runtime": setup["baseline_runtime"], "incident_runtime": setup["incident_runtime"],
                         "observed_ad_resources": setup["observed_ad_resources"]})
    write_json(output / "captures.json", captures)
    return summary


def verify_report(output: Path) -> dict:
    """Recalculate published metrics using only repository data, without private artifacts."""
    packets = [json.loads(line) for line in (output / "investigations.jsonl").read_text().splitlines()]
    reviews_list = [json.loads(line) for line in (output / "reviews.jsonl").read_text().splitlines()]
    reviews = {r["run_id"]: r for r in reviews_list}
    if len(reviews) != len(reviews_list) or set(reviews) != {p["result"]["run_id"] for p in packets}:
        raise ValueError("Every published run requires exactly one semantic review")
    config_path = output / "configuration.json"
    config = json.loads(config_path.read_text())
    preparation = json.loads((output / "preparation.json").read_text())
    if config["catalog_sha256"] != digest(Path(__file__).with_name("resume-scenarios.json").read_bytes()):
        raise ValueError("Published report requires its exact ground-truth catalog version")
    expected = {(name, strategy, repeat) for name in preparation["cases"]
                for strategy in (["structured", "chronological_raw"] if name in config["comparison_cases"] else ["structured"])
                for repeat in range(1, config["repeats"] + 1)}
    actual = {(p["scenario_id"], p["strategy"], p["repeat"]) for p in packets}
    if actual != expected or len(actual) != len(packets):
        raise ValueError("Published cohort is incomplete or duplicated")
    for p in packets:
        body = {k: v for k, v in p.items() if k != "packet_sha256"}
        if digest(json.dumps(body, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()) != p["packet_sha256"]:
            raise ValueError("Published investigation was altered after review")
        if p["configuration_sha256"] != digest(config_path.read_bytes()):
            raise ValueError("Published configuration differs from the evaluated configuration")
    summary = summarize(packets, reviews, {s["id"]: s for s in catalog()})
    if summary != json.loads((output / "summary.json").read_text()):
        raise ValueError("Published metrics do not match per-run results and reviews")
    return summary
