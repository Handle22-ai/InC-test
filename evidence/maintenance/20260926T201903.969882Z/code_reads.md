# Maintenance source-read ledger

Human source inspections requested or reported: **none**.

CODE-READ-ID: AGENT-MAINTENANCE-001
Observed failure: no new production failure; the requested optional field is absent.
Why evidence was insufficient: implementing compatibility required inspecting the selected
snapshot constructor, current JSON serializer/decoder, and shared projection boundary.
Source inspected: `rebuilt/snapshot.py`, `rebuilt/store.py`, `harness/storage_ports.py`,
`harness/storage_evaluation.py`, `tests/test_storage.py`; `Makefile` for offline commands.
What was learned: JSON payload has three shared keys, while source identity is a separate
envelope field; shared adapters project only the payload. Extending native metadata need
not change either shared adapter or the generic acceptance rules.
Missing harness/evidence capability: no optional-field oracle or genuine old-writer fixture.
Harness improvement made: preserved a synthetic database written before the code change;
added ten independent native-readback extension checks; retained longitudinal comparisons
of both whole case/state records and requirement findings.
Could the same code read be avoided next time? The technical extension contract and
durable learning identify the boundary and tests. Agent inspection of changed code may
still be necessary; human source inspection was not needed for this task.

Scope expansions beyond selected implementation paths: new isolated extension test file,
this ledger and other new evidence, requested README/manifest links, a technical decision,
durable learning and regression mapping. No inherited source inspection was performed.
