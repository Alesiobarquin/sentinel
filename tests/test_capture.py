import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from scripts import capture
from sentinel.tools.common import TimeWindow
from sentinel.tools.http import TelemetryError
from sentinel.tools.logs.opensearch import LogQueryResult
from sentinel.tools.metrics.prometheus import MetricQueryResult
from sentinel.tools.traces.jaeger import DependencyResult, TraceQueryResult


class CaptureTests(unittest.TestCase):
    def test_failed_signal_preserves_independent_evidence_and_audit(self):
        window = TimeWindow(100, 220)
        schema_text = (capture.ROOT / "infra/docker/log-schema.json").read_text()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "infra/docker").mkdir(parents=True)
            (root / "infra/docker/log-schema.json").write_text(schema_text)
            (root / "infra/docker/demo.lock.json").write_text(json.dumps({"version": "test", "commit": "test"}))
            flags = root / ".cache/demo/source/src/flagd/demo.flagd.json"
            flags.parent.mkdir(parents=True)
            flags.write_text(json.dumps({"flags": {"paymentFailure": {"defaultVariant": "off"}}}))
            output = root / "evidence.json"
            with patch.object(capture, "ROOT", root), patch.object(capture, "PrometheusProvider") as metrics, \
                    patch.object(capture, "JaegerProvider") as traces, patch.object(capture, "OpenSearchProvider") as logs:
                metrics.return_value.query_metrics.side_effect = [
                    TelemetryError("Metrics transport unavailable"),
                    MetricQueryResult("prometheus", capture.LATENCY_QUERY, "vector", (), ()),
                ]
                traces.return_value.services.return_value = ("payment",)
                traces.return_value.query_traces.return_value = TraceQueryResult("jaeger", "payment", window, 10, False, ())
                traces.return_value.get_service_dependencies.return_value = DependencyResult("jaeger", window, ())
                logs.return_value.query_logs.return_value = LogQueryResult("opensearch", "otel-logs*", "payment", window, 100, 0, "eq", 0, True, ())
                result = capture.capture("incident", window, output)

            self.assertFalse(result["complete"])
            self.assertEqual(set(result["errors"]), {"calls"})
            self.assertEqual(result["errors"]["calls"]["type"], "TelemetryError")
            self.assertNotIn("calls", result["data"])
            self.assertEqual(result["data"]["services"], ("payment",))
            self.assertEqual(result["data"]["logs"]["returned_count"], 0)
            self.assertIn("traces", result["data"])
            self.assertIn("dependencies", result["data"])
            self.assertFalse(json.loads(output.read_text())["complete"])
            events = [json.loads(line) for line in (root / "var/audit/tool-calls.jsonl").read_text().splitlines()]
            finished = [event for event in events if event["event"] == "tool_finished"]
            self.assertEqual(len(finished), 6)
            self.assertEqual(sum(not event["success"] for event in finished), 1)

    def test_existing_capture_is_preserved_without_reading_backends(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "evidence.json"
            output.write_text("original evidence\n")
            with patch.object(capture, "PrometheusProvider") as metrics, \
                    patch.object(capture, "JaegerProvider") as traces, patch.object(capture, "OpenSearchProvider") as logs:
                with self.assertRaisesRegex(ValueError, "already exists"):
                    capture.capture("incident", TimeWindow(100, 220), output)
                metrics.assert_not_called()
                traces.assert_not_called()
                logs.assert_not_called()
            self.assertEqual(output.read_text(), "original evidence\n")
