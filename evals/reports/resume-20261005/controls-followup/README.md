# Control follow-up — executed and reviewed

Planned: 15 additional attempts on the same healthy, missing-telemetry, and
ambiguous corpora (nine primary, six baseline), preserving c27bbb3 inference,
model, instructions, and budgets. This follows provider failures in the original
study; it does not replace any original trial or improve its fault accuracy.

Executed: all 15 attempts. The first three quota failures remain; the remaining
12 ran on October 6 after the provider responded again. Primary controls produced
one explicit healthy abstention, five budget stops, and three model failures.
Baseline controls produced one qualified no-current-fault diagnosis, one budget
stop, and four model failures. Missing/ambiguous cases produced no terminal
abstention. Completion refers to evaluation execution, not passing the controls.

Reported usage is **552,602 tokens**, with seven unknown-usage requests.
Subscription dollars remain unknown. The packet-bound reviews, exact catalog,
configuration, capture checks, summary, and completion status are retained.
`transport-observations.jsonl` supplies bounded SDK diagnostics, associated with
failed model events by unique timestamps within 100 ms. Unobserved HTTP causes
stay unknown. `continuation-method.jsonl` binds the frozen-source operator helper;
its `.py.txt` snapshot is for inspection, not execution from this directory.

Run offline from the repository root:

```sh
uv run python scripts/run_evaluation.py verify --report evals/reports/resume-20261005/controls-followup
```

The [full report](../../../../docs/validation/resume-evaluation.md) explains
the initial pause, resumed execution, semantic judgments, and limitations.
