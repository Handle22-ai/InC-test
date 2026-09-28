# Synthetic format compatibility — durable learning

Current evidence: `evidence/format-compatibility/20260926T204022.284775Z/report.md`.
Contract: `context/decisions/005-synthetic-capture-reference-alias.md`.

`captureReference` is a read-only spelling alias at the native stored-document boundary.
The public snapshot attribute and canonical serialization remain `capture_reference`.
Conflicting keys must raise a named error; do not select a preferred key or use a truthy
fallback. Empty strings and explicit null are valid values. Equal values are accepted
only when valid: Python equality between numbers/booleans is not proof of a valid string.
The existing snapshot validator remains the single optional-field type rule.

Exact replay of an alias document returns the existing replay receipt without changing
bytes. Refresh writes canonical metadata. This avoids turning reader compatibility into
an unrequested migration or changing receipt semantics. Unknown unrelated fields still
fail validation. Native read/all/chain and source-conflict behavior are covered by the
synthetic tests. Nothing asserts a real NGPL format change.

Before editing, 49 tests and the captured shared evaluation were preserved. The nine new
format tests failed against the old reader (five assertion failures, ten errors across
subtests), then all 58 tests passed after a five-line decoder change. Shared findings and
all case/state records are identical to both selected and immediate pre-change baselines.
Existing classification failures, inherited storage defects and missing-prior unknowns
remain; no live model calls were made.

Session evidence is separate from code evidence. Named environment variables exposed
the session/thread ID, but not how the platform launched it or its memory setting.
Earlier coding messages and a preexisting history summary were visible in the supplied
context, so the requested isolated-session condition was not satisfied. No summary,
fork, resume or import was requested by the agent. Do not infer the platform mechanism
that supplied context or retroactively certify any prior exercise.
