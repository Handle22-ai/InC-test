> **Historical (archived 2026-09-28).** This records an earlier build pass. The Make targets and evidence paths it names were removed; the evidence stays at commit `8ea74f8` (see `evidence/ARCHIVE.md`). Current commands are in README.md. Do not follow the commands below.

# The Harness — evaluator-style repository review

**Purpose:** Review this submission as a skeptical technical evaluator, using the InCommodities North America **Technical Challenge: The Harness, v5** as the authority.

**Status:** Independent practice-review guide. This is not InCommodities’ private scoring rubric, an official grade, or a completed audit of the current repository. The brief supplies priorities but no numerical weights or letter-grade thresholds. Do not invent them.

**Central question:** Can an engineer own the specification and make defensible decisions from evidence, while agents implement and maintain the system without the engineer routinely inspecting source?

This guide distinguishes **assessment completion**, **harness credibility**, **component acceptance**, and **application autonomy**. These are different conclusions. A harness can correctly reject the inherited application and still be a strong assessment submission.

## Source and review conventions

Source references below refer to the original five-page challenge, expected in this submission at `docs/challenge/InC_Challenge_Tech_Lead_The_Harness_v5.pdf`. Locate and verify the actual document; do not substitute an AI-authored starter charter.

- **[C1] Page 1 — Objective, AI Tooling, Scenario, Structure.** The exercise is not a code review; the spec and harness receive most attention; false trading signals have asymmetric risk; tooling is the candidate’s choice.
- **[C2] Page 2 — Phase 1 and Phase 2.** Specification, state/history, derived checks, gates, evidence, change handling, context recovery, governance, costs and alternatives.
- **[C3] Page 3 — Phase 3, Phase 4, Time Expectation.** One rebuilt component, evidence-based findings, autonomy, genuinely fresh maintenance, code-read limitations, team conversation, and the eight-to-ten-hour timebox.
- **[C4] Page 4 — Deliverables, What We Pay Attention To, Why This Challenge.** Repository contents, reproducible README, declared evaluation priorities, candid limitations, and permission to document domain assumptions.
- **[C5] Page 5 — Trading Signal Definition and Pipeline EBB Sources.** Meaningful disruptions, typical signal characteristics, routine non-signals, duplicate superseding signals, and no requirement to scrape.

“Brief requires” describes source requirements. “Review method” and “strong evidence” are recommendations for assessing those requirements, not extra obligations silently added to the challenge.

---

## 1. Review posture: examine the work, do not improve it while grading it

Record the candidate commit, any uncommitted additions, review environment, and evidence available. Pin the review to that revision. A passing test of an earlier revision does not automatically verify the current one.

Review without changing application code, requirements, labels, acceptance thresholds, or historical evidence. Run commands in a separate checkout or disposable state where practical. Write only new review receipts. Do not run a second writing agent in the active development workspace.

Inspect command definitions before execution. Start with the documented offline workflow. Do not expose credentials, fetch capture references, or make live application model calls without separate authorization. Dependency installation may require approved package access; distinguish that from application network use.

Read the specification and evidence **before** using implementation source to diagnose findings. Targeted reviewer inspection of harness/adapters is appropriate when necessary, but record what it establishes. A reviewer’s source read is not a candidate’s historical human source read. Do not ask an agent to invent what the human personally inspected.

Use earlier audit reports as leads, not as current verdicts. Newer work may have closed their gaps. A polished later summary is also not a substitute for its underlying evidence.

### Evidence strength

Label the support for each conclusion:

| Evidence level | Meaning |
|---|---|
| **Claimed** | Described in a summary, README, or operator message. |
| **Inspected** | The underlying requirement, inputs, logs, outputs, or metadata were read and support the claim. |
| **Recomputed** | Counts or conclusions were independently derived from retained raw artifacts. |
| **Reproduced** | The documented execution was rerun for the identified revision and its relevant result observed. |

A historical live-model experiment can have strong inspected/recomputed evidence without being rerun. Do not require fresh stochastic calls merely to give every row the same evidence label.

### Assessment status

