# Requirement coverage

Run `reviewed-run-final` · spec `c1f20c1cf233a0ccdd5607c33a443bf653f0e3993b334b806498b55686d4b937` · mode `REVIEWED_SPEC` · commit `15d4bdd8bb09ffb06679f8ce8fca180b3d2a6e03`.

PASS means the declared check passed on the listed observations, not that the whole obligation is proven. OUT_OF_SCOPE rows are declared in spec-verification and never gated.

| Requirement | Check | Result | Observations | Evidence kind and status (count) |
|---|---|---|---:|---|
| HISTORY-001 | lineage | PASS | 1 | INDEPENDENT_SEMANTIC_WITNESS PASS: 1 |
| HISTORY-002 | replay | PASS | 3 | FROZEN_WITNESS_MATCH PASS: 1; INDEPENDENT_SEMANTIC_WITNESS PASS: 1; initial PASS: 1 |
| HISTORY-003 | out_of_scope | OUT_OF_SCOPE | 0 |  |
| HISTORY-004 | out_of_scope | OUT_OF_SCOPE | 0 |  |
| HISTORY-005 | out_of_scope | OUT_OF_SCOPE | 0 |  |
| INPUT-001 | identity | PASS | 79 | OUTPUT_IDENTITY PASS: 79 |
| INPUT-002 | refusal | PASS | 9 | DIRECT_COMPONENT_REFUSAL_RETAINED PASS: 1; FROZEN_WITNESS_MATCH PASS: 3; INDEPENDENT_SEMANTIC_WITNESS PASS: 3; initial PASS: 2 |
| OBS-001 | provenance | PASS | 1 | RUN_PROVENANCE PASS: 1 |
| OBS-002 | integrity | PASS | 1 | INHERITED_INTEGRITY PASS: 1 |
| OBS-003 | regression | UNKNOWN | 1 | REGRESSION_COMPARISON UNKNOWN: 1 |
| OUTPUT-001 | decision_shape | PASS | 28 | PUBLISHER_CLASSIFIER_CONSISTENT PASS: 12; disposition PASS: 12; reason PASS: 4 |
| OUTPUT-002 | quantities | PASS | 69 | CAPTURED_UPSTREAM_EXTRACTION PASS: 69 |
| OUTPUT-003 | links | PASS | 69 | CAPTURED_UPSTREAM_EXTRACTION PASS: 69 |
| OUTPUT-004 | field_values | PASS | 12 | CAPTURED_UPSTREAM_EXTRACTION PASS: 12 |
| OUTPUT-005 | field_values | PASS | 30 | CAPTURED_UPSTREAM_EXTRACTION PASS: 30 |
| OUTPUT-006 | field_values | PASS | 27 | CAPTURED_UPSTREAM_EXTRACTION PASS: 27 |
| SAFETY-001 | model_proof | PASS | 4 | INDEPENDENT_SEMANTIC_WITNESS PASS: 1; UNUSABLE_SEMANTICS_REFUSED PASS: 2; semantic_safety PASS: 1 |
| SAFETY-002 | refusal | PASS | 1 | initial PASS: 1 |
| SIGNAL-001 | classification | PASS | 58 | FROZEN_WITNESS_MATCH PASS: 5; INDEPENDENT_SEMANTIC_WITNESS PASS: 3; LABELED_FALSE_POSITIVES PASS: 3; LABELED_MISSED_POSITIVES PASS: 3; LABEL_UNRESOLVED_COUNTED COUNTED: 18; REAL_SOURCE_POSITIVE_WITNESS PASS: 2; SUPPLIED_LABEL_COMPARISON PASS: 24 |
| SIGNAL-002 | classification | PASS | 11 | DECLARED_CASE_COMPARISON PASS: 9; FROZEN_WITNESS_MATCH PASS: 1; initial PASS: 1 |
| SIGNAL-003 | classification | PASS | 3 | DECLARED_CASE_COMPARISON PASS: 3 |
| SIGNAL-004 | classification | PASS | 6 | DECLARED_CASE_REVIEW_AS_SPECIFIED PASS: 6 |
| STATE-001 | out_of_scope | OUT_OF_SCOPE | 0 |  |
| STATE-002 | out_of_scope | OUT_OF_SCOPE | 0 |  |
| STATE-003 | replay | PASS | 4 | initial PASS: 4 |
| STATE-004 | revision | PASS | 4 | FROZEN_WITNESS_MATCH PASS: 2; INDEPENDENT_SEMANTIC_WITNESS PASS: 1; initial PASS: 1 |
| STATE-005 | out_of_scope | OUT_OF_SCOPE | 0 |  |
| STATE-006 | restart | PASS | 2 | initial PASS: 2 |

[Exact observations](results.json)
