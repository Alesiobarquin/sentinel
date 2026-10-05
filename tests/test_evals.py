from contextlib import redirect_stdout
from io import StringIO
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from evals.grading import grade
from scripts import demo
from scripts.lab_scenarios import SCENARIOS
from sentinel.agent.contracts import Evidence, InvestigationStep, ToolRequest


class EvaluationTests(unittest.TestCase):
    def test_catalog_has_reproducible_truth_evidence_cleanup_and_unsafe_actions(self):
        catalog = json.loads(Path("evals/scenarios.json").read_text())
        self.assertEqual({s["id"] for s in catalog["scenarios"]}, set(SCENARIOS))
        for scenario in catalog["scenarios"]:
            fault = SCENARIOS[scenario["id"]]
            self.assertEqual((scenario["expected_flag"], scenario["expected_variant"]), (fault.flag, fault.variant))
            self.assertTrue(scenario["expected_evidence"])
            self.assertTrue(scenario["unsafe_actions"])
            self.assertEqual(scenario["cleanup"], "make lab-reset")

    def test_all_fault_helpers_restore_the_exact_prior_setting(self):
        for scenario, fault in SCENARIOS.items():
            with self.subTest(scenario=scenario), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                path = root / "src/flagd/demo.flagd.json"
                path.parent.mkdir(parents=True)
                path.write_text(json.dumps({"flags": {fault.flag: {"state": "ENABLED", "defaultVariant": "off", "variants": {"off": 0, fault.variant: fault.value}}}}))
                with patch.object(demo, "SOURCE", root), patch.object(demo, "STATE", root / "state.json"), patch.object(demo, "fetch_demo"), redirect_stdout(StringIO()):
                    demo.inject_fault(scenario)
                    self.assertEqual(json.loads(path.read_text())["flags"][fault.flag]["defaultVariant"], fault.variant)
                    demo.reset_fault()
                    self.assertEqual(json.loads(path.read_text())["flags"][fault.flag]["defaultVariant"], "off")

    def test_keyword_signal_is_never_promoted_to_correctness(self):
        scenario = json.loads(Path("evals/scenarios.json").read_text())["scenarios"][0]
        step = InvestigationStep.model_validate({
            "action": "diagnose", "reason": "Fixture", "tool": None,
            "hypotheses": [{"name": "Fixture", "explanation": "Synthetic", "confidence": 0.5, "supporting_evidence": [], "contradicting_evidence": [], "status": "active"}],
            "diagnosis": {"root_cause": "paymentFailure is NOT the cause", "confidence": 0.5, "evidence_ids": ["ev_1", "ev_2"],
                          "affected_services": ["payment"], "recommended_remediation": "Restart it", "remediation_kind": "request_restart", "limitations": ["Fixture"]}})
        evidence = [Evidence(id="ev_1", run_id="fixture", kind="log", source="fixture", observed_at=1.0,
                             tool=ToolRequest(name="logs", service="payment", period="incident"), success=True, summary={}, payload_file="x"),
                    Evidence(id="ev_2", run_id="fixture", kind="configuration", source="fixture", observed_at=1.0,
                             tool=ToolRequest(name="runtime_configuration", service=None, period=None), success=True,
                             summary={"flags": [{"name": "paymentFailure", "default_variant": "100%"}]}, payload_file="y")]
        result = grade(step, evidence, scenario)
        self.assertTrue(result["cause_mentions_expected_flag"])
        self.assertTrue(result["requires_manual_causal_review"])
        self.assertFalse(result["remediation_kind_acceptable"])
        self.assertNotIn("correct", result)
        self.assertNotIn("accuracy", result)

    def test_an_exercise_cannot_reset_another_exercises_fault(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / "src/flagd/demo.flagd.json"
            path.parent.mkdir(parents=True)
            path.write_text(json.dumps({"flags": {"paymentFailure": {"state": "ENABLED", "defaultVariant": "off", "variants": {"off": 0, "100%": 1}}}}))
            with patch.object(demo, "SOURCE", root), patch.object(demo, "STATE", root / "state.json"), patch.object(demo, "fetch_demo"), redirect_stdout(StringIO()):
                demo.inject_fault("payment-failure", owner_id="first-exercise")
                demo.reset_fault(owner_id="second-exercise")
                self.assertTrue(demo.STATE.exists())
                self.assertEqual(json.loads(path.read_text())["flags"]["paymentFailure"]["defaultVariant"], "100%")
                demo.reset_fault(owner_id="first-exercise")
                self.assertFalse(demo.STATE.exists())
                self.assertEqual(json.loads(path.read_text())["flags"]["paymentFailure"]["defaultVariant"], "off")


if __name__ == "__main__":
    unittest.main()
