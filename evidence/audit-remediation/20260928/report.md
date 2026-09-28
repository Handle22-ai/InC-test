# Audit correction at e49b478

## Generated consequences of this spec

Captured cases: **46** (two 23-case captures; 14 labels per capture). No abstention is a correct negative.

| Rule | Matches / cases | Wins / cases | First failed conditions (counts) |
|---|---:|---:|---|
| BR-FORMAT | 0/46 | 0/46 | Format: 46 |
| BR-SEMANTICS | 2/46 | 2/46 | Oracle answer: 44 |
| BR-CONTRADICTION | 3/46 | 3/46 | Conflict: 43 |
| BR-HISTORY | 4/46 | 3/46 | History: 42 |
| BR-UNCHANGED | 4/46 | 4/46 | Operational change: 42 |
| BR-ROUTINE | 6/46 | 6/46 | Information-only: 37; Restriction: 3 |
| BR-HISTORICAL | 0/46 | 0/46 | Restriction current: 24; Service class: 22 |
| BR-FIRM | 24/46 | 19/46 | Service class: 22 |
| BR-UNRESOLVED | 46/46 | 9/46 |  |

Previous commit: `51b74caf1a6b372dea65d90deda3f3290674a502`. Spec-to-spec consequences with current fixed compiler; not a runtime regression mapping

| Notice/capture | From | To |
|---|---|---|
| — | No changed outcome observed | — |


[All nonmatches and first failed conditions](clean-gate/consequences.md).

The supplied audit of `51b74caf1a6b372dea65d90deda3f3290674a502` is retained as [supplied-audit.txt](supplied-audit.txt). The D1 wording defect and stale entry instructions were defects, not limitations excused by the existing disclaimers. This pass corrects the harness and evidence workflow while preserving the reviewed business policy.

Tested source commit: **`e49b4782105518211ad503513b275c2c26062dea`**. Source content SHA256: `c26d7c76aaaebbb9d734e1736c951c587d215fef15e3cecca67197ef58afb914`. The later retention commit changes only evidence.

The spec remains **`c7a3898dab4f2acb0e2123ed218449023e3fbec94d9bd0b1704376605afaac1f`**, policy `assessment-v4-timezone-separation-20260928`. Thomas Hand's existing exact-spec assertion and read receipt remain valid for those same bytes. No business rule, threshold, expected label, classifier output schema, candidate scope or recommendation authorization changed.

## Verified corrections

- D checks now bind both the hand-authored check and exact sentence hash. Inverting D1-005 cannot inherit PASS, even after compiling and generating a new named receipt: it reports D_SENTENCE_CHANGED / UNKNOWN and prevents component execution. Compile/reread cannot silently rebind a check. A normal PASS remains a bounded compiled constraint, not proof of every clause in a sentence.
- Independent preflight refusals are collected. A contradiction and stale receipt appear together, with full D_SENTENCE_CONTRADICTION codes and all applicable sentences, including D5-001. They belong to Gate 1; unexecuted Gate 3 says NOT_RUN. Parser failures name the field, raw value, capture, stable row and spec line.
- The existing reviewed assumption registration is checked again by the gate, context selector and offline entrypoints. A-004 cannot be changed without a refusal. The registered assumption view is included in context; its older implementation limits are identified as historical.
- The effective model configuration is compared with captured identities. A bogus override reports MODEL_CONFIG_CHANGED without executing a live model. Synthetic SDK observations identify their configured model as synthetic-provider.
- Python gate exits now distinguish PASS 0, usage 2, UNKNOWN 3, FAIL 4 and ERROR 5. ERROR outranks FAIL, which outranks UNKNOWN. GNU Make still collapses failed recipes to 2; direct Python is the CI interface. The classifier CLI's existing stdout and exits are unchanged.
- Current entry documents no longer instruct a reader to edit generated YAML, synchronize Markdown/YAML, expect current Gate 3 PASS, or rely on the obsolete temporal self-promotion scheme. Historical ADR bytes remain intact; the decision index marks 007/011 superseded by the spec-decisions block.
- Coverage is generated from each run and stamped with policy/spec/run/commit identity. It separates finite scoped observations from full UNKNOWN obligations. One fresh-session index links current-component recovery and accurately scopes earlier storage exercises. Later code reads are indexed, including the explicitly unrecoverable b9cd042 inventory gap.
- Live refusal handling writes one receipt per invocation, retaining the first concrete cause. This is tested with synthetic failures; no live call was made and historical duplicate receipts were not rewritten.
- Baseline registration uses the active exact-spec receipt and clean-source checks, rather than the obsolete ADR promotion verifier. No baseline was registered in the main repository; temporary reference registration was confined to the regression proof clone.

[Disposition of every audit finding, including unresolved questions](findings-disposition.json).

## Clean execution

The managed checkout `/Users/thomashand/.codex/worktrees/audit-correction-clean/incommodities-take-home` started at the exact tested commit with empty tracked and untracked Git status. Status was still empty immediately before the gate; no tracked changes remained afterward. The existing Python 3.14.7 environment was used without network installation.

| Command | Result |
|---|---|
| make check with recorded Python | 185 tests PASS; formatting, lint and mypy PASS |
| harness compile --check | PASS; generated artifacts unchanged |
| Python offline gate | Exit 3; Gate 1 PASS / Gate 2 UNKNOWN / Gate 3 UNKNOWN, NONCOMPARABLE |
| evaluate-spec, twice | Both PASS, CONTRACT_WITNESSES_AGREE; identical fixture hash below |
| Current maintenance context | Complete selected rows retained in JSON; Markdown 53,926 bytes / 568 lines |

Semantic fixture SHA256: `cc64faba96c0e7f30290e6dff7549d23a097991cd8d390e423163229821a1197`.

