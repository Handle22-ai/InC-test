# Where the code was read anyway

Commit IDs below refer to the earlier, unpublished history (see [ARCHIVE.md](ARCHIVE.md)); they cannot be checked from this repository.

**The full ledger is generated, not written by hand:** [code-read-ledger/LEDGER.md](code-read-ledger/LEDGER.md), made by `code-read-ledger/generate.py` from the Claude Code transcripts and subagent transcripts in this project's own transcript directory (its first line gives the current counts). It does not cover sessions started with a scratch directory as their working directory, which Claude Code files under a different project directory. The fifth audit found at least five such sessions missing: 72f48bc1 (edited `inherited/notice_parser.py`, `rebuilt/normalization.py` and `rebuilt/signals.py`, and created `rebuilt/source_times.py`), b46b1da3 (edited `rebuilt/source_input.py`, read 7 harness modules), cf419715 (edited `rebuilt/store.py` and 5 harness files), a5b54ffe and 5fe647b9 (harness reads). Transcripts of the sibling checkout `../incommodities-test`, and reads made after the ledger was last generated, are also missing. It classifies each tool call mechanically; its rules and limits are in the script. The entries below explain the reads that mattered. Where they disagree with the ledger, the ledger is right. Codex sessions are not in the ledger; their reads are the hand-reconstructed table below.

The human owner reports no direct source reads. The transcripts show three IDE-open events, each while an agent session ran: `harness/trading_evaluation.py` (session 3bd56e2e, 09-28 ~09:28Z) and `harness/behavior_contract.py` (sessions 2edc1739 and 2348e84d). Whether the file was read is not recorded. Every other read below was made by an agent: the building agent, an audit, or a maintenance subagent. The question for each read is what the harness could not show without it.

## What the reads say about the harness

| Pattern | Reads | What the harness lacked | Status after remediation (2026-09-28) |
|---|---|---|---|
| Finding the inherited system's worst defect | V2 diagnosis: `inherited/llm_utils.py:525–559`, `notice_validator.py:273–309` | Traces showed missing impact verdicts but not that a missing verdict silently scores "small" | Partly closed: the replay's semantic-safety relation exposes the fallback from behavior. Nothing names it without a read. |
| What a rule column means | Every fresh session opened `harness/domain_rules.py` to learn what FIRM_DISRUPTION is | Predicate meaning lived in harness code, not in spec.md | **Partly closed.** Rule, set and mapping changes need less harness reading: the NNS session read component files and ran two greps over harness code and a probe that imported the harness oracle (see fresh_session.md), but opened no harness module to learn what "firm" means. Parser and format changes still do: a second audit's fresh session (timezone-suffixed timestamps) read 7 harness modules to learn how `date_formats` reaches the parser checks. |
| The component was the harness | The gate imported the component, and the component imported the harness | No separation between oracle and implementation, so agreement checks were circular | **Closed:** `rebuilt/` imports nothing from `harness/`, and a test enforces it. |
| The author graded itself | The orchestrating thread wrote `rebuilt/*.py`, then re-read it ~25 times while evaluating it | No independent writer/evaluator split | Open. The gate now flags evaluator/oracle edits (Gate 3 EVALUATOR_OR_ORACLE_CHANGED), but one thread still writes both. |
| Audits reading on the human's behalf | Supplied audits read `inherited/` and `harness/`; the ledger shows 23 transcripts (audits, their helpers and the build sessions) touching `rebuilt/` as of 2026-09-28, and the second and third audits (7f5d703d, a612115b) mutated `rebuilt/rule_engine.py` and `harness/trading_evaluation.py` in scratch copies | Self-reported evidence did not reveal its own false PASSes | Partly closed: Gates 1–2 now judge declared budgets instead of staying UNKNOWN, and Gate 3 names moved files. |

## Reads missing from the earlier ledger

Reconstructed on 2026-09-28 from the Codex and Claude Code transcripts by an audit agent.
Times are UTC and approximate. None of these is a human read.

| When | Session | Files | Why | Gap |
|---|---|---|---|---|
| 09-26 20:17, 20:37 | Codex a80187497d22 | `rebuilt/` (the two early "fresh" maintenance runs) | Maintenance, run in the same thread that wrote the component ("I can see earlier coding messages") | The "fresh session" was not fresh |
| 09-26 22:07 | Codex c2bc81cb4ef5 | Edit to `rebuilt/snapshot.py` during finalization | Finalization fix | Component edit outside a recorded maintenance exercise |
| 09-27 00:07–00:19 | Codex c2bc81cb4ef5 | `inherited/main.py`, `notice_scraper.py`, `notice_parser.py` (NoticeProcessor, lines 528–585) | Building the E2E command | No documented inherited CLI contract |
| 09-27 00:38 | Evaluator review | R-01…R-08 in `evaluator-reviews/20260927T003830.293495Z/reviewer-source-reads.md` | Independent review | Was not linked from this index |
| 09-27 23:14 | Codex 577a50af3f44 ("independent verification") | `rebuilt/signals.py` 1–260 | Verification | Verification read the implementation instead of evidence |
| 09-28 00:47–01:04 | Codex 2fa72f4acba4 | Spec-only build in `/private/tmp`; its ledger says no reads, but the thread already held repository context | "Build from spec only" | The builder was not context-isolated |
| 09-28 01:50–03:32 | Codex 2fa72f4acba4 | `normalized_classifier.py`, `signals.py`, `normalization.py` (the B9CD042 reads, previously "cannot be reconstructed") | Integration | See the author/evaluator pattern |
| 09-26 – 09-28 | Claude audits at f7de5a5, 9c75f30, 019de93, b9cd042 (×2), b2c82e9, and one more | `inherited/` and `harness/` file:line citations | Supplied audits (proxy reads) | Only 3 of 10 audits had proxy entries |
| 09-28 | Claude session 2edc1739 (began as an audit, then did the remediation) | Created `rebuilt/rule_engine.py` (the evaluator, about 240 lines), rewrote `rebuilt/normalized_classifier.py`, and edited `normalization.py` and `signals.py`, plus many `harness/` modules. One pre-publication commit changed the component (`rule_engine.py`, `signals.py`) and the oracle (`domain_rules.py`, `signal_evaluation.py`) together. | Separating the component from the harness; the publisher snapshot rule | The same session wrote the component and changed the evaluator that judges it, in one commit. Gate 3 now flags such edits, but it did not exist yet when that commit was made. |

