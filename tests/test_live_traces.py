import os
import time
import unittest

from sentinel.tools.common import TimeWindow
from sentinel.tools.traces import JaegerProvider


@unittest.skipUnless(os.getenv("SENTINEL_LIVE_TESTS") == "1", "requires a running demo and SENTINEL_LIVE_TESTS=1")
class LiveTraceTests(unittest.TestCase):
    def test_demo_has_services_and_payment_traces(self):
        provider = JaegerProvider(os.getenv("SENTINEL_JAEGER_URL", "http://127.0.0.1:8080/jaeger/ui"))
        service = os.getenv("SENTINEL_LIVE_SERVICE", "payment")
        self.assertIn(service, provider.services(), "Allow checkout traffic to warm up")
        end = time.time()
        result = provider.query_traces(service, TimeWindow(end - 900, end), limit=5)
        self.assertTrue(result.traces, "No recent traces: confirm checkout/payment traffic")
        self.assertTrue(all(service in t.services for t in result.traces))

    def test_dependency_endpoint_returns_a_valid_graph(self):
        provider = JaegerProvider(os.getenv("SENTINEL_JAEGER_URL", "http://127.0.0.1:8080/jaeger/ui"))
        end = time.time()
        result = provider.get_service_dependencies(TimeWindow(end - 900, end))
        self.assertEqual(result.source, "jaeger")
        # An empty graph does not establish that services made no calls.
        self.assertTrue(all(e.call_count >= 0 for e in result.edges))
