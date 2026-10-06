# Resume evaluation: Sentinel — AI Incident Investigation Agent

**The original 48-attempt cohort is executed, reviewed, and recalculable. The
abstention follow-up is blocked by ChatGPT Subscription Sharing limits; this
sprint is not complete.** Results below describe the original cohort, including
failed requests and exhausted budgets. They are development measurements, not
production reliability claims.

Sentinel supplies the typed diagnostic adapters, telemetry reduction, context
selection, model loop, policy, audit, evaluation harness, and recorded-run viewer.
The monitored services and existing fault branches belong to the external
OpenTelemetry Demo. The PRD is not implementation evidence.

## Counts and evidence

| Cohort | Actual AI attempts | Purpose and treatment |
| --- | ---: | --- |
| Fixed primary | 36 | Three runs on each of 12 captured cases; used for primary metrics. |
| Matched context baseline | 12 | Three runs on four of those cases; paired with the corresponding primary runs. |
| Initial development cohort | 3 | Failed before an action-contract/context correction; retained separately. |
| Operational probe | 1 | Single-call availability probe, not a diagnosis benchmark. |
| Control follow-up so far | 3 | All quota failures; 15 planned, 12 unexecuted. No original trial is replaced. |
| Total sprint attempts so far | 55 | 48 original + 3 initial + 1 probe + 3 blocked follow-up. |

The fixed cohort has **12 scenarios: 9 diagnosis-expected faults and 3 abstention
controls**, 48 bound semantic reviews, 348 model calls, and 360 actual diagnostic
reads. Repetitions share **one real native-tool capture per case**. These are
48 live model investigations over captured real telemetry, not 48 independent
fault injections or live-backend latency experiments.

Public records: [investigations](../../evals/reports/resume-20261005/investigations.jsonl),
[reviews](../../evals/reports/resume-20261005/reviews.jsonl),
[summary](../../evals/reports/resume-20261005/summary.json),
[configuration](../../evals/reports/resume-20261005/configuration.json),
[exact evaluated catalog](../../evals/reports/resume-20261005/scenarios.json), and
[capture checks/runtime identities](../../evals/reports/resume-20261005/captures.json).
These are publication-limited per-run results, native evidence projections, and
original model decisions. Full tool corpora, selected model contexts, SDK outputs,
and self-traces remain in local, gitignored `var/resume-evaluation/` directories;
provider-private records and credentials are excluded from publication.

## Method and fixed configuration

The external target is OpenTelemetry Demo 3.1.0, source commit
`dedc0178918e260823323b8d95005a8cb924b007`, running in the isolated Docker Compose
lab. The evaluated agent/harness source is commit
`c27bbb317f7666a10b54e3f317db18d8230c0563`, with source fingerprint
`bf16f03662efca7c24fd1ef93c133ce04b8778d187039156d0064206823c43f5`.
The catalog fingerprint is
`e813e73e669fea378632c10c03dfa375935e98c3cbdfaad3f66369b873a49e15`.
Later harness/reporting corrections do not retroactively change that cohort.

| Setting | Fixed value |
| --- | --- |
| Model | `gpt-5.6-luna`, selected from the authorized account catalog |
| Transport | Direct OpenAI Responses SDK, public endpoint, streamed ChatGPT OAuth plan usage |
| Model/tool call bounds | 10 / 12 per investigation |
| Reported-token admission bound | 100,000 per investigation |
| Selected context / response bound | 32,000 / 12,000 UTF-8 bytes |
| Runner / request timeout | 300 / at most 30 seconds |
| Repeats | 3 per case per evaluated strategy |
| SDK retries / parallel tool calls | Disabled / disabled |
| Output-token limit | Not sent on the subscription route; the local response-size bound applies |
| Monetary cost | Unknown; subscription usage is not API dollar billing |

The model alias is retained rather than a claimed immutable server snapshot.
Preview transport omits unsupported sampling settings, so no temperature/seed is
claimed. The fixed main-cohort aggregate admission allowance was 3,887,726
reported tokens after the initial 112,274-token cohort, within a 4,000,000-token
sprint allowance. Unknown-usage requests make this an admission bound over
reported subtotals, not a guaranteed hard credit or actual token-consumption cap.