## Live path drift (second audit's live run, 2026-09-28)

CODE-READ-ID: AGENT-LIVE-PATH-20260928
Observed failure: `make evaluate-inherited LIVE=1` produced HARNESS_FAILURE findings recorded only as `check_error: ValueError`, so Measurement valid was False; preflight on README's MAX_CALLS=1 reported `observed_signal: true` although the helper call was blocked.
Why evidence was insufficient: the error record kept the exception type but not its message, and no check tied the spec's check names to the live evaluator.
Source inspected: `harness/gates.py` (check dispatch), `harness/evaluator.py`, `harness/preflight.py`, `harness/adapter.py`, `harness/live.py`.
What was learned: the remediation added the check names `refusal` and `replay` to spec-verification and the offline gate, but the live evaluator had no branch for them. The offline and live paths drifted, and nothing bound them together.
Missing harness capability: one registry of check names that both paths must cover; error records that keep the message; a preflight that refuses when any call is blocked; a command that turns a live run into a scored capture.
Harness improvement made: `spec_compiler.CHECK_NAMES` plus `tests/test_check_registry.py` (every name needs a live branch, and the live scoring of a retained live capture has no HARNESS_FAILURE); messages kept; preflight refuses blocked calls (tested with budgets 1 and 2); `python -m harness register-capture`; a cross-capture differences table in CURRENT.md. These are evaluator changes, reported by Gate 3 as EVALUATOR_OR_ORACLE_CHANGED until the owner registers a new reference.
Could the same code read be avoided next time? Yes. A new check name without a live branch now fails `make check` before any live run.
Result: the first full live run after the fix (`evidence/legacy/20260928T180936.681804Z`, 38 calls, registered as capture-2) had no HARNESS_FAILURE. It exposed one more gap: "Measurement valid" and the exit code counted the inherited system's own unusable verdicts (46528, restart-replay) as an invalid measurement. Validity now depends on the calls being answered, and those two cases are findings (`harness/evidence.py`, `harness/evaluator.py`). That run's own summary.md was written by the old code and still says False; it was left as written.

## Reads behind the second- and third-audit fixes (2026-09-28)

CODE-READ-ID: AGENT-AUDIT2-FIXES-20260928
Observed failure: second audit #4 (missing-prior given a prior it never had), the control-plane findings, and the live-path drift; third audit #1–#9.
Why evidence was insufficient: the evidence showed the wrong outcome (History=COMPLETE on missing-prior, an accepted gate after a self-registered reference, a relaxed input row passing) but not where the harness built it.
Source inspected (agent, harness side): `harness/captures.py`, `consequences.py`, `trading_evaluation.py`, `normalized_evaluation.py`, `proposals.py`, `spec_compiler.py`, `current_evidence.py`, `rule_invariants.py`, `baseline.py`, `spec_ownership.py`, `context.py`, `gates.py`, `evaluator.py`, `preflight.py`, `adapter.py`, `live.py`, `offline.py`, `comparison_identity.py`, `input_contract_checks.py`, and the affected tests. Component side: none beyond `rebuilt/signals.py` (earlier entry).
What was learned: history was accumulated per capture, not per case; registration and reread accepted any name; the input-contract check compared the parser with the same row it reads; precedence was guarded only for named rules.
Missing harness capability: per-case store isolation; owner-bound registration with recorded accepted changes; code-owned boundaries for required inputs and refusal-first precedence keyed on conditions, not names; consequences running frozen witnesses.
Harness improvement made: all of the above, with tests. These are evaluator changes, so Gate 3 reports EVALUATOR_OR_ORACLE_CHANGED until the owner registers a new reference.
Could the same code read be avoided next time? Partly. The new boundaries and tests catch these mutations directly; locating a harness bug from a wrong outcome still needs a read.

CODE-READ-ID: AGENT-AUDIT2-FRESH-20260928
Observed failure: none; a second audit's fresh session was asked to accept CT/CST/CDT-suffixed timestamps.
Source inspected (agent, reported by the auditor): `rebuilt/source_input.py` (edited), `rule_engine.py`, `normalization.py`, `normalized_classifier.py`, `classifier.py`, and 7 harness modules: `spec_compiler.py` (5 times), `input_contract_checks.py`, `signal_evaluation.py`, `specification.py`, `captures.py`, `consequences.py`, `domain_rules.py`.
Why evidence was insufficient: not recorded by the auditor (entry incomplete).
Missing harness capability: the package did not say how `date_formats` reaches the parser checks. The manifest instructions now say so; see `context/pending-learning/source-format-changes.md`.
Could the same code read be avoided next time? Partly; format changes still need a parser edit.

