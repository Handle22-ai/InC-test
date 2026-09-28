# Decision 004 — optional capture reference, rebuilt envelope only

Authorization: the user's maintenance request, retained verbatim in
`evidence/maintenance/20260926T201903.969882Z/starting_request.txt`.
This is a technical extension, not a change to business policy, labels or thresholds.

The rebuilt snapshot envelope accepts `capture_reference: str | None = None`.
The string is opaque and never dereferenced. Missing/null means no capture reference;
any string, including an empty string, is retained verbatim. Other types are rejected.
Existing caller signatures remain valid and old stored documents load with `None`.

The field is serialized beside the notice/location/restriction payload inside the
existing atomic document. No table migration or inherited schema change is needed.
The shared `output()` projection remains exactly notice, locations and restrictions.
Native `SnapshotStore.read`, `all` and `chain` expose the metadata on the snapshot.

Identity remains NGPL notice ID plus the supplied source hash. A metadata-only change
updates the same current snapshot and uses the existing `refreshed` receipt disposition;
exact envelope replay uses `replayed`. A full snapshot write whose reference is `None`
clears an earlier reference. This follows the existing full-snapshot replacement API:
omission is not a partial-update instruction, and there is no implicit metadata merge.
These receipt details are technical extension behavior, not a claim of new content or
alert delivery. Same-ID/different-source-hash conflicts still reject the entire write.

Extension checks remain separate from shared storage acceptance, with explicitly
synthetic examples. The inherited store is not evaluated for or said to support this
field. Binding requirements and unresolved policies retain their existing status.

Source-scope expansions for this exercise: `tests/test_capture_reference.py` isolates
new checks; this decision, new evidence/learning/regression files and `README.md` record
the requested handoff. `Makefile` was read only to verify the required offline commands.
No inherited implementation inspection or modification was required.
