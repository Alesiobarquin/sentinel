from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from evals.corpus import CorpusTools, LabCase, catalog, cleanup, digest, request_key
from evals.scoring import distribution, fraction, summarize, validate_review
from sentinel.agent.context import build_context
from sentinel.agent.contracts import Evidence, Incident, ToolRequest
from sentinel.tools.http import TelemetryError


def packet(run="fixture", status="diagnosed", scenario="fault", strategy="structured"):
    return {"scenario_id": scenario, "strategy": strategy, "repeat": 1, "corpus_sha256": "same-capture",
            "configuration_sha256": "same-config", "packet_sha256": "fixture-hash",
            "result": {"run_id": run, "status": status, "diagnosis": {"remediation_executed": False} if status == "diagnosed" else None,
                       "model_calls": 2, "tool_calls": 2, "latency_ms": 1000, "input_tokens": 100,
                       "output_tokens": 50, "usage_unknown": False, "approximate_api_cost_usd": None},
            "decisions": [{"valid": True}], "tool_requests": [{"name": "logs"}]}


def review(p, outcome="correct"):
    return {"run_id": p["result"]["run_id"], "packet_sha256": p["packet_sha256"],
            "reviewer": "Codex-assisted semantic review", "rubric_version": 1, "root_cause": outcome,
            "appropriate_abstention": False, "claims_supported": True if p["result"]["status"] == "diagnosed" else None,
            "important_evidence_retrieved": ["Observed logs"], "unsafe_recommendation": False,
            "within_advisory_scope": True, "unnecessary_tool_calls": 0,
            "notes": "Synthetic scoring fixture, not an AI evaluation.", "claim_checks": [{"claim": "Fixture", "supported": True}]}


def cases():
    return {name: {"expected_outcome": outcome, "expected_evidence": ["Observed logs"], "required_tools": ["logs"]}
            for name, outcome in [("fault", "diagnose"), ("control", "abstain")]}


class BenchmarkTests(unittest.TestCase):
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
        self.assertEqual(summarize([normal, baseline], reviews, cases())["comparison"]["pairs"], 1)
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


if __name__ == "__main__":
    unittest.main()
