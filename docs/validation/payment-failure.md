# Live validation: payment-failure scenario

**Run date:** 2026-10-04. **Result:** real fault reproduced, prior `off` variant
restored, successful new payment transactions observed. This is deterministic
manual investigation evidence, not an AI diagnosis or an accuracy benchmark.

## Target and capture provenance

The isolated `sentinel-demo` Compose project ran official Demo 3.1.0 at commit
`dedc0178918e260823323b8d95005a8cb924b007`. It had 28 services and 19 discovered
trace identities. Prometheus, Jaeger 2.19.0, and OpenSearch 3.7.0 passed live
adapter checks. The initial readiness probe incorrectly expected `up`; live
discovery showed OTLP-pushed metrics, and readiness was corrected to require a
positive `count({__name__!=""})` result. A subsequent probe observed 8,186 active
series, trace services, and a yellow single-node OpenSearch cluster. These smoke
results alone did not establish incident diagnosis or log ingestion.

Local captures are [baseline.json](../../var/live-validation/baseline.json),
[incident.json](../../var/live-validation/incident.json), and
[recovery.json](../../var/live-validation/recovery.json). Each contains the source
pin, window, query results, coverage limits, errors, and on-disk flag variant.
All six independent reads succeeded in each capture. `complete=true` describes
successful reads, not complete incident coverage. Files under `var/` are ignored
and will not appear in a fresh checkout; this document preserves the observed
facts and the [runbook](../runbooks/payment-failure.md) reproduces the collection.
Tool starts/finishes are recorded in
[the local audit file](../../var/audit/tool-calls.jsonl).

## Measured windows and observations

All timestamps below are UTC. Windows differ in length; these counts should not
be compared as rates or used as diagnosis-accuracy scores.

| Observation | Baseline | Fault | Recovery |
| --- | --- | --- | --- |
| Window on 2026-10-04 | 23:19:08.839–23:21:08.839 | 23:22:17.066–23:31:22.090 | 23:31:30.659–23:37:02.804 |
| Window duration | 120 s | 545.025 s | 332.145 s |
| Flag on disk at capture | `off` | `100%` | `off` |
| Returned payment traces | 9 | 10; result limit reached | 6 |
| Selected payment server ERROR spans | 0 | 10 | 0 |
| Payment logs returned | 18 | 40 | 12 |
| `Transaction complete.` logs | 9 | 0 | 6 |
| Matching payment failure warnings | 0 | 20 | 0 |
| Returned trace IDs also present in payment logs | 9 | 10 | 6 |
| Dependency edges returned | 38 | 35 | 39 |

OpenSearch reported exact matching totals equal to each returned sample at query
time. The trace endpoint has no exact matching total; the incident's ten-trace
limit means additional traces were omitted. Each sampled fault trace includes
both a payment server error span and an internal `charge` error span. The twenty
selected payment error spans therefore represent ten sampled failed calls.
The dependency graphs aggregate observed calls, include self-edges, and are not
complete static topologies.

The file write enabling `100%` occurred at Unix second `1791156137.0657625`;
the first captured warning was at `1791156144.515`. Reset restored the previous
`off` value at `1791156690.658593`; the first captured completion afterwards was
at `1791156727.073`. File-write timestamps are not runtime acknowledgments, and
these observations are not measured agent detection or remediation latency.

## Independent evidence and causal explanation

Representative failing trace: **`aa826bf337f6adc1dd937c3f2c66184a`**, beginning
at Unix second `1791156650.012192`. It contains:

| Service / operation | Span ID | Observation |
| --- | --- | --- |
| Payment / `oteldemo.PaymentService/Charge` | `6bfa2c553c2fb3b1` | ERROR, 4.507 ms, matching status description |
| Payment / `charge` | `ed269575ee9bd87f` | ERROR, 1.155 ms; child of the payment server span |
| Checkout / payment client call | `4754b78a37401891` | Parent of payment server span; gRPC `UNKNOWN` and matching description |
| Checkout / `PlaceOrder` | `e358ff4bb1b8fd56` | ERROR; failed-to-charge description includes the same cause |
| Frontend / checkout API route | `467b727c0e3a8354` | ERROR and HTTP 422 |
| Load generator / POST | `d8a8c505aa62ae1d` | Observed HTTP 422 |

