<!-- Index copy of evidence/run-20260928/CURRENT.md, produced by `make gate` (reviewed spec) on commit 0ced592 with a clean tree. Per-case files are omitted from the commit (the replay and trading results are included); the full per-case run is the Gate 3 reference directory. -->

# Evidence for the engineer's next decision

Mode **REVIEWED_SPEC** · human review: read receipt matches these spec bytes (an assertion, not authentication) · accepted: **True**.

Non-passing finding codes: **none**. CI accepts only exit 0 from a reviewed run.

Gates judge the **rebuilt component**. The inherited system is measured below, not gated (12-step replay: **FAIL**).

| Gate | Status | Why |
|---|---|---|
| 1 — contracts_and_invariants | PASS | All in-scope findings passed |
| 2 — trading_behavior | PASS | All in-scope findings passed |
| 3 — regression_change | PASS | Nothing changed since the reference; this is not a regression test of a change |

Run `final-run` · commit `0ced592d4f09cb05c3daed2469bd89a8189ceb0f` · tracked changes `False` · spec `a5bb4e2231092d6da4928c346d8d8f3722c8d44299a721de5c58d4be35249e76`.

Reread by **Thomas Hand**, covering decisions: AUDIT3-001.

Gate 3 reference `evidence/reference-20260928c` (commit `997ff18`), registered by **Thomas Hand**; evaluator/oracle changes it accepted: oracle: context/authority-reference.json, requirements/capture-registry.json, requirements/trading-evidence.json; evaluator: harness/__main__.py, harness/baseline.py, harness/consequences.py, harness/context.py, harness/current_evidence.py, harness/evaluator.py, harness/evidence.py, harness/normalized_evaluation.py, harness/proposals.py, harness/rule_invariants.py, harness/spec_ownership.py, harness/spec_tables.py, harness/trading_evaluation.py, tests/test_audit_controls.py, tests/test_check_registry.py, tests/test_derivation_integrity.py, tests/test_feedback_loop.py, tests/test_spec_owner_review.py, tests/test_spec_predicates.py, tests/test_spec_source.py.

Gate 2 limits, as declared in spec-settings acceptance (the comparison code is guarded by Gate 3 and the reference owner): max_missed_positives_per_capture = 2, max_false_positives_per_capture = 0, review_satisfies = ['SIGNAL-002', 'SIGNAL-004'].

**Not claimed by this gate** (spec-verification `out_of_scope`): HISTORY-003, HISTORY-004, HISTORY-005, STATE-001, STATE-002, STATE-005. D prose is unchecked except D6, which scopes the annotation oracle; 25 code-owned boundary checks constrain the tables.

## For the desk

| Capture | Labeled positives missed (limit) | Labeled negatives signaled (limit) | Labeled negatives sent to review |
|---|---|---|---|
| capture-0 | 2/7 (2) — 46732, 46881 | 0/7 (0) — none | 4/7 — 46528, 46725, 46728, 46795 |
| capture-1 | 2/7 (2) — 46732, 46881 | 0/7 (0) — none | 4/7 — 46528, 46725, 46728, 46795 |
| capture-2 | 2/7 (2) — 46732, 46881 | 0/7 (0) — none | 4/7 — 46528, 46725, 46728, 46795 |

A positive sent to review counts as missed: nobody on the desk receives review items today. Limits are spec-settings `acceptance`. Negatives sent to review have no budget yet; that needs a desk decision on review capacity.

| Capture / system | Detected positives | False positives | True negatives | Negative on positive | Positive unresolved | Negative unresolved | Errors | Unresolved / labeled |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| capture-0 / inherited + 512-token variant | 7/7 | 1 | 6/7 | 0 | 0 | 0 | 0 | 0/14 |
| capture-1 / unmodified inherited captured output | 6/7 | 1 | 5/7 | 0 | 1 | 1 | 2 | 2/14 |
| capture-2 / unmodified inherited captured output | 7/7 | 0 | 6/7 | 0 | 0 | 1 | 1 | 1/14 |
| capture-0 / spec-derived classifier | 5/7 | 0 | 3/7 | 0 | 2 | 4 | 0 | 6/14 |
| capture-1 / spec-derived classifier | 5/7 | 0 | 3/7 | 0 | 2 | 4 | 1 | 6/14 |
| capture-2 / spec-derived classifier | 5/7 | 0 | 3/7 | 0 | 2 | 4 | 1 | 6/14 |

