import os
import unittest

from sentinel.tools.metrics import PrometheusProvider, READINESS_QUERY


@unittest.skipUnless(os.getenv("SENTINEL_LIVE_TESTS") == "1", "requires a running demo and SENTINEL_LIVE_TESTS=1")
class LiveMetricsTests(unittest.TestCase):
    def test_prometheus_has_active_telemetry_samples(self):
        provider = PrometheusProvider(os.getenv("SENTINEL_PROMETHEUS_URL", "http://127.0.0.1:9090"))
        result = provider.query_metrics(READINESS_QUERY)
        self.assertEqual(result.result_type, "vector")
        self.assertTrue(result.series, "Prometheus has no active telemetry samples yet")
        self.assertGreater(result.series[0].samples[0].value, 0)

    def test_demo_span_metrics_are_ingested(self):
        provider = PrometheusProvider(os.getenv("SENTINEL_PROMETHEUS_URL", "http://127.0.0.1:9090"))
        self.assertIn("traces_span_metrics_calls_total", provider.metric_names())