Use **DEMONSTRATED**, **PARTIAL**, **NOT DEMONSTRATED**, **CONTRADICTED**, or **NOT ASSESSED**, always with scope and evidence. Mark genuinely optional work **OPTIONAL**. An unavailable artifact is unverified, not automatically a proven code defect.

Do not confuse these review statuses with the application’s PASS/FAIL/UNKNOWN/ERROR findings.

---

## 2. The reviewer’s first pass

Within a short initial read, the repository should make the following understandable:

1. What the inherited system is supposed to do and which specification is authoritative.
2. What the harness actually derives and executes, versus what remains authored manually.
3. What it found, what was rebuilt, and which claims the evidence supports.
4. Whether a genuinely fresh agent maintained the component using persisted context.
5. How to reproduce the demonstration and what remains unsafe or unproven.

**Review method:** Start with the original brief, README, `spec.md`, `harness.md`, coverage, and the current evidence index. A difficult navigation experience is a handoff finding, not an automatic failing grade.

For this candidate, the reported command surface is:

```bash
make help
make setup
make demo
make check
make context TASK=notice-snapshot-maintenance
```

Verify these against the actual checkout before running. They are not commands prescribed by InCommodities. Do not assume the reconstructed historical replay has the same targets as the polished candidate.

---

## 3. Phase 1 — Can the engineer own the specification? [C2]

### Brief requires

An implementation-independent specification covering purpose, input/output contracts, required behavior, refused failure modes, cross-scrape memory, earlier notices, revisions, already-signaled events, missing/late/reprocessed notices, and history sufficient to explain past decisions. It should be precise enough for an agent to implement and a harness to derive checks without another person translating intent.

### Review method

Read the current specification itself. For each important behavior, identify the input/precondition, required result or state transition, forbidden result, and evidence that would establish it. Requirement IDs aid traceability but are not proof of precision.

Inspect lifecycle decisions particularly carefully:

| Area | Question the specification should answer |
|---|---|
| Identity and replay | What counts as the same notice, source version, or event? What must remain unchanged on reprocessing? |
| Revisions | How is a genuine revision distinguished from a replay? What is updated, retained, suppressed, or reconsidered? |
| Already signaled | What decision/delivery memory is required, and what must not be emitted again? |
| Missing/late/out-of-order | What is actionable, which clock/order is authoritative, and what happens when needed history is unavailable? |
| Explanation | Which source, state, policy and decision versions must remain available to explain an earlier result? |
| Invalid/uncertain input | What is rejected, deferred, marked unknown, or routed to review rather than silently converted into a normal decision? |

Do not invent lifecycle policy on the candidate’s behalf. Check whether the author has made precise assessment assumptions where the domain is underspecified. The brief permits documented assumptions; it does not require external stakeholder approval for every assessment choice. [C4]

**Strong evidence:** A second engineer can explain how a new case should behave from the spec alone. Implemented, evaluated, assumed, and unresolved behaviors are visibly separated.

**Concern:** The spec says “handle gracefully” or “avoid duplicates” while identity, failure disposition, and history semantics exist only in code. An UNKNOWN check cannot substitute for undefined intended behavior.

**Fair judgment:** The entire system’s intended behavior must be addressed, but the brief only requires rebuilding one component. Specifying an unimplemented behavior is not the same as falsely claiming it works.

---

## 4. Phase 2 — Does the harness replace routine source inspection? [C2]

### 4.1 Derivation, not just matching labels

**Brief requires:** Tests, contracts, and evaluations should come from the specification rather than being independently hand-written.

**Review method:** Trace representative requirements into the executable check plan. Include the headline storage invariant and another relevant family, such as an output contract or labeled behavior check. Inspect actual executable inputs, not only prose assertions that “checks are derived.”

```text
Requirement / approved assumption
→ machine-readable rule or other derivation mechanism
→ strategy and case selection/transformation
→ concrete expected result or oracle
→ executed result
→ retained evidence and acceptance decision
```

Determine where expected values originate: schema, invariant, supplied annotation, explicit policy, or judgment. A generic check engine can be handwritten. A manually authored requirement can configure it. Those are different from separately writing every application-specific test and attaching IDs afterward.

Ask what happens when a relevant requirement parameter changes. Would the planned check change mechanically? Establish this from artifacts or an isolated derivation-only probe, not by altering approved requirements in the submission.

