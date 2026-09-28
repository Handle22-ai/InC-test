# EXECUTION_PLAN.md — Exact Order of Work

## Phase 0 — Establish baseline

1. Read instruction files.
2. Inspect repository tree.
3. Read challenge/repository docs.
4. Determine setup/runtime.
5. Locate labeled data.
6. Locate optional unlabeled data.
7. Run inherited system once.
8. Record environment assumptions.
9. Do not make substantive fixes yet.

Deliverables:
- `artifacts/repo_map.md`;
- working baseline execution;
- environment notes.

## Phase 1 — Specification

Create `spec.md`.

Define:
- purpose;
- inputs;
- outputs;
- signal behavior;
- refusal/failure behavior;
- persistent state;
- revisions;
- duplicates/reprocessing;
- late/missing/out-of-order behavior;
- historical explainability;
- provenance/evidence.

## Phase 2 — Executable requirements

Create `requirements/requirements.yaml`.

Support:
- contract checks;
- invariants;
- metamorphic checks;
- labeled evaluations;
- negative controls.

## Phase 3 — Minimal harness

Required capabilities:

1. load/validate requirements;
2. invoke system through adapter;
3. execute Gate 1;
4. execute Gate 2;
5. execute Gate 3;
6. retain raw evidence;
7. generate evidence summary;
8. compare implementations;
9. select task context.

## Phase 4 — Legacy baseline

Run:
- Gate 1;
- Gate 2;
- duplicate;
- revision;
- repeated revision;
- missing history;
- admin negative control;
- field mutation.

Preserve results before substantive repair.

## Phase 5 — Diagnose only as necessary

If evidence is insufficient:
- inspect smallest relevant code area;
- record code read;
- improve evidence surface.

## Phase 6 — Rebuild one component

Default preference:

```text
NormalizedNotice + EventHistory → SignalDecision
```

unless repository structure strongly favors another boundary.

## Phase 7 — Compare

Run inherited and rebuilt implementations through the same gates.

Produce:
- per-requirement comparisons;
- regressions;
- newly passing/failing cases;
- unchanged behavior;
- known unknowns.

## Phase 8 — Persistent context

Create/fill:
- manifest;
- domain;
- assumptions;
- decisions;
- failures;
- regressions;
- proposals.

## Phase 9 — Fresh session

Start a genuinely fresh agent and execute `FRESH_SESSION_TASK.md`.

## Phase 10 — Evidence polish

Make `evidence/summary.md` concise and decision-oriented.

## Phase 11 — Documentation

Finalize:
- `README.md`;
- `harness.md`;
- coverage;
- limitations/edge map.

## Phase 12 — Final review

Run `CODEX_FINAL_REVIEW.md`.

Prefer completion of the proof chain over extra features.
