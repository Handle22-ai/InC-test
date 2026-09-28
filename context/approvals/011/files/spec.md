# Behavioral specification — assessment version 3

Policy identity: `assessment-v3-owner-20260928`. Original lifecycle approval: [exact message](evidence/policy/20260927T010449.918426Z/owner-approval.txt); [ADR 006](context/decisions/006-assessment-lifecycle-policy.md). The original challenge defines submission obligations. Exact event identity, refusal, timing, adjudication and retention choices below are owner-approved assessment assumptions, not approval by InCommodities or a trading desk.

Normative companions: [system fields/interfaces](docs/system-contract.md), [canonical structured behavior](requirements/behavior.yaml), [normalized input](requirements/normalized-input.schema.json), and [proposal output](requirements/normalized-output.schema.json). The structured behavior owns supported rule conditions, precedence and actions; its [human table](docs/signal-contract.md) and state-safety view are generated/strictly validated. Pending rule choices are not active. D1–D6 remain governing policy.

Purpose: classify operational NGPL notices for trading relevance and extract source-grounded restrictions with explainable state. This contract is implementation-independent. No trading execution is authorized.

Scope: saved notices, observable decisions and current storage, plus specified lifecycle refusal/alert/history obligations. Implemented behavior and available checks are identified per requirement and in [coverage](evidence/coverage.md). Approval does not imply implementation or evidence. The separate bounded recommendation candidate now implements initial-decision memory, unchanged-revision suppression and selected failure/history refusals. Delivery, material updates, reconciliation and complete historical decision retrieval remain unimplemented; full lifecycle proof is still unavailable.

Three gates remain contracts/invariants, trading behavior and regression/change. Harness PASS/FAIL/ERROR/UNKNOWN, execution-domain classifications and application dispositions are distinct. A completed evaluation is not application acceptance. Historical labels are evaluation-only; they never authorize an alert or supply an implementation answer.

Historical policy/source snapshots and runs remain unchanged under their original identities. Re-evaluating frozen captures under this policy creates a new identified check execution, not a new model prediction or retrospective recertification. Assumption scope: [context/assumptions.md](context/assumptions.md).

## Approved lifecycle decisions

D1–D6 below are normative owner decisions; they do not replace requirement IDs. Broad challenge obligations and exact assessment assumptions are distinguished in ADR 006.

### D1 — Already-signaled identity and memory

Within the bounded NGPL assessment, identify a notice version by pipeline, notice ID and source-content hash. Identify an event by pipeline and the root notice ID of its complete, acyclic, explicit prior-notice chain. Do not infer identity from ID order, subject or text similarity. An incomplete chain or disputed cross-chain identity blocks automatic alerting, but not retention of the input or an explicitly uncertain candidate for review; retain any human-approved correlation and its evidence. Issue at most one initial alert per resolved event. Identify a material update by that event and its distinct source notice version. Identical replay or same-source re-extraction must not create another alert revision. Persist each alert key, decision reference, delivery attempt and acknowledgement across restarts. Retry with the same key; unconfirmed delivery stays uncertain. Require receiver idempotency before claiming duplicate-free delivery. Retain this memory without automatic expiry throughout the assessment; production retention requires separate approval.

### D2 — Revisions and material changes

Compare a revision to its explicit predecessor using source-grounded constraints, services/directions, restriction kind/value/unit, operational status, effective interval and operational assertions in the body. Ignore IDs, links, capture/scrape metadata and whitespace-only presentation changes for materiality. If operational facts are unchanged, classify the supersede as nonmaterial and issue no new alert. Other changes require a recorded MATERIAL, NONMATERIAL or UNRESOLVED decision under D6; a changed number alone is not a materiality threshold. If a resolved event has no prior initial-alert record or attempt, its first MATERIAL and actionable decision may create the initial alert under D1. If an initial-alert record exists, a qualifying material revision produces a linked update. An unacknowledged initial attempt reuses its existing key; replay must not create another initial alert. UNRESOLVED changes are REVIEW_REQUIRED. A lift/termination must compare the prior restriction; do not generalize one rule from the two labeled termination examples. For the bounded same-ID/different-source-content case, retain the conflicting capture as evidence, preserve the last accepted snapshot, and require review before changed content can authorize alerting. Do not automatically overwrite, merge, discard or reconcile the conflict. Automatic reconciliation remains outside the implemented storage scope; this specified refusal boundary does not establish a complete source-version service.

### D3 — Missing, late and out-of-order notices

Record source event/publication times with stated timezone, ingestion time, and an explicitly supplied timezone-aware UTC reference time for each decision. Ambiguous time meaning remains unknown; do not substitute the machine/model clock. Missing ancestors, cycles or conflicting successor ordering defer alerting and retain the gap. When history arrives, create a new reconciliation decision following explicit prior links; retain the original uncertain decision. For the same accepted source versions, normalized facts, reference time and approved adjudications, the final event view must be order-independent. Do not expect independently regenerated stochastic model outputs to be identical. Actual delivery attempts remain historical and use D1 keys; final-view order independence does not imply identical real-time delivery histories. A restriction ending at or before the reference time is historical-only for a new disruption alert. Current or future intervals may be actionable after D6; assume no arbitrary age or advance-notice cutoff. Unknown time bounds and point changes such as a lift require a human actionability decision at that reference time. Historical label evaluation stays separate: never rescore it against today or treat it as permission for stale delivery. For bounded proposal classification, a source-grounded operational firm-service disruption may be SIGNAL_CANDIDATE when the source timestamp lacks a trusted timezone. Unresolved source timezone remains explicit and prohibits automatic current/future actionability and recommendation authorization; the actionability/authorization boundary returns REVIEW_REQUIRED. recommendation_allowed remains false. No NGPL timezone, UTC conversion, lateness cutoff or desk SLA is inferred. Resolved historical-only intervals and clock-dependent revision/actionability decisions retain time precedence.

