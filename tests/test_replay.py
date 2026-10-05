"""Publication safeguards use offline artifacts, never live model calls."""

from dataclasses import asdict
import json
from pathlib import Path
import tempfile
import unittest

from sentinel.agent.contracts import Incident, Usage
from sentinel.agent.provider import ModelReply
from sentinel.agent.runner import InvestigationRunner
from sentinel.replay import Replay, build_replay, public_summary, replay_records


class Model:
    model, billing_mode = "offline-fixture", "chatgpt"

    def __init__(self):
        self.call = 0

    def step(self, instructions, context, budget, *, timeout):
        self.call += 1
        hypothesis = {"name": "Synthetic cause", "explanation": "Offline fixture", "confidence": 0.5,
                      "supporting_evidence": [], "contradicting_evidence": [], "status": "active"}
        decision = {"action": "read", "reason": "Read logs", "hypotheses": [hypothesis],
                    "tool": {"name": "logs", "service": "payment", "period": "incident"}, "diagnosis": None}
        if self.call == 2:
            decision.update(action="diagnose", reason="Fixture diagnosis", tool=None, diagnosis={
                "root_cause": "Synthetic cause", "confidence": 0.5, "evidence_ids": ["ev_001", "ev_002"],
                "affected_services": ["payment"], "recommended_remediation": "Request review",
                "remediation_kind": "request_config_revert", "limitations": ["Offline fixture"]})
        return ModelReply(decision, Usage(input_tokens=100, output_tokens=50), "fixture", self.model, 1.0)


class Tools:
    def validate(self, request):
        pass

    def execute(self, request):
        if request.name == "services":
            raw = {"services": ["payment"], "authorization": "private-field"}
            return "inventory", "jaeger", raw, raw
        raw = {"service": "payment", "window": {"start": 1000.0, "end": 1180.0},
               "matched_count": 1, "matched_count_relation": "eq", "returned_count": 1,
               "sample_complete": True, "omitted_groups": 0, "record_examples_per_group": 3,
               "groups": [{"severity": "warn", "message_excerpt": "Synthetic warning", "message_truncated": False,
                           "message_sha256": "a" * 64, "sample_count": 1, "first_seen": 1010.0,
                           "last_seen": 1010.0, "records": [{"timestamp": 1010.0, "trace_id": "b" * 32,
                                                           "document_id": "private-document", "index": "private-index"}]}]}
        return "log", "opensearch", raw, raw


class ReplayTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        root = Path(self.temp.name)
        incident = Incident(service="payment", symptom="Synthetic fixture errors", start=1000.0, end=1180.0)
        runner = InvestigationRunner(Model(), Tools(), output_root=root / "runs")
        self.result = runner.run(incident)
        self.run = runner.directory
        self.exercise = root / "exercise"
        self.exercise.mkdir()
        observation = {"estimated_server_error_calls": 0.0, "selected_service_error_spans": 0,
                       "sampled_log_groups": 1, "sampled_warning_or_error_logs": 0, "all_reads_succeeded": True}
        self.write(self.exercise / "agent-result.json", asdict(self.result))
        self.write(self.exercise / "exercise-report.json", {"agent_result": str(self.exercise / "agent-result.json"),
            "baseline": observation, "recovery": observation, "injected_at": 990.0, "reset_at": 1200.0,
            "remediation_executed_by_agent": False, "cleanup_performed_by_developer_exercise": True,
            "manual_causal_review_required": True})
        self.review = {"run_id": self.result.run_id, "acknowledged_on": "2026-10-05",
                       "checkpoint_acknowledged": True, "causal_review": "accepted", "expected_cause": "Synthetic cause",
                       "note": "Offline publication fixture", "limitations": ["Synthetic test"], "source_hashes": {}}
        self.snapshot()

    def write(self, path, value):
        path.write_text(json.dumps(value))

    def snapshot(self):
        self.review["source_hashes"] = replay_records(self.run, self.exercise)[0].hashes

    def export(self):
        return build_replay(self.run, self.exercise, self.review)

    def test_preserves_measurements_and_citations_without_private_fields(self):
        payload = self.export()
        self.assertEqual(payload["diagnosis"]["evidence_ids"], ["ev_001", "ev_002"])
        self.assertEqual((payload["input_tokens"], payload["output_tokens"]), (200, 100))
        self.assertEqual([s["evidence_id"] for s in payload["steps"]], ["ev_001", "ev_002", None])
        self.assertFalse(payload["remediation_executed_by_agent"])
        self.assertFalse(payload["diagnosis"]["remediation_execution_available"])
        text = json.dumps(payload)
        for excluded in ("private-field", "private-document", "private-index", "payload_file", "directory"):
            self.assertNotIn(excluded, text)

    def test_checkpoint_acknowledgment_is_required(self):
        self.review["checkpoint_acknowledged"] = False
        with self.assertRaises(ValueError):
            self.export()

    def test_failed_investigation_cannot_be_published_as_success(self):
        result = asdict(self.result)
        result.update(status="failed", diagnosis=None)
        self.write(self.run / "result.json", result)
        with self.assertRaisesRegex(ValueError, "Failed or inconclusive"):
            self.export()

    def test_records_changed_after_review_are_rejected(self):
        with (self.run / "events.jsonl").open("a") as stream:
            stream.write("\n")
        with self.assertRaisesRegex(ValueError, "reviewed snapshot"):
            self.export()

    def test_future_evidence_citations_are_rejected(self):
        path = self.run / "decision-01.json"
        decision = json.loads(path.read_text())
        decision["hypotheses"][0]["supporting_evidence"] = ["ev_002"]
        self.write(path, decision)
        self.snapshot()
        with self.assertRaisesRegex(ValueError, "unavailable"):
            self.export()

    def test_secret_in_selected_text_is_rejected_without_normalization(self):
        path = self.run / "events.jsonl"
        events = [json.loads(line) for line in path.read_text().splitlines()]
        for event in events:
            if event["event"] == "evidence" and event["kind"] == "log":
                event["summary"]["groups"][0]["message_excerpt"] = "sk-" + "x" * 40
        path.write_text("\n".join(json.dumps(e) for e in events) + "\n")
        self.snapshot()
        with self.assertRaisesRegex(ValueError, "private data"):
            self.export()

    def test_nested_trace_attributes_are_allowlisted(self):
        result = public_summary("trace", {"service": "payment", "traces": [{"trace_id": "a" * 32,
            "spans": [{"service": "payment", "is_error": True,
                       "attributes": {"error": True, "server.address": "private-address", "card.number": "private-card"}}]}]})
        self.assertEqual(result["traces"][0]["spans"][0]["attributes"], {"error": True})

    def test_unreviewed_source_paths_are_rejected(self):
        with self.assertRaisesRegex(ValueError, "allowlist"):
            public_summary("source_code", {"commit": "a" * 40, "files": [{"file": "../../credentials"}]})

    def test_new_evidence_kinds_need_publication_schema(self):
        with self.assertRaisesRegex(ValueError, "publication schema"):
            public_summary("arbitrary", {})

    def test_public_bundle_validation_detects_usage_tampering(self):
        payload = self.export()
        payload["input_tokens"] += 1
        with self.assertRaisesRegex(ValueError, "usage/counts"):
            Replay.model_validate(payload)

    def test_checked_in_real_bundle_retains_coverage(self):
        path = Path(__file__).resolve().parents[1] / "apps/web/public/investigation.json"
        replay = Replay.model_validate_json(path.read_bytes())
        metrics = next(e for e in replay.evidence if e.id == "ev_002")
        traces = next(e for e in replay.evidence if e.id == "ev_004")
        self.assertEqual(metrics.summary["minimum_counter_samples"]["values"][0]["value"], 3.0)
        self.assertTrue(traces.summary["limit_reached"])
        self.assertEqual(traces.summary["omitted_traces"], 3)
        self.assertIn("interpretation", metrics.summary)


if __name__ == "__main__":
    unittest.main()