Each case has a fresh 180-second baseline and 180-second incident window, with
settling/export waits outside the windows. The capture queries real Prometheus
span-derived metrics, OpenSearch logs, Jaeger distributed traces/dependencies,
pinned source, and the current mounted flag snapshot. Existing adapters parse
backend results. Ground truth, injected-fault labels, Docker runtime snapshots,
and preparation checks stay outside model context. The model receives only the
symptom, service, explicit time windows, and requested evidence.

Native tool replay gives each repetition and comparison arm the same immutable
observations. The agent still chooses reads, updates hypotheses, selects context,
and requests live model inference. A corpus hash prevents silent data changes;
source/configuration changes require a separate cohort. Alternating comparison
order reduces order effects. There is no automatic retry of a completed failed
trial. Guard stops/resumptions and rejected preparations are retained in the
[method records](../../evals/reports/resume-20261005/method/).

### Preparation details and limits

- Four real preparations were rejected: default domestic shipping traffic did
  not exercise the international branch; Docker inventory timed out before
  injection; post-collector-stop Jaeger inventory timed out; and Kafka restarted
  during a baseline. An additional operator preflight was stopped before capture
  or injection to remove fault-specific wording from inventory metadata. None
  entered model scoring. Kafka's original memory/heap settings were left alone;
  a restart alone does not establish its cause.
- Accepted shipping capture used real frontend cart/checkout requests with the
  upstream Canadian fixture during both windows. Two in-window shipping
  `POST /ship-order` spans lasted 5,011.266 and 5,139.793 ms. The driver waits five
  seconds after responses; it is closed-loop traffic, not a fixed-arrival load
  experiment. Shipping logs are not exported to OpenSearch in this target.
- The missing-telemetry case stops the collector. Its allowlist is bootstrapped
  from a genuine prior Jaeger service inventory, with observation time and a
  generic freshness limitation. All subsequent metrics/logs/traces/dependencies
  are actual backend queries. This is capture preparation, not agent caching.
- Checkout and product catalog use 128 MiB minimum limits after upstream 20 MiB
  limits caused restarts. Runtime/image IDs and restart counts are retained.
  These are developer target changes, not agent remediation.
- The evaluated healthy incident had sampled successful traffic and no payment
  error spans; its preceding baseline included one payment connection failure.
  That imperfection is disclosed, not silently relabeled as a pristine baseline.
  The original cart catalog called its Error logs “warning,” and shipping expected
  unavailable delay logs. Those categories receive no retrospective credit.
  Catalog v2 fixes these definitions and the stock capture now checks both
  healthy windows. Historical scoring uses the exact archived v1 catalog.

## Scoring

Each review reads the actual terminal decision, retrieved evidence, prior
hypotheses, and scenario ground truth. Reviews bind to a packet hash and identify
**Codex-assisted semantic review, not independent human adjudication**. Arithmetic
and schema validation are automated; semantic judgments remain contestable.

- **Correct:** right originating service/mechanism and scope, without a material
  unsupported additional cause. Current source/configuration must be qualified.
- **Partially correct:** substantially right mechanism with a material incorrect
  or unsupported scope/causal addition. No fractional credit enters accuracy.
- **Incorrect:** wrong or unsupported causal attribution.
- **Abstained:** explicit `insufficient_evidence` terminal action. Its appropriateness
  is scored separately; abstention on a diagnosable fault is not a correct cause.
- **Execution failure:** invalid decisions, duplicate reads, provider/context
  failures, and budget exhaustion. These stay in denominators and are not abstention.

Fault accuracy divides correct root causes by all diagnosis-expected trials.
Healthy/missing/ambiguous controls are separate. Grounding divides fully supported
material causal claims by emitted diagnoses; valid citation IDs are a different
metric. Typed citation fields are validated by the application, but not every
citation embedded in prose. Expected-evidence and required-tool coverage measure
catalog coverage, not calibrated retrieval precision or tool-selection accuracy.
Unrelated/unconfigured reads are distinguished from reasonable hypothesis tests.
Safety records advisory violations and unsafe recommendations separately from
actual infrastructure execution. Confidence scores are ranking indicators.

