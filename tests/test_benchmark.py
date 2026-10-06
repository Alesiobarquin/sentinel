from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from evals.benchmark import evaluate
from evals.corpus import CATALOG, CorpusTools, LabCase, catalog, cleanup, digest, request_key, write_json
from evals.scoring import distribution, fraction, public_native, summarize, validate_review, verify_report
from sentinel.agent.context import build_context
from sentinel.agent.contracts import Evidence, Incident, ToolRequest
from sentinel.agent.runner import RunResult
from sentinel.tools.http import TelemetryError


def packet(run="fixture", status="diagnosed", scenario="fault", strategy="structured"):
    return {"scenario_id": scenario, "strategy": strategy, "repeat": 1, "corpus_sha256": "same-capture",
            "configuration_sha256": "same-config", "packet_sha256": "fixture-hash",
            "result": {"run_id": run, "status": status, "diagnosis": {"remediation_executed": False} if status == "diagnosed" else None,
                       "model_calls": 2, "tool_calls": 2, "latency_ms": 1000, "input_tokens": 100,
                       "output_tokens": 50, "usage_unknown": False, "approximate_api_cost_usd": None},
            "decisions": [{"valid": True}], "tool_requests": [{"name": "logs"}], "evidence": [{"id": "ev_001"}]}


def review(p, outcome="correct"):
    return {"run_id": p["result"]["run_id"], "packet_sha256": p["packet_sha256"],
            "reviewer": "Codex-assisted semantic review", "rubric_version": 1, "root_cause": outcome,
            "appropriate_abstention": False, "claims_supported": True if p["result"]["status"] == "diagnosed" else None,
            "important_evidence_retrieved": ["Observed logs"], "unsafe_recommendation": False,
            "within_advisory_scope": True, "unnecessary_tool_calls": 0,
            "notes": "Synthetic scoring fixture, not an AI evaluation.",
            "claim_checks": [{"claim": "Fixture", "evidence_ids": ["ev_001"], "supported": True, "reason": "Synthetic fixture"}]}


def cases():
    return {name: {"expected_outcome": outcome, "expected_evidence": ["Observed logs"], "required_tools": ["logs"]}
            for name, outcome in [("fault", "diagnose"), ("control", "abstain")]}


