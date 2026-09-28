# Fresh-session maintenance — blocked repair proposal

Status: **BLOCKED BY AUTOMATIC APPROVAL REVIEW; component maintenance is not complete.** This is author-side verification, not independent evaluation. The proposed repair was never applied or executed. No human review, acceptance, materiality decision, recommendation authorization, delivery or live model call is claimed.

## Starting request and recovered context

Starting request: A numeric source restriction can disappear from normalized quantities when its vocabulary is unsupported. Make that loss explicit in retained normalization evidence, including the original value and unit. Do not infer volume conversion, classification, materiality or authorization.

The worker started with no prior chat history. The parent supplied the repository/worktree and Python locations, task scope, no-live rule, read-only policy/grader boundary and evidence destination. The worktree remained at `667df760870ccd9bad4409f314d3abfb1aca9e0d` throughout.

Automatically selected context: `harness.commands context` for `recommendation-classification-maintenance`, retained in [context/package.md](context/package.md) and package.json. It selected `classifier.py`, `rebuilt/normalized_classifier.py`, `rebuilt/normalization.py`, and `rebuilt/source_input.py`, the full requirement-row package, spec rule block and five pending-learning records marked unapproved. The task narrowed the actual component scope to normalization and focused proposed tests.

Requirements loaded: the package includes 20 binding and 8 specified-only requirements. Task-relevant rows are OUTPUT-002 (quantity meaning/units), OUTPUT-004 (annotated quantities; this task adds no annotation), SAFETY-002 (explicit unsupported evidence), OBS-001 (provenance), OBS-003 (regression evidence), D6-006/D6-007 (preserve stated values/units; no unsupported conversion), INPUT-SOURCE-038/039 (raw numeric value/unit), IF-INPUT-094 through IF-INPUT-100 (normalization evidence), and the finite normalization maps. No requirement or threshold was changed.

Decisions and assumptions loaded: the spec's current D6 and assumptions A-006/A-008 are controlling. ADR 010, `context/decisions/010-integrated-release-hardening.md`, was read as historical technical context for canonical mappings, preserved evidence and no label/score input. Current spec-source context explicitly states that historical ADRs are not competing active policy. No pending learning was treated as approval.

Known failures loaded: `context/failures/spec-evidence-current.md`, `context/pending-learning/integrated-captured-boundary.md`, the selected pending-learning inventory and current evidence. These explain extraction association limits, unresolved source time/history and the difference between observations and acceptance. They do not prescribe a new numeric quantity mapping.

Source scope read: `rebuilt/normalization.py`, `rebuilt/source_input.py`, `tests/test_positive_path.py`, and the offline command wrapper `harness/offline.py` after direct unittest correctly refused stale review. Source searches are retained in commands.jsonl. No human source read occurred. The agent used source inspection to locate the mapping omission, not to redefine expected behavior.

Context sufficiency: README, spec, CURRENT and the generated task package were sufficient to identify the correct component, existing trace contract, observation-only commands and no-conversion boundary without an implementation walkthrough. The context did not resolve the user-authorization conflict detected by automatic review. The parent later specified concrete `150 Dth` and `2.5 MMcf/d` witness values and pointed out an existing OBS-003 reporting discrepancy. These did not change requirements.

Additional human explanation required: approval of the specific proposed component edit is now required because automatic approval review rejected it as conflicting with the user's audit-only instruction. Parent instructed no retry or workaround and will ask the user about the concrete proposal.

## Finding and concrete proposed repair

[Failure record](failure.json) and [raw synthetic witnesses](witnesses-before.stdout.txt) show that unsupported numeric restriction types produce an empty facts.quantities list. Their raw source values and units are already retained in source.fields.retained_extraction and the aggregate trace. The defect is the absence of an explicit numeric omission reason and row-specific mapping evidence, not total destruction of the raw data.

[Proposed component diff](proposed-normalization.patch), **not applied**, would:

- Retain each unmapped non-null numeric restriction's row index, raw restriction type, value and unit.
- Add a row-specific gap identifying omission from facts.quantities.
- Add a normalization_trace entry with the raw values, normalized_value null, source/body reference, normalizer supplier and explicit no-conversion handling.
- Leave supported quantity mappings and nonnumeric categorical rows unchanged. Zero is retained as a numeric value. Missing units/types remain null; no unit is invented.

[Proposed focused tests](test_normalization_evidence.py) and [integration diff](proposed-tests.patch) remain under evidence, outside the active tests directory. They cover unsupported percent/volume/flow vocabularies, `150 Dth`, `2.5 MMcf/d`, zero, absent unit/type, multiple identical unmapped rows alongside a supported row, supported hourly quantities above 100, categorical unavailability and caller-input nonmutation. They add no labels or evaluation requirements.