### D4 — History needed to explain a decision

Give every decision an immutable identity. Retrieve by that identity the exact input bytes/hash, extracted facts, prior versions and missing-history observations available then, reference/ingestion times, outcome/reasons, human adjudications, spec/rule/code/ dependency/model/prompt identities, relevant model execution evidence, and delivery key/attempt/acknowledgement when applicable. Later information and corrections create linked decisions without replacing their evidence or presenting later facts as known at an earlier decision. Preserve missing-history observations as missingness; do not backfill later facts into an old explanation. Retain failed/deferred decisions too. Do not automatically prune assessment records or retain credentials. Production retention or redaction needs separate approval. Current snapshot readback alone is not historical decision evidence.

### D5 — Malformed input and failures

Empty, structurally invalid, contradictory or unsupported input must yield an explicit uncertain/error disposition, reason code and retained input evidence, not a successful negative classification or alert. Validation failure leaves the last valid snapshot unchanged. Invalid input or unresolved contradictions use UNKNOWN with a distinguishing reason; model/provider, environment and harness failures retain their separate existing classifications. Missing an optional strong-signal field alone is not malformed input. Conflicting identity, impossible quantities and incompatible operational assertions require correction/review, not fabricated facts. Unresolved timestamp meaning requires review at the actionability/authorization boundary; it does not alone prohibit a source-grounded firm-service candidate under D3. A corrected execution is a new linked decision; retain the failed attempt. Classification is unscorable only where the necessary semantic result is unavailable. Structural, persistence, uncertainty and failure-handling requirements remain evaluable when their required observations exist. Application dispositions are distinct from harness PASS/FAIL/ERROR/UNKNOWN statuses and execution-domain classifications. A successful API response with an unusable verdict must not silently become a valid negative or small-impact decision.

### D6 — Materiality, oracles and alert authorization

For new assessment cases outside the frozen label oracle, require a named human's recorded MATERIAL/NONMATERIAL/UNRESOLVED adjudication with cited source evidence. MATERIAL must identify a meaningful expected effect on gas flow or regional prices; NONMATERIAL must explain routine/administrative content or why a capacity change is minor. Unsupported judgement is UNRESOLVED and withholds an alert. Models may propose facts/reasons but may not approve this adjudication. Critical/unplanned status, planned material impact, segment, quantity and geography are evidence to weigh, not a mandatory all-fields checklist or numeric score cutoff. Extract stated values with units and meaning; absent values stay unknown. Do not convert scheduled-to MDQ percentages into absolute curtailed volume without the required source capacity/basis. Keep the fixed 14 labels as an evaluation oracle only. Labels do not authorize runtime alerts and must not be supplied as the implementation's answer to classification. Assessment alerting requires recorded approval and satisfied identity, history and actionability conditions; model proposals and known test labels are not approval. Under this owner approval, adopt the existing source-based firm scheduled-to MDQ percentage, constraint-segment and named-zone annotations as binding checks only for their annotated cases. Adopt unchanged-operational-body supersede checks only when the prior is complete and differences are confined to revision metadata or whitespace. Before applying binding scope, verify that included annotations have traceable source support; unsupported annotations remain unapproved or not evaluated and must be listed. This approval does not mean the owner personally audited each annotation. Neither oracle certifies unannotated fields, absolute curtailed volume or real material revisions. Apply the approved scope in new identified runs; old exploratory conclusions keep their original governance and must not be recertified retrospectively.

## INPUT-001 — Input identity

Requirement: Preserve the input notice identity and the content used for a decision.

Rationale: Decisions must refer to the actual notice.

Severity: critical

Inputs / preconditions: A readable notice with an explicit identity.

Expected behavior: Output ID equals input ID; original input hash is retained.

Forbidden behavior: Silent identity substitution.

Required evidence: case input and hash; observed output/state; check result and requirement ID

Deterministic or evaluative: deterministic

Governance: grounded

Basis: inherited/design.md; challenge v5; exact existing contract retained

Approval: existing-contract

Enforcement: binding

Implementation status: implemented_bounded

Check status: executable_scoped

Demonstrated evidence: evidence/coverage.md (per-policy evidence; approval does not establish behavior)

Decisions: Existing contract retained

Validation: Gate 1 / contract / identity

Source: spec.md

Policy: assessment-v3-owner-20260928

Executable parameters: {}

## INPUT-002 — Invalid input

Requirement: Invalid or contradictory input must have an explicit uncertain/error disposition, retained evidence and preservation of the last valid snapshot.

Rationale: Prevent fabricated actionable facts.

Severity: critical

Inputs / preconditions: Invalid, empty, contradictory or unsupported input.

Expected behavior: Apply D5: retain input and reason; prohibit a successful negative or alert from invalidity; preserve valid state. Evaluate each requirement where its observations exist.

