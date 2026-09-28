# DELIVERABLES_AND_ACCEPTANCE.md

## `spec.md`
Must cover:
- purpose;
- input/output contracts;
- stable requirement IDs;
- signal behavior;
- refusal/failure behavior;
- persistent state;
- revisions;
- duplicate/reprocessing;
- late/missing/out-of-order notices;
- historical explainability;
- provenance/evidence;
- assumptions.

## `harness.md`
Must answer:

> What does the engineer look at instead of code?

Describe:
- spec → validation derivation;
- context selection;
- coding-agent workflow;
- three gates;
- evidence surface;
- failure → learning;
- requirement governance;
- model/spec changes;
- cross-session persistence;
- superseded guidance;
- first-day workflow;
- gate rationale/cost/alternatives;
- limitations.

## `README.md`
Must explain:
- setup;
- run inherited system;
- evaluate inherited;
- generate evidence;
- evaluate rebuilt;
- compare;
- select context;
- reproduce fresh session.

## Harness implementation
Must include:
- requirement loading;
- common SUT boundary;
- inherited adapter;
- rebuilt adapter;
- three gates;
- evidence generation;
- regression comparison;
- context selection.

## Machine-readable requirements
Must make important checks traceable from spec → rule → strategy/check → evidence.

## Rebuilt component
Must be meaningful, spec-driven, and judged by the same gates.

## Evidence
Required:
- `evidence/summary.md`;
- legacy evidence;
- rebuilt evidence;
- comparisons;
- coverage;
- code-read ledger;
- fresh-session record.

## Persistent context
Required:
- domain;
- assumptions;
- decisions;
- failures;
- regressions;
- manifest/index;
- proposals.

## Trading-risk evaluation
At minimum surface:
- false signals;
- missed critical disruptions;
- routine notices incorrectly signaled;
- duplicate revision signals;
- volume errors;
- segment errors;
- geography errors;
- OOD cases.

## Metamorphic / negative coverage
Include:
- duplicate notice;
- revision;
- repeated revision;
- missing prior;
- admin negative control;
- field mutation;
- replay/out-of-order where feasible.

## Autonomy envelope
Tie autonomy to demonstrated evidence.

## Edge map
Document:
- evidence gaps;
- code-inspection needs;
- ambiguous requirements;
- data/eval weaknesses;
- context-selection limits;
- omitted work;
- next steps.

# Final A+ proof

```text
requirement
→ machine-readable representation
→ derived check
→ legacy failure
→ evidence
→ code-read escalation if needed
→ harness improvement
→ rebuilt component
→ same check
→ improved result
→ fresh-session maintenance
→ persisted context recovered
→ new durable learning
```
