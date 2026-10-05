"""Sentinel spans are always saved locally; OTLP export is explicitly configured."""

import json
from pathlib import Path

from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor, SpanExporter, SpanExportResult


class JsonSpanExporter(SpanExporter):
    def __init__(self, path: Path):
        self.path = path

    def export(self, spans):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a") as stream:
            for span in spans:
                stream.write(json.dumps(json.loads(span.to_json()), separators=(",", ":")) + "\n")
        return SpanExportResult.SUCCESS

    def shutdown(self):
        pass


def tracing(path: Path, endpoint: str | None = None) -> TracerProvider:
    provider = TracerProvider(resource=Resource.create({"service.name": "sentinel", "service.version": "0.1.0"}))
    provider.add_span_processor(SimpleSpanProcessor(JsonSpanExporter(path)))
    if endpoint:
        from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
        from opentelemetry.sdk.trace.export import BatchSpanProcessor
        provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter(endpoint=endpoint, timeout=5)))
    return provider
