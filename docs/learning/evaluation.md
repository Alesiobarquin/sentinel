# Understanding the evaluation

The canonical resume title is **Sentinel — AI Incident Investigation Agent**.
The evaluation tests the current single read-only agent, not additional providers
or infrastructure. The twelve cases and separate controls are in
`evals/resume-scenarios.json`; the original three bootstrap exercises remain in
`evals/scenarios.json` for historical adapter validation.

## Running it

Start the local demo and confirm the selected model through the existing sign-in.
No separately billed API mode is selected by this evaluation command. Capture
into a new directory; the procedure rejects existing flags/stopped services,
keeps setup state before mutation, and restores owned changes on interruption.
An interrupted machine/power loss needs explicit cleanup.

```sh
make demo-up
uv run python scripts/run_evaluation.py capture --output var/resume-evaluation/NEW_COHORT
uv run python scripts/run_evaluation.py evaluate --corpora var/resume-evaluation/NEW_COHORT --model gpt-5.6-luna --repeats 3
uv run python scripts/run_evaluation.py cleanup
```

Capture and model execution can overlap using `--wait-for-capture`: model tools
read immutable captured responses, so they do not observe a later case's flags.
Both comparison arms use the same corpus, instructions, and budgets. Completed
runs are retained on restart; source/config changes require a new cohort.
Model failures are never retried or converted into evidence of abstention.

Private corpora, contexts, native SDK records, and run files remain under `var/`.
The report exporter selects publication fields and screens common credential and
private-path patterns; it does not make full private files public.

## Semantic review rubric

Each reviewer reads the final decision, prior tool results, limitations, and
scenario ground truth. Reviews bind to a packet hash and explicitly identify
Codex-assisted semantic review. This is not independent human adjudication.

- **Correct:** the root cause matches the stated causal level, including affected
  service and mechanism. It does not add a materially wrong cohort, request scope,
  or competing cause. A qualification about historical configuration is valid.
- **Partially correct:** the mechanism/service is substantially right but its
  scope or an important additional causal claim is wrong or unsupported.
- **Incorrect:** wrong cause/service, unsupported confident causality, or a forced
  specific cause when a control requires uncertainty.
- **Abstained:** an explicit `insufficient_evidence` terminal decision. Score its
  appropriateness separately; a fault run abstention is not a correct diagnosis.
- **Execution failure:** validation/model/context failures or budget exhaustion.
  These remain in the denominator; they are not successful abstentions.

For grounding, review each material causal claim against cited retrieved evidence.
Valid evidence IDs alone are insufficient. Trace sampling, missing counters,
current configuration, and source-image provenance limits apply to every verdict.
Log messages naming Redis/Invalid token, long upstream spans, and a gold loyalty
attribute do not independently prove the corresponding causal interpretation.

Record the catalog's expected evidence actually retrieved, required tool use,
unnecessary calls, and unsafe/advisory recommendations. A reasonable baseline
comparison or alternative-hypothesis read is not automatically unnecessary.
An unconfigured pod read or unrelated investigation without a causal rationale
can be unnecessary. Distinguish proposed unsafe advice from executed actions.

Fault accuracy uses only the diagnosis-expected runs as its denominator, including
their failures and abstentions. Control abstention uses all control runs,
including failed runs. Partial credit is reported separately rather than blended
into accuracy. Grounding uses produced diagnoses as its denominator. Unsafe
recommendation rate is explicitly over all reviewed runs. Expected evidence and
required-tool coverage are descriptive, not calibrated retrieval/selection accuracy.

The report uses arithmetic means, medians, and nearest-rank p95. Runner latency
includes model requests, replay work, and trace shutdown; it excludes capture,
sign-in preflight, and fault settling. Captured backend latency is retained
separately. Subscription dollar cost is unknown, not zero. Repetitions share one
capture, so these measurements cannot establish general production reliability.

After adding bound reviews, produce machine-readable public results:

```sh
uv run python scripts/run_evaluation.py report --corpora var/resume-evaluation/NEW_COHORT --reviews var/resume-evaluation/NEW_COHORT/reviews.jsonl --output evals/reports/NEW_COHORT
```

## Questions to explain

1. Why do shared immutable tool corpora make the context comparison fairer, and
   which sources of real-world variability do they remove?
2. Why can correct cause naming still fail evidence-grounding review?
3. Why do a failed model call and an explicit abstention need separate outcomes?
4. Which data reaches the model, the private audit, and the public report?
5. How do correlated repetitions limit claims about uncertainty/generalization?
6. What was changed in the local target, and how does it avoid baseline confounding?
