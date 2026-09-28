# Earlier history and archived evidence

This repository's history starts at root commit `41fd172`, made on 2026-09-28; later commits build on it (`git rev-list --count HEAD`). The earlier working history (50 commits across several branches) and 15,423 build-history evidence files (earlier runs, receipts, superseded fresh sessions, audit responses, raw transcripts) are not part of this repository and are not offered for review. The current workflow never read them.

Commit IDs cited in `code_reads.md`, `fresh_session.md`, `docs/positions.md` and spec decision rows (for example `8ea74f8`, `b9cd042`, `d9ed00f`) refer to that earlier history and cannot be checked from this repository.

What this repository keeps (466 evidence files in the root commit; `git ls-files evidence | wc -l` for today's count):
- every file the tests, `gate`, `consequences` or `context` open, found by tracing file opens with `context/proposals/trace_evidence_opens.py`;
- every owner approval, ruling and the human code-read account;
- the ledgers `code_reads.md` links to;
- the index pages and the registered captures, including the live run of 2026-09-28.

## Who made the commits

Every commit in this repository was made by a coding agent (Claude Code), with the author and committer set to the owner, Thomas Hand. The owner asked for the agent co-author trailer to be removed, so the author field does not show who did the work. It shows who is accountable for it. What the owner did personally:
- ran every spec reread (`harness reread --person`) from the owner's own shell (the `!` prefix or a terminal); the agent then committed the receipt;
- gave each decision approval in words; the agent then set the row's status to `approved`;
- asked for each reference registration, except the first.

The first reference registration, commit `35b5af7` ("Register the reviewed run of 41fd172 as the Gate 3 reference"), was run by the agent without being asked. The history had just been rewritten, and the owner's request at that moment was only to remove the agent as a contributor. The later registrations (`1dc5837`, `ee6fe7b`, `0ced592`) were each made after the owner asked for them. A registration is an owner action (README), so `35b5af7` should be read as the agent's, not the owner's.
