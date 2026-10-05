"""Synthetic Jaeger payloads exercise parsing, not actual demo integration."""

from copy import deepcopy
import unittest
from unittest.mock import Mock

from sentinel.tools.common import TimeWindow
from sentinel.tools.http import TelemetryError
from sentinel.tools.traces.jaeger import JaegerProvider, summarize_trace

TRACE = "1234567890abcdef1234567890abcdef"
ROOT = "0000000000000001"
CHILD = "0000000000000002"
START = 1_791_144_000_000_000


def trace_fixture():
    return {
        "traceID": TRACE,
        "processes": {"p1": {"serviceName": "checkout"}, "p2": {"serviceName": "payment"}},
        "spans": [
            {"traceID": TRACE, "spanID": ROOT, "operationName": "checkout", "processID": "p1",
             "startTime": START, "duration": 100_000, "tags": [{"key": "error", "value": False}], "references": []},
            {"traceID": TRACE, "spanID": CHILD, "operationName": "charge", "processID": "p2",
             "startTime": START + 20_000, "duration": 40_000,
             "tags": [{"key": "error", "value": True}, {"key": "error.message", "value": "synthetic payment error"}],
             "references": [{"refType": "CHILD_OF", "traceID": TRACE, "spanID": ROOT}]},
        ],
        "warnings": ["synthetic warning"],
    }


