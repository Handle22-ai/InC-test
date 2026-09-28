# AGENTS.md — InCommodities Harness Operating Charter

## Mission

You are completing the InCommodities North America technical challenge, **The Harness**.

This is **not** primarily a code-review, cleanup, or refactor exercise.

Build and demonstrate an engineering harness where:

- the specification is the authoritative description of intended behavior;
- AI coding agents may inspect and modify implementation code;
- the human engineer primarily owns the specification and reviews evidence;
- tests, contracts, invariants, negative controls, and evaluations are derived from the specification;
- the harness independently evaluates whether generated work satisfies requirements;
- failures become durable engineering knowledge;
- context survives across completely fresh agent sessions;
- requirement changes remain under explicit human control;
- limitations and human code reads are documented candidly.

The success criterion is:

> Can an engineer maintain and trust this system by owning precise requirements and inspecting evidence, without routinely needing to read implementation source code?

## Authority hierarchy

1. `spec.md`
2. Machine-readable requirements derived from `spec.md`
3. Human-approved ADRs / decisions
4. Human-approved assumptions
5. Known failures / regressions
6. Existing tests
7. Existing implementation

The implementation does **not** define correct behavior.

If the specification is incomplete, record the ambiguity and create an explicit assumption or proposed clarification.

Never modify a requirement or acceptance threshold merely to make failing code pass.

## Core control loop

```text
Engineer intent / spec change
            ↓
       Specification
            ↓
 Machine-readable requirements
            ↓
     Context selection
            ↓
       Coding agent
            ↓
      Running system
            ↓
 Independent validation gates
            ↓
          Evidence
            ↓
       Human decision
            ↓
 Durable learning / proposals
```

## First-pass rule

Do not start by fixing the inherited implementation.

First:

1. identify how it runs;
2. identify inputs and outputs;
3. locate labeled examples;
4. identify persistent state;
5. identify major component boundaries;
6. identify model/LLM calls;
7. establish one successful end-to-end execution;
8. preserve a behavioral baseline.

Create `artifacts/repo_map.md`.

## Specification rules

Create `spec.md` as an implementation-independent behavioral contract.

Use stable IDs:

```text
INPUT-*
OUTPUT-*
SIGNAL-*
STATE-*
HISTORY-*
SAFETY-*
OBS-*
```

Each important requirement should include:

```text
ID
Requirement
Rationale
Severity
Inputs / preconditions
Expected behavior
Forbidden behavior
Required evidence
Deterministic or evaluative
```

Explicitly cover:

- previous notices;
- repeated scraping;
- revisions;
- superseding notices;
- already-emitted signals;
- late-arriving notices;
- missing prior notices;
- out-of-order processing;
- reprocessing;
- restart / replay;
- history needed to explain a past decision.

Unsupported behavior must be recorded as an assumption, not silently promoted to fact.

## Machine-readable requirements

Create `requirements/requirements.yaml`.

Prefer:

```text
requirement
    ↓
machine-readable rule
    ↓
generic validation strategy
    ↓
derived/generated check
    ↓
evidence
```

## Context selection

Given a task, determine:

- applicable requirements;
- affected components;
- relevant interfaces;
- likely source scope;
- decisions;
- assumptions;
- known failures;
- regression cases;
- required gates.

Do not rely on prior chat history as project memory.

## Persistent engineering memory

Use:

```text
context/
├── manifest.yaml
├── domain.md
├── assumptions.md
├── decisions/
├── failures/
├── regressions/
└── proposals/
```

Do not silently resolve conflicting guidance.

## Three primary gates

Build exactly three primary gates unless compelling evidence requires another.

### Gate 1 — Contracts and invariants

Prefer deterministic checks:

- schema validity;
- required provenance;
- required fields;
- valid units;
- impossible values;
- state transition validity;
- idempotency;
- duplicate suppression;
- revision semantics;
- history consistency.

### Gate 2 — Trading behavior evaluation

Report at minimum:

- false trading signals;
- missed critical/unplanned disruptions;
- routine notices incorrectly signaled;
- duplicate signals from revisions;
- curtailment-volume extraction failures;
- pipeline-segment extraction failures;
- geography/relevance failures;
- ambiguous / unsupported / OOD cases.

### Gate 3 — Regression / change

Run whenever implementation, model, prompt, source format, dependency, or specification changes.

Report:

- newly passing cases;
- newly failing cases;
- unchanged behavior;
- unexpected differences;
- requirements affected.

## Derived negative and metamorphic checks

At minimum explore:

- duplicate input;
- revision;
- repeated revision;
- missing history;
- out-of-order history;
- replay/restart where feasible;
- administrative negative control;
- field mutation.

## Evaluate before fixing

Run the inherited implementation through the harness before substantive repairs.

For every meaningful failure retain:

```text
Requirement:
Input:
Expected:
Observed:
Risk:
Evidence:
Possible failure domain:
Confidence:
```

## Human code-read policy

Human source inspection is allowed only as an escalation when evidence is insufficient.

Maintain `evidence/code_reads.md`.

Each entry must include:

```text
CODE-READ-ID:
Observed failure:
Why evidence was insufficient:
Source inspected:
What was learned:
Missing harness/evidence capability:
Harness improvement made:
Could the same code read be avoided next time?
```

## Rebuild one meaningful component

Prefer a boundary like:

```text
NormalizedNotice + EventHistory → SignalDecision
```

Do not simply copy/refactor the inherited implementation.

## Same harness for inherited and rebuilt systems

Both implementations must face:

- same requirements;
- same contracts;
- same behavioral evaluation;
- same regression rules;
- same acceptance policy.

## Evidence surface

Generate `evidence/summary.md` with:

- run identity;
- gate statuses;
- blocking findings;
- requirement coverage;
- assumptions;
- known unknowns;
- OOD cases;
- code-read summary;
- autonomy envelope;
- harness limitations.

Never report PASS without evidence.

## Failure-to-learning loop

Automatically retain:

- failing examples;
- execution evidence;
- regression candidates;
- model outputs where relevant;
- traces;
- requirement mappings.

Do not automatically change requirements, thresholds, autonomy policy, or approved ADRs.

If the spec is incomplete, create a proposal requiring human approval.

## Fresh-session exercise

After the rebuilt component works, start a genuinely new agent session with no prior chat.

Record:

```text
Starting request:
Context selected automatically:
Requirements loaded:
ADRs loaded:
Known failures loaded:
Source scope selected:
Additional human explanation required:
Files changed:
Gate results:
Regression result:
New learning:
Knowledge retained for the next session:
```

## Clean-code standard

Prefer:

- explicit module boundaries;
- strong typing;
- small cohesive functions;
- narrow interfaces;
- schemas/models over loose dictionaries;
- deterministic policy where possible;
- isolated model usage;
- reproducible commands;
- structured errors;
- useful logging;
- tests for harness infrastructure;
- minimal dependencies.

Avoid:

- giant orchestration classes;
- speculative abstractions;
- hidden global state;
- unnecessary agent frameworks;
- duplicated business rules;
- LLMs for hard invariants;
- tests mirroring implementation details.

## Agent architecture

Prefer:

```text
deterministic harness
       │
       ├── selects context
       ▼
   coding agent
       │
       ▼
      repo
       │
       ▼
deterministic harness
       │
       ▼
     evidence
```

The harness owns correctness and evidence. The coding agent owns implementation work.

## Current maintenance workflow

Read `README.md`, `spec.md` and `evidence/CURRENT.md`. Build-time prompts under
`docs/history/` are historical context, never competing active instructions.

Distinguish an implementation defect from an inadequate requirement or missing
evidence. For a policy proposal, edit a copy of spec.md and run:

```bash
make consequences SPEC=context/proposals/proposed-spec.md BASE=spec.md
```

Inspect improved outcomes, adverse changes and unresolved cases before adopting
a change. Generated consequences never replace independently supplied labels.
Do not write a human read receipt merely because an agent edited the spec.

```bash
make setup
make check
make compile
make context TASK=recommendation-classification-maintenance
make gate
```

`python -m harness gate --proposal` measures the current unreviewed spec without
acceptance. The ordinary gate refuses a stale review; CI accepts only exit 0.
Historical commands are documented in harness.md. Live calls require explicit
current authorization and a call budget. Agent implementation reads are allowed;
the goal is evidence sufficient for the human engineer to decide.

## Stop conditions

Do not declare the submission ready until:

1. intended behavior can be understood from `spec.md`;
2. important validation is visibly derived from requirements;
3. inherited system has been evaluated;
4. meaningful findings are preserved;
5. one meaningful component has been rebuilt;
6. both systems face same gates;
7. evidence explains failures;
8. persistent context exists outside chat;
9. a fresh-session maintenance exercise is complete;
10. learning survives future sessions;
11. requirement changes remain human-controlled;
12. code reads are documented;
13. remaining limitations are explicit;
14. README commands reproduce the workflow.
