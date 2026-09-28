# AUDIT-CRITICAL-001 — pending owner decision

Status: unapproved proposal; NOT RECOMMENDED as written after consequence measurement. No policy, label, threshold, classification or authorization change is activated.

The supplied audit identifies a silent-negative risk: a trusted source header says Critical=Y and Force Majeure, while the model marks the notice informational and supplies no restrictions. The current normalized rule language does not consult that source header. The retained synthetic probe in `evidence/audit-remediation/20260928/critical-informational-probe.json` currently yields NON_SIGNAL / NO_SIGNAL through BR-ROUTINE.

Proposed bounded decision for review: when a trusted, source-grounded Critical=Y header conflicts with a model-only information-only conclusion and no extracted operational restrictions, return UNRESOLVED / REVIEW_REQUIRED with a source-criticality disagreement reason. Do not infer SIGNAL_CANDIDATE, materiality, a timezone, current/future actionability, or recommendation authorization from the header alone. Unknown or missing criticality remains unknown. A source-grounded disruption meeting existing BR-FIRM remains candidate-only.

This requires an explicit normative rule/input-evidence amendment and a newly reviewed spec identity. D6 says criticality is evidence to weigh; it does not establish this header-only classifier precedence. No new operator, numeric cutoff or universal critical-notice signal rule is proposed. Until the owner rules, retain the reproducer and surface the missing rule as an unresolved coverage gap under SIGNAL-003; do not claim the probe passes a critical-disruption check.

## Measured consequences before a ruling

The offline counterfactual in [routine-review-preview](../../evidence/spec-feedback/20260928/routine-review-preview/REPORT.md) changes BR-ROUTINE to REVIEW_REQUIRED. It models the proposed override on the captured routine cases; it does not add a header predicate or activate policy. All six affected observations have Critical=1, as do all 14 unique labeled source notices.

The affected IDs are 46604, 46775 and 46818 in each of two correlated captures. True negatives fall from 3 to 0 in each capture; detected positives remain 5/7 and 4/7. This amendment does not recover the force-majeure error. No recommendation is authorized. A source-grounded force-majeure proposal needs its own domain ruling and consequence run; do not substitute notice type as automatic signal permission.