**Strong evidence:** The mapping is executable, inspectable, and reproducible. Ordinary infrastructure or extension tests are honestly distinguished from spec-derived checks.

**Concern:** Prose and YAML are two independently edited authorities; the rule only selects a bespoke test that embeds the real policy elsewhere; tests mirror the implementation’s mistake. Do not demand a general natural-language-to-test compiler or a particular serialization format.

### 4.2 Gates that constrain acceptance

**Brief requires:** Explain what a build must pass, what failures cannot be hidden, and each gate/check’s purpose, cost, and alternatives. “Three gates with teeth” expresses a preference for meaningful controls, not an exact gate-count mandate.

**Review method:** Inspect the actual acceptance path. Identify scope, mandatory checks, unknown/error treatment, prerequisites, approval exceptions, and whether observed failures can block acceptance. Separate evaluator execution from release authorization.

Use existing synthetic controls where available to test zero evaluated cases, invalid output, an execution error coexisting with a requirement failure, and proposed assumptions that must not silently change binding policy. Do not add a large testing project during the audit; report missing coverage.

**Strong evidence:** Results and acceptance are explicit, failure cases remain visible, and a successful measurement command cannot be mistaken for permission to deploy.

**Concern:** Everything exits zero with a green headline; missing evidence passes; failed checks are dropped; thresholds are adjusted after seeing results. A report-only manual approval workflow can be legitimate if its boundary is explicit—do not invent a mandatory deployment pipeline.

### 4.3 Evidence surface and change handling

**Brief requires:** The engineer can decide trust from the evidence; failures lead back to specification/context; model and specification changes are handled deliberately; the engineer’s first day is described.

**Review method:** Follow the reading path from a summary to raw inputs, outputs/state, check results, and versions. Check model/configuration identity, source revision, dataset identity, environment, and known missing metadata. Recompute a metric and compare like-for-like cases. Examine one retained failure and the requirement clarification or implementation correction it prompted.

Not every defect needs a requirement change: if existing intent was sufficient, the implementation may be wrong. The important part is explicit diagnosis and durable learning, not weakening the spec to make a result pass.

**Strong evidence:** An engineer can answer what ran, why a check failed, what changed, and what remains unknown without immediately reading application code.

**Concern:** Several stale “current” summaries conflict; a synthetic input is presented as real; model-upgrade effects are mixed with storage changes; green regression is presented as complete correctness.

### 4.4 Context and authority beyond the chat

**Brief requires:** Requirements, assumptions, decisions, known failures, context selection/loading, supersession, approval responsibility, and learning survive into the next session.

**Review method:** Use the documented selector. Inspect the actual package, inclusion reasons, authority/status, and current references. Verify one learned failure or decision appears in later selected context. Check how conflicts and superseded instructions are handled.

**Strong evidence:** The task can be understood and maintained from durable artifacts; the package is current and bounded; added explanation is recorded.

**Concern:** Hidden conversation memory is the real knowledge store; the manifest points to stale content; proposed policy becomes authoritative silently. Explicit task profiles are an acceptable bounded design—arbitrary repository decomposition or multi-agent routing is not required.

---

## 5. Phase 3 — Does execution prove the claims? [C3]

### 5.1 Meaningful rebuild and fair comparison

**Brief requires:** Rebuild at least one component from the specification through the harness without the candidate reading its generated code; use evidence to surface inherited defects and judge autonomy.

**Review method:** Identify the chosen component boundary and why it matters. Verify task/spec/context artifacts, the rebuild chronology, and the checks actually applied. Compare implementations on equivalent scoped inputs and state. Ensure an adapter is not repairing the inherited output before measuring it.

**Strong evidence:** A meaningful component is independently implemented, the same relevant contract judges both versions, and improvements do not destroy required history or collapse distinct identities.

**Concern:** A configuration tweak is represented as the complete rebuild; cleanup of copied code is presented as independent generation; different model outputs create an unfair storage comparison; the candidate’s acceptance depends on reading every generated source file.

An agent may read implementation code. Do not conflate that with the human candidate doing so. Separate evaluator inspection from the candidate’s original workflow.

### 5.2 Defects, trading relevance, and limits