class TraceTests(unittest.TestCase):
    def test_equivalent_legacy_tags_are_accepted_but_contradictions_are_not(self):
        raw = trace_fixture()
        raw["spans"][1]["tags"] = [{"key": "error", "value": "true"}, {"key": "error", "value": True},
                                   {"key": "otel.status_code", "value": "ERROR"}, {"key": "otel.status_code", "value": 2}]
        self.assertTrue(summarize_trace(raw, service="payment").spans[0].is_error)
        for conflict in [False, 1]:
            bad = deepcopy(raw)
            bad["spans"][1]["tags"].append({"key": "error", "value": conflict})
            with self.assertRaises(TelemetryError):
                summarize_trace(bad, service="payment")

    def test_requested_service_survives_long_upstream_failures(self):
        raw = trace_fixture()
        raw["spans"][0]["tags"] = [{"key": "error", "value": True}]
        result = summarize_trace(raw, service="payment", span_limit=1)
        self.assertEqual(result.spans[0].service, "payment")
        raw["spans"][1]["tags"] = [{"key": "error", "value": False}]
        result = summarize_trace(raw, service="payment", span_limit=1)
        self.assertEqual(result.spans[0].service, "payment")
        self.assertFalse(result.spans[0].is_error)

    def test_summary_preserves_relationships_and_prioritizes_error_spans(self):
        trace = summarize_trace(trace_fixture(), service="payment", span_limit=1)
        self.assertEqual(trace.trace_id, TRACE)
        self.assertEqual(trace.start_time, START / 1_000_000)
        self.assertEqual(trace.observed_duration_ms, 100)  # Not 140 ms summed spans.
        self.assertEqual(trace.services, ("checkout", "payment"))
        self.assertEqual(trace.root_span_ids, (ROOT,))
        self.assertEqual(trace.error_span_count, 1)
        self.assertEqual(trace.span_count, 2)
        self.assertEqual(trace.omitted_span_count, 1)
        self.assertEqual(trace.spans[0].span_id, CHILD)
        self.assertEqual(trace.spans[0].duration_ms, 40)
        self.assertEqual(trace.spans[0].references[0].span_id, ROOT)
        self.assertEqual(trace.warnings, ("synthetic warning",))

    def test_error_tags_are_explicit_and_not_general_truthiness(self):
        for key, value, expected in [
            ("error", "false", False), ("error", False, False), ("error", "true", True),
            ("otel.status_code", "ERROR", True), ("otel.status_code", 2, True),
            ("otel.status_code", True, False), ("http.status_code", 500, False),
        ]:
            with self.subTest(key=key, value=value):
                raw = trace_fixture()
                raw["spans"][1]["tags"] = [{"key": key, "value": value}]
                result = summarize_trace(raw, service="payment")
                child = next(s for s in result.spans if s.span_id == CHILD)
                self.assertEqual(child.is_error, expected)

    def test_missing_parents_and_backend_warnings_remain_visible(self):
        raw = trace_fixture()
        raw["spans"][1]["references"][0]["spanID"] = "0000000000000099"
        raw["spans"][1]["warnings"] = ["synthetic warning", "missing parent"]
        result = summarize_trace(raw, service="payment")
        self.assertEqual(result.unresolved_parent_count, 1)
        self.assertEqual(result.warnings, ("synthetic warning", "missing parent"))

    def test_malformed_traces_fail_instead_of_becoming_empty_evidence(self):
        good = trace_fixture()
        bad = []
        for key, value in [("spans", []), ("spans", [None]), ("processes", []), ("traceID", "bad"), ("warnings", "warning")]:
            item = deepcopy(good)
            item[key] = value
            bad.append(item)
        for key, value in [("duration", -1), ("duration", True), ("startTime", 2**64), ("tags", {}), ("references", {}), ("processID", "missing"), ("traceID", "ffffffffffffffff")]:
            item = deepcopy(good)
            item["spans"][0][key] = value
            bad.append(item)
        duplicate = deepcopy(good)
        duplicate["spans"][1]["spanID"] = ROOT
        bad.extend([duplicate, None])
        for item in bad:
            with self.subTest(item=item), self.assertRaises(TelemetryError):
                summarize_trace(item, service="payment")
        with self.assertRaises(TelemetryError):
            summarize_trace(good, service="absent")

    def test_query_uses_microseconds_and_keeps_limit_reached_visible(self):
        client = Mock()
        client.get.return_value = {"data": [trace_fixture()], "errors": None}
        window = TimeWindow(START / 1_000_000, START / 1_000_000 + 60)
        result = JaegerProvider(client=client).query_traces("payment", window, limit=1, min_duration_ms=0.001)
        path, parameters = client.get.call_args.args
        self.assertEqual(path, "/api/traces")
        self.assertEqual(parameters["start"], START)
        self.assertEqual(parameters["end"], START + 60_000_000)
        self.assertEqual(parameters["minDuration"], "1us")
        self.assertTrue(result.limit_reached)

    def test_empty_matches_stay_empty_and_partial_results_fail(self):
        client = Mock()
        provider = JaegerProvider(client=client)
        window = TimeWindow(0, 60)
        client.get.return_value = {"data": []}
        result = provider.query_traces("payment", window)
        self.assertEqual(result.traces, ())
        self.assertFalse(result.limit_reached)
        for payload in [
            {"data": [trace_fixture()], "errors": [{"msg": "private backend detail"}]},
            {"data": [trace_fixture(), trace_fixture()]}, {"data": {}}, {"data": [], "errors": {}},
        ]:
            client.get.return_value = payload
            with self.subTest(payload=payload), self.assertRaises(TelemetryError):
                provider.query_traces("payment", window, limit=1)
        client.get.return_value = {"data": [trace_fixture(), trace_fixture()]}
        with self.assertRaisesRegex(TelemetryError, "duplicate"):
            provider.query_traces("payment", window)

    def test_invalid_query_arguments_do_not_reach_the_backend(self):
        client = Mock()
        provider = JaegerProvider(client=client)
        for parameters in [
            {"limit": 0}, {"limit": True}, {"span_limit": 21}, {"span_limit": -1},
            {"min_duration_ms": float("nan")}, {"min_duration_ms": "1"},
            {"min_duration_ms": -1}, {"min_duration_ms": 21_600_001},
        ]:
            with self.subTest(parameters=parameters), self.assertRaises(ValueError):
                provider.query_traces("payment", TimeWindow(0, 60), **parameters)
        with self.assertRaises(ValueError):
            provider.query_traces("payment", TimeWindow(10_000_000_000, 10_000_000_060))
        client.get.assert_not_called()

    def test_wrong_window_data_is_not_used_as_incident_evidence(self):
        client = Mock()
        client.get.return_value = {"data": [trace_fixture()]}
        with self.assertRaisesRegex(TelemetryError, "outside the requested window"):
            JaegerProvider(client=client).query_traces("payment", TimeWindow(0, 60))

    def test_service_discovery_is_sorted_and_validated(self):
        client = Mock()
        client.get.return_value = {"data": ["payment", "checkout", "payment"]}
        self.assertEqual(JaegerProvider(client=client).services(), ("checkout", "payment"))
        client.get.return_value = {"data": ["payment", None]}
        with self.assertRaises(TelemetryError):
            JaegerProvider(client=client).services()

    def test_dependency_query_uses_milliseconds_and_validates_edges(self):
        client = Mock()
        client.get.return_value = {"data": [{"parent": "checkout", "child": "payment", "callCount": 7}]}
        result = JaegerProvider(client=client).get_service_dependencies(TimeWindow(10, 60))
        self.assertEqual(client.get.call_args.args, ("/api/dependencies", {"endTs": 60_000, "lookback": 50_000}))
        self.assertEqual(result.edges[0].call_count, 7)
        for data in [
            [{"parent": "checkout", "child": "payment", "callCount": True}],
            [{"parent": "checkout", "child": "payment", "callCount": -1}],
            [result.edges[0]],
            [{"parent": "checkout", "child": "payment", "callCount": 1}] * 2,
        ]:
            client.get.return_value = {"data": data}
            with self.subTest(data=data), self.assertRaises(TelemetryError):
                JaegerProvider(client=client).get_service_dependencies(TimeWindow(0, 60))


if __name__ == "__main__":
    unittest.main()