Forbidden behavior: Silent valid-negative/small-impact fallback, fabricated facts or loss of the last valid snapshot.

Required evidence: case input and hash; observed output/state; check result and requirement ID

Deterministic or evaluative: deterministic

Governance: assessment-assumption

Basis: Challenge v5 pp. 2, 4–5: broad lifecycle/refusal/evidence obligations; exact bounded behavior is an owner-approved assessment assumption under ADR 006.

Approval: owner-approved

Enforcement: binding

Implementation status: partial

Check status: not_available

Demonstrated evidence: evidence/coverage.md (per-policy evidence; approval does not establish behavior)

Decisions: D5

Validation: Gate 1 / contract / deferred

Source: spec.md

Policy: assessment-v3-owner-20260928

Executable parameters: {}

## OUTPUT-001 — Decision contract

Requirement: Every successful decision exposes identity, binary signal classification, bounded numeric confidence, reasons, and extraction collections.

Rationale: Consumers need a stable observable contract.

Severity: critical

Inputs / preconditions: Successful processing.

Expected behavior: Finite confidence in [0,1], binary signal, nonempty reasons, lists for locations and restrictions.

Forbidden behavior: Missing fields, NaN, infinity or out-of-range confidence.

Required evidence: case input and hash; observed output/state; check result and requirement ID

Deterministic or evaluative: deterministic

Governance: grounded

Basis: inherited/design.md; challenge v5; exact existing contract retained

Approval: owner-approved

Enforcement: binding

Implementation status: implemented_bounded

Check status: executable_scoped

Demonstrated evidence: evidence/coverage.md (per-policy evidence; approval does not establish behavior)

Decisions: D5

Validation: Gate 1 / contract / decision_shape

Source: spec.md

Policy: assessment-v3-owner-20260928

Executable parameters: {"confidence_max": 1, "confidence_min": 0}

## OUTPUT-002 — Quantities and units

Requirement: Numeric restrictions must be finite and nonnegative, carry a unit, and distinguish scheduled-to percent MDQ from volume reduction.

Rationale: Wrong quantities invert trading meaning.

Severity: high

Inputs / preconditions: Extracted restriction rows.

Expected behavior: Scheduled-to percent MDQ in [0,100]; a nonnumeric unavailability restriction may have null value/unit.

Forbidden behavior: Interpreting 55% scheduled as 55% reduction or imposing [0,100] on hourly entitlement percentages.

Required evidence: case input and hash; observed output/state; check result and requirement ID

Deterministic or evaluative: deterministic

Governance: grounded

Basis: inherited/design.md; challenge v5; exact existing contract retained

Approval: owner-approved

Enforcement: binding

Implementation status: implemented_bounded

Check status: executable_scoped

Demonstrated evidence: evidence/coverage.md (per-policy evidence; approval does not establish behavior)

Decisions: D5, D6

Validation: Gate 1 / contract / quantities

Source: spec.md

Policy: assessment-v3-owner-20260928

Executable parameters: {"maximum_mdq": 100, "minimum": 0}

## OUTPUT-003 — Restriction location linkage

Requirement: Each extracted restriction must reference a location belonging to the same notice.

Rationale: Prevents assignment to the wrong constraint.

Severity: high

Inputs / preconditions: Extracted rows.

Expected behavior: Unique location indexes and valid restriction-to-location joins.

Forbidden behavior: Orphan restrictions or cross-notice joins.

Required evidence: case input and hash; observed output/state; check result and requirement ID

Deterministic or evaluative: deterministic

Governance: grounded

Basis: inherited/design.md; challenge v5; exact existing contract retained

Approval: owner-approved

Enforcement: binding

Implementation status: implemented_bounded

Check status: executable_scoped

Demonstrated evidence: evidence/coverage.md (per-policy evidence; approval does not establish behavior)

Decisions: D5

Validation: Gate 1 / invariant / links

Source: spec.md

Policy: assessment-v3-owner-20260928

Executable parameters: {}

## OUTPUT-004 — Volume extraction

Requirement: Extract the stated firm scheduled-to MDQ percentage on annotated notices.

Rationale: Measures semantic extraction independently of scoring.

Severity: high

Inputs / preconditions: An annotated firm percentage is present.

Expected behavior: Equal the supplied HTML percentage, including field mutation.

Forbidden behavior: Missing or numerically incorrect firm percentage.

Required evidence: case input and hash; observed output/state; check result and requirement ID

Deterministic or evaluative: evaluative

Governance: assessment-assumption

Basis: Challenge v5 pp. 2, 4–5: broad lifecycle/refusal/evidence obligations; exact bounded behavior is an owner-approved assessment assumption under ADR 006.

Approval: owner-approved

Enforcement: binding

Implementation status: implemented_bounded

Check status: executable_scoped

Demonstrated evidence: evidence/coverage.md (per-policy evidence; approval does not establish behavior)

Decisions: D6

Validation: Gate 2 / labeled_eval / field_values

Source: spec.md

Policy: assessment-v3-owner-20260928

Executable parameters: {"field": "firm_mdq", "oracle_support": "requirements/oracle-support.json"}

## OUTPUT-005 — Segment extraction

Requirement: Retain annotated affected constraint segment identifiers.

Rationale: Identifiable constraints are required for decisions.

Severity: high

Inputs / preconditions: Annotated segment in supplied HTML.

