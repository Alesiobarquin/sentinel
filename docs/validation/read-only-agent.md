# Read-only agent implementation validation

This record separates deterministic implementation tests, live adapter/fault
validation, and future live AI evaluation. No real model call, live OAuth grant,
AI diagnosis accuracy, or portfolio-readiness result is claimed.

Final deterministic checks: 106 tests passed with eight live cases skipped on
Python 3.12.12, 3.13.5, and 3.14.7. Compilation also passed. CI's locked environment
is configured for 3.12/3.14 but has not run on GitHub. See the later live-resource
failure below; a passing deterministic suite cannot certify backend availability.

## Implemented behavior

Closed incident/tool/model contracts, explicit hypotheses, evidence IDs,
deterministic context bounds, service policy, repeated-read rejection, independent
tool/call/token/cost limits, no SDK retries, completed-stream handling, citation
validation, and explicit failure/insufficient/budget outcomes are implemented.
Run artifacts preserve model decisions and tool payloads outside selected context.
Sentinel itself produces OTel investigation/context/model/tool spans.

Auth tests use locally signed RSA tokens and a real loopback callback with mocked
public token/JWKS requests. They check issuer/audience/expiry/nonce/signature,
state/client/PKCE/redirect, granted scope, account match, protected files, and
rotating refresh. These do not prove the real account can authorize plan use.
Public OIDC discovery independently confirmed issuer, JWKS, RS256, and revocation
endpoint. The real consent/token exchange awaits the developer.

## Live reads and Sentinel telemetry

On 2026-10-05 all eight semantic tools worked against the pinned Compose demo:
service inventory, latency ranking, metrics, logs, traces, dependencies, current
configuration, and allowlisted source. Captures and tool timing are under
`var/live-validation/phase-1/`. A 300-second latency ranking reported checkout
at approximately 1,880 ms p95 from the span-derived histogram. This is one
observed telemetry estimate, not an application benchmark.

Sentinel OTLP export reached the existing collector and Jaeger. Trace
`12f6ba26f977252fda866fbae8a896a6` contains nine spans under service `sentinel`
(one validation root and eight reads). `validation.llm_invoked=false` distinguishes
this from an AI run. The raw Jaeger response and local span records were retained.

Two live Kubernetes tests passed with the actual service-account credentials.
Pod/event reads were allowed; creation/patching, secrets, and another namespace
were denied by `auth can-i`. The initial 32 MiB pod reported two OOM restarts,
which the adapter preserved. A recreated 64 MiB fixture was initially ready
without restarts, but later that pod and CoreDNS were OOM-killed. A combined
111-test run then failed its two Kubernetes tests on API timeouts. VM memory
showed about 459 MiB available and effectively zero free swap; failure inspection
and the failed suite remain under `var/live-validation/`. Compose and kind are
subsequently validated separately on this shared Docker VM. The
cluster is cleaned up after verification to release Docker resources. This
fixture does not establish that the Compose demo runs in Kubernetes.

After stopping only Sentinel's Compose services and recreating kind, both live
Kubernetes tests and all six role checks passed. The pod was ready with zero
restarts, and available VM memory was about 3.62 GiB. The test took 0.394 seconds
in that one isolated run; this is not a latency benchmark. Independent live
targets are now explicit Make targets. Other projects were left running.

Kind was then deleted and the full demo restored. All 28 services were running,
configured health checks passed, and all six fresh telemetry tests passed. The
common telemetry transport now rejects redirects; a real loopback test verifies
that a redirect does not trigger a second read. Restarting Jaeger can clear its
in-memory trace history, so historical claims refer to retained raw captures.

## Three real fault scenarios

The deterministic run used 90-second baseline/fault/recovery windows and a
20-second export allowance. It ran sequentially with all feature defaults initially
off and restored each prior flag. Artifacts are under
`var/scenarios/20261005T042153.638594Z/`.

