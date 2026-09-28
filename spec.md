# Behavioral specification — bounded notice decisions

Policy: `assessment-v4-timezone-separation-20260928`. The engineer owns this contract and evaluates changes using `make consequences SPEC=path/to/proposal.md`. Generated expectations explain a proposal; frozen labels and source evidence evaluate it independently.

Boundary: `NormalizedNotice + EventHistory → SignalDecision`. BR-FIRM proposes source-grounded candidates only. Unknown source timezone stays UNKNOWN; automatic time actionability and recommendation authorization require review. No materiality, recommendation, delivery or production approval is implied.

This is the editable source for the bounded rule, input, replay and parameter tables. Fixed tables compile deterministically. The compiler and code-owned safety boundaries remain hand-authored and require review; they are not derived from arbitrary prose. Every prose obligation is UNCHECKED. Adding an obligation with an UNCHECKED declaration is supported, but never creates a passing check. Implementation status and observations belong in generated evidence.

## Engineer workflow

Read the current evidence, identify an implementation defect, a policy gap or an evaluation gap, then edit a proposal copy of this file. Compare changed decisions, detected positives, false positives, true negatives and unresolved cases by capture. Retain adverse consequences. Acceptance requires the separate offline gate; proposal generation never approves or activates a policy.

## Approved lifecycle decisions

D1–D6 retain the assessment obligations as an owned list of unchecked prose, with one exception: the annotation oracle behind OUTPUT-004/005/006 and STATE-004 was approved for D6 exactly as worded (ADR 011). Editing any D6 sentence takes those four requirements out of scope (UNKNOWN) until the owner re-approves the annotation scope. The spec-checks table references related code-owned boundary checks for navigation only. Their results are reported separately and cannot certify or reinterpret these sentences. An inverted sentence remains visibly UNCHECKED, never constraint PASS. Changing a boundary requires an explicit reviewed contract/check change, not a prose edit.

### D1 — Already-signaled identity and memory

[D1-001] Within the bounded NGPL assessment, identify a notice version by pipeline, notice ID and source-content hash.
[D1-002] Identify an event by pipeline and the root notice ID of its complete, acyclic, explicit prior-notice chain.
[D1-003] Do not infer identity from ID order, subject or text similarity.
[D1-004] An incomplete chain or disputed cross-chain identity blocks automatic alerting, but not retention of the input or an explicitly uncertain candidate for review; retain any human-approved correlation and its evidence.
[D1-005] Initial alerts per resolved event must not exceed PARAM-INITIAL-001.
[D1-006] Identify a material update by that event and its distinct source notice version.
[D1-007] Identical replay or same-source re-extraction must not create another alert revision.
[D1-008] Persist each alert key, decision reference, delivery attempt and acknowledgement across restarts.
[D1-009] Retry with the same key; unconfirmed delivery stays uncertain.
[D1-010] Require receiver idempotency before claiming duplicate-free delivery.
[D1-011] Retain this memory without automatic expiry throughout the assessment; production retention requires separate approval.

### D2 — Revisions and material changes

[D2-001] Compare a revision to its explicit predecessor using source-grounded constraints, services/directions, restriction kind/value/unit, operational status, effective interval and operational assertions in the body.
[D2-002] Ignore IDs, links, capture/scrape metadata and whitespace-only presentation changes for materiality.
[D2-003] If operational facts are unchanged, classify the supersede as nonmaterial and issue no new alert.
[D2-004] Other changes require a recorded MATERIAL, NONMATERIAL or UNRESOLVED decision under D6; a changed number alone is not a materiality threshold.
[D2-005] If a resolved event has no prior initial-alert record or attempt, its first MATERIAL and actionable decision may create the initial alert under D1.
[D2-006] If an initial-alert record exists, a qualifying material revision produces a linked update.
[D2-007] An unacknowledged initial attempt reuses its existing key; replay must not create another initial alert.
[D2-008] UNRESOLVED changes are REVIEW_REQUIRED.
[D2-009] A lift/termination must compare the prior restriction; do not generalize one rule from the two labeled termination examples.
[D2-010] For the bounded same-ID/different-source-content case, retain the conflicting capture as evidence, preserve the last accepted snapshot, and require review before changed content can authorize alerting.
[D2-011] Do not automatically overwrite, merge, discard or reconcile the conflict.
[D2-012] Automatic reconciliation remains outside the implemented storage scope; this specified refusal boundary does not establish a complete source-version service.

### D3 — Missing, late and out-of-order notices

[D3-001] Record source event/publication times with stated timezone, ingestion time, and an explicitly supplied timezone-aware UTC reference time for each decision.
[D3-002] Ambiguous time meaning remains unknown; do not substitute the machine/model clock.
[D3-003] Missing ancestors, cycles or conflicting successor ordering defer alerting and retain the gap.
[D3-004] When history arrives, create a new reconciliation decision following explicit prior links; retain the original uncertain decision.
[D3-005] For the same accepted source versions, normalized facts, reference time and approved adjudications, the final event view must be order-independent.
[D3-006] Do not expect independently regenerated stochastic model outputs to be identical.
[D3-007] Actual delivery attempts remain historical and use D1 keys; final-view order independence does not imply identical real-time delivery histories.
[D3-008] A restriction ending at or before the reference time is historical-only for a new disruption alert.
[D3-009] Current or future intervals may be actionable after D6; assume no arbitrary age or advance-notice cutoff.
[D3-010] Unknown time bounds and point changes such as a lift require a human actionability decision at that reference time.
[D3-011] Historical label evaluation stays separate: never rescore it against today or treat it as permission for stale delivery.
[D3-012] A source-grounded operational disruption may classify as SIGNAL_CANDIDATE even when its source timestamp timezone is unresolved. Unknown source timezone does not veto BR-FIRM classification; its candidate-only scope and all other evidence/history/refusal rules remain unchanged.
[D3-013] Unresolved source timezone remains explicitly UNKNOWN and prohibits automatic current/future actionability and recommendation authorization; the actionability/authorization boundary returns REVIEW_REQUIRED even if a caller supplies authorization. recommendation_allowed remains false. The normalized time_basis value UNRESOLVED represents this unknown meaning; UTC fields for unzoned timestamps stay null and the actionability record explicitly reports source_timezone_status UNKNOWN.
[D3-014] No NGPL timezone, UTC conversion, lateness cutoff or desk SLA is inferred.
[D3-015] Where the source timestamp has an explicit trusted timezone, normal current/future/historical evaluation may proceed. Resolved historical-only intervals and clock-dependent revision/actionability decisions retain time precedence. Classification alone never grants materiality approval, recommendation authorization or delivery permission.

### D4 — History needed to explain a decision

[D4-001] Give every decision an immutable identity.
[D4-002] Retrieve by that identity the exact input bytes/hash, extracted facts, prior versions and missing-history observations available then, reference/ingestion times, outcome/reasons, human adjudications, spec/rule/code/ dependency/model/prompt identities, relevant model execution evidence, and delivery key/attempt/acknowledgement when applicable.
[D4-003] Later information and corrections create linked decisions without replacing their evidence or presenting later facts as known at an earlier decision.
[D4-004] Preserve missing-history observations as missingness; do not backfill later facts into an old explanation.
[D4-005] Retain failed/deferred decisions too.
[D4-006] Do not automatically prune assessment records or retain credentials.
[D4-007] Production retention or redaction needs separate approval.
[D4-008] Current snapshot readback alone is not historical decision evidence.

### D5 — Malformed input and failures

[D5-001] Empty, structurally invalid, contradictory or unsupported input must yield an explicit uncertain/error disposition, reason code and retained input evidence, not a successful negative classification or alert.
[D5-002] Validation failure leaves the last valid snapshot unchanged.
[D5-003] Invalid input or unresolved contradictions use UNKNOWN with a distinguishing reason; model/provider, environment and harness failures retain their separate existing classifications.
[D5-004] Missing an optional strong-signal field alone is not malformed input.
[D5-005] Conflicting identity, impossible quantities and incompatible operational assertions require correction/review, not fabricated facts.
[D5-006] Unresolved timestamp meaning requires REVIEW_REQUIRED at the actionability/authorization boundary under D3. It does not by itself block a source-grounded firm-disruption candidate; malformed timestamps and other invalid evidence retain their existing refusal rules.
[D5-007] A corrected execution is a new linked decision; retain the failed attempt.
[D5-008] Classification is unscorable only where the necessary semantic result is unavailable.
[D5-009] Structural, persistence, uncertainty and failure-handling requirements remain evaluable when their required observations exist.
[D5-010] Application dispositions are distinct from harness PASS/FAIL/ERROR/UNKNOWN statuses and execution-domain classifications.
[D5-011] A successful API response with an unusable verdict must not silently become a valid negative or small-impact decision.

### D6 — Materiality, oracles and alert authorization

[D6-001] For new assessment cases outside the frozen label oracle, require a named human's recorded MATERIAL/NONMATERIAL/UNRESOLVED adjudication with cited source evidence.
[D6-002] MATERIAL must identify a meaningful expected effect on gas flow or regional prices; NONMATERIAL must explain routine/administrative content or why a capacity change is minor.
[D6-003] Unsupported judgement is UNRESOLVED and withholds an alert.
[D6-004] Models may propose facts/reasons but may not approve this adjudication.
[D6-005] Critical/unplanned status, planned material impact, segment, quantity and geography are evidence to weigh, not a mandatory all-fields checklist or numeric score cutoff.
[D6-006] Extract stated values with units and meaning; absent values stay unknown.
[D6-007] Do not convert scheduled-to MDQ percentages into absolute curtailed volume without the required source capacity/basis.
[D6-008] Keep the fixed 14 labels as an evaluation oracle only.
[D6-009] Labels do not authorize runtime alerts and must not be supplied as the implementation's answer to classification.
[D6-010] Assessment alerting requires recorded approval and satisfied identity, history and actionability conditions; model proposals and known test labels are not approval.
[D6-011] Under this owner approval, adopt the existing source-based firm scheduled-to MDQ percentage, constraint-segment and named-zone annotations as binding checks only for their annotated cases.
[D6-012] Adopt unchanged-operational-body supersede checks only when the prior is complete and differences are confined to revision metadata or whitespace.
[D6-013] Before applying binding scope, verify that included annotations have traceable source support; unsupported annotations remain unapproved or not evaluated and must be listed.
[D6-014] This approval does not mean the owner personally audited each annotation.
[D6-015] Neither oracle certifies unannotated fields, absolute curtailed volume or real material revisions.
[D6-016] Apply the approved scope in new identified runs; old exploratory conclusions keep their original governance and must not be recertified retrospectively.

## Assessment assumptions

These retained assessment assumptions use this spec's decision and exact-reread process. The historical assumption register/commit ceiling is not an active gate for this component. No scope or trading approval is added.

