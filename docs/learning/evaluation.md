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
The current harness stops new requests immediately after a recognized subscription
usage-limit failure; generic failures stop after three consecutive failed runs.
Both retain completed attempts. Do not use sign-in loops or paid fallbacks to
work around an account/app limit. A model catalog listing proves model access,
not that sufficient usage remains for a study.
The simpler baseline keeps the newest complete native results first, without
signal ranking or the agent's additional result reduction. Both strategies
retain an evidence index and explicit omission IDs within 32,000 bytes.

Private corpora, contexts, native SDK records, and run files remain under `var/`.
The report exporter selects publication fields and screens common credential and
private-path patterns; it does not make full private files public.

### Real capture preparation

International shipping needs non-US orders; default domestic traffic may never
exercise its delay. The stock capture runs `scripts/evaluation_workload.py`
during both baseline and incident, sending actual loopback cart/checkout requests
with the upstream Canadian fixture. It requires an in-window five-second shipping
server span, records empty shipping log coverage, audits only safe request
metadata, and joins the workload thread before marking the case ready. This is
closed-loop traffic, not a fixed-arrival performance benchmark.

Before stopping the collector, capture queries a real Jaeger service inventory
to bootstrap tool service permissions. Only its observed service names, time,
and a generic freshness limit enter model context. The injected method remains
outside it. Missing telemetry is then queried through the real adapters; no
synthetic empty responses are inserted. Runtime guards reject interrupted or
restarted baselines. Healthy controls require sampled traffic and no payment
error spans in both windows.

Each capture archives the exact catalog bytes. Reporting verifies that snapshot's
hash, even when the current definitions are corrected later. Do not retroactively
rescore a cohort with easier evidence categories or quietly replace a failed
preparation/model trial.

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
Check explicit citations in the diagnosis text as well as its structured list.
The application validates typed citation fields, not every reference embedded
in prose. Whole matching traces can include child spans outside the requested
window; inspect their timestamps before equating them with in-window metrics.

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
The healthy case can produce a factually supported no-current-fault conclusion
through `diagnose`. Record that semantic verdict separately from the prescribed
explicit-abstention terminal state; it is not a fabricated fault attribution.
The report also shows unsafe recommendations over emitted diagnoses, so a failed
run with no recommendation cannot make the system appear safer by itself.

The report uses arithmetic means, medians, and nearest-rank p95. Runner latency
includes model requests, replay work, and trace shutdown; it excludes capture,
sign-in preflight, and fault settling. Captured backend latency is retained
separately. Subscription dollar cost is unknown, not zero. Repetitions share one
capture, so these measurements cannot establish general production reliability.
Unknown-usage runs contain reported subtotals, not full consumption. Complete-token
statistics exclude those runs. The comparison's complete-usage efficiency subset
requires known usage in both members of a pair; do not remove failed pairs from
accuracy or attribute speed to successful reasoning when requests never completed.

After adding bound reviews, produce machine-readable public results:

```sh
uv run python scripts/run_evaluation.py report --corpora var/resume-evaluation/NEW_COHORT --reviews var/resume-evaluation/NEW_COHORT/reviews.jsonl --output evals/reports/NEW_COHORT
uv run python scripts/run_evaluation.py verify --report evals/reports/NEW_COHORT
```

`verify` recalculates the published summary from the public investigation and
review JSONL files. It checks cohort completeness, packet/configuration hashes,
ground-truth catalog identity, and review binding without model credentials or
private run directories. Recalculation verifies arithmetic and provenance;
independent judgment is still needed to challenge the semantic reviews.

## Completed frozen control cohort

The original 48 trials and separate 15-trial control follow-up are complete.
Three retained subscription-limit failures were followed by twelve new trials
on October 6 after the provider resumed responding. No failure was replaced and
the fixed inference configuration was preserved. During a confirmed quota failure,
pause new requests until authorized account/app usage is available. OpenAI's
[recovery guidance](https://developers.openai.com/siwc/token-sharing-open-source/errors-and-recovery)
does not establish a reset time from the error alone; review ChatGPT Settings → Usage.

Continuation used the existing frozen c27bbb3 worktree and absolute corpus path.
The current main source/catalog has later preparation/reporting/observability
changes, so it correctly fails the original configuration-identity check.

```sh
sentinel_project="$(pwd)"
# Already prepared in this workspace; otherwise create this detached checkout.
git worktree add --detach var/evaluation-source c27bbb317f7666a10b54e3f317db18d8230c0563
cd var/evaluation-source
"$sentinel_project/.venv/bin/python" scripts/run_evaluation.py evaluate \
  --corpora "$sentinel_project/var/resume-evaluation/20261005-controls-followup" \
  --model gpt-5.6-luna --repeats 3 --token-cap 1743426
```

This is the recorded continuation command, not a request for another cohort.
Do not recreate an existing worktree or change the saved allowance. The frozen
runner retains its older three-failure guard; the operator helper stops new
requests immediately after a confirmed quota failure. Continuation skips existing
triples, preserves every failed attempt, keeps the original inference fingerprint
and catalog, and reports the follow-up separately. Model
availability/account timing is a confounder, not an architecture improvement.
The [published operator helper](../../evals/reports/resume-20261005/controls-followup/resume_frozen_control_followup.py.txt)
observes safe transport failures without changing model request arguments. Its
hash is bound in the continuation record. Full-context/SDK records remain private.

Both cohorts can be verified and the 63-attempt study recalculated offline:

```sh
uv run python scripts/run_evaluation.py verify --report evals/reports/resume-20261005
uv run python scripts/run_evaluation.py verify --report evals/reports/resume-20261005/controls-followup
uv run python scripts/summarize_resume_evaluation.py --report evals/reports/resume-20261005
```

The study verifier rejects duplicate run IDs and differing inference/catalog
identities. Its fault-accuracy denominator remains 27; additional controls cannot
raise it. The explicit-abstention denominator becomes 18 primary control trials.
All strategies contribute to descriptive usage totals, not the primary fault rate.

## Questions to explain

1. Why do shared immutable tool corpora make the context comparison fairer, and
   which sources of real-world variability do they remove?
2. Why can correct cause naming still fail evidence-grounding review?
3. Why do a failed model call and an explicit abstention need separate outcomes?
4. Which data reaches the model, the private audit, and the public report?
5. How do correlated repetitions limit claims about uncertainty/generalization?
6. What was changed in the local target, and how does it avoid baseline confounding?
7. Why did retrieving the correct source fail to ensure it remained usable in
   later context, and why does the duplicate-read policy matter?
8. Why did the native baseline diagnose one more fault despite higher average
   token use? What would a new fair comparison need to change and hold fixed?
9. How do provider failures, imperfect controls, and assisted grading limit the
   observed accuracy and abstention claims?
