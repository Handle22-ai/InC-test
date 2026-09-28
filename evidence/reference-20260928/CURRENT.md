# Evidence for the engineer's next decision

Mode **REVIEWED_SPEC** · human review: read receipt matches these spec bytes (an assertion, not authentication) · accepted: **False**.

Non-passing finding codes: **EVALUATOR_OR_ORACLE_CHANGED, REGRESSION_COMPARISON**. CI accepts only exit 0 from a reviewed run.

Gates judge the **rebuilt component**. The inherited system is measured below, not gated (12-step replay: **FAIL**).

| Gate | Status | Why |
|---|---|---|
| 1 — contracts_and_invariants | PASS | All in-scope findings passed |
| 2 — trading_behavior | PASS | All in-scope findings passed |
| 3 — regression_change | UNKNOWN | Harness, tests or evaluation oracle changed since the reference (evaluator); register a reviewed reference before this comparison can pass |

Run `reviewed-run` · commit `5c91e8b9b596e530f3f7e337d24c8e0055743a2b` · tracked changes `False` · spec `c89f760b3f2167345112801cd7825d26c40c102996239d13a2c788c9c4d363b6`.

**Not claimed by this gate** (spec-verification `out_of_scope`): HISTORY-003, HISTORY-004, HISTORY-005, STATE-001, STATE-002, STATE-005. All 73 D prose obligations are unchecked prose; 23 code-owned boundary checks constrain the tables.

## For the desk

| Capture | Labeled positives missed (limit) | Labeled negatives signaled (limit) | Labeled negatives sent to review |
|---|---|---|---|
| capture-0 | 2/7 (2) — 46732, 46881 | 0/7 (0) — none | 4/7 — 46528, 46725, 46728, 46795 |
| capture-1 | 2/7 (2) — 46732, 46881 | 0/7 (0) — none | 4/7 — 46528, 46725, 46728, 46795 |

A positive sent to review counts as missed: nobody on the desk receives review items today. Limits are spec-settings `acceptance`. Negatives sent to review have no budget yet; that needs a desk decision on review capacity.

| Capture / system | Detected positives | False positives | True negatives | Negative on positive | Positive unresolved | Negative unresolved | Errors | Unresolved / labeled |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| capture-0 / inherited + 512-token variant | 7/7 | 1 | 6/7 | 0 | 0 | 0 | 0 | 0/14 |
| capture-1 / unmodified inherited captured output | 6/7 | 1 | 5/7 | 0 | 1 | 1 | 2 | 2/14 |
| capture-0 / spec-derived classifier | 5/7 | 0 | 3/7 | 0 | 2 | 4 | 0 | 6/14 |
| capture-1 / spec-derived classifier | 5/7 | 0 | 3/7 | 0 | 2 | 4 | 1 | 6/14 |

Both captures carry the same 14 labels and are not independent samples. capture-1 is the unmodified inherited run; capture-0 raised its impact-verdict token budget to 512. Unresolved cases are never counted as correct.

Upstream extraction retained from the inherited runs (no new model call):

| Check | PASS | FAIL | ERROR | UNKNOWN |
|---|---:|---:|---:|---:|
| firm_mdq | 8 | 0 | 0 | 0 |
| links | 46 | 0 | 0 | 0 |
| quantities | 46 | 0 | 0 | 0 |
| segments | 20 | 0 | 0 | 0 |
| zones | 18 | 0 | 0 | 0 |

| Observed count | Cases |
|---|---:|
| supplied_label_false_positives | 0 |
| supplied_label_false_negatives | 0 |
| unscored_labeled | 12 |
| routine_admin_signaled | 0 |
| duplicate_replay_recommendations | 0 |
| semantic_execution_refusals | 1 |
| history_required_review | 5 |
| labeled_scored | 16 |
| labeled_total | 28 |

Inherited system on the 12-step replay: **FAIL** — 10 behavioral failures, 16 observations it has no interface for (UNKNOWN). [Observations](signals/results.json).

Unlabeled recent NGPL notices: 25 HTML headers, 0 input-contract errors; 7/7 PDF outage reports are an unsupported format and go to review. Classifying them needs live extraction.

## Generated consequences of this spec

Captured cases: **46** (two 23-case captures; 14 labels per capture). No abstention is a correct negative.

| Rule | Matches / cases | Wins / cases | First failed conditions (counts) |
|---|---:|---:|---|
| BR-FORMAT | 0/46 | 0/46 | Format: 46 |
| BR-SEMANTICS | 1/46 | 1/46 | Oracle answer: 45 |
| BR-CONTRADICTION | 3/46 | 3/46 | Conflict: 43 |
| BR-HISTORY | 6/46 | 5/46 | History: 40 |
| BR-UNCHANGED | 4/46 | 4/46 | Operational change: 42 |
| BR-ROUTINE | 6/46 | 6/46 | Information-only: 37; Restriction: 3 |
| BR-HISTORICAL | 0/46 | 0/46 | Restriction current: 24; Service class: 22 |
| BR-FIRM | 24/46 | 20/46 | Service class: 22 |
| BR-UNRESOLVED | 46/46 | 7/46 |  |

Previous commit: `0164af56c69e227c574b72b624da2f16bdc77bd2`. Spec-to-spec consequences with current fixed compiler; not a runtime regression mapping

| Notice/capture | From | To |
|---|---|---|
| — | No changed outcome observed | — |

[Every notice's first failed condition](consequences.md). Generated consequences are not independent labels.

## Open domain questions

- Unzoned NGPL times stay UNKNOWN: no automatic actionability or recommendation.
- WITHDRAWN status, geography priority and absolute-volume meaning need desk rulings (spec A-009).

[Raw results](results.json) · [Coverage](coverage.md) · [Boundary checks](rule-invariants.json) · [Artifact hashes](manifest.json)
