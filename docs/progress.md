# Implementation progress

## Resume evaluation sprint — all model trials complete

Canonical resume title: **Sentinel — AI Incident Investigation Agent**. The
12-case real-telemetry catalog contains nine faults and healthy, missing-evidence,
and ambiguous controls. The fixed `gpt-5.6-luna` study executed **63 AI attempts**:
48 original trials and a separate 15-trial control follow-up. All attempts have
packet-bound semantic reviews, including the three initial subscription-limit
failures in the follow-up. There are **45 primary attempts, 18 native-context
baseline attempts, and 18 matched pairs**. The sprint has 67 total attempts when
three excluded development failures and one operational probe are included.

Primary fault accuracy remains **9/27 (33.3%)**; controls stay outside that
accuracy denominator. Appropriate explicit abstention is **1/18 primary control
trials (5.6%)** across both cohorts. Material cited claims are grounded in
**9/12 primary diagnoses**, or **15/18 diagnoses across both strategies**.
Missing/ambiguous follow-up trials still end in provider failures or budget stops.
No accuracy benefit from ranked context is demonstrated. These are development
measurements with Codex-assisted reviews, not a reliable-production-system claim.
See [method, denominators, and limitations](validation/resume-evaluation.md).

The original inference code and catalog remained frozen at c27bbb3 for the
resumed trials. The provider resumed responding on October 6; twelve additional
trials completed the planned follow-up. No earlier failed trial was replaced,
no paid API fallback was used, and no new fault injections were needed. Both
cohorts pass offline verification. The [study summary](../evals/reports/resume-20261005/study-summary.json)
reproduces **447 model calls, 465 diagnostic reads, and 2,694,789 reported tokens**,
with 17 unknown-usage requests. Dollar cost remains unknown.

All twelve accepted captures were cleaned up. Four rejected preparations and
one pre-injection operator abort remain documented. Post-cohort changes improve
stock shipping/gap preparation, future catalog/admission definitions, failure
observability, archived catalogs, and report verification. They do not change the
benchmarked inference algorithm. Stock shipping and collector-gap captures were
reproduced with cleanup; six live telemetry checks passed afterward. Kubernetes'
two live reader tests and six permission checks remain historical isolated-kind
evidence; this sprint's monitored application runs in Compose.

Fresh `make check` passed **153 deterministic tests**, eight opt-in live skips,
and compilation. Public presentation and final browser/publication checks are
recorded in [site validation](validation/recruiter-site.md). The original reviewed
payment recording remains unchanged. The README, project notes,
[implementation audit](validation/resume-audit.md), and
[three resume versions](resume-entry.md) use measured results and explicit limits.
No AWS, Terraform, MCP, persistent database state, GitHub diagnostic tool, or
agent write permissions were added. The local Docker lab stays down with volumes
retained; the frozen source and saved corpora remain available for reproduction.