| Assumption | Current approved scope | Remaining limit |
|---|---|---|
| A-001 | D3: historical label evaluation separate from current alerting; explicit reference clock/time semantics | Actionability engine and time/permutation checks are not implemented/evaluated. |
| A-002 | D2/D6: retain the 14 supplied evaluation labels; use prior context and explicit adjudication for new termination decisions | Labels cannot become implementation answers or runtime approval; no universal lift rule inferred. |
| A-003 | D2/D6: unchanged operational supersedes are nonmaterial with complete prior and source-verified scope | Narrow synthetic checks only; material-update delivery is unimplemented/unevaluated. |
| A-004 | D1/D3: retain uncertain candidates, block automatic alerts on history gaps, reconcile using fixed accepted evidence | Reconciliation/event view is specified only. |
| A-005 | D1/D2: classification and storage receipts are distinct from delivery; persistent keys/attempts/acks and receiver contract required | Delivery interface is absent; duplicate-free delivery is not demonstrated. |
| A-006 | D6: source-supported firm MDQ/constraint-segment/named-zone annotations prospectively binding only where verified | Unsupported annotations remain unapproved/UNKNOWN; no absolute-volume or complete extraction/relevance claim. |
| A-007 | Confidence remains a bounded score, not a calibrated probability; D6 uses named-human adjudication and recorded approval | Existing weights/thresholds are implementation facts, not newly approved domain cutoffs. |
| A-008 | D5/D6: explicit unsupported/uncertain disposition and preserved evidence/state | Broader formats/pipelines/OOD execution, production retention and autonomous-trading acceptance remain unimplemented or unapproved. |
| A-009 | Brief signal factors, measured on the 14 labels: the critical header is set on all 14 (no information); one labeled notice (46624) is in the Louisiana Zone; notice type FORCE MAJEURE appears once (46864). No critical-header or geography rule is adopted. | The labels cannot test Henry Hub/LNG priority. The desk must supply labeled geography cases before a relevance rule can be measured. |

## Requirements

Each row retains its requirement, rationale, severity, preconditions, expected/forbidden behavior and evidence obligation. Authority records historical assessment scope, not a fresh review. Original provenance remains in the previous spec revision. No implementation status in this table is an acceptance claim.

```spec-requirements
ID | Title | Requirement | Rationale | Severity | Inputs | Expected | Forbidden | Evidence | Mode | Authority | Decisions
INPUT-001 | Input identity | Preserve the input notice identity and the content used for a decision. | Decisions must refer to the actual notice. | critical | A readable notice with an explicit identity. | Output ID equals input ID; original input hash is retained. | Silent identity substitution. | case input and hash; observed output/state; check result and requirement ID | deterministic | grounded / existing-contract | Existing contract retained
INPUT-002 | Invalid input | Invalid or contradictory input must have an explicit uncertain/error disposition, retained evidence and preservation of the last valid snapshot. | Prevent fabricated actionable facts. | critical | Invalid, empty, contradictory or unsupported input. | Apply D5: retain input and reason; prohibit a successful negative or alert from invalidity; preserve valid state. Evaluate each requirement where its observations exist. | Silent valid-negative/small-impact fallback, fabricated facts or loss of the last valid snapshot. | case input and hash; observed output/state; check result and requirement ID | deterministic | assessment-assumption / owner-approved | D5
OUTPUT-001 | Decision contract | Every decision exposes notice identity, source hash, a classification (SIGNAL_CANDIDATE, NON_SIGNAL or UNRESOLVED), a disposition, nonempty reason codes and evidence references, with recommendation_allowed always false. Retained inherited outputs keep a finite confidence in [0,1]. | Consumers need a stable observable contract. | critical | Successful processing. | Output validates against the IF-OUTPUT schema; reason_codes[0] names the winning rule; inherited confidence is finite in [0,1]. | Missing fields, an unknown classification or disposition, recommendation_allowed true, NaN, infinity or out-of-range inherited confidence. | case input and hash; observed output/state; check result and requirement ID | deterministic | grounded / owner-approved | D5
OUTPUT-002 | Quantities and units | Numeric restrictions must be finite and nonnegative, carry a unit, and distinguish scheduled-to percent MDQ from volume reduction. | Wrong quantities invert trading meaning. | high | Extracted restriction rows. | Scheduled-to percent MDQ in [0,100]; a nonnumeric unavailability restriction may have null value/unit. | Interpreting 55% scheduled as 55% reduction or imposing [0,100] on hourly entitlement percentages. | case input and hash; observed output/state; check result and requirement ID | deterministic | grounded / owner-approved | D5, D6
OUTPUT-003 | Restriction location linkage | Each extracted restriction must reference a location belonging to the same notice. | Prevents assignment to the wrong constraint. | high | Extracted rows. | Unique location indexes and valid restriction-to-location joins. | Orphan restrictions or cross-notice joins. | case input and hash; observed output/state; check result and requirement ID | deterministic | grounded / owner-approved | D5
OUTPUT-004 | Volume extraction | Extract the stated firm scheduled-to MDQ percentage on annotated notices. | Measures semantic extraction independently of scoring. | high | An annotated firm percentage is present. | Equal the supplied HTML percentage, including field mutation. | Missing or numerically incorrect firm percentage. | case input and hash; observed output/state; check result and requirement ID | evaluative | assessment-assumption / owner-approved | D6
OUTPUT-005 | Segment extraction | Retain annotated affected constraint segment identifiers. | Identifiable constraints are required for decisions. | high | Annotated segment in supplied HTML. | Expected segment appears in extracted locations. | Missing or incorrect constraint segment. | case input and hash; observed output/state; check result and requirement ID | evaluative | assessment-assumption / owner-approved | D6
OUTPUT-006 | Geography extraction | Retain annotated geographic zones without treating a name alone as proof of curtailment. | Geography supports relevance but does not establish impact. | high | Annotated zone in supplied HTML. | Expected zone appears in location output; classification checked independently. | Loss of annotated zone. | case input and hash; observed output/state; check result and requirement ID | evaluative | assessment-assumption / owner-approved | D6
SIGNAL-001 | Trading relevance and labeled evaluation | Classify notices from source-supported operational effects on gas flow or regional prices; routine, administrative and minor changes are not signals, and insufficient evidence remains unresolved. | Makes baseline behavior independently assessable. | critical | Accepted source facts and sufficient semantic evidence; frozen labels apply only to their separate historical evaluation. | Apply the supported behavioral contract without label lookup; report the frozen 14-case evaluation separately, including disagreements and unscorable cases. Labels never authorize runtime recommendations. | Relabeling examples to match implementation or treating execution failures as negatives. | case input and hash; observed output/state; check result and requirement ID | evaluative | grounded / owner-approved | D6
SIGNAL-002 | Routine and administrative control | Routine administrative, IT and plan-index notices without operational flow restrictions must not signal. | Avoid false trading signals from routine postings. | critical | Routine administrative, IT or plan-index source content without an operational flow restriction. | No signal for routine content without operational restriction; supplied selected examples remain evaluation data. | Outage or maintenance words alone create a signal. | case input and hash; observed output/state; check result and requirement ID | evaluative | grounded / owner-approved | D6
SIGNAL-003 | Critical disruption recall | Detect the labeled unplanned force-majeure disruption. | Missing unplanned flow disruption is a high-risk outcome. | critical | A source-supported material critical or unplanned operational disruption with sufficient semantic evidence. | Retain supported disruption candidates; typical signal characteristics are evidence, not an all-fields checklist. Frozen critical-case recall is a separate scoped evaluation. | Silent missed critical disruption. | case input and hash; observed output/state; check result and requirement ID | evaluative | grounded / owner-approved | D6
SIGNAL-004 | Termination and prior context | Evaluate lifting a prior material restriction using available prior context and preserve case-specific termination labels. | A lift can matter as much as onset. | high | A lift or termination with its explicit prior restriction and available source evidence. | Compare prior operational context; do not always suppress or always inherit signal classification. Unresolved materiality/history requires review; frozen examples remain evaluation-only. | A generic policy inferred from two conflicting-looking examples without human clarification. | case input and hash; observed output/state; check result and requirement ID | evaluative | grounded / owner-approved | D2, D3, D6
STATE-001 | Durable state | Successfully processed notices and their child records must survive database close and reopen. | Restart must not lose evidence. | critical | An acknowledged database insertion. | Reopened rows equal saved state; current notice exists. | Success with lost or absent rows. | case input and hash; observed output/state; check result and requirement ID | deterministic | grounded / existing-contract | Existing contract retained
STATE-002 | Idempotent stored observations | Reprocessing identical notice content must not accumulate duplicate stored location or restriction observations. | Repeated scraping must not multiply state. | critical | Same notice processed repeatedly, including after restart. | Child rows per notice reflect the current extraction once; notice row is unique. | Duplicate child rows or multiple versions without explicit version identity. | case input and hash; observed output/state; check result and requirement ID | deterministic | grounded / existing-contract | Existing contract retained
STATE-003 | Already emitted signals | Automatic alerting must use the approved event identity, persistent alert keys and acknowledgement contract. | Duplicate trading actions create risk. | critical | A candidate for automatic alerting, including initial, update, replay and retry decisions. | Apply D1, D2 and D6: resolve the explicit chain and approval/actionability conditions; persist attempts and acknowledgements; reuse unacknowledged keys; retain uncertain candidates without automatic alerting. | Using classification labels or storage receipts as delivery approval; duplicate initial alerts or unsupported duplicate-free delivery claims. | case input and hash; observed output/state; check result and requirement ID | deterministic | assessment-assumption / owner-approved | D1, D2, D6
STATE-004 | Nonmaterial supersedes | A superseding notice with unchanged operational content must not generate another signal. | Suppress routine revision noise. | high | A complete prior chain; source-supported unchanged operational content with only revision metadata or whitespace changes. | Classify the verified synthetic unchanged-body and repeated revision cases as non-signals; under D2/D6, withhold another alert for unchanged operational facts. | A new signal solely because identity/metadata changed; extrapolation to material updates or proof of delivered-alert deduplication. | case input and hash; observed output/state; check result and requirement ID | deterministic | assessment-assumption / owner-approved | D2, D6
STATE-005 | Material revisions | Material revisions require explicit adjudication and linked initial/update decisions while preserving source conflicts for review. | Do not hide changed operational risk. | high | A revision changes operational facts, or an existing notice ID arrives with different source content. | Apply D2: distinguish first initial alert, linked update and unacknowledged retry. Retain conflicting captures, preserve the last accepted snapshot and require review before changed content authorizes alerts. | Unconditional supersede suppression; a second initial alert after an existing attempt; automatic overwrite, merge, discard or reconciliation of source conflicts. | case input and hash; observed output/state; check result and requirement ID | deterministic | assessment-assumption / owner-approved | D2, D6
STATE-006 | Replay and restart | Replaying a notice after closing and reopening persistent state must not create another initial alert. | Reproducible restart behavior. | high | Identical notice replay after close/reopen. | After restart, an identical replay or unchanged revision records no new initial alert (replay steps D and F). | Accumulation due solely to process lifetime. | case input and hash; observed output/state; check result and requirement ID | deterministic | grounded / owner-approved | D1
HISTORY-001 | Available prior lineage | A referenced prior notice that is available must be recoverable through the stored notice chain. | Decisions need traceable context. | high | Prior row exists before evaluation. | Chain includes referenced prior and current identities. | Missing or fabricated available-prior linkage. | case input and hash; observed output/state; check result and requirement ID | deterministic | grounded / owner-approved | D1
HISTORY-002 | Missing prior notices | Missing or disputed prior history must block automatic alerting while preserving the input, gap and uncertain candidate. | Do not hide context gaps. | high | An ancestor is missing or a chain is disputed, cyclic or conflicting. | Apply D1/D3: retain missingness and defer automatic alerting; new history may support a new linked reconciliation decision. | Invented priors, silently complete history, discarded uncertain candidates or retroactive replacement of earlier missingness. | case input and hash; observed output/state; check result and requirement ID | deterministic | assessment-assumption / owner-approved | D1, D3
HISTORY-003 | Out-of-order processing | Out-of-order arrivals must reconcile to an order-independent final view under fixed accepted evidence. | Arrival order is not event chronology. | high | The same accepted source versions, normalized facts, reference time and approved adjudications, processed in different orders. | Apply D3: create linked reconciliation decisions, preserve earlier uncertainty and historical delivery attempts; compare final views using fixed facts. | Using ID sort as chronology; demanding identical stochastic regeneration or identical real-time delivery histories. | case input and hash; observed output/state; check result and requirement ID | deterministic | assessment-assumption / owner-approved | D3
HISTORY-004 | Late notices | Late-notice actionability must use explicit source-time semantics and a supplied reference clock, separate from historical label scoring. | Historical relevance differs from current actionability. | high | A decision about current alerting, including late notices and unresolved point changes. | Apply D3/D6: record source/publication/ingestion times and timezone-aware UTC reference time. Ended restrictions are historical-only for new disruption alerts; unresolved times/lifts require human actionability review. | Implicit machine/model clock, invented age cutoff, rescoring historical labels against today or treating known labels as alert permission. | case input and hash; observed output/state; check result and requirement ID | deterministic | assessment-assumption / owner-approved | D3, D6
HISTORY-005 | Historical explainability | Past decisions must be retrievable by immutable identity with exactly the context available at decision time. | Mutable state alone cannot explain past decisions. | high | A past successful, failed or deferred decision, including after later corrections or revisions. | Apply D4: retain and retrieve input, prior versions/missingness, clocks, facts, reasons, adjudications, implementation/policy/model identities and applicable delivery records. Later information creates linked decisions. | Backfilling later facts into old explanations, replacing earlier evidence, automatic assessment pruning, credential retention or claiming a complete service from current snapshots. | case input and hash; observed output/state; check result and requirement ID | deterministic | assessment-assumption / owner-approved | D4
SAFETY-001 | Execution failures are not behavior | Provider, environment, harness and unknown failures must not be reported as valid behavioral decisions. | A fallback can conceal an invalid baseline. | critical | Every execution. | Separate execution-domain failures from application dispositions and harness verdicts. An unusable model verdict cannot become a valid negative/small-impact result. Classification is unscorable only without its semantic result; other observable requirements remain evaluable. | PASS from a mock, silent fallback, invalid helper verdict or credential failure; blanket exclusion of independently observable structure/state/failure handling. | case input and hash; observed output/state; check result and requirement ID | deterministic | grounded / owner-approved | D5
SAFETY-002 | Unsupported and OOD inputs | Unsupported inputs must retain explicit uncertainty/error evidence and withhold automatic alerting within the approved assessment scope. | Constrain autonomy to demonstrated evidence. | high | Unsupported formats, pipelines, ambiguous assertions or insufficient source support. | Apply D5/D6: retain reason and input; preserve last valid state. Missing optional strong-signal fields alone are not malformed. Unsupported annotations are unapproved or not evaluated and listed. | Extrapolating the labeled corpus or narrow source-supported fields to general production safety or fabricating missing facts. | case input and hash; observed output/state; check result and requirement ID | evaluative | assessment-assumption / owner-approved | D5
OBS-001 | Evidence provenance | Every run must retain input, spec, requirements, implementation, model/prompt and dependency identities plus raw output and prior state. | Supports independent review and reproduction. | critical | Every harness run. | Retain input hashes, model request IDs, raw output, prior state and spec/rule/code/dependency/model/prompt identities. New policy applies only to new identified evaluations; historical evidence keeps its original policy. | Unattributed or reused historical results presented as fresh. | case input and hash; observed output/state; check result and requirement ID | deterministic | grounded / owner-approved | D4
OBS-002 | Inherited integrity | The inherited source and supplied data must remain unchanged through baseline collection. | Preserves a trustworthy comparison point. | critical | Baseline preparation and execution. | Before/after hashes match approved inherited snapshot. | Repairing inherited implementation before evidence exists. | case input and hash; observed output/state; check result and requirement ID | deterministic | grounded / existing-contract | Existing contract retained
OBS-003 | Regression/change evidence | Compare requirement results and observable decisions when implementation, prompt, model, source, dependency or specification changes. | Changes need attributable evidence. | high | A baseline or comparable run exists. | Three primary gates; new pass/fail, unchanged and unexpected differences reported; first-run comparison is UNKNOWN. | Calling absent comparison PASS or changing requirements to clear failures. | case input and hash; observed output/state; check result and requirement ID | deterministic | grounded / existing-contract | Existing contract retained
```

