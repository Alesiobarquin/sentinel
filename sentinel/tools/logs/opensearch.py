"""Service-scoped, read-only OpenSearch queries with explicit schema contracts."""

from dataclasses import dataclass
from datetime import datetime
import hashlib
import math
import re
from typing import Protocol

from sentinel.tools.common import TimeWindow, validate_limit, validate_service
from sentinel.tools.http import JsonHttpClient, TelemetryError


def _field_name(value: str) -> None:
    if not isinstance(value, str) or len(value) > 256 or not re.fullmatch(r"[A-Za-z_@][A-Za-z0-9_.@-]*", value):
        raise ValueError("Log fields must be explicit names or dotted paths of at most 256 characters")
    if any(not part for part in value.split(".")):
        raise ValueError("Log field paths cannot contain empty components")


def _index_pattern(value: str) -> None:
    if not isinstance(value, str) or not re.fullmatch(r"[a-z0-9][a-z0-9._*-]{0,199}", value):
        raise ValueError("Choose a log index or pattern with a literal prefix, without slashes or commas")


def _source_name(field: str) -> str:
    # Keyword multi-fields normally do not exist as separate _source properties.
    return field.removesuffix(".keyword")


@dataclass(frozen=True)
class LogSchema:
    service_field: str
    timestamp_field: str
    body_field: str
    severity_field: str | None = None
    trace_id_field: str | None = None
    service_source_field: str | None = None
    timestamp_encoding: str = "iso8601"

    def __post_init__(self):
        for field in (self.service_field, self.timestamp_field, self.body_field):
            _field_name(field)
        if len({self.service_field, self.timestamp_field, self.body_field}) != 3:
            raise ValueError("Service, timestamp, and body fields must be distinct")
        for field in (self.severity_field, self.trace_id_field, self.service_source_field):
            if field is not None:
                _field_name(field)
        if self.timestamp_encoding not in {"iso8601", "epoch_millis", "epoch_seconds"}:
            raise ValueError("Timestamp encoding must be iso8601, epoch_millis, or epoch_seconds")

    @property
    def service_source(self) -> str:
        return self.service_source_field or _source_name(self.service_field)

    @property
    def query_fields(self) -> tuple[str, ...]:
        return tuple(sorted({f for f in (
            self.service_field, self.timestamp_field, self.body_field,
            self.severity_field, self.trace_id_field,
        ) if f is not None}))

    @property
    def source_fields(self) -> tuple[str, ...]:
        return tuple(sorted({self.service_source, *(
            _source_name(f) for f in (
                self.timestamp_field, self.body_field, self.severity_field, self.trace_id_field,
            ) if f is not None
        )}))


@dataclass(frozen=True)
class FieldType:
    name: str
    searchable: bool
    aggregatable: bool
    non_searchable_indices: tuple[str, ...]


@dataclass(frozen=True)
class FieldCapability:
    field: str
    types: tuple[FieldType, ...]


@dataclass(frozen=True)
class FieldCapabilitiesResult:
    source: str
    index_pattern: str
    indices: tuple[str, ...]
    fields: tuple[FieldCapability, ...]


@dataclass(frozen=True)
class LogReference:
    index: str
    document_id: str
    timestamp: float
    trace_id: str | None


@dataclass(frozen=True)
class LogGroup:
    severity: str | None
    message_excerpt: str
    message_truncated: bool
    message_sha256: str
    sample_count: int
    first_seen: float
    last_seen: float
    records: tuple[LogReference, ...]


@dataclass(frozen=True)
class LogQueryResult:
    source: str
    index_pattern: str
    service: str
    window: TimeWindow
    limit: int
    matched_count: int
    matched_count_relation: str
    returned_count: int
    sample_complete: bool
    groups: tuple[LogGroup, ...]


class LogProvider(Protocol):
    def fields(self, index_pattern: str) -> FieldCapabilitiesResult: ...

    def query_logs(
        self, service: str, window: TimeWindow, *, index_pattern: str,
        schema: LogSchema, limit: int = 50, severity: str | None = None,
    ) -> LogQueryResult: ...


def _strings(value) -> tuple[str, ...]:
    if not isinstance(value, list) or not all(isinstance(v, str) for v in value):
        raise ValueError("Invalid string list")
    return tuple(value)


def _uint(value) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError("Invalid count")
    return value