CODE-READ-ID: AGENT-AUDIT3-FRESH-20260928
Observed failure: none; the third audit's fresh session was asked to make absolute Dth/d curtailments candidates and carry the volume on the decision.
Source inspected (reported by the auditor): `inherited/llm_utils.py`, five in-scope `rebuilt/` files, and `harness/gates.py` (out of scope, to learn why Gate 3 failed).
Why evidence was insufficient: not recorded by the auditor (entry incomplete).
Missing harness capability: not recorded (entry incomplete); the Gate 3 read suggests CURRENT.md did not list the failing finding.
What was learned: a D6 prose edit silently took the annotation oracle out of scope (now declared in spec.md). The session moved its rule into the unchecked assumptions table to get green, and its own `--inputs` examples cleared UNMEASURED; examples no longer clear it.
Could the same code read be avoided next time? The Gate 3 read, yes: CURRENT.md now lists every non-passing finding and the D6 binding is stated in the spec.

## Detailed entries (retained)

Earlier ledgers:

| Record | Evidence gap and learning |
|---|---|
| [V2 diagnosis](reviews/v2/code_reads.md) | Traces showed missing impact verdicts but needed a read to identify the silent small-impact fallback; reporting now separates generation, interpretation and acceptance. |
| [Rebuild](rebuild/20260926T194455.389677Z/code_reads.md) | A fair port needed actual FK invocation protocol; the mistaken first port is retained. Exact readback now supplements counts. |
| [Optional field](maintenance/20260926T201903.969882Z/code_reads.md) | Shared payload checks cannot prove native metadata; old-writer fixture/native tests were added. |
| [Alias reader](format-compatibility/20260926T204022.284775Z/code_reads.md) | Decoder/validator boundary needed inspection; separate conflict/type/canonical-write tests retain the learning. |
| [Audit](audit/20260926T211023.984214Z/context_recovery.json) | Source reads verified command safety, independent derivation and attribution; no repair occurred. |
| Finalization | Inspected Makefile, adapter import/configuration, context selector, gates/reporters and preserved snapshots. dotenv 1.0.0 still loads credentials for nominally offline commands. Added an isolated offline launcher and two boundary tests; live and business behavior unchanged. Replay baseline is reconstructed by hashes rather than guessed Git history. |

Future agents can recover those boundary facts and evidence without repeating diagnosis.
Changed boundaries may still require agent source reads. The human's role remains spec,
evidence and explicit policy approval; this record does not claim zero agent code reads.

Current policy pass: [agent source reads and consistency work](policy/20260927T010449.918426Z/code_reads.md). No human source-read claim is added. Historical entries above retain their original scope.

Current integrity pass: [agent inspection and retained controls](integrity/20260927T021057.685073Z/code_reads.md). No human implementation-read claim or historical recertification is added.

Bounded correction: [agent inspection record](correction/20260927T220352.636265Z/code_reads.md). Recovered worker: [actual source/context/change account](../submission/maintenance-recovery/20260927T220352Z/README.md).

Specification/evidence pass: [same-agent inspection and evidence improvements](specification/20260927T234809.632974Z/code_reads.md). Owner account unchanged.

Evaluator review ledger: [R-01…R-08](evaluator-reviews/20260927T003830.293495Z/reviewer-source-reads.md).

## Agent structural inspection — 2026-09-28 successor

CODE-READ-ID: AGENT-STRUCTURAL-20260928 (agent inspection, not a newly asserted human code read).
Observed failure: disposable semantic/policy/context mutations were accepted and repeated fixture hashes differed.
Why evidence was insufficient: original probe results showed the gap; implementation inspection was needed by the coding agent to replace the hard-coded predicate path and connect runtime/gates. No human source-read escalation was requested.
Source inspected: harness behavior/specification/context/requirements/authority/runtime/commands/live paths, downstream evidence interfaces, affected tests, and normalized schemas.
What was learned: prose and runtime semantics diverged; policy hashes alone lacked exact decision trace; time metadata contaminated fixture identity.
Missing harness/evidence capability: executable canonical predicates, independent runtime witnesses, reviewed assumption/index checks and bounded regression acceptance.
Harness improvement made: documented in [hardening report](derivation-integrity/20260928T011856Z/report.md), with preserved mutation receipts and generated CURRENT.
Could the same code read be avoided next time? The engineer can inspect runtime mutation and gate evidence; the coding agent still needs source inspection for implementation changes. No new firsthand claim about the owner's source-reading behavior is made.

## Later agent reads and explicit historical gaps

These are agent reads. No additional human implementation-source inspection is asserted. Retrospective entries identify their evidence limits rather than inventing a complete old tool history.

### AGENT-B9CD042-RETROSPECTIVE

CODE-READ-ID: AGENT-B9CD042-RETROSPECTIVE

Observed failure: Supplied audit reports 18 source reads around b9cd042 without a retained read log.

Why evidence was insufficient: No exact source list was found; changed-file lists cannot establish what was read.

Source inspected: UNKNOWN — exact files and read purpose cannot be reconstructed honestly from the supplied audit.

What was learned: The read ledger is incomplete for that pass.

Missing harness/evidence capability: Contemporaneous file/read-purpose inventory.

Harness improvement made: This retrospective gap is explicitly indexed; current reads are recorded below.

Could the same code read be avoided next time?: No; the missing historical account cannot be recovered by rerunning checks. New sessions can avoid this omission by recording reads as they happen.


### AGENT-POSITIVE-9450181

CODE-READ-ID: AGENT-POSITIVE-9450181

Observed failure: Lost row associations and classification/actionability coupling; inadequate authority and runtime trace evidence.

Why evidence was insufficient: Audit observations did not identify the reduction, publisher and promotion seams to repair.

Source inspected: harness/requirements.py, policy_trace.py, requirement_trace.py, context_integrity.py, authority.py, context.py, behavior_contract.py, predicates.py, trading_evaluation.py, normalized_evaluation.py, comparison_identity.py, current_evidence.py, signal_evaluation.py, baseline.py, current_snapshot.py, temporal_authority.py; rebuilt/normalization.py, normalized_classifier.py, signals.py; inherited/notice_parser.py header/extraction construction; tests/authority_fixture.py and affected integrity/policy/context/positive-path tests; submission/verify_positive_path.py.