The brief describes meaningful flow/price disruptions, typical strong-signal characteristics, routine non-signals, and duplicate superseding signals. False trading signals have asymmetric risk. [C1, C5]

**Review method:** Inspect actual supplied labels and retained notices behind a disagreement. Separate classification disagreements, extraction issues, execution/fallback behavior, persistence defects, and delivery guarantees. Verify case counts and denominators. An unscorable semantic result may still supply structural or error-handling evidence.

Treat “typically” as “typically.” Do not insist every strong signal contain every listed field, invent curtailment thresholds, or approve exploratory field oracles on the candidate’s behalf.

**Strong evidence:** A few risk-relevant findings with inspectable examples, explicit assumptions, and a bounded autonomy decision.

**Concern:** Aggregate accuracy hides false signals; multiple assertions become multiple independent bugs; duplicate child rows are called duplicate trader alerts; unseen/unlabeled notices are assigned an accuracy score without ground truth.

Do not require every inherited defect to be repaired, a large new corpus, production trading integration, or live scraping. Unlabeled-corpus evaluation is optional. Record sampling and semantic uncertainty instead of requiring invented certainty.

### 5.3 Actual fresh-session maintenance

**Brief requires:** A genuinely fresh session without the original conversation makes one small maintenance change, recovers relevant requirements/decisions, checks prior behavior, and retains learning. The starting request, selected context, extra human explanation, and resulting evidence must be recorded.

**Review method:** Inspect the actual launch/session observations, request, pre-change baseline, selected package, implementation diff, before/after results, and newly retained context. “Prepared,” “launcher ready,” or “context recovery succeeded” is not implementation evidence.

Prior coding conversation visibly supplied means that run does not satisfy the stated condition. A different model, a new title, or a new identifier alone is insufficient. Repository-persisted decisions and failures are intended context, not contamination.

A replay must be labeled as a replay and start from a verified pre-change state. State prior exposure to the completed solution; do not retroactively certify earlier attempts or claim unseen novelty. Judge the observed exercise against the brief without inventing a requirement for cryptographic proof of hidden platform state, root-only Git objects, or OS-level isolation. Such controls may strengthen a demonstration but are not specified mandates.

**Strong evidence:** The agent actually changes the component using recorded durable context, preserves applicable behavior, and makes new learning available to another session.

**Concern:** Only preparation ran; existing completed code was retested; a parent transcript or compacted history supplied the answer; extra human coaching was omitted. Honest technical maintenance can receive credit separately from an unmet no-prior-conversation condition.

### 5.4 Where the harness still needs code reads

**Brief emphasizes:** The candid map of necessary code reads and evidence gaps is one of the most important discussion artifacts.

**Review method:** Read the candidate’s code-read ledger and limitations. For a reported human read, ask what the evidence could not establish, why source inspection helped, and whether observability or checks improved. A legitimate unresolved limitation is acceptable.

Do not demand a fabricated human read when none occurred. Instead assess whether the workflow and evidence substantiate the statement and whether the candidate understands what remains opaque. Agent/tool reads should be recorded separately.

---

## 6. Deliverable usability and professional engineering [C4]

Verify the private submission contains `spec.md`, `harness.md`, harness code, rebuilt component, coverage including code reads and maintenance, repeatable context artifacts, and a README explaining harness execution and fresh-session startup.

Test what is actually delivered. A working directory containing untracked code, external receipts, or local-only fixtures is not automatically a complete Git handoff. Pin source and evidence identities; a later evidence-only bundle can truthfully document an earlier tested commit without pretending the later revision was itself fully tested.

**Review method:** Follow the README in a separate clean checkout with declared dependencies and no reused project environment. Record supported platform/runtime, actual commands, generated links, fixture access, exit semantics, and model-call prerequisites. Live provider evaluation needs credentials; a captured offline demonstration need not prove fresh model correctness.

Assess code quality proportionately to the user’s engineering goals. Check configured formatting, lint, typing, tests, dependency reproducibility, interfaces, error behavior, and stated exclusions. Report exactly what was run. Non-strict typing is not strict typing; syntax parsing is not type checking.

