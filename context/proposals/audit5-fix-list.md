# Fifth audit: ordered fix list (proposal, nothing adopted)

Source: the fifth audit of `3aaba89` (2026-09-28). Finding numbers (#n) refer to that audit's table. The list is ordered by value per unit of effort. Within each tier, the first item matters most.

## Done on branch `audit5-doc-fixes` (documentation only; no spec, harness, test or oracle change)

| # | Fix | File |
|---|---|---|
| 1 | Define "missed" as classification ≠ SIGNAL_CANDIDATE; state that every candidate is also REVIEW_REQUIRED, so nothing reaches the desk; state that the budget equals today's misses | harness.md |
| 4, 5 | Drop "identical on all three captures"; list the per-capture differences; 46528 is ERROR, not review, in captures 1–2 | harness.md |
| 6 | Report the fourth live run (5/7; 46507 lost to a missing verdict) and retitle the recall row | harness.md |
| 32 | Say which "has caught" claims are held by tests (none of the cited codes) and which the fifth audit reproduced | harness.md |
| 10, 31, 33 | Consequences headline caveat; call counts per full run; `e2e-live` is a one-notice smoke test | README.md |
| 18, 20, 21, 22 | Ledger scope and the missing sessions; NNS session reads; incomplete entries marked; AUDIT4-001 status; an entry for the fifth audit's reads | evidence/code_reads.md |
| 19 | Operational instructions and the failed `make check` recorded | evidence/fresh_session.md |
| 23 | Current registration 695cc5f and its "reviewed" wording | evidence/ARCHIVE.md |
| 27 | Per-case files come from an equivalent run, not this one | evidence/CURRENT.md (index comment) |
| 7 | 46528 reproduced a missing verdict, not a signal from one | docs/positions.md |

## Tier 1: evaluator fixes (harness/ or tests/, one commit each, then owner review and a new reference)

1. **Done in `3fb95fa`: #3 Make consequences agree with the gate.** Parity test added. Open: state the history-retention rule in spec.md (Tier 2), and the owner registers a new reference. Evaluate each case on the runtime's own normalized input, including each capture's history. Add a test: consequences `matched_rule` equals gate `matched_rule` on all 69 cases. Today they differ on capture-2's two revision cases (BR-HISTORY 7 vs 9, BR-UNCHANGED 6 vs 4). This is the highest-value fix: the engineer is told to trust this preview.
2. **Done in the commit after `96b9101`: #11 A spec type change must produce a finding, not a crash.** It now exits 4 and names spec.md:447. Open: the catch-all in `normalized_evaluation.py` still labels any harness exception SPECIFICATION_INTEGRITY_ERROR without a traceback. INPUT-SOURCE-022 `integer`→`text` gives `KeyError: 'candidate_classification'`, reported as SPECIFICATION_INTEGRITY_ERROR. Catch the error per case, emit INPUT_CONTRACT_MISMATCH naming the row, and add a test.
3. **#32 One negative-control test per gate code** that no test holds: INPUT_DATE_FORMAT_MISMATCH, ROUTINE_ADMIN_SIGNALED, LABELED_MISSED_POSITIVES, LABELED_FALSE_POSITIVES, MODEL_CONFIG_CHANGED. Use the fifth audit's mutations: day-first date format, BR-FIRM action → UNRESOLVED, scheduled-MDQ unit → PERCENT, `LLM_MODEL=x`.
4. **#12 Flag every unmeasured table edit.** Raise UNMEASURED_POLICY_EDIT for action edits, as consequences already does. Show D-sentence and assumption edits in CURRENT.md's headline, not only in the reread record.
5. **#13 Mark an unreviewed spec in the context package.** When the spec hash differs from `context/spec-read-pin.json`, `make context` should stamp package.md "spec unreviewed" or refuse. Either way, say that the assumptions table is prose with no check.
6. **#14 In proposal mode, compute "covered by the last reread" from the pin only.**
7. **#2 Rename `supplied_label_false_negatives`** to `…_decided_negative`, or count unresolved positives in it.
8. **#10 Name the refusing stage in the consequences headline** (compile, witness or gate).
9. **#45 Remove string- and count-coupled tests** that fail on harmless edits (the fifth audit's precedence and quantifier mutations).
10. **#34 Preflight: `helpers_complete` should be false or N/A when extraction failed.**

## Tier 2: spec prose (a `proposed` decision row, then the owner approves and rereads)

Run `make consequences` first; all of these should show 0 changed outcomes.
- #15 spec.md:203: "23 listed below, plus `refusals_first` and `required_inputs`, which are keyed on conditions", or list the two rows so their violations stop reporting `spec.md:1`.
- #16 spec.md:284: define all four statuses the compiler accepts (`proposed`, `owner-requested`, `approved`, `rejected`).
- #8 Split STATE-003 into what the replay observes (at most one initial alert at the seam) and an `out_of_scope` part (persistent keys, acknowledgement). Consider the same for OBS-001.
- #9 Report `review_satisfies` rows as REVIEW_AS_SPECIFIED, not PASS. This also needs an evaluator change (Tier 1).
- #30 NNS-FIRM-001's "desk request": leave the approved row, but move the correction from AUDIT4-001's prose into a status the report shows.

## Tier 3: owner and desk decisions (no code until decided)

- #35 A miss tolerance and a review capacity set by someone other than the author. Until then, report Gate 2 as "no regression from the 2026-09-28 baseline", not PASS.
- #36 REMEDIATION-001: either state it as an accepted risk (a firm disruption with a failed helper still becomes a candidate, which is the behavior harness.md lists as an inherited defect), or restore the veto and accept 46864's miss.
- #37 Name a review owner. Run the 25 unlabeled HTML notices live (about 40 calls) and report the review rate.
- #44 Decide whether each live run can be registered as an observation-only capture that does not move the oracle. The fourth run (5/7) is currently outside the repository.
- #41 Decide whether the runtime should refuse on a stale reread, or only CI and deploy should.
- #42 Evidence of branch protection (an API response or screenshot) and one PR the gate blocked.

## Tier 4: delete (use `context/proposals/deletion-list.md`'s probe-per-item method)

- #24 `context/spec-owner-review.json` (PENDING_PERSON, old spec) and the stale bindings in `context/authority-reference.json`: regenerate or delete. Stale protected files look authoritative.
- #25 The nine missing files pinned in `requirements/capture-registry.json` and its missing `source_pin`: unpin (an oracle change) or restore. Add a dead-link check to `make check`; the audit found 131 dead targets.
- #26 `context/approvals/012/manifest.yaml:9`: remove the reference to the deleted `artifacts/runtime_requirements.md`.
- #40 `main.py` (a PyCharm stub), `templates/`, `variants/`, legacy ADR records superseded by spec.md, and the eight UNAPPROVED pending-learning notes that are resolved. Move D-prose with no check to an appendix.
- #39 `rebuilt/store.py` and `snapshot.py` serve out-of-scope requirements: freeze them as a separate component with a stated contract, or delete them and their tests.

## Tier 5: evidence to redo

- #43 Rerun the fresh-session exercise on HEAD from a separate session, and replace fresh_session.md's record. The fifth audit's rerun (suffixed amendment IDs) proposed rather than edited, and opened 3 source files because the package does not state identifier types.
- #20 Regenerate the ledger over every transcript directory whose sessions touch this repository's paths.