Distributions use arithmetic mean, median, and nearest-rank p95. Runner latency
includes model requests, replay work, and tracing shutdown, but excludes capture
waits and authentication preflight. It is not live backend response time or MTTR.
Complete-usage token distributions exclude every investigation with unknown usage;
reported aggregate totals remain lower bounds. Failed-request model latency was
not recorded by the evaluated provider, so those missing measurements are explicit.

## Primary results: 36 attempts

### Root cause and abstention

**9/27 fault trials (33.3%) produced a correct root cause**, with one partial
cause, one fault abstention, and 16 execution failures. The overall primary
terminal states were 12 diagnoses, one explicit abstention, eight budget stops,
and 15 other failures. Only 10 diagnoses were on faults; the other two were
qualified no-current-fault findings on the healthy control.

| Case | Correct / 3 | Partial | Abstained | Execution failures |
| --- | ---: | ---: | ---: | ---: |
| Payment error branch | 1 | 0 | 0 | 2 |
| Cart EmptyCart bad-store branch | 1 | 1 | 0 | 1 |
| Intermittent ad failure | 1 | 0 | 1 | 1 |
| International shipping delay | 0 | 0 | 0 | 3 |
| Catalog lock contention | 1 | 0 | 0 | 2 |
| Ad CPU worker loop | 2 | 0 | 0 | 1 |
| Checkout bad payment address | 3 | 0 | 0 | 0 |
| Checkout symptom / downstream payment fault | 0 | 0 | 0 | 3 |
| Unavailable payment process | 0 | 0 | 0 | 3 |

| Control | Explicit appropriate abstention / 3 | Observed behavior |
| --- | ---: | --- |
| Healthy payment incident | 0 | Two grounded no-current-fault conclusions used `diagnose`; one budget stop. These are terminal-protocol mismatches, not fabricated fault causes. |
| Missing telemetry | 0 | Three provider failures; no terminal conclusion. |
| Ambiguous payment without source/configuration | 0 | Three first-request provider failures; no fault telemetry read or terminal conclusion. |

**Explicit appropriate abstention was 0/9 controls.** The missing/ambiguous
results do not show a model choosing a wrong cause; they show that provider
failures prevented measurement of its uncertainty behavior. The later control
follow-up remains necessary. The healthy findings support restrained no-fault
reasoning, but do not satisfy the specified abstention terminal state.

### Grounding, tools, and safety

| Metric | Primary result and denominator |
| --- | --- |
| Structurally valid diagnosis citations | 12/12 emitted diagnoses |
| Material claims supported by cited retrieved evidence | 9/12 emitted diagnoses (75.0%) |
| Expected-evidence catalog coverage | 121/144 categories (84.0%), including catalog/export limitations above |
| Required-tool coverage | 93/111 required operation slots (83.8%); attempted reads count, even if unconfigured |
| Unnecessary executed reads | 1 (unconfigured pod read); 2 across all 48 attempts |
| Unsafe recommendations | 0/36 attempts; 0/12 emitted diagnoses |
| Recommendations outside advisory scope | 0/36 attempts |
| Agent infrastructure actions executed | 0, by implementation; no execution tool exists |

No adversarial prompt-injection evaluation was run. Zero unsafe advice in these
controlled cases is not a general safety guarantee. A named correct cause can
fail grounding: ad/catalog conclusions omitted the specific citation supporting
part of the cause, and a partial cart conclusion added unsupported Valkey scope.

### Efficiency

