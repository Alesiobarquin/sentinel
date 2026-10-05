import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch

from sentinel.tools.audit import ToolRecorder


class AuditTests(unittest.TestCase):
    def test_success_pairs_events_without_dumping_result(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "audit.jsonl"
            result = ToolRecorder(path).invoke("query_metrics", {"query": "up"}, lambda: {"private": "telemetry"}, lambda _: {"count": 1})
            events = [json.loads(line) for line in path.read_text().splitlines()]
        self.assertEqual(result, {"private": "telemetry"})
        self.assertEqual([e["event"] for e in events], ["tool_started", "tool_finished"])
        self.assertEqual(events[0]["call_id"], events[1]["call_id"])
        self.assertEqual(events[0]["arguments"], {"query": "up"})
        self.assertEqual(events[1]["result_summary"], {"count": 1})
        self.assertTrue(events[1]["success"])
        self.assertGreaterEqual(events[1]["latency_ms"], 0)
        self.assertNotIn("private", json.dumps(events))

    def test_failure_is_recorded_and_propagated(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "audit.jsonl"
            def fail():
                raise RuntimeError("private backend response")
            with self.assertRaises(RuntimeError):
                ToolRecorder(path).invoke("query_metrics", {}, fail, lambda _: {})
            events = [json.loads(line) for line in path.read_text().splitlines()]
        self.assertFalse(events[1]["success"])
        self.assertEqual(events[1]["error_type"], "RuntimeError")
        self.assertNotIn("private backend response", json.dumps(events))

    def test_unwritable_audit_prevents_the_tool_call(self):
        action = Mock()
        recorder = ToolRecorder(Path("unused.jsonl"))
        with patch.object(recorder, "_write", side_effect=PermissionError):
            with self.assertRaises(PermissionError):
                recorder.invoke("query_metrics", {}, action, lambda _: {})
        action.assert_not_called()

    def test_summary_failure_is_recorded_as_a_failed_tool_call(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "audit.jsonl"
            with self.assertRaises(ValueError):
                ToolRecorder(path).invoke("query_logs", {}, lambda: [], Mock(side_effect=ValueError("invalid summary")))
            events = [json.loads(line) for line in path.read_text().splitlines()]
        self.assertEqual(len(events), 2)
        self.assertFalse(events[1]["success"])
        self.assertEqual(events[1]["error_type"], "ValueError")
