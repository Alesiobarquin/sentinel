# Investigation learning notes

Read this alongside the real run artifacts, not as a replacement for running
the lab. Start with the [investigation guide](../investigation.md) and
[Kubernetes notes](../kubernetes.md).

## How the pieces work

An adapter converts backend responses into typed telemetry. A semantic tool
chooses fixed queries, filters, and deterministic reduction. Evidence connects
that result to a run and citation ID. Context selection chooses which reduced
results the model sees. A hypothesis states a competing explanation and its
support/contradictions. The model chooses the next read or conclusion; policy
decides whether that choice is permitted. The runner records every transition.

Understand why an unavailable backend and an empty query result are different,
and why neither establishes health. Trace sampling, top-k reduction, export
delay, and current configuration snapshots all constrain a conclusion. In the
measured ad fault, metrics and a warning showed errors that a small trace sample
missed. The payment source shows that the gold attribute is assigned inside
the injected failure branch; it is not proof of a preselected customer cohort.

The initial trace reducer could keep only long upstream errors. Keeping at least
one requested-service span and prioritizing its errors fixes the omission without
discarding explicit coverage limits. Legacy `error="true"` and native `error=true`
are equivalent; `error=true` and `error=false` remain a real conflict. Study the
tests before weakening parsing rules.

Authentication uses state for callback binding, PKCE for code interception
resistance, nonce for the identity token, signature/issuer/audience checks for
trusted identity, and scopes for plan-use authorization. They solve different
problems. A read-only prompt does not provide Kubernetes RBAC or tool policy.

## Before changing this code

- Trace an incident from CLI input to one saved evidence record and final citation.
- Explain each admission limit and which ones can be crossed by an in-flight request.
- Identify where arbitrary queries, files, namespace selection, and writes are excluded.
- Follow a failed read, malformed model reply, invalid citation, and missing-usage stream.
- Show the difference between developer bootstrap permissions and the agent's reader identity.
- Explain what local run files guarantee and what PostgreSQL must eventually add.
- Inspect the scenario catalog and prove it never reaches model context.

## Five questions for checkpoint 2

1. Which specific observations connect the symptoms to the proposed cause, and
   which part is an inference? How would you distinguish a real credential or
   storage failure from the demo's injected branch?
2. Why can logs/metrics show an error while a bounded trace sample shows none?
   Why are Prometheus increase values sometimes fractional or missing?
3. What does an evidence citation prove, and what does it fail to prove? Why
   does mentioning the expected flag not establish diagnosis accuracy?
4. How do tool policy, Kubernetes RBAC, model validation, approval, and auditing
   differ? Which component would actually prevent an infrastructure write?
5. What changes when using ChatGPT OAuth instead of an API key? Explain the
   billing distinction, account model catalog, token refresh, and cap limitations.

## Manual exercise

Run `make login`, inspect `make models`, and run `make first-investigation` once.
Follow the output into `var/investigations/`. Match final citations to raw tool
results and the OTel trace. Compare baseline/fault/recovery windows. Explain
any missing/conflicting data before accepting the diagnosis. Check that the
tracked lab fault is gone. A correct live run is checkpoint 2; it is not yet
portfolio readiness or a measured general accuracy rate.