| Measurement | Mean | Median | p95 | Scope |
| --- | ---: | ---: | ---: | --- |
| Diagnostic reads | 7.69 | 8 | 11 | All 36 attempts; includes automatic inventory |
| Model calls | 7.47 | 8 | 10 | All 36 attempts |
| Runner latency | 74.84 s | 79.45 s | 117.60 s | All 36, including fast request failures |
| Emitted-diagnosis latency | 80.31 s | 75.93 s | 119.31 s | 12 diagnoses; not an all-attempt success measure |
| Model-response latency | 9.98 s | 9.22 s | 16.67 s | 262 measured calls; 7 failed-call latencies missing |
| Prompt tokens | 50,452 | 46,171 | 73,122 | 29 investigations with fully reported usage |
| Completion tokens | 3,183 | 3,229 | 3,925 | Same 29 |
| Total tokens | 53,636 | 49,690 | 76,830 | Same 29 |

Primary reported subtotals: **1,525,152 input + 96,948 output = 1,622,100 tokens**.
Seven primary runs have one unknown-usage request each. Across all original 48,
**2,015,031 input + 127,156 output = 2,142,187 reported tokens**, with ten
unknown-usage requests. Including initial failures, the availability probe, and
three blocked follow-up attempts gives **2,258,634 reported tokens so far** and
13 unknown-usage requests. Actual total token/credit consumption and monetary
cost remain unknown. Neither unknown usage nor subscription inference is $0.

## Context comparison: 12 matched pairs

Structured context ranks reduced results by signal/period/recency. The simpler
baseline selects newer complete native parsed results first, without additional
agent reduction or signal ranking. Both retain the same evidence index, omission
IDs, instructions, semantic tools, 32,000-byte limit, budgets, model, and corpus.
Native adapters still parse/bound telemetry in both arms; the baseline is not an
unlimited dump of backend bytes. Both strategies can omit oversized whole results.

Comparison cases are payment, shipping, healthy payment, and ambiguous payment,
with three matched repeats each. Reduction and ordering change together, so this
is a strategy comparison, not an isolated attribution to one ranking rule.

| All 12 pairs per arm | Structured | Native newest-first baseline |
| --- | ---: | ---: |
| Correct fault root causes | 1/6 (16.7%) | 2/6 (33.3%) |
| Grounded emitted diagnoses | 3/3 | 5/5 |
| Appropriate control abstention | 0/6 | 0/6 |
| Mean diagnostic reads | 6.58 | 6.92 |
| Mean model calls | 6.42 | 6.58 |
| Mean runner latency | 61.90 s | 68.25 s |
| Reported token subtotal | 431,410 | 520,087 |
| Unknown-usage investigations | 3 | 3 |

Three ambiguous first-request failures in each arm depress means and supply no
model-behavior comparison. The **nine pairs with complete usage in both arms**
(payment, shipping, healthy) provide the following descriptive efficiency subset.
Failed/budget-stopped investigations with known usage remain in this subset;
all pairs remain in the accuracy denominators above.

| Nine complete-usage pairs per arm | Structured | Baseline |
| --- | ---: | ---: |
| Mean prompt / completion tokens | 44,962 / 2,973 | 54,431 / 3,356 |
| Mean total tokens | 47,934 | 57,787 |
| Mean reads / model calls | 8.44 / 8.22 | 8.89 / 8.44 |
| Mean / median runner latency | 81.34 / 76.40 s | 89.60 / 93.26 s |

**The experiment does not show an accuracy benefit for structured selection.**
The baseline produced one more correct payment diagnosis; neither arm diagnosed
shipping or explicitly abstained on a control. Token/latency differences are
exploratory observations on a small development subset with differing terminal
behavior, not a general efficiency gain or a reliability improvement claim.

## Failures, corrections, and blocked follow-up

The [initial three attempts](../../evals/reports/resume-20261005/initial-aborted-cohort/)
used 21 model calls, 21 reads, and 112,274 reported tokens before correction. One
terminal action mixed a diagnosis with a tool; two baseline runs repeated an
omitted source read. Commit c27bbb3 introduced the action-specific nested schema
union. Both arms received identical action/omission instructions, and the baseline
changed from oldest-first to newest-first so later reads were usable. These
changes were informed by failures: this is not a preregistered or held-out study.
See [ADR 010](../decisions/010-repeated-ai-evaluation.md).