The verification table binds finite checks to requirements. Case IDs select regression examples; they are never classifier inputs. `out_of_scope` rows are not built or observed by this component (durable inherited storage, material-update delivery, out-of-order reconciliation, late-notice actionability and historical decision retrieval); the gate lists them and never claims them. Every other row must be observed or its gate is UNKNOWN.

```spec-verification
ID | Gate | Check type | Check | Parameters
INPUT-001 | 1 | contract | identity | {}
INPUT-002 | 1 | contract | refusal | {}
OUTPUT-001 | 1 | contract | decision_shape | {"confidence_max": 1, "confidence_min": 0}
OUTPUT-002 | 1 | contract | quantities | {"maximum_mdq": 100, "minimum": 0}
OUTPUT-003 | 1 | invariant | links | {}
OUTPUT-004 | 2 | labeled_eval | field_values | {"field": "firm_mdq", "oracle_support": "requirements/oracle-support.json"}
OUTPUT-005 | 2 | labeled_eval | field_values | {"field": "segments", "oracle_support": "requirements/oracle-support.json"}
OUTPUT-006 | 2 | labeled_eval | field_values | {"field": "zones", "oracle_support": "requirements/oracle-support.json"}
SIGNAL-001 | 2 | labeled_eval | classification | {}
SIGNAL-002 | 2 | negative_control | classification | {"ids": [46604, 46775, 46818]}
SIGNAL-003 | 2 | labeled_eval | classification | {"ids": [46864]}
SIGNAL-004 | 2 | labeled_eval | classification | {"ids": [46732, 46725]}
STATE-001 | 1 | invariant | out_of_scope | {}
STATE-002 | 1 | metamorphic | out_of_scope | {}
STATE-003 | 1 | metamorphic | replay | {}
STATE-004 | 2 | metamorphic | revision | {"oracle_support": "requirements/oracle-support.json"}
STATE-005 | 2 | metamorphic | out_of_scope | {}
STATE-006 | 1 | metamorphic | restart | {}
HISTORY-001 | 1 | invariant | lineage | {}
HISTORY-002 | 1 | metamorphic | replay | {}
HISTORY-003 | 1 | metamorphic | out_of_scope | {}
HISTORY-004 | 2 | metamorphic | out_of_scope | {}
HISTORY-005 | 1 | invariant | out_of_scope | {}
SAFETY-001 | 1 | contract | model_proof | {}
SAFETY-002 | 2 | negative_control | refusal | {}
OBS-001 | 1 | contract | provenance | {}
OBS-002 | 1 | invariant | integrity | {}
OBS-003 | 3 | invariant | regression | {}
```

What two PASS rows cover. STATE-003 PASS means the publisher-seam replay steps A, B, E and missing-authorization recorded at most PARAM-INITIAL-001 initial alerts per event, none on replay and none without authorization; persistent alert keys, delivery attempts and acknowledgements (D1-008 to D1-010) are not built, so no check covers them. OBS-001 PASS means the gate run recorded the source-content hash, the spec hash, the comparison identity, the configured model and each registered capture's original execution identity; model request IDs, raw output and prior state are kept inside the registered captures and are not re-checked per run. Both requirements stay as written; these notes narrow what their PASS claims, not what they require.

## Bounded parameters and check scope

PARAM-INITIAL-001 is a maximum, not an observed count. Replay totals are checked against this value. Changing the value changes the check; a prose edit cannot redefine the parameter. These constraints do not establish delivery, retention or adjudication correctness.

```spec-parameters
ID | Meaning | Value | Unit | Requirement
PARAM-INITIAL-001 | Maximum initial alerts | 1 | initial alerts per resolved event | D1-005
```

The no-duplicate assessment boundary permits at most one initial alert per resolved event. The parameter may tighten that maximum but cannot exceed one. The 25 compiled checks are code-owned boundaries over table/schema/replay structure, not semantic interpretations of the D prose. 23 are named in the table below next to the D-sentences they relate to; `refusals_first` and `required_inputs` are keyed on rule conditions and input rows and have no row there. All D prose remains UNCHECKED.

