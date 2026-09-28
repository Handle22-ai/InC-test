# What the engineer looks at instead of code

Two documents: **spec.md**, which they own, and **CURRENT.md** of the latest gate run, which they read. The code between them is the agents' job. This file explains why that division can be trusted, and where it cannot yet.

## How checks come out of the spec

`make compile` turns spec.md's tables into generated files, which no one edits by hand (the gate refuses drift):

| Spec table | Becomes | Checked by |
|---|---|---|
| `spec-rules`, `spec-actions`, precedence | the decision table (`requirements/behavior.yaml`) | the component executes it; the harness oracle re-derives it |
| `spec-predicates` + `spec-settings.sets` | what every rule-column value means, as a small closed condition language | the component and the harness each evaluate it with their own code |
| `spec-interfaces` | input/output JSON Schemas | the component validates every decision against them |
| `spec-inputs`, `date_formats` | the parser contract | the gate parses every declared field, every labeled notice header and the 25 unlabeled HTML samples, and refuses ambiguous date formats |
| `spec-replays` | the 12-step publisher replay (duplicates, restart, refusals) | run against both the rebuilt and the inherited system |
| `spec-verification` | which requirement each check covers, and which rows are `out_of_scope` | per-requirement coverage in `coverage.md` |
| `spec-settings.acceptance` | Gate 2 budgets | per-capture missed-positive and false-positive findings |

What is still hand-written: 25 boundary checks in `harness/rule_invariants.py`, such as "a history gap must be refused before a firm candidate". They stop a table edit from quietly removing a safety refusal, and they change only by code review. The 73 numbered D-sentences are owned prose that explain intent. No check claims them, with one exception: the D6 wording scopes the annotation oracle behind OUTPUT-004/005/006 and STATE-004, so editing a D6 sentence takes those four requirements out of scope (UNKNOWN) until the owner re-approves it.

## Three gates

| Gate | Why it exists | Cost | Has it caught something | What would go undetected without it | Considered instead |
|---|---|---|---|---|---|
| 1 Contracts | Generated files match the spec; tables respect the boundaries; the parser honors the input contract; identity, provenance and inherited-byte integrity hold | seconds, no model calls | In controls: hand-edited `behavior.yaml` (GENERATED_ARTIFACT_DRIFT names the rule row); reordered precedence (BOUNDARY_VIOLATION); day-first dates (INPUT_DATE_FORMAT_MISMATCH, now AMBIGUOUS too) | Silent drift between what the engineer reads and what runs | Trusting tests alone. Tests caught some of these, but failed on unrelated fixtures too, so they could not say which spec row broke. The gate names the row. |
| 2 Trading behavior | The rebuilt classifier on 69 retained executions of the inherited system (three captures of 23 cases: 14 labeled notices and 9 synthetic replay scenarios each; capture-2 is a live run from 2026-09-28), plus frozen witnesses | seconds, no model calls | In a control, routine notices turned into candidates (ROUTINE_ADMIN_SIGNALED). In real data, the force-majeure case lost to a helper failure. That prompted a policy change, not a fix: REMEDIATION-001 now ignores helper failures for firm disruptions, and the frozen witness was re-frozen in the same session | False and missed signals, which is what the desk pays for | Scoring the raw inherited `is_signal`. Rejected: it credits failed executions. |
| 3 Change | Every decision against a registered reference run | seconds | In controls, changed and missing cases. In this remediation, every edit to the harness or labels (EVALUATOR_OR_ORACLE_CHANGED, naming the files) | A code change that shifts decisions the spec did not ask to shift; an agent editing its own grader | Refusing to compare across spec changes. Rejected: spec changes are exactly when comparison matters. |

The acceptance budgets (REMEDIATION-003, approved by the owner) are a ratchet at today's measured level: at most 2 missed positives and 0 false positives per capture. A positive sent to review counts as missed, because no one on the desk receives review items yet.

