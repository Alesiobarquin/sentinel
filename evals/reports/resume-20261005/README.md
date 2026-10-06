# Fixed-model evaluation records

This directory contains the original 48 executed investigation attempts and their
bound Codex-assisted semantic reviews, plus a completed 15-attempt control follow-up.
The [full method/results](../../../docs/validation/resume-evaluation.md)
report primary fault accuracy of 9/27, distinguish explicit abstention from
operational failures, and explain the paired context comparison.

- `investigations.jsonl`: original decisions, privacy-limited native/reduced
  evidence, context-selection IDs, usage, timing, and terminal results per run.
- `reviews.jsonl`: causal verdicts, claim-level grounding, expected-evidence
  matches, unnecessary reads, and advisory/safety checks bound to packet hashes.
- `summary.json`: descriptive metrics recalculated from those two files.
- `configuration.json`, `scenarios.json`, `preparation.json`, `captures.json`:
  exact evaluated configuration/catalog, case identities, and accepted setup
  checks/runtime snapshots.
- `method/`: helper snapshots, rejected preparations, recovery records, workload
  audit, prior-inventory provenance, and separate operational probe.
- `initial-aborted-cohort/`: three failed development trials, not discarded or
  added to the corrected cohort's accuracy denominator.
- `controls-followup/`: 15 executed and reviewed control trials, preserving
  three earlier quota failures. One explicit healthy abstention, one qualified
  no-fault diagnosis, six budget stops, and seven model failures are recorded.
- `study-summary.json`: verified totals across both cohorts: 63 scored attempts,
  18 matched context pairs, and 67 sprint attempts including four exclusions.

From the repository root, run:

```sh
uv run python scripts/run_evaluation.py verify --report evals/reports/resume-20261005
uv run python scripts/summarize_resume_evaluation.py --report evals/reports/resume-20261005
```

Verification checks complete trial identities, packet/configuration/catalog
hashes, review binding, and arithmetic. It is offline and needs no private run
files or credentials. It cannot independently adjudicate semantic correctness
or attest the model provider's private execution records. Do not treat filtered
native evidence as a complete backend export or count repeated shared captures
as independent injected incidents. Full original artifacts remain in gitignored
local `var/resume-evaluation/20261005-fixed/`.

See [external-code attribution](NOTICE.md).
