import unittest
from unittest.mock import Mock

from sentinel.tools.http import TelemetryError
from sentinel.tools.metrics.prometheus import PrometheusProvider, parse_result


def response(kind, result, **extra):
    return {"status": "success", "data": {"resultType": kind, "result": result}, **extra}


class MetricsTests(unittest.TestCase):
    def test_vector_preserves_labels_and_timestamp(self):
        result = parse_result(response("vector", [{"metric": {"service_name": "payment"}, "value": [100, "1.5"]}]), "up")
        self.assertEqual(result.series[0].labels, {"service_name": "payment"})
        self.assertEqual(result.series[0].samples[0].timestamp, 100)
        self.assertEqual(result.series[0].samples[0].value, 1.5)

    def test_range_preserves_sample_order_and_missing_values(self):
        result = parse_result(response("matrix", [{"metric": {}, "values": [[100, "NaN"], [115, "+Inf"], [130, "0"]]}]), "latency")
        self.assertEqual([s.value for s in result.series[0].samples], [None, None, 0])
        self.assertEqual([s.timestamp for s in result.series[0].samples], [100, 115, 130])

    def test_scalar_is_a_series_without_labels(self):
        result = parse_result(response("scalar", [123, "42"]), "42")
        self.assertEqual(result.series[0].labels, {})
        self.assertEqual(result.series[0].samples[0].value, 42)

    def test_empty_result_is_not_invented_health_evidence(self):
        result = parse_result(response("vector", [], warnings=["partial data"]), "up")
        self.assertEqual(result.series, ())
        self.assertEqual(result.warnings, ("partial data",))

    def test_malformed_results_fail_instead_of_returning_zero(self):
        for payload in [
            {"status": "error", "error": "private backend detail"},
            response("string", [100, "text"]),
            response("vector", [{"metric": {}, "histogram": [100, {}]}]),
            response("vector", [{"metric": [], "value": [100, "1"]}]),
            response("vector", [{"metric": {}, "value": [100, True]}]),
            response("matrix", [{"metric": {}, "values": [["NaN", "1"]]}]),
            response("vector", [], warnings="invalid"),
        ]:
            with self.subTest(payload=payload), self.assertRaises(TelemetryError):
                parse_result(payload, "up")

    def test_invalid_queries_never_reach_transport(self):
        client = Mock()
        provider = PrometheusProvider(client=client)
        for query, parameters in [
            ("", {}), ("q" * 4097, {}),
            ("up", {"start": 10}),
            ("up", {"start": 20, "end": 10}),
            ("up", {"start": 0, "end": 21601}),
            ("up", {"start": 0, "end": 10000, "step": 1}),
            ("up", {"start": 0, "end": 30, "step": 0}),
            ("up", {"start": 0, "end": float("inf")}),
            ("up", {"start": 0, "end": 30, "at": 15}),
            ("up", {"at": float("nan")}),
            ("up", {"at": -1}),
        ]:
            with self.subTest(parameters=parameters), self.assertRaises(ValueError):
                provider.query_metrics(query, **parameters)
        client.get.assert_not_called()

    def test_range_uses_explicit_window_and_prometheus_timeout(self):
        client = Mock()
        client.get.return_value = response("matrix", [])
        result = PrometheusProvider(client=client).query_metrics("up", start=0, end=30, step=15)
        client.get.assert_called_once_with("/api/v1/query_range", {"query": "up", "timeout": "8s", "start": 0, "end": 30, "step": 15})
        self.assertEqual((result.start, result.end, result.step), (0, 30, 15))

    def test_instant_time_zero_is_not_lost(self):
        client = Mock()
        client.get.return_value = response("vector", [])
        PrometheusProvider(client=client).query_metrics("up", at=0)
        client.get.assert_called_once_with("/api/v1/query", {"query": "up", "timeout": "8s", "time": 0})

    def test_range_rejects_wrong_response_type(self):
        client = Mock()
        client.get.return_value = response("scalar", [0, "1"])
        with self.assertRaises(TelemetryError):
            PrometheusProvider(client=client).query_metrics("up", start=0, end=30)

    def test_metric_discovery_rejects_malformed_data(self):
        client = Mock()
        provider = PrometheusProvider(client=client)
        client.get.return_value = {"status": "success", "data": ["b", "a", "a"]}
        self.assertEqual(provider.metric_names(), ("a", "b"))
        client.get.return_value = {"status": "success", "data": [42]}
        with self.assertRaises(TelemetryError):
            provider.metric_names()
