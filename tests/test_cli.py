from contextlib import redirect_stderr, redirect_stdout
from io import BytesIO, StringIO
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from urllib.parse import urlsplit

from sentinel.__main__ import main
from sentinel.tools.http import TelemetryError
from sentinel.tools.metrics.prometheus import parse_result
from test_logs import SCHEMA, START, document, fields_fixture, response
from test_traces import START as TRACE_START, trace_fixture
from dataclasses import asdict


class CliTests(unittest.TestCase):
    def test_output_is_structured_and_the_call_is_audited(self):
        result = parse_result({"status": "success", "data": {"resultType": "vector", "result": []}}, "up")
        with tempfile.TemporaryDirectory() as directory:
            audit = Path(directory) / "audit.jsonl"
            output = StringIO()
            with patch.dict("os.environ", {"SENTINEL_AUDIT_PATH": str(audit)}), patch("sentinel.__main__.PrometheusProvider") as provider, redirect_stdout(output):
                provider.return_value.query_metrics.return_value = result
                code = main(["metrics", "--query", "up"])
            events = [json.loads(line) for line in audit.read_text().splitlines()]
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(output.getvalue())["series"], [])
        self.assertTrue(events[1]["success"])

    def test_failure_returns_nonzero_without_a_traceback(self):
        with tempfile.TemporaryDirectory() as directory:
            errors = StringIO()
            with patch.dict("os.environ", {"SENTINEL_AUDIT_PATH": str(Path(directory) / "audit.jsonl")}), patch("sentinel.__main__.PrometheusProvider") as provider, redirect_stderr(errors):
                provider.return_value.query_metrics.side_effect = TelemetryError("backend unavailable")
                code = main(["metrics", "--query", "up"])
        self.assertEqual(code, 1)
        self.assertIn("backend unavailable", errors.getvalue())
        self.assertNotIn("Traceback", errors.getvalue())

    def test_trace_commands_run_through_the_adapter_and_audit(self):
        cases = [
            (["services"], {"data": ["payment", "checkout"]}, "services", "trace_services"),
            (["traces", "--service", "payment", "--start", str(TRACE_START / 1_000_000), "--end", str(TRACE_START / 1_000_000 + 60)],
             {"data": [trace_fixture()]}, "traces", "query_traces"),
            (["dependencies", "--start", "0", "--end", "60"],
             {"data": [{"parent": "checkout", "child": "payment", "callCount": 5}]}, "edges", "get_service_dependencies"),
        ]
        for argv, payload, output_key, tool in cases:
            with self.subTest(command=argv[0]), tempfile.TemporaryDirectory() as directory:
                audit = Path(directory) / "audit.jsonl"
                output = StringIO()
                with patch.dict("os.environ", {"SENTINEL_AUDIT_PATH": str(audit)}), patch("sentinel.tools.http.urlopen", return_value=BytesIO(json.dumps(payload).encode())), redirect_stdout(output):
                    code = main(argv)
                events = [json.loads(line) for line in audit.read_text().splitlines()]
                self.assertEqual(code, 0)
                self.assertTrue(json.loads(output.getvalue())[output_key])
                self.assertEqual(events[0]["tool"], tool)
                self.assertTrue(events[1]["success"])

    def test_log_cli_runs_schema_preflight_search_grouping_and_audit(self):
        requests = []
        def serve(request, **kwargs):
            requests.append(request)
            payload = fields_fixture() if urlsplit(request.full_url).path.endswith("/_field_caps") else response([document()])
            return BytesIO(json.dumps(payload).encode())
        with tempfile.TemporaryDirectory() as directory:
            schema = Path(directory) / "schema.json"
            schema.write_text(json.dumps(asdict(SCHEMA)))
            audit = Path(directory) / "audit.jsonl"
            output = StringIO()
            with patch.dict("os.environ", {"SENTINEL_AUDIT_PATH": str(audit)}), patch("sentinel.tools.http.urlopen", side_effect=serve), redirect_stdout(output):
                code = main(["logs", "--index", "logs-*", "--schema", str(schema), "--service", "payment", "--start", str(START), "--end", str(START + 60)])
            events = [json.loads(line) for line in audit.read_text().splitlines()]
        self.assertEqual(code, 0)
        self.assertEqual([r.get_method() for r in requests], ["GET", "POST"])
        self.assertEqual(json.loads(output.getvalue())["groups"][0]["sample_count"], 1)
        self.assertEqual(events[0]["arguments"]["schema"], asdict(SCHEMA))
        self.assertNotIn("synthetic error", json.dumps(events))

    def test_field_discovery_cli_outputs_structured_mapping_information(self):
        with tempfile.TemporaryDirectory() as directory:
            output = StringIO()
            with patch.dict("os.environ", {"SENTINEL_AUDIT_PATH": str(Path(directory) / "audit.jsonl")}), patch("sentinel.tools.http.urlopen", return_value=BytesIO(json.dumps(fields_fixture()).encode())), redirect_stdout(output):
                code = main(["log-fields", "--index", "logs-*"])
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(output.getvalue())["source"], "opensearch")
        self.assertEqual(len(json.loads(output.getvalue())["indices"]), 2)

    def test_invalid_log_schema_does_not_issue_a_network_request(self):
        for payload in [[], {"service_field": "service"}, {**asdict(SCHEMA), "unknown": "field"}]:
            with self.subTest(payload=payload), tempfile.TemporaryDirectory() as directory:
                schema = Path(directory) / "schema.json"
                schema.write_text(json.dumps(payload))
                errors = StringIO()
                with patch("sentinel.tools.http.urlopen") as transport, redirect_stderr(errors):
                    code = main(["logs", "--index", "logs-*", "--schema", str(schema), "--service", "payment", "--start", "0", "--end", "60"])
                self.assertEqual(code, 1)
                self.assertIn("Invalid log schema", errors.getvalue())
                self.assertNotIn("Traceback", errors.getvalue())
                transport.assert_not_called()
