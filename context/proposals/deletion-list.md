# Proposal: what to delete, and what each deletion stops detecting (fourth audit #30, #7)

Status: **proposed, nothing deleted.** The owner decides from the table. Once approved, all
deletions land together with #5 and #14 before one reread and one reference registration, and
harness.md gets one paragraph on what was removed and why.

## Method

Each candidate was removed in its own scratch clone of commit `3dcc801`. The clone then ran
seven mutation probes, each committed on top of the removal, plus an unmutated control. For each
run the table records `harness compile`, `harness gate --proposal` (exit and finding codes) and
`make check`. A deletion counts as costing detection if a probe that was red at baseline goes green.

| Probe | Mutation |
|---|---|
| P1 | BR-CONTRADICTION action → NO_OPERATIONAL_RESTRICTION |
| P2 | BR-FIRM moved above BR-UNCHANGED in the precedence line |
| P3 | BR-FIRM moved above BR-HISTORICAL |
| P4 | `overlaps` → `within` in the FIRM_DISRUPTION predicate |
| P5 | Hand-edit of `requirements/behavior.yaml`, with its hash refreshed in `compiled-build.json` |
| P6 | `max_missed_positives_per_capture` 2 → 4 under an approved row without LOOSENS_ACCEPTANCE |
| P7 | Committed edit to `context/assumptions.md` (A-004 "block" → "allow" automatic alerts) |

Baseline (no deletion):

| Probe | compile | gate --proposal | make check |
|---|---|---|---|
| control | — | 3: EVALUATOR_OR_ORACLE_CHANGED, REGRESSION_COMPARISON | 0 |
| P1, P2, P3 | 2 BOUNDARY_VIOLATION | 5 | 69 tests fail |
| P4 | 0 | 3, adds UNMEASURED_POLICY_EDIT | 1 test fails (see note 1) |
| P5 | not run | 5 GENERATED_ARTIFACT_DRIFT | 22 fail |
| P6 | 2 ACCEPTANCE_LOOSENED | 5 | 53 fail |
| P7 | 0 | 3, same codes as control | 0 (**undetected**; `make context` also exits 0) |

## Candidates