| Fault | Selected service error spans in fault | Selected warning/error logs in fault | Estimated server error calls | Recovery sample |
| --- | ---: | ---: | --- | --- |
| Payment charge failure | 10 across five traces | 5 warnings | Missing; preserved as unknown | 0 selected service errors and 0 warning/error logs |
| Cart EmptyCart failure | 1 | 1 error | Approximately 5.096 | 0 selected service errors and 0 warning/error logs |
| Intermittent ad failure | 0 | 1 warning | Approximately 2.075 | 0 selected service errors and 0 warning/error logs |

Counts are bounded samples, not incident totals. Payment can have server and
internal error spans for one request; ten spans are not ten failed payments.
`increase()` is extrapolated and can be fractional. Missing metric series are
not zeros. The ad trace sample missed the intermittent failures while a warning
and status counters showed them. Recovery metric estimates were zero in these
windows, but the samples do not prove there were no later failures.

This run exposed two reduction/parser issues: equivalent legacy string/native
boolean `error` tags were rejected, and long upstream errors could occupy all
selected span slots. Both are fixed and covered by tests. True contradictory
tags still fail. The corrected reducer guarantees a requested-service span and
prioritizes its errors. Historical windows were reread with the corrected adapter,
with new tool audits and `corrected-traces.json`/`corrected-report.json`. Original
failures and captures remain intact. The original batch exited nonzero because
of its pre-fix payment baseline trace failure; it is not relabeled as a clean run.

The collector had recently been recreated to publish loopback OTLP. Short-window
metric absence remains unexplained by a measured sample-timing audit; it is not
attributed definitively to that restart. The first live exercise uses a longer
180-second window and a 30-second export allowance, while still treating missing
metrics as unknown. The developer's Docker also hosts other projects, so these
are uncontrolled local validation observations, not reliable performance trials.

After completion, every feature default was `off` and the tracked fault state
was absent. No agent infrastructure write or paid cloud resource was involved.

## Fresh post-fix scenario run

The batch under `var/scenarios/20261005T050922.978004Z/` completed successfully
after the parser fixes and demo restoration. It used 180-second windows with
a 30-second export allowance. All 45 semantic reads succeeded; no LLM was invoked.
Each baseline had zero selected error spans and warning/error logs. Each recovery
had zero estimated error calls, selected error spans, and warning/error logs.

| Fault | Selected service error spans | Selected warning/error logs | Estimated server error calls |
| --- | ---: | ---: | --- |
| Payment charge failure | 12 across six traces | 11 | Approximately 13.682 |
| Cart EmptyCart failure | 0 in the bounded trace sample | 2 | Approximately 3.986 |
| Intermittent ad failure | 3 | 6 | Missing; preserved as unknown |

The updated metrics tool was then exercised over all nine saved windows, with
new audited `metric-coverage.json` captures. The payment and cart fault windows
had two minimum error-counter samples. The ad fault window had one raw error
sample, independently retained in `raw-counter-samples.json`; this explains why
an error increase could not be computed for that series. It does not explain
the older batch's missing payment estimate. The cart trace sample missed failures
that metrics and logs observed. Fractional estimates and sampled span/log counts
retain the same interpretation limits as the earlier table.

All feature defaults were `off` and tracked fault state was absent after this
batch. This establishes a clean capture/cleanup run, not AI diagnosis accuracy.

## Remaining acceptance work

Complete real browser sign-in and confirm a smaller available model. Run one
bounded investigation; verify the actual causal explanation, hypotheses,
citations, usage, latency, and failure behavior. Present checkpoint 2 and have
the developer reproduce it manually. Then continue guide phases: persistence/API,
web product, measured repeated AI evaluations, GitHub context, controlled
remediation, MCP, and explicitly approved ephemeral cloud deployment.

The three-case catalog is a start, not ten-case portfolio evaluation. Keyword
grading is only a review signal; even negating the expected flag can match a
keyword. No automatic correctness score is inferred. See
[learning questions](../learning/investigation.md) and
[recorded progress](../progress.md).