Expected behavior: Expected segment appears in extracted locations.

Forbidden behavior: Missing or incorrect constraint segment.

Required evidence: case input and hash; observed output/state; check result and requirement ID

Deterministic or evaluative: evaluative

Governance: assessment-assumption

Basis: Challenge v5 pp. 2, 4–5: broad lifecycle/refusal/evidence obligations; exact bounded behavior is an owner-approved assessment assumption under ADR 006.

Approval: owner-approved

Enforcement: binding

Implementation status: implemented_bounded

Check status: executable_scoped

Demonstrated evidence: evidence/coverage.md (per-policy evidence; approval does not establish behavior)

Decisions: D6

Validation: Gate 2 / labeled_eval / field_values

Source: spec.md

Policy: assessment-v3-owner-20260928

Executable parameters: {"field": "segments", "oracle_support": "requirements/oracle-support.json"}

## OUTPUT-006 — Geography extraction

Requirement: Retain annotated geographic zones without treating a name alone as proof of curtailment.

Rationale: Geography supports relevance but does not establish impact.

Severity: high

Inputs / preconditions: Annotated zone in supplied HTML.

Expected behavior: Expected zone appears in location output; classification checked independently.

Forbidden behavior: Loss of annotated zone.

Required evidence: case input and hash; observed output/state; check result and requirement ID

Deterministic or evaluative: evaluative

Governance: assessment-assumption

Basis: Challenge v5 pp. 2, 4–5: broad lifecycle/refusal/evidence obligations; exact bounded behavior is an owner-approved assessment assumption under ADR 006.

Approval: owner-approved

Enforcement: binding

Implementation status: implemented_bounded

Check status: executable_scoped

Demonstrated evidence: evidence/coverage.md (per-policy evidence; approval does not establish behavior)

Decisions: D6

Validation: Gate 2 / labeled_eval / field_values

Source: spec.md

Policy: assessment-v3-owner-20260928

Executable parameters: {"field": "zones", "oracle_support": "requirements/oracle-support.json"}

## SIGNAL-001 — Trading relevance and labeled evaluation

Requirement: Classify notices from source-supported operational effects on gas flow or regional prices; routine, administrative and minor changes are not signals, and insufficient evidence remains unresolved.

Rationale: Makes baseline behavior independently assessable.

Severity: critical

Inputs / preconditions: Accepted source facts and sufficient semantic evidence; frozen labels apply only to their separate historical evaluation.

Expected behavior: Apply the supported behavioral contract without label lookup; report the frozen 14-case evaluation separately, including disagreements and unscorable cases. Labels never authorize runtime recommendations.

Forbidden behavior: Relabeling examples to match implementation or treating execution failures as negatives.

Required evidence: case input and hash; observed output/state; check result and requirement ID

Deterministic or evaluative: evaluative

Governance: grounded

Basis: inherited/design.md; challenge v5; exact existing contract retained

Approval: owner-approved

Enforcement: binding

Implementation status: partial

Check status: executable_scoped

Demonstrated evidence: evidence/coverage.md (per-policy evidence; approval does not establish behavior)

Decisions: D6

Validation: Gate 2 / labeled_eval / classification

Source: spec.md

Policy: assessment-v3-owner-20260928

Executable parameters: {}

## SIGNAL-002 — Routine and administrative control

Requirement: Routine administrative, IT and plan-index notices without operational flow restrictions must not signal.

Rationale: Avoid false trading signals from routine postings.

Severity: critical

Inputs / preconditions: Routine administrative, IT or plan-index source content without an operational flow restriction.

Expected behavior: No signal for routine content without operational restriction; supplied selected examples remain evaluation data.

Forbidden behavior: Outage or maintenance words alone create a signal.

Required evidence: case input and hash; observed output/state; check result and requirement ID

Deterministic or evaluative: evaluative

Governance: grounded

Basis: inherited/design.md; challenge v5; exact existing contract retained

Approval: owner-approved

Enforcement: binding

Implementation status: implemented_bounded

Check status: executable_scoped

Demonstrated evidence: evidence/coverage.md (per-policy evidence; approval does not establish behavior)

Decisions: D6

Validation: Gate 2 / negative_control / classification

Source: spec.md

Policy: assessment-v3-owner-20260928

Executable parameters: {"ids": [46604, 46775, 46818]}

## SIGNAL-003 — Critical disruption recall

Requirement: Detect the labeled unplanned force-majeure disruption.

Rationale: Missing unplanned flow disruption is a high-risk outcome.

Severity: critical

Inputs / preconditions: A source-supported material critical or unplanned operational disruption with sufficient semantic evidence.

Expected behavior: Retain supported disruption candidates; typical signal characteristics are evidence, not an all-fields checklist. Frozen critical-case recall is a separate scoped evaluation.

Forbidden behavior: Silent missed critical disruption.

Required evidence: case input and hash; observed output/state; check result and requirement ID

Deterministic or evaluative: evaluative

Governance: grounded

Basis: inherited/design.md; challenge v5; exact existing contract retained

Approval: owner-approved

Enforcement: binding

Implementation status: implemented_bounded

Check status: executable_scoped

Demonstrated evidence: evidence/coverage.md (per-policy evidence; approval does not establish behavior)

Decisions: D6

Validation: Gate 2 / labeled_eval / classification

