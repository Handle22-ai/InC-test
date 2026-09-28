# Source scope and human-read record

No human source inspection or additional explanation was requested or reported.

CODE-READ-ID: AGENT-FORMAT-001
Observed failure: the native pre-change reader rejects synthetic alternate-key records.
Why evidence was insufficient: the requested new format required finding the existing
decode/validation boundary while keeping writes and shared projections unchanged.
Source inspected: selected `rebuilt/store.py`, `rebuilt/snapshot.py`,
`tests/test_capture_reference.py`, `harness/storage_evaluation.py`; `Makefile` read-only.
What was learned: alias resolution belongs before the existing `from_output` validation;
the writer and shared observation ports require no changes.
Missing harness/evidence capability: no alternate-spelling/conflicting-key checks.
Harness improvement made: nine isolated synthetic format tests, preserved before/after
results and exact shared comparison; writer AST verified unchanged.
Could the same code read be avoided next time? The new decision, test mapping and learning
identify this boundary; agent source inspection may still be necessary for another change.

Scope expansions: new `tests/test_capture_reference_alias.py`; new decision/learning/
regression and evidence artifacts; requested README/manifest links; Makefile read-only.
No inherited source or shared acceptance rule was inspected for modification or changed.