What was learned: Source-header and model suppliers differed; row reduction and scope promotion needed explicit evidence.

Missing harness/evidence capability: Per-field supplier/normalization trace, source-to-proposal traces and temporal controls.

Harness improvement made: See [contemporaneous record](positive-path/20260928-owner-separation/source-reads.md).

Could the same code read be avoided next time?: The engineer can use retained traces; coding-agent edits may still require implementation reads.


### AGENT-SPEC-SOURCE-14ACD22

CODE-READ-ID: AGENT-SPEC-SOURCE-14ACD22

Observed failure: Writable policy duplication, missing parser field contract, Rsp Date/Time parser mismatch.

Why evidence was insufficient: Migration needed the exact rule/state inventory; malformed-date evidence did not reveal the header prefix bug.

Source inspected: Compilation/loading/context/gates/reporting/consequence modules; rebuilt normalization/classifier/publisher; inherited parser read fields; affected tests. Exact scope and saved-header diagnosis are in the linked original record.

What was learned: The header prefix consumed the wrong response-date field; compilation could replace manual view synchronization.

Missing harness/evidence capability: Parser read inventory, valid/missing/malformed probes and stable spec-row diagnostics.

Harness improvement made: See [contemporaneous record](spec-source/20260928/source-reads.md).

Could the same code read be avoided next time?: Future similar parser failures should identify the field/capture from gate evidence; implementation repair still may require source.


### AGENT-TIMEZONE-4CB4B27

CODE-READ-ID: AGENT-TIMEZONE-4CB4B27

Observed failure: Unknown-clock candidate classification conflicted with the subsequent owner ruling.

Why evidence was insufficient: Evidence showed the veto but implementing the boundary required locating rule and publisher guards.

Source inspected: harness/rule_invariants.py, real-source witness evaluator, compiler/ownership and positive-path tests; rebuilt publisher actionability guard. This reconstructs the scope stated in the historical report, not an exhaustive tool transcript.

What was learned: Classification could be separated while retaining UNKNOWN, null UTC fields and authorization refusal.

Missing harness/evidence capability: Explicit source_timezone_status and boundary observations.

Harness improvement made: See [historical timezone report](timezone-separation/20260928/report.md).

Could the same code read be avoided next time?: Boundary traces support future review; coding changes may still need source reads.


### AGENT-OWNER-REVIEW-D9ED00F

CODE-READ-ID: AGENT-OWNER-REVIEW-D9ED00F

Observed failure: Reviewer name was required inside an already reviewed exact-byte spec.

Why evidence was insufficient: Receipt behavior and source-identity exclusions were not fully exposed in the prior gate refusal.

Source inspected: harness/spec_ownership.py, runtime.py, normalized_evaluation.py, baseline.py, offline.py, current_evidence.py, consequences.py, __main__.py, commands.py; tests/authority_fixture.py, test_spec_source.py and ownership/derivation tests; Makefile and entry documents as interfaces.

What was learned: An explicit detached name assertion could bind exact reviewed bytes without changing policy.

Missing harness/evidence capability: Detached identity receipt, stale/tampered record checks, exact source/run verification.

Harness improvement made: See [owner-review report](owner-review/20260928/report.md) and tests/test_spec_owner_review.py.

Could the same code read be avoided next time?: The documented receipt now avoids that diagnostic read for an engineer; it is not authenticated ownership.


### AGENT-AUDIT-51B74CA-CORRECTION

CODE-READ-ID: AGENT-AUDIT-51B74CA-CORRECTION

Observed failure: Supplied audit reproduced inverted D1 PASS, unguarded assumptions, misleading provenance and conflicting entry documents.

Why evidence was insufficient: Reports did not reveal check binding, omitted assumption invocation, preflight short-circuiting or duplicate refusal ownership.

Source inspected: harness/rule_invariants.py, spec_compiler.py, spec_ownership.py, normalized_evaluation.py, comparison_identity.py, context.py, context_integrity.py, input_contract_checks.py, current_evidence.py, live.py, preflight.py, offline.py, commands.py, __main__.py, signal_evaluation.py, adapter.py, captures.py, baseline.py, temporal_authority.py; rebuilt/normalization.py, normalized_classifier.py, source_input.py; tests/authority_fixture.py, test_spec_source.py, test_positive_path.py, test_normalized_hardening.py, test_release_hardening.py, test_final_correction.py and related tests inspected by targeted searches.

What was learned: D checks only keyed IDs; active context omitted an existing assumption verifier; synthetic configured model inherited an environment value; wrapper wrote a second refusal.

Missing harness/evidence capability: Exact sentence/check bindings, collected preflight reasons, current run coverage and provenance, one current index.

Harness improvement made: See [audit remediation evidence](audit-remediation/20260928/report.md); current changes and tests record the improvements.

Could the same code read be avoided next time?: The new mutation receipts and structured reasons should avoid repeating diagnosis for the engineer. Agent source reads remain necessary to implement repairs.

## CODE-READ-FEEDBACK-20260928 — evidence-driven maintenance

