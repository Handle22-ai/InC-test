# Evidence for the engineer's next decision

Mode: **PROPOSAL_ONLY**. Human review: **PENDING for these spec bytes**. Application acceptance: **NOT ESTABLISHED**.

Blocking findings: **CAPTURED_LABEL_UNSCORED, CHECK_DEFERRED, DECLARED_CASE_UNSCORED, DECLARED_CHECK_UNOBSERVED**. CI accepts only exit 0 from a reviewed run; incomplete or skipped validation does not pass.

| Gate | Status | Meaning |
|---|---|---|
| 3 — regression_change | PASS | UNCHANGED_OR_IMPROVED |
| 1 — contracts_and_invariants | UNKNOWN | Bounded checks only |
| 2 — trading_behavior | UNKNOWN | Bounded checks only |

Run `final-observation` · commit `e46f4f6a9efbe7b286c1eab04efe10b02eefae90` · tracked changes `False`.
Spec `340a24705e7c26f3a4997972e7c23a1e47787ecce5aad6f6a3397792d0354d77` · source content `fd73a37fb32dbebbcdb1cfd0bcc98a638b32eb8c6b8e3c2a21f3d7698daf8925`.

## Observed tradeoffs

| Capture / system | Detected positives | False positives | True negatives | Negative on positive | Positive unresolved | Negative unresolved | Errors | Unresolved / labeled |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| capture-0 / inherited + 512-token variant | 7/7 | 1 | 6/7 | 0 | 0 | 0 | 0 | 0/14 |
| capture-1 / unmodified inherited captured output | 6/7 | 1 | 5/7 | 0 | 1 | 1 | 2 | 2/14 |
| capture-0 / spec-derived classifier | 5/7 | 0 | 3/7 | 0 | 2 | 4 | 0 | 6/14 |
| capture-1 / spec-derived classifier | 4/7 | 0 | 3/7 | 0 | 3 | 4 | 2 | 7/14 |

Each capture has the same 14 labels; they are not independent samples. Unresolved positives are not detected positives. Unresolved negatives are not true negatives. Saved inherited predictions and current classifier executions share the same source cases; no live model ran.
Errors are included in unresolved counts. The primary unmodified inherited run is capture-1; capture-0 changes the impact-verdict token budget to 512. The classifier abstains where history, semantics or source assertions are insufficient; that review workload is visible rather than counted as correct suppression.

Shared retained upstream extraction (annotated fields only; no new extraction run):

| Field | PASS | FAIL | ERROR | UNKNOWN |
|---|---:|---:|---:|---:|
| firm_mdq | 8 | 0 | 0 | 0 |
| segments | 20 | 0 | 0 | 0 |
| zones | 18 | 0 | 0 | 0 |

| Declared disruption example | Captured outcome | Winning rule |
|---|---|---|
| capture-0/46864 | positive | BR-FIRM |
| capture-1/46864 | error | BR-SEMANTICS |
The errored force-majeure example is unresolved coverage, not a passing disruption detection. No Critical-header override is adopted.

| Observed metric | Count |
|---|---:|
| supplied_label_false_positives | 0 |
| supplied_label_false_negatives | 0 |
| unscored_labeled | 13 |
| routine_admin_signaled | 0 |
| duplicate_replay_recommendations | 0 |
| semantic_execution_refusals | 2 |
| history_required_review | 3 |
| labeled_scored | 15 |
| labeled_total | 28 |

Inherited downstream replay: **FAIL**. 11 behavioral failures; 15 unsupported interface observations (UNKNOWN). [Both implementations' replay observations](signals/results.json).

Direct component refusal retention: **PASS**. Direct malformed-status refusal retained across reopen; not WITHDRAWN business semantics or complete lifecycle retention. [Probe](direct-refusal.json).

## Generated consequences of this spec

Captured cases: **46** (two 23-case captures; 14 labels per capture). No abstention is a correct negative.

| Rule | Matches / cases | Wins / cases | First failed conditions (counts) |
|---|---:|---:|---|
| BR-FORMAT | 0/46 | 0/46 | Format: 46 |
| BR-SEMANTICS | 2/46 | 2/46 | Oracle answer: 44 |
| BR-CONTRADICTION | 3/46 | 3/46 | Conflict: 43 |
| BR-HISTORY | 4/46 | 3/46 | History: 42 |
| BR-UNCHANGED | 4/46 | 4/46 | Operational change: 42 |
| BR-ROUTINE | 6/46 | 6/46 | Information-only: 37; Restriction: 3 |
| BR-HISTORICAL | 0/46 | 0/46 | Restriction current: 24; Service class: 22 |
| BR-FIRM | 24/46 | 19/46 | Service class: 22 |
| BR-UNRESOLVED | 46/46 | 9/46 |  |

Previous commit: `4b943c0dc8601a41e550b7de737e845b0643abd2`. Spec-to-spec consequences with current fixed compiler; not a runtime regression mapping

| Notice/capture | From | To |
|---|---|---|
| — | No changed outcome observed | — |

[Every notice's first failed condition](consequences.md). Generated consequences are not independent labels.

## What remains unresolved

- Source timezone stays UNKNOWN where unzoned; no automatic current/future actionability or recommendation authorization.
- WITHDRAWN business semantics, source force-majeure precedence and recall/false-positive tradeoffs need explicit domain decisions.
- Partial D checks do not prove full lifecycle, delivery, retention or materiality obligations.
- Gate 3 needs compatible observed reference evidence; differences remain visible when comparison is not valid.

Code-owned compiled boundary checks: `{'PASS': 23}`. Every D prose obligation remains UNCHECKED. [Separate observations](rule-invariants.json) · [Requirement coverage](coverage.md).

[Raw results](results.json) · [Comparison identity](comparison-identity.json) · [Artifact hashes](manifest.json)

## Contract refusals

- DECLARED_CHECK_UNOBSERVED: No observations for the check declared in spec-verification
- CHECK_DEFERRED: The spec declares this check deferred
- DECLARED_CHECK_UNOBSERVED: No observations for the check declared in spec-verification
- DECLARED_CHECK_UNOBSERVED: No observations for the check declared in spec-verification
- DECLARED_CHECK_UNOBSERVED: No observations for the check declared in spec-verification
- DECLARED_CHECK_UNOBSERVED: No observations for the check declared in spec-verification
- CHECK_DEFERRED: The spec declares this check deferred
- CHECK_DEFERRED: The spec declares this check deferred
- CHECK_DEFERRED: The spec declares this check deferred
- CHECK_DEFERRED: The spec declares this check deferred
- DECLARED_CHECK_UNOBSERVED: No observations for the check declared in spec-verification
- DECLARED_CHECK_UNOBSERVED: No observations for the check declared in spec-verification
