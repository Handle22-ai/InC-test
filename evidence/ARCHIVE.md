# Archived evidence and earlier history

This repository starts from a single commit made on 2026-09-28. The earlier working history is not published here: 50 commits across several branches, and 15,423 build-history evidence files (earlier runs, receipts, superseded fresh sessions, audit responses, zipped raw transcripts). The current workflow never reads any of it.

It is preserved byte-for-byte in a git bundle kept by the author, available on request:

```bash
git clone incommodities-take-home-history-20260928.bundle history
git -C history show 8ea74f8:evidence/<path>
```

Commit IDs cited in `code_reads.md`, `fresh_session.md`, `docs/positions.md` and spec decision rows (for example `8ea74f8`, `b9cd042`, `d9ed00f`) refer to that history.

What stayed in this repository (462 evidence files):
- every file the tests, `gate`, `consequences` or `context` opened, found by tracing file opens with `context/proposals/trace_evidence_opens.py`;
- every owner approval, ruling and the human code-read account;
- the ledgers `code_reads.md` links to;
- the index pages.