The fixed cohort still exposed limitations that ordinary schema tests missed:
source omitted from selected context led to rejected duplicate source reads;
correct flag naming did not always include a supporting mechanism citation;
all six shipping attempts failed despite actual delayed spans; and some runs
continued collecting evidence until the ten-call limit rather than concluding.
Eight original failures were `DecisionError`; ten were `ModelError`. The other
12 unsuccessful original attempts exhausted budgets. Unknown-usage errors in the
original provider did not retain enough transport diagnostics to attribute all
of them to quota.

A separate one-call operational probe succeeded in making a diagnostic read,
used 2,113 reported tokens, and stopped at its one-call budget. It is not evidence
of a successful diagnosis. The subsequent planned 15-attempt control follow-up
executed **three attempts**, all rejected by the provider's explicit Subscription
Sharing usage-limit message. One received an initial read decision; the other
two failed on their first model request. Their 2,060 reported-token subtotal is
incomplete; all three have unknown usage. Records are retained separately in
[the blocked control ledger](../../evals/reports/resume-20261005/controls-followup/).
No original failure is retried or replaced. Twelve follow-up trials remain.

OpenAI's [recovery guidance](https://developers.openai.com/siwc/token-sharing-open-source/errors-and-recovery)
says to pause new plan-usage requests and review ChatGPT Settings → Usage. The
error alone establishes neither a reset time nor whether the limit is plan-wide
or app-specific. No paid API fallback or new sign-in was attempted. A detached
c27bbb3 checkout preserves the original inference configuration for continuation
once usage is available; future observations will be reported separately.

Post-cohort changes add failure latency and safe provider type/status/quota
metadata, stop a future batch immediately after a known quota failure, archive
the exact scoring catalog, fix future catalog/admission defects, and incorporate
the shipping workload/prior-inventory preparation into the stock CLI. Both
paths reproduced real captures and cleanup, followed by six passing live
telemetry checks. Stronger missing-telemetry admission checks passed on those
immutable corpora, requiring positive baseline coverage and empty incident
metrics/logs/traces; controls no longer carry an empty-string fault-marker
check. See [post-cohort validation](../../evals/reports/resume-20261005/method/post-cohort-capture-validation.json). These changes do
not repair the evaluated agent's context omission/terminal-selection behavior or
justify applying old accuracy results to a new inference configuration.

## Recalculate and reproduce

Run offline, without credentials or private files:

```sh
uv run python scripts/run_evaluation.py verify --report evals/reports/resume-20261005
```

This checks completeness, packet/configuration/catalog hashes, review binding,
and summary arithmetic. It does not certify semantic judgments independently.
GitHub Actions performs the same recalculation. The
[evaluation guide](../learning/evaluation.md) documents capture, execution,
cleanup, review, quota handling, and frozen-source continuation.

Deterministic tests, real backend integration tests, and browser checks are
separate validation layers; none count as AI investigations. The public site
continues to show the original reviewed payment investigation, with tools,
hypotheses, evidence, confidence ranking, recommendation, and helper recovery.
It is a saved replay. Visitors do not start an agent or query the local lab.

## Known limits and remaining work

The controls need an available provider and completion of the separate follow-up
before this sprint can meet its abstention standard. Independent human review,
fresh captures across repeated injections, held-out cases, stronger causal-context
retention, and budget-aware terminal behavior would strengthen the next study.
More technology would not address those measured failure modes.

Ground truth is controlled, source-readable, and sometimes directly exposed by
current flags. Bounded/sparse telemetry, catalog defects, one capture per case,
model aliases, provider availability, and assisted grading limit generalization.
Jaeger returns whole matching traces: child spans may extend outside the queried
window. A full trace envelope is neither the requested service's latency nor a
computed critical path. Runtime images and pinned source are recorded, but source
inspection is not exact build-artifact attestation. CPU branch evidence does not
supply a measured CPU percentage. Confidence is not a calibrated probability.

Sentinel has no AWS/Terraform deployment, MCP server, database-backed incident
state, automatic detection service, GitHub diagnostic tool, or executable
remediation. Kubernetes is a separately validated read-only kind fixture; the
monitored application and the evaluation cohort run in Compose.
