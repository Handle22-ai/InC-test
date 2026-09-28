# Fresh-session maintenance exercise (2026-09-28, branch claude/audit-remediation)

**What the session was.** A subagent (`agent-a78d2c9`), spawned with the Agent tool by the build-and-remediation session `2edc1739`, ran 16:00:50–16:06:09Z on a clean clone of pre-publication commit `d09b68d` (see ARCHIVE.md). It had no conversation history, but it was not an independent session: the thread that wrote the component and the harness chose the request, wrote the prompt and received the report. Its prompt, verbatim:

> Operational setup (not part of the task): your checkout is /private/tmp/claude-501/-Users-thomashand-PycharmProjects-incommodities-take-home/2edc1739-994d-433d-9bcc-5c6208585f1d/scratchpad/fresh2 . Work only there; never touch /Users/thomashand/PycharmProjects/incommodities-take-home. Before running commands: `export PATH=/usr/bin:/bin:/usr/sbin:/sbin:$HOME/.local/bin; unset VIRTUAL_ENV ANTHROPIC_API_KEY` and cd into the checkout. No live model calls. Do not commit.
>
> ---
>
> You are maintaining this repository. Read README.md, spec.md and evidence/CURRENT.md. Run `make setup` if `.venv` is missing, then `make context TASK=recommendation-classification-maintenance` and read the package.md it prints. Change only the files the package lists as source scope, plus spec.md through the "Change the policy" steps. Record any source you read in evidence/code_reads.md. Never edit frozen labels or witnesses, and never write a reread receipt. The change: the inherited extractor labels NGPL's No-Notice Service restrictions with service_type `NO_NOTICE`. NNS is a firm, storage-backed service, but today those rows are not recognised as firm. The desk wants a firm restriction on NNS handled like other firm-service disruptions.
>
> When done, report: files changed, commands run with exit codes, the gate results before and after, and anything you needed that the repository did not give you.

The operational block and the reporting paragraph were added by the build session; the middle paragraph is README's fresh-session message plus the change.

**Starting request.** The inherited extractor labels NGPL's No-Notice Service restrictions with `service_type: NO_NOTICE`. NNS is a firm, storage-backed service, but today those rows are not recognised as firm. The desk wants a firm restriction on NNS handled like other firm-service disruptions. (No desk exists: the candidate posed this maintenance request.)

**Context selected automatically.** `make context TASK=recommendation-classification-maintenance` exited 0. It supplied the binding requirements and a source scope of `classifier.py` and `rebuilt/{normalized_classifier,normalization,rule_engine,source_input}.py`, plus pending learning marked unapproved and the superseded guidance.

**Requirements and decisions used.** The spec-predicates table and `FIRM_SERVICES`, the interface enums, `normalization.services`, SIGNAL-001/003, and the REMEDIATION decision rows.

**Source opened or searched** (from the transcript by `evidence/code-read-ledger/generate.py`; the session's own account understated it):
- read in full: `rebuilt/normalized_classifier.py`;
- read in part: `rebuilt/normalization.py` (lines 1–60), `tests/test_spec_predicates.py` (lines 1–80, after `make check` failed);
- grepped: `rebuilt/*.py` (service and FIRM), `rebuilt/rule_engine.py` (definitions), `harness/consequences.py` (definitions), `harness/*.py` twice (capture paths; service enums), `inherited/*.py` (NO_NOTICE);
- executed: two probe scripts that imported `harness.domain_rules.derive`, `harness.spec_compiler`, `harness.runtime` and `rebuilt.normalized_classifier`, to compare the harness oracle with the component on an NNS witness.

So it searched harness and inherited code and ran the harness oracle directly, beyond the five in-scope files. Before the remediation, a similar request made an earlier subagent open 14 source files, 9 of them harness modules, to find what "firm" meant; that session also edited the oracle (see `AGENT-NNS-A8F1AB8D` in code_reads.md).

**Additional human explanation required.** None.

**What changed.** spec.md only, through the proposal and consequences steps:
- `NO_NOTICE` normalizes to a new `NO_NOTICE_FIRM` value (the source distinction is kept);
- `NO_NOTICE_FIRM` joins `FIRM_SERVICES` and the four service enums;
- decision row `NNS-FIRM-001` is marked **proposed**.

Generated files were recompiled. No component or harness code changed.

**Gate results.** `make consequences`: 0 of 46 captured outcomes change. The only captured NNS row (46528, labeled negative) is a partial hourly limit and correctly stays non-firm. `gate --proposal` gave the same result before and after: Gate 1 PASS, Gate 2 PASS, Gate 3 UNKNOWN (EVALUATOR_OR_ORACLE_CHANGED, already present from the remediation). The desk view is unchanged: 2 of 7 positives missed and 0 false positives per capture. A scratch probe showed the component and the harness oracle agreeing: NNS unavailable → BR-FIRM; NNS partial and interruptible → unresolved.

**New learning, retained for the next session.**
1. A test matched the literal `FIRM_SERVICES` text, so any real edit of the set broke it. The coordinating session fixed the test in the same commit that adopted the NNS policy; an evaluator change and a policy change should not share a commit.
2. No labeled or frozen NNS outage exists, so the intended effect is unmeasured. The owner should add an NNS-unavailable witness; that is an oracle change.
3. The desk should confirm that a partial NNS limit stays non-firm, as it does for primary and secondary firm service.
4. The package should say that service mappings and `FIRM_SERVICES` are spec-owned. The session's own code_reads.md entry names two component files; the transcript shows more (listed above).

**Owner decision:** NNS-FIRM-001 approved on 2026-09-28 and covered by the owner's reread. Still open: an NNS-unavailable witness.
