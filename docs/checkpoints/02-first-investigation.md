# Checkpoint 2: first correct live AI investigation

**Status: acknowledged by the developer on 2026-10-05.** The developer replied
“Acknowledged” after receiving this concrete review. Correct diagnosis and sampled
recovery are verified. This uses real telemetry from the pinned external OpenTelemetry Demo.
It is one correct case after two failed model investigations, not an accuracy benchmark.

## Result to review

Run `b4e5c4bc-ad01-4fde-b147-6446762705e2` used `gpt-5.6-luna` through ChatGPT
sign-in. Sentinel identified the enabled `paymentFailure` fault branch as the
cause of payment charge errors. It recommended human review of a reversible
flag revert and did not execute remediation.

| Recorded measurement | Value |
| --- | --- |
| Model calls / read-only tool calls | 8 / 8 |
| Reported input / output tokens | 45,171 / 3,209 |
| Total reported tokens / run budget | 48,380 / 50,000 |
| Investigation latency | 120,076.353 ms |
| Billing | ChatGPT subscription; exact credit/dollar consumption unavailable |
| Baseline / incident windows | 180 seconds each |
| Baseline / incident estimated server errors | 0 / 8.99977500562486 |
| Incident warning logs | 6 of 12 returned records |
| Incident traces returned / selected for context | 6 / 3 |

The model's confidence value, `0.94`, is a ranking indicator, not a calibrated
probability. Token and call limits were respected; subscription mode cannot
enforce an exact credit cap or server-side per-response output limit.

## Evidence and causal review

| ID | Tool | Observation |
| --- | --- | --- |
| `ev_001` | Service discovery | Traced inventory establishes allowed service reads. |
| `ev_002` | Incident payment metrics | Approximately nine span-derived server errors; three raw counter samples per status; p95 server-span duration 48 ms. |
| `ev_003` | Incident payment logs | Six warnings with the exact invalid-token failure message and six charge-received logs; all twelve matching records returned. |
| `ev_004` | Incident payment traces | Failing payment spans and matching errors propagated into checkout; six traces returned, with three selected for model context. |
| `ev_005` | Pinned payment source | `charge.js` evaluates `paymentFailure` and throws the matching message inside its failure branch; `index.js` logs and returns the gRPC error. |
| `ev_006` | Current flag snapshot | `paymentFailure` default variant `100%`, numeric value 1, no targeting. This is a current mounted-file snapshot. |
| `ev_007` | Baseline payment metrics | Zero estimated server errors, approximately 7.5 unset-status server calls, three raw counter samples per status. |
| `ev_008` | Baseline payment logs | Eight charge-received and eight transaction-complete logs; no warning group in the returned sample. |

The final diagnosis cites `ev_002` through `ev_007`. Every citation refers to a
successful, earlier read. The eight tool calls totaled about 3.87 seconds; the
remainder includes model requests, context work, and trace-export shutdown.

The explanation matches the independently known injected scenario. An invalid-token
message alone could suggest a credential problem. Matching logs/traces, a healthy
baseline, an exact source branch, and the enabled configuration jointly distinguish
the synthetic fault mechanism. The gold loyalty attribute is assigned inside the
fault branch; it does not identify a preselected customer cohort.

All six raw warning trace IDs occur in the six returned traces. For example,
trace `07c916c0b0628d5bfc3866fedfdc49a0` contains payment server span
`d15b68134aeba145`, internal charge span `ff12f2c9ccc186f2`, and checkout span
`f6aa88f904290f05`, each carrying the matching propagated error.

A current file cannot prove historical effective evaluation, pinned local source
cannot prove image contents, fractional Prometheus increases are estimates, and
bounded traces omit spans. The diagnosis preserves these qualifications.

## Recovery and observability

The developer exercise restored the previous flag variant immediately after the
investigation. Sentinel has no configuration-write executor. All five baseline
reads and all five recovery reads succeeded. Recovery showed zero estimated
payment server errors, zero selected payment error spans, and zero sampled
warning/error logs. The recovery window was 15:06:00–15:09:00 UTC on October 5;
the initial baseline was 14:56:38–14:59:38 UTC. All feature-flag defaults were
verified `off`, and the tracked fault file was absent. These are sampled recovery
observations, not proof of complete health across the distributed application.

Twenty-five Sentinel self-trace span records are retained locally. The OTLP HTTP
export reported a timeout during this run; delivery of its complete self-trace
to Jaeger is not established. This did not erase the local audit. Earlier
self-instrumentation validation is a separate result.

## Relevant code and artifacts

- [Typed decisions and budgets](../../sentinel/agent/contracts.py).
- [Fixed queries, reduction, and source/configuration reads](../../sentinel/agent/diagnostics.py).
- [Bounded context selection and omissions](../../sentinel/agent/context.py).
- [Policy, citation validation, and investigation loop](../../sentinel/agent/runner.py).
- [Model transport and finalized stream validation](../../sentinel/agent/provider.py).
- [Developer-owned setup, reset, and recovery](../../scripts/first_investigation.py).
- [External failure branch](https://github.com/open-telemetry/opentelemetry-demo/blob/dedc0178918e260823323b8d95005a8cb924b007/src/payment/charge.js#L38).
- [External gRPC error/log path](https://github.com/open-telemetry/opentelemetry-demo/blob/dedc0178918e260823323b8d95005a8cb924b007/src/payment/index.js#L12).

Gitignored records in `var/investigations/b4e5c4bc-ad01-4fde-b147-6446762705e2/`
contain decisions, contexts, full evidence, native responses, audit, local spans,
and `result.json`. The baseline/reset/recovery exercise is
`var/first-investigation/20261005T150008.891540Z/`. Public replay data must be a
reviewed, filtered export, rather than these private directories.

## Reproduce and inspect

The coding agent executed this exercise through CLI at the developer's request.
These steps support hands-on learning; repeating uses another bounded investigation.

```bash
make demo-up
make demo-verify
make models
SENTINEL_MODEL=gpt-5.6-luna make first-investigation
```

Select a smaller model actually in the account catalog if availability changes.
The helper captures baseline, injects the developer-owned fault, waits for telemetry,
runs one investigation, resets even on failure, then captures recovery. Inspect
the printed run directory, match citations to evidence, compare windows, and
verify the tracked fault is gone. See the [manual runbook](../runbooks/payment-failure.md)
for independent queries. A repeat can fail; preserve that outcome.

## Five questions for review

1. What connects this error to the flag-controlled branch rather than a credential
   failure? Which claims remain inference?
2. Why is the error-call increase fractional? Why does a missing counter series
   differ from zero errors? What do three raw samples establish?
3. What can an evidence citation, source snapshot, or current configuration
   snapshot prove? What can each fail to prove?
4. Which policy and reader permissions prevent writes? Why does the exercise's
   reset not mean Sentinel executed remediation?
5. How do ChatGPT sign-in, account model availability, reported-token limits,
   exact subscription credits, and separately billed API keys differ?

## Required acknowledgment

[AGENTS.md](../../AGENTS.md) requires: “stop after diagnosing one real injected
incident.” It requires the evidence, cause, code, reproduction, and five questions
at this checkpoint. Review this concrete result before acknowledging continuation
to the public replay and explanation page. That acknowledgment is now recorded;
work proceeds to the focused recruiter site. Later write/cloud permissions and full portfolio acceptance
criteria remain separately gated.
