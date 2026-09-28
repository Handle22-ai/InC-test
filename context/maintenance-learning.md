# Capture-reference maintenance — recovered knowledge for later sessions

Evidence: `evidence/maintenance/20260926T201903.969882Z/fresh_session.md`.
Technical extension contract: `context/decisions/004-capture-reference-extension.md`.

The rebuilt snapshot now has an optional opaque `capture_reference`. Existing callers
and pre-change documents load with `None`; no table migration is required. The reference
round-trips through native read/all/chain, but is deliberately absent from `output()`.
That projection is the unchanged shared contract used to compare both stores. Passing
shared storage checks alone therefore cannot establish optional metadata persistence:
the separate `tests/test_capture_reference.py` checks native readback.

Metadata-only changes refresh the same notice/source identity. Full-snapshot writes
with `None` clear the current reference; omission is not a patch or implicit merge.
Changed source hashes still conflict, and a failed write preserves the whole prior
document. A stored JSON value must be an object before optional-key extraction, and
invalid reference types remain explicit errors. No reference string is dereferenced.

The compatibility database was written by the unchanged pre-maintenance implementation
before editing source, explicitly labeled synthetic, and retained with its hash. Tests
copy it into temporary databases. Do not recreate it using the new writer and call that
proof of old-format compatibility. Keep this fixture available for future regressions.

Offline results: 49 tests pass (39 existing, 10 extension-specific). Relative to both
the manifest-selected paired run and the newly captured pre-change run, 157 shared
findings per implementation are unchanged, as are all 21 case/state records per system.
No new shared passes/failures or unexpected differences. The 46528 false positive and
three missing-prior unknowns persist. The inherited store still has its replay defects;
the optional field is neither required of nor supported by that inherited store.

No live model calls, requirement changes, label changes or threshold changes occurred.
No additional human explanation or human source-read escalation was needed. The selector
and repository provided the task facts. However, earlier messages were present in the
supplied conversation context: this record cannot certify the charter's strict no-prior-
chat session-isolation condition. Maintenance success is not full challenge completion.

Future tasks should select current context, verify its hashes, preserve their baseline,
and compare shared behavior independently of extension-specific evidence. Treat the
original prepared request and earlier reports as historical completed-stage records.
