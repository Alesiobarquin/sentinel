# ADR 010: repeated investigation evaluation on real captured telemetry

## Context

The developer authorized an evaluation sprint and a comparison of deterministic
reduction/bounded context with a simpler context strategy. One successful model
diagnosis does not establish accuracy. Requerying mutable source/configuration
and sampled traces separately for each strategy would confound the comparison.

## Decision

Use twelve controlled cases in the pinned Docker Demo, including three abstention
controls. Query the real Prometheus, OpenSearch, and Jaeger backends in each
case's baseline/incident windows, and freeze native parsed results plus reduced
summaries in a hash-bound tool corpus. No ground truth enters model context.
Run three independent fixed-model investigations per case. Compare four selected
cases with three baseline repeats using identical tool corpora and budgets.

The normal strategy retains ranked, reduced results. The baseline selects whole
native parsed results in newest-first chronological order with the same byte bound, evidence
index, tools, instructions, citation validation, and stopping rules. It receives
broader results; no useful fields are deliberately removed. Both strategies may
omit whole entries at the shared context limit, with explicit omission IDs.
This comparison measures the combined reduction/ordering choice, not either
component in isolation. Replay isolates model/tool-selection variability; it
does not measure live backend response variability or full incident MTTR.

Ground truth and semantic review are separate from model runs. Structural checks
alone are not correctness. Review claims and citations against the captured
evidence; publish per-run decisions, verdicts, denominators, and summary code.
Record review as Codex-assisted, not independent human adjudication. Preserve all
failures and incomplete preparations. No run is silently retried or omitted.

The initial cohort was stopped after three failures (one action-shape failure,
two duplicate reads). It is retained separately from the corrected cohort. The
flat schema did not express mutually exclusive read/diagnosis fields; expose
the Python constraints through a nested union in the strict model schema.
[OpenAI's schema documentation](https://developers.openai.com/api/docs/guides/structured-outputs)
supports nested unions and requires an object at the root. Both strategies
receive the same clarified action/omission instructions. The initial baseline
retained oldest results first and crowded out a newly requested source read;
use the ordinary newest-first alternative for the final comparison. This
change follows inspection of the failed attempts, so the final comparison is
development-set evidence, not a preregistered or held-out benchmark.

The pinned checkout/product-catalog 20 MiB limits showed repeated restarts before
evaluation. Normalize these two local limits to at least 128 MiB, record runtime
identity/restarts with each capture, and require clean baseline windows. This is
local target preparation, not agent remediation or paid infrastructure.

## Alternatives

Fresh fault injection per model run adds expensive waits and sampling changes.
Synthetic fixture answers would bypass the telemetry stack. An LLM-only judge
would introduce another model/provider and grading uncertainty. A deliberately
truncated baseline would not test a credible simpler implementation.

## Consequences

Snapshot replay retains bounded native tool data, not every raw backend document.
Repeated runs share one capture per case, so confidence intervals cannot treat
all repetitions as independent environments. Faults are controlled and often
source-readable. Current flag snapshots cannot establish historical evaluation.
Complete private corpora remain local; reviewed field-restricted results can be
published. Model requests use the existing sign-in, capped per-run budgets, and
an aggregate usage stop. Subscription monetary cost remains unknown.

## Reconsider when

Additional independent captures or held-out natural incidents are available;
judgments need independent human review; or measured results justify changing
the agent architecture. Keep the current single agent and read-only permissions.