class BenchmarkTests(unittest.TestCase):
    def test_subscription_limit_stops_batch_after_retaining_the_first_failed_attempt(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_json(root / "preparation.json", {"cases": ["fixture"]})
            write_json(root / "fixture/ready.json", {
                "incident": Incident(service="payment", symptom="Fixture", start=1000.0, end=1180.0).model_dump(),
                "corpus_sha256": "fixture"})
            run = root / "investigations/quota"
            run.mkdir(parents=True)
            (run / "events.jsonl").write_text('{"event":"model_finished","failure_category":"subscription_usage_limit"}\n')
            failed = RunResult("quota", "failed", "Safe failure", None, "gpt-5.6-luna", "chatgpt",
                               1, 1, 0, 0, 0, None, True, 1.0, ["ev_001"], str(run))
            with patch("evals.benchmark.code_hash", return_value="frozen"), \
                 patch("evals.benchmark.CorpusTools"), patch("evals.benchmark.model_provider") as provider, \
                 patch("evals.benchmark.InvestigationRunner") as runner:
                runner.return_value.run.return_value = failed
                with self.assertRaisesRegex(ValueError, "paused new requests"):
                    evaluate(root, model="gpt-5.6-luna", repeats=3)
                self.assertEqual(provider.call_count, 1)
                self.assertEqual(runner.return_value.run.call_count, 1)
            rows = (root / "runs.jsonl").read_text().splitlines()
            self.assertEqual(len(rows), 1)
            self.assertTrue(json.loads(rows[0])["result"]["usage_unknown"])
            self.assertFalse((root / "model-complete.json").exists())

    def test_catalog_has_distinct_faults_and_all_three_abstention_controls(self):
        scenarios = catalog()
        self.assertGreaterEqual(len(scenarios), 10)
        self.assertLessEqual(len(scenarios), 15)
        self.assertEqual(len({s["id"] for s in scenarios}), len(scenarios))
        controls = [s for s in scenarios if s["expected_outcome"] == "abstain"]
        self.assertTrue(any(s["category"] == "healthy control" for s in controls))
        self.assertTrue(any(s["category"] == "insufficient evidence control" for s in controls))
        self.assertTrue(any("ambiguous" in s["category"] for s in controls))
        for scenario in scenarios:
            self.assertTrue(scenario["noncausal_evidence"])
            self.assertTrue(scenario["acceptable_remediation"])

    def test_corpus_replays_native_results_and_rejects_tampering_or_missing_reads(self):
        request = ToolRequest(name="services", service=None, period=None)
        corpus = {"incident": {"service": "payment"}, "records": {request_key(request):
                  {"success": True, "kind": "inventory", "source": "fixture", "raw": {"services": ["payment"]},
                   "summary": {"services": ["payment"]}}}}
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "corpus.json"
            path.write_text(json.dumps(corpus))
            tools = CorpusTools(path, digest(path.read_bytes()))
            self.assertEqual(tools.execute(request)[2], {"services": ["payment"]})
            with self.assertRaises(ValueError):
                tools.execute(ToolRequest(name="logs", service="payment", period="incident"))
            with self.assertRaises(ValueError):
                tools.execute(ToolRequest(name="logs", service="unknown", period="incident"))
            original = digest(path.read_bytes())
            path.write_text('{}')
            with self.assertRaises(ValueError):
                CorpusTools(path, original)

    def test_real_capture_failures_are_not_replaced_by_fake_health(self):
        inventory = ToolRequest(name="services", service=None, period=None)
        request = ToolRequest(name="source", service="payment", period=None)
        corpus = {"incident": {"service": "payment"}, "records": {
            request_key(inventory): {"raw": {"services": ["payment"]}},
            request_key(request): {"success": False, "message": "Source access unavailable"}}}
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "corpus.json"
            path.write_text(json.dumps(corpus))
            with self.assertRaises(TelemetryError):
                CorpusTools(path, digest(path.read_bytes())).execute(request)

    def test_baseline_has_same_index_budget_and_complete_native_payload(self):
        incident = Incident(service="payment", symptom="Fixture", start=1000.0, end=1180.0)
        e = Evidence(id="ev_001", run_id="fixture", kind="log", source="fixture", observed_at=1.0,
                     tool=ToolRequest(name="logs", service="payment", period="incident"), success=True,
                     summary={"reduced": True, "coverage": "bounded"}, payload_file="x")
        raw = {"native_records": list(range(20)), "coverage": "bounded"}
        normal = build_context(incident, [e], [], max_bytes=4000, remaining={})
        baseline = build_context(incident, [e], [], max_bytes=4000, remaining={},
                                 strategy="chronological_raw", payloads={e.id: raw})
        self.assertEqual(normal["evidence_index"], baseline["evidence_index"])
        self.assertEqual(baseline["selected_evidence"][0]["summary"], raw)
        self.assertNotIn("ground_truth", baseline)
        self.assertEqual(e.summary, {"reduced": True, "coverage": "bounded"})
        with self.assertRaises(ValueError):
            build_context(incident, [e], [], max_bytes=4000, remaining={}, strategy="chronological_raw")

    def test_oversized_native_result_is_explicitly_omitted_not_silently_truncated(self):
        incident = Incident(service="payment", symptom="Fixture", start=1000.0, end=1180.0)
        e = Evidence(id="ev_001", run_id="fixture", kind="log", source="fixture", observed_at=1.0,
                     tool=ToolRequest(name="logs", service="payment", period="incident"), success=True,
                     summary={"reduced": True}, payload_file="x")
        context = build_context(incident, [e], [], max_bytes=4000, remaining={}, strategy="chronological_raw",
                                payloads={e.id: {"native": "a" * 8000}})
        self.assertEqual(context["omitted_evidence_ids"], [e.id])
        self.assertEqual(context["selected_evidence"], [])

    def test_raw_baseline_prioritizes_recent_reads_without_signal_ranking(self):
        incident = Incident(service="payment", symptom="Fixture", start=1000.0, end=1180.0)
        evidence = [Evidence(id=f"ev_{i:03d}", run_id="fixture", kind="inventory", source="fixture", observed_at=float(i),
                             tool=ToolRequest(name="services", service=None, period=None), success=True,
                             summary={"reduced": True}, payload_file="fixture") for i in [1, 2]]
        context = build_context(incident, evidence, [], max_bytes=4000, remaining={}, strategy="chronological_raw",
                                payloads={e.id: {"native": "a" * 1500} for e in evidence})
        self.assertEqual([e["id"] for e in context["selected_evidence"]], ["ev_002"])
        self.assertEqual(context["omitted_evidence_ids"], ["ev_001"])

    def test_fault_restores_prior_settings_after_failure_and_checks_ownership(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            flag_path = root / "source/src/flagd/demo.flagd.json"
            flag_path.parent.mkdir(parents=True)
            flag_path.write_text(json.dumps({"flags": {"paymentFailure": {"state": "ENABLED", "defaultVariant": "off", "variants": {"off": 0, "100%": 1}}}}))
            state = root / "evaluation-state.json"
            with patch("evals.corpus.LAB_STATE", state), patch("evals.corpus.demo.SOURCE", root / "source"), \
                 patch("evals.corpus.demo.STATE", root / "legacy-fault.json"), patch("evals.corpus.runtime", return_value=[]):
                case = {"id": "fixture", "injection": {"flags": {"paymentFailure": "100%"}, "stop_services": []}}
                with self.assertRaises(RuntimeError):
                    with LabCase(case):
                        self.assertEqual(json.loads(flag_path.read_text())["flags"]["paymentFailure"]["defaultVariant"], "100%")
                        with self.assertRaises(ValueError):
                            cleanup("different-owner")
                        raise RuntimeError("Synthetic failure")
                self.assertFalse(state.exists())
                self.assertEqual(json.loads(flag_path.read_text())["flags"]["paymentFailure"]["defaultVariant"], "off")

    def test_semantic_summary_separates_partial_correct_failures_and_controls(self):
        good, partial = packet("good"), packet("partial")
        failed = packet("failed", status="failed", scenario="control")
        verdicts = {p["result"]["run_id"]: review(p, outcome) for p, outcome in
                    [(good, "correct"), (partial, "partially_correct"), (failed, "execution_failure")]}
        summary = summarize([good, partial, failed], verdicts, cases())["primary"]
        self.assertEqual(summary["fault_root_cause_accuracy"], fraction(1, 2))
        self.assertEqual(summary["control_appropriate_abstention"], fraction(0, 1))
        self.assertEqual(summary["causal_verdicts"]["execution_failure"], 1)
        self.assertIsNone(summary["monetary_cost_usd"])

    def test_abstention_only_counts_if_terminal_decision_matches_control(self):
        p = packet(status="insufficient_evidence", scenario="control")
        r = review(p, "abstained")
        r["appropriate_abstention"] = True
        summary = summarize([p], {p["result"]["run_id"]: r}, cases())["primary"]
        self.assertEqual(summary["control_appropriate_abstention"], fraction(1, 1))
        bad = deepcopy(r)
        bad["root_cause"] = "correct"
        with self.assertRaises(ValueError):
            validate_review(p, bad, cases()["control"])

    def test_correct_no_fault_finding_is_not_a_false_cause_or_explicit_abstention(self):
        p = packet(status="diagnosed", scenario="control")
        r = review(p, "correct")
        summary = summarize([p], {p["result"]["run_id"]: r}, cases())["primary"]
        self.assertEqual(summary["control_appropriate_abstention"], fraction(0, 1))
        self.assertEqual(summary["control_diagnosis_outputs"], 1)
        self.assertEqual(summary["control_unsupported_fault_attributions"], 0)

    def test_unknown_usage_subtotals_are_excluded_from_complete_token_statistics(self):
        complete = packet("complete")
        unknown = packet("unknown", status="failed")
        unknown["result"].update(input_tokens=900, output_tokens=100, usage_unknown=True)
        complete["model_measurements"] = [{"latency_ms": 250, "usage_unknown": False},
                                          {"latency_ms": 500, "usage_unknown": False}]
        unknown["model_measurements"] = [{"latency_ms": 800, "usage_unknown": False},
                                         {"usage_unknown": True}]
        reviews = {p["result"]["run_id"]: review(p, verdict) for p, verdict in
                   [(complete, "correct"), (unknown, "execution_failure")]}
        summary = summarize([complete, unknown], reviews, cases())["primary"]
        self.assertEqual(summary["reported_token_sum"], 1150)
        self.assertEqual(summary["usage_unknown_runs"], 1)
        self.assertEqual(summary["usage_unknown_model_calls"], 1)
        self.assertEqual(summary["fully_reported_tokens"]["total"]["count"], 1)
        self.assertEqual(summary["fully_reported_tokens"]["total"]["mean"], 150)
        self.assertEqual(summary["model_call_latency_seconds"]["count"], 3)
        self.assertEqual(summary["model_call_latency_missing"], 1)

    def test_incomplete_or_stale_semantic_reviews_cannot_produce_accuracy(self):
        p = packet()
        with self.assertRaises(ValueError):
            summarize([p], {}, cases())
        r = review(p)
        r["packet_sha256"] = "different"
        with self.assertRaises(ValueError):
            validate_review(p, r, cases()["fault"])
        r = review(p)
        r["claims_supported"] = None
        with self.assertRaises(ValueError):
            validate_review(p, r, cases()["fault"])

    def test_paired_comparison_rejects_different_data_or_unpaired_repeats(self):
        normal = packet("normal")
        baseline = packet("baseline", strategy="chronological_raw")
        reviews = {p["result"]["run_id"]: review(p) for p in [normal, baseline]}
        comparison = summarize([normal, baseline], reviews, cases())["comparison"]
        self.assertEqual(comparison["pairs"], 1)
        self.assertEqual(comparison["complete_usage_efficiency"]["pairs"], 1)
        baseline["result"]["usage_unknown"] = True
        comparison = summarize([normal, baseline], reviews, cases())["comparison"]
        self.assertEqual(comparison["complete_usage_efficiency"]["pairs"], 0)
        self.assertEqual(comparison["structured"]["fault_root_cause_accuracy"], fraction(1, 1))
        self.assertEqual(comparison["chronological_raw"]["fault_root_cause_accuracy"], fraction(1, 1))
        baseline["corpus_sha256"] = "different"
        with self.assertRaises(ValueError):
            summarize([normal, baseline], reviews, cases())
        with self.assertRaises(ValueError):
            summarize([baseline], reviews, cases())

    def test_distribution_uses_documented_nearest_rank_and_unknown_empty_values(self):
        self.assertEqual(distribution([1, 2, 3])["p95"], 3)
        self.assertEqual(distribution([1, 2, 3])["median"], 2)
        self.assertIsNone(distribution([])["mean"])
        self.assertIsNone(fraction(0, 0)["rate"])

    def test_public_native_retains_broader_samples_and_drops_unreviewed_fields(self):
        e = Evidence(id="ev_001", run_id="fixture", kind="metric", source="prometheus", observed_at=1.0,
                     tool=ToolRequest(name="latency_ranking", service=None, period="incident"), success=True,
                     summary={}, payload_file="fixture")
        raw = {"query": "fixture", "series": [{"labels": {"service_name": "payment", "secret": "discard"},
               "samples": [{"timestamp": 1.0, "value": None}, {"timestamp": 2.0, "value": 3.0}]}], "private": "discard"}
        exported = public_native(e, raw)
        self.assertEqual(exported["series"][0]["samples"], raw["series"][0]["samples"])
        self.assertEqual(exported["series"][0]["labels"], {"service_name": "payment"})
        self.assertNotIn("private", exported)

    def test_semantic_review_rejects_duplicate_evidence_and_unbound_claims(self):
        p = packet()
        r = review(p)
        r["important_evidence_retrieved"] *= 2
        with self.assertRaises(ValueError):
            validate_review(p, r, cases()["fault"])
        r = review(p)
        r["claim_checks"][0]["evidence_ids"] = ["ev_999"]
        with self.assertRaises(ValueError):
            validate_review(p, r, cases()["fault"])

    def test_public_summary_is_recalculable_without_private_run_files(self):
        case = catalog()[0]
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            config = {"catalog_sha256": digest(CATALOG.read_bytes()), "comparison_cases": [], "repeats": 3}
            write_json(root / "configuration.json", config)
            write_json(root / "preparation.json", {"cases": [case["id"]]})
            (root / "scenarios.json").write_bytes(CATALOG.read_bytes())
            packets, reviews = [], []
            for repeat in range(1, 4):
                p = packet(f"fixture-{repeat}", scenario=case["id"])
                p["repeat"] = repeat
                p["configuration_sha256"] = digest((root / "configuration.json").read_bytes())
                body = {k: v for k, v in p.items() if k != "packet_sha256"}
                p["packet_sha256"] = digest(json.dumps(body, sort_keys=True, separators=(",", ":")).encode())
                r = review(p)
                r["important_evidence_retrieved"] = []
                packets.append(p)
                reviews.append(r)
            for name, values in [("investigations", packets), ("reviews", reviews)]:
                (root / f"{name}.jsonl").write_text("\n".join(json.dumps(v) for v in values) + "\n")
            summary = summarize(packets, {r["run_id"]: r for r in reviews}, {s["id"]: s for s in catalog()})
            write_json(root / "summary.json", summary)
            self.assertEqual(verify_report(root), summary)
            future = root / "future-catalog.json"
            future.write_text('{}')
            with patch("evals.corpus.CATALOG", future):
                self.assertEqual(verify_report(root), summary)
            snapshot = root / "scenarios.json"
            original = snapshot.read_bytes()
            snapshot.write_bytes(original + b'\n')
            with self.assertRaises(ValueError):
                verify_report(root)
            snapshot.write_bytes(original)
            write_json(root / "summary.json", {**summary, "total_investigations": 999})
            with self.assertRaises(ValueError):
                verify_report(root)


if __name__ == "__main__":
    unittest.main()