def _parse_fields(payload: dict, index_pattern: str) -> FieldCapabilitiesResult:
    try:
        indices = _strings(payload["indices"])
        raw_fields = payload["fields"]
        if not isinstance(raw_fields, dict):
            raise ValueError("Invalid field capabilities")
        fields = []
        for name, variants in raw_fields.items():
            if not isinstance(name, str) or not isinstance(variants, dict) or not variants:
                raise ValueError("Invalid field variants")
            types = []
            for kind, capability in variants.items():
                if (
                    not isinstance(kind, str) or not isinstance(capability, dict)
                    or capability.get("type") != kind
                    or type(capability.get("searchable")) is not bool
                    or type(capability.get("aggregatable")) is not bool
                ):
                    raise ValueError("Invalid field type")
                types.append(FieldType(
                    kind, capability["searchable"], capability["aggregatable"],
                    () if capability.get("non_searchable_indices") is None else _strings(capability["non_searchable_indices"]),
                ))
            fields.append(FieldCapability(name, tuple(sorted(types, key=lambda t: t.name))))
    except (KeyError, TypeError, ValueError) as exc:
        raise TelemetryError("Malformed OpenSearch field capabilities") from exc
    return FieldCapabilitiesResult("opensearch", index_pattern, tuple(sorted(indices)), tuple(sorted(fields, key=lambda f: f.field)))


def _check_schema(schema: LogSchema, capabilities: FieldCapabilitiesResult, severity: str | None) -> None:
    if not capabilities.indices:
        raise TelemetryError("OpenSearch reported no indices for the log schema")
    fields = {f.field: f for f in capabilities.fields}
    text_types = {"text", "keyword", "constant_keyword", "wildcard"}
    requirements = {
        schema.service_field: {"keyword", "constant_keyword"},
        schema.timestamp_field: {"date", "date_nanos"},
        schema.body_field: text_types,
    }
    for optional in (schema.severity_field, schema.trace_id_field):
        if optional:
            requirements[optional] = text_types
    if severity is not None:
        if not schema.severity_field:
            raise ValueError("A severity filter requires severity_field in the log schema")
        requirements[schema.severity_field] = {"keyword", "constant_keyword"}
    for field, allowed in requirements.items():
        if field not in fields or any(t.name not in allowed for t in fields[field].types):
            raise TelemetryError(f"Log schema field {field} is absent or has incompatible mappings")
        if field == schema.service_field or severity is not None and field == schema.severity_field:
            if any(not t.searchable or t.non_searchable_indices for t in fields[field].types):
                raise TelemetryError(f"Log schema field {field} is not searchable across the selected indices")


def _source_value(document: dict, field: str):
    """Resolve nested and literal dotted OTel keys, refusing ambiguous matches."""
    parts = field.split(".")

    def resolve(node, offset):
        if offset == len(parts):
            return [node]
        if not isinstance(node, dict):
            return []
        values = []
        for end in range(offset + 1, len(parts) + 1):
            key = ".".join(parts[offset:end])
            if key in node:
                values.extend(resolve(node[key], end))
        return values

    values = resolve(document, 0)
    if len(values) > 1:
        raise ValueError("Ambiguous source field")
    return values[0] if values else None


def _timestamp(value, encoding: str) -> float:
    if encoding == "iso8601":
        if not isinstance(value, str):
            raise ValueError("Expected an ISO 8601 log timestamp")
        parsed = datetime.fromisoformat(value)
        if parsed.tzinfo is None:
            raise ValueError("Log timestamps require an explicit timezone")
        result = parsed.timestamp()
    else:
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError("Expected a numeric log timestamp")
        result = value / (1000 if encoding == "epoch_millis" else 1)
    if not math.isfinite(result) or result < 0:
        raise ValueError("Invalid log timestamp")
    return result


def _trace_id(value) -> str | None:
    if value is None or value == "":
        return None
    if not isinstance(value, str) or not re.fullmatch(r"(?:[0-9a-fA-F]{16}|[0-9a-fA-F]{32})", value):
        raise ValueError("Invalid log trace ID")
    return value.lower() if int(value, 16) else None


