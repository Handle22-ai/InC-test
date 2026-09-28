# Positions held, changed and dropped (2026-09-28 remediation)

An audit of commit `8ea74f8` found 36 problems. This page records what changed in
response, what did not and why, and what now waits on the owner.

## Held, with the evidence that held them

| Position | Evidence |
|---|---|
| Output stays a candidate; `recommendation_allowed` is always false | No consumer receives review items or alerts. Authorizing recommendations with no delivery path would be a claim without evidence. |
| No timezone is inferred for NGPL times (TZ-NGPL-001 stays rejected) | REMEDIATION-002 decides "ended" only when it holds under every UTC offset, so it needs no zone. |
| No critical-header rule | `is_critical = 1` on all 14 labeled notices, so the header cannot separate signals from non-signals (spec A-009). |
| No geography rule yet | One labeled notice (46624) is in the Louisiana Zone. A Henry Hub/LNG priority cannot be measured until the desk labels geography cases. |
| Frozen labels and witnesses change only with the owner | The agent was blocked from re-freezing `unusable-impact` and waited. The owner approved REMEDIATION-001; the re-freeze names them. |

## Changed

| Was | Now | Why |
|---|---|---|
| What FIRM_DISRUPTION means lived in `harness/domain_rules.py` | The `spec-predicates` table in spec.md | Every fresh session had to read harness code to change "what is firm" (audit #23) |
| The rebuilt component imported the harness, so the gate checked the harness against itself | `rebuilt/` imports nothing from `harness/`; a test enforces it | Agreement checks were circular (#22) |
| A failed impact helper vetoed every decision | It vetoes only non-firm notices; such decisions are neither stored nor published | 46864, the only notice typed FORCE MAJEURE, was lost to a helper no rule reads (REMEDIATION-001, approved) |
| Gate could never exit 0: 12 rows permanently UNKNOWN | Six unobservable rows are declared out of scope and listed; five gained observers; Gate 2 judges acceptance budgets | A gate that cannot pass cannot discriminate (#13; REMEDIATION-003, approved) |
| Gate 3 NONCOMPARABLE on any spec change | Changed decisions must match the spec's derivation; harness or oracle edits are named and block | Spec changes are when regression evidence matters (#8, #15) |
| Unzoned restrictions could never end | ENDED once past under every offset; labels scored as of posting | Expired restrictions stayed candidates live (#29; REMEDIATION-002, approved) |
| Ambiguous date formats passed silently | Refused as INPUT_DATE_FORMAT_AMBIGUOUS | #18 |

## Dropped

- Nine legacy modules and their Make targets (demo, policy, review, storage integration and others). No current workflow used them.
- The claim that the early 09-26 maintenance runs were fresh sessions: they ran in the thread that wrote the component.
- "Deferred" as a check state. A row is either in scope, observed and gated, or declared out of scope.

## Owner steps (done 2026-09-28)

1. Reread of spec `4448a6f9…` recorded; it covers FEEDBACK-001, AUDIT-TRUTH-001, REMEDIATION-001 to -003 and NNS-FIRM-001.
2. The reviewed run of the publication root commit is registered as the Gate 3 reference (`evidence/reference-20260928`).
3. Build-history evidence is archived (`evidence/ARCHIVE.md`).

`make gate` now exits 0 with all three gates PASS. Gate 3 PASS here means nothing has changed since the reference; the next change is its first real test.

Still open: an NNS-unavailable witness and labeled geography cases from the desk (spec A-009).

## Second audit (2026-09-28): what changed, what is held

Fixed with evidence:
- **#4, missing-prior leak.** Each captured case now sees only the store it was captured with; `missing-prior` is refused as a history gap (BR-HISTORY reach 4 → 6), and a test holds it.
- **Control plane.** A dirty tree is never accepted. A crash inside the component is exit 4. A model set in `inherited/.env` is unverifiable. `consequences` exits 4 on a proposal the compiler would refuse and flags unmeasured edits. A hand-edited predicate names its row. There is now a CI gate and a CODEOWNERS file.
- **Documents.** Every A-finding is corrected, and pending learning from both fresh sessions is retained.

Held, with reasons:
- **#1 / #31, approval.** Correct: the receipt is not authentication, and a local mechanism cannot stop an agent that holds the owner's credentials. The answer is branch protection with required CI and code-owner review (README), and ultimately a second reviewer. It is stated as the first limit in harness.md, not defended as sufficient.
- **#28, the budget equals today's misses.** It is a ratchet the owner approved, not a desk tolerance. The desk must set the real miss tolerance and a review capacity; until then, Gate 2's budget can only detect a regression.
- **#21, unpublished history.** A deliberate choice to publish one commit. The full history and raw transcripts are kept in a bundle and are available on request; the evidence says so and marks every cited commit as pre-publication.
- **#29 / #30, scope.** `rebuilt/` holds a parser, normalizer, engine, publisher and store. The classifier boundary is the maintained component; the publisher and store are the downstream seam the replay tests exercise. The maintenance exercise was deliberately spec-only, which is what the spec-predicates change was meant to make possible.
- **#33 / #34, completeness-only checks.** Upstream extraction checks re-check frozen captures, and Gate 3 had not failed alone. Gate 3's distinct value is now naming harness and oracle edits (EVALUATOR_OR_ORACLE_CHANGED); the extraction rows are reported, not relied on.

## Third audit (2026-09-28)

Fixed, with tests:
- **#1 / #17, reference registration.** `harness register-reference RUN DEST --person OWNER` replaces the undocumented baseline command. It refuses non-owners, records the person and the evaluator/oracle files they accepted, and CURRENT.md shows both. A reference with no owner stops Gate 3 from passing but never hides a regression. Earlier commit messages that said "reviewed run" meant the gate ran in reviewed-spec mode. They are pushed and stay as written; from now on such commits say "observed".
- **#2, reviewer identity.** `spec-settings.owners` lists who may reread or register; anyone else is refused, and CURRENT.md names the reviewer and the decisions covered. The owners list is taken from the spec last reread, so an edit cannot add its own reviewer (tested).
- **#3 / #4, circular or partial guards.** New code-owned boundaries: `required_inputs` (identity, status and body stay ERROR when missing) and `refusals_first` (any row refusing on a safety condition precedes every deciding row). Both are keyed on conditions and actions, not rule names.
- **#5 / #9, consequences.** It now runs the frozen classifier witnesses, so the auditor's routine mutation exits 4. Author-supplied `--inputs` no longer clear UNMEASURED.
- **#6, #15, #16, report.** Every non-passing finding is listed with requirement and case; coverage shows status per evidence kind; results.json carries its run ID.
- **#8, baseline.** `make consequences` defaults to the spec you last reread.
- **#10, #24, spec.** D6's binding to the annotation oracle is declared, and what the normalizer decides is stated.
- **#14, #30, context.** The manifest is pruned to paths that exist (a test holds this), and the package now carries known failures, decisions and assumptions.

Held, or waiting on you:
- **#7, review-rate budget.** Needs a number from you or the desk. Setting it to today's 4/7 would repeat #25's problem.
- **#20, agent attribution.** Every commit is authored as the owner because the owner asked to remove the Claude co-author line. The honest middle ground is a non-contributor trailer such as `Assisted-by: coding agent`. That is the owner's call.
- **#25–#32 (C).** The budget is still today's measured misses; the brief's factors are still not rules (no labels to measure them); branch protection is not yet evidenced; out-of-scope memory requirements stay out of scope. Each is stated in harness.md "Limits" or above.

## After the third audit

- **Live path, now exercised.** `make preflight` (2 calls) and `make evaluate-inherited` (38 calls, `claude-sonnet-4-6`) ran with the owner's key. The full run had no harness failure. It reproduced the missing-verdict defect on 46528 live, and it did not reproduce the 46725 false positive, so that false positive depends on the run. It is registered as capture-2, and the report lists every notice where captures disagree.
- **Owners.** The owners list now comes from the last reread spec, so an edit cannot add its own reviewer.
