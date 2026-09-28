# ARCHITECTURE_AND_CODE_QUALITY.md

## Goal

Keep the harness clean, explicit, and boring.

The value is the control model and evidence, not framework sophistication.

## Suggested modules

```text
src/
├── harness/
│   ├── requirements.*
│   ├── context.*
│   ├── evaluator.*
│   ├── evidence.*
│   ├── models.*
│   ├── cli.*
│   └── gates/
│       ├── contracts.*
│       ├── behavior.*
│       └── regression.*
│
├── adapters/
│   ├── inherited.*
│   └── rebuilt.*
│
└── rebuilt/
    └── <selected_component>/
```

## Core conceptual interface

```python
class SystemUnderTest(Protocol):
    def process(
        self,
        notice: Notice,
        history: EventHistory,
    ) -> SignalDecision:
        ...
```

Use equivalent patterns in the repository's language.

## Structured results

Prefer explicit models such as:

```python
class GateResult:
    gate: GateName
    status: GateStatus
    findings: list[Finding]
    evidence_refs: list[EvidenceRef]
```

```python
class Finding:
    requirement_id: str
    severity: Severity
    expected: object
    observed: object
    risk: str
    evidence_refs: list[EvidenceRef]
```

## Separation of responsibilities

### Requirement loader
Loads/validates requirements.

### Context selector
Maps task to requirements, decisions, failures, assumptions, regressions, source scope.

### Adapters
Present inherited/rebuilt systems through a common boundary.

### Gates
Apply generic strategies and return evidence.

### Evidence layer
Retains raw run artifacts, findings, comparisons, provenance.

### Coding agent
Inspects/modifies implementation.

The coding agent does not define correctness.

## Deterministic vs model-based

Use deterministic code for:
- schemas;
- units;
- required fields;
- state transitions;
- idempotency;
- duplicate rules;
- pass/fail aggregation;
- regression diffing;
- evidence generation.

Use model calls only for genuinely semantic interpretation.

## Generic strategies

Prefer:

```text
contract → ContractStrategy
metamorphic → MetamorphicStrategy
labeled_eval → DatasetEvaluationStrategy
negative_control → NegativeControlStrategy
```

## Evidence provenance

Record where practical:
- run ID;
- timestamp;
- spec hash/version;
- requirements hash/version;
- source/build revision;
- model/prompt version;
- dataset identity;
- case ID;
- output;
- gate;
- requirement ID.

## Failure safety

Use explicit statuses:

```text
PASS
FAIL
UNKNOWN
ERROR
```

Never convert inability to evaluate into PASS.

## Testing expectations

Test:
- requirement loading;
- strategy selection;
- context selection;
- gate aggregation;
- evidence serialization;
- regression diffing;
- non-trivial adapters.

## Dependency discipline

Avoid:
- large agent frameworks without need;
- vector DBs when files suffice;
- workflow engines for simple sequences;
- web UIs.

## Clean-code review

Before finalizing:

1. Does each module have one clear responsibility?
2. Are requirements in the spec rather than duplicated in code?
3. Can legacy/rebuilt swap behind the adapter?
4. Are exact policies deterministic?
5. Can findings trace to requirements?
6. Are evaluator errors distinct from behavioral failures?
7. Are types/schemas explicit?
8. Is the command surface simple?
9. Is there unnecessary multi-agent complexity?
10. Does any abstraction mainly exist to look sophisticated?
