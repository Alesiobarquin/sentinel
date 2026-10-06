# Fixed-model evaluation records

This directory contains 48 executed investigation attempts and their bound
Codex-assisted semantic reviews. The [full method/results](../../../docs/validation/resume-evaluation.md)
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
- `controls-followup/`: incomplete separate follow-up; three quota failures,
  12 planned trials unexecuted. It is not a complete repeated-control study.

From the repository root, run:

```sh
uv run python scripts/run_evaluation.py verify --report evals/reports/resume-20261005
```

Verification checks complete trial identities, packet/configuration/catalog
hashes, review binding, and arithmetic. It is offline and needs no private run
files or credentials. It cannot independently adjudicate semantic correctness
or attest the model provider's private execution records. Do not treat filtered
native evidence as a complete backend export or count repeated shared captures
as independent injected incidents. Full original artifacts remain in gitignored
local `var/resume-evaluation/20261005-fixed/`.

See [external-code attribution](NOTICE.md).