Observed failure: supplied dfb3f77 audit reports misleading sentence/requirement PASS, hidden tradeoffs, cumbersome proposal workflow and a wrapper masking missing component refusal retention.
Why evidence was insufficient: existing reports could not distinguish a spec consequence from independent correctness, and the publisher's refusal origin was not observable without a direct probe.
Source inspected (coding agent, not a claimed human code read): harness compiler/tables, rule invariants, consequences, requirements, context, gate orchestration, reporting, capture/trading evaluation, receipt validation, command dispatch and baseline code; rebuilt normalized_classifier.py, normalization.py and signals.py; associated test fixtures and tests. No live model or original repository outside this checkout was accessed.
What was learned: status metadata dominated the spec; schemas can be losslessly generated from field tables; the initial-alert maximum was hard-coded; invalid publisher input raised before retention; generated policy drift and a stale human review are distinct from proposal measurement.
Missing harness/evidence capability: an adoption-free consequence preview with labeled tradeoffs, exact declaration changes and a direct component refusal/reopen probe.
Harness improvement made: fixed-format compact spec tables, executable maximum parameter, explicit PARTIAL/UNCHECKED scope, read-only proposal reports, source-example coverage, visible inherited/rebuilt tradeoffs, a direct refusal retention control and a short context index.
Could the same code read be avoided next time? The human can inspect the spec and new evidence. Coding-agent reads remain allowed; arbitrary future business semantics cannot be inferred. No zero-source-read or independent-evaluation claim is made. The fresh-session record lists its own reads separately.

## Supplied audits as code-read escalations by proxy

CODE-READ-ID: AUDIT-PROXY-51b74ca
Observed failure: supplied audit drove the audit-remediation pass.
Why evidence was insufficient: author-reported results did not expose all contract/refusal and source-identity gaps.
Source inspected: the reviewer-reported paths in [the retained supplied audit](audit-remediation/20260928/supplied-audit.txt); this ledger does not invent an exhaustive read list.
What was learned: evidence claims needed direct source and mutation verification.
Missing harness/evidence capability: self-reporting did not make its omissions evident.
Harness improvement made: the dated audit-remediation report records the bounded repairs; later audits show they were insufficient.
Could the same code read be avoided next time? Only for the specific reproduced controls; complete avoidance is not established.

CODE-READ-ID: AUDIT-PROXY-dfb3f77
Observed failure: [the supplied audit](spec-feedback/20260928/supplied-audit.txt) found reporting, ownership and maintained-scope gaps.
Why evidence was insufficient: raw receipts and passing synthetic coverage obscured source-case failures and proposal tradeoffs.
Source inspected: reviewer-reported harness/component paths in that audit, not a claim of owner firsthand inspection.
What was learned: declaration and consequence evidence were missing; author-written checks did not independently validate the grader.
Missing harness/evidence capability: truthful per-case coverage and zero-reach declaration evidence.
Harness improvement made: proposal reporting and source-case coverage; the 427c7d7 audit subsequently found false inherited scores and exit/drift defects.
Could the same code read be avoided next time? The added controls cover reproduced defects, but independent checker review remains necessary.

CODE-READ-ID: AUDIT-PROXY-427c7d7
Observed failure: [the supplied audit](audit-truth/20260928/supplied-audit.txt) reproduces successful refusal exits, gate-side file writes, credited MODEL_FAILUREs and unobserved checks reported PASS.
Why evidence was insufficient: headline results were generated by the same incorrect scoring/exit paths they purported to validate.
Source inspected: reviewer reports harness/ inspection and no direct rebuilt/ read; its separate fresh agent reported component reads. Do not merge those into a fictional owner read or verified exhaustive list.
What was learned: executable mutations and direct component probes are needed in addition to report assertions.
Missing harness/evidence capability: read-only gate proof, execution-aware scoring, declared-check coverage accounting, explicit code-owned versus prose scope.
Harness improvement made: these controls are now exercised by test_audit_truth.py and the retained audit-truth pass; the fresh-session source-read record separately accounts for component maintenance.
Could the same code read be avoided next time? The specific defects are visible in regression evidence. This does not prove all future grader/source inspection unnecessary.

CODE-READ-ID: AGENT-AUDIT-TRUTH-20260928
Observed failure: current supplied audit findings required implementation repair.
Why evidence was insufficient: source inspection was needed to locate the exit override, implicit build, raw signal scoring and duplicated scope inventories.
Source inspected: normalized_evaluation, spec_compiler/tables/ownership, contract_preflight, proposals/consequences, trading_evaluation, current_evidence, context/manifest, offline/commands, behavior_contract, rule_invariants, signal_evaluation, baseline/comparison_identity, live/preflight, gates, normalized_classifier and normalization; affected tests and documentation.
What was learned: the gate's successful-looking status could coexist with skipped declared checks, while an old assumption ceiling blocked unrelated maintenance.
Missing harness/evidence capability: the audit controls listed above and a maintained-component exercise without grader edits.
Harness improvement made: deterministic regressions, explicit scope/limits and corrected generated evidence. No business policy or human review was inferred.
Could the same code read be avoided next time? A human can inspect these reproduced failures through the receipts; coding-agent reads remain necessary for repairs.

CODE-READ-ID: AGENT-QUANTITY-PROPOSAL-20260928
Observed failure: unsupported numeric restriction omitted from normalized quantities without a row-specific explanation; 150 Dth and 2.5 MMcf/d witnesses retained.
Why evidence was insufficient: raw retained rows did not show exactly which mapping lost the numeric quantity; direct unittest was first blocked by stale review rather than reaching the witness.
Source inspected: fresh worker read rebuilt/normalization.py, rebuilt/source_input.py, tests/test_positive_path.py and harness/offline.py; exact searches and outputs are retained in [the fresh-session record](audit-truth/20260928/fresh-maintenance/record.md). These are coding-agent reads, not an asserted owner firsthand read or independent evaluation.
What was learned: raw values already survive; the missing behavior is an explicit row-specific omission trace. No volume conversion or new quantity meaning is justified.
Missing harness/evidence capability: a usable omission explanation plus documented offline observation testing; the separate OBS-003 coverage binding was also incomplete.
Harness improvement made: the parent repaired OBS-003 coverage. The component patch and focused tests are prepared but unapplied because automatic approval review rejected that write. All 225 parent-guarded files remained unchanged during the worker exercise.
Could the same code read be avoided next time? The concrete witnesses and patch expose this omission to the engineer. Repair and validation remain pending, so avoidance is not demonstrated.

