<!-- Index copy of evidence/run-20260928/CURRENT.md, produced by `make gate` (reviewed spec) on commit ca5ef22 with a clean tree. Per-case files are omitted from the commit; re-run the command to regenerate them. -->

# Evidence for the engineer's next decision

Mode **REVIEWED_SPEC** · human review: read receipt matches these spec bytes (an assertion, not authentication) · accepted: **True**.

Non-passing finding codes: **none**. CI accepts only exit 0 from a reviewed run.

| Gate | Status | Why |
|---|---|---|
| 1 — contracts_and_invariants | PASS | All in-scope findings passed |
| 2 — trading_behavior | PASS | All in-scope findings passed |
| 3 — regression_change | PASS | Nothing changed since the reference; this is not a regression test of a change |

Run `final-run` · commit `ca5ef229b9ca35808eb0c170ea77d94805d92f83` · tracked changes `False` · spec `4448a6f9e9ee3841e0086a8e556c21bbd584efc9167742a831154f70e3e18a8e`.

**Not claimed by this gate** (spec-verification `out_of_scope`): HISTORY-003, HISTORY-004, HISTORY-005, STATE-001, STATE-002, STATE-005. All 73 D prose obligations are unchecked prose; 23 code-owned boundary checks constrain the tables.

## For the desk

| Capture | Labeled positives missed (limit) | Labeled negatives signaled (limit) |
|---|---|---|
| capture-0 | 2/7 (2) — 46732, 46881 | 0/7 (0) — none |
| capture-1 | 2/7 (2) — 46732, 46881 | 0/7 (0) — none |

A positive sent to review counts as missed: nobody on the desk receives review items today. Limits are spec-settings `acceptance`.

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
| history_required_review | 3 |
| labeled_scored | 16 |
| labeled_total | 28 |

Inherited system on the 12-step replay: **FAIL** — 10 behavioral failures, 16 observations it has no interface for (UNKNOWN). [Observations](run-20260928/signals/results.json).

Unlabeled recent NGPL notices: 25 HTML headers, 0 input-contract errors; 7/7 PDF outage reports are an unsupported format and go to review. Classifying them needs live extraction.

## Generated consequences of this spec

Captured cases: **46** (two 23-case captures; 14 labels per capture). No abstention is a correct negative.

| Rule | Matches / cases | Wins / cases | First failed conditions (counts) |
|---|---:|---:|---|
| BR-FORMAT | 0/46 | 0/46 | Format: 46 |
| BR-SEMANTICS | 1/46 | 1/46 | Oracle answer: 45 |
| BR-CONTRADICTION | 3/46 | 3/46 | Conflict: 43 |
| BR-HISTORY | 4/46 | 3/46 | History: 42 |
| BR-UNCHANGED | 4/46 | 4/46 | Operational change: 42 |
| BR-ROUTINE | 6/46 | 6/46 | Information-only: 37; Restriction: 3 |
| BR-HISTORICAL | 0/46 | 0/46 | Restriction current: 24; Service class: 22 |
| BR-FIRM | 24/46 | 20/46 | Service class: 22 |
| BR-UNRESOLVED | 46/46 | 9/46 |  |

Previous commit: `c90e5d25267dbf8ef415143561a0b17864c3a9da`. Spec-to-spec consequences with current fixed compiler; not a runtime regression mapping

| Notice/capture | From | To |
|---|---|---|
| — | No changed outcome observed | — |

[Every notice's first failed condition](run-20260928/consequences.md). Generated consequences are not independent labels.

## Open domain questions

- Unzoned NGPL times stay UNKNOWN: no automatic actionability or recommendation.
- WITHDRAWN status, geography priority and absolute-volume meaning need desk rulings (spec A-009).

[Raw results](run-20260928/results.json) · [Coverage](run-20260928/coverage.md) · [Boundary checks](run-20260928/rule-invariants.json) · [Artifact hashes](run-20260928/manifest.json)