**Abstention is not safety, and the rebuilt component is not shown to be the better system.** On the live capture-2, the inherited system detects 7/7 labeled positives with 0 false positives and leaves 1/14 labeled notices unresolved. The rebuilt component detects 5/7, also with 0 false positives, but leaves 6/14 unresolved: 2 positives and 4 negatives (46528, 46725, 46728, 46795) go to review instead of a decision. Its zero false positives are bought largely by abstaining. The review queue those cases go to has no owner and no capacity budget: nobody receives it, and Gate 2 limits only missed positives and false positives, not how much is sent to review. So "0 false positives" in the desk table is not evidence that the rebuilt component is safer. Settling it needs a desk review-capacity number and the review rate on unlabeled live notices; until then the honest comparison is that the inherited system finds more on these 14 labels and the rebuilt one is more predictable across runs (its outcomes are identical on all three captures, while the inherited system's differ).

## What the evidence surface must never hide

Missed positives, false positives, abstentions counted as correct, execution failures scored as behavior, rows the gate does not claim, and an unreviewed spec. CURRENT.md shows each of these at the top. Unresolved cases are counted, never credited.

## When something fails

1. Is the spec right and the code wrong? Fix the code; the spec does not change.
2. Is the spec wrong or silent? Copy it, edit the proposal, run `make consequences`, and read what improves and what gets worse.
3. Is there too little evidence to tell? Add an observation or a labeled case, not a rule.

The engineer decides, records a decision row, and rereads the exact bytes. The gate refuses a spec nobody reread.

## When the model changes

The offline gate replays retained captures, so it sees only that the configured model differs (Gate 3 MODEL_CONFIG_CHANGED), and it cannot tell a new model from a nonexistent ID. To learn what a new model does, run `make evaluate-inherited LIVE=1 MAX_CALLS=45`, then `python -m harness register-capture <run>/results.json`. The gate scores that capture next to the retained ones and lists every labeled notice where the runs disagree (today: 46528, 46725, 46864). Registering is an oracle change, so Gate 3 stays UNKNOWN until the owner registers a new reference.

## Context across sessions

`make context TASK=recommendation-classification-maintenance` writes a package: binding requirements, the source files in scope, pending learning (marked unapproved) and superseded guidance (with the reason it lost). A fresh agent needs README, the package, spec.md and CURRENT.md. Learning goes to `context/pending-learning/`; only the owner promotes it into spec.md. Conflicting guidance becomes a proposal file; neither version is silently picked.

## The engineer's first day

Read CURRENT.md top to bottom (ten minutes). Open spec.md at `spec-predicates` and the rule table: that is the whole decision logic, about 40 lines, over facts the normalizer produces. What the normalizer decides (content kind, scalar availability, service and availability mapping) is stated just above that table and driven by `spec-settings.normalization`; a new extractor vocabulary or unit can still need a normalizer code change. Pick one missed positive (46732 or 46881), change a condition in a proposal copy, and run consequences. They will see what it recovers and what it costs before anything changes.

## What the harness found in the inherited system

Real-model evidence first: three captures of the inherited system (two from 2026-09-26, one live run on 2026-09-28), each covering the 14 labeled notices and 9 scenarios. CURRENT.md regenerates both tables below on every gate run.

| Finding | Real-model evidence | Desk risk |
|---|---|---|
| It signals again when the same notice is processed again, including after a restart | `duplicate-input` and `restart-replay` signal in all 3 captures | Duplicate position triggers from one event |
| A failed model verdict can still produce a signal | Of 4 real MODEL_FAILURE cases, 2 still signalled (46864 in capture-1, `restart-replay` in capture-2) and 2 did not (46528 twice). The cause, a missing impact verdict silently scored "small", was located by a code read (`code_reads.md`, V2 diagnosis) | A failed call can look like a real signal |
| Its output depends on the run | 46725 (an OFO, labeled negative) signalled in one unmodified run but not the live one; 46528 signalled only with the 512-token variant; 46864 failed in one run and signalled in the others | The same notice can trigger a position change on one run and not another |
| It detects the labeled positives well | 6/7, 7/7 and 7/7 across the captures | Its recall is not the problem; its failures above are |

**Synthetic-replay findings the real captures do not reproduce.** A stub model drives the 12-step replay, and with it the inherited system signals on an unchanged revision (step C), on a missing prior (missing-history) and on an unsupported PDF. In all three real captures, `unchanged-revision`, `repeated-revision` and `missing-prior` produce **no signal**: the real supersede helper says the revision is not material. So these are behaviours the stub induces, not demonstrated defects. The PDF case has no real capture. One further replay failure, missing-authorization, tests an authorization contract the inherited system never had.

## Autonomy today

**Candidate-only.** The rebuilt component may flag notices for a human. It may not trigger positions, and `recommendation_allowed` is always false. On the labels it makes no false positives, but it misses 2 of 7 positives per capture: 46732, a lifted restriction, goes to review under BR-UNRESOLVED; 46881 goes to review because its prior notice is missing (BR-HISTORY). No one receives review items yet.

Moving toward automatic alerts would need:
- a named owner and a response time for review items;
- delivery with alert keys, acknowledgement and idempotent retry. Only STATE-003's initial-alert limit is checked, at the synthetic publisher seam; keys and acknowledgements are not built, and STATE-005 is out of scope;
- the out-of-order and late-notice checks (HISTORY-003/004), which are out of scope today;
- desk-labeled cases for geography and NNS, beyond the 14 current labels;
- a live run of `make evaluate-inherited` whenever the model changes.

## With more time

- Make the memory obligations executable: out-of-order arrival converging to one final view, retry with the same alert key, and late history reconciling an earlier uncertain decision. Most of the 73 D-sentences would then become checks instead of prose.
- Separate the writer from the evaluator structurally: a component agent with no write access to `harness/`, `tests/` or the frozen oracle, with the gate enforcing it.
- Cut spec.md: generate the duplicated `history[]` schema rows, and move the D-prose that has no check into an appendix.
- Get desk labels for geography (Henry Hub/LNG), NNS outages and terminations, and measure a relevance rule through consequences.
- Run the unlabeled NGPL set live (about 40 calls) and report what the harness says about notices nobody labeled.

## Limits, stated before a reviewer finds them

- One agent thread still writes the component and runs the evaluator. The gate flags evaluator edits, but it cannot stop a writer from also editing the tests.
- **The approval step is not agent-proof.** Any process on the owner's machine can add an `approved` decision row, run `harness reread --person 'Thomas Hand'`, and get an accepted run; a second audit did exactly that. The receipt names a person; it does not authenticate one. The control is outside the repository: branch protection on `main` requiring the CI gate and code-owner review (see README). Even then, an agent holding the owner's own credentials can act as the owner. Real separation needs a second reviewer, or a signing key the agent cannot reach. The same holds for `register-reference`, which clears Gate 3's EVALUATOR_OR_ORACLE_CHANGED: it names an owner and records the files accepted, and CURRENT.md shows both, but it cannot prove who ran it.
- 14 labels, correlated across three captures. No geography or Henry Hub/LNG case can be measured yet (spec A-009).
- Out of scope, and listed as such: durable storage, material-update delivery, out-of-order reconciliation, late-notice actionability, historical decision retrieval.
- The unlabeled samples get header and format checks only. Classifying them needs a live run.
