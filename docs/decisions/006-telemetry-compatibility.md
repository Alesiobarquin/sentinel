# ADR 006: initial trace and log compatibility boundaries

**Status:** implemented and live-validated against the pinned demo on 2026-10-04.

## Context

The pinned demo provides Jaeger and OpenSearch. The initial adapter contracts
were built offline and then tested against Jaeger 2.19.0 and OpenSearch 3.7.0
in the running Demo 3.1.0. Service discovery, trace/dependency queries, field
preflight, and normalized payment logs passed live checks.
Jaeger classifies its UI JSON API as internal, subject to change. Its stable read
API uses OTLP/gRPC. See the [official API documentation](https://www.jaegertracing.io/docs/2.21/architecture/apis/).

## Decision

Keep the initial `/api/services`, `/api/traces`, and `/api/dependencies` reads
inside a Jaeger compatibility adapter. Query traces in Unix microseconds and
dependencies in milliseconds; normalize result timestamps to seconds and
durations to milliseconds. Preserve IDs, parent references, explicit error
attributes, missing parents, warnings, and selection limits. Normalize equivalent
legacy/native error representations, reject real conflicts, and retain a requested
service span before prioritizing the remaining errors. Reject query errors
and malformed results. Validate this adapter against the pinned runtime before
using its results as evidence.

For OpenSearch, require an explicit `LogSchema` and a scoped index expression.
Check [field capabilities](https://docs.opensearch.org/latest/api-reference/search-apis/field-caps/)
before constructing a service/time-filtered [search](https://docs.opensearch.org/latest/api-reference/search-apis/search/).
Keep exact service/severity filters on keyword fields, handle source-field paths
separately from keyword multi-fields, and reject mixed incompatible mappings.
Use only read endpoints even though the search body travels through HTTP POST.
Reject timed-out or partial searches. Group identical full messages and severity
within the returned sample; never label those counts as population frequencies.

## Alternatives

Implementing gRPC now adds dependencies before the local target works. Baking
in guessed log field names can silently omit evidence or misidentify services.
Forwarding raw backend payloads obscures units and can waste the future model's
budget. Approximate message normalization may merge distinct failures before its
behavior has been evaluated.

## Why this option

The adapters make units, coverage, and provenance reviewable using only the
standard library. Explicit compatibility boundaries let live discovery correct
backend assumptions without coupling future agent logic to raw payloads.

## Consequences

The Jaeger JSON surface is temporary and version-sensitive. The schema example
documents supported configuration. The separately checked-in
[runtime schema](../../infra/docker/log-schema.json) records verified mappings:
`resource.service.name.keyword`, `@timestamp`, `body`, `severity.text.keyword`,
and `traceId`. Payment failures use lowercase `warn`, with the exception message
in the body and literal dotted exception attributes. Schema preflight still runs
for each query; a checked-in schema does not guarantee future compatibility.
Structured log bodies, unconfigured timestamp representations, and array-valued identities
are unsupported and fail explicitly. Search samples are the newest matching
documents, bounded at 100; matching totals can be lower bounds above 10,000.
These adapters do not prove diagnostic accuracy or full incident coverage.

## Future reconsideration

Repeat mapping and payload discovery after upgrades.
Move Jaeger reads to a stable API when its maintenance benefit justifies the
dependency. Add richer reduction or schema support when a real incident and
tests demonstrate the need.