```spec-checks
ID | Check | Sentence coverage
D1-001 | source_identity | UNCHECKED
D1-002 | explicit_history | UNCHECKED
D1-003 | domain_identity | UNCHECKED
D1-004 | history_refusal | UNCHECKED
D1-005 | one_initial | UNCHECKED
D1-006 | - | UNCHECKED
D1-007 | replay_suppression | UNCHECKED
D1-008 | - | UNCHECKED
D1-009 | - | UNCHECKED
D1-010 | - | UNCHECKED
D1-011 | - | UNCHECKED
D2-001 | - | UNCHECKED
D2-002 | - | UNCHECKED
D2-003 | unchanged_suppression | UNCHECKED
D2-004 | unresolved_refusal | UNCHECKED
D2-005 | - | UNCHECKED
D2-006 | - | UNCHECKED
D2-007 | replay_suppression | UNCHECKED
D2-008 | unresolved_refusal | UNCHECKED
D2-009 | - | UNCHECKED
D2-010 | conflict_refusal | UNCHECKED
D2-011 | - | UNCHECKED
D2-012 | - | UNCHECKED
D3-001 | time_schema | UNCHECKED
D3-002 | no_timezone_inference | UNCHECKED
D3-003 | history_refusal | UNCHECKED
D3-004 | - | UNCHECKED
D3-005 | - | UNCHECKED
D3-006 | - | UNCHECKED
D3-007 | - | UNCHECKED
D3-008 | historical_precedence | UNCHECKED
D3-009 | no_age_cutoff | UNCHECKED
D3-010 | clock_boundary | UNCHECKED
D3-011 | no_labels_or_authorization | UNCHECKED
D3-012 | clock_boundary | UNCHECKED
D3-013 | clock_boundary | UNCHECKED
D3-014 | no_timezone_inference | UNCHECKED
D3-015 | historical_precedence | UNCHECKED
D4-001 | - | UNCHECKED
D4-002 | output_provenance | UNCHECKED
D4-003 | - | UNCHECKED
D4-004 | - | UNCHECKED
D4-005 | - | UNCHECKED
D4-006 | - | UNCHECKED
D4-007 | - | UNCHECKED
D4-008 | - | UNCHECKED
D5-001 | invalid_refusal | UNCHECKED
D5-002 | - | UNCHECKED
D5-003 | invalid_refusal | UNCHECKED
D5-004 | optional_unknown | UNCHECKED
D5-005 | conflict_refusal | UNCHECKED
D5-006 | clock_boundary | UNCHECKED
D5-007 | - | UNCHECKED
D5-008 | semantics_refusal | UNCHECKED
D5-009 | - | UNCHECKED
D5-010 | disposition_vocabulary | UNCHECKED
D5-011 | semantics_refusal | UNCHECKED
D6-001 | candidate_only | UNCHECKED
D6-002 | - | UNCHECKED
D6-003 | unresolved_refusal | UNCHECKED
D6-004 | candidate_only | UNCHECKED
D6-005 | no_quantity_checklist | UNCHECKED
D6-006 | optional_unknown | UNCHECKED
D6-007 | no_absolute_inference | UNCHECKED
D6-008 | no_labels_or_authorization | UNCHECKED
D6-009 | no_labels_or_authorization | UNCHECKED
D6-010 | candidate_only | UNCHECKED
D6-011 | - | UNCHECKED
D6-012 | unchanged_suppression | UNCHECKED
D6-013 | - | UNCHECKED
D6-014 | - | UNCHECKED
D6-015 | - | UNCHECKED
D6-016 | - | UNCHECKED
```

## Spec ownership and decisions

Thomas Hand is the repository owner and the only listed spec owner (`spec-settings.owners`); `harness reread` and `harness register-reference` refuse anyone else. Decision status: `proposed` means the change is written and awaits the owner; `owner-requested` means the owner asked for the change; `approved` means the owner approved the stated result; `rejected` records a proposal the owner turned down, kept as history with no effect. Only `owner-requested` and `approved` count, and only once the owner has reread the exact bytes; `harness reread` refuses while any row added since the last reread is `proposed` or `rejected`. Every spec change requires a named decision and makes the old read receipt stale. The hash and name are assertions, not authentication; required human review is enforced outside this repository (branch protection and CODEOWNERS).

```spec-decisions
ID | Status | Person | Previous spec SHA256 | Decision
ARCH-SOURCE-001 | owner-requested | Thomas Hand | 1adc8936b31bbe5b142bf18e71338b80bb6d066fa67be3d6f7c8fa2edda9017e | Adopt the spec-source architecture. Its original timezone proposal was subsequently rejected by TZ-NGPL-001; TZ-NGPL-002 is the active timezone ruling.
TZ-NGPL-001 | rejected | Thomas Hand | - | REJECTED proposal: NGPL posts in Central time; timestamps without a zone are parsed as America/Chicago. No such default is authorized.
TZ-NGPL-002 | owner-requested | Thomas Hand | 5d4adfff7cb944c6a4ec9e9f17bb0ea7deaed47dfff2eeb35583703786a2245f | Adopt source-grounded SIGNAL_CANDIDATE classification with unknown timezone; prohibit automatic time actionability and recommendation authorization, require REVIEW_REQUIRED, and never infer a zone. Exact ruling: evidence/timezone-separation/20260928/owner-ruling.txt.
FEEDBACK-001 | owner-requested | Thomas Hand | c7a3898dab4f2acb0e2123ed218449023e3fbec94d9bd0b1704376605afaac1f | Make evidence-driven spec maintenance practical: compact normative tables, preview consequences before adoption, explicit check limits and measured tradeoffs. Preserve classification policy, labels, thresholds and authorization.
AUDIT-TRUTH-001 | owner-requested | Thomas Hand | c7a3898dab4f2acb0e2123ed218449023e3fbec94d9bd0b1704376605afaac1f | Repair gate exits, read-only validation, execution-failure scoring and honest check coverage. Keep unchecked prose separate from code-owned boundaries; retain assumptions here. No new business policy or exact human reread is asserted.
REMEDIATION-001 | approved | Thomas Hand | c7a3898dab4f2acb0e2123ed218449023e3fbec94d9bd0b1704376605afaac1f | Predicate meaning moves into spec-predicates. An unusable helper verdict vetoes a decision only when the notice is not a firm disruption; the publisher neither stores nor publishes such a decision (SEMANTICS_INCOMPLETE). Measured: capture-1/46864 ERROR -> SIGNAL_CANDIDATE, no new false positive. The publisher witness unusable-impact was re-frozen to match; spec and witness changed in the same session, so the owner's approval is the independent check.
REMEDIATION-002 | approved | Thomas Hand | c7a3898dab4f2acb0e2123ed218449023e3fbec94d9bd0b1704376605afaac1f | Approved by Thomas Hand 2026-09-28: a restriction with no stated timezone is ENDED when its latest naive source end plus unresolved_time_margin_hours (at least 14, the largest UTC offset) is at or before the reference time. Labeled captures are scored as of each notice's post time (D3-011). No captured outcome changes; live candidates for long-ended restrictions become HISTORICAL_ONLY.
REMEDIATION-003 | approved | Thomas Hand | c7a3898dab4f2acb0e2123ed218449023e3fbec94d9bd0b1704376605afaac1f | Approved by Thomas Hand 2026-09-28: Gate 2 acceptance budgets. Per capture, at most 0 labeled negatives may be candidates and at most 2 labeled positives may be missed (a positive sent to review counts as missed). 2 is the measured value on 2026-09-28: a ratchet that may only tighten, not a quality claim. Review is the specified outcome for SIGNAL-002 and SIGNAL-004 cases; an unresolved SIGNAL-003 case fails. Six verification rows that this component cannot observe are declared out_of_scope. OUTPUT-001 and STATE-006 text now describe what their checks observe.
NNS-FIRM-001 | approved | Thomas Hand | c7a3898dab4f2acb0e2123ed218449023e3fbec94d9bd0b1704376605afaac1f | Approved by Thomas Hand 2026-09-28 (desk request): NGPL No-Notice Service is a firm, storage-backed service. Extracted service_type NO_NOTICE normalizes to a distinct NO_NOTICE_FIRM value (source distinction preserved) and NO_NOTICE_FIRM joins FIRM_SERVICES, so a firm NNS restriction (UNAVAILABLE or PRIMARY_ONLY) is a FIRM_DISRUPTION like other firm services. Measured by make consequences: 0/46 captured outcomes change; the only captured NNS row (46528, labeled negative) is an HOURLY_LIMIT_PCT partial limit and stays non-firm-disruption. No captured or labeled NNS outage exists, so the intended positive effect is unmeasured by frozen labels.
AUDIT2-001 | approved | Thomas Hand | 4448a6f9e9ee3841e0086a8e556c21bbd584efc9167742a831154f70e3e18a8e | Approved by Thomas Hand 2026-09-28: remove status prose that was false on the reviewed bytes ("awaits an exact-spec human reread", "Exact spec reread still pending"). No rule, predicate, setting or requirement changes; make consequences shows 0 of 46 changed.
AUDIT3-001 | approved | Thomas Hand | c89f760b3f2167345112801cd7825d26c40c102996239d13a2c788c9c4d363b6 | Approved by Thomas Hand 2026-09-28. Third audit: list the spec owner (only listed owners may reread or register a reference); declare that D6 wording scopes the annotation oracle; state the decision status vocabulary; state what the normalizer decides; remove stale "review remains pending" text from FEEDBACK-001; count 25 code-owned boundaries (adds refusals_first and required_inputs). No rule, predicate, set or acceptance value changes.
AUDIT4-001 | approved | Thomas Hand | a5bb4e2231092d6da4928c346d8d8f3722c8d44299a721de5c58d4be35249e76 | Fourth audit: `within SET` on an empty list is now false (it was vacuously true), in both the harness oracle and the component; the operator text now states what `overlaps` and `within` mean. The only condition using `within` is History COMPLETE (`history.statuses within LINKED_STATUSES`), so a notice with an empty linked-status list is now History GAP (BR-HISTORY, MISSING_HISTORY) instead of COMPLETE. Measured by gate --proposal on e7541f9: 0 captured decisions change (Gate 3 changed_decisions empty, 91 of 91 captured cases unchanged); no rule, predicate, set or acceptance value changes. Record correction (not a policy change): NNS-FIRM-001's "desk request" was a maintenance request posed by the candidate; no desk exists. NNS-FIRM-001 is left as approved and reread.
AUDIT5-001 | proposed | Thomas Hand | c1f20c1cf233a0ccdd5607c33a443bf653f0e3993b334b806498b55686d4b937 | Fifth audit, wording only: a note under the verification table states what the STATE-003 and OBS-001 PASS rows cover and what is not built; both requirements stay as written. The decision-status vocabulary lists all four statuses the compiler accepts and what reread accepts; the boundary-check count says 23 are listed and names the two that are not. No requirement, rule, predicate, set, setting or acceptance value changes; make consequences shows 0 of 69 captured outcomes changed.
```

## Fixed domain rules

ANY imposes no condition. Conditions are checked left to right; the precedence line orders all rows. Oracle answer is extraction/helper usability, never an evaluation label. The column vocabulary is requirements/rule-block.schema.json; what each value means is the `spec-predicates` table below.

- Format: ANY, SUPPORTED, UNSUPPORTED.
- Oracle answer: ANY, USABLE, UNUSABLE.
- Conflict: ANY, YES, NO.
- History: ANY, COMPLETE, GAP.
- Operational change: ANY, UNCHANGED, CHANGED, UNKNOWN.
- Information-only: ANY, YES, NO.
- Restriction: ANY, KNOWN, NONE, UNKNOWN.
- Service class: ANY, FIRM_DISRUPTION, OTHER.
- Restriction current: ANY, CURRENT, ENDED, UNKNOWN.