CODE-READ-ID: AGENT-NNS-FIRM-20260928
Observed failure: a maintenance request posed by the candidate (no desk exists; NNS-FIRM-001 calls it a "desk request", corrected in AUDIT4-001), not a gate failure. Extracted NGPL rows with service_type NO_NOTICE normalized to UNKNOWN (visible in capture-1/46528 normalization_trace), so a firm No-Notice Service restriction could never satisfy the FIRM_DISRUPTION predicate.
Why evidence was insufficient: the evidence showed NO_NOTICE -> UNKNOWN but not whether the spec services map is the only path, i.e. whether a spec-only change (new normalized value plus FIRM_SERVICES membership) would work without component code.
Source inspected: coding-agent reads of rebuilt/normalization.py lines 1-60, one search of harness/consequences.py (out of scope) (services come from spec-settings normalization.services, defaulting to UNKNOWN), grep of service handling in rebuilt/source_input.py, rule_engine.py and classifier.py, and rebuilt/normalized_classifier.py (CLI and classify). tests/test_spec_predicates.py was read after make check failed. No component source was changed.
What was learned: service vocabulary, FIRM_SERVICES and the interface enums are all spec-owned, so the change is spec-only (NNS-FIRM-001; proposed by the session, later approved by the owner, and covered by the owner's reread). tests/test_spec_predicates.py::test_a_set_edit_in_the_spec_changes_behavior_without_code pins the literal spec text '"FIRM_SERVICES": ["PRIMARY_FIRM", "SECONDARY_FIRM"]' as a fixture, so any legitimate edit of that set fails make check.
Missing harness/evidence capability: (1) no captured or labeled NNS outage, so the intended positive effect is invisible to make consequences (0/46 changes); the effect was shown only by a scratch metamorphic probe (firm-positive witness with service swapped to NO_NOTICE_FIRM: old spec refuses, new spec BR-FIRM; PARTIAL and INTERRUPTIBLE controls stay BR-UNRESOLVED). (2) the spec-predicate test should derive its fixture from the compiled set rather than from literal spec bytes.
Harness improvement made: none by the fresh session. Afterwards, the coordinating session fixed the brittle fixture in `tests/test_spec_predicates.py` in the same commit that adopted the NNS policy. That bundled an evaluator change with a policy change; it should have been a separate, separately approved commit.
Could the same code read be avoided next time? Yes, if context packages stated that service mapping and FIRM_SERVICES are spec-owned with no code path, and if an NNS witness existed.

CODE-READ-ID: AGENT-AUDIT4-WITHIN-6F8F35E
Observed failure: fourth audit #6. `within SET` was true for an empty list, so History COMPLETE (`history.statuses within LINKED_STATUSES`) could hold with no linked statuses at all. The finding was supplied by the audit; no gate had failed.
Why evidence was insufficient: the spec did not say what `within` means on an empty list, and no witness or captured case has an empty status list, so neither the gate nor CURRENT.md could show the vacuous truth.
Source inspected: the coordinating agent (not a fresh session) read only the `within` branches, via `grep -n '"within"' harness/domain_rules.py rebuilt/rule_engine.py`, then changed one line in each file by exact-string replacement. Files edited in commit `6f8f35e`: `harness/domain_rules.py` (oracle), `rebuilt/rule_engine.py` (component), `spec.md` (operator text), `tests/test_spec_predicates.py`. The same agent wrote `rebuilt/rule_engine.py` earlier in this session, so it knew the rest of the file without reopening it; that prior authorship is the real source knowledge behind the edit. The same commit also changed `harness/spec_ownership.py`, `harness/spec_compiler.py`, `harness/contract_preflight.py`, `harness/normalized_evaluation.py`, `harness/current_evidence.py` and `tests/test_spec_source.py` for audit #3 and #2, with no source read beyond the functions edited.
What was learned: both evaluators used `all(...)`/subset semantics, which are true on an empty list. Nothing in the captures reaches that case: Gate 3 on the next run reported 0 changed decisions of 91.
Missing harness/evidence capability: (1) the operator meaning was not in the spec, so there was nothing to derive a check from; (2) no empty-list witness for History; (3) the harness has no rule that a component change and an oracle change go in separate commits. Here both changed in one commit, so the oracle was not held fixed while the component changed: agreement between them after the commit is not independent evidence.
Harness improvement made: the spec now states the meaning of `overlaps` and `within` (decision AUDIT4-001, proposed at the time and approved in `61d4052`), and `test_an_empty_list_is_never_within_a_set` checks both evaluators against that text. The commit was not split: five later commits touch the same files, and splitting it means rewriting that unpushed history, which the owner has not asked for. Gate 3 names both files under `changed_files`, so the owner sees them before registering a reference.
Could the same code read be avoided next time? Partly. With the operator meaning in the spec and a test on it, a future change to it is visible without reading source. AGENTS.md now states that rule (trimmed to the current workflow in `e3b9f02`); no check enforces it.

CODE-READ-ID: AGENT-NNS-A8F1AB8D
Observed failure: none; this is a writer/evaluator breach found by the fourth audit. Subagent `agent-a8f1ab8d` of the build session `2edc1739` ran 15:00:51–15:12:47Z on 2026-09-28 in a scratch clone (`scratchpad/fresh`), as the first attempt at a "fresh" maintenance session. The request was the NNS change, then worded as service_type `NO_NOTICE_FIRM`.
Why evidence was insufficient: predicate meaning (what FIRM_DISRUPTION is) lived in `harness/domain_rules.py`, so the session could not make the change from spec.md.
Source inspected: from the transcript (`evidence/code-read-ledger/`): read `harness/behavior_contract.py`, `consequences.py`, `context.py`, `domain_rules.py`, `offline.py`, `proposals.py`, `rule_invariants.py`, `spec_compiler.py`, `spec_tables.py`, `inherited/llm_utils.py`, `inherited/notice_parser.py`, `rebuilt/normalization.py`, `tests/test_positive_path.py`, plus globs over `harness/*.py` and `rebuilt/*.py`; imported `harness.spec_ownership`, `harness.runtime` and `rebuilt` modules in probes. **Edited the oracle**: `harness/domain_rules.py` (the hard-coded firm-service set) and `harness/spec_compiler.py` (a legacy default for `firm_services`); edited spec.md; created `tests/test_no_notice_firm.py` and `evidence/nns-firm/20260928/record.md`.
What was learned: a maintenance session asked to change behavior changed the evaluator that judges the behavior. Nothing stopped it: the context package's source scope was advice, and the gate compared the component with an oracle the session had just edited.
Missing harness/evidence capability: predicate meaning in the spec; a refusal (or at least a named report) when an evaluator file changes alongside the component.
Harness improvement made: its edits stayed in the scratch clone and were never merged. The coordinating session then moved predicate meaning into the `spec-predicates` table (REMEDIATION-001), and Gate 3 now reports any edit under `harness/` or `tests/` as EVALUATOR_OR_ORACLE_CHANGED, naming the files, until an owner registers a new reference. This entry was missing until the fourth audit found the breach in the transcript; the earlier record mentioned only this session's reads.
Could the same code read be avoided next time? The read, yes: the second NNS session needed no oracle read. The edit is now visible but not prevented; a session can still edit harness files, and only Gate 3 and code-owner review expose it.

CODE-READ-ID: AGENT-UNNAMED-EDITS-20260928
Observed failure: fourth audit #10. Earlier entries did not name three harness files the build session edited: `harness/credential_guard.py` and `harness/capture_registration.py` (created in `a6628e4`, the live-path work) and `harness/spec_tables.py` (edited in `c260405`, third-audit fixes). Nor did they record the second and third audits (sessions 7f5d703d and a612115b), which read `harness/` and `inherited/` files and mutated `rebuilt/rule_engine.py` and `harness/trading_evaluation.py` in scratch copies to test the gate.
Why evidence was insufficient: the entries were written from memory at commit time, so they listed what seemed important, not what happened.
Source inspected: the files named, by the build session 2edc1739 (its main thread); the audits' reads are listed per transcript in the ledger.
What was learned: a hand-written code-read log drifts from the transcripts within a day.
Missing harness/evidence capability: a generated ledger.
Harness improvement made: `code-read-ledger/generate.py` and its output. Entries in this file are now explanations of reads the ledger lists, not the record itself.
Could the same code read be avoided next time? Not the reads; they were edits. The omission can be avoided by regenerating the ledger before each submission.

CODE-READ-ID: AGENT-AUDIT4-ROUND2-20260928
Observed failure: fourth-audit items #5 (date probe), #14 (provider failure classes) and #30/#7 (deletion list), worked by the build session 2edc1739.
Why evidence was insufficient: #5 and #14 name behavior the evidence could not show (a 12-hour format reading the wrong instant; a billing 400 reported as a generic failure). The deletion list needed to know what each module is wired into, which only imports and file-open traces show.
Source inspected: `harness/input_contract_checks.py`, `rebuilt/source_input.py` (timestamp), `rebuilt/rule_engine.py` and `harness/domain_rules.py` (naive end parsing), `harness/live.py`, `harness/adapter.py`, `harness/preflight.py`, `harness/spec_compiler.py`, `harness/spec_tables.py`, `harness/rule_invariants.py`, `harness/trading_evaluation.py`, `harness/normalized_evaluation.py`, `harness/current_evidence.py`, `harness/context_integrity.py`, `harness/storage_evaluation.py`, `harness/spec_ownership.py`, and the tests each change touched. The ledger lists every call.
What was learned: the naive values the date formats produce are discarded by the component, so a %I→%H edit was latent. `verify_assumptions` has no caller outside tests. `storage_evaluation.py` serves only out-of-scope requirements. And the loosening and owners guards failed open whenever the current compiler could not compile the reviewed spec.
Missing harness/evidence capability: a mutation-probe run per deletion (now in the proposal); a guard that reads the reviewed settings without compiling them.
Harness improvement made: `46a1d32` (#5), `3dcc801` (#14), `8381144` (the fail-open guard), and `context/proposals/deletion-list.md`.
Could the same code read be avoided next time? For the deletion list, partly: the open-trace and the probe runner are reproducible and described in the proposal. For the fixes, no; they were repairs.

CODE-READ-ID: AUDIT5-20260928
Observed failure: a fifth audit of `3aaba89`, run by a separate Claude Code session and its subagents in scratch clones. It reproduced README's commands and mutated spec.md. It did not open anything under `rebuilt/`.
Why evidence was insufficient: CURRENT.md and the gate output did not say how the offline gate resolves `LLM_MODEL`, whether a gate code is emitted anywhere but the report, or what reads the assumptions table.
Source inspected: `harness/comparison_identity.py` and `harness/credential_guard.py` (grep for `LLM_MODEL`), `inherited/llm_utils.py` (default model line), `harness/normalized_evaluation.py` (`source_identity`), `harness/context.py` (artifact list), and, in scratch, `harness/context_integrity.py`, `spec_ownership.py`, `rule_invariants.py`, `spec_compiler.py`, `contract_preflight.py`, `consequences.py`, `current_evidence.py`, plus `tests/test_spec_source.py`, `test_normalized_hardening.py` and `test_audit_controls.py` (parts). A fresh-session subagent on HEAD read `classifier.py`, `rebuilt/source_input.py` and `rebuilt/normalization.py`.
What was learned: the gate emits the codes harness.md cites, but no test holds INPUT_DATE_FORMAT_MISMATCH, ROUTINE_ADMIN_SIGNALED or the Gate 2 budget codes. The assumptions table has no consumer outside `make context`. The package does not say that notice IDs are integers from parser to output.
Missing harness/evidence capability: negative-control tests per gate code; a consumer or an unreviewed-spec warning for the assumptions table; input-type facts in the context package.
Harness improvement made: none; documentation corrections only (`context/proposals/audit5-fix-list.md`).
Could the same code read be avoided next time? The model-resolution and assumptions reads, yes, if harness.md stated both. The fresh session's reads, yes, if the package stated identifier types.

CODE-READ-ID: AUDIT5-TIER1-CONSEQUENCES-20260928
Observed failure: fifth audit #3. `make consequences` reported BR-HISTORY wins 7 and BR-UNCHANGED wins 6, while the gate executed 9 and 4. The disagreement was on capture-2 `unchanged-revision` and `repeated-revision`: consequences showed BR-UNCHANGED, the gate BR-HISTORY.
Why evidence was insufficient: both reports showed the two outcomes but not why the histories differed. Neither states which earlier versions of a notice the publisher keeps as history.
Source inspected: `harness/consequences.py` (lines 1–158), `harness/captures.py` (all), `harness/trading_evaluation.py` (55–194, 419–427), and `rebuilt/signals.py` (a grep for definitions, then 30–69 and 123–230). The signals.py read found the rule: a notice enters history only when its classification is not UNRESOLVED and `SemanticEvidence.refusal()` is None. In capture-2 the latest 46624 before the revisions is `restart-replay`, whose impact verdict failed, so the gate's history had a gap.
What was learned: the publisher's history-retention rule lives only in component code; spec.md does not state it.
Missing harness/evidence capability: a check that the preview and the gate agree (now `test_consequences_match_the_rules_the_gate_executes`); the retention rule stated in spec.md so it can be derived instead of mirrored.
Harness improvement made: `3fb95fa`, where consequences mirrors the rule by reusing the gate's `semantic_evidence`, plus the parity test. It is an evaluator change, so Gate 3 reports EVALUATOR_OR_ORACLE_CHANGED until the owner registers a new reference.
Could the same code read be avoided next time? Yes, if spec.md stated which decisions enter history. That is a spec proposal for the owner.

CODE-READ-ID: AUDIT5-TIER1-CRASH-20260928
Observed failure: fifth audit #11. Changing INPUT-SOURCE-022 from `integer` to `text` made `gate --proposal` exit 5 with `SPECIFICATION_INTEGRITY_ERROR "KeyError: 'candidate_classification'"`, and CURRENT.md named no spec row.
Why evidence was insufficient: the crash was reduced to a key name; the gate retained neither a traceback nor the refused input.
Source inspected: `harness/normalized_evaluation.py` (800–840, the catch-all that labels any exception SPECIFICATION_INTEGRITY_ERROR), `harness/signal_evaluation.py` (120–160, 250–280, 292–336, 445–470), `harness/current_evidence.py` (295–312), and `rebuilt/signals.py` (84–122, the input-refusal record, which has no `candidate_classification`).
What was learned: the component's refusal already names the row (`spec.md:447: block spec-inputs, row INPUT-SOURCE-022`); the harness dropped it. The catch-all still turns any unexpected harness exception into a spec-integrity refusal.
Missing harness/evidence capability: a stated output shape for refusals, and a traceback kept for harness exceptions.
Harness improvement made: the replay observer reads the key tolerantly and attaches `refused_by` to failing findings; test `test_an_input_refusal_in_the_replay_is_a_finding_not_a_crash`. It is an evaluator change.
Could the same code read be avoided next time? Yes, if the catch-all kept a traceback under evidence and labeled it HARNESS_EXCEPTION instead of SPECIFICATION_INTEGRITY_ERROR. That is a further Tier 1 item.

CODE-READ-ID: AUDIT5-TIER1-GATE-CODES-20260928
Observed failure: fifth audit #32. harness.md cited INPUT_DATE_FORMAT_MISMATCH, ROUTINE_ADMIN_SIGNALED, LABELED_MISSED_POSITIVES and LABELED_FALSE_POSITIVES as catches, and MODEL_CONFIG_CHANGED as the model-change signal, but no test raised any of them.
Why evidence was insufficient: to write a test that raises a code, you need to know where it is emitted and from what input. No evidence file says that.
Source inspected: `harness/input_contract_checks.py` (48–60, 140–228), `harness/trading_evaluation.py` (268–292, 379–420), `harness/normalized_evaluation.py` (690–720), and the import lines of `rebuilt/signals.py` (to patch `classify` where the publisher calls it). No component logic was read.
What was learned: the budget comparison is a pure function; the routine code is emitted only from the trading loop, so testing it needs the publisher's classifier patched.
Missing harness/evidence capability: a registry mapping each gate code to its emitter and a triggering mutation, generated rather than hand-kept.
Harness improvement made: `tests/test_gate_codes.py` (`fd98aef`). Each test was mutation-checked: breaking its emitter makes it fail.
Could the same code read be avoided next time? Yes, with that registry.

