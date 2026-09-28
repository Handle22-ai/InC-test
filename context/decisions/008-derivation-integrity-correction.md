# ADR 008 — Narrow derivation-integrity correction

Status: owner-approved technical correction, with no D1–D6 business amendment.
Authority: [exact current owner request](../../evidence/derivation-integrity/20260928T011856Z/owner-request.txt).
Starting source: commit `019de93564ced1b3b4766316afda0ba106eb9348` plus the
preserved BR-FIRM approval overlay. Original packages and receipts remain intact.

Restore BR-SEMANTICS to its pre-approval UNRESOLVED / ERROR action. The phrase
“remains REVIEW_REQUIRED” did not authorize changing ERROR. Descriptive wording
such as “remains X” must not silently change the previous X. This corrects the
overreach in the prior ADR 007 recording and keeps BR-FIRM's approved candidate
predicates, precedence and recommendation_allowed false. BR-CONTRADICTION and
the downstream publisher's error behavior remain unchanged.

Move the existing bounded feature predicates into canonical structured data in
requirements/behavior.yaml. Generic expression evaluation and mechanical prior
chain observations implement the supported vocabulary. The representation
changes; existing candidate business meaning, D1–D6, labels, numeric bounds,
input/output schemas and publication authorization do not.

Keep source assertions and prospective witness expectations independent of the
contract interpreter. Preserve the eight original synthetic cases and their
classifications. Add the requested PRIMARY_ONLY distinguishing witness without
altering the existing cases. A canonical active outcome that disagrees with a
frozen witness produces CONTRACT_CONTRADICTS_FIXTURE and nonzero exit. Timing
metadata is outside semantic fixture identity. READY means only contract/witness
agreement, never a builder pass.

Require D-rule changes to reference registered owner-approved decision bodies
containing the exact new wording, with a new policy ID and higher policy version.
The new ADR 006 machine record projects the already adopted historical wording;
it creates no new policy. A re-pin, missing/stale/mismatched artifact, or merely
accepted record is insufficient. Changed wording must also occur in its new
registered ADR. Local files and the verifier remain writable by the same worker;
this is semantic approval traceability, not cryptographic owner authentication.

Context selection must validate canonical contract and generated view consistency
before publishing a context package. This adds a guard to the existing selection
path, not a context-system redesign.

Verify the exact requested mutations in disposable copies, run the specified
checks, then create a successor commit and a fresh spec-only package. Do not
launch its builder or import another evaluator's report into the repository.
