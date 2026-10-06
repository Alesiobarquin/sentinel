# Resume evidence audit

Re-audited on 2026-10-06 UTC against actual source, dependencies, git history,
retained real captures, fixed-model results/reviews, Docker cleanup, tests, and
the public replay. The evaluated source is c27bbb3; later source changes concern
preparation, catalog versioning, grading summaries, and failure observability.
They do not constitute a newly benchmarked investigation algorithm. The PRD was
not implementation evidence. All 63 scored attempts across the original cohort
and control follow-up are executed and reviewed, including provider failures and
budget stops. See [the full evaluation](resume-evaluation.md).

## What works end to end

Sentinel is a local Python CLI and a public Next.js investigation replay.
A developer provides a service, symptom, and incident/baseline windows. The agent
discovers traced services, requests bounded diagnostic reads, updates structured
hypotheses, and finishes with a cited diagnosis or an explicit failure,
insufficient-evidence, or budget-exhausted outcome. Full run records remain in
local JSON/JSONL files. The public site displays a reviewed, restricted export;
visitors cannot start an investigation or change infrastructure.

The original public successful exercise injected the existing OpenTelemetry Demo's
payment fault. The agent queried incident metrics, logs, and traces, inspected
pinned source and a current flag snapshot, then compared baseline metrics and
logs. Its diagnosis correctly identified the deliberate payment failure branch.
A separate developer helper reset the fault and captured recovery. The agent
did not perform remediation. The expected cause was outside the incident input;
the source and configuration tools could reveal the cause during investigation.

Sources: [runner](../../sentinel/agent/runner.py),
[local wiring](../../sentinel/agent/local.py),
[CLI](../../sentinel/__main__.py),
[exercise](../../scripts/first_investigation.py),
[reviewed public record](../../apps/web/public/investigation.json), and
[causal review](../checkpoints/02-first-investigation.md).

## Implementation and infrastructure findings

