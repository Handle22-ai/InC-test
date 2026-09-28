# START HERE — InCommodities Technical Challenge

## Objective

Build the smallest convincing version of the engineering system described by the challenge:

> The engineer owns the specification and reads evidence.  
> The harness selects context, lets an AI coding agent operate on the implementation, derives validation from the specification, and preserves what is learned across sessions.

Do **not** approach this as a conventional code-review-and-fix exercise.

The inherited implementation is a system under evaluation. The specification defines correctness.

## First Codex Prompt

After placing this starter kit in the private challenge repository, start Codex and send:

```text
Read AGENTS.md, EXECUTION_PLAN.md, ARCHITECTURE_AND_CODE_QUALITY.md,
and DELIVERABLES_AND_ACCEPTANCE.md.

Then execute INITIAL_TASK.md.

Treat the repository instructions as authoritative project instructions.

Do not begin by fixing or refactoring the inherited implementation.
First establish the system boundary, specification, executable requirements,
and a preserved evidence baseline of the inherited behavior.

Do not claim anything is complete until you have run and verified it.
```

## What the finished submission needs to prove

```text
Requirement
    ↓
Machine-readable requirement
    ↓
Derived validation
    ↓
Inherited implementation
    ↓
Observed failure
    ↓
Evidence
    ↓
Code-read escalation only if evidence is insufficient
    ↓
Harness/evidence improvement
    ↓
Rebuilt component
    ↓
Same validation
    ↓
Fresh-session maintenance task
    ↓
Persisted context recovered automatically
    ↓
New knowledge retained for future sessions
```

## Recommended order

1. Get inherited system running.
2. Map component boundaries.
3. Write `spec.md`.
4. Write executable `requirements/requirements.yaml`.
5. Build minimal harness.
6. Baseline inherited implementation.
7. Find meaningful failures through evidence.
8. Improve evidence when diagnosis forces a code read.
9. Rebuild one meaningful component.
10. Evaluate inherited vs rebuilt through same gates.
11. Persist context.
12. Run genuinely fresh maintenance session.
13. Finalize `harness.md`, evidence, README, coverage, limitations.
14. Run `CODEX_FINAL_REVIEW.md`.
