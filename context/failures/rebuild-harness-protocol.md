# Retained harness failure — relative path and connection protocol

Observed in `evidence/rebuild/20260926T194455.389677Z/component/` (preserved).

Requirement: OBS-001, OBS-003; fair same-protocol comparison.
Input: frozen 512-token normalized snapshots; relative output directory.
Expected: evidence summary written; inherited application protocol retained.
Observed: final summary formatting rejected a relative path. Review of retained checks
also found three inherited insert errors caused by enabling FK enforcement before
insertion, whereas the captured application enables it afterward.
Risk: mistaking a harness configuration error for inherited behavior.
Evidence: `execution_error.json`, per-system results/cases in that directory.
Possible failure domain: HARNESS_FAILURE; confidence: direct observed run and protocol read.

Narrow correction: resolve output path at the boundary; keep inherited init → insert →
enable_fk ordering. Do not suppress insert failures or manufacture missing prior notices.
The next two runs are retained separately, with `component-final/` the authoritative
paired run. The second run was superseded only because automatic failure/regression
retention and absent-comparator reporting were added; the paired results did not change.

Learning: connection initialization order is part of an adapter's fidelity. Read the
existing observation workflow before choosing connection flags. A count-only check is
insufficient to prove current snapshot readback; retain raw state and compare all fields
through the same check for both implementations.
