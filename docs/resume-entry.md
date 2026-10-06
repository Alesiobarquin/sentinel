# Sentinel — AI Incident Investigation Agent: resume entries

Based on the [implementation audit](validation/resume-audit.md) and the
[48-attempt fixed evaluation](validation/resume-evaluation.md). The control
follow-up remains quota-blocked; these entries use executed results only.
OpenTelemetry Demo is the external monitored application. “Live” links to the
public recorded-run viewer, not a hosted investigation agent. The canonical
subtitle remains **AI Incident Investigation Agent**.

## Version A — Best Overall

**Sentinel — AI Incident Investigation Agent** | Python, OpenAI SDK, OpenTelemetry, Docker, Kubernetes, GitHub Actions | [GitHub](https://github.com/Alesiobarquin/sentinel) | [Live](https://alesiobarquin.github.io/sentinel/)

- Built a tool-calling agent with 9 read-only tools that investigates OpenTelemetry Demo faults using logs, metrics, distributed traces, bounded context, and evidence checks.
- Evaluated 12 real-telemetry cases across 48 AI attempts, including 12 matched context pairs; published per-run causal, grounding, abstention, token, and latency results with failures retained.

## Version B — Applied AI / FDSE

**Sentinel — AI Incident Investigation Agent** | Python, OpenAI SDK, Pydantic, OpenTelemetry, Docker, GitHub Actions | [GitHub](https://github.com/Alesiobarquin/sentinel) | [Live](https://alesiobarquin.github.io/sentinel/)

- Engineered a schema-validated agent loop that updates competing hypotheses from ranked logs, metrics, and traces, with citations checked against prior successful reads.
- Benchmarked 12 OpenTelemetry Demo cases over 48 AI attempts, comparing reduced and native context strategies through claim-level grounding, abstention, and latency/token measurements.

## Version C — Backend / Infrastructure SWE

**Sentinel — AI Incident Investigation Agent** | Python, OpenTelemetry, Docker, Kubernetes, OpenAI SDK, GitHub Actions | [GitHub](https://github.com/Alesiobarquin/sentinel) | [Live](https://alesiobarquin.github.io/sentinel/)

- Developed bounded Prometheus, OpenSearch, and Jaeger adapters to correlate logs, metrics, and distributed traces for an AI agent investigating the OpenTelemetry Demo.
- Validated namespace-scoped Kubernetes RBAC in kind and ran 48 AI evaluations across 12 captured cases, with owned-fault cleanup, tool audits, and latency/token accounting.

**Recommendation:** Use Version A by default. It connects the implemented agent
and real telemetry to an inspectable repeated evaluation, without implying high
accuracy or production scale. Kubernetes describes the separate read-only fixture;
Docker is the actual monitored runtime.

## Metrics worth collecting before finalizing

- **Complete the blocked control follow-up:** Execute the remaining 12 triples
  when subscription usage is available, preserving the frozen configuration.
  Report explicit abstention, grounded no-fault findings, provider failures, and
  budget stops separately; do not replace original failures or pool controls into
  fault accuracy.
- **Independently adjudicate causes and citations:** Have an engineer challenge
  the assisted reviews against retrieved evidence and noncausal signals, including
  the imperfect healthy baseline. The current 9/27 fault and 9/12 grounding scores
  are inspectable development judgments, not independently verified benchmarks.
- **Measure a targeted reliability change on fresh captures:** Compare compact
  retention of causal source/configuration evidence and budget-aware finishing
  against this frozen agent. Measure valid correct completion, grounding,
  abstention, duplicated-read/budget failures, tokens, and latency on held-out
  cases with repeated independent injections.

The study measured 33.3% primary fault accuracy and no appropriate explicit
control abstention. Those results are not a basis for claiming a reliable or
production-ready diagnosis system. Lower token use in the small complete-usage
comparison does not establish an accuracy improvement or lower monetary cost.
Deterministic test counts are omitted from the primary resume bullets because the
executed AI evaluation is more relevant. No subscription dollar cost is claimed.