The brief says code craftsmanship is not scored. Do not let cosmetic perfection, cross-platform expansion, or extra static tooling outweigh missing specification/maintenance proof. Equally, broken setup or concealed failures undermine the requested engineer workflow.

Preserve historical evidence. Update current navigation deliberately. A large evidence archive can be acceptable when its index makes the few decisive artifacts easy to inspect; file volume is not an achievement metric.

---

## 7. Candidate-specific spot checks — investigate, do not assume

These are targeted questions based on previously supplied reports. They are not a current audit result. Verify the latest candidate and latest worker output before assigning status.

| Claim area | What to check | What not to conclude |
|---|---|---|
| `STATE-002` | Trace the recorded duplicate case: expected 1 notice/1 location/3 restrictions versus inherited 1/2/6 and rebuilt 1/1/3. Inspect identical captured input, state, oracle, raw output and adapter behavior. | One trace establishes all lifecycle behavior. |
| 200 → 512 token experiment | Verify the one-setting variant, successful but truncated responses, helper/fallback behavior, declared trial progression, and separate candidate identity. | Newly scorable cases prove corrected classifications; provider success proves a usable verdict. |
| Frozen case `46528` | Compare the supplied label with the captured output and preserve the reported mismatch in scoped comparisons. | Frozen replay is a new model prediction, or a label mismatch proves an undisputed domain conclusion. |
| Persistence improvement | Distinguish duplicate observations, one defect family, three scenarios and nine overlapping improved assertions. Check retained prior links and separate missing-prior unknowns. | Duplicate rows prove duplicate delivered alerts; reopen proves crash/acknowledgement recovery. |
| Optional-field and alias maintenance | Inspect native-reader extension checks separately from the shared contract, compatibility direction and historical writer fixture. | Inherited support for the extension, improved trading decisions, or automatic satisfaction of fresh-session isolation. |
| Latest engineering candidate | Verify the operator-reported commit `f7de5a5094a33c3b53cff33cede071e7c79127bd`, 64-test/29-file tooling scope, clean-clone receipts and delivery of those receipts. Prefer actual latest artifacts if the revision changed. | Earlier reports saying tools were unavailable remain current; uncommitted receipts are already delivered. |
| Lifecycle proposal | Inspect whether precise intended behavior is now adopted as an explicit owner assumption/requirement or remains proposed. | Polished docs resolve an open policy; old evidence validated newly adopted rules. |
| Isolated replay | Locate the actual worker run and retained learning, if completed. Compare its baseline with the declared reconstruction and record observed launch context. | `READY_TO_LAUNCH_WORKER` or successful reconstruction means maintenance has occurred. |

Historical numerical anchors above come from the supplied audit/rebuild/maintenance records. The polished-candidate identity and readiness details came from operator-pasted reports and require fresh inspection. Do not hardcode any of these numbers as required future test outcomes.

---

## 8. Phase 4 — Rehearse the evaluator conversation [C3]

Repository evidence can prepare this conversation, but cannot establish how the candidate will actually collaborate in it. Ask the following without scripting a single “correct” answer:

| Question | Listen for |
|---|---|
| Why rebuild persistence rather than the entire classifier? | Evidence-led boundary selection, controlled comparison, limits, and timebox judgment. |
| Show me how one check comes from the specification. | A live trace and honest distinction between authored policy, derivation, labels, and generic machinery. |
| Why can the demo succeed while gates fail? | Measurement completion versus acceptance, explicit scope, and no concealment of failures. |
| What happens when a model or specification changes? | Versioned intent, reevaluation, comparability, retained evidence and controlled approval. |
| What happens when a revision arrives before its original? | A precise rule or explicit remaining gap, not a confident invention after the fact. |
| What did the fresh agent actually recover? | Selected context, decisions, prior failures, extra help and new retained learning. |
| Where did you still need code? | Honest escalation reasons and an understanding of missing evidence. |
| I trust reading the PR more than your harness. Why change? | Listening to the missing assurance, offering evidence, allowing justified inspection, and adjusting the approach rather than defending a slogan. |

The brief explicitly permits holding, adjusting, or dropping a position with reasons. Do not reward ideological claims that engineers must never read code. Judge whether the candidate can bring a skeptical colleague along.

---

## 9. Conclude without inventing an official grade