```spec-rules
ID | Format | Oracle answer | Conflict | History | Operational change | Information-only | Restriction | Service class | Restriction current | Action
BR-FORMAT | UNSUPPORTED | ANY | ANY | ANY | ANY | ANY | ANY | ANY | ANY | UNSUPPORTED_FORMAT
BR-SEMANTICS | ANY | UNUSABLE | ANY | ANY | ANY | ANY | ANY | ANY | ANY | UNUSABLE_SEMANTICS
BR-CONTRADICTION | ANY | ANY | YES | ANY | ANY | ANY | ANY | ANY | ANY | CONTRADICTORY_EVIDENCE
BR-HISTORY | ANY | ANY | ANY | GAP | ANY | ANY | ANY | ANY | ANY | MISSING_HISTORY
BR-UNCHANGED | ANY | ANY | ANY | ANY | UNCHANGED | ANY | ANY | ANY | ANY | UNCHANGED_REVISION
BR-ROUTINE | ANY | ANY | ANY | ANY | ANY | YES | NONE | ANY | ANY | NO_OPERATIONAL_RESTRICTION
BR-HISTORICAL | ANY | ANY | ANY | ANY | ANY | ANY | ANY | FIRM_DISRUPTION | ENDED | HISTORICAL_ONLY
BR-FIRM | ANY | ANY | ANY | ANY | ANY | ANY | ANY | FIRM_DISRUPTION | ANY | FIRM_CANDIDATE
BR-UNRESOLVED | ANY | ANY | ANY | ANY | ANY | ANY | ANY | ANY | ANY | UNRESOLVED
Precedence: BR-FORMAT > BR-SEMANTICS > BR-CONTRADICTION > BR-HISTORY > BR-UNCHANGED > BR-ROUTINE > BR-HISTORICAL > BR-FIRM > BR-UNRESOLVED
```

The normalizer (`rebuilt/normalization.py`) turns the retained extraction into the facts these conditions read, using only the maps in `spec-settings.normalization`: `content_kind` is INFORMATIONAL when the extractor set information-only, RESTRICTION when it found restriction rows, otherwise UNKNOWN; scalar `availability` is the one value shared by every row, otherwise UNKNOWN; services and availability map through the `services` and `availability` tables (unmapped values stay UNKNOWN); `evidence.contradictory` is always false from this normalizer, so conflicts reach the rules only through the Conflict condition below. It adds no other judgement; anything else a decision needs belongs in this table.

What each column value means. Rows for a column are tried top to bottom; the first true condition gives the value, and the last row of each column is `otherwise`. A condition reads normalized input fields, the derived observations below, named sets from `spec-settings.sets` (`SUPPORTED_FORMATS`, `ROOT_STATUSES` and `LINKED_STATUSES` come from `formats` and `history_statuses`), and `[Column]` values defined earlier in this table. Operators: `and`, `or`, `not`, parentheses, `in SET`, `overlaps SET` (shares at least one member), `within SET` (at least one member, and every member is in SET; an empty list is never within), `= VALUE`, `any facts.restrictions has (...)`. Nothing else parses. Changing a set or a condition here changes behavior; no code edit is needed.

```spec-predicates
Column | Value | Condition
Format | SUPPORTED | source.media_type in SUPPORTED_FORMATS
Format | UNSUPPORTED | otherwise
Information-only | YES | facts.content_kind in INFORMATION_KINDS
Information-only | NO | otherwise
Restriction | KNOWN | facts.availability in RESTRICTED_AVAILABILITY or any facts.restrictions has (availability in RESTRICTED_AVAILABILITY)
Restriction | NONE | [Information-only] = YES
Restriction | UNKNOWN | otherwise
Conflict | YES | evidence.contradictory or ([Information-only] = YES and [Restriction] = KNOWN)
Conflict | NO | otherwise
History | COMPLETE | history.complete and history.root_status in ROOT_STATUSES and history.statuses within LINKED_STATUSES
History | GAP | otherwise
Operational change | UNCHANGED | notice.status = SUPERSEDE and predecessor.status in UNCHANGED_PREDECESSOR_STATUSES and predecessor.facts_equal
Operational change | CHANGED | predecessor.present
Operational change | UNKNOWN | otherwise
Service class | FIRM_DISRUPTION | facts.content_kind = RESTRICTION and (any facts.restrictions has (service in FIRM_SERVICES and availability = UNAVAILABLE) or facts.availability = PRIMARY_ONLY or (facts.services overlaps FIRM_SERVICES and facts.availability = UNAVAILABLE))
Service class | OTHER | otherwise
Oracle answer | USABLE | evidence.extraction_usable and (evidence.helpers_usable or [Service class] = FIRM_DISRUPTION)
Oracle answer | UNUSABLE | otherwise
Restriction current | ENDED | time.ended or time.ended_in_any_timezone
Restriction current | CURRENT | time.current
Restriction current | UNKNOWN | otherwise
```

Derived observations are computed from the input, never supplied by a model or label:

| Observation | Meaning |
|---|---|
| history.complete | Following `notice.prior_notice_id` through `history` reaches a root with no missing ID and no cycle, and no two history entries share a notice ID. |
| history.root_status / history.statuses | Status of the chain root, and of every notice on the chain including the arriving one. |
| predecessor.present / .status | The history entry whose notice ID equals `notice.prior_notice_id`, and its status. |
| predecessor.facts_equal | The arriving and predecessor normalized facts are equal as JSON (booleans and numbers are not interchangeable). |
| time.ended | `facts.time_basis` is UTC, `facts.end_time` is present, and it is at or before `reference_time`. |
| time.current | `facts.time_basis` is UTC, `facts.start_time` is present, and the restriction has not ended. |
| time.ended_in_any_timezone | `facts.time_basis` is UNRESOLVED, every restriction row's `source_end` (or, with no rows, the notice end) is a naive date or date-time (a bare date ends at the next midnight; TBD or missing is unknown), and the latest one plus `unresolved_time_margin_hours` is at or before `reference_time`. The margin must be at least 14 hours, the largest UTC offset, so the restriction has ended whatever the source timezone. No timezone is inferred. |

```spec-actions
Action | Classification | Disposition | Reason
UNSUPPORTED_FORMAT | UNRESOLVED | REVIEW_REQUIRED | UNSUPPORTED_FORMAT
UNUSABLE_SEMANTICS | UNRESOLVED | ERROR | UNUSABLE_SEMANTICS
CONTRADICTORY_EVIDENCE | UNRESOLVED | REVIEW_REQUIRED | CONTRADICTORY_EVIDENCE
MISSING_HISTORY | UNRESOLVED | REVIEW_REQUIRED | MISSING_HISTORY
UNCHANGED_REVISION | NON_SIGNAL | SUPPRESSED | UNCHANGED_REVISION
NO_OPERATIONAL_RESTRICTION | NON_SIGNAL | NO_SIGNAL | NO_OPERATIONAL_RESTRICTION
HISTORICAL_ONLY | NON_SIGNAL | NO_SIGNAL | HISTORICAL_ONLY
FIRM_CANDIDATE | SIGNAL_CANDIDATE | CANDIDATE_ONLY | FIRM_CANDIDATE
UNRESOLVED | UNRESOLVED | REVIEW_REQUIRED | UNRESOLVED
```

## Stateful replay checks

A–F plus six refusal controls use synthetic authorization and semantic evidence. They test the separate publisher seam, not live recommendations or delivery. D4-005/D5-001 require the stateful boundary to retain a refused decision and its input even when called without a harness wrapper. The stateless classifier CLI does not provide durable storage.

```spec-replays
ID | Arriving notice | Restart | Oracle answer | Authorization | Action | Requirement
A | root | NO | valid | YES | REPLAY_A | STATE-003
B | root | NO | valid | YES | REPLAY_B | STATE-003
C | unchanged_revision | NO | valid | YES | REPLAY_C | STATE-004
D | unchanged_revision | YES | valid | YES | REPLAY_D | STATE-006
E | distinct | NO | valid | YES | REPLAY_E | STATE-003
F | distinct | YES | valid | YES | REPLAY_F | STATE-006
unusable-impact | root | NO | unusable_impact | YES | REPLAY_UNUSABLE_IMPACT | INPUT-002
unavailable-extraction | extraction_failure | NO | unavailable_extraction | YES | REPLAY_UNAVAILABLE_EXTRACTION | INPUT-002
missing-history | missing_history | NO | valid | YES | REPLAY_MISSING_HISTORY | HISTORY-002
missing-authorization | unauthorized | NO | valid | NO | REPLAY_MISSING_AUTHORIZATION | STATE-003
routine | routine | NO | information_only | YES | REPLAY_ROUTINE | SIGNAL-002
unsupported-format | unsupported_format | NO | valid | YES | REPLAY_UNSUPPORTED_FORMAT | SAFETY-002
```

```spec-replay-actions
Action | Initial alerts | Disposition | Reason | Semantic safety
REPLAY_A | 1 | INITIAL_RECOMMENDATION | - | -
REPLAY_B | 0 | SUPPRESSED | - | -
REPLAY_C | 0 | SUPPRESSED | - | -
REPLAY_D | 0 | SUPPRESSED | - | -
REPLAY_E | 1 | INITIAL_RECOMMENDATION | - | -
REPLAY_F | 0 | SUPPRESSED | - | -
REPLAY_UNUSABLE_IMPACT | 0 | REVIEW_REQUIRED | SEMANTICS_INCOMPLETE | -
REPLAY_UNAVAILABLE_EXTRACTION | 0 | ERROR | - | YES
REPLAY_MISSING_HISTORY | 0 | REVIEW_REQUIRED | MISSING_HISTORY | -
REPLAY_MISSING_AUTHORIZATION | 0 | REVIEW_REQUIRED | AUTHORIZATION_REQUIRED | -
REPLAY_ROUTINE | 0 | NO_SIGNAL | - | -
REPLAY_UNSUPPORTED_FORMAT | 0 | REVIEW_REQUIRED | UNSUPPORTED_FORMAT | -
```

## Parser input contract

Every field consumed by the bounded source parser or capture normalizer is listed below. Source fields retain their original values and supplier. A missing required field or malformed typed value produces an identified ERROR/REVIEW, never a guessed identity, INITIATE status, time or negative classification. Optional absent values stay unknown. Case normalization and whitespace trimming are presentation only. No captured is_signal/confidence/label is a semantic input. Header date formats are fixed below; ISO dates/offset timestamps are also accepted in retained captures. Naive dates/times remain unresolved; TBD is an unknown end, not infinity. Missing timestamps never use the wall clock, download time or a different header as a substitute.

