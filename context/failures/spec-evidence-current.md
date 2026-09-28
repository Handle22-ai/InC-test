# Current specification/evidence learning — nonbinding

These observations/proposals do not change requirements or grant authority. [Current run](../../evidence/specification/20260927T234809.632974Z/report.md).

- Historical storage reinterpretation replaced previous policy identity; current code retains original manifest identity and marks changed policy/evaluator comparisons noncomparable without a mapping.
- Semantic unscorability did not imply safe presentation: inherited unusable-impact emitted a valid-looking recommendation. SAFETY-001 now observes presented classification and report count. Extraction stays independently scorable.
- Baseline-B 46864 persisted positive at 0.50, exactly the inherited threshold, with helper None/default-small evidence. Its positive label means this is unsafe fallback, not a false positive.
- Count duplicate recommendation steps independently of missing disposition/reason fields. Those are separate output-contract findings. Gate mapping follows the declared requirement.
- Source 46732 explicitly names prior 46507. The prior-loaded captured-extraction replay is separate from isolated/corpus-absent history checks and does not create a model capture.
- Parser LOC groups collapse segment/CS/zone arity; non-LOC groups form products. The normalized contract preserves associations; raw extraction is not certified by semantic stubs.
- The old worker exercise is recovered and complete on its reconstructed baseline, with strict isolation qualified. Do not rerun it or transplant it into this candidate.

The [original proposal](../proposals/normalized-classifier-rule.md) is now approved prospectively by [ADR 007](../decisions/007-br-firm-proposal-classification.md) for candidate classification only; old blocked evidence remains historical. The independent spec-only builder has not run; no implementation or solution transcript belongs in its package.

[Concrete retained input-probe learning](../../evidence/specification/20260927T234809.632974Z/checks/input-probe/learning.json) is nonbinding; future selection does not adopt it as policy.

Current hardening: [CURRENT](../../evidence/CURRENT.md) and [actual disposable probes](../../evidence/derivation-integrity/20260928T011856Z/report.md). BR-SEMANTICS restored ERROR; runtime canonical predicates are checked by frozen witnesses. D-rule hash-only re-pins and unauthorized assumption/index edits are refused. Pending learning is automatically surfaced as unapproved, and cannot alter core authority.