| Area | Verified implementation and boundary | Evidence |
| --- | --- | --- |
| Agent orchestration | One explicit sequential read/evidence/hypothesis loop. Model decisions select a read, diagnose, or report insufficient evidence. There is no multi-agent orchestrator. | [runner](../../sentinel/agent/runner.py) |
| Structured model output | Direct Responses SDK transport exposes one strict namespaced `investigation_step` function. Its schema contains a typed request for one of nine native diagnostic operations. Nine semantic tools does not mean nine separate model-facing SDK functions. | [provider](../../sentinel/agent/provider.py), [contracts](../../sentinel/agent/contracts.py) |
| Diagnostic tools | `services`, `latency_ranking`, `metrics`, `logs`, `traces`, `dependencies`, `runtime_configuration`, `source`, `pods`. Eight operate against the configured Compose target; pod reads require separate Kubernetes configuration. | [tools](../../sentinel/agent/diagnostics.py), [tool tests](../../tests/test_diagnostics.py) |
| Metrics | Prometheus instant/range queries and discovery; semantic reads use fixed span-derived status counter, sample-count, and p95 queries. The model cannot supply arbitrary PromQL. | [metrics adapter](../../sentinel/tools/metrics/prometheus.py), [live tests](../../tests/test_live_metrics.py) |
| Logs | OpenSearch field/schema preflight and bounded service/time searches; exact message/severity grouping retains hashes, document identity, timestamps, trace IDs, and coverage. Partial searches are rejected. | [logs adapter](../../sentinel/tools/logs/opensearch.py), [live tests](../../tests/test_live_logs.py) |
| Distributed traces | Jaeger service discovery, bounded traces and parent references, error/status parsing, selected spans, and aggregated dependency reads. This is an adapter to the pinned Jaeger UI JSON compatibility endpoint. | [trace adapter](../../sentinel/tools/traces/jaeger.py), [live tests](../../tests/test_live_traces.py) |
| Deterministic reduction | Fixed metric summaries, log grouping/ranking, selected error/requested-service spans, bounded dependency edges, and allowlisted source excerpts precede inference. Omissions and missing coverage remain explicit. | [diagnostics](../../sentinel/agent/diagnostics.py) |
| Model context | Whole reduced results are ranked by success, incident period, signal kind, and recency, then selected within a byte budget. An evidence index and omission IDs remain; full history is saved outside context. No vector database or RAG pipeline exists. | [context selection](../../sentinel/agent/context.py), [context tests](../../tests/test_agent.py) |
| Hypotheses and diagnosis | Model supplies competing hypotheses, evidence for/against, status, and confidence ranking. Python rejects invalid/failed citations, overlapping support/contradiction, and diagnoses lacking two evidence kinds including telemetry. These checks do not establish semantic causal correctness. | [contracts](../../sentinel/agent/contracts.py), [reference validation](../../sentinel/agent/runner.py) |
| Failure handling and budgets | Duplicate reads stop, SDK retries are disabled, malformed/incomplete output is surfaced, and usage is retained where reported. Call, elapsed-time, context, response-size, and reported-token limits apply. Subscription mode cannot guarantee a hard pre-response token/dollar cap. | [runner](../../sentinel/agent/runner.py), [provider](../../sentinel/agent/provider.py), [regressions](../../tests/test_provider.py) |
| Persistence and audit | Local files retain input, contexts, decisions, full evidence, model records, hypotheses, tool arguments/timing/outcomes, final usage and status. There is no database incident lifecycle or resumable service queue. | [runner](../../sentinel/agent/runner.py), [audit recorder](../../sentinel/tools/audit.py) |
| OpenTelemetry | Sentinel creates investigation/context/model/tool spans, records model usage attributes, always exports local span JSONL, and optionally exports OTLP. A separate nine-span validation trace reached Jaeger; complete OTLP delivery of the successful model run is unverified after an export timeout. | [instrumentation](../../sentinel/observability.py), local `var/live-validation/phase-1/sentinel-jaeger-trace.json` and successful run `spans.jsonl` |
| Incident creation/detection | The original three exercises and twelve-case catalog use developer-only flag/container helpers, persisted ownership, and cleanup. The agent receives a symptom/window through the CLI. No continuous alerting or automatic detection service exists. | [fault helpers](../../evals/corpus.py), [catalog](../../evals/resume-scenarios.json), [CLI](../../sentinel/__main__.py) |
| Kubernetes | GET-only pod/event adapter with namespace and response validation. A separate kind fixture uses a service-account Role/Binding restricted to pod/event get/list. Historical live tests prove read access and denial of writes, secrets, and other namespaces. The demo is not deployed on Kubernetes; the fixture has been deleted and was not recreated during this audit. | [adapter](../../sentinel/tools/kubernetes.py), [fixture](../../infra/kubernetes/fixture.json), [live tests](../../tests/test_live_kubernetes.py), local `var/live-validation/phase-1/rbac-isolated.json` |
| Docker | Bootstrap downloads pinned external source, validates provenance, renders isolated Compose configuration, requires versioned images, and binds published endpoints to loopback. The target configuration has 28 external Compose services. Sentinel's Python CLI itself runs in the local virtual environment. | [bootstrap](../../scripts/demo.py), [source lock](../../infra/docker/demo.lock.json), local `.cache/demo/compose.json` and Docker process listing |
| AWS / Terraform / MCP | No implemented AWS deployment, Terraform resources, or MCP transport/server. Native diagnostic tools and an SDK function namespace are not MCP. | Tracked file inventory, dependencies, source inspection |
| PostgreSQL / Redis | No Sentinel PostgreSQL, SQLAlchemy, Alembic, or Redis integration. `valkey-cart` belongs to the external demo. A demo error mentioning Redis is not evidence that Sentinel implements Redis caching. | [dependencies](../../pyproject.toml), source and rendered Compose inventory |
| GitHub | Repository hosting, pinned archive download, Actions CI, and Pages deployment are implemented. The investigation agent has no GitHub issue/PR/deployment adapter or write tool. | [bootstrap](../../scripts/demo.py), [workflow](../../.github/workflows/ci.yml) |
| Remediation and approval | Structured recommendations label required human review/approval. No execution or interactive infrastructure-approval workflow exists. Actual permissions are enforced by typed application contracts, source/service allowlists, read-only transports, and fixture RBAC. | [runner](../../sentinel/agent/runner.py), [contracts](../../sentinel/agent/contracts.py), [RBAC fixture](../../infra/kubernetes/fixture.json) |
| Repeated AI evaluation | Twelve structured real-target cases and immutable native-tool corpora. The original cohort has three repeats per case and twelve matched context pairs; the additional control cohort adds fifteen attempts and six pairs. All 63 attempts have semantic reviews and safety/abstention/efficiency metrics. Offline verification checks completeness, hashes, arithmetic, shared inference identity, and duplicate run IDs. | [harness](../../evals/benchmark.py), [grading](../../evals/scoring.py), [study verifier](../../scripts/summarize_resume_evaluation.py), [raw results/reviews](../../evals/reports/resume-20261005/), [report](resume-evaluation.md) |
| Concurrency and caching | Agent reads/model calls are sequential, with parallel calls disabled. Evaluation has a developer-only shipping workload thread and immutable in-memory corpus replay. Prior inventory is capture bootstrap, not agent caching. Archive/replay-record caching exists; no inference cache, asynchronous task queue, or distributed workers. | [provider](../../sentinel/agent/provider.py), [workload](../../scripts/evaluation_workload.py), [corpus](../../evals/corpus.py) |
| API and frontend | No FastAPI service or runtime frontend backend. Next.js/React/TypeScript statically exports the project notes, architecture details, and interactive saved-run viewer. | [Python dependencies](../../pyproject.toml), [web package](../../apps/web/package.json), [Next.js config](../../apps/web/next.config.ts) |
| Deployment | Public GitHub Pages website; builds validate the replay, recalculate evaluation metrics, type-check/build the frontend, and run Python/browser tests before deployment. This deploys the viewer, not a public agent/telemetry lab or production monitoring system. | [workflow](../../.github/workflows/ci.yml), [successful hosted run](https://github.com/Alesiobarquin/sentinel/actions/runs/37412976918), [live site](https://alesiobarquin.github.io/sentinel/) |

## Engineering details useful in an interview

- Model-facing schema and Python validation describe the same global/service and
  timed/untimed argument families. An actual invalid configuration-tool argument
  led to the schema fix in commit `c0b0aa8`; regression tests cover the contract.
- The provider handles finalized streaming tool items when the completed response
  has empty output, while still requiring response completion, measured usage,
  correct function identity/count/size, and agreement with terminal output when
  both representations exist.
- Trace duration uses the observed start/end envelope, not a sum of overlapping
  spans. Selection retains a requested-service span even when upstream errors
  would otherwise occupy every slot, and exposes unresolved parents and omissions.
- Log grouping hashes the full original message before truncating display text,
  preventing different long messages with matching prefixes from being merged.
- Counter sample counts make sparse telemetry explicit: one sample cannot support
  an increase/rate, and missing values are not reported as zero.
- Fault setup saves prior state before mutation and binds cleanup to an owner ID;
  one exercise cannot silently reset another exercise's fault.
- Publication verifies source-record hashes and previously available citations,
  projects nested field allowlists, preserves measured usage, and rejects failed
  or unreviewed runs. Credential-pattern screening is supplementary to review.

Relevant history: initial native/agent implementation `773b057`, model-schema fix
`c0b0aa8`, successful causal review `a471b79`, reviewed replay/deployment `dd3fcc1`,
engineering presentation `8c9ef30`, repeated-evaluation foundation `95a9d98`, and
nested action-contract correction `c27bbb3`. The initial three failed attempts
are retained alongside the fixed study; they are not silently dropped. The repository and site acknowledge AI
coding assistance; interview claims about personal understanding should be
supported by the developer's ability to explain these mechanisms.

## Verified measurements

| Fact | Result | Interpretation and evidence |
| --- | --- | --- |
| Native diagnostic operations | 9 | Eight Compose operations plus optional Kubernetes pod/event diagnostics; [descriptions](../../sentinel/agent/diagnostics.py). |
| Queried telemetry backends | 3 | Prometheus, OpenSearch, Jaeger; all six opt-in telemetry tests passed again during this audit. |
| Reproducible evaluation cases | 12 | Nine faults and three controls, each accepted from real telemetry; three model repetitions share one capture per case. Historical three-case adapter exercises are separate. [Exact evaluated catalog](../../evals/reports/resume-20261005/scenarios.json). |
| Latest retained deterministic fault batch | 45/45 reads succeeded | Three scenarios × three windows × five operations, in local `var/scenarios/20261005T050922.978004Z/reports.json`. Cart error spans were missed in the bounded trace sample; ad counter increase remained unknown. Read success is not retrieval completeness or AI accuracy. |
| Executed fixed-model AI attempts | 63 | 45 primary plus 18 context-baseline; all reviewed, with failures retained. The sprint has 67 total attempts including three excluded development failures and one operational probe. Earlier pre-sprint investigations are separate. [Verified study totals](../../evals/reports/resume-20261005/study-summary.json). |
| Primary fault accuracy | 9/27 (33.3%) | One partial, one abstention, 16 execution failures. Failures remain in the denominator; healthy controls are not pooled into fault accuracy. |
| Grounding | 9/12 emitted primary diagnoses; 15/18 across both strategies/cohorts | Valid typed citations do not ensure semantic support. Assisted reviews, not independent adjudication. |
| Explicit appropriate abstention | 1/18 primary control trials | One healthy follow-up returns explicit insufficient evidence. Missing/ambiguous trials end in budget/provider failures. Grounded no-fault `diagnose` answers are recorded separately from the required abstention action. |
| Paired context comparison | 18 pairs | Original twelve pairs show no structured accuracy gain; nine complete-usage pairs average 47,934 vs 57,787 tokens. The six control-only follow-up pairs have just one fully reported pair. Different terminal behavior and provider failures limit efficiency claims. |
| Safety | 0/63 observed unsafe recommendations or advisory-scope violations | No executed agent infrastructure action; no adversarial security evaluation. |
| Study efficiency | 7.38 reads and 7.10 model calls mean; 86.62 s median latency | All 63 attempts, including provider/budget failures; native replay, not live-backend response time or MTTR. |
| Study token usage | 2,694,789 reported tokens; 17 requests with unknown usage | 46 fully reported investigations average 55,453 tokens. Subscription monetary cost is unknown. [Recalculable study totals](../../evals/reports/resume-20261005/study-summary.json). |
| Fixed-cohort reported usage | 2,142,187 tokens; 10 unknown-usage requests | Lower bound. Complete-usage primary mean is 53,636 tokens over 29 investigations; subscription dollar cost unknown. |
| Successful model run | 8 model requests, 8 diagnostic reads | Run `b4e5c4bc-ad01-4fde-b147-6446762705e2`; inventory is one automatic read and the remaining seven are model-selected. Recovery reads belong to the separate helper. |
| Reported runner latency | 120,076.353 ms | One run, approximately 120.1 seconds; includes runner shutdown and excludes fault-window waits, detection, and helper recovery. Not an average or MTTR. |
| Successful-run usage | 45,171 input + 3,209 output = 48,380 tokens | Reported usage, cached input zero; [public record](../../apps/web/public/investigation.json). |
| Monetary model cost | Not measured for this run | Subscription billing; `approximate_api_cost_usd` is null. Separately billed API mode has an estimator/admission reservation but no retained live API cost benchmark. Do not claim $0 inference. |
| Evidence/context | 8 evidence records; largest selected request context 29,171 bytes | Eight saved context selections stayed within the configured 32,000-byte context limit. The later context comparison is separate; it establishes no accuracy improvement. |
| Structural grade of successful run | Citation/source/flag/remediation checks passed | Recomputed during this audit in local `var/resume-audit-grade.json`. The grader explicitly requires manual causal review; keyword and structural success do not imply semantic correctness. |
| Baseline/recovery capture | 5/5 reads in each window; zero sampled error signals | Retained successful exercise report. Sampled observations, not proof of complete health; reset performed by the helper. |
| Deterministic suite | 153 passed; 8 live tests skipped | Final `make check` discovers 161 tests and passes compilation; local `var/resume-evaluation-completed-python.log`. Separate from live AI evaluations. |
| Live telemetry checks | 6 passed; 2 Kubernetes cases skipped | Fresh `make check-live-telemetry`; local `var/resume-evaluation-final-live-telemetry.log`. |
| Kubernetes verification | 2 historically passed live tests; 6 permission checks | Retained isolated kind test log and RBAC JSON: two allowed reads and four denied write/secret/other-namespace operations. Not rerun against a deleted cluster. |
| Browser checks | 22 executions: 11 cases × 2 viewports | Completed-study local suite passed in 9.2 seconds without retries. The earlier 48-attempt site's public suite passed in 14.9 seconds; completed-study deployment checks are recorded separately in [site validation](recruiter-site.md). This is separate from AI evaluation. |
| External lab inventory | 28 Compose services | All 28 were running after final capture cleanup and before the owned lab was stopped to release resources. External target infrastructure, not 28 original Sentinel microservices. Recorded traced inventory has 20 identities including Sentinel and non-business-service identities; not a defensible headline count of monitored application services. |

## Deployment and current validation

The public viewer preserves the original reviewed payment record. The sprint's
website changes add confidence-ranking clarity and contextual evaluation results
without replacing that recording or adding a live backend. Source/configuration
methods and per-run reviews are linked beside measured claims. Final local and
HTTPS checks, deployment identity, byte equality, and screenshots are recorded in
[site validation](recruiter-site.md). The hosted workflow gates Pages on Python,
offline report verification, recording validation, TypeScript/static export, and
browser checks. Costly AI evaluations remain outside CI.

The revised stock CLI successfully captured the international-shipping fault and
collector telemetry gap. Stronger admission checks passed on those immutable real
observations, and all six live telemetry tests passed afterward. Cleanup restored
all flags and the collector, left no tracked fault, and showed 28 running services.
Only Sentinel's Compose lab was then stopped, preserving volumes and source.
The twelve resumed model trials used saved real corpora, so the lab stayed down.
No cloud resources or kind cluster were created this sprint.

Current failure-observability changes record elapsed failed-request time and safe
provider class/status/code metadata, recognize the confirmed quota condition,
and pause future batch requests after retaining the failed attempt. They neither
retry requests nor switch billing. Frozen source and corpus identities are kept
through the completed follow-up; post-cohort fixes are not represented as
rebenchmarked agent reliability improvements. The continuation's safe observer
left model request arguments unchanged. The completed study is reproducible
offline from public packets, reviews, catalogs, and summaries.

## Claims to exclude from the resume

High diagnosis reliability, structured-context accuracy improvement, calibrated
confidence, complete telemetry coverage, general safety, production scale, MTTR
reduction, lower monetary model cost, autonomous remediation, a live public agent,
AWS/Terraform, MCP, database incident persistence, or ownership of the monitored
application. The 9/27 fault result includes substantial completion failures;
only 1/18 primary control trials abstains appropriately, and missing/ambiguous
controls do not reach the required terminal action within this configuration.
A private JSONL audit is not a production database or workflow service.

The [resume versions](../resume-entry.md) prioritize the implemented tool-calling
agent and auditable executed evaluation footprint. Kubernetes denotes the separate
read-only kind fixture; the application and model study use Compose. Model defaults
differ from the evaluated account-selected alias; reproduction must select the
validated available model explicitly. No paid API fallback was authorized.
