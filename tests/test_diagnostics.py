from dataclasses import asdict
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock

from sentinel.agent.contracts import Incident, ToolRequest
from sentinel.agent.diagnostics import DiagnosticTools
from sentinel.tools.http import TelemetryError
from sentinel.tools.logs import LogSchema
from sentinel.tools.metrics.prometheus import parse_result


class DiagnosticTests(unittest.TestCase):
    def tools(self, **kwargs):
        provider = Mock()
        provider.query_metrics.return_value = parse_result({"status": "success", "data": {
            "resultType": "vector", "result": [{"metric": {"status_code": "STATUS_CODE_ERROR"}, "value": [1500, "NaN"]}]}}, "fixture")
        traces = Mock()
        traces.services.return_value = ("payment", "checkout")
        return DiagnosticTools(Incident(service="payment", symptom="Errors", start=1200.0, end=1500.0),
                               metrics=provider, traces=traces, logs=Mock(), log_schema=LogSchema("service", "time", "body"),
                               log_index="otel-logs*", **kwargs)

    def test_semantic_metrics_construct_fixed_queries_and_preserve_missing_samples(self):
        tools = self.tools()
        result = tools.execute(ToolRequest(name="metrics", service="payment", period="baseline"))
        calls = tools.metrics.query_metrics.call_args_list
        self.assertEqual(len(calls), 3)
        self.assertIn('service_name="payment"', calls[0].args[0])
        self.assertIn('span_kind="SPAN_KIND_SERVER"', calls[0].args[0])
        self.assertIn("[300s]", calls[0].args[0])
        self.assertEqual(calls[0].kwargs["at"], 1200.0)
        self.assertIsNone(result[3]["calls"]["values"][0]["value"])
        self.assertIn("count_over_time", calls[2].args[0])
        self.assertIn("min by (status_code)", calls[2].args[0])
        self.assertEqual(calls[2].kwargs["at"], 1200.0)
        self.assertIsNone(result[3]["minimum_counter_samples"]["values"][0]["value"])
        with self.assertRaises(ValueError):
            tools.execute(ToolRequest(name="metrics", service='payment"} or vector(1)', period="incident"))

    def test_one_counter_sample_preserves_unknown_increase_instead_of_implying_health(self):
        tools = self.tools()
        empty = {"status": "success", "data": {"resultType": "vector", "result": []}}
        one = {"status": "success", "data": {"resultType": "vector", "result": [
            {"metric": {"status_code": "STATUS_CODE_ERROR"}, "value": [1500, "1"]}]}}
        tools.metrics.query_metrics.side_effect = [parse_result(empty, "increase"), parse_result(empty, "p95"),
                                                  parse_result(one, "samples")]
        _, _, raw, summary = tools.execute(ToolRequest(name="metrics", service="payment", period="incident"))
        self.assertEqual(summary["calls"]["values"], [])
        self.assertEqual(summary["minimum_counter_samples"]["values"][0]["value"], 1)
        self.assertIn("not requests", summary["minimum_counter_samples"]["interpretation"])
        self.assertIn("minimum_counter_samples", raw)

    def test_service_scope_only_expands_from_read_inventory(self):
        tools = self.tools()
        with self.assertRaises(ValueError):
            tools.validate(ToolRequest(name="traces", service="checkout", period="incident"))
        tools.execute(ToolRequest(name="services", service=None, period=None))
        tools.validate(ToolRequest(name="traces", service="checkout", period="incident"))
        with self.assertRaises(TelemetryError):
            tools.execute(ToolRequest(name="pods", service="payment", period=None))

    def test_source_is_allowlisted_bounded_and_explicit_about_excerpt_coverage(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "src").mkdir()
            lines = ["ordinary code" for _ in range(300)]
            lines[240] = 'getBooleanValue("someFeature", false);'
            (root / "src/service.py").write_text("\n".join(lines))
            tools = self.tools(source_root=root, source_files={"payment": ["src/service.py"]}, source_commit="pinned")
            _, _, raw, summary = tools.execute(ToolRequest(name="source", service="payment", period=None))
            record = summary["files"][0]
            self.assertIn("241:", record["excerpt"])
            self.assertFalse(record["complete"])
            self.assertEqual(record["total_lines"], 300)
            self.assertEqual(len(record["sha256"]), 64)
            outside = root.parent / "outside.py"
            with self.assertRaises(TelemetryError):
                tools._read_source("../outside.py", 1000)

    def test_runtime_configuration_is_current_data_without_scenario_state(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / "src/flagd/demo.flagd.json"
            path.parent.mkdir(parents=True)
            path.write_text(json.dumps({"flags": {"someFeature": {"state": "ENABLED", "defaultVariant": "on",
                                                                   "variants": {"off": False, "on": True}, "targeting": {}}}}))
            (root / "fault-state.json").write_text('{"ground_truth":"must never be read"}')
            tools = self.tools(source_root=root)
            result = tools.execute(ToolRequest(name="runtime_configuration", service=None, period=None))
            self.assertEqual(result[3]["flags"][0]["default_variant"], "on")
            self.assertNotIn("ground_truth", json.dumps(result))
            self.assertIn("historical", result[3]["limitation"])


if __name__ == "__main__":
    unittest.main()
