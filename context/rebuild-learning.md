> **Historical (archived 2026-09-28).** This records an earlier build pass. The Make targets and evidence paths it names were removed; the evidence stays at commit `8ea74f8` (see `evidence/ARCHIVE.md`). Current commands are in README.md. Do not follow the commands below.

# Notice snapshot rebuild — durable learning

The user approved the component scope in ADR 003, not all assumptions. Binding business
requirements and thresholds were not changed. The 512-token variant remains separate.

The smallest meaningful repair was storage: one typed notice snapshot commits as one
SQLite document. It contains current notice/location/restriction observations, not an
immutable event log. The rebuilt store raises an explicit content conflict for same-ID,
different-hash input; it never silently resolves that policy question. Distinct prior
notices are retained. Available chains are observable; missing links are exposed by the
native chain result, without implementing reconciliation or retroactive decisions.

Both ports received the same 21 frozen normalized snapshots from the existing candidate
capture, in identically empty per-group temporary databases, reopening after each write.
Existing storage assertions are unchanged. Exact current readback and persisted-join
checks supplement those assertions equally for both systems. No adapter deletes or
deduplicates rows; inherited surrogate row IDs are excluded only from normalized payload
comparison and remain in raw state. Nine checks changed FAIL → PASS. 148 were unchanged.
The rebuilt store has 134 passing storage findings, no failures, and three UNKNOWN
missing-prior findings outside HISTORY-001's available-prior precondition. Available
prior cases pass. Frozen decisions remain 13/14 label matches, with 46528 still failing.

The failed first harness attempt is retained in `context/failures/rebuild-harness-protocol.md`.
Final repeatable comparison: `make evaluate-storage`. It writes fresh evidence, captured
inputs, source/spec/dependency identities, failures and regression candidates. Native
storage guard tests use explicitly synthetic inputs; they are not live trading evidence.

Do not conflate replay of a captured normalized output with another model execution.
The targeted live integration command uses one normal parser invocation and fans out its
single normalized output to both stores. Its authorization/outcome is documented in the
current rebuild report. It is a boundary integration, not a replacement of the inherited
production CLI or its SQLite-coupled history reader.

No human code read was requested or reported. Agent source reads were recorded separately.
No fresh-session maintenance change has been implemented. The next session must read
`context/maintenance-request.md` and run the manifest selector; no prior chat is needed.