Source: spec.md

Policy: assessment-v3-owner-20260928

Executable parameters: {"ids": [46864]}

## SIGNAL-004 — Termination and prior context

Requirement: Evaluate lifting a prior material restriction using available prior context and preserve case-specific termination labels.

Rationale: A lift can matter as much as onset.

Severity: high

Inputs / preconditions: A lift or termination with its explicit prior restriction and available source evidence.

Expected behavior: Compare prior operational context; do not always suppress or always inherit signal classification. Unresolved materiality/history requires review; frozen examples remain evaluation-only.

Forbidden behavior: A generic policy inferred from two conflicting-looking examples without human clarification.

Required evidence: case input and hash; observed output/state; check result and requirement ID

Deterministic or evaluative: evaluative

Governance: grounded

Basis: inherited/design.md; challenge v5; exact existing contract retained

Approval: owner-approved

Enforcement: binding

Implementation status: partial

Check status: executable_scoped

Demonstrated evidence: evidence/coverage.md (per-policy evidence; approval does not establish behavior)

Decisions: D2, D3, D6

Validation: Gate 2 / labeled_eval / classification

Source: spec.md

Policy: assessment-v3-owner-20260928

Executable parameters: {"ids": [46732, 46725]}

## STATE-001 — Durable state

Requirement: Successfully processed notices and their child records must survive database close and reopen.

Rationale: Restart must not lose evidence.

Severity: critical

Inputs / preconditions: An acknowledged database insertion.

Expected behavior: Reopened rows equal saved state; current notice exists.

Forbidden behavior: Success with lost or absent rows.

Required evidence: case input and hash; observed output/state; check result and requirement ID

Deterministic or evaluative: deterministic

Governance: grounded

Basis: inherited/design.md; challenge v5; exact existing contract retained

Approval: existing-contract

Enforcement: binding

Implementation status: partial

Check status: executable_scoped

Demonstrated evidence: evidence/coverage.md (per-policy evidence; approval does not establish behavior)

Decisions: Existing contract retained

Validation: Gate 1 / invariant / persistence

Source: spec.md

Policy: assessment-v3-owner-20260928

Executable parameters: {}

## STATE-002 — Idempotent stored observations

Requirement: Reprocessing identical notice content must not accumulate duplicate stored location or restriction observations.

Rationale: Repeated scraping must not multiply state.

Severity: critical

Inputs / preconditions: Same notice processed repeatedly, including after restart.

Expected behavior: Child rows per notice reflect the current extraction once; notice row is unique.

Forbidden behavior: Duplicate child rows or multiple versions without explicit version identity.

Required evidence: case input and hash; observed output/state; check result and requirement ID

Deterministic or evaluative: deterministic

Governance: grounded

Basis: inherited/database.py interface contract; challenge v5; exact existing contract retained

Approval: existing-contract

Enforcement: binding

Implementation status: partial

Check status: executable_scoped

Demonstrated evidence: evidence/coverage.md (per-policy evidence; approval does not establish behavior)

Decisions: Existing contract retained

Validation: Gate 1 / metamorphic / stored_idempotency

Source: spec.md

Policy: assessment-v3-owner-20260928

Executable parameters: {}

## STATE-003 — Already emitted signals

Requirement: Automatic alerting must use the approved event identity, persistent alert keys and acknowledgement contract.

Rationale: Duplicate trading actions create risk.

Severity: critical

Inputs / preconditions: A candidate for automatic alerting, including initial, update, replay and retry decisions.

Expected behavior: Apply D1, D2 and D6: resolve the explicit chain and approval/actionability conditions; persist attempts and acknowledgements; reuse unacknowledged keys; retain uncertain candidates without automatic alerting.

Forbidden behavior: Using classification labels or storage receipts as delivery approval; duplicate initial alerts or unsupported duplicate-free delivery claims.

Required evidence: case input and hash; observed output/state; check result and requirement ID

Deterministic or evaluative: deterministic

Governance: assessment-assumption

Basis: Challenge v5 pp. 2, 4–5: broad lifecycle/refusal/evidence obligations; exact bounded behavior is an owner-approved assessment assumption under ADR 006.

Approval: owner-approved

Enforcement: binding

Implementation status: partial

Check status: not_available

Demonstrated evidence: evidence/coverage.md (per-policy evidence; approval does not establish behavior)

Decisions: D1, D2, D6

Validation: Gate 1 / metamorphic / deferred

Source: spec.md

Policy: assessment-v3-owner-20260928

Executable parameters: {}

## STATE-004 — Nonmaterial supersedes

Requirement: A superseding notice with unchanged operational content must not generate another signal.

Rationale: Suppress routine revision noise.

Severity: high

Inputs / preconditions: A complete prior chain; source-supported unchanged operational content with only revision metadata or whitespace changes.

Expected behavior: Classify the verified synthetic unchanged-body and repeated revision cases as non-signals; under D2/D6, withhold another alert for unchanged operational facts.

Forbidden behavior: A new signal solely because identity/metadata changed; extrapolation to material updates or proof of delivered-alert deduplication.

Required evidence: case input and hash; observed output/state; check result and requirement ID

Deterministic or evaluative: deterministic

Governance: assessment-assumption

Basis: Challenge v5 pp. 2, 4–5: broad lifecycle/refusal/evidence obligations; exact bounded behavior is an owner-approved assessment assumption under ADR 006.