Expected effect is limited to explicit evidence of omitted source quantities. Correctness of the proposed patch remains unverified because it was not applied. No changed classification, materiality or authorization is claimed.

## Commands and results

Exact argument vectors and complete stdout/stderr for recorded commands are in [commands.jsonl](commands.jsonl). [starting-context.md](starting-context.md) records bootstrap commands, direct file-creation/move events and the rejected mutation. The tools' full initial transcript was not exported; initial broad-read display truncation is documented, and task-relevant rows were reread through the recorder.

| Check | Result |
|---|---|
| Before ordinary offline gate | exit 5, PREFLIGHT_REFUSED, UNRECORDED_SPEC_CHANGE; no acceptance |
| Before explicit proposal gate | exit 3, Gate 1 UNKNOWN, Gate 2 UNKNOWN, Gate 3 PASS |
| First direct unittest attempt | exit 1, stale-review errors; not evidence of the quantity defect |
| Focused tests through existing offline observation wrapper | Failures demonstrate missing omission trace; categorical/supported control passes |
| Final unintegrated focused proposal tests | exit 1; 3 test methods, 7 failure records including six parameter cases and the mixed-row test |
| Repository `make check` with supplied Python | exit 0; 91 files formatting/lint/type checks pass, 205 existing tests pass |
| After-session ordinary gate, unchanged component | exit 5, same pending review refusal |
| After-session proposal gate, unchanged component | exit 3, Gate 1 UNKNOWN, Gate 2 UNKNOWN, Gate 3 PASS |

No setup was needed: the supplied pinned environment was usable. No compile command was run because this task forbade generated requirements/build changes and the component repair was blocked. The existing gate verified artifacts without regenerating them.

Regression result: all 68 compared cases are unchanged, including the 46 captured observations. No newly passing, newly failing, missing or unexpected case differences; no affected requirement IDs in Gate 3. Direct before/after case dictionaries and trading metrics are equal. This verifies unchanged existing behavior; it is **not** a repaired-component regression result. Gate 3 uses the pre-existing registered observation reference and claims no approval of UNKNOWN outcomes.

Existing reporting discrepancy: both proposal runs report Gate 3 PASS while OBS-003 coverage remains UNKNOWN with zero observations/DECLARED_CHECK_UNOBSERVED. This discrepancy was independently visible in coverage.md and results.json after the parent flagged it. The worker did not change the grader; the parent owns the separate correction.

## Files changed and preservation

Only this untracked evidence directory was retained. The temporary new test file under tests/ was moved into evidence before final verification. No tracked file changed. [Preservation hashes](preservation.json) verify all 16,125 tracked files unchanged, including 212 selected policy/grader/context/instruction/build files; the broader all-tracked check also covers all other guarded files. The component SHA-256 is unchanged: `14ccfbd69be7743fc83299c6d277fe11dbd660ed2190c7d70e43a570bc357232`.

No commit was made. No other checkout was edited. Existing parent evidence directories remain unmodified by this worker. There was no live access or new human review receipt.

## New learning retained for the next session

1. An unsupported numeric restriction can survive in raw evidence while disappearing silently from normalized quantities; inspect explicit mapping evidence as well as retained raw rows.
2. Unsupported vocabulary must not be converted to an invented canonical quantity or unit. Preserve zero, absent units and row identity separately from mapping success.
3. The existing offline test command runs in proposal scope. Direct unittest uses normal review enforcement and can refuse before reaching component behavior; that refusal is not a defect demonstration.
4. Gate 3 PASS and requirement coverage must be inspected together while the existing OBS-003 binding discrepancy remains unresolved.
5. This repair proposal is reviewable but blocked. The next session must obtain the specific user authorization, then apply and validate the patch and focused tests against the same unchanged policies and labels. A new ordinary human spec review must not be fabricated as part of that work.

Knowledge remains in this record, failure.json, exact proposed diffs, concrete tests/witnesses, command outputs and before/after manifests. It was not automatically promoted into the read-only context index or policy.

## Approval refusal

Automatic approval review rejected the attempted edit to rebuilt/normalization.py: “This directly modifies rebuilt/normalization.py and changes generated normalization gaps and traces, conflicting with the user’s explicit instruction not to change generated behavior while recording the review.” The tool instructed no bypass. [Exact retained refusal](approval-rejection.json). No retry, indirect application or completed maintenance claim followed.
