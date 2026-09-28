# AGENTS.md — how a coding agent works in this repository

The engineer owns `spec.md` and reads `evidence/CURRENT.md`. You maintain the implementation. The
harness, not you, decides whether the work satisfies the spec. The build-time charter that used to
be here is in git history (root commit `41fd172`); it described deliverables that no longer exist.

## Authority, highest first

1. `spec.md`, and the files `make compile` generates from it
2. Approved decision rows in `spec.md` (`spec-decisions`)
3. Frozen labels and witnesses (`requirements/*witnesses.json`, `dataset.json`)
4. Tests, then the implementation

The implementation never defines correct behavior. If the spec is silent, say so and propose a
decision row with status `proposed`; do not decide it in code.

## Start of every session

```bash
make setup      # if .venv is missing
make check
make context TASK=recommendation-classification-maintenance   # read the package.md it prints
make gate       # or: .venv/bin/python -B -m harness gate --proposal
```

Change only the files the package lists as source scope, plus `spec.md` through README's "Change
the policy" steps (`make consequences` before adopting). Prior chat is not project memory.

## Never, unless the owner explicitly says so for this change

- write a reread receipt (`harness reread`) or register a reference (`harness register-reference`);
- edit frozen labels or witnesses, or change an acceptance budget or approved decision row;
- change a requirement or budget to make failing code pass. (REMEDIATION-003 set the Gate 2 budgets at
  the level measured on the day; that is a ratchet the owner approved, not a desk tolerance. See
  harness.md.)
- make live model calls without `LIVE=1`, a call budget and the owner's current authorization;
- persist credentials.

Editing `harness/` or `tests/` is an evaluator change: keep it in a separate commit from any
component change, because Gate 3 reports it and the owner must review it.

## Records

- Record every source file you read or edit, and why the evidence was not enough, in
  `evidence/code_reads.md`. The ledger in `evidence/code-read-ledger/` is generated from transcripts
  and is the check on that record.
- A spec gap becomes a proposal in `context/proposals/` or a `proposed` decision row, never a
  silent change.
- Report exit codes, and never report PASS without the evidence that produced it.