Use the brief’s stated emphasis: specification and harness first; executed evidence, cross-session maintenance, risk judgment and honest limits alongside them. Code volume, architecture sophistication, model branding, and all-green application results are not substitute criteria. [C1, C4]

For internal assessment only, use one of these **provisional review outcomes**:

- **Strong evidence against the brief:** The central workflow and required demonstrations are supported; shortcomings are explicit; only bounded delivery or optional work remains.
- **Credible partial submission:** Useful spec/harness/component evidence exists, but a required behavior or demonstration remains incomplete or only reported.
- **Insufficiently substantiated:** Important conclusions cannot be traced or reproduced, or the harness’s independence/authority is mostly asserted.

These are review labels, not predicted InCommodities grades. Do not turn missing proof into an invented numerical penalty or automatic hiring verdict. Candid partial work is explicitly permitted; assess what is demonstrated and disclose the gap. [C3]

Separate final findings into **required proof gaps**, **evidence-credibility issues**, **delivery/reproducibility blockers**, **known application limitations**, and **optional improvements**. Recommend at most three highest-value next actions. Do not create another unbounded feature backlog.

---

## 10. Required output from the reviewing agent

Create a new review report, with supporting receipts in a new directory, using this structure:

```markdown
# Evaluator-style review — The Harness v5

## Review identity and limits
Candidate commit and worktree state:
Original brief verified:
Review environment and context sources:
Artifacts inspected:
Commands reproduced:
What was not inspected or executed:

## Executive assessment
Provisional review outcome and scope:
Strongest demonstrated evidence:
Most consequential missing proof:
Separate component/application acceptance conclusions:

## Requirement-by-requirement assessment
| Brief page/section | Criterion | Status | Evidence level | Actual artifact/result | Limit or concern |
|---|---|---|---|---|---|

## Three decisive evidence trails
1. Requirement → derived check → inherited result → rebuilt result.
2. Execution/semantic failure → retained evidence → bounded conclusion.
3. Fresh-session request → selected context → change → checks → learning.
Mark any unverified trail explicitly.

## Reproducibility and evidence integrity
Commands, outputs, exits, clean-environment scope, versions and receipt paths.
Counts recomputed; exclusions and overlapping assertions; source preservation.
Evaluator completion versus acceptance behavior.

## Specification, context and governance
Lifecycle precision; assumption status; derived/manual coverage;
source/rule consistency; supersession; approval; model/spec change handling.

## Professional quality and delivery
Actual checks and exclusions; README usability; portable artifact delivery;
private-sharing status where verifiable.

## Conversation readiness
Questions the candidate can answer from evidence; remaining judgment gaps.

## Findings and next actions
Required proof gaps:
Evidence-credibility issues:
Delivery blockers:
Known application limits:
Optional improvements:
Top three actions, with a bounded definition of done:
```

For every material claim, cite the actual repository-relative artifact and line/section, run ID, or JSON field. Do not cite a summary as though its raw evidence was inspected. Retain command outcomes in the new review directory; do not rewrite old reports or fix the submission while reviewing it.

### Short kickoff request

```text
Review this repository using EVALUATOR_REVIEW.md and the original
InCommodities “The Harness v5” brief.

Act as a skeptical technical evaluator, not an implementation agent.
The brief is authoritative; the review guide is an independent method,
not an official grading rubric or permission to expand the assignment.

Pin the reviewed revision. Inspect current spec, harness, coverage,
context, evidence, and delivery. Verify representative raw claims and
reproduce the documented offline workflow in isolated state where
feasible. Report current facts rather than recycling stale audit gaps.

Do not edit source, policy, labels, or historical evidence. Do not make
live application model calls or expose credentials. Write only new
review artifacts and receipt logs.

Evaluate all four phases and distinguish required proof gaps from known
application failures and optional polish. Do not inflate test/file/check
counts into independent evidence. Do not certify prepared replay as
executed fresh-session maintenance.

Produce the report in Section 10. Give an evidence-backed provisional
assessment, no guaranteed grade, and at most three high-value next actions.
```

**Final test:** Can the reviewer understand intent, follow one real proof, reproduce the relevant result, see how a new session maintained it, and identify the limits without discovering that the headline claims were overstated?