```spec-inputs
ID | Field | Type | Missing | Malformed | Supplier
INPUT-SOURCE-001 | header.tsp | text | UNKNOWN | ERROR | source_parser
INPUT-SOURCE-002 | header.critical | text | UNKNOWN | ERROR | source_parser
INPUT-SOURCE-003 | header.type1 | text | UNKNOWN | ERROR | source_parser
INPUT-SOURCE-004 | header.type2 | text | UNKNOWN | ERROR | source_parser
INPUT-SOURCE-005 | header.notice_effective_date | timestamp | UNKNOWN | ERROR | source_parser
INPUT-SOURCE-006 | header.notice_end_date | timestamp | UNKNOWN | ERROR | source_parser
INPUT-SOURCE-007 | header.post_date | timestamp | UNKNOWN | ERROR | source_parser
INPUT-SOURCE-008 | header.notice_id | identifier | ERROR | ERROR | source_parser
INPUT-SOURCE-009 | header.req_rsp | text | UNKNOWN | ERROR | source_parser
INPUT-SOURCE-010 | header.rsp_date | timestamp | UNKNOWN | ERROR | source_parser
INPUT-SOURCE-011 | header.status | text | ERROR | ERROR | source_parser
INPUT-SOURCE-012 | header.prior_notice_id | identifier | UNKNOWN | ERROR | source_parser
INPUT-SOURCE-013 | header.subject | text | UNKNOWN | ERROR | source_parser
INPUT-SOURCE-014 | metadata.notice_id | identifier | UNKNOWN | ERROR | source_parser
INPUT-SOURCE-015 | metadata.notice_type | text | UNKNOWN | ERROR | source_parser
INPUT-SOURCE-016 | metadata.subject | text | UNKNOWN | ERROR | source_parser
INPUT-SOURCE-017 | metadata.download_date | timestamp | UNKNOWN | ERROR | source_parser
INPUT-SOURCE-018 | metadata.source_url | text | UNKNOWN | ERROR | source_parser
INPUT-SOURCE-019 | metadata.html_file | text | UNKNOWN | ERROR | source_parser
INPUT-SOURCE-020 | body | text | ERROR | ERROR | source_parser
INPUT-SOURCE-021 | notice.notice_id | integer | ERROR | ERROR | source_parser
INPUT-SOURCE-022 | notice.prior_notice_id | integer | UNKNOWN | ERROR | source_parser
INPUT-SOURCE-023 | notice.status | text | ERROR | ERROR | source_parser
INPUT-SOURCE-024 | notice.notice_type | text | ERROR | ERROR | source_parser
INPUT-SOURCE-025 | notice.information_only | flag | UNKNOWN | ERROR | model
INPUT-SOURCE-026 | notice.body_text | text | ERROR | ERROR | source_parser
INPUT-SOURCE-027 | notice.effective_datetime | timestamp | UNKNOWN | ERROR | source_parser
INPUT-SOURCE-028 | notice.end_datetime | timestamp | UNKNOWN | ERROR | source_parser
INPUT-SOURCE-029 | locations | rows | UNKNOWN | ERROR | model
INPUT-SOURCE-030 | restrictions | rows | UNKNOWN | ERROR | model
INPUT-SOURCE-031 | locations[].loc_code | text_or_integer | UNKNOWN | ERROR | model
INPUT-SOURCE-032 | locations[].segment | text_or_integer | UNKNOWN | ERROR | model
INPUT-SOURCE-033 | locations[].compressor_station | text_or_integer | UNKNOWN | ERROR | model
INPUT-SOURCE-034 | locations[].zone | text_or_integer | UNKNOWN | ERROR | model
INPUT-SOURCE-035 | locations[].system | text_or_integer | UNKNOWN | ERROR | model
INPUT-SOURCE-036 | restrictions[].service_type | text | UNKNOWN | ERROR | model
INPUT-SOURCE-037 | restrictions[].restriction_type | text | UNKNOWN | ERROR | model
INPUT-SOURCE-038 | restrictions[].restriction_value | number | UNKNOWN | ERROR | model
INPUT-SOURCE-039 | restrictions[].restriction_unit | text | UNKNOWN | ERROR | model
INPUT-SOURCE-040 | restrictions[].status | text | UNKNOWN | ERROR | model
INPUT-SOURCE-041 | restrictions[].location_index | integer | UNKNOWN | ERROR | model
INPUT-SOURCE-042 | restrictions[].start_datetime | timestamp | UNKNOWN | ERROR | model
INPUT-SOURCE-043 | restrictions[].end_datetime | timestamp | UNKNOWN | ERROR | model
INPUT-SOURCE-044 | semantic.extraction_usable | boolean | ERROR | ERROR | retained_evidence
INPUT-SOURCE-045 | semantic.execution_error | text | UNKNOWN | ERROR | retained_evidence
INPUT-SOURCE-046 | semantic.helpers | helper_pairs | UNKNOWN | ERROR | retained_evidence
INPUT-SOURCE-047 | semantic.source_media_type | text | UNKNOWN | ERROR | retained_evidence
```

[INPUT-TIME-001] Accept the date formats in spec-settings only. Malformed times return an identified input issue; valid naive/date-only values remain UNKNOWN in UTC fields. No default timezone is active; TZ-NGPL-001 is rejected. Source-grounded classification and actionability are separated by D3-012/D3-013.

[INPUT-VALUES-002] A rows value is a list of objects. semantic.helpers is a list of exactly two-element [name, answer] pairs with a text name and a JSON scalar answer. Missing optional collections are unknown; malformed collections or members produce an identified error before normalization. No source value is fabricated to continue after malformed input.

[INPUT-PARSER-001] Gate-time parser checks enumerate every field, exercise missing and malformed values and all declared date forms, and inspect every retained HTML header. The bounded parser is checked separately from the inherited parser; inherited fallbacks do not define correct behavior.

The classifier CLI runs only with matching generated artifacts and a current exact-spec read receipt. Pending review is REVIEW_PENDING on stderr, no stdout decision, exit 3; invalid input/contract is exit 2. A valid decision with a current receipt exits 0. These are CLI execution outcomes, not business approval.

### Closed vocabulary and refusal boundary

| Input | Allowed values / behavior |
|---|---|
| Source notice status | INITIATE, SUPERSEDE, TERMINATE. INITIATE may be a root; linked versions follow explicit prior IDs. WITHDRAWN and other new values have no approved mapping. |
| Unknown normalized status or malformed input | The classifier CLI emits structured INPUT_OR_CONTRACT_ERROR on stderr and exits 2. No successful negative is inferred. This stateless CLI does not implement durable refusal retention; D4-005/D5-001 remain unsatisfied at that boundary. |
| Source time | Explicit trusted offsets may resolve time. Naive and date-only source values stay UNKNOWN; UTC values remain null. No default timezone. |
| Notice type / critical header | Retained source facts. No header-only force-majeure or criticality precedence is approved. |
| Normalized enumerations | The interface table below is exhaustive, including content kind, service, quantity and time basis. |

## Interface fields

Fixed field declarations generate JSON Schema. `$` is the root, `[]` an array item. JSON cells express literal types, allowed values, constants and representation bounds only. A dash means no constraint. Missing required fields, wrong types, unknown enumerations and extra fields where forbidden are errors. No new operators are accepted.

