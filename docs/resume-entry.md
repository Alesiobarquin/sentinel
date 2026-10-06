# Sentinel — AI Incident Investigation Agent: resume entries

Based on the [implementation audit](validation/resume-audit.md) and the
[63-attempt evaluation study](validation/resume-evaluation.md). Both the original
cohort and the control follow-up are executed and reviewed, including failures.
OpenTelemetry Demo is the external monitored application. “Live” links to the
public recorded-run viewer, not a hosted investigation agent. The canonical
subtitle remains **AI Incident Investigation Agent**.

## Version A — Best Overall

**Sentinel — AI Incident Investigation Agent** | Python, OpenAI SDK, OpenTelemetry, Docker, Kubernetes, GitHub Actions | [GitHub](https://github.com/Alesiobarquin/sentinel) | [Live](https://alesiobarquin.github.io/sentinel/)

- Built a tool-calling agent with 9 read-only tools that investigates OpenTelemetry Demo faults using logs, metrics, distributed traces, bounded context, and evidence checks.
- Evaluated 12 real-telemetry cases across 63 AI attempts, including 18 matched context pairs; published per-run causal, grounding, abstention, token, and latency results with failures retained.

## Version B — Applied AI / FDSE

**Sentinel — AI Incident Investigation Agent** | Python, OpenAI SDK, Pydantic, OpenTelemetry, Docker, GitHub Actions | [GitHub](https://github.com/Alesiobarquin/sentinel) | [Live](https://alesiobarquin.github.io/sentinel/)

- Engineered a schema-validated agent loop that updates competing hypotheses from ranked logs, metrics, and traces, with citations checked against prior successful reads.
- Benchmarked 12 OpenTelemetry Demo cases over 63 AI attempts, comparing reduced and native context strategies through claim-level grounding, abstention, and latency/token measurements.

## Version C — Backend / Infrastructure SWE

**Sentinel — AI Incident Investigation Agent** | Python, OpenTelemetry, Docker, Kubernetes, OpenAI SDK, GitHub Actions | [GitHub](https://github.com/Alesiobarquin/sentinel) | [Live](https://alesiobarquin.github.io/sentinel/)

- Developed bounded Prometheus, OpenSearch, and Jaeger adapters to correlate logs, metrics, and distributed traces for an AI agent investigating the OpenTelemetry Demo.
- Validated namespace-scoped Kubernetes RBAC in kind and ran 63 AI evaluations across 12 captured cases, with owned-fault cleanup, tool audits, and latency/token accounting.

**Recommendation:** Use Version A by default. It connects the implemented agent
and real telemetry to an inspectable repeated evaluation, without implying high
accuracy or production scale. Kubernetes describes the separate read-only fixture;
Docker is the actual monitored runtime.

## Metrics worth collecting before finalizing

- **Independently adjudicate causes and citations:** Have an engineer challenge
  the assisted reviews against retrieved evidence and noncausal signals, including
  the imperfect healthy baseline. The current 9/27 fault and 9/12 grounding scores
  are inspectable development judgments, not independently verified benchmarks.
- **Measure a targeted reliability change on fresh captures:** Compare compact
  retention of causal source/configuration evidence and budget-aware finishing
  against this frozen agent. Measure valid correct completion, grounding,
  abstention, duplicated-read/budget failures, tokens, and latency on held-out
  cases with repeated independent injections.

The study measured 33.3% primary fault accuracy and appropriate explicit
abstention in 1/18 primary control trials. Those results are not a basis for
claiming a reliable or production-ready diagnosis system. Lower token use in the
small complete-usage comparison does not establish an accuracy improvement or
lower monetary cost.
Deterministic test counts are omitted from the primary resume bullets because the
executed AI evaluation is more relevant. No subscription dollar cost is claimed.