The completed report and site are published from source `52ba8fc`.
[Hosted checks and Pages deployment](https://github.com/Alesiobarquin/sentinel/actions/runs/37471001073)
passed Python 3.12/3.14 (153 deterministic passes and eight live skips each),
verification of both cohorts, and 22 CI browser executions. All **22 actual
public HTTPS executions passed in 15.1 seconds** without retries. Five public
paths returned 200; the published report/resume/summary files match the release,
and the payment recording remains byte-identical. Public desktop/mobile views
were inspected. All sprint deliverables are complete; the documented accuracy,
abstention, and grading limitations remain. The owned preview was stopped.

## Delivery before the evaluation sprint — 2026-10-05

The resume evidence audit checked source, retained investigation/scenario records,
git history, Docker state, hosted CI, and the public site rather than PRD intentions.
Fresh checks passed 122 deterministic Python tests (eight live skips), compilation,
six live telemetry tests (two Kubernetes skips), public replay validation, and
all 22 HTTPS desktop/mobile browser checks in 16.9 seconds without retries. The
fetched public recording matches the checkout byte-for-byte. The separate kind
fixture was not recreated; its earlier live RBAC results remain historical.
No real fault, live model request, cloud resource, or deployment was made by this
audit. See [the evidence and boundaries](validation/resume-audit.md) and
[three resume versions](resume-entry.md). Repeated causal AI accuracy and
efficiency benchmarks remain unmeasured; the correct payment run is one case.

The source is public at [Alesiobarquin/sentinel](https://github.com/Alesiobarquin/sentinel).
The first [hosted deterministic CI run](https://github.com/Alesiobarquin/sentinel/actions/runs/37327673968)
passed on Python 3.12 and 3.14. The focused recruiter site is now public:
[landing](https://alesiobarquin.github.io/sentinel/),
[interactive demo](https://alesiobarquin.github.io/sentinel/demo/), and
[project/learning page](https://alesiobarquin.github.io/sentinel/project/).
[The first Pages deployment](https://github.com/Alesiobarquin/sentinel/actions/runs/37349717998)
passed Python, web, and deploy jobs. All 22 browser checks also passed against
the actual HTTPS site. The repository About field links the verified homepage.

ChatGPT sign-in is complete. Real model run
`968a752f-8f1d-4dd5-acab-c95076d4a96e` passed the corrected streaming transport,
read inventory, metrics, logs, traces, and source, then failed application
validation: the model supplied a service argument to a global configuration
tool. It used five model calls and five tool calls, with 18,285 input and 1,679
output tokens; it produced no final diagnosis. The developer exercise reset
the fault. All baseline/recovery reads succeeded, with zero sampled errors.

Tool scope/time argument families now appear in the model-facing JSON Schema,
matching the existing Python validator. Instructions also require disjoint
supporting/contradicting evidence lists. The latest deterministic suite passed
**111 tests plus eight opt-in live skips and compilation**, also passing
[hosted CI](https://github.com/Alesiobarquin/sentinel/actions/runs/37329418839).

The corrected exercise produced the first causally correct live AI diagnosis:
`b4e5c4bc-ad01-4fde-b147-6446762705e2`, `gpt-5.6-luna`, eight model calls and
eight read-only tools, 45,171 input / 3,209 output tokens, 120,076.353 ms latency.
It identified the enabled payment-failure branch, cited metrics/logs/traces/source
and current configuration, compared the baseline, and recommended a human-reviewed
flag revert. Recommendations were not executed. All baseline/recovery reads
succeeded with zero sampled payment errors; the exercise restored all flags to
`off` and left no tracked fault. An OTLP export timeout occurred; 25 local
self-trace spans remain, but this run's complete Jaeger delivery is unverified.
See [checkpoint 2's concrete review](checkpoints/02-first-investigation.md).
The developer acknowledged checkpoint 2 on 2026-10-05. The focused static recruiter
site can now proceed. This single
correct case does not establish an AI accuracy rate or full PRD portfolio readiness.

The prescribed Next.js/React/TypeScript frontend now includes a landing page,
interactive replay, and explanatory project/learning page. Replay exposes original
read order, hypotheses, reasons, evidence IDs, timing, usage, diagnosis, and
developer-helper recovery. The public recording comes from the real successful
run through a reviewed exporter with source-record hashes, prior-citation checks,
field allowlists, bounds, and credential-pattern screening. Private audit files,
SDK responses, endpoints, and model credentials are excluded.

The latest local checks passed **122 deterministic tests plus eight opt-in live
skips and compilation**, TypeScript checks, and static export. All **22 Chromium
browser checks** passed across desktop and mobile after fixing a genuine mobile
grid overflow/tap failure and an indexed navigation accessible name. Original
failure logs are retained in `var/site-tests.log`; the corrected result is in
`var/site-tests-fixed.log`. Six screenshots were inspected. The Actions workflow
now gates Pages deployment on Python and web checks. Visitors make no model or
telemetry requests. See [site operation](recruiter-site.md),
[site learning material](learning/recruiter-site.md), and
[the delivery review](checkpoints/05-recruiter-delivery.md).

Public endpoint checks returned HTTP 200 for the landing/demo/project pages,
recording JSON, and sharing image. The public browser suite passed all 22 cases
in 17.1 seconds without retries, including the real Pages 404 and repository
asset paths; `var/site-tests-public.log` retains the result. A public landing
screenshot was inspected. Third-party source/runtime notices and license copies
are distributed with the site. See [public site validation](validation/recruiter-site.md).

The developer requested a student-portfolio tone rather than product marketing.
The landing, demo, project, 404 page, metadata, and sharing image now use concise
factual wording. The icon beside Sentinel was removed, headings were reduced,
and repeated closing banners were deleted. First-person project notes describe
implementation, tests, limitations, and lessons. This preference is recorded in
`AGENTS.md`. TypeScript/static export and all 22 desktop/mobile browser checks
passed after the revision; screenshots were inspected. The original investigation
record is unchanged. A pre-existing unrelated server occupied port 4173, so local
checks used an owned preview on 4175; the failed startup log is retained.

The developer then allowed the original logo to return and requested polish for
technical and nontechnical recruiters. The logo is restored in the header,
favicon, and sharing preview. The landing explains the task and data types in
plain language; the project overview summarizes ownership, result, and scope.
Demo entry links open at the result. A brief diagnosis summary is followed by
the unchanged original model explanation in an expandable section, with evidence
and the full replay still available. TypeScript/static export and all 22 updated
browser checks passed locally; desktop/mobile screenshots were inspected. The
final suite took 11.7 seconds without retries. The original recording is unchanged.

The developer requested a second review from an experienced engineer's perspective.
The landing is now a concise project write-up instead of a dashboard preview,
headline statistics, generic feature cards, and technology badges. It describes
the actual payment experiment and links directly to its logs, source branch, and
configuration snapshot. Project notes link implementation and regression tests,
describe failed attempts and telemetry/resource issues, acknowledge AI coding
assistance, and keep run measurements with their scope. A misleading claim that
private failure captures were public was corrected. The next evaluation gap is
stated without adding a technology roadmap to the page.

The reviewed recording remains unchanged. TypeScript/static export and all 22
desktop/mobile browser checks passed after the final readability adjustment
(10.6 seconds, retries disabled). Six routes had no horizontal overflow, and 24
linked source/test/document paths resolved in the checkout. Screenshots of the
landing, implementation, development, validation, result, and sharing image were
inspected. See the latest [site validation](validation/recruiter-site.md).

The entries below preserve the earlier implementation and validation history;
their then-current statements about authorization, publication, and CI are
superseded by this status.

## Recruiter launch planning

On 2026-10-05 the developer requested exact human steps and a hosting comparison
using free plans and their already approved GitHub Student Developer Pack.
[The launch plan](recruiter-launch-plan.md) records executable local sign-in and
first-investigation steps, account setup, conditional deployment instructions,
current official prices/offers, and credit-expiry cleanup. [ADR 009](decisions/009-recruiter-demo-hosting.md)
proposes a static recruiter viewer with an optional student-funded read-only API.
The proposal is not an accepted architecture change. No account was connected,
resource created, inference run, or source published during this planning work.
Checkpoint 2 and later implementation/permission gates remain pending.

The developer then clarified the public delivery target: one recruiter demo and
an explanatory project/learning page, with the coding agent executing CLI steps
and involving the human for browser sign-in. The revised plan and ADR 009 use
GitHub Pages through the already authenticated CLI, with no separate public
backend or new hosting account required. This is a delivery decision; unbuilt
PRD capabilities and AWS deployment are not claimed as complete.

ChatGPT browser authorization completed on 2026-10-05. The account catalog does
not include the previous default `gpt-6-luna`; `gpt-5.6-luna` was explicitly
selected for the first exercise. Preflight passed. The first baseline capture
at `var/first-investigation/20261005T143316.819702Z/` failed its trace read with a
Jaeger timeout before fault injection or any model request. Six live telemetry
checks then passed, and a new exercise began with a fresh baseline. Preserve
that failure record. No successful AI diagnosis is established by sign-in alone.
The initial real model run `5c30f56e-5171-4f95-a3b3-2be53872e4d1` failed in the
transport adapter after one response (1,236 input / 335 output tokens). It did
not produce a diagnosis. Baseline and recovery reads all passed, error samples
were zero in both, and the developer exercise reset the fault. Two bounded
transport diagnostics used the same saved context and retained private captures;
they were not additional incident diagnoses or evaluation successes.

The real subscription stream delivered a finalized namespaced function call in
`response.output_item.done` but left terminal `response.completed.output` empty.
The provider now accepts finalized stream items only after successful response
completion and reported usage. Tool identity/count/size checks, duplicate-index
rejection, and terminal/stream consistency remain enforced. Native response and
completed tool records are saved outside selected model context. Replaying the
captured real stream through the SDK's mocked HTTP transport passed without a
network request. Four new deterministic regression cases cover this behavior
and failure-audit retention.

The provider-fix deterministic checks passed: **110 tests, eight opt-in live
skips, and compilation**. The subsequent exercise and contract fix are recorded
in the current status above; checkpoint 2 requires a correct diagnosis and review.

## Bootstrap work implemented

- Official Demo 3.1.0 source commit recorded in `infra/docker/demo.lock.json`.
- Commit-archive fetch, temporary extraction, cache provenance, and cache checks.
- Official Compose layers rendered into an isolated local runtime configuration.
- Loopback store/telemetry endpoints, startup timeout, status, shutdown, and probes.
- Typed Prometheus tool: instant/range queries and metric discovery.
- Typed Jaeger compatibility adapter: service discovery, compact traces, and
  aggregated dependency queries with explicit units and coverage limits.
- Typed OpenSearch adapter: field discovery, explicit schema preflight, bounded
  service/time searches, exact message/severity grouping, and correlation IDs.
- Initial developer CLI commands for all three adapters used the standard library.
- Local tool-call auditing and one developer-only payment fault/reset helper.
- Bounded multi-signal capture utility with explicit partial-failure reporting
  and protection against overwriting prior evidence.
- Offline tests, opt-in live tests, and deterministic GitHub Actions configuration.
- Setup, architecture, six ADRs, telemetry notes, runbook, and learning questions.

## Verified locally

Latest `make check` on 2026-10-04: **64 deterministic tests passed; six live
tests skipped; Python compilation passed**, using Python 3.14.7. Local Markdown
links and log-schema configurations are checked separately. Tests exercise
synthetic adapter payloads, request validation, failures, audit events, a synthetic
upstream archive, Compose isolation, and restoration of a prior fault variant.
They do not establish diagnosis quality. Live integration is recorded separately.
CLI tests run actual parsers/adapters with synthetic HTTP responses, including
log schema preflight, grouped output, request failure, and audit persistence.
Trace tests cover parent relationships, overlapping durations, missing parents,
explicit error status, query time units, result limits, and mismatched windows.
Log tests cover mixed mappings, partial searches, correlation/document identity,
sample coverage, timestamp formats, and excerpt collisions without false merging.

## Live integration and manual fault evidence

Initial attempts were blocked by sandbox network and Docker-socket access.
Approved shell access on 2026-10-04 resolved both. The source archive and images
downloaded, `make demo-up` succeeded, and all configured container health checks
passed. The full runtime contains 28 Compose services and 19 traced identities.
The demo is still running locally; no cloud resources were created.

All six live tests (two per backend) passed against real telemetry with
`SENTINEL_LOG_INDEX='otel-logs*'` and
`SENTINEL_LOG_SCHEMA=infra/docker/log-schema.json`. The opt-in suite then contained
68 tests, all passing; the two capture utility tests were added afterwards and
passed in the latest offline suite. Hosted CI has not run.

Live discovery corrected the readiness assumption: this full target pushes
metrics over OTLP, and `up` is absent. A positive active-series count now probes
ingestion. Actual OpenSearch mappings and source paths are checked in; payment
failure warnings use lowercase `warn`. Jaeger's temporary UI JSON adapter was
validated against the pinned 2.19.0 runtime.

The payment fault produced ten sampled failing traces and twenty matching warning
logs. Every returned trace ID appeared in payment logs. The helper restored the
prior `off` flag; six new traces and six completion logs then showed successful
behavior without observed errors. The cumulative error counter had a late
increase before flattening; the validation record retains this timing limitation.
An optional follow-up warning query did not return and was canceled; no additional
capture or explanation of that individual counter event is claimed.
See [measured evidence](validation/payment-failure.md), local captures under
`var/live-validation/`, and [the runbook](runbooks/payment-failure.md).

That initial stage did not yet include Kubernetes or model-facing contracts.
The later implementation/validation below records those additions. No real
model calls, AI accuracy evaluations, or agent remediation permissions exist yet.

## Checkpoint status

[Checkpoint 1](checkpoints/01-architecture.md) was acknowledged on 2026-10-04 by
the instruction to continue following the guide toward a resume-ready project. It
presents the architecture, actual services/data flow, local setup, technology
rationale, five decisions, learning questions, and evidence limits. Acknowledgment
is recorded; work now proceeds toward checkpoint 2. Later permission, cost,
and learning gates remain in effect. Checkpoint 2 now records the first correct
live diagnosis and recovery; the developer acknowledged its review on 2026-10-05.

## Current work

Implemented read-only Kubernetes state, semantic diagnostic tools, structured
evidence/hypotheses, a bounded single-agent loop, direct OpenAI integration, and
Sentinel's own OpenTelemetry spans. Pydantic validates untrusted model inputs;
the OpenAI SDK isolates model transport; the OTel SDK/exporter observes runs.
These dependencies follow the approved stack and are locked with uv.
The developer selected ChatGPT subscription sign-in and prefers a smaller model
with capped usage. Supported public OAuth login, protected credentials, rotation,
account catalog, and streaming SDK transport are implemented. Browser login is
configured; the current status above records the selected model and live result.
Subscription preview limits prevent an exact credit/output-token cap;
the application stops at bounded calls/bytes/time and reported-token usage.
Separately billed API mode is optional with known-price admission reservations.

Defaults: eight model calls, ten semantic reads, 50,000 reported tokens, 32 KB
selected context, 12 KB response, and 300 seconds with per-request timeouts.
Unknown usage remains explicit. Recommendations cannot execute remediation.
Run files save full payloads, context selection, hypotheses, decisions, audit,
tokens, approximate API cost where applicable, latency, and outcome.

All eight semantic tools passed real local reads. Sentinel's own nine-span
validation trace reached Jaeger. Two live kind tests passed: actual reader token
reads work, while writes/secrets/other namespaces are denied. The separate kind
fixture was recreated with a 64 MiB limit after its initial OOM history was
observed; cleanup releases resources after tests. The application still uses
Compose. Phase 1's diagnostic script surfaces are now present and demonstrated;
full application migration to kind remains later work.

Three reversible real scenarios now have setup/cleanup, ground truth, expected
evidence, acceptable remediation, unsafe actions, and deterministic capture.
They produced payment, EmptyCart, and intermittent ad error evidence and were
reset. Validation found/fixed equivalent legacy error-tag handling and retention
of requested-service spans. Original failed captures are preserved; corrected
historical reads are separately audited. Missing short-window metrics and a trace
sample that missed intermittent ad errors remain visible. These are deterministic
fault/adapter observations, not AI evaluation scores.

`make login`, `make models`, and `make first-investigation` prepare the next real
diagnosis. The first-run helper checks auth before mutation, uses a preceding
baseline with a settling gap, resets its owned fault on failure, captures recovery,
and stops after one agent run. [Checkpoint 2](checkpoints/02-first-investigation.md)
is pending. Do not claim portfolio readiness or bypass the later guide gates.

See [implementation validation](validation/read-only-agent.md),
[the loop/auth guide](investigation.md), [Kubernetes notes](kubernetes.md),
[new decisions](decisions/README.md), and [learning material](learning/investigation.md).

## Latest checks and local resource constraint

On 2026-10-05 the final offline suite contains **106 deterministic tests plus
eight opt-in live tests**. It passed on Python 3.12.12 and 3.14.7 (live cases
skipped), and `make check` passed with Python 3.13.5 and compilation. The locked
environment uses uv; CI installs that lock on Python 3.12/3.14. Hosted CI has not
run. Local Git was initialized on `main`; no remote or GitHub write was performed.

The combined 111-test live suite later failed its two Kubernetes cases because
the shared Docker VM's memory/swap was nearly exhausted. Kind's 64 MiB fixture
and CoreDNS were OOM-killed; controller/scheduler containers also restarted.
The adapter surfaced timeouts. Failure logs and container termination records
are retained rather than relabeled as a successful run.

Validation now runs the full Compose demo and kind separately on this shared VM.
After stopping only Sentinel's Compose services and recreating the isolated kind
cluster, both Kubernetes tests and all six permission checks passed. The fixture
was ready with zero restarts; VM available memory rose from about 459 MiB to
about 3.62 GiB. This is a local resource observation, not a performance benchmark.
Use `make check-live-telemetry` and `make check-live-kubernetes` for separate live
checks; stop kind after its checks and restore the demo. Increasing only the
fixture's limit was insufficient.

Kind was deleted after its isolated checks and Sentinel's full demo was restored.
Fresh metrics/logs/traces passed all six live checks; all 28 services were running
and configured container health checks passed. Jaeger's in-memory history can be
lost on restart; saved raw validation captures remain available.

The final code also rejects telemetry redirects, exposes minimum raw counter
sample counts, and closes the model transport even if exercise cleanup fails.
Regression tests cover these paths. Raw payment counter observations were about
60 seconds apart; coverage rereads of the fresh 180-second fault window returned
two error-counter samples. Earlier short-window missing metrics remain unknown.

The post-fix batch at `var/scenarios/20261005T050922.978004Z/` completed with all
45 semantic reads passing, using 180-second windows and 30-second export delays.
Payment, EmptyCart, and intermittent ad faults each produced real error evidence.
All recovery windows showed zero sampled error signals; all flags were restored
to `off`, and no tracked fault remained. New audited metric-coverage reads across
all nine windows confirmed that the ad incident had only one raw error-counter
sample, so its missing increase remains unknown. See the fresh-run table in the
validation record. No live AI request or AI quality score was produced.
