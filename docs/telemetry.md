# Inspecting the local telemetry environment

The pinned upstream demo uses Prometheus, Jaeger, and OpenSearch. Sentinel should
consume their data rather than replace them. Their configurations remain in
`.cache/demo/source/src/` and originate from the external demo.

## Metrics

The implemented adapter uses the stable [Prometheus HTTP API](https://prometheus.io/docs/prometheus/latest/querying/api/):
`/api/v1/query` for instant numeric queries, `/api/v1/query_range` for windows,
and `/api/v1/label/__name__/values` for discovery.

Start with `make metrics` and `make metric-names`. The readiness expression is
`count({__name__!=""})`. In this pinned full deployment, the Collector pushes
metrics to Prometheus over OTLP/HTTP; `up` is absent. The full Collector layer
replaces the core metrics receiver array and omits its `prometheus/ad` receiver.
Even when present in another deployment, `up` describes scrape availability
and does not establish that the web store's requests succeed. Choose incident
queries only after inspecting the real metric names, labels, units, and histogram
representation emitted by this release. Do not invent a service latency series
from the PRD's illustrative values. Percentiles belong to distributions; do not
calculate a percentile over already-calculated percentile samples.

Live discovery verified `demo_payment_transactions_total`,
`traces_span_metrics_calls_total`, and
`traces_span_metrics_duration_milliseconds_bucket`. The span-metrics connector
derives the latter two from traces. The payment scenario filters
`service_name="payment"`, `span_kind="SPAN_KIND_SERVER"`, and
`span_name="oteldemo.PaymentService/Charge"`, then compares `status_code`
series. Filtering server spans avoids counting the same request's client and
internal spans again. `STATUS_CODE_UNSET` means no explicit error status; it is
not an HTTP success code. Success is corroborated with transaction logs/traces.
Counters are cumulative, and export can lag the request time. A range evaluation
step of 15 seconds does not force a new source observation every 15 seconds.

The model-facing `metrics` tool makes three fixed reads: status-counter increase,
server-span p95, and minimum raw counter sample counts grouped by status. The
last query uses [count_over_time](https://prometheus.io/docs/prometheus/latest/querying/functions/#aggregation_over_time)
and preserves missing results. Sample counts are telemetry observations, not
requests. Fewer than two counter samples cannot establish an increase; a larger
count does not prove complete incident coverage. A measured post-restart payment
counter capture contained observations approximately 60 seconds apart, making
short windows especially sensitive to alignment and newly created status series.
The earlier missing metric values remain recorded rather than replaced with zero.

The capture helper also computes a two-minute p95 from server-span histogram
buckets, grouped by service. Its unit is milliseconds. This compares operation
distributions, not a checkout critical path or an application SLO. The highest
latency service alone is insufficient evidence of the payment fault.

Ranges use Unix seconds, at most six hours, with at most 5000 evaluation points
per series. HTTP responses are limited to 5 MB. Backend warnings are preserved,
empty matches remain empty, and NaN/infinite values become `null`. Native
histogram JSON is currently unsupported; convert it with an appropriate PromQL
function to float results or extend the adapter explicitly with tests.

## Traces

Use Jaeger through <http://127.0.0.1:8080/jaeger/ui/>. The direct query port 16686
is also published; honor the base path in the pinned Jaeger configuration.
`demo-verify` checks `/jaeger/ui/api/services` through the proxy as a bootstrap
probe. The [Jaeger API documentation](https://www.jaegertracing.io/docs/latest/apis/)
classifies `/api/*` as an internal UI API. Keep any initial compatibility adapter
isolated and test it against the pinned demo; consider the stable OTLP-based read
API before choosing a long-term contract.

The implemented `JaegerProvider` discovers services, queries traces, and reads
Jaeger's aggregated dependency graph:

```bash
uv run python -m sentinel services
WINDOW_END=$(uv run python -c 'import time; print(time.time())')
WINDOW_START=$(uv run python -c 'import time; print(time.time() - 300)')
uv run python -m sentinel traces --service payment --start "$WINDOW_START" --end "$WINDOW_END" \
  --limit 10 --span-limit 5 --min-duration-ms 0
uv run python -m sentinel dependencies --start "$WINDOW_START" --end "$WINDOW_END"
```

CLI inputs use Unix seconds and windows up to six hours. Jaeger's trace query
and span timestamps use microseconds; dependency queries use milliseconds. The
adapter performs these conversions. The minimum duration is rounded up to a
microsecond. Limits are at most 100 traces and 20 selected spans per trace.

Each trace retains its ID, observed start/envelope duration, services, total
span/error counts, root IDs, unresolved parent count, warnings, and omitted span
count. Selected spans retain IDs, service/operation names, start times, durations
in milliseconds, parent references, and allowlisted diagnostic attributes.
Explicit `error=true` or an OTel error status marks an error; an HTTP status tag
is preserved without inventing a span status. Requested-service errors are
preferred, and at least one requested-service span is retained when present;
remaining errors precede longer non-error spans. Equivalent string/native boolean
error tags are normalized while contradictory values fail. Overlapping span
durations are not summed.

`limit_reached` means the query may have omitted traces; Jaeger does not provide
an exact total here. Warnings and unresolved parents can indicate incomplete
traces. The observed envelope is not a critical path or proof of root cause.
Empty dependency results may reflect missing/delayed aggregation. Query failures
are tool errors. Service, trace, and dependency reads passed live tests against
the pinned Jaeger 2.19.0 runtime. This does not stabilize its internal UI API.

## Logs

OpenSearch is available at <http://127.0.0.1:9200>. The cluster-health probe checks
backend availability only. The implemented `OpenSearchProvider` uses the
[field capabilities API](https://docs.opensearch.org/latest/api-reference/search-apis/field-caps/)
for discovery/preflight and the [search API](https://docs.opensearch.org/latest/api-reference/search-apis/search/)
for bounded service/time-filtered reads. Its POST endpoint performs a search.

The verified runtime exports to `otel-logs-YYYY-MM-DD`; the observed index was
`otel-logs-2026-10-04`. The explicit
[pinned schema](../infra/docker/log-schema.json) was checked against mappings and
source documents. Repeat discovery when upgrading or selecting another backend:

```bash
curl --fail --silent --show-error 'http://127.0.0.1:9200/_cat/indices?format=json'
uv run python -m sentinel log-fields --index 'otel-logs*'
curl --fail --silent --show-error 'http://127.0.0.1:9200/otel-logs*/_search?size=1'
```

Use `infra/docker/log-schema.json` for this pin. For other targets, build a new
schema from the observed mappings and `_source` document.
The [example schema](examples/log-schema.example.json) shows supported fields;
**it is illustrative and is not the verified schema of Demo 3.1.0.** The log
adapter will not auto-select fields. Configure:

| Property | Contract |
| --- | --- |
| `service_field` | Searchable keyword/constant-keyword field for exact service filtering |
| `timestamp_field` | Date/date-nanos field for filtering and sorting |
| `body_field` | Field whose source value is a string message |
| `severity_field` | Optional string field; keyword required when filtering by severity |
| `trace_id_field` | Optional string containing a hexadecimal trace ID |
| `service_source_field` | Optional explicit source path if it differs from the query field |
| `timestamp_encoding` | `iso8601` with a timezone, `epoch_millis`, or `epoch_seconds` |

For source reads, `.keyword` is removed from conventional multi-field paths.
Service source paths can be overridden explicitly. Nested objects and literal
dotted OTel attribute keys are supported; ambiguous representations fail.
Unsupported structured message bodies, array identities, and timezone-free
timestamps fail. Timestamps normalize to floating-point Unix seconds; this is
not a tool for nanosecond measurements.

The verified fields are `resource.service.name.keyword` (keyword), `@timestamp`
(date), `body` (text), `severity.text.keyword` (keyword), and `traceId` (text).
The source stores `resource["service.name"]` as a literal dotted key. Payment
failures appear as lowercase `warn`; the full exception message is present in
`body` and `attributes["exception.message"]`. Filtering by uppercase `ERROR`
would miss this scenario's payment warnings.

```bash
uv run python -m sentinel logs --service payment --index 'otel-logs*' \
  --schema infra/docker/log-schema.json --start "$WINDOW_START" --end "$WINDOW_END" \
  --limit 50 --severity warn
```

Choose the actual severity label; omit the filter to inspect all severities.
Windows use `[start, end)` and at most six hours. Queries select the newest
matching documents, with at most 100 returned and an eight-second server timeout.
These three adapters share a 10-second HTTP timeout, 5 MB response bound, and no
retries or redirects. Configure the final backend base URL explicitly; a redirect
fails instead of issuing another read to a backend-selected destination.
Incompatible/unmapped fields, timeouts, shard failures, early termination, and
records from the wrong service/window/indices become explicit failures.

Groups combine identical full messages and severity **within the sample**.
They retain sample counts, first/last timestamps, index/document IDs, and trace
IDs. Message excerpts stop at 800 characters with explicit truncation and a
full-message hash; matching excerpts alone do not merge groups. Matching totals
are reported separately with `eq` (exact) or `gte` (lower bound). Counting stops
at 10,000 matches. `sample_complete` is true only if an exact total equals the
returned count. An empty match is not proof of service health.

After configuration, run all live checks:

```bash
export SENTINEL_LOG_INDEX='otel-logs*'
export SENTINEL_LOG_SCHEMA=infra/docker/log-schema.json
make check-live-telemetry
```

Without the index and schema settings, log integration tests skip explicitly.
`SENTINEL_LIVE_SERVICE` defaults to `payment` and can select another observed
service that emits both traces and logs. All six backend integration checks
passed locally on 2026-10-04, and actual incident traces/logs were correlated.

## Before agent work

The first real fault and recovery are documented in
[the validation record](validation/payment-failure.md); review
[checkpoint 1](checkpoints/01-architecture.md) before agent implementation.
Deterministic tools should
reduce duplicate logs and summarize relevant spans/metrics before passing
evidence to the model. Runtime measurements and captures must come from actual
queries; tests with fabricated fixture data establish parser behavior only.