Every capture carries the same 14 labels; captures are repeated runs of the inherited system, not independent samples. capture-0 raised its impact-verdict token budget to 512; later captures are unmodified runs (see the registry for their dates and models). Unresolved cases are never counted as correct.

Upstream extraction retained from the inherited runs (no new model call):

| Check | PASS | FAIL | ERROR | UNKNOWN |
|---|---:|---:|---:|---:|
| firm_mdq | 12 | 0 | 0 | 0 |
| links | 69 | 0 | 0 | 0 |
| quantities | 69 | 0 | 0 | 0 |
| segments | 30 | 0 | 0 | 0 |
| zones | 27 | 0 | 0 | 0 |

Where the captures disagree (the same labeled notice, different runs of the inherited system):

| Notice | Label | capture-0 inherited / rebuilt | capture-1 inherited / rebuilt | capture-2 inherited / rebuilt |
|---|---|---|---|---|
| 46528 | no signal | signal / UNRESOLVED | MODEL_FAILURE / UNRESOLVED | MODEL_FAILURE / UNRESOLVED |
| 46725 | no signal | no signal / UNRESOLVED | signal / UNRESOLVED | no signal / UNRESOLVED |
| 46864 | signal | signal / SIGNAL_CANDIDATE | MODEL_FAILURE / SIGNAL_CANDIDATE | signal / SIGNAL_CANDIDATE |

| Observed count | Cases |
|---|---:|
| supplied_label_false_positives | 0 |
| supplied_label_false_negatives | 0 |
| unscored_labeled | 18 |
| routine_admin_signaled | 0 |
| duplicate_replay_recommendations | 0 |
| semantic_execution_refusals | 2 |
| history_required_review | 9 |
| labeled_scored | 24 |
| labeled_total | 42 |

Inherited system on the 12-step replay: **FAIL** — 10 behavioral failures, 16 observations it has no interface for (UNKNOWN). [Observations](run-20260928/signals/results.json).

Unlabeled recent NGPL notices: 25 HTML headers, 0 input-contract errors; 7/7 PDF outage reports are an unsupported format and go to review. Classifying them needs live extraction.

## Generated consequences of this spec

Captured cases: **69** (3 captures of 23 cases; 14 labels per capture). No abstention is a correct negative.

| Rule | Matches / cases | Wins / cases | First failed conditions (counts) |
|---|---:|---:|---|
| BR-FORMAT | 0/69 | 0/69 | Format: 69 |
| BR-SEMANTICS | 2/69 | 2/69 | Oracle answer: 67 |
| BR-CONTRADICTION | 5/69 | 5/69 | Conflict: 64 |
| BR-HISTORY | 9/69 | 7/69 | History: 60 |
| BR-UNCHANGED | 6/69 | 6/69 | Operational change: 63 |
| BR-ROUTINE | 9/69 | 9/69 | Information-only: 55; Restriction: 5 |
| BR-HISTORICAL | 0/69 | 0/69 | Restriction current: 36; Service class: 33 |
| BR-FIRM | 36/69 | 30/69 | Service class: 33 |
| BR-UNRESOLVED | 69/69 | 10/69 |  |

Previous commit: `997ff186f30ca11337177729f934b63e14830f07`. Spec-to-spec consequences with current fixed compiler; not a runtime regression mapping

| Notice/capture | From | To |
|---|---|---|
| — | No changed outcome observed | — |

[Every notice's first failed condition](run-20260928/consequences.md). Generated consequences are not independent labels.

## Open domain questions

- Unzoned NGPL times stay UNKNOWN: no automatic actionability or recommendation.
- WITHDRAWN status, geography priority and absolute-volume meaning need desk rulings (spec A-009).

[Raw results](run-20260928/results.json) · [Coverage](run-20260928/coverage.md) · [Boundary checks](run-20260928/rule-invariants.json) · [Artifact hashes](run-20260928/manifest.json)