[Exact clean commands and logs](clean-commands.json) · [check results](clean-check.stderr.txt) · [gate stdout](clean-gate.stdout.txt) · [run results](clean-gate/results.json) · [generated coverage](clean-gate/coverage.md) · [verification](verification.json).

The full run has 426 files, with 353 gate-manifest hashes verified before retention and again inside [clean-gate.zip](clean-gate.zip). The 2,119,583-byte archive includes raw JSON, reports, inputs and SQLite evidence. Its SHA256 is `aeda2f3d6a2fe0daa82ac08746125d04a6200212c378859dced45396d244bf8f`. Extract it to a fresh scratch directory to inspect the complete original CURRENT.md, spec rendering and individual receipts. Selected result/coverage files remain directly readable alongside this report. Existing historical evidence was preserved; new raw runs are compressed rather than adding hundreds of loose files per replay.

## Mutation and regression evidence

The [corrected mutation script](mutation_proofs.py), [commands](proofs-corrected/commands.json) and [assertion summary](proofs-corrected/summary.json) run only in a disposable clone of the tested source. Every invented reviewer/decision in those controls is explicitly synthetic.

| Control | Observed outcome |
|---|---|
| D1 “at least one”, before reread | Exit 5; stale receipt and changed sentence retained |
| Same inverted sentence after named synthetic reread | Exit 3; D1-005 UNKNOWN / D_SENTENCE_CHANGED; no component cases run |
| BR-CONTRADICTION changed to candidate | Exit 5; D2/D5 contradictions and stale receipt retained together |
| A-004 changed from block to allow history-gap alerts | Gate exit 5, named A-004 refusal; context also refuses |
| Month/day format changed | Exit 5; identified fields/raw values and source captures |
| Generated behavior.yaml edited | Exit 5; GENERATED_ARTIFACT_DRIFT |
| --skip-live passed to offline gate | Usage exit 2 |
| Bogus model environment | Exit 3; Gate 3 MODEL_CONFIG_CHANGED; synthetic execution remains labelled synthetic |
| Actual classifier code drops detailed provenance references | Gates 1/2 remain PASS/UNKNOWN; Gate 3 FAIL, Python exit 4 |
| Classifier restored against the same temporary reference | Gates 1/2 remain PASS/UNKNOWN; Gate 3 PASS, Python exit 3 due to trading UNKNOWN |

The last two rows demonstrate a concrete Gate 3 contribution: an unexpected output/provenance change that the finite contract/trading observations did not reject. This is deliberately injected fault evidence, not a claim that Gate 3 catches every regression. Semantic changes without a justified mapping remain NONCOMPARABLE.

The [first proof attempt](proofs/commands.json) correctly detected the code regression, but its restore step also reset the tracked temporary reference pointer. Gate 3 consequently returned NONCOMPARABLE; the script's expected-PASS assertion failed. The [diagnostic](proof-first-attempt-diagnostic.json) and original script/receipts are retained. The corrected restore touches only the classifier, keeping the temporary reference. No expected labels, main reference or harness result were changed to make the control pass.

Development test failures are retained too: the first compact-context fixture used an empty string rather than the established null reference convention, and the new isolated assumption test omitted authority files from its fixture. Both fixture/rendering issues were corrected; all 185 tests subsequently passed. The initial inverted-D1 PASS observation is in [before-probes.json](before-probes.json).

## Unchanged behavior and remaining questions

All 27 protected spec/requirements/generated-contract/classifier files match their starting hashes. All 46 recorded classifier outputs are unchanged. D checks remain 41 scoped PASS / 32 UNKNOWN / 0 FAIL. All 19 candidates retain UNKNOWN timezone and REVIEW_REQUIRED, with zero captured recommendation authorizations and publication attempts. The main regression reference was not repinned. Gate 2's 13 unscored observations and the 32 broader UNKNOWN D obligations remain unresolved.

**Audit #13 remains a pending business-policy decision.** The retained [synthetic critical/informational input](critical-informational-probe.json) produces [NON_SIGNAL / NO_SIGNAL](critical-informational-output.json). It establishes the reported risk path; it does not prove source criticality alone is a material disruption. The [proposed amendment](../../../context/pending-learning/audit-critical-informational.md) would require UNRESOLVED / REVIEW_REQUIRED for source-confirmed criticality conflicting with a model-only informational conclusion, without inferring a candidate or authorizing a recommendation. It has not been activated.

The reviewed spec's five-versus-six refusal-control count remains a recorded editorial discrepancy; its table and current guide identify all six. Fixing that prose changes the spec identity and needs a new review. Unused ANY columns, spec restructuring, desk latency, second-human/host enforcement and a live v4 inherited evaluation remain explicit questions or unverified limits. No fresh-agent usability timing or new independent evaluation is invented. See [contract questions](../../../context/pending-learning/audit-contract-questions.md).

The current workflow is candidate review, not paging, recommendation approval or delivery. No materiality approval, InCommodities approval, production authorization, production acceptance, cryptographic authentication or completed independent evaluation is claimed.

## Records and retained learning

[Starting context and protected hashes](starting-context.json) · [every changed file](files-changed.json) · [code-read ledger](../../code_reads.md) · [fresh-session index](../../fresh_session.md) · [old entry documents](entry-docs-before/README.md) · [final context package](final-context/package.md).

Retained learning: an ID is not a sentence's meaning; changed wording must invalidate an old check binding. Invocation boundaries should own failure receipts. Context inclusion should preserve exact authority without repeating whole schemas and machine rows. An evidence restore must not silently restore its comparison reference. Historical approval records and source-read gaps must be labelled rather than retroactively rewritten. Pending policy decisions stay outside executable business behavior.
