# Requirement coverage

Run `final-run` · spec `c89f760b3f2167345112801cd7825d26c40c102996239d13a2c788c9c4d363b6` · mode `REVIEWED_SPEC` · commit `1dc58370b2d0399e50b0fb88b76453fc3d16842f`.

PASS means the declared check passed on the listed observations, not that the whole obligation is proven. OUT_OF_SCOPE rows are declared in spec-verification and never gated.

| Requirement | Check | Result | Observations | Evidence kinds |
|---|---|---|---:|---|
| HISTORY-001 | lineage | PASS | 1 | INDEPENDENT_SEMANTIC_WITNESS: 1 |
| HISTORY-002 | replay | PASS | 3 | FROZEN_WITNESS_MATCH: 1; INDEPENDENT_SEMANTIC_WITNESS: 1; initial: 1 |
| HISTORY-003 | out_of_scope | OUT_OF_SCOPE | 0 |  |
| HISTORY-004 | out_of_scope | OUT_OF_SCOPE | 0 |  |
| HISTORY-005 | out_of_scope | OUT_OF_SCOPE | 0 |  |
| INPUT-001 | identity | PASS | 56 | OUTPUT_IDENTITY: 56 |
| INPUT-002 | refusal | PASS | 9 | DIRECT_COMPONENT_REFUSAL_RETAINED: 1; FROZEN_WITNESS_MATCH: 3; INDEPENDENT_SEMANTIC_WITNESS: 3; initial: 2 |
| OBS-001 | provenance | PASS | 1 | RUN_PROVENANCE: 1 |
| OBS-002 | integrity | PASS | 1 | INHERITED_INTEGRITY: 1 |
| OBS-003 | regression | PASS | 1 | REGRESSION_COMPARISON: 1 |
| OUTPUT-001 | decision_shape | PASS | 28 | PUBLISHER_CLASSIFIER_CONSISTENT: 12; disposition: 12; reason: 4 |
| OUTPUT-002 | quantities | PASS | 46 | CAPTURED_UPSTREAM_EXTRACTION: 46 |
| OUTPUT-003 | links | PASS | 46 | CAPTURED_UPSTREAM_EXTRACTION: 46 |
| OUTPUT-004 | field_values | PASS | 8 | CAPTURED_UPSTREAM_EXTRACTION: 8 |
| OUTPUT-005 | field_values | PASS | 20 | CAPTURED_UPSTREAM_EXTRACTION: 20 |
| OUTPUT-006 | field_values | PASS | 18 | CAPTURED_UPSTREAM_EXTRACTION: 18 |
| SAFETY-001 | model_proof | PASS | 3 | INDEPENDENT_SEMANTIC_WITNESS: 1; UNUSABLE_SEMANTICS_REFUSED: 1; semantic_safety: 1 |
| SAFETY-002 | refusal | PASS | 1 | initial: 1 |
| SIGNAL-001 | classification | PASS | 42 | FROZEN_WITNESS_MATCH: 5; INDEPENDENT_SEMANTIC_WITNESS: 3; LABELED_FALSE_POSITIVES: 2; LABELED_MISSED_POSITIVES: 2; LABEL_UNRESOLVED_COUNTED: 12; REAL_SOURCE_POSITIVE_WITNESS: 2; SUPPLIED_LABEL_COMPARISON: 16 |
| SIGNAL-002 | classification | PASS | 8 | DECLARED_CASE_COMPARISON: 6; FROZEN_WITNESS_MATCH: 1; initial: 1 |
| SIGNAL-003 | classification | PASS | 2 | DECLARED_CASE_COMPARISON: 2 |
| SIGNAL-004 | classification | PASS | 4 | DECLARED_CASE_REVIEW_AS_SPECIFIED: 4 |
| STATE-001 | out_of_scope | OUT_OF_SCOPE | 0 |  |
| STATE-002 | out_of_scope | OUT_OF_SCOPE | 0 |  |
| STATE-003 | replay | PASS | 4 | initial: 4 |
| STATE-004 | revision | PASS | 4 | FROZEN_WITNESS_MATCH: 2; INDEPENDENT_SEMANTIC_WITNESS: 1; initial: 1 |
| STATE-005 | out_of_scope | OUT_OF_SCOPE | 0 |  |
| STATE-006 | restart | PASS | 2 | initial: 2 |

[Exact observations](results.json)
