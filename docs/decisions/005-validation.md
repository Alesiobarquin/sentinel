# ADR 005: separate deterministic, live, and AI validation

**Status:** accepted; AI evaluation harness is pending.

## Context

Parser correctness, integration with real telemetry, and diagnostic accuracy
are different claims. Model variability and API cost should not destabilize CI.

## Decision

Use standard-library unittest for deterministic adapter, policy, context, auth,
budget, failure, audit, CLI, and bootstrap tests. Test real Prometheus, Jaeger,
and OpenSearch with `make check-live-telemetry`; test the separate reader fixture
with `make check-live-kubernetes`. Configure locked deterministic GitHub Actions
checks on Python 3.12 and 3.14. Keep real AI calls outside ordinary CI.
Live logs additionally require a schema and index configured from the running
target; omitted configuration yields an explicit skip.

## Alternatives

Running LLM calls for every commit would be expensive and variable. Testing only
mocked payloads would not establish real backend compatibility. A single canned
demo would not establish diagnosis accuracy across failures.

## Why this option

Fast offline tests catch malformed responses and safety regressions; explicit
live checks establish interoperability; scenario evaluations will measure actual
agent behavior once that behavior exists.

## Consequences

Skipped live tests are pending evidence, not a passed integration. Synthetic unit
fixtures cannot justify portfolio metrics. The first payment fault's setup,
symptoms, cleanup, and ground truth were verified on the pinned running target
on 2026-10-04; see [the validation record](../validation/payment-failure.md).
This validates deterministic evidence collection, not AI diagnosis quality.
Three scenarios now have explicit truth, expected evidence, unsafe actions, and
cleanup. The free capture harness and structural grader are implemented; keyword
signals still require manual causal review. Live AI evaluation remains pending.
CI linting/type checks/build validation will expand with
the backend/frontend and infrastructure implementation.

## Future reconsideration

Rerun integration checks when the pinned target or adapter contracts change.
Kind and the full Compose demo run separately on the constrained shared VM.
Add end-to-end AI incident tests after actual sign-in. Add measured
accuracy, evidence coverage, tool selection, unsafe-action
rate, latency, model cost, and remediation correctness through independent AI
evaluation workflows.