| # | Item | Files and lines | spec.md / CURRENT.md lines removed | What it detected (probe results with it removed) | Recommendation |
|---|---|---|---|---|---|
| 1 | `evidence/audit-truth/` files that no command opens and no document links (the 2 linked files stay), plus 4 unused `artifacts/` files | 359 files, 12 MB | none | All seven probes identical to baseline; control passes. No test, gate, consequences, context or compile run opens them (traced with an audit hook). **Could never fail.** | Delete |
| 2 | `harness/storage_evaluation.py` and the tests that exist only for it | 511 + ~30 lines | none | All probes identical. It serves STATE-001/002 (its `STORAGE_IDS`), which are declared `out_of_scope`; no gate, context or consequences run calls it. Control fails only `test_every_manifest_path_exists`, because the hash-registered `context/manifest.yaml` still names it twice. **Could never fail.** | Delete. The owner updates the manifest and re-registers it (an oracle change) |
| 3 | CAPTURED_UPSTREAM_EXTRACTION as gate findings (OUTPUT-002 to 006) | ~0 net code; findings move to a report list | 5 spec-verification rows become `out_of_scope`; one `bounds` entry drops; results lose 207 of 423 finding rows; CURRENT.md's extraction table stays | All probes identical. These rows re-check frozen inherited output, so no change under `rebuilt/` can move them. Control loses `test_contradictory_spec_bounds_fail_at_the_spec_block` (it uses the OUTPUT-002 bound; move it to OUTPUT-001). | Demote to a report table. Declaring OUTPUT-002 to 006 `out_of_scope` narrows what the gate claims: a policy decision for the owner, in the same decision row |
| 4 | `context/assumptions.md`, `context/assumptions-register.json`, `context_integrity.verify_assumptions` and its test | 16 + 58 + ~38 + ~20 lines | none (spec.md keeps the live A-001 to A-009 table) | P1–P6 identical; P7 not applicable. At baseline P7 is **undetected** by compile, gate, `make check` and `make context`: the only caller of `verify_assumptions` is a test. **Could never fail.** | Delete; drop its CODEOWNERS line; point `context/domain.md` at spec.md |
| 5 | `spec-checks`: the "Sentence coverage" column (UNCHECKED on all 73 rows), the 32 rows that name no boundary, the compile rule that every D sentence has a row, and the 73 `D_SENTENCE_UNCHECKED` rows in rule-invariants | ~25 lines of code; 4 tests that pin the removed rows | spec.md −32 lines (table 73 → 41 rows) | P1–P5 and P7 identical. **P6 went green**: the loosening guard compiled the reviewed spec with the new compiler, failed, and treated that as "nothing loosened". Fixed in `8381144` (the guard reads the reviewed settings without compiling). Re-run with the fix: P6 refused (ACCEPTANCE_LOOSENED). | Do it. The 41 remaining rows are the D-sentence references the 25 boundaries print |
| 6 | Duplicated `$.history[]` rows in `spec-interfaces` | ~15 lines of generator code in `spec_tables.py` | spec.md −38 lines (38 of 39 history rows are byte-identical to their top-level twin; ~90 was an overestimate) | Not probed: this is a generator, not a deletion. The generated-drift check and the schema tests cover the result. | Do it, and probe after implementing |
| 7 | CURRENT.md header | renderer only | 26 lines before the desk view, several over 300 characters → about 10: mode and acceptance, the gate table, the reviewer. Run identity, reference files, spec-edit lists, Gate 2 limits and out-of-scope rows move below the desk view | Not probed: probes judge exit and finding codes, which a renderer cannot change. | Do it |
| 8 | OUTPUT_IDENTITY rows | renderer/report only | results lose 78 of 79 rows (one PASS row per capture with a count; every FAIL kept) | Not probed; no probe targets identity. It is a real invariant (it would catch a component that reports the wrong notice or source hash), so collapse it, don't delete it. | Collapse |
| 9 | `harness/e2e.py`, `harness/storage_ports.py`, `tests/test_e2e.py` | 287 + 136 + 63 lines | README loses `make e2e-live` | Offline probes cannot reach it: it runs only with LIVE=1 against freshly fetched notices. It produced the brief's one end-to-end run. | Owner decision: keep while `make e2e-live` is a README command, otherwise delete |
| 10 | Superseded ADRs (`context/decisions/001–012`) and history-only proposals (`context/proposals/*.md` except this one) | 22 + 7 files | none | Not probed. They are hash-registered in `context/authority-reference.json`, and `make context` opens them, so deleting them is a context-authority change. | Hold. Later, move the superseded ones to `docs/history/` with one re-registration |

Checked and kept:
- `harness/signal_evaluation.py` (521 lines) is the 12-step publisher replay the gate runs, not a second evaluator of the classifier. The duplicated evaluation path that drifted before (AGENT-LIVE-PATH) is the live evaluator: `evaluator.py`, `gates.py`, `evidence.py`, `preflight.py`, `regression.py` and `adapter.py`, about 1,460 lines. It is the only way a live run becomes a scored capture, and `tests/test_check_registry.py` now binds its check names to the offline gate's. Keep it.
- As the auditor listed: the spec compiler, the generated-drift check, the 25 code-owned boundaries, consequences, the per-capture desk table, the stub-versus-real reconciliation table, and the #2 and #3 checks.

## Notes

1. **P4 is caught by `make check` only by accident.** The failing test, `test_same_policy_runtime_regression_fails_behavior_and_change_gates`, runs a real baseline against the registered reference. Any spec table edit adds an UNMEASURED_POLICY_EDIT finding for OBS-003, and the test asserts exactly one OBS-003 observation. It fails for any unmeasured spec edit, not because FIRM_DISRUPTION changed (C2's own spec edit trips it the same way). The gate's UNMEASURED_POLICY_EDIT is the real signal for P4. Fix: give the test its own reference, so that it does not depend on the repository's reference.
2. **P7 has no detector at baseline.** Item 4 removes the file rather than guarding it, because spec.md already holds the live assumptions.
3. Probing found one defect (item 5, fixed in `8381144`); the other deletions found none.
4. Stop criterion, not yet met. The seven probes exercise the compile boundaries, the generated-drift check, UNMEASURED_POLICY_EDIT and the loosening guard. The input-contract probes, frozen witnesses, Gate 2 budgets and Gate 3 comparison each have their own mutation tests in `make check`, but these were not rerun per deletion. Items 6, 9 and 10 need the owner's call or a follow-up probe.
