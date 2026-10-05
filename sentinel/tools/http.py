"""Small bounded JSON transport, shared by telemetry adapters."""

import json
import math
from http.client import HTTPException
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener


class _NoRedirects(HTTPRedirectHandler):
    def redirect_request(self, request, response, code, message, headers, new_url):
        return None


# Keep telemetry reads at the configured endpoint. Do not replace the global
# urllib opener: the developer bootstrap still needs GitHub archive redirects.
urlopen = build_opener(_NoRedirects()).open


class TelemetryError(RuntimeError):
    """A diagnostic request failed; this is not evidence of application health."""


class JsonHttpClient:
    def __init__(self, base_url: str, *, timeout: float = 10, max_bytes: int = 5_000_000):
        parsed = urlsplit(base_url)
        if (
            parsed.scheme not in {"http", "https"}
            or not parsed.hostname
            or parsed.username is not None
            or parsed.password is not None
            or parsed.query
            or parsed.fragment
        ):
            raise ValueError("Base URL must be HTTP(S), without credentials, query, or fragment")
        if not math.isfinite(timeout) or timeout <= 0 or max_bytes < 1:
            raise ValueError("Timeout and response size limit must be positive")
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.max_bytes = max_bytes

    def get(self, path: str, parameters: dict | None = None) -> dict:
        return self._request("GET", path, parameters=parameters)

    def post(self, path: str, body: dict, parameters: dict | None = None) -> dict:
        """JSON transport for read-only search APIs; not an exposed agent tool."""
        if not isinstance(body, dict):
            raise ValueError("Request body must be a JSON object")
        return self._request("POST", path, parameters=parameters, body=body)

    def _request(self, method: str, path: str, *, parameters: dict | None = None, body: dict | None = None) -> dict:
        if not path.startswith("/") or path.startswith("//"):
            raise ValueError("Request path must be relative to the configured backend")
        url = self.base_url + path
        if parameters:
            url += "?" + urlencode(parameters)
        headers = {"Accept": "application/json"}
        data = None
        if body is not None:
            data = json.dumps(body, allow_nan=False).encode("utf-8")
            if len(data) > 64_000:
                raise ValueError("JSON request exceeds the 64 KB limit")
            headers["Content-Type"] = "application/json"
        request = Request(url, data=data, headers=headers, method=method)
        try:
            with urlopen(request, timeout=self.timeout) as response:
                raw = response.read(self.max_bytes + 1)
        except HTTPError as exc:
            exc.close()
            raise TelemetryError(f"Telemetry backend returned HTTP {exc.code}") from exc
        except (URLError, TimeoutError, OSError, HTTPException) as exc:
            raise TelemetryError("Telemetry backend unavailable or timed out") from exc
        if len(raw) > self.max_bytes:
            raise TelemetryError("Telemetry response exceeds the configured size limit")
        try:
            payload = json.loads(raw)
        except (ValueError, UnicodeDecodeError) as exc:
            raise TelemetryError("Telemetry backend returned invalid JSON") from exc
        if not isinstance(payload, dict):
            raise TelemetryError("Telemetry backend returned an unexpected JSON shape")
        return payload
