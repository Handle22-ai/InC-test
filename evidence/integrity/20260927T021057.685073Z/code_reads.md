# Agent source reads — integrity correction

No human source read was requested or reported. These are agent inspections while resolving reproduced evidence gaps.

CODE-READ-ID: INTEGRITY-001
Observed failure: missing/rebound rules, tampered captures and changed approval text could evade current checks.
Why evidence was insufficient: prior receipts did not expose loader/reference trust boundaries.
Source inspected: harness/requirements.py, gates.py, context.py, review.py, evidence.py and requirement/context metadata.
What was learned: substring checks and copied annotations were insufficient; local writable references cannot authenticate owners.
Missing harness/evidence capability: per-ID binding, capture/oracle separation and explicit authority limits.
Harness improvement made: structured consistency checks, pinned capture verification, canonical oracle use, repeated mutation probes and honest manual boundary.
Could the same code read be avoided next time? These cases have retained tests/probes; new authority mechanisms still need inspection.

CODE-READ-ID: INTEGRITY-002
Observed failure: paired results labeled regression, invisible persisted output on helper failure, missing readback exception and incorrect chain accepted.
Why evidence was insufficient: summaries conflated comparison scopes and incomplete execution with absent observations.
Source inspected: harness/regression.py, storage_evaluation.py, storage_ports.py, adapter.py and relevant tests.
What was learned: compare each system with its prior, observe storage after writes and preserve usable facts independently of semantic completion.
Missing harness/evidence capability: stable comparator identities and readback fault probes.
Harness improvement made: separate paired/temporal records, actual inherited-for-rebuilt substitute test, storage doubles and evaluator-attributed new interpretations.
Could the same code read be avoided next time? Covered failures now have repeatable infrastructure tests; application limits remain explicit.

CODE-READ-ID: INTEGRITY-003
Observed failure: Make values executed synthetic markers, unknown options reached work hooks, historical PASS substituted for current readiness and unlisted executables were absent from inventory.
Why evidence was insufficient: old success receipts did not test hostile arguments or early side effects.
Source inspected: Makefile; harness/runtime.py, offline.py, preflight.py, evaluator.py, candidate.py, storage_integration.py, e2e.py and command tests.
What was learned: argument transfer, early validation and inventory checks must precede imports/work; no-call budgets are unexercised.
Missing harness/evidence capability: disposable shell markers, provider stubs and alternate synthetic credential-access tests.
Harness improvement made: safe argv transfer, explicit live/budget gates, run-scoped writes, expanded offline guards and structured early failures.
Could the same code read be avoided next time? Repeated probes/tests cover these paths. In-process guards do not establish OS isolation.
