"""Prometheus read API adapter. Non-finite samples remain missing, never zero."""

from dataclasses import dataclass
import math
from typing import Protocol

from sentinel.tools.http import JsonHttpClient, TelemetryError

READINESS_QUERY = 'count({__name__!=""})'


@dataclass(frozen=True)
class Sample:
    timestamp: float
    value: float | None


@dataclass(frozen=True)
class MetricSeries:
    labels: dict[str, str]
    samples: tuple[Sample, ...]


@dataclass(frozen=True)
class MetricQueryResult:
    source: str
    query: str
    result_type: str
    series: tuple[MetricSeries, ...]
    warnings: tuple[str, ...]
    start: float | None = None
    end: float | None = None
    step: float | None = None


class MetricsProvider(Protocol):
    def query_metrics(
        self, query: str, *, at: float | None = None,
        start: float | None = None, end: float | None = None, step: float = 15,
    ) -> MetricQueryResult: ...

    def metric_names(self) -> tuple[str, ...]: ...


def _sample(raw: list) -> Sample:
    if not isinstance(raw, list) or len(raw) != 2:
        raise ValueError("Invalid sample")
    if any(isinstance(value, bool) for value in raw):
        raise ValueError("Boolean values are not numeric telemetry samples")
    timestamp, value = float(raw[0]), float(raw[1])
    if not math.isfinite(timestamp):
        raise ValueError("Invalid sample timestamp")
    return Sample(timestamp, value if math.isfinite(value) else None)


def parse_result(payload: dict, query: str, **window) -> MetricQueryResult:
    if payload.get("status") != "success":
        # Do not echo backend response bodies: they can contain raw telemetry.
        raise TelemetryError("Prometheus reported a query failure")
    try:
        data = payload["data"]
        result_type, raw_result = data["resultType"], data["result"]
        series = []
        if result_type == "scalar":
            series.append(MetricSeries({}, (_sample(raw_result),)))
        elif result_type in {"vector", "matrix"}:
            if not isinstance(raw_result, list):
                raise ValueError("Expected a list of series")
            for item in raw_result:
                labels = item["metric"]
                if not isinstance(labels, dict) or not all(
                    isinstance(k, str) and isinstance(v, str) for k, v in labels.items()
                ):
                    raise ValueError("Invalid labels")
                raw_samples = [item["value"]] if result_type == "vector" else item["values"]
                if not isinstance(raw_samples, list):
                    raise ValueError("Invalid samples")
                series.append(MetricSeries(labels, tuple(_sample(s) for s in raw_samples)))
        else:
            raise ValueError("Only numeric float-sample queries are supported")
        warnings = payload.get("warnings", [])
        if not isinstance(warnings, list) or not all(isinstance(w, str) for w in warnings):
            raise ValueError("Invalid warnings")
    except (KeyError, TypeError, ValueError, OverflowError) as exc:
        raise TelemetryError("Unsupported or malformed Prometheus query result") from exc
    return MetricQueryResult("prometheus", query, result_type, tuple(series), tuple(warnings), **window)


class PrometheusProvider:
    def __init__(self, url: str = "http://127.0.0.1:9090", *, client: JsonHttpClient | None = None):
        self.client = client or JsonHttpClient(url)

    def query_metrics(
        self, query: str, *, at: float | None = None,
        start: float | None = None, end: float | None = None, step: float = 15,
    ) -> MetricQueryResult:
        if not query.strip() or len(query) > 4096:
            raise ValueError("Query must contain 1–4096 characters")
        ranged = start is not None or end is not None
        parameters: dict = {"query": query, "timeout": "8s"}
        if ranged:
            if start is None or end is None or at is not None:
                raise ValueError("A range needs start and end and cannot include an instant timestamp")
            if not all(math.isfinite(v) for v in (start, end, step)):
                raise ValueError("Range values must be finite")
            if start < 0 or end < start or end - start > 21600 or step <= 0:
                raise ValueError("Range must be nonnegative, ordered, at most six hours, with positive step")
            if (end - start) / step + 1 > 5000:
                raise ValueError("Range exceeds 5000 samples per series; increase step")
            parameters.update(start=start, end=end, step=step)
            payload = self.client.get("/api/v1/query_range", parameters)
            result = parse_result(payload, query, start=start, end=end, step=step)
            if result.result_type != "matrix":
                raise TelemetryError("Prometheus range query did not return a matrix")
            return result
        if at is not None:
            if not math.isfinite(at) or at < 0:
                raise ValueError("Instant timestamp must be finite and nonnegative")
            parameters["time"] = at
        return parse_result(self.client.get("/api/v1/query", parameters), query)

    def metric_names(self) -> tuple[str, ...]:
        payload = self.client.get("/api/v1/label/__name__/values")
        names = payload.get("data")
        if payload.get("status") != "success" or not isinstance(names, list) or not all(
            isinstance(name, str) for name in names
        ):
            raise TelemetryError("Invalid Prometheus metric-name response")
        return tuple(sorted(set(names)))
