# Sentinel project case study

**Draft for the planned public project page.** Claims below describe implemented
work and recorded validation. This draft is not a declaration that the full PRD
portfolio acceptance criteria have been met. A browser-authenticated AI exercise
is now being attempted; its result must be added after manual causal review.

## Problem and original contribution

Distributed incidents leave fragments across metrics, logs, traces, runtime
state, and source code. Sentinel investigates a bounded incident window using
typed tools, reduced evidence, explicit hypotheses, and evidence-linked model
decisions. It persists the investigation audit and instruments itself.

The original work is Sentinel's Python adapters, deterministic reduction,
contracts, model loop, policy, authentication, auditing, evaluation fixtures,
bootstrap scripts, tests, and documentation. The pinned OpenTelemetry Demo is
the external target application, maintained by the OpenTelemetry authors.

## Implemented architecture

One native investigation loop reads Prometheus metrics, OpenSearch logs, Jaeger
traces, allowlisted source, current feature-flag configuration, and optionally
restricted Kubernetes state. Typed Pydantic decisions select semantic tools;
application code validates arguments and enforces permissions outside prompts.

Full tool results and the audit stay in local run files. The model receives a
bounded selection with evidence IDs and explicit omissions. Recommendations
cannot execute infrastructure changes. Sentinel exports its own OTel spans to
the local telemetry stack.

The model transport uses the public OpenAI Responses API with supported ChatGPT
OAuth sign-in. It validates state, PKCE, nonce, JWT signatures, permissions, and
account identity; credentials are stored outside the repository with owner-only
permissions. Model catalog availability is checked before an exercise injects
a fault. There is no automatic model upgrade or endless retry loop.

## Evidence already recorded

- 111 deterministic tests passed locally, with eight opt-in live tests skipped
  in the ordinary run. Python compilation passed. These tests validate behavior,
  not AI diagnosis accuracy.
- Six telemetry integration checks passed against the real local backends.
- Two Kubernetes integration checks passed in a separate kind fixture; reader
  credentials were denied writes, secrets, and other namespaces.
- Payment, EmptyCart, and intermittent ad faults produced real error evidence
  during deterministic captures. All were reset. These are three fault scenarios,
  not three successful AI diagnoses or an accuracy benchmark.
- Failed captures and combined Docker-memory failures were preserved. Later
  isolated validation passed without relabeling those earlier failures.
- [Hosted CI](https://github.com/Alesiobarquin/sentinel/actions/runs/37327673968)
  passed the then-current 110-test deterministic suite on Python 3.12 and 3.14.
  Real model runs have exposed transport and argument-contract failures; neither
  failed investigation is counted as a correct diagnosis.

See [progress](progress.md), [agent validation](validation/read-only-agent.md),
and [fault evidence](validation/payment-failure.md). Add a successful AI exercise
only after inspecting its actual diagnosis and causal evidence.

## Engineering lessons supported by this work

These are the concrete lessons the project illustrates. The developer should
be able to explain them during checkpoint review and interviews.

1. **Deterministic reduction makes evidence manageable.** Log grouping, compact
   traces, span-derived metrics, and bounded source excerpts reduce data before
   inference. Omissions and coverage limits remain visible to the investigator.
2. **Missing telemetry is different from a healthy system.** An error counter with
   one raw sample cannot establish an increase of zero. Export delays require
   deliberate incident and recovery windows; sampled traces can miss intermittent
   failures.
3. **Compatibility requires real payloads.** The actual demo pushes metrics over
   OTLP, so a Prometheus `up` readiness assumption was wrong. Logs required an
   explicit schema, and Jaeger emitted equivalent string and boolean error tags.
4. **Permissions belong in application code.** A prompt is not an enforcement
   boundary. Typed tools, allowlists, RBAC checks, and citation validation restrict
   both malicious input and ordinary model mistakes.
5. **Correctly formatted output is not proof of a correct diagnosis.** Evidence
   citations need causal review. A model must be able to stop with insufficient
   evidence, conflicting observations, failed tools, or an exhausted budget.
6. **Development resources affect reliability.** The full demo and kind fixture
   competed for the shared Docker VM's memory. Testing them separately produced
   a reproducible result and retained the original failed attempt.
7. **Public presentation has different resource needs from an incident lab.**
   A verified static replay can expose the real reasoning and evidence without
   continuously running telemetry generators or charging model usage per visit.
8. **A live transport check can expose a fixture assumption.** The first actual
   model response completed its function call during streaming but returned an
   empty terminal output list. Retaining the native stream and replaying it
   through the SDK offline identified the adapter defect without weakening
   tool policy or pretending the first diagnosis succeeded.

## Limitations and remaining work

The public demo is a retained investigation, not a live incident-response service.
ChatGPT subscription preview does not provide an exact server-side credit cap.
Tool/call/byte/time limits and reported-token accounting remain explicit.

FastAPI/PostgreSQL persistence, the web product, incident chat, expanded AI
evaluations, GitHub deployment context, controlled remediation, MCP, and a
temporary AWS/Terraform/EKS deployment remain later guide work. Describe each
as completed only when its implementation and validation are recorded.

The public project page should link original code, measured validation, runbook,
and architecture. It should invite evidence inspection and local reproduction
without promising capabilities that the implementation does not yet have.
