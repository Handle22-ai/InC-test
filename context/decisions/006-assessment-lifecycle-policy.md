# ADR 006 — Owner-approved bounded lifecycle assessment policy

Status: APPROVED WITH AMENDMENTS by the repository owner on 2026-09-27 UTC.
Policy: `assessment-v2-owner-20260927`. Exact owner decision: [evidence/policy/20260927T010449.918426Z/owner-approval.txt](../../evidence/policy/20260927T010449.918426Z/owner-approval.txt).
This is not approval by InCommodities or a trading desk, and not application acceptance.

The owner approved D1–D6 from the [preserved proposal](../../evidence/policy/20260927T010449.918426Z/before/context/proposals/v5-lifecycle-completion.md), subject to the exact attached amendments. The adopted normative wording is in spec.md and requirements/requirements.yaml. D labels map onto existing requirement IDs.

| Decision | Challenge obligation | Owner-approved assessment choices / amendment |
|---|---|---|
| D1 | Remember earlier notices and already-signaled events; suppress duplicates (pp. 2/5) | Explicit-chain/root identity, source hash, durable attempts/acknowledgements, same-key retry, assessment retention; gaps block automatic alerts but retain uncertain candidates. |
| D2 | Revisions and nonduplicate supersedes (pp. 2/5) | Compare operational facts; human adjudication; initial versus update versus unacknowledged retry; retain source conflict evidence while preserving the accepted snapshot. |
| D3 | Missing/late/reprocessed history (p. 2) | Explicit reference clock/end boundary; defer history gaps; fixed accepted versions, normalized facts and adjudications for convergence. Real-time attempts need not be identical. |
| D4 | Explain past decisions (p. 2) | Immutable decision-ID retrieval, missingness as known then, linked corrections, no automatic assessment pruning. |
| D5 | Refuse failure modes (pp. 1/2) | Explicit uncertain/error disposition, preserved valid state, distinguish API success from usable verdict; score each requirement when its observations exist. |
| D6 | Meaningful disruption, typical features and documented assumptions (pp. 4/5) | Named-human materiality and recorded alert approval; labels evaluation-only; source-verified narrow field/revision checks prospectively binding. |

## Scope and supersession

Supersedes the pending-policy status of the D1–D6 proposal and corresponding parts of A-001–A-008 and historical ADR 003 discussion. It does not rewrite those historical decisions or the prepared/running replay's contract. Storage identity/receipts/conflict behavior in ADR 003 and technical extensions 004/005 remain unchanged. Production retention, broad formats, source-version reconciliation and trading autonomy are not authorized.

The four rows OUTPUT-004/005/006 and STATE-004 move from exploratory v2 reporting to binding **only for source-supported annotations and satisfied preconditions**. Source support is retained in requirements/oracle-support.json; unsupported evidence yields UNKNOWN and is listed. This is a prospective governance change, not a software repair or a claim that the owner inspected every annotation. Old labels, thresholds, reports and outcomes remain under their original policy.

## Implementation and verification

No deferred event/delivery/reconciliation/history system is implemented. Approved requirements may lack executable checks. Current spec/rules distinguish authority, approval, enforcement, implementation, check availability and the evidence index. Reporting/selection consume the metadata without a separate current exception list. New evaluations identify the policy and frozen-input lineage. See [current coverage](../../evidence/coverage.md) and the [policy-pass report](../../evidence/policy/20260927T010449.918426Z/report.md).

## Human control

Further requirements, oracle scope, labels, numerical thresholds or autonomy changes require explicit owner approval. A model, label, passing storage receipt or owner approval of this specification is not runtime alert authorization.