def _parse_logs(
    payload: dict, *, service: str, window: TimeWindow, index_pattern: str,
    schema: LogSchema, limit: int, severity: str | None, indices: tuple[str, ...],
) -> LogQueryResult:
    try:
        shards = payload["_shards"]
        if not isinstance(shards, dict) or type(payload.get("timed_out")) is not bool:
            raise ValueError("Missing search completion status")
        total_shards = _uint(shards["total"])
        successful, failed = _uint(shards["successful"]), _uint(shards["failed"])
        if payload["timed_out"] or failed or not total_shards or successful != total_shards or payload.get("terminated_early", False) is not False:
            raise TelemetryError("OpenSearch search was incomplete; partial results were not used")
        hits = payload["hits"]
        total = hits["total"]
        count, relation = _uint(total["value"]), total["relation"]
        documents = hits["hits"]
        if relation not in {"eq", "gte"} or not isinstance(documents, list) or len(documents) > limit or count < len(documents):
            raise ValueError("Invalid search hits or count")
        grouped = {}
        seen = set()
        for hit in documents:
            index, document_id, source = hit["_index"], hit["_id"], hit["_source"]
            if (
                not isinstance(index, str) or index not in indices
                or not isinstance(document_id, str) or not document_id
                or not isinstance(source, dict) or (index, document_id) in seen
            ):
                raise ValueError("Invalid or duplicate log document")
            seen.add((index, document_id))
            if _source_value(source, schema.service_source) != service:
                raise ValueError("Log does not belong to the requested service")
            at = _timestamp(_source_value(source, _source_name(schema.timestamp_field)), schema.timestamp_encoding)
            if not window.start <= at < window.end:
                raise ValueError("Log is outside the requested window")
            message = _source_value(source, _source_name(schema.body_field))
            level = _source_value(source, _source_name(schema.severity_field)) if schema.severity_field else None
            if not isinstance(message, str) or level is not None and not isinstance(level, str):
                raise ValueError("Unsupported log body or severity")
            if severity is not None and level != severity:
                raise ValueError("Log does not match the requested severity")
            trace_id = _trace_id(_source_value(source, _source_name(schema.trace_id_field))) if schema.trace_id_field else None
            grouped.setdefault((level, message), []).append(LogReference(index, document_id, at, trace_id))
        groups = []
        for (level, message), records in grouped.items():
            ordered = tuple(sorted(records, key=lambda r: (r.timestamp, r.index, r.document_id)))
            groups.append(LogGroup(
                level, message[:800], len(message) > 800, hashlib.sha256(message.encode()).hexdigest(),
                len(records), ordered[0].timestamp, ordered[-1].timestamp, ordered,
            ))
    except (KeyError, TypeError, ValueError, OverflowError, OSError) as exc:
        raise TelemetryError("Unsupported or malformed OpenSearch log response; check the explicit schema") from exc
    groups.sort(key=lambda g: (-g.sample_count, -g.last_seen, g.severity or "", g.message_sha256))
    return LogQueryResult(
        "opensearch", index_pattern, service, window, limit, count, relation,
        len(documents), relation == "eq" and count == len(documents), tuple(groups),
    )


class OpenSearchProvider:
    def __init__(self, url: str = "http://127.0.0.1:9200", *, client: JsonHttpClient | None = None):
        self.client = client or JsonHttpClient(url)

    def _fields(self, index_pattern: str, fields: str) -> FieldCapabilitiesResult:
        return _parse_fields(self.client.get(f"/{index_pattern}/_field_caps", {
            "fields": fields, "include_unmapped": "true", "allow_no_indices": "false",
        }), index_pattern)

    def fields(self, index_pattern: str) -> FieldCapabilitiesResult:
        _index_pattern(index_pattern)
        return self._fields(index_pattern, "*")

    def query_logs(
        self, service: str, window: TimeWindow, *, index_pattern: str,
        schema: LogSchema, limit: int = 50, severity: str | None = None,
    ) -> LogQueryResult:
        validate_service(service)
        validate_limit(limit)
        _index_pattern(index_pattern)
        if severity is not None and (not isinstance(severity, str) or not severity.strip() or len(severity) > 64 or any(ord(c) < 32 for c in severity)):
            raise ValueError("Severity must be a nonempty label of at most 64 characters")
        if severity is not None and not schema.severity_field:
            raise ValueError("A severity filter requires severity_field in the log schema")
        capabilities = self._fields(index_pattern, ",".join(schema.query_fields))
        _check_schema(schema, capabilities, severity)
        filters = [
            {"term": {schema.service_field: service}},
            {"range": {schema.timestamp_field: {"gte": window.iso_start, "lt": window.iso_end}}},
        ]
        if severity is not None:
            filters.append({"term": {schema.severity_field: severity}})
        payload = self.client.post(f"/{index_pattern}/_search", {
            "size": limit, "timeout": "8s", "track_total_hits": 10000,
            "query": {"bool": {"filter": filters}},
            "sort": [{schema.timestamp_field: {"order": "desc"}}],
            "_source": list(schema.source_fields),
        }, {"allow_partial_search_results": "false", "allow_no_indices": "false"})
        return _parse_logs(
            payload, service=service, window=window, index_pattern=index_pattern,
            schema=schema, limit=limit, severity=severity, indices=capabilities.indices,
        )
