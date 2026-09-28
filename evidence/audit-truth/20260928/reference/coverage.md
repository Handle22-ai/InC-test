# Observed coverage

Spec `340a24705e7c26f3a4997972e7c23a1e47787ecce5aad6f6a3397792d0354d77`; mode `PROPOSAL_ONLY`; commit `e46f4f6a9efbe7b286c1eab04efe10b02eefae90`.

Finite observations only. PASS means the named checks passed on these cases; full obligations remain UNKNOWN. Synthetic witnesses do not establish declared source-case recall. Checks with absent preconditions are listed separately in trading/results.json.

| Requirement | Declared check / availability | Scoped result | Observations | Evidence kinds | Full obligation |
|---|---|---|---:|---|---|
| HISTORY-001 | lineage / declared | PASS | 1 | INDEPENDENT_SEMANTIC_WITNESS: 1 | UNKNOWN |
| HISTORY-002 | deferred / deferred | UNKNOWN | 3 | AGREEMENT: 1; CHECK_DEFERRED: 1; INDEPENDENT_SEMANTIC_WITNESS: 1; initial: 1 | UNKNOWN |
| HISTORY-003 | deferred / deferred | UNKNOWN | 0 | CHECK_DEFERRED: 1 | UNKNOWN |
| HISTORY-004 | deferred / deferred | UNKNOWN | 0 | CHECK_DEFERRED: 1 | UNKNOWN |
| HISTORY-005 | deferred / deferred | UNKNOWN | 0 | CHECK_DEFERRED: 1 | UNKNOWN |
| INPUT-001 | identity / declared | UNKNOWN | 0 | DECLARED_CHECK_UNOBSERVED: 1 | UNKNOWN |
| INPUT-002 | deferred / deferred | UNKNOWN | 10 | AGREEMENT: 3; CHECK_DEFERRED: 1; DIRECT_COMPONENT_REFUSAL_RETAINED: 1; INDEPENDENT_SEMANTIC_WITNESS: 3; initial: 3 | UNKNOWN |
| OBS-001 | provenance / declared | UNKNOWN | 0 | DECLARED_CHECK_UNOBSERVED: 1 | UNKNOWN |
| OBS-002 | integrity / declared | UNKNOWN | 0 | DECLARED_CHECK_UNOBSERVED: 1 | UNKNOWN |
| OBS-003 | regression / declared | PASS | 1 | REGRESSION_COMPARISON: 1 | UNKNOWN |
| OUTPUT-001 | decision_shape / declared | PASS | 27 | AGREEMENT: 12; disposition: 12; reason: 3 | UNKNOWN |
| OUTPUT-002 | quantities / declared | UNKNOWN | 0 | DECLARED_CHECK_UNOBSERVED: 1 | UNKNOWN |
| OUTPUT-003 | links / declared | UNKNOWN | 0 | DECLARED_CHECK_UNOBSERVED: 1 | UNKNOWN |
| OUTPUT-004 | field_values / declared | PASS | 8 | CAPTURED_UPSTREAM_EXTRACTION: 8 | UNKNOWN |
| OUTPUT-005 | field_values / declared | PASS | 20 | CAPTURED_UPSTREAM_EXTRACTION: 20 | UNKNOWN |
| OUTPUT-006 | field_values / declared | PASS | 18 | CAPTURED_UPSTREAM_EXTRACTION: 18 | UNKNOWN |
| SAFETY-001 | model_proof / declared | PASS | 5 | INDEPENDENT_SEMANTIC_WITNESS: 1; UNUSABLE_SEMANTICS_REFUSED: 2; semantic_safety: 2 | UNKNOWN |
| SAFETY-002 | deferred / deferred | UNKNOWN | 0 | CHECK_DEFERRED: 1 | UNKNOWN |
| SIGNAL-001 | classification / declared | UNKNOWN | 38 | AGREEMENT: 5; CAPTURED_LABEL_UNSCORED: 13; INDEPENDENT_SEMANTIC_WITNESS: 3; REAL_SOURCE_POSITIVE_WITNESS: 2; SUPPLIED_LABEL_COMPARISON: 15 | UNKNOWN |
| SIGNAL-002 | classification / declared | PASS | 8 | AGREEMENT: 1; DECLARED_CASE_COMPARISON: 6; initial: 1 | UNKNOWN |
| SIGNAL-003 | classification / declared | UNKNOWN | 2 | DECLARED_CASE_COMPARISON: 1; DECLARED_CASE_UNSCORED: 1 | UNKNOWN |
| SIGNAL-004 | classification / declared | UNKNOWN | 4 | DECLARED_CASE_UNSCORED: 4 | UNKNOWN |
| STATE-001 | persistence / declared | UNKNOWN | 0 | DECLARED_CHECK_UNOBSERVED: 1 | UNKNOWN |
| STATE-002 | stored_idempotency / declared | UNKNOWN | 0 | DECLARED_CHECK_UNOBSERVED: 1 | UNKNOWN |
| STATE-003 | deferred / deferred | UNKNOWN | 4 | CHECK_DEFERRED: 1; initial: 4 | UNKNOWN |
| STATE-004 | revision / declared | PASS | 4 | AGREEMENT: 2; INDEPENDENT_SEMANTIC_WITNESS: 1; initial: 1 | UNKNOWN |
| STATE-005 | deferred / deferred | UNKNOWN | 0 | CHECK_DEFERRED: 1 | UNKNOWN |
| STATE-006 | restart / declared | PASS | 2 | initial: 2 | UNKNOWN |

[Exact observations](results.json) · [D sentence coverage](rule-invariants.json)
