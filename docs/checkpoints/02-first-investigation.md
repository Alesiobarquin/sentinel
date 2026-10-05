# Checkpoint 2: first successful AI investigation

**Status: pending live ChatGPT authorization and diagnosis.** Deterministic
fixtures and real telemetry validation do not satisfy this checkpoint. No
model-produced root cause, token/cost result, or AI accuracy is claimed here.

The agent implementation and [manual exercise](../investigation.md) are ready.
After browser sign-in, run one real payment investigation and replace this pending
status with its actual run ID, model, outcome, usage, latency, and evidence.
Do not proceed to major API/web implementation before the required review.

The review must show:

1. The symptom, healthy baseline, fault period, and retained telemetry limits.
2. The actual tool sequence and evidence IDs from `tools.jsonl`/`events.jsonl`.
3. The model's proposed cause and the observations supporting or contradicting it.
4. Relevant pinned source, current configuration, and reproducible manual steps.
5. Cleanup/recovery observations, distinguishing developer reset from agent remediation.
6. The five [technical questions](../learning/investigation.md).

The developer should run the exercise manually, inspect evidence, and explain
the diagnosis. A schema-valid response can be incorrect; evaluate causality
before marking the checkpoint achieved. Confidence is a ranking indicator.

[AGENTS.md](../../AGENTS.md) requires: “stop after diagnosing one real injected
incident.” At that point present the concrete result and learning questions,
then wait for acknowledgment before the next guide phase. Later write and cloud
permissions remain separately gated.
