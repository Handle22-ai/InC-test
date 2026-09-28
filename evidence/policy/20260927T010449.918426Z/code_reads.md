# Policy-pass source reads — agent only

No human implementation read was requested or reported. These are coding-agent reads required to synchronize explicitly approved policy, not claims about the owner's behavior.

CODE-READ-ID: POLICY-AGENT-001
Observed issue: four grounded rows were treated as exploratory by a separate reporter exception list; approved lifecycle policy needed explicit check-availability treatment.
Why evidence was insufficient: reports exposed the split but could not establish all executable dispatch and selection dependencies.
Source inspected: harness/requirements.py, review.py, gates.py, context.py, policy evaluation/Make/offline boundary and affected infrastructure tests.
What was learned: source basis, acceptance scope and available component checks were conflated; the reporter already preserves observable structural evidence when semantic execution fails.
Missing harness capability: current-policy metadata consistency and conditional source-support enforcement.
Improvement: explicit requirement enforcement consumed by reporter/selector; prose/metadata consistency checks; source-support/precondition checks; new-policy captured evaluation with original provenance and zero model calls.
Avoidable next time: tests and selected context now retain these boundaries; executable changes may still require agent reads.

CODE-READ-ID: POLICY-AGENT-002
Observed issue: D6 approval was conditional on traceable annotation support, including synthetic mutation/revision cases.
Why evidence was insufficient: prior PASS counts alone do not establish an independent source oracle.
Source inspected: supplied HTML, dataset annotations, existing evaluator transformation and inherited notice_parser._extract_body boundary (read-only).
What was learned: all included annotations have direct source support; 46507 has stale segment-17 header text but operative segment-14 wording; 46864 root cause and constraint differ (8/9). Synthetic mutation/revision lineage is explicit.
Missing harness capability: source support could not previously restrict a check's binding applicability.
Improvement: requirements/oracle-support.json plus source hashes/excerpts and complete-prior checks; unsupported evidence is UNKNOWN and listed.
Avoidable next time: retain source excerpts/hashes and verify additional annotations before applying approved scope.

## POLICY-READ-04 — Older formatter governance

Agent-only inspection of harness/evidence.py and its call in harness/evaluator.py found stale proposed/unapproved and no-rebuild wording. Current approval/check metadata now appears in this formatter, and it refuses mismatched historical policy fingerprints before writing. Regression coverage renders only in a temporary directory. No human source inspection or live run is claimed.
