# Recommended rebuild — notice snapshot persistence

Status: PROPOSED component boundary, not implementation approval or a business-policy decision.
The token-budget candidate is an execution-configuration experiment, not the required meaningful rebuild.

## Boundary

`NoticeSnapshot + ExistingHistory → PersistedNoticeSnapshot + WriteReceipt`

Rebuild the per-notice storage component from the specification: identity-keyed, typed input snapshots;
a cohesive transaction for the notice and its location/restriction observations; an explicit write
receipt; and observable readback. Identical reprocessing must retain one current set of child
observations. Keep raw run evidence outside this mutable current-state store.

Why this boundary: both unmodified-baseline attempts independently demonstrate stored-row accumulation
on exact repeated input, a repeated supersede, and restart/replay. The evidence is narrow and directly
checkable. It does not require settling uncertain trading labels or treating delivered alerts as rows.
The charter prefers a decision/history component, but the verified state boundary provides a smaller,
better-specified first rebuild while still exercising history, replay and independent validation.

## Requirements and demonstrated checks

- STATE-001: successful notice/children persist across close/reopen.
- STATE-002: repeated identical source/version does not accumulate current child observations.
- STATE-006: replay after reopening retains the same current observation set.
- OUTPUT-003: restriction-to-location joins stay within the notice.
- HISTORY-001: available prior notice links remain recoverable.
- INPUT-001 and OBS-001/002: identity, provenance and unchanged source/evidence remain traceable.

These are existing documented contract checks, not new approved semantic policies. A first comparison
should swap only this storage component behind the same notice-processing workflow and run the same
three gates, dataset, initial-state protocol and state probes. Include isolated infrastructure failure
checks for incomplete writes; any new requirement beyond the current contract must remain a proposal.

## Open policy and scope boundaries

- Logical-event IDs and delivered-alert exactly-once behavior are not yet observable; no delivery guarantee.
- Same notice ID with genuinely changed content needs a human-approved version policy.
- Missing-prior reconciliation, out-of-order final state, immutable application history and crash/ack
  recovery need policy/evidence beyond the current simple replay probe.
- Materiality, late-notice cutoffs/timezones and the 46725 label interpretation stay separate.
- This rebuild does not change the model, prompts, impact scoring or supplied labels.

## Remaining challenge sequence

1. Select task context automatically from manifest: applicable requirements, map, assumptions,
   storage findings, this proposal and the unchanged source scope.
2. Build the bounded component independently from the behavioral contract; do not copy/refactor the
   inherited insert implementation. Keep both versions available through a narrow adapter.
3. Evaluate both with the same gates and acceptance treatment, including failure preservation.
4. Once the rebuilt component works, perform the required genuinely fresh-session maintenance task,
   recording automatically selected context and durable new knowledge.

Do not spend the remaining challenge repeatedly tuning the inherited model until every label passes.
The current evidence already supports proceeding toward a meaningful state-component rebuild.
