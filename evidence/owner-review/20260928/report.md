# Thomas Hand review and clean offline gate

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

Previous commit: `4cb4b278364900b9961138dedfb8ef5a96f12e87`. Spec-to-spec consequences with current fixed compiler; not a runtime regression mapping

| Notice/capture | From | To |
|---|---|---|
| — | No changed outcome observed | — |


[Every nonmatch and first failed condition](clean-gate/consequences.md) · [Spec with its generated consequences](clean-gate/spec-rendered.md).

Thomas Hand is recorded as repository owner and named human reviewer of the exact normative spec for this assessment, covering ARCH-SOURCE-001 and TZ-NGPL-002. The [owner assertion](../../../context/spec-owner-review.json) contains the supplied instruction and exact decision bodies. The [generated read receipt](../../../context/spec-read-pin.json) pins that record and this unchanged spec:

`c7a3898dab4f2acb0e2123ed218449023e3fbec94d9bd0b1704376605afaac1f`

This review is not InCommodities approval, production authorization, cryptographic authentication, materiality approval, recommendation authorization or delivery authorization. It does not make UNKNOWN lifecycle obligations pass. No completed independent evaluation is claimed.

The unchanged spec retains its earlier PENDING_PERSON placeholders. A detached identity assertion resolves those names only for these reviewed bytes. Editing the placeholders would have changed the identity being reviewed. Receipt validation now accepts the explicit record, checks all covered decision bodies and statuses, and refuses stale spec bytes, conflicting names, rejected decisions, record drift or an escalated scope. Existing named-in-spec receipts remain supported. Business policy was not changed.

## Clean execution and gate results

Execution commit: `d9ed00f1c6a4ffcc5f32b4303df5d6653733d2ef`.

Checkout: `/Users/thomashand/.codex/worktrees/owner-review-clean/incommodities-take-home`. Git status, including untracked files, was empty before checks and immediately before the gate. Tracked status remained empty afterward. The existing pinned Python 3.14.7 environment was used without installing dependencies. The gate ran through the offline network/credential guard, with zero live model calls.

| Check | Observed result |
|---|---|
| Full make check | Exit 0; 179 tests pass; formatting, lint and mypy pass |
| Fresh compile comparison | Exit 0; generated artifacts unchanged |
| Exact read receipt validation | Exit 0; Thomas Hand and current spec identity |
| Gate 1: contracts and invariants | PASS within its bounded scope |
| Gate 2: trading behavior | UNKNOWN; 13 captured-label observations remain unscored |
| Gate 3: regression/change | UNKNOWN / NONCOMPARABLE; semantic/evaluator identity differs from the registered comparison reference, no approved mapping |
| Offline gate process | Exit 2; bounded and application acceptance both false |
| D-line checks | 41 scoped PASS, 32 UNKNOWN, 0 FAIL; identical to starting state |

[Command arguments, working directories, times, exits and log paths](clean-commands.json) · [Check stdout](check.stdout.txt) · [Test cases and results](check.stderr.txt) · [Gate stdout](gate.stdout.txt) · [Full run report](clean-gate/CURRENT.md) · [Raw results](clean-gate/results.json).

The receipt clears only the missing-name preflight refusal. UNKNOWN lifecycle evidence is still required. Synthetic publisher steps with fixture authorization are not real authorization or delivery.

## Preservation and boundary evidence

[Starting context](starting-context.json) records starting commit `4cb4b278364900b9961138dedfb8ef5a96f12e87`, selected context, the spec identity, 31 protected file hashes and all D-line observations. The [preservation check](preservation.json) shows no changes to spec.md, requirements, generated contracts, classifier.py, rebuilt components, domain rules or D checks. A fresh compile independently confirms artifact consistency. Thresholds, labels and recommendation authorization remain unchanged.

[Verification](verification.json) confirms that the clean execution's source matches its committed revision and the current source content identity `0593d815fe5129bf781639868fa2e8c815176d02e60a2d136fde94ce7c7aacb4`. The gate manifest was verified before and after copying its 350 indexed artifacts back to this checkout. [Additional rendering hashes](additional-renderings.json) cover byte-for-byte copies of consequences.md and spec-rendered.md, which the gate's JSON-focused manifest does not index. Evidence/report files are outside the source identity scope. No baseline was registered or repinned.

All 46 classifier outputs and projected actionability/publication outcomes match the earlier retained synthetic-receipt run. All 19 candidates retain UNKNOWN source timezone and REVIEW_REQUIRED; automatic current/future actionability is false, recommendation authorizations are zero, initial decisions are zero and publication attempts are zero. This recorded-output comparison does not override Gate 3's NONCOMPARABLE result.

An initial evidence assertion compared the old candidate-only 19-row projection against 46 new observations and reported 27 absent rows. The comparison was corrected to use the old full 46-row trading result. No classifier, rule, gate or expected label changed for that correction; the diagnostic is retained in verification.json. The report-copy step also found that the gate manifest excludes two Markdown renderings; those were copied separately and hashed without changing the gate.

## Files and commands

The [complete changed-file inventory](files-changed.json) names every changed or added file. The source/context changes are:

- `harness/spec_ownership.py`: explicit detached review validation and receipt generation; receipts cannot claim approval.
- `tests/test_spec_owner_review.py`: seven checks for preserved identity/artifacts/UNKNOWN, stale or tampered records, conflicting names, rejected decisions and review limits.
- `tests/authority_fixture.py`: copy the receipt's pinned identity record into isolated authority fixtures.
- `context/spec-owner-review.json`: supplied Thomas Hand assertion and exact decision bodies.
- `context/spec-read-pin.json`: generated current receipt.
- `context/spec-review-learning.md`: durable workflow and limits.
- `README.md`, `harness.md`: documented exact-spec binding, receipt command and external review boundary.
- `evidence/owner-review/20260928/`: starting context, generated receipt, preservation proof, clean-run script and logs, raw artifacts, verification, report and complete file inventory.
- `evidence/CURRENT.md`, `evidence/summary.md`: updated current evidence links and statuses; historical raw evidence preserved.

Pre-commit checks: 19 focused ownership/spec tests, lint, mypy and git diff --check passed. The clean checkout then ran the complete suite above. Receipt generation used:

```bash
.venv/bin/python -B -m harness reread --decision TZ-NGPL-002 --person 'Thomas Hand' --review-record context/spec-owner-review.json
```

The clean commands and receipts are retained by [run_clean_verification.py](run_clean_verification.py). On a new clean checkout, run `make check PYTHON=/path/to/python`, then `python -B -m harness gate --output evidence/NEW_RUN`. Output must be a new evidence directory. The current expected gate exit is 2 because UNKNOWN remains unresolved.

## Unresolved questions and retained learning

The owner/reviewer identity assertion is resolved for this exact assessment spec. Source timezone remains UNKNOWN unless a source supplies a trusted zone; no timezone support was found or assumed here. Full lifecycle/delivery/history and broader extraction evidence remain incomplete; the registered regression comparison still lacks an approved mapping. Review metadata resolves none of those obligations.

Human review is the supplied normative-spec review. The agent inspected receipt and harness source to implement this metadata workflow; no new human implementation-source read is asserted. Required human review on spec.md remains an external repository-owner/host responsibility. Local hashes provide consistency, not authentication.

Retained learning: bind a later-supplied reviewer identity to the exact reviewed bytes; preserve UNKNOWN and authority boundaries; compare matching evidence populations; retain clean execution identity separately from subsequent evidence-only commits. See [durable context](../../../context/spec-review-learning.md).
