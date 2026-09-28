# Inherited baseline evidence

Run: `20260928T180936.681804Z`. Measurement valid: **False**.
Assessment policy: `assessment-v4-timezone-separation-20260928`. Approval is distinct from implementation and proof.
Valid measurement does not mean behavioral acceptance. No production or trading autonomy is authorized.

Gate 1 — contracts/invariants: **FAIL**.
Gate 2 — trading behavior: **ERROR**.
Gate 3 — regression/change: **UNKNOWN** (first baseline has no trusted comparator).

Labeled decisions: 13/13 correct among 14 supplied cases.
False signals: []; missed signals: [].
Critical/unplanned misses: {'coverage': 'scored', 'scored_assertions': 1, 'failures': []}; routine false signals: {'coverage': 'scored', 'scored_assertions': 3, 'failures': []}.
Unchanged-revision signal classifications: {'coverage': 'scored', 'scored_assertions': 2, 'failures': []}; delivered-alert duplication: UNKNOWN.
Field probe failures — volume: {'coverage': 'scored', 'scored_assertions': 4, 'failures': []}; segment: {'coverage': 'scored', 'scored_assertions': 10, 'failures': []}; zone: {'coverage': 'scored', 'scored_assertions': 9, 'failures': []}.
Execution failures: [{'case': '46528', 'domain': 'MODEL_FAILURE'}, {'case': 'restart-replay', 'domain': 'MODEL_FAILURE'}].

## Blocking findings

- SIGNAL-001 / 46528: ERROR; MODEL_FAILURE. See `cases/46528.json` and failure record.
- STATE-006 / restart-replay: FAIL; BEHAVIORAL_FAILURE. See `cases/restart-replay.json` and failure record.
- SAFETY-001 / 46528: FAIL; BEHAVIORAL_FAILURE. See `cases/46528.json` and failure record.
- SAFETY-001 / restart-replay: FAIL; BEHAVIORAL_FAILURE. See `cases/restart-replay.json` and failure record.

## Requirement coverage

| Requirement | Status | Strategy / check | Approval / enforcement | Implementation / checks | Counts |
|---|---|---|---|---|---|
| INPUT-001 | PASS | contract / identity | existing-contract / binding | not_established / executable_scoped | {'PASS': 23} |
| INPUT-002 | UNKNOWN | contract / refusal | owner-approved / binding | not_established / executable_scoped | {'N/A': 1} |
| OUTPUT-001 | PASS | contract / decision_shape | owner-approved / binding | not_established / executable_scoped | {'PASS': 21, 'N/A': 2} |
| OUTPUT-002 | PASS | contract / quantities | owner-approved / binding | not_established / executable_scoped | {'PASS': 23} |
| OUTPUT-003 | PASS | invariant / links | owner-approved / binding | not_established / executable_scoped | {'PASS': 23} |
| OUTPUT-004 | PASS | labeled_eval / field_values | owner-approved / binding | not_established / executable_scoped | {'PASS': 4} |
| OUTPUT-005 | PASS | labeled_eval / field_values | owner-approved / binding | not_established / executable_scoped | {'PASS': 10} |
| OUTPUT-006 | PASS | labeled_eval / field_values | owner-approved / binding | not_established / executable_scoped | {'PASS': 9} |
| SIGNAL-001 | ERROR | labeled_eval / classification | owner-approved / binding | not_established / executable_scoped | {'PASS': 13, 'ERROR': 1} |
| SIGNAL-002 | PASS | negative_control / classification | owner-approved / binding | not_established / executable_scoped | {'PASS': 3} |
| SIGNAL-003 | PASS | labeled_eval / classification | owner-approved / binding | not_established / executable_scoped | {'PASS': 1} |
| SIGNAL-004 | PASS | labeled_eval / classification | owner-approved / binding | not_established / executable_scoped | {'PASS': 2} |
| STATE-001 | UNKNOWN | invariant / out_of_scope | existing-contract / binding | not_established / not_available | {'UNKNOWN': 1} |
| STATE-002 | UNKNOWN | metamorphic / out_of_scope | existing-contract / binding | not_established / not_available | {'UNKNOWN': 1} |
| STATE-003 | UNKNOWN | metamorphic / replay | owner-approved / binding | not_established / executable_scoped | {'N/A': 1} |
| STATE-004 | PASS | metamorphic / revision | owner-approved / binding | not_established / executable_scoped | {'PASS': 2} |
| STATE-005 | UNKNOWN | metamorphic / out_of_scope | owner-approved / binding | not_established / not_available | {'UNKNOWN': 1} |
| STATE-006 | FAIL | metamorphic / restart | owner-approved / binding | not_established / executable_scoped | {'FAIL': 1} |
| HISTORY-001 | UNKNOWN | invariant / lineage | owner-approved / binding | not_established / executable_scoped | {'UNKNOWN': 3, 'PASS': 4} |
| HISTORY-002 | UNKNOWN | metamorphic / replay | owner-approved / binding | not_established / executable_scoped | {'N/A': 1} |
| HISTORY-003 | UNKNOWN | metamorphic / out_of_scope | owner-approved / binding | not_established / not_available | {'UNKNOWN': 1} |
| HISTORY-004 | UNKNOWN | metamorphic / out_of_scope | owner-approved / binding | not_established / not_available | {'UNKNOWN': 1} |
| HISTORY-005 | UNKNOWN | invariant / out_of_scope | owner-approved / binding | not_established / not_available | {'UNKNOWN': 1} |
| SAFETY-001 | FAIL | contract / model_proof | owner-approved / binding | not_established / executable_scoped | {'PASS': 21, 'FAIL': 2} |
| SAFETY-002 | UNKNOWN | negative_control / refusal | owner-approved / binding | not_established / executable_scoped | {'N/A': 1} |
| OBS-001 | PASS | contract / provenance | owner-approved / binding | not_established / executable_scoped | {'PASS': 1} |
| OBS-002 | PASS | invariant / integrity | existing-contract / binding | not_established / executable_scoped | {'PASS': 1} |
| OBS-003 | UNKNOWN | invariant / regression | existing-contract / binding | not_established / executable_scoped | {'UNKNOWN': 1} |

## Assumptions, unknowns and limits

Requirements without complete executable checks: STATE-001, STATE-002, STATE-005, HISTORY-003, HISTORY-004, HISTORY-005. Their approval, implementation and check status are separate in the coverage table; absence of a check does not establish PASS.
This is a small, previously calibrated dataset with no held-out population estimate. Model outputs are stochastic; one run is not a reliability bound.
Field probes cover source-supported selected percentages, segments and zones only. This run does not establish complete extraction, malformed/OOD, PDF or live-scraper coverage.
Missing-history and out-of-order traces are retained. Approved reconciliation/delivery requirements remain unimplemented; no external emission interface is available.
Replay probe reopens SQLite; it is not a process-crash/atomic-delivery test. This evaluation does not establish fresh-agent maintenance completion.
Historical label evaluation is separate from current alert authorization. Approved clock and actionability requirements still lack complete implementation and execution proof.
Human code reads: none requested or reported; agent boundary discovery is documented in artifacts/repo_map.md and evidence/code_reads.md.
Autonomy envelope: local evidence collection only. No source repair, label changes, trading actions, or readiness claim.

## Traceability

spec.md → requirements/requirements.yaml → validation.check in harness/gates.py → results.json findings → cases/*.json + raw model requests/responses + SQLite.
manifest.json records hashes and runtime; summary.json holds structured metrics; failures/ retains findings; regression.json records the missing comparator.
context/failures and context/regressions retain candidate records automatically. They do not approve new requirements.
