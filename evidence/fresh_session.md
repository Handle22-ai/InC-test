# Fresh-session maintenance exercise (2026-09-28, branch claude/audit-remediation)

A new agent session started with no conversation history, on a clean clone of commit `d09b68d`. It received only README's first message plus the change below. Nothing else was explained.

**Starting request.** The inherited extractor labels NGPL's No-Notice Service restrictions with `service_type: NO_NOTICE`. NNS is a firm, storage-backed service, but today those rows are not recognised as firm. The desk wants a firm restriction on NNS handled like other firm-service disruptions.

**Context selected automatically.** `make context TASK=recommendation-classification-maintenance` exited 0. It supplied the binding requirements and a source scope of `classifier.py` and `rebuilt/{normalized_classifier,normalization,rule_engine,source_input}.py`, plus pending learning marked unapproved and the superseded guidance.

**Requirements and decisions used.** The spec-predicates table and `FIRM_SERVICES`, the interface enums, `normalization.services`, SIGNAL-001/003, and the REMEDIATION decision rows.

**Source opened or searched.** Only files in scope: the five component files above, plus `tests/test_spec_predicates.py` when a test failed, and one search of `harness/consequences.py`. It did not open `harness/domain_rules.py`. Before the remediation, the same request made the session open 14 source files, 9 of them harness modules, to find what "firm" meant.

**Additional human explanation required.** None.

**What changed.** spec.md only, through the proposal and consequences steps:
- `NO_NOTICE` normalizes to a new `NO_NOTICE_FIRM` value (the source distinction is kept);
- `NO_NOTICE_FIRM` joins `FIRM_SERVICES` and the four service enums;
- decision row `NNS-FIRM-001` is marked **proposed**.

Generated files were recompiled. No component or harness code changed.

**Gate results.** `make consequences`: 0 of 46 captured outcomes change. The only captured NNS row (46528, labeled negative) is a partial hourly limit and correctly stays non-firm. `gate --proposal` gave the same result before and after: Gate 1 PASS, Gate 2 PASS, Gate 3 UNKNOWN (EVALUATOR_OR_ORACLE_CHANGED, already present from the remediation). The desk view is unchanged: 2 of 7 positives missed and 0 false positives per capture. A scratch probe showed the component and the harness oracle agreeing: NNS unavailable → BR-FIRM; NNS partial and interruptible → unresolved.

**New learning, retained for the next session.**
1. A test matched the literal `FIRM_SERVICES` text, so any real edit of the set broke it. The test now reads the current set. Fixed on this branch.
2. No labeled or frozen NNS outage exists, so the intended effect is unmeasured. The owner should add an NNS-unavailable witness; that is an oracle change.
3. The desk should confirm that a partial NNS limit stays non-firm, as it does for primary and secondary firm service.
4. The package should say that service mappings and `FIRM_SERVICES` are spec-owned. The agent read two component files to confirm this; both reads are recorded in `code_reads.md`.

**Owner decision:** NNS-FIRM-001 approved 2026-09-28. Still open: reread, and add an NNS-unavailable witness.