The correlated payment warning is document **`l2pBCaEB3jXhgCdUh14L`** in
**`otel-logs-2026-10-04`**, timestamp `1791156650.575`, with that same trace ID.
Its message is:

```text
Payment request failed. Invalid token. demo.user_context.loyalty_level=gold
```

The pinned upstream
[charge implementation](https://github.com/open-telemetry/opentelemetry-demo/blob/dedc0178918e260823323b8d95005a8cb924b007/src/payment/charge.js#L38-L49)
evaluates `paymentFailure` numerically. The `100%` variant is `1`, so its random
comparison always enters the fault branch. That branch assigns the `gold`
attribute and throws the exact observed error before normal card processing.
It does not select an existing gold customer cohort. The catch path records
an exception and ERROR status; the
[service handler](https://github.com/open-telemetry/opentelemetry-demo/blob/dedc0178918e260823323b8d95005a8cb924b007/src/payment/index.js)
logs the exception at `warn` and returns the error. Trace parent references and
matching descriptions connect this failure to checkout and frontend symptoms.

The diagnosis is an enabled simulator fault, not a proven real token-provider
failure or deployment regression. The controlled change, exact code branch,
independent correlated logs/traces, and new successful calls after restoration
provide the manual causal evidence.

## Queries, schema, and timing limits

The payment call-counter expression is:

```promql
traces_span_metrics_calls_total{service_name="payment",span_kind="SPAN_KIND_SERVER",span_name="oteldemo.PaymentService/Charge"}
```

Capture range evaluations used a 15-second step. Baseline `STATUS_CODE_UNSET`
samples rose from 28 to 37. During the fault, ERROR samples rose from 0 to 19;
UNSET samples rose from 40 to 43 early and then flattened. These are cumulative
exported observations, not exact event-time counts. The fault capture contained
no completion logs, so the early UNSET rise must not be treated as proof of
healthy charges inside the fault period.

After reset, ERROR samples moved from 20 to 21 at 23:32:30.659 and stayed at 21
through the final evaluation at 23:37:00.659. UNSET samples rose from 43 to 49.
The initial ERROR rise is consistent with delayed export of a preceding failure;
these captures alone do not identify that individual event. Recovery is supported
by six new correlated traces/completion logs without observed errors, plus the
subsequently stable error counter. The discrepancy is retained explicitly.
An additional warning query around reset did not return and was canceled without
a completed capture. It supplies no extra event-level evidence; the export-timing
explanation remains an inference rather than a proven attribution of that event.

Server-span p95 uses:

```promql
histogram_quantile(0.95,sum by(service_name,le)(rate(traces_span_metrics_duration_milliseconds_bucket{span_kind="SPAN_KIND_SERVER"}[2m])))
```

This has millisecond units and combines server operations within each service.
It is not a checkout critical path or SLO. Payment did not need to become the
highest-latency service to cause this failure; ranking latency alone cannot
identify the root cause.

Logs use index expression `otel-logs*`, exact payment service filtering, a
`[start,end)` range, and a 100-document newest-first limit with
[the verified schema](../../infra/docker/log-schema.json). The service field is
`resource.service.name.keyword`, timestamp is `@timestamp`, body is `body`,
severity is `severity.text.keyword`, and correlation is `traceId`. The source
contains literal dotted resource keys. Payment warning labels are lowercase.
Traces use the same window, at most ten traces and ten selected spans per trace.
All HTTP reads have a timeout and payload bound; failures are surfaced without
automatic retries. No live failure was hidden or retried into a passing result.

## Reproduction and remaining work

Use the [manual runbook](../runbooks/payment-failure.md) to repeat baseline,
injection, incident capture, reset, and recovery. The lab remains running with
the prior `off` variant restored. Stop it with `make demo-down` when finished.

AI hypotheses, evidence IDs for model context, model calls/costs, graders,
Kubernetes state, and approved remediation are not implemented. This is one
validated developer scenario; the portfolio requires broader scenarios and
measured agent behavior. Review [checkpoint 1](../checkpoints/01-architecture.md)
before beginning the investigation agent.
