# Proposal: archive build-history evidence

Status: **PROPOSED — owner action.** An agent was blocked, correctly, from removing these
files itself.

## Finding

15,763 files are tracked under `evidence/` (about 596 MB). While the full test suite,
`gate --proposal`, `consequences` and `context` run, only **424** of them are ever opened.
The rest are earlier runs, receipts, zipped transcripts and superseded fresh sessions.
Another 108 files in `submission/` (receipts, inventories, earlier handoffs) are read by
nothing except `setup.sh` and `verify_positive_path.py`.

## How the keep-set was measured

Run the four workflows with the audit hook in `context/proposals/trace_evidence_opens.py`
installed as `sitecustomize`:

```bash
mkdir -p /tmp/trace && cp context/proposals/trace_evidence_opens.py /tmp/trace/sitecustomize.py
export PYTHONPATH=/tmp/trace EVIDENCE_OPEN_LOG=/tmp/trace/open.log
.venv/bin/python -B -m harness.offline test
.venv/bin/python -B -m harness gate --proposal
.venv/bin/python -B -m harness consequences
HARNESS_TASK=recommendation-classification-maintenance .venv/bin/python -B -m harness.commands context
```

Keep:
- every tracked file named in `open.log`;
- every owner approval, ruling or `human-code-read-account.txt`;
- `evidence/{CURRENT,coverage,code_reads,fresh_session}.md` and `evidence/current-baseline.json`;
- `submission/setup.sh` and `submission/verify_positive_path.py`.

## If you agree

Remove the rest in one commit, and add `evidence/ARCHIVE.md` saying everything stays
retrievable at the commit before removal (`git show <commit>:evidence/<path>`). Then run
`make check` and `gate --proposal` again. The trace predicts both are unchanged.
