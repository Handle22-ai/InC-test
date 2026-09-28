# CODEX_FINAL_REVIEW.md — Final Self-Review

Verify using actual artifacts and runs.

## Specification
- Can intended behavior be understood without source?
- Are state/revision/reprocessing semantics explicit?
- Are assumptions separated?
- Are IDs stable?

## Derived validation
- Can a requirement be traced mechanically to a check?
- Are generic strategies used where reasonable?
- Are important checks more than manually authored tests with IDs?

## Legacy evidence
- Was legacy evaluated before substantive repair?
- Are failures preserved?
- Can findings trace to requirements and concrete I/O?

## Trading risk
- False signals visible?
- Missed critical disruptions?
- Duplicate revisions?
- Extraction failures?
- OOD cases?
- High-risk failures not hidden by aggregate accuracy?

## Code-read honesty
- Human code reads recorded?
- Why was evidence insufficient?
- Did code reads improve harness/evidence?
- Are we falsely implying zero code reads?

## Rebuilt component
- Built from spec?
- Clean boundary?
- Same gates?
- Accepted via evidence rather than human implementation review?

## Context persistence
- Decisions, assumptions, failures, regressions, proposals outside chat?
- Superseded guidance explicit?
- Selector returns relevant subset?

## Fresh session
- Genuinely fresh?
- Prompt preserved?
- Context preserved?
- Extra explanation disclosed?
- Gates rerun?
- New learning persisted?

## Evidence surface
- Readable in minutes?
- Run/spec/build/model/dataset identified?
- Gates clear?
- Blocking findings clear?
- Assumptions/unknowns clear?
- Autonomy envelope clear?
- Limitations clear?

## Clean code
- Cohesive modules?
- Explicit interfaces?
- Deterministic policies deterministic?
- Model isolated?
- Errors visible?
- Minimal dependencies?
- Simple commands?
- Unnecessary agent complexity removed?

## Reproducibility
Actually run documented commands.

## End-to-end story
Confirm at least one complete chain:

```text
requirement
→ machine-readable rule
→ derived check
→ legacy behavior
→ failure evidence
→ diagnosis/code-read escalation
→ harness improvement
→ rebuilt implementation
→ same check
→ fresh-session change
→ persisted context
→ new learning
```

## Honesty check
List:
- incomplete work;
- ambiguity;
- what would be done with more time;
- where source inspection remains necessary;
- evidence-backed conclusions;
- assumptions.
