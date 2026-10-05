import os
import time
import unittest

from sentinel.__main__ import load_log_schema
from sentinel.tools.common import TimeWindow
from sentinel.tools.logs import OpenSearchProvider


@unittest.skipUnless(os.getenv("SENTINEL_LIVE_TESTS") == "1", "requires a running demo and SENTINEL_LIVE_TESTS=1")
class LiveLogTests(unittest.TestCase):
    def setUp(self):
        schema_path = os.getenv("SENTINEL_LOG_SCHEMA")
        self.index = os.getenv("SENTINEL_LOG_INDEX")
        if not schema_path or not self.index:
            self.skipTest("inspect real mappings and set SENTINEL_LOG_SCHEMA and SENTINEL_LOG_INDEX")
        self.schema = load_log_schema(schema_path)
        self.provider = OpenSearchProvider(os.getenv("SENTINEL_OPENSEARCH_URL", "http://127.0.0.1:9200"))

    def test_configured_index_has_field_capabilities(self):
        result = self.provider.fields(self.index)
        self.assertTrue(result.indices)
        self.assertIn(self.schema.timestamp_field, {f.field for f in result.fields})

    def test_service_logs_are_ingested_and_normalized(self):
        end = time.time()
        service = os.getenv("SENTINEL_LIVE_SERVICE", "payment")
        result = self.provider.query_logs(service, TimeWindow(end - 900, end), index_pattern=self.index, schema=self.schema, limit=20)
        self.assertGreater(result.returned_count, 0, "No service logs: confirm the Collector exports logs and traffic is running")
        self.assertEqual(sum(group.sample_count for group in result.groups), result.returned_count)