Approval: owner-approved

Enforcement: binding

Implementation status: partial

Check status: executable_scoped

Demonstrated evidence: evidence/coverage.md (per-policy evidence; approval does not establish behavior)

Decisions: D2, D6

Validation: Gate 2 / metamorphic / revision

Source: spec.md

Policy: assessment-v3-owner-20260928

Executable parameters: {"oracle_support": "requirements/oracle-support.json"}

## STATE-005 — Material revisions

Requirement: Material revisions require explicit adjudication and linked initial/update decisions while preserving source conflicts for review.

Rationale: Do not hide changed operational risk.

Severity: high

Inputs / preconditions: A revision changes operational facts, or an existing notice ID arrives with different source content.

Expected behavior: Apply D2: distinguish first initial alert, linked update and unacknowledged retry. Retain conflicting captures, preserve the last accepted snapshot and require review before changed content authorizes alerts.

Forbidden behavior: Unconditional supersede suppression; a second initial alert after an existing attempt; automatic overwrite, merge, discard or reconciliation of source conflicts.

Required evidence: case input and hash; observed output/state; check result and requirement ID

Deterministic or evaluative: deterministic

Governance: assessment-assumption

Basis: Challenge v5 pp. 2, 4–5: broad lifecycle/refusal/evidence obligations; exact bounded behavior is an owner-approved assessment assumption under ADR 006.

Approval: owner-approved

Enforcement: binding

Implementation status: not_implemented

Check status: not_available

Demonstrated evidence: evidence/coverage.md (per-policy evidence; approval does not establish behavior)

Decisions: D2, D6

Validation: Gate 2 / metamorphic / deferred

Source: spec.md

Policy: assessment-v3-owner-20260928

Executable parameters: {}

## STATE-006 — Replay and restart

Requirement: Replay after reopening persistent state must preserve stored observation idempotency.

Rationale: Reproducible restart behavior.

Severity: high

Inputs / preconditions: Identical notice replay after close/reopen.

Expected behavior: Current extraction appears once after replay.

Forbidden behavior: Accumulation due solely to process lifetime.

Required evidence: case input and hash; observed output/state; check result and requirement ID

Deterministic or evaluative: deterministic

Governance: grounded

Basis: inherited/design.md; challenge v5; exact existing contract retained

Approval: owner-approved

Enforcement: binding

Implementation status: partial

Check status: executable_scoped

Demonstrated evidence: evidence/coverage.md (per-policy evidence; approval does not establish behavior)

Decisions: D1

Validation: Gate 1 / metamorphic / restart

Source: spec.md

Policy: assessment-v3-owner-20260928

Executable parameters: {}

## HISTORY-001 — Available prior lineage

Requirement: A referenced prior notice that is available must be recoverable through the stored notice chain.

Rationale: Decisions need traceable context.

Severity: high

Inputs / preconditions: Prior row exists before evaluation.

Expected behavior: Chain includes referenced prior and current identities.

Forbidden behavior: Missing or fabricated available-prior linkage.

Required evidence: case input and hash; observed output/state; check result and requirement ID

Deterministic or evaluative: deterministic

Governance: grounded

Basis: inherited/design.md; challenge v5; exact existing contract retained

Approval: owner-approved

Enforcement: binding

Implementation status: implemented_bounded

Check status: executable_scoped

Demonstrated evidence: evidence/coverage.md (per-policy evidence; approval does not establish behavior)

Decisions: D1

Validation: Gate 1 / invariant / lineage

Source: spec.md

Policy: assessment-v3-owner-20260928

Executable parameters: {}

## HISTORY-002 — Missing prior notices

Requirement: Missing or disputed prior history must block automatic alerting while preserving the input, gap and uncertain candidate.

Rationale: Do not hide context gaps.

Severity: high

Inputs / preconditions: An ancestor is missing or a chain is disputed, cyclic or conflicting.

Expected behavior: Apply D1/D3: retain missingness and defer automatic alerting; new history may support a new linked reconciliation decision.

Forbidden behavior: Invented priors, silently complete history, discarded uncertain candidates or retroactive replacement of earlier missingness.

Required evidence: case input and hash; observed output/state; check result and requirement ID

Deterministic or evaluative: deterministic

Governance: assessment-assumption

Basis: Challenge v5 pp. 2, 4–5: broad lifecycle/refusal/evidence obligations; exact bounded behavior is an owner-approved assessment assumption under ADR 006.

Approval: owner-approved

Enforcement: binding

Implementation status: partial

Check status: not_available

Demonstrated evidence: evidence/coverage.md (per-policy evidence; approval does not establish behavior)

Decisions: D1, D3

Validation: Gate 1 / metamorphic / deferred

Source: spec.md

Policy: assessment-v3-owner-20260928

Executable parameters: {}

## HISTORY-003 — Out-of-order processing

Requirement: Out-of-order arrivals must reconcile to an order-independent final view under fixed accepted evidence.

Rationale: Arrival order is not event chronology.

Severity: high

Inputs / preconditions: The same accepted source versions, normalized facts, reference time and approved adjudications, processed in different orders.

Expected behavior: Apply D3: create linked reconciliation decisions, preserve earlier uncertainty and historical delivery attempts; compare final views using fixed facts.

Forbidden behavior: Using ID sort as chronology; demanding identical stochastic regeneration or identical real-time delivery histories.

