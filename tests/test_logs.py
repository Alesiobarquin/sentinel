"""Explicit synthetic mappings and documents; not the pinned demo's schema."""

from copy import deepcopy
from dataclasses import replace
from datetime import datetime, timezone
import unittest
from unittest.mock import Mock

from sentinel.tools.common import TimeWindow
from sentinel.tools.http import TelemetryError
from sentinel.tools.logs import LogSchema, OpenSearchProvider

START = 1_700_000_000
WINDOW = TimeWindow(START, START + 60)
SCHEMA = LogSchema(
    "resource.attributes.service.name.keyword", "@timestamp", "body",
    severity_field="severityText.keyword", trace_id_field="trace_id",
)
TRACE = "1234567890abcdef1234567890abcdef"


def fields_fixture():
    kinds = {
        SCHEMA.service_field: "keyword", SCHEMA.timestamp_field: "date", SCHEMA.body_field: "text",
        SCHEMA.severity_field: "keyword", SCHEMA.trace_id_field: "keyword",
    }
    return {
        "indices": ["logs-1", "logs-2"],
        "fields": {name: {kind: {"type": kind, "searchable": True, "aggregatable": kind != "text"}} for name, kind in kinds.items()},
    }


def document(document_id="a", *, index="logs-1", message="synthetic error", level="ERROR", at=START + 1):
    return {
        "_index": index, "_id": document_id,
        "_source": {
            "resource": {"attributes": {"service.name": "payment"}},
            "@timestamp": datetime.fromtimestamp(at, timezone.utc).isoformat(),
            "body": message, "severityText": level, "trace_id": TRACE,
        },
    }


def response(documents, *, total=None, relation="eq"):
    return {
        "timed_out": False,
        "_shards": {"total": 2, "successful": 2, "skipped": 0, "failed": 0},
        "hits": {"total": {"value": len(documents) if total is None else total, "relation": relation}, "hits": documents},
    }


def setup_provider(documents, **response_options):
    client = Mock()
    client.get.return_value = fields_fixture()
    client.post.return_value = response(documents, **response_options)
    return OpenSearchProvider(client=client), client


def query(provider, **options):
    return provider.query_logs("payment", WINDOW, index_pattern="logs-*", schema=SCHEMA, **options)


