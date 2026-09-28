# Sample notices

Raw scraper output for 25 NGPL notices (IDs 47121–47215) downloaded on 2026-09-11,
plus 7 Outage Impact Report PDFs, `metadata.json`, and `notice_list.json`.

These are **unlabeled** and are **not** the evaluation set. They are not scored by
`evaluation/run_eval.py` and have no entry in its `LABELS` table. They are included
so the parsing and extraction path can be exercised on real notice HTML without
re-running the scraper against the live bulletin board.

The labeled evaluation set is described in `calibration.md`.

The `html_file` / `impact_report_file` paths inside `metadata.json` are relative to the
repository root.