Required evidence: case input and hash; observed output/state; check result and requirement ID

Deterministic or evaluative: deterministic

Governance: assessment-assumption

Basis: Challenge v5 pp. 2, 4–5: broad lifecycle/refusal/evidence obligations; exact bounded behavior is an owner-approved assessment assumption under ADR 006.

Approval: owner-approved

Enforcement: binding

Implementation status: not_implemented

Check status: not_available

Demonstrated evidence: evidence/coverage.md (per-policy evidence; approval does not establish behavior)

Decisions: D3

Validation: Gate 1 / metamorphic / deferred

Source: spec.md

Policy: assessment-v3-owner-20260928

Executable parameters: {}

## HISTORY-004 — Late notices

Requirement: Late-notice actionability must use explicit source-time semantics and a supplied reference clock, separate from historical label scoring.

Rationale: Historical relevance differs from current actionability.

Severity: high

Inputs / preconditions: A decision about current alerting, including late notices and unresolved point changes.

Expected behavior: Apply D3/D6: record source/publication/ingestion times and timezone-aware UTC reference time. Ended restrictions are historical-only for new disruption alerts; unresolved times/lifts require human actionability review.

Forbidden behavior: Implicit machine/model clock, invented age cutoff, rescoring historical labels against today or treating known labels as alert permission.

Required evidence: case input and hash; observed output/state; check result and requirement ID

Deterministic or evaluative: deterministic

Governance: assessment-assumption

Basis: Challenge v5 pp. 2, 4–5: broad lifecycle/refusal/evidence obligations; exact bounded behavior is an owner-approved assessment assumption under ADR 006.

Approval: owner-approved

Enforcement: binding

Implementation status: not_implemented

Check status: not_available

Demonstrated evidence: evidence/coverage.md (per-policy evidence; approval does not establish behavior)

Decisions: D3, D6

Validation: Gate 2 / metamorphic / deferred

Source: spec.md

Policy: assessment-v3-owner-20260928

Executable parameters: {}

## HISTORY-005 — Historical explainability

Requirement: Past decisions must be retrievable by immutable identity with exactly the context available at decision time.

Rationale: Mutable state alone cannot explain past decisions.

Severity: high

Inputs / preconditions: A past successful, failed or deferred decision, including after later corrections or revisions.

Expected behavior: Apply D4: retain and retrieve input, prior versions/missingness, clocks, facts, reasons, adjudications, implementation/policy/model identities and applicable delivery records. Later information creates linked decisions.

Forbidden behavior: Backfilling later facts into old explanations, replacing earlier evidence, automatic assessment pruning, credential retention or claiming a complete service from current snapshots.

Required evidence: case input and hash; observed output/state; check result and requirement ID

Deterministic or evaluative: deterministic

Governance: assessment-assumption

Basis: Challenge v5 pp. 2, 4–5: broad lifecycle/refusal/evidence obligations; exact bounded behavior is an owner-approved assessment assumption under ADR 006.

Approval: owner-approved

Enforcement: binding

Implementation status: not_implemented

Check status: not_available

Demonstrated evidence: evidence/coverage.md (per-policy evidence; approval does not establish behavior)

Decisions: D4

Validation: Gate 1 / invariant / deferred

Source: spec.md

Policy: assessment-v3-owner-20260928

Executable parameters: {}

## SAFETY-001 — Execution failures are not behavior

Requirement: Provider, environment, harness and unknown failures must not be reported as valid behavioral decisions.

Rationale: A fallback can conceal an invalid baseline.

Severity: critical

Inputs / preconditions: Every execution.

Expected behavior: Separate execution-domain failures from application dispositions and harness verdicts. An unusable model verdict cannot become a valid negative/small-impact result. Classification is unscorable only without its semantic result; other observable requirements remain evaluable.

Forbidden behavior: PASS from a mock, silent fallback, invalid helper verdict or credential failure; blanket exclusion of independently observable structure/state/failure handling.

Required evidence: case input and hash; observed output/state; check result and requirement ID

Deterministic or evaluative: deterministic

Governance: grounded

Basis: inherited/design.md; challenge v5; exact existing contract retained

Approval: owner-approved

Enforcement: binding

Implementation status: partial

Check status: executable_scoped

Demonstrated evidence: evidence/coverage.md (per-policy evidence; approval does not establish behavior)

Decisions: D5

Validation: Gate 1 / contract / model_proof

Source: spec.md

Policy: assessment-v3-owner-20260928

Executable parameters: {}

## SAFETY-002 — Unsupported and OOD inputs

Requirement: Unsupported inputs must retain explicit uncertainty/error evidence and withhold automatic alerting within the approved assessment scope.

Rationale: Constrain autonomy to demonstrated evidence.

Severity: high

Inputs / preconditions: Unsupported formats, pipelines, ambiguous assertions or insufficient source support.

Expected behavior: Apply D5/D6: retain reason and input; preserve last valid state. Missing optional strong-signal fields alone are not malformed. Unsupported annotations are unapproved or not evaluated and listed.

Forbidden behavior: Extrapolating the labeled corpus or narrow source-supported fields to general production safety or fabricating missing facts.

Required evidence: case input and hash; observed output/state; check result and requirement ID

Deterministic or evaluative: evaluative

Governance: assessment-assumption

