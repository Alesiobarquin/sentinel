# Sentinel resume entry

Based on the [implementation audit](validation/resume-audit.md), including fresh
deterministic, live telemetry, and public-site browser checks. The monitored
OpenTelemetry Demo is external software. The public demo is a recording of a real
local investigation; it is not a live public agent.

## Version A — Best Overall

**Sentinel — AI Incident Investigation Agent** | Python, OpenAI SDK, OpenTelemetry, Kubernetes, Docker, GitHub Actions | [GitHub](https://github.com/Alesiobarquin/sentinel) | [Live](https://alesiobarquin.github.io/sentinel/)

- Built a tool-calling agent that queried logs, metrics, and distributed traces from the OpenTelemetry Demo to diagnose an injected payment fault.
- Implemented 9 typed read-only tools, telemetry reduction, bounded context selection, and citation checks; validated behavior with 122 deterministic tests.

## Version B — Applied AI / FDSE

**Sentinel — AI Incident Investigation Agent** | Python, OpenAI SDK, Pydantic, OpenTelemetry, Docker | [GitHub](https://github.com/Alesiobarquin/sentinel) | [Live](https://alesiobarquin.github.io/sentinel/)

- Engineered a schema-validated agent loop with ranked telemetry context, competing hypotheses, and citations restricted to previously retrieved evidence.
- Diagnosed an injected OpenTelemetry Demo fault in 8 read-only calls; built 3 reproducible scenarios with structural evidence and remediation checks.

## Version C — Backend / Infrastructure SWE

**Sentinel — AI Incident Investigation Agent** | Python, OpenTelemetry, Docker, Kubernetes, GitHub Actions, Next.js | [GitHub](https://github.com/Alesiobarquin/sentinel) | [Live](https://alesiobarquin.github.io/sentinel/)

- Developed telemetry adapters that query and reduce logs, metrics, and distributed traces from the OpenTelemetry Demo for an AI investigation agent.
- Validated read-only Kubernetes RBAC in kind, denying writes and secrets; gated public demo deployment on 122 deterministic and 22 browser tests.

**Recommendation:** Use Version A by default. It connects a demonstrated diagnosis
to the tool contracts, context selection, and tests implemented in the project.
Those details are relevant across SWE, Applied AI, and FDSE roles.

## Metrics worth collecting before finalizing

- **Diagnosis success and abstention:** Repeat model investigations across the
  three existing faults with fixed model/budgets and manual causal grading.
  Add healthy, missing-evidence, and misleading-error controls. Report completed,
  correct, inconclusive, and failed runs separately with the sample size.
- **Evidence and safety quality:** Grade whether citations actually support the
  cause/remediation, expected signals were found, and recommendations were unsafe.
  Include hostile telemetry and denied-tool attempts; distinguish unsafe model
  proposals from actions actually executed or blocked by policy.
- **Investigation efficiency:** From those same runs, measure median/p95 latency,
  tool calls, reported input/output tokens, and budget-exhaustion frequency. Use
  actual billed cost only where available; subscription usage is not API dollars.
- **Context-selection effect:** Compare the current reduction/selection against a
  fixed alternative on the same scenarios and model, measuring diagnosis/evidence
  quality and token use. This could support a defensible improvement claim.

Repeated all-scenario AI evaluation is the largest remaining measurement gap.
Neither the existing capture harness nor deterministic test counts establish
diagnosis accuracy. These measurements are proposed work, not completed results.
