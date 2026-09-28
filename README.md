# The Harness

The engineer owns [spec.md](spec.md) and reads [evidence/CURRENT.md](evidence/CURRENT.md). Coding agents maintain the implementation. The rebuilt component is `NormalizedNotice + EventHistory → SignalDecision` in `rebuilt/`. Its output is a candidate, never a trading recommendation. (The replay tests drive a downstream publisher seam with synthetic authorization, and that seam reports `INITIAL_RECOMMENDATION` so duplicate suppression can be checked. No real recommendation path exists.)

This repository's history starts at root commit `41fd172`; the earlier working history is described in [evidence/ARCHIVE.md](evidence/ARCHIVE.md). [harness.md](harness.md) explains the three gates, what each costs and what it would miss. The code-read map is [evidence/code_reads.md](evidence/code_reads.md).

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

`--proposal` runs the component on the unreviewed spec by setting `NGPL_MEASURE_UNREVIEWED_SPEC` to the spec's SHA-256 for that run only. The component refuses an unreviewed spec unless that variable matches, so anyone who sets it by hand can run the component (`rebuilt/normalized_classifier.py`) on unreviewed bytes. It is a measurement switch, not approval: the gate's own acceptance still needs the reread, and `make gate` still exits 5.

Each run writes `evidence/normalized/<time>/CURRENT.md`. It leads with the desk view: labeled positives missed and labeled negatives signaled, per capture. It also lists what the gate does not claim.

| Python gate exit | Meaning |
|---|---|
| 0 | All three gates pass on a reviewed spec |
| 3 | Something in scope is UNKNOWN, or the run is proposal-only |
| 4 | An established failure |
| 5 | Refused before running: stale review, drifted generated files, or a boundary violation |

CI (`.github/workflows/gate.yml`) runs `make check` and the gate, and passes only on exit 0. Make reports any failure as exit 2.

**What makes the owner's review real:** in GitHub settings, protect `main`. Require pull requests, require the `gate` check, require review from code owners (`.github/CODEOWNERS` covers spec.md, the read receipt, the frozen labels and witnesses, the capture registry and trading evidence, the reference pointer and reference runs, the harness and the tests; branch protection itself is not verified by this repository), and include administrators. Without that, anyone who can run `harness reread` can produce an accepted run; see harness.md, "Limits".

## Run the harness against the inherited system (live model calls)

The inherited system needs an Anthropic key: export `ANTHROPIC_API_KEY`, or put it in `.env` at the repo root or in `inherited/`. The offline gate resolves the model the way the inherited system does (environment first, then the first `.env` found from `inherited/` upward). It reads only the `LLM_MODEL` line from that file, never the key. Every live command also needs `LIVE=1` and a call budget.

```bash
make preflight          LIVE=1 MAX_CALLS=2    # one real notice: extraction plus its impact helper
make evaluate-inherited LIVE=1 MAX_CALLS=45   # preflight plus 23 cases, about 40 calls (the one full run made 38)
make e2e-live           LIVE=1 MAX_CALLS=10   # inherited CLI on freshly fetched NGPL notices
```

Preflight passes only if every call it needed was made and answered. A blocked or failed helper call reports BUDGET_EXHAUSTED or the failure, never a signal. A wrong key reports AUTHENTICATION_FAILURE and a missing key CREDENTIALS_MISSING. An account without credit reports BILLING and an unknown model MODEL_NOT_FOUND; both stop further calls. Any other provider error is PROVIDER_FAILURE. Each failed call keeps its status code and the provider's own error message, with anything shaped like a key redacted; other exception text is never kept.

To score a live run with the gate (an oracle change, so the owner does it):

```bash
.venv/bin/python -B -m harness register-capture evidence/legacy/<run>/results.json
git add evidence/legacy/<run> requirements/capture-registry.json requirements/trading-evidence.json context/authority-reference.json
make gate
```

The gate then scores the new capture next to the retained ones, and CURRENT.md lists every labeled notice where the captures disagree. Gate 3 reports EVALUATOR_OR_ORACLE_CHANGED until the owner registers a new reference.

## Change the policy

1. Copy the spec: `cp spec.md context/proposals/proposed-spec.md`, then edit a rule, predicate, set or setting.
2. `make consequences SPEC=context/proposals/proposed-spec.md`, then read the printed `REPORT.md`. The baseline defaults to the spec you last reread (pass `BASE=` to override). The report shows every changed notice and the per-capture tradeoffs; keep the losses visible. Exit 4 with a **WOULD BE REFUSED** headline means a compile boundary, the input contract or a frozen classifier witness rejects the proposal; publisher-replay witnesses run only in the gate. **UNMEASURED** means no captured case changes. Examples you supply with `--inputs` are illustrations, not evidence.
3. To adopt, edit `spec.md` and add a `spec-decisions` row with status `proposed`, then run `make compile`.
4. The owner reads the new bytes, sets the row to `approved`, and runs `.venv/bin/python -B -m harness reread --person 'Thomas Hand'`. Only names in `spec-settings.owners` are accepted. The receipt covers every decision row added since the last reread, and refuses if any is not approved. Agents never do this step, and never register a reference unasked (one did, once: `35b5af7`, see evidence/ARCHIVE.md).
5. `make gate`.

Budgets only tighten silently. Raising any `max_` value in `spec-settings.acceptance`, or adding to `review_satisfies`, is refused (`ACCEPTANCE_LOOSENED`) by `make compile`, the gate's preflight and `harness reread`, each comparing against the spec at the last reread, unless a decision row whose Previous spec SHA256 is that spec says `LOOSENS_ACCEPTANCE`. Rereading first does not get around it: the reread runs the same check before it replaces the receipt.

A change to frozen labels or witnesses (`requirements/*witnesses.json`, `dataset.json`) is an oracle change, and a change under `harness/` or `tests/` is an evaluator change. Gate 3 reports either as EVALUATOR_OR_ORACLE_CHANGED, naming the files, until an owner reviews them and registers a new reference from a clean run:

```bash
.venv/bin/python -B -m harness gate --output evidence/reviewed-run
.venv/bin/python -B -m harness register-reference evidence/reviewed-run evidence/reference-<date> --person 'Thomas Hand'
```

The reference records who registered it, which evaluator and oracle files they accepted, and any spec table edit it was registered over that changed no measured decision (UNMEASURED_POLICY_EDIT). CURRENT.md shows all three, and keeps listing the spec table edits the last reread covered, so registering a reference does not erase the record of an unmeasured edit. Like the reread, this is an assertion, not authentication.

## Start a fresh agent session

Open a new agent session in this checkout, with no prior conversation, and paste:

> You are maintaining this repository. Read README.md, spec.md and evidence/CURRENT.md. Run `make setup` if `.venv` is missing, then `make context TASK=recommendation-classification-maintenance` and read the package.md it prints. Change only the files the package lists as source scope, plus spec.md through the "Change the policy" steps. Record any source you read in evidence/code_reads.md. Never edit frozen labels or witnesses, and never write a reread receipt. The change: <describe it>.

The package lists the binding requirements, source scope, pending learning and superseded guidance. The last fresh session is recorded in [evidence/fresh_session.md](evidence/fresh_session.md).
