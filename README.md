# The Harness

The engineer owns [spec.md](spec.md) and reads [evidence/CURRENT.md](evidence/CURRENT.md). Coding agents maintain the implementation. The rebuilt component is `NormalizedNotice + EventHistory → SignalDecision` in `rebuilt/`. Its output is a candidate, never a trading recommendation. (The replay tests drive a downstream publisher seam with synthetic authorization, and that seam reports `INITIAL_RECOMMENDATION` so duplicate suppression can be checked. No real recommendation path exists.)

This repository starts from one commit; the earlier working history is described in [evidence/ARCHIVE.md](evidence/ARCHIVE.md). [harness.md](harness.md) explains the three gates, what each costs and what it would miss. The code-read map is [evidence/code_reads.md](evidence/code_reads.md).

## Run the harness (offline, no API key)

Needs Python 3.14+, Git and Make. `make setup` downloads pinned packages; everything after it is offline.

```bash
make setup      # venv and pinned dependencies
make check      # format, lint, types, tests
make compile    # spec.md -> requirements/*.yaml and schemas; refuses boundary violations
make gate       # the acceptance run: needs the owner's reread of the current spec bytes
```

`make gate` refuses (exit 5) until the owner has reread the current spec. To measure an unreviewed spec without accepting it, run:

```bash
.venv/bin/python -B -m harness gate --proposal
```

Each run writes `evidence/normalized/<time>/CURRENT.md`. It leads with the desk view: labeled positives missed and labeled negatives signaled, per capture. It also lists what the gate does not claim.

| Python gate exit | Meaning |
|---|---|
| 0 | All three gates pass on a reviewed spec |
| 3 | Something in scope is UNKNOWN, or the run is proposal-only |
| 4 | An established failure |
| 5 | Refused before running: stale review, drifted generated files, or a boundary violation |

CI (`.github/workflows/gate.yml`) runs `make check` and the gate, and passes only on exit 0. Make reports any failure as exit 2.

**What makes the owner's review real:** in GitHub settings, protect `main`. Require pull requests, require the `gate` check, require review from code owners (`.github/CODEOWNERS` covers spec.md, the read receipt, the oracle and the harness), and include administrators. Without that, anyone who can run `harness reread` can produce an accepted run; see harness.md, "Limits".

## Run the harness against the inherited system (live model calls)

The inherited system needs an Anthropic key: export `ANTHROPIC_API_KEY`, or put it in `.env` at the repo root or in `inherited/`. The offline gate resolves the model the way the inherited system does (environment first, then the first `.env` found from `inherited/` upward). It reads only the `LLM_MODEL` line from that file, never the key. Every live command also needs `LIVE=1` and a call budget.

```bash
make preflight          LIVE=1 MAX_CALLS=2    # one real notice: extraction plus its impact helper
make evaluate-inherited LIVE=1 MAX_CALLS=45   # preflight (2) + 23 cases (39) = 41 calls
make e2e-live           LIVE=1 MAX_CALLS=10   # inherited CLI on freshly fetched NGPL notices
```

Preflight passes only if every call it needed was made and answered. A blocked or failed helper call reports BUDGET_EXHAUSTED or the failure, never a signal. A wrong key reports AUTHENTICATION_FAILURE and a missing key CREDENTIALS_MISSING. The model ID itself is not validated: a nonexistent model surfaces only as a failed call.

To score a live run with the gate (an oracle change, so the owner does it):

```bash
.venv/bin/python -B -m harness register-capture evidence/legacy/<run>/results.json
git add evidence/legacy/<run> requirements/capture-registry.json requirements/trading-evidence.json context/authority-reference.json
make gate
```

The gate then scores the new capture next to the retained ones, and CURRENT.md lists every labeled notice where the captures disagree. Gate 3 reports EVALUATOR_OR_ORACLE_CHANGED until the owner registers a new reference.

## Change the policy

1. Copy the spec: `cp spec.md context/proposals/proposed-spec.md`, then edit a rule, predicate, set or setting.
2. `make consequences SPEC=context/proposals/proposed-spec.md BASE=spec.md`, then read the printed `REPORT.md`. It shows every changed notice and the per-capture tradeoffs. Keep the losses visible. Exit 4 and a **WOULD BE REFUSED** headline mean the compiler and gate would reject the proposal. An **UNMEASURED** headline means no captured case or supplied example exercises the edit.
3. To adopt, edit `spec.md` and add a `spec-decisions` row with status `proposed`, then run `make compile`.
4. The owner reads the new bytes, sets the row to `approved`, and runs `.venv/bin/python -B -m harness reread --person 'Name'`. The receipt covers every decision row added since the last reread, and refuses if any of them is not yet approved. Agents never do this step.
5. `make gate`.

A change to frozen labels or witnesses (`requirements/*witnesses.json`, `dataset.json`) is an oracle change. Only the owner makes it; Gate 3 reports it as EVALUATOR_OR_ORACLE_CHANGED until a new reference is registered.

## Start a fresh agent session

Open a new agent session in this checkout, with no prior conversation, and paste:

> You are maintaining this repository. Read README.md, spec.md and evidence/CURRENT.md. Run `make setup` if `.venv` is missing, then `make context TASK=recommendation-classification-maintenance` and read the package.md it prints. Change only the files the package lists as source scope, plus spec.md through the "Change the policy" steps. Record any source you read in evidence/code_reads.md. Never edit frozen labels or witnesses, and never write a reread receipt. The change: <describe it>.

The package lists the binding requirements, source scope, pending learning and superseded guidance. The last fresh session is recorded in [evidence/fresh_session.md](evidence/fresh_session.md).
