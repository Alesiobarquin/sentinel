import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import MagicMock, patch

from evals.benchmark import preparation_checks
from evals.corpus import capture_inventory, catalog, request_key
from scripts.evaluation_workload import InternationalCheckoutWorkload
from sentinel.agent.contracts import Incident, ToolRequest


def fixture(case):
    corpus = {"incident": {"start": 100.0, "end": 280.0}, "records": {}}
    for service in case["affected_services"]:
        for period in ["baseline", "incident"]:
            for name in ["metrics", "logs", "traces"]:
                key = request_key(ToolRequest(name=name, service=service, period=period))
                corpus["records"][key] = {"success": True, "raw": {"groups": [], "traces": []}}
    return corpus


class EvaluationPreparationTests(unittest.TestCase):
    def test_shipping_admission_uses_real_in_window_ship_order_span_not_missing_logs(self):
        case = next(c for c in catalog() if c["id"] == "shipping-slowdown")
        corpus = fixture(case)
        key = request_key(ToolRequest(name="traces", service="shipping", period="incident"))
        span = {"service": "shipping", "operation": "POST /ship-order", "start_time": 110.0,
                "duration_ms": 5010.0, "span_id": "fixture"}
        corpus["records"][key]["raw"]["traces"] = [{"spans": [span]}]
        result = preparation_checks(case, corpus)
        self.assertTrue(result["passed"])
        self.assertFalse(result["observations"]["fault_log_marker_observed"])
        span["operation"] = "POST /get-quote"
        self.assertFalse(preparation_checks(case, corpus)["passed"])
        span["operation"], span["start_time"] = "POST /ship-order", 90.0
        self.assertFalse(preparation_checks(case, corpus)["passed"])

    def test_healthy_control_rejects_an_error_in_earlier_payment_baseline(self):
        case = next(c for c in catalog() if c["id"] == "healthy-payment")
        corpus = fixture(case)
        for period in ["baseline", "incident"]:
            logs = request_key(ToolRequest(name="logs", service="payment", period=period))
            traces = request_key(ToolRequest(name="traces", service="payment", period=period))
            corpus["records"][logs]["raw"]["groups"] = [{"message_excerpt": "Transaction complete."}]
            corpus["records"][traces]["raw"]["traces"] = [{"spans": [{"service": "payment", "is_error": False}]}]
        self.assertTrue(preparation_checks(case, corpus)["passed"])
        self.assertNotIn("real_backend_marker_present", preparation_checks(case, corpus)["checks"])
        baseline = request_key(ToolRequest(name="traces", service="payment", period="baseline"))
        corpus["records"][baseline]["raw"]["traces"][0]["spans"][0]["is_error"] = True
        self.assertFalse(preparation_checks(case, corpus)["passed"])

    def test_missing_telemetry_control_requires_real_baseline_and_all_three_empty_sources(self):
        case = next(c for c in catalog() if c["id"] == "collector-coverage-gap")
        corpus = fixture(case)
        self.assertFalse(preparation_checks(case, corpus)["passed"])
        baseline_logs = request_key(ToolRequest(name="logs", service="payment", period="baseline"))
        baseline_traces = request_key(ToolRequest(name="traces", service="payment", period="baseline"))
        baseline_metrics = request_key(ToolRequest(name="metrics", service="payment", period="baseline"))
        corpus["records"][baseline_logs]["raw"]["groups"] = [{"message_excerpt": "Successful payment"}]
        corpus["records"][baseline_traces]["raw"]["traces"] = [{"spans": [{"service": "payment"}]}]
        corpus["records"][baseline_metrics]["raw"]["calls"] = {"series": [{"samples": [{"value": 4.0}]}]}
        result = preparation_checks(case, corpus)
        self.assertTrue(result["passed"])
        self.assertNotIn("real_backend_marker_present", result["checks"])
        incident_metrics = request_key(ToolRequest(name="metrics", service="payment", period="incident"))
        corpus["records"][incident_metrics]["raw"]["calls"] = {"series": [{"samples": [{"value": 1.0}]}]}
        self.assertFalse(preparation_checks(case, corpus)["passed"])

    def test_prior_inventory_is_observed_and_carries_no_injection_hint_to_model(self):
        tools = MagicMock()
        tools.execute.return_value = ("inventory", "jaeger", {"services": ["payment"]}, {"services": ["payment"]})
        incident = Incident(service="payment", symptom="Fixture", start=1000.0, end=1180.0)
        with tempfile.TemporaryDirectory() as directory, patch("evals.corpus.local_tools", return_value=tools):
            result = capture_inventory(incident, Path(directory))
            self.assertEqual(tools.execute.call_count, 1)
            self.assertEqual(result[1], "jaeger_prior_inventory")
            self.assertEqual(result[2]["services"], ["payment"])
            self.assertIn("observed_at", result[3])
            self.assertNotIn("collector", json.dumps(result))
            self.assertNotIn("stop", json.dumps(result))
            self.assertTrue((Path(directory) / "baseline-inventory-audit.jsonl").exists())

    def test_workload_uses_loopback_and_does_not_audit_request_body(self):
        with tempfile.TemporaryDirectory() as directory:
            workload = InternationalCheckoutWorkload(Path(directory))
            response = MagicMock()
            response.__enter__.return_value = response
            response.status, response.read.return_value = 200, b'{}'
            body = {"creditCard": {"cardNumber": "synthetic-private-value"}, "userId": "fixture-user"}
            with patch("scripts.evaluation_workload.urllib.request.urlopen", return_value=response) as urlopen:
                workload._request("/api/checkout", body)
            request = urlopen.call_args.args[0]
            self.assertEqual(request.full_url, "http://127.0.0.1:8080/api/checkout")
            self.assertEqual(request.get_header("Baggage"), "synthetic_request=true")
            self.assertEqual(json.loads(request.data), body)
            audit = (Path(directory) / "workload.jsonl").read_text()
            self.assertNotIn("creditCard", audit)
            self.assertNotIn("synthetic-private-value", audit)
            self.assertEqual(json.loads(audit)["status"], 200)

    def test_workload_records_bounded_response_failure(self):
        with tempfile.TemporaryDirectory() as directory:
            workload = InternationalCheckoutWorkload(Path(directory))
            response = MagicMock()
            response.__enter__.return_value = response
            response.status, response.read.return_value = 200, b'x' * 1_000_001
            with patch("scripts.evaluation_workload.urllib.request.urlopen", return_value=response):
                workload._request("/api/cart", {})
            self.assertEqual(json.loads((Path(directory) / "workload.jsonl").read_text())["error_type"], "ValueError")

    def test_workload_shutdown_surfaces_a_live_thread_or_driver_failure(self):
        workload = InternationalCheckoutWorkload(Path("unused-fixture"))
        workload.thread = MagicMock()
        workload.thread.is_alive.return_value = True
        with self.assertRaises(ValueError):
            workload.__exit__(None, None, None)
        self.assertTrue(workload.stop.is_set())
        workload.thread.is_alive.return_value = False
        workload.failure = "SyntheticDriverError"
        with self.assertRaises(ValueError):
            workload.__exit__(None, None, None)


if __name__ == "__main__":
    unittest.main()