```spec-interfaces
ID | Interface | Field | Type | Required fields | Allowed values | Constant | Minimum | Minimum items | Pattern | Extra fields | Meaning
IF-INPUT-001 | input | $ | "object" | ["version","source","notice","facts","history","reference_time","evidence"] | - | - | - | - | - | false | -
IF-INPUT-002 | input | $.version | - | - | - | 1 | - | - | - | - | -
IF-INPUT-003 | input | $.source | "object" | ["pipeline","media_type","sha256","bytes_reference","fields"] | - | - | - | - | - | false | -
IF-INPUT-004 | input | $.source.pipeline | - | - | - | "NGPL" | - | - | - | - | -
IF-INPUT-005 | input | $.source.media_type | "string" | - | - | - | - | - | - | - | "text/html or application/vnd.ngpl.normalized+json supported; other types yield review without extraction claim."
IF-INPUT-006 | input | $.source.sha256 | "string" | - | - | - | - | - | "^[0-9a-f]{64}$" | - | -
IF-INPUT-007 | input | $.source.bytes_reference | "string" | - | - | - | - | - | - | - | "Immutable relative source byte artifact, not a URL standing in for retained content."
IF-INPUT-008 | input | $.source.fields | "object" | - | - | - | - | - | - | {"type":"string"} | "Verbatim source header values, source timezone text, body/source spans, and ingestion timestamp. Inferred facts stay in facts, never rewrite raw fields."
IF-INPUT-009 | input | $.notice | "object" | ["notice_id","prior_notice_id","status","notice_type"] | - | - | - | - | - | false | -
IF-INPUT-010 | input | $.notice.notice_id | "integer" | - | - | - | - | - | - | - | -
IF-INPUT-011 | input | $.notice.prior_notice_id | ["integer","null"] | - | - | - | - | - | - | - | -
IF-INPUT-012 | input | $.notice.status | "string" | - | ["INITIATE","SUPERSEDE","TERMINATE"] | - | - | - | - | - | "Source notice status."
IF-INPUT-013 | input | $.notice.notice_type | "string" | - | - | - | - | - | - | - | "Source Notice Type Desc (1), with subtype retained in source fields."
IF-INPUT-014 | input | $.facts | "object" | ["content_kind","services","availability","locations","quantities","operational_assertions","start_time","end_time","time_basis"] | - | - | - | - | - | false | -
IF-INPUT-015 | input | $.facts.content_kind | "string" | - | ["ADMINISTRATIVE","INFORMATIONAL","RESTRICTION","RESTORATION","UNKNOWN"] | - | - | - | - | - | "Normalized source content, not materiality or a signal label."
IF-INPUT-016 | input | $.facts.services | "array" | - | - | - | - | - | - | - | -
IF-INPUT-017 | input | $.facts.services[] | "string" | - | ["PRIMARY_FIRM","SECONDARY_FIRM","NO_NOTICE_FIRM","INTERRUPTIBLE","AOR_ITS","UNKNOWN"] | - | - | - | - | - | "Service affected; preserve source distinctions in assertions."
IF-INPUT-018 | input | $.facts.availability | "string" | - | ["UNAVAILABLE","PRIMARY_ONLY","PARTIAL","AVAILABLE","UNKNOWN"] | - | - | - | - | - | "Source restriction, not an impact score."
IF-INPUT-019 | input | $.facts.locations | "array" | - | - | - | - | - | - | - | -
IF-INPUT-020 | input | $.facts.locations[] | "object" | ["kind","value","evidence_ref"] | - | - | - | - | - | false | -
IF-INPUT-021 | input | $.facts.locations[].kind | "string" | - | ["SEGMENT","ZONE","SYSTEM","LOC","COMPRESSOR_STATION"] | - | - | - | - | - | "Source identifier kind, never proof of curtailment by itself."
IF-INPUT-022 | input | $.facts.locations[].value | "string" | - | - | - | - | - | - | - | "Exact identifier; constraint point distinguished from root cause."
IF-INPUT-023 | input | $.facts.locations[].evidence_ref | "string" | - | - | - | - | - | - | - | "Source span/page/field reference."
IF-INPUT-024 | input | $.facts.quantities | "array" | - | - | - | - | - | - | - | -
IF-INPUT-025 | input | $.facts.quantities[] | "object" | ["kind","value","unit","basis","evidence_ref"] | - | - | - | - | - | false | -
IF-INPUT-026 | input | $.facts.quantities[].kind | "string" | - | ["SCHEDULED_TO_PCT_MDQ","HOURLY_LIMIT_PCT","ABSOLUTE_CURTAILMENT","UNAVAILABLE"] | - | - | - | - | - | "Kinds must not be interchanged."
IF-INPUT-027 | input | $.facts.quantities[].value | ["number","null"] | - | - | - | 0 | - | - | - | -
IF-INPUT-028 | input | $.facts.quantities[].unit | "string" | - | ["PERCENT_MDQ","PERCENT_ENTITLEMENT","MMBtu","Dth","NONE"] | - | - | - | - | - | "Null quantity for categorical UNAVAILABLE uses NONE; absolute energy needs stated basis."
IF-INPUT-029 | input | $.facts.quantities[].basis | "string" | - | - | - | - | - | - | - | "Scheduled-to percentage is remaining allowed capacity; never infer absolute volume without source capacity/time basis."
IF-INPUT-030 | input | $.facts.quantities[].evidence_ref | "string" | - | - | - | - | - | - | - | "Exact supporting source span."
IF-INPUT-031 | input | $.facts.operational_assertions | "array" | - | - | - | - | - | - | - | -
IF-INPUT-032 | input | $.facts.operational_assertions[] | "string" | - | - | - | - | - | - | - | "Source-grounded operational assertion with source span; preserve material body facts, not capture metadata."
IF-INPUT-033 | input | $.facts.start_time | ["string","null"] | - | - | - | - | - | - | - | "ISO 8601 with explicit UTC offset when known; null means absent/unresolved; never silently assume local timezone."
IF-INPUT-034 | input | $.facts.end_time | ["string","null"] | - | - | - | - | - | - | - | "ISO 8601 with explicit UTC offset when known; null means absent/unresolved; never silently assume local timezone."
IF-INPUT-035 | input | $.facts.time_basis | "string" | - | ["UTC","UNRESOLVED"] | - | - | - | - | - | "Explicit accepted time interpretation; source timezone retained in source fields."
IF-INPUT-036 | input | $.facts.restrictions | "array" | - | - | - | - | - | - | - | "Per-row source associations. Optional for prior v1 normalized witnesses; required from the retained-capture normalizer."
IF-INPUT-037 | input | $.facts.restrictions[] | "object" | ["service","availability","restriction_type","status","location_index","source_start","source_end","evidence_ref"] | - | - | - | - | - | false | -
IF-INPUT-038 | input | $.facts.restrictions[].service | "string" | - | ["PRIMARY_FIRM","SECONDARY_FIRM","NO_NOTICE_FIRM","INTERRUPTIBLE","AOR_ITS","UNKNOWN"] | - | - | - | - | - | -
IF-INPUT-039 | input | $.facts.restrictions[].availability | "string" | - | ["UNAVAILABLE","PRIMARY_ONLY","PARTIAL","AVAILABLE","UNKNOWN"] | - | - | - | - | - | -
IF-INPUT-040 | input | $.facts.restrictions[].restriction_type | "string" | - | - | - | - | - | - | - | -
IF-INPUT-041 | input | $.facts.restrictions[].status | "string" | - | - | - | - | - | - | - | -
IF-INPUT-042 | input | $.facts.restrictions[].location_index | ["integer","null"] | - | - | - | - | - | - | - | -
IF-INPUT-043 | input | $.facts.restrictions[].source_start | ["string","null"] | - | - | - | - | - | - | - | -
IF-INPUT-044 | input | $.facts.restrictions[].source_end | ["string","null"] | - | - | - | - | - | - | - | -
IF-INPUT-045 | input | $.facts.restrictions[].evidence_ref | "string" | - | - | - | - | - | - | - | -
IF-INPUT-046 | input | $.history | "array" | - | - | - | - | - | - | - | "Accepted prior versions, explicit links only. Empty is a valid root history; absent referenced ID is missing proof. Each entry represents one accepted immutable source version."
IF-INPUT-047 | input | $.history[] | "object" | ["source_sha256","notice","facts"] | - | - | - | - | - | false | -
IF-INPUT-048 | input | $.history[].source_sha256 | "string" | - | - | - | - | - | "^[0-9a-f]{64}$" | - | -
IF-INPUT-049 | input | $.history[].notice | "object" | ["notice_id","prior_notice_id","status","notice_type"] | - | - | - | - | - | false | -
IF-INPUT-050 | input | $.history[].notice.notice_id | "integer" | - | - | - | - | - | - | - | -
IF-INPUT-051 | input | $.history[].notice.prior_notice_id | ["integer","null"] | - | - | - | - | - | - | - | -
IF-INPUT-052 | input | $.history[].notice.status | "string" | - | ["INITIATE","SUPERSEDE","TERMINATE"] | - | - | - | - | - | "Source notice status."
IF-INPUT-053 | input | $.history[].notice.notice_type | "string" | - | - | - | - | - | - | - | "Source Notice Type Desc (1), with subtype retained in source fields."
IF-INPUT-054 | input | $.history[].facts | "object" | ["content_kind","services","availability","locations","quantities","operational_assertions","start_time","end_time","time_basis"] | - | - | - | - | - | false | -
IF-INPUT-055 | input | $.history[].facts.content_kind | "string" | - | ["ADMINISTRATIVE","INFORMATIONAL","RESTRICTION","RESTORATION","UNKNOWN"] | - | - | - | - | - | "Normalized source content, not materiality or a signal label."
IF-INPUT-056 | input | $.history[].facts.services | "array" | - | - | - | - | - | - | - | -
IF-INPUT-057 | input | $.history[].facts.services[] | "string" | - | ["PRIMARY_FIRM","SECONDARY_FIRM","NO_NOTICE_FIRM","INTERRUPTIBLE","AOR_ITS","UNKNOWN"] | - | - | - | - | - | "Service affected; preserve source distinctions in assertions."
IF-INPUT-058 | input | $.history[].facts.availability | "string" | - | ["UNAVAILABLE","PRIMARY_ONLY","PARTIAL","AVAILABLE","UNKNOWN"] | - | - | - | - | - | "Source restriction, not an impact score."
IF-INPUT-059 | input | $.history[].facts.locations | "array" | - | - | - | - | - | - | - | -
IF-INPUT-060 | input | $.history[].facts.locations[] | "object" | ["kind","value","evidence_ref"] | - | - | - | - | - | false | -
IF-INPUT-061 | input | $.history[].facts.locations[].kind | "string" | - | ["SEGMENT","ZONE","SYSTEM","LOC","COMPRESSOR_STATION"] | - | - | - | - | - | "Source identifier kind, never proof of curtailment by itself."
IF-INPUT-062 | input | $.history[].facts.locations[].value | "string" | - | - | - | - | - | - | - | "Exact identifier; constraint point distinguished from root cause."
IF-INPUT-063 | input | $.history[].facts.locations[].evidence_ref | "string" | - | - | - | - | - | - | - | "Source span/page/field reference."
IF-INPUT-064 | input | $.history[].facts.quantities | "array" | - | - | - | - | - | - | - | -
IF-INPUT-065 | input | $.history[].facts.quantities[] | "object" | ["kind","value","unit","basis","evidence_ref"] | - | - | - | - | - | false | -
IF-INPUT-066 | input | $.history[].facts.quantities[].kind | "string" | - | ["SCHEDULED_TO_PCT_MDQ","HOURLY_LIMIT_PCT","ABSOLUTE_CURTAILMENT","UNAVAILABLE"] | - | - | - | - | - | "Kinds must not be interchanged."
IF-INPUT-067 | input | $.history[].facts.quantities[].value | ["number","null"] | - | - | - | 0 | - | - | - | -
IF-INPUT-068 | input | $.history[].facts.quantities[].unit | "string" | - | ["PERCENT_MDQ","PERCENT_ENTITLEMENT","MMBtu","Dth","NONE"] | - | - | - | - | - | "Null quantity for categorical UNAVAILABLE uses NONE; absolute energy needs stated basis."
IF-INPUT-069 | input | $.history[].facts.quantities[].basis | "string" | - | - | - | - | - | - | - | "Scheduled-to percentage is remaining allowed capacity; never infer absolute volume without source capacity/time basis."
IF-INPUT-070 | input | $.history[].facts.quantities[].evidence_ref | "string" | - | - | - | - | - | - | - | "Exact supporting source span."
IF-INPUT-071 | input | $.history[].facts.operational_assertions | "array" | - | - | - | - | - | - | - | -
IF-INPUT-072 | input | $.history[].facts.operational_assertions[] | "string" | - | - | - | - | - | - | - | "Source-grounded operational assertion with source span; preserve material body facts, not capture metadata."
IF-INPUT-073 | input | $.history[].facts.start_time | ["string","null"] | - | - | - | - | - | - | - | "ISO 8601 with explicit UTC offset when known; null means absent/unresolved; never silently assume local timezone."
IF-INPUT-074 | input | $.history[].facts.end_time | ["string","null"] | - | - | - | - | - | - | - | "ISO 8601 with explicit UTC offset when known; null means absent/unresolved; never silently assume local timezone."
IF-INPUT-075 | input | $.history[].facts.time_basis | "string" | - | ["UTC","UNRESOLVED"] | - | - | - | - | - | "Explicit accepted time interpretation; source timezone retained in source fields."
IF-INPUT-076 | input | $.history[].facts.restrictions | "array" | - | - | - | - | - | - | - | "Per-row source associations. Optional for prior v1 normalized witnesses; required from the retained-capture normalizer."
IF-INPUT-077 | input | $.history[].facts.restrictions[] | "object" | ["service","availability","restriction_type","status","location_index","source_start","source_end","evidence_ref"] | - | - | - | - | - | false | -
IF-INPUT-078 | input | $.history[].facts.restrictions[].service | "string" | - | ["PRIMARY_FIRM","SECONDARY_FIRM","NO_NOTICE_FIRM","INTERRUPTIBLE","AOR_ITS","UNKNOWN"] | - | - | - | - | - | -
IF-INPUT-079 | input | $.history[].facts.restrictions[].availability | "string" | - | ["UNAVAILABLE","PRIMARY_ONLY","PARTIAL","AVAILABLE","UNKNOWN"] | - | - | - | - | - | -
IF-INPUT-080 | input | $.history[].facts.restrictions[].restriction_type | "string" | - | - | - | - | - | - | - | -
IF-INPUT-081 | input | $.history[].facts.restrictions[].status | "string" | - | - | - | - | - | - | - | -
IF-INPUT-082 | input | $.history[].facts.restrictions[].location_index | ["integer","null"] | - | - | - | - | - | - | - | -
IF-INPUT-083 | input | $.history[].facts.restrictions[].source_start | ["string","null"] | - | - | - | - | - | - | - | -
IF-INPUT-084 | input | $.history[].facts.restrictions[].source_end | ["string","null"] | - | - | - | - | - | - | - | -
IF-INPUT-085 | input | $.history[].facts.restrictions[].evidence_ref | "string" | - | - | - | - | - | - | - | -
IF-INPUT-086 | input | $.reference_time | "string" | - | - | - | - | - | - | - | "Required ISO 8601 UTC timestamp supplied by caller; never substitute machine clock."
IF-INPUT-087 | input | $.evidence | "object" | ["extraction_usable","helpers_usable","contradictory","references"] | - | - | - | - | - | false | -
IF-INPUT-088 | input | $.evidence.extraction_usable | "boolean" | - | - | - | - | - | - | - | -
IF-INPUT-089 | input | $.evidence.helpers_usable | "boolean" | - | - | - | - | - | - | - | "Necessary helper result available; not a supplied impact/materiality answer."
IF-INPUT-090 | input | $.evidence.contradictory | "boolean" | - | - | - | - | - | - | - | "Known unresolved source conflicts, not permission to skip the classifier checking obvious conflicts."
IF-INPUT-091 | input | $.evidence.references | "array" | - | - | - | - | - | - | - | -
IF-INPUT-092 | input | $.evidence.references[] | "string" | - | - | - | - | - | - | - | "Retained extraction/model/tool request/response or source evidence references, sanitized."
IF-INPUT-093 | input | $.normalization_trace | "array" | - | - | - | - | - | - | - | -
IF-INPUT-094 | input | $.normalization_trace[] | "object" | ["field","source_basis","source_value","normalized_value","supplied_by","unknown_handling"] | - | - | - | - | - | true | -
IF-INPUT-095 | input | $.normalization_trace[].field | "string" | - | - | - | - | - | - | - | -
IF-INPUT-096 | input | $.normalization_trace[].source_basis | "string" | - | - | - | - | - | - | - | -
IF-INPUT-097 | input | $.normalization_trace[].source_value | - | - | - | - | - | - | - | - | -
IF-INPUT-098 | input | $.normalization_trace[].normalized_value | - | - | - | - | - | - | - | - | -
IF-INPUT-099 | input | $.normalization_trace[].supplied_by | "string" | - | ["model","source_parser","human","normalizer","retained_history","unknown"] | - | - | - | - | - | -
IF-INPUT-100 | input | $.normalization_trace[].unknown_handling | "string" | - | - | - | - | - | - | - | -
IF-OUTPUT-001 | output | $ | "object" | ["notice_id","source_sha256","classification","disposition","reason_codes","evidence_refs","recommendation_allowed"] | - | - | - | - | - | false | -
IF-OUTPUT-002 | output | $.notice_id | "integer" | - | - | - | - | - | - | - | -
IF-OUTPUT-003 | output | $.source_sha256 | "string" | - | - | - | - | - | "^[0-9a-f]{64}$" | - | -
IF-OUTPUT-004 | output | $.classification | "string" | - | ["SIGNAL_CANDIDATE","NON_SIGNAL","UNRESOLVED"] | - | - | - | - | - | "A proposal, never authorization."
IF-OUTPUT-005 | output | $.disposition | "string" | - | ["CANDIDATE_ONLY","NO_SIGNAL","SUPPRESSED","REVIEW_REQUIRED","ERROR"] | - | - | - | - | - | "Distinct from harness PASS/FAIL/ERROR/UNKNOWN."
IF-OUTPUT-006 | output | $.reason_codes | "array" | - | - | - | - | 1 | - | - | -
IF-OUTPUT-007 | output | $.reason_codes[] | "string" | - | - | - | - | - | - | - | "Rule ID or explicit input-contract error."
IF-OUTPUT-008 | output | $.evidence_refs | "array" | - | - | - | - | - | - | - | -
IF-OUTPUT-009 | output | $.evidence_refs[] | "string" | - | - | - | - | - | - | - | -
IF-OUTPUT-010 | output | $.recommendation_allowed | - | - | - | false | - | - | - | - | "This classifier has no D6 authorization interface; publication is a separate existing component."
```