Basis: Challenge v5 pp. 2, 4–5: broad lifecycle/refusal/evidence obligations; exact bounded behavior is an owner-approved assessment assumption under ADR 006.

Approval: owner-approved

Enforcement: binding

Implementation status: not_implemented

Check status: not_available

Demonstrated evidence: evidence/coverage.md (per-policy evidence; approval does not establish behavior)

Decisions: D5

Validation: Gate 2 / negative_control / deferred

Source: spec.md

Policy: assessment-v3-owner-20260928

Executable parameters: {}

## OBS-001 — Evidence provenance

Requirement: Every run must retain input, spec, requirements, implementation, model/prompt and dependency identities plus raw output and prior state.

Rationale: Supports independent review and reproduction.

Severity: critical

Inputs / preconditions: Every harness run.

Expected behavior: Retain input hashes, model request IDs, raw output, prior state and spec/rule/code/dependency/model/prompt identities. New policy applies only to new identified evaluations; historical evidence keeps its original policy.

Forbidden behavior: Unattributed or reused historical results presented as fresh.

Required evidence: case input and hash; observed output/state; check result and requirement ID

Deterministic or evaluative: deterministic

Governance: grounded

Basis: inherited/design.md; challenge v5; exact existing contract retained

Approval: owner-approved

Enforcement: binding

Implementation status: implemented_bounded

Check status: executable_scoped

Demonstrated evidence: evidence/coverage.md (per-policy evidence; approval does not establish behavior)

Decisions: D4

Validation: Gate 1 / contract / provenance

Source: spec.md

Policy: assessment-v3-owner-20260928

Executable parameters: {}

## OBS-002 — Inherited integrity

Requirement: The inherited source and supplied data must remain unchanged through baseline collection.

Rationale: Preserves a trustworthy comparison point.

Severity: critical

Inputs / preconditions: Baseline preparation and execution.

Expected behavior: Before/after hashes match approved inherited snapshot.

Forbidden behavior: Repairing inherited implementation before evidence exists.

Required evidence: case input and hash; observed output/state; check result and requirement ID

Deterministic or evaluative: deterministic

Governance: grounded

Basis: inherited/design.md; challenge v5; exact existing contract retained

Approval: existing-contract

Enforcement: binding

Implementation status: implemented_bounded

Check status: executable_scoped

Demonstrated evidence: evidence/coverage.md (per-policy evidence; approval does not establish behavior)

Decisions: Existing contract retained

Validation: Gate 1 / invariant / integrity

Source: spec.md

Policy: assessment-v3-owner-20260928

Executable parameters: {}

## OBS-003 — Regression/change evidence

Requirement: Compare requirement results and observable decisions when implementation, prompt, model, source, dependency or specification changes.

Rationale: Changes need attributable evidence.

Severity: high

Inputs / preconditions: A baseline or comparable run exists.

Expected behavior: Three primary gates; new pass/fail, unchanged and unexpected differences reported; first-run comparison is UNKNOWN.

Forbidden behavior: Calling absent comparison PASS or changing requirements to clear failures.

Required evidence: case input and hash; observed output/state; check result and requirement ID

Deterministic or evaluative: deterministic

Governance: grounded

Basis: inherited/design.md; challenge v5; exact existing contract retained

Approval: existing-contract

Enforcement: binding

Implementation status: implemented_bounded

Check status: executable_scoped

Demonstrated evidence: evidence/coverage.md (per-policy evidence; approval does not establish behavior)

Decisions: Existing contract retained

Validation: Gate 3 / invariant / regression

Source: spec.md

Policy: assessment-v3-owner-20260928

Executable parameters: {}

## Bounded recommendation demonstration

Implementation edition: `signal-safety-v1` under unchanged `assessment-v3-owner-20260928` D1–D6. [Source-referenced decision table](docs/signal-contract.md) separates classifier proposals from authorization. [Machine-readable partial contract](requirements/signal-safety.yaml) selects the controlled sequence and executable expected relationships. It supplements the existing obligations; it does not replace the deferred full checks or approve application acceptance. INPUT-002, STATE-003 and HISTORY-002 are now partially implemented. Their full checks remain unavailable; partial checks are reported separately in coverage.

The observable seam is the application's signals report, with the separate candidate producing outbound initial recommendation decisions. A–E hold facts, reference time and synthetic adjudications fixed: authorized root, exact replay, unchanged linked revision, reopen/replay revision, distinct authorized root. Initial counts are 1, 0, 0, 0, 1 under D1–D3. An additional restart/replay of the distinct root detects loss of initial-decision memory even when unchanged-revision suppression would mask it. Unusable impact after extraction, unavailable extraction, missing prior, absent authorization and routine content have no outbound decision. The distinct root guards against suppressing everything. Fixtures use synthetic SDK responses, never label lookups; controlled semantic behavior is not model accuracy.

## Temporal promotion boundary

Binding requirements, policy and assumptions may be proposed by an implementation agent, but may not become authoritative from an approval record created in the same candidate change. The exact normative artifact hashes and policy/requirement revision identities must be approved in an ancestor committed revision, with implementation strictly later. Same-tree or same-commit self-promotion returns UNAPPROVED_SELF_PROMOTION. This is temporal separation, not human identity authentication. Owner-authorized amendment and baseline/current-evidence protocol: [ADR 011](context/decisions/011-classification-actionability.md).