class LogTests(unittest.TestCase):
    def test_exact_grouping_preserves_document_identity_and_trace_correlation(self):
        documents = [document("a"), document("a", index="logs-2", at=START + 2), document("b", level="WARN")]
        provider, _ = setup_provider(documents)
        result = query(provider)
        self.assertEqual(result.returned_count, 3)
        self.assertTrue(result.sample_complete)
        self.assertEqual(len(result.groups), 2)
        group = result.groups[0]
        self.assertEqual(group.sample_count, 2)
        self.assertEqual(group.severity, "ERROR")
        self.assertEqual(group.first_seen, START + 1)
        self.assertEqual(group.last_seen, START + 2)
        self.assertEqual({(r.index, r.document_id) for r in group.records}, {("logs-1", "a"), ("logs-2", "a")})
        self.assertEqual(group.records[0].trace_id, TRACE)

    def test_query_is_read_only_filtered_and_bounded(self):
        provider, client = setup_provider([document()])
        query(provider, limit=5, severity="ERROR")
        self.assertEqual(client.get.call_args.args[0], "/logs-*/_field_caps")
        self.assertEqual(client.get.call_args.args[1]["include_unmapped"], "true")
        path, body, parameters = client.post.call_args.args
        self.assertEqual(path, "/logs-*/_search")
        self.assertEqual(body["size"], 5)
        self.assertEqual(body["timeout"], "8s")
        self.assertEqual(body["track_total_hits"], 10000)
        self.assertEqual(body["query"]["bool"]["filter"], [
            {"term": {SCHEMA.service_field: "payment"}},
            {"range": {"@timestamp": {"gte": WINDOW.iso_start, "lt": WINDOW.iso_end}}},
            {"term": {SCHEMA.severity_field: "ERROR"}},
        ])
        self.assertEqual(body["_source"], list(SCHEMA.source_fields))
        self.assertNotIn("resource.attributes.service.name.keyword", body["_source"])
        self.assertEqual(parameters["allow_partial_search_results"], "false")

    def test_sample_counts_are_distinct_from_matching_population(self):
        for total, relation in [(100, "eq"), (10000, "gte")]:
            provider, _ = setup_provider([document("a"), document("b")], total=total, relation=relation)
            result = query(provider, limit=2)
            self.assertEqual(result.matched_count, total)
            self.assertEqual(result.matched_count_relation, relation)
            self.assertFalse(result.sample_complete)
            self.assertEqual(result.groups[0].sample_count, 2)

    def test_empty_results_are_empty_and_not_a_health_claim(self):
        provider, _ = setup_provider([])
        result = query(provider)
        self.assertEqual(result.groups, ())
        self.assertEqual(result.matched_count, 0)
        self.assertTrue(result.sample_complete)

    def test_timeouts_partial_shards_and_early_termination_fail(self):
        partial = []
        for key, value in [("timed_out", True), ("terminated_early", True), ("timed_out", "false")]:
            item = response([document()])
            item[key] = value
            partial.append(item)
        for total, successful, failed in [(2, 1, 1), (2, 1, 0), (0, 0, 0)]:
            item = response([document()])
            item["_shards"] = {"total": total, "successful": successful, "failed": failed}
            partial.append(item)
        for payload in partial:
            provider, client = setup_provider([])
            client.post.return_value = payload
            with self.subTest(payload=payload), self.assertRaises(TelemetryError):
                query(provider)

    def test_schema_validation_rejects_missing_conflicting_and_unsearchable_fields(self):
        variants = []
        for kind in ["text", "unmapped"]:
            caps = fields_fixture()
            caps["fields"][SCHEMA.service_field][kind] = {"type": kind, "searchable": True, "aggregatable": False}
            variants.append(caps)
        missing = fields_fixture()
        del missing["fields"][SCHEMA.timestamp_field]
        variants.append(missing)
        unsearchable = fields_fixture()
        unsearchable["fields"][SCHEMA.service_field]["keyword"]["non_searchable_indices"] = ["logs-2"]
        variants.append(unsearchable)
        no_indices = fields_fixture()
        no_indices["indices"] = []
        variants.append(no_indices)
        for caps in variants:
            provider, client = setup_provider([])
            client.get.return_value = caps
            with self.subTest(caps=caps), self.assertRaises(TelemetryError):
                query(provider)
            client.post.assert_not_called()

    def test_malformed_or_mismatched_documents_are_rejected(self):
        bad = []
        for field, value in [
            ("body", {}), ("severityText", 7), ("trace_id", "not-a-trace"),
            ("@timestamp", "2023-11-14T22:13:21"), ("@timestamp", WINDOW.iso_end),
            ("@timestamp", 1_700_000_001),
        ]:
            item = document()
            item["_source"][field] = value
            bad.append(item)
        wrong_service = document()
        wrong_service["_source"]["resource"]["attributes"]["service.name"] = "checkout"
        bad.append(wrong_service)
        ambiguous = document()
        ambiguous["_source"]["resource"]["attributes"]["service"] = {"name": "payment"}
        bad.append(ambiguous)
        bad.append(document(index="unselected-index"))
        for item in bad:
            provider, _ = setup_provider([item])
            with self.subTest(item=item), self.assertRaises(TelemetryError):
                query(provider)
        provider, _ = setup_provider([document(), document()])
        with self.assertRaises(TelemetryError):
            query(provider)

    def test_timestamp_encodings_and_source_override_are_explicit(self):
        for encoding, value in [("epoch_millis", (START + 1) * 1000), ("epoch_seconds", START + 1)]:
            provider, client = setup_provider([])
            item = document()
            item["_source"]["@timestamp"] = value
            item["_source"]["service"] = "payment"
            del item["_source"]["resource"]
            client.post.return_value = response([item])
            result = provider.query_logs("payment", WINDOW, index_pattern="logs-*", schema=replace(
                SCHEMA, timestamp_encoding=encoding, service_source_field="service",
            ))
            self.assertEqual(result.groups[0].first_seen, START + 1)
            self.assertIn("service", client.post.call_args.args[1]["_source"])

    def test_excerpts_do_not_merge_different_full_messages(self):
        first, second = "x" * 800 + "a", "x" * 800 + "b"
        provider, _ = setup_provider([document("a", message=first), document("b", message=second)])
        result = query(provider)
        self.assertEqual(len(result.groups), 2)
        self.assertTrue(all(g.message_truncated for g in result.groups))
        self.assertEqual(result.groups[0].message_excerpt, result.groups[1].message_excerpt)
        self.assertNotEqual(result.groups[0].message_sha256, result.groups[1].message_sha256)

    def test_field_discovery_preserves_mixed_types_and_handles_null_indices(self):
        provider, client = setup_provider([])
        caps = fields_fixture()
        caps["fields"]["other"] = {
            "text": {"type": "text", "searchable": False, "aggregatable": False, "non_searchable_indices": None},
            "keyword": {"type": "keyword", "searchable": True, "aggregatable": True},
        }
        client.get.return_value = caps
        result = provider.fields("logs-*")
        field = next(f for f in result.fields if f.field == "other")
        self.assertEqual([t.name for t in field.types], ["keyword", "text"])
        self.assertFalse(field.types[1].searchable)
        client.get.return_value = {"indices": [], "fields": {"bad": {"text": {"searchable": "true"}}}}
        with self.assertRaises(TelemetryError):
            provider.fields("logs-*")

    def test_invalid_arguments_do_not_reach_transport(self):
        for options in [{"limit": 0}, {"limit": 101}, {"limit": True}, {"severity": ""}, {"severity": "ERROR\n"}]:
            provider, client = setup_provider([])
            with self.subTest(options=options), self.assertRaises(ValueError):
                query(provider, **options)
            client.get.assert_not_called()
            client.post.assert_not_called()
        for index in ["*", "logs/../_delete", "logs,users", "logs?size=500", "Logs"]:
            provider, client = setup_provider([])
            with self.subTest(index=index), self.assertRaises(ValueError):
                provider.fields(index)
            client.get.assert_not_called()
        for changes in [{"timestamp_encoding": "auto"}, {"body_field": "*"}, {"timestamp_field": SCHEMA.service_field}]:
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                replace(SCHEMA, **changes)

    def test_severity_filter_requires_exact_mapping(self):
        provider, client = setup_provider([])
        caps = fields_fixture()
        caps["fields"][SCHEMA.severity_field] = {"text": {"type": "text", "searchable": True, "aggregatable": False}}
        client.get.return_value = caps
        with self.assertRaises(TelemetryError):
            query(provider, severity="ERROR")
        client.post.assert_not_called()
        no_severity = replace(SCHEMA, severity_field=None)
        with self.assertRaises(ValueError):
            provider.query_logs("payment", WINDOW, index_pattern="logs-*", schema=no_severity, severity="ERROR")


if __name__ == "__main__":
    unittest.main()
