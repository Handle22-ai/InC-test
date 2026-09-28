# ADR 003 — bounded notice snapshot persistence

Status: component scope APPROVED by the user's 2026-09-26 instruction following review
of `evidence/reviews/v2/report.md` and the rebuild proposal. This does not approve proposed
domain policies. Supersedes only the proposal's awaiting-implementation-approval status.

Boundary: `NoticeSnapshot + ExistingHistory → PersistedNoticeSnapshot + WriteReceipt`.
Binding storage requirements: INPUT-001, OUTPUT-003, STATE-001, STATE-002, STATE-006,
HISTORY-001. Evidence/change obligations: OBS-001, OBS-002, OBS-003.

Identity is the supplied NGPL notice ID within this bounded store. A source-content SHA256
distinguishes source versions; identical reprocessing means the same notice ID and source
bytes/hash. A snapshot comprises the complete notice, its current location observations,
and restrictions joined by notice ID and location index. Replaying the same captured
snapshot must leave one current observation set, observable through readback and reopening.
Receipts acknowledge storage only; they do not acknowledge trading-alert delivery.

Engineering choice: keep each complete current snapshot in one SQLite document, keyed by
notice ID. One transaction commits its related records. Return an explicit receipt only
after commit. Preserve separate notice identities and recover available prior links.
This is independently constructed from the contract, not copied from inherited insert SQL.
Same-source refreshed extraction may replace the current observation set as STATE-002
states; historical extraction evidence belongs in immutable run files outside this store.

Same-ID different source content is UNSUPPORTED pending a human-approved policy. Raise an
explicit conflict and leave the existing state intact. A conflict is not a successful
discard, merge, overwrite, or claim that the changed notice was processed. No new version
policy, reconciliation, historical event model, or delivered-alert mechanism is introduced.

STATE-003/005, HISTORY-002/003/004/005, SAFETY-002 remain proposed. A-001 through A-008
remain proposed. STATE-004 synthetic materiality and narrow OUTPUT-004/005/006 probes
retain the v2 exploratory interpretation. Supplied labels and all acceptance thresholds
remain unchanged. The 512-token configuration is a separate completed experiment.

Proceed serially; preserve original source and evidence; use identical frozen normalized
inputs and assertions for both stores, then a small integration run with fixed model and
prompts. Prepare, but do not implement or simulate, the genuinely fresh-session task.
