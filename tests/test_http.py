from io import BytesIO
from http.client import IncompleteRead
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import threading
import unittest
from unittest.mock import patch
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, urlsplit

from sentinel.tools.http import JsonHttpClient, TelemetryError


class HttpTests(unittest.TestCase):
    def test_backend_redirect_cannot_issue_a_second_out_of_scope_read(self):
        paths = []
        class RedirectBackend(BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass
            def do_GET(self):
                paths.append(self.path)
                self.send_response(302)
                self.send_header("Location", f"http://127.0.0.1:{self.server.server_port}/outside-policy")
                self.send_header("Content-Length", "0")
                self.end_headers()
        with HTTPServer(("127.0.0.1", 0), RedirectBackend) as server:
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            try:
                with self.assertRaisesRegex(TelemetryError, "HTTP 302"):
                    JsonHttpClient(f"http://127.0.0.1:{server.server_port}").get("/api/v1/query")
            finally:
                server.shutdown()
                thread.join(timeout=3)
        self.assertEqual(paths, ["/api/v1/query"])

    def test_parameters_are_encoded_and_request_has_a_timeout(self):
        with patch("sentinel.tools.http.urlopen", return_value=BytesIO(b'{"status":"success"}')) as transport:
            client = JsonHttpClient("http://127.0.0.1:9090", timeout=3)
            result = client.get("/api/v1/query", {"query": 'up{service_name="payment"}', "time": 0})
        request = transport.call_args.args[0]
        self.assertEqual(parse_qs(urlsplit(request.full_url).query), {"query": ['up{service_name="payment"}'], "time": ["0"]})
        self.assertEqual(transport.call_args.kwargs["timeout"], 3)
        self.assertEqual(result, {"status": "success"})

    def test_http_errors_do_not_expose_backend_details(self):
        error = HTTPError("http://localhost", 503, "private detail", None, None)
        with patch("sentinel.tools.http.urlopen", side_effect=error) as transport:
            with self.assertRaisesRegex(TelemetryError, "HTTP 503") as caught:
                JsonHttpClient("http://localhost").get("/api/v1/query")
        self.assertNotIn("private detail", str(caught.exception))
        transport.assert_called_once()

    def test_network_failure_is_explicit_and_never_retried(self):
        with patch("sentinel.tools.http.urlopen", side_effect=URLError("offline")) as transport:
            with self.assertRaisesRegex(TelemetryError, "unavailable"):
                JsonHttpClient("http://localhost").get("/api/v1/query")
        transport.assert_called_once()

    def test_broken_response_stream_is_a_tool_failure(self):
        with patch("sentinel.tools.http.urlopen", side_effect=IncompleteRead(b"partial")):
            with self.assertRaises(TelemetryError):
                JsonHttpClient("http://localhost").get("/api/v1/query")

    def test_malformed_or_oversized_responses_fail(self):
        for body, limit in [(b"not json", 100), (b"[]", 100), (b"{\"x\":1}", 2)]:
            with self.subTest(body=body), patch("sentinel.tools.http.urlopen", return_value=BytesIO(body)):
                with self.assertRaises(TelemetryError):
                    JsonHttpClient("http://localhost", max_bytes=limit).get("/api/v1/query")

    def test_base_url_cannot_embed_credentials_or_parameters(self):
        for url in ["file:///tmp/x", "http://user:token@localhost", "http://localhost?query=x", "http://localhost#fragment", "http://"]:
            with self.subTest(url=url), self.assertRaises(ValueError):
                JsonHttpClient(url)

    def test_invalid_timeout_or_path_is_rejected(self):
        for timeout in [0, -1, float("inf"), float("nan")]:
            with self.subTest(timeout=timeout), self.assertRaises(ValueError):
                JsonHttpClient("http://localhost", timeout=timeout)
        with self.assertRaises(ValueError):
            JsonHttpClient("http://localhost").get("//elsewhere/api")

    def test_search_post_has_a_json_body_and_retains_transport_bounds(self):
        body = {"size": 5, "query": {"term": {"service": "payment"}}}
        with patch("sentinel.tools.http.urlopen", return_value=BytesIO(b'{"hits":{}}')) as transport:
            JsonHttpClient("http://localhost", timeout=3).post("/logs-*/_search", body, {"allow_partial_search_results": "false"})
        request = transport.call_args.args[0]
        self.assertEqual(request.get_method(), "POST")
        self.assertEqual(request.get_header("Content-type"), "application/json")
        self.assertEqual(json.loads(request.data), body)
        self.assertEqual(parse_qs(urlsplit(request.full_url).query), {"allow_partial_search_results": ["false"]})
        self.assertEqual(transport.call_args.kwargs["timeout"], 3)

    def test_invalid_or_oversized_search_body_is_rejected_before_network(self):
        with patch("sentinel.tools.http.urlopen") as transport:
            for body in [[], {"value": float("nan")}, {"query": "x" * 64_000}]:
                with self.subTest(body_type=type(body)), self.assertRaises(ValueError):
                    JsonHttpClient("http://localhost").post("/logs-*/_search", body)
        transport.assert_not_called()