## Fixed settings

Finite normalization maps, accepted date formats and representation bounds. These preserve existing policy; absent source facts remain unknown.

```spec-settings
{
  "version": 6,
  "policy_id": "assessment-v4-timezone-separation-20260928",
  "bounds": {"OUTPUT-002.maximum_mdq": 100, "OUTPUT-002.minimum": 0, "OUTPUT-001.confidence_max": 1},
  "bound_source": "Existing representation bounds, not materiality cutoffs; compiler validates finite values and gate checks use this spec.",
  "formats": {"supported": ["text/html", "application/vnd.ngpl.normalized+json"], "unsupported": ["application/pdf", "text/plain", "application/octet-stream"], "meaning": "HTML is parsed from saved bytes; no PDF/OCR/attachment extraction. Normalized classifier does not implement HTML ingestion."},
  "history_statuses": {"root": ["INITIATE"], "linked": ["INITIATE", "SUPERSEDE", "TERMINATE"]},
  "owners": ["Thomas Hand"],
  "unresolved_time_margin_hours": 14,
  "acceptance": {"max_missed_positives_per_capture": 2, "max_false_positives_per_capture": 0, "review_satisfies": ["SIGNAL-002", "SIGNAL-004"]},
  "sets": {"FIRM_SERVICES": ["PRIMARY_FIRM", "SECONDARY_FIRM", "NO_NOTICE_FIRM"], "RESTRICTED_AVAILABILITY": ["UNAVAILABLE", "PRIMARY_ONLY", "PARTIAL"], "INFORMATION_KINDS": ["ADMINISTRATIVE", "INFORMATIONAL"], "UNCHANGED_PREDECESSOR_STATUSES": ["INITIATE", "SUPERSEDE"]},
  "normalization": {"boundary": "Map retained extracted assertions with provenance. Preserve each service/restriction/location/interval association, including unknown rows. Scalar mixed availability remains UNKNOWN, but known per-row evidence is never erased. Never use is_signal, confidence, labels or a classification as input evidence. No timezone inferred.", "services": {"PRIMARY_FIRM": "PRIMARY_FIRM", "SECONDARY_FIRM": "SECONDARY_FIRM", "SECONDARY_INPATH_FIRM": "SECONDARY_FIRM", "SECONDARY_OUTPATH_FIRM": "SECONDARY_FIRM", "NO_NOTICE": "NO_NOTICE_FIRM", "INTERRUPTIBLE": "INTERRUPTIBLE", "AOR_ITS": "AOR_ITS"}, "availability": {"UNAVAILABLE": "UNAVAILABLE", "PRIMARY_ONLY": "PRIMARY_ONLY", "SCHEDULED_TO_PCT_MDQ": "PARTIAL", "HOURLY_LIMIT_PCT": "PARTIAL"}, "locations": {"loc_code": "LOC", "segment": "SEGMENT", "compressor_station": "COMPRESSOR_STATION", "zone": "ZONE", "system": "SYSTEM"}, "quantities": {"SCHEDULED_TO_PCT_MDQ": {"kind": "SCHEDULED_TO_PCT_MDQ", "unit": "PERCENT_MDQ"}, "HOURLY_LIMIT_PCT": {"kind": "HOURLY_LIMIT_PCT", "unit": "PERCENT_ENTITLEMENT"}}, "content": {"information_only": "INFORMATIONAL", "restrictions": "RESTRICTION", "otherwise": "UNKNOWN"}, "helper_values": {"llm_assess_curtailment_impact": ["large", "medium", "small"], "llm_is_supersede_material": [true, false]}},
  "quantity_units": {"SCHEDULED_TO_PCT_MDQ": ["PERCENT_MDQ"], "HOURLY_LIMIT_PCT": ["PERCENT_ENTITLEMENT"], "ABSOLUTE_CURTAILMENT": ["MMBtu", "Dth"], "UNAVAILABLE": ["NONE"]},
  "boundary": "Source-grounded normalized facts -> candidate only, including when source timezone is UNKNOWN. Unknown timezone blocks automatic current/future actionability and recommendation authorization, requiring REVIEW_REQUIRED. No timezone is inferred.",
  "rule_requirements": {"BR-FORMAT": ["INPUT-002"], "BR-SEMANTICS": ["SAFETY-001", "INPUT-002"], "BR-CONTRADICTION": ["INPUT-002"], "BR-HISTORY": ["HISTORY-002"], "BR-UNCHANGED": ["STATE-004"], "BR-ROUTINE": ["SIGNAL-002"], "BR-HISTORICAL": ["SIGNAL-003"], "BR-FIRM": ["SIGNAL-001", "SIGNAL-003"], "BR-UNRESOLVED": ["SIGNAL-001", "SIGNAL-004"]},
  "state_safety": {"version": 1, "policy_id": "assessment-v4-timezone-separation-20260928", "scope": "bounded initial outbound recommendation decisions; not delivery or complete lifecycle acceptance", "basis": "spec.md D1-D3/D5-D6; owner behavioral-improvement request", "reference_time": "2026-01-15T12:00:00+00:00", "synthetic": true, "requirements": ["INPUT-002", "STATE-003", "STATE-004", "STATE-006", "HISTORY-002", "SAFETY-001", "SIGNAL-002"], "relations": {"initial": {"field": "initial_count", "kind": "behavior"}, "disposition": {"requirement": "OUTPUT-001", "field": "disposition", "kind": "output_contract"}, "reason": {"requirement": "OUTPUT-001", "field": "reason", "kind": "output_contract"}, "semantic_safety": {"requirement": "SAFETY-001", "field": "semantic_safety", "kind": "behavior"}}},
  "timezone": {"decision": "TZ-NGPL-002", "status": "owner-requested-no-inference", "rejected_proposal": "TZ-NGPL-001", "rule": "Unknown source timezone permits source-grounded candidate classification only; actionability and authorization require review. Explicit trusted source offsets permit temporal evaluation.", "active_default": null},
  "date_formats": ["%m/%d/%Y %I:%M:%S%p", "%m/%d/%Y %I:%M:%S %p", "%m/%d/%Y", "ISO8601"]
}
```

## Generated consequences

Run `make consequences SPEC=path/to/proposal.md BASE=spec.md` to see changed outcomes, per-capture label tradeoffs, rule reach and the first failed condition for every nonmatch. The report shows proposal and baseline hashes, unresolved checks and input problems. No receipt or active generated artifact is changed. `make gate` separately evaluates the adopted spec and refuses stale review.
