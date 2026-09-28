# Repository map

## Baseline and scope

User approved initializing the current files as a new baseline on 2026-09-26.
Commit: `765442763efef85b72b1c0abf25c853177684f3a`. Original upstream provenance is unknown.
97 inherited project files (119 regular files including local environment and IDE artifacts).
`inherited_manifest.json` records exact input hashes. Supplied old results are preserved but untrusted.
No inherited source changes. One coding agent, per user instruction. Root resolves to this directory;
no enclosing Git repository, project symlinks, or inherited hardlinks were found. The harness allocates
new run-local SQLite databases; no other workspace's state is used. This is not an OS-level proof
that no unrelated process could write these files. Hashes are checked before and after evaluation.

## Components and boundaries

| Component | Input → output | Dependencies / state |
|---|---|---|
| notice_scraper.py | NGPL EBB pages → HTML files, metadata.json | Selenium, Chrome, driver, live EBB; not exercised |
| notice_parser.py | saved HTML + metadata + prior DB → notice row, locations, restrictions | BeautifulSoup; normal application boundary |
| llm_utils.py | notice text / restrictions / prior → tool extraction or categorical response | Anthropic Messages API; dotenv config |
| notice_validator.py | type, status, text, extracted fields, prior row → signal, confidence, flags | deterministic scoring and LLM impact/materiality calls |
| database.py | rows → SQLite; prior chain → records | notices, notice_locations, notice_restrictions |
| main.py / NoticeProcessor | metadata list → parse calls, DB inserts, signal-positive report | caller-supplied paths; batch execution |
| evaluation/run_eval.py | 14 saved HTML notices → parse/validation JSON, SQLite, summary | binary label map; own execution path |
| harness/adapter.py | NoticeInput + SQLite history → raw observed output + model trace + state snapshots | invokes unchanged normal parser and database functions |

## Model boundary

`llm_utils.get_client()` creates Anthropic clients. `llm_extract_notice` uses forced tool output;
`llm_assess_curtailment_impact` sizes impact; `llm_is_supersede_material` compares revisions.
Additional helper functions classify type/retrospective text; their invocation is observable per request.
Preflight selected `claude-sonnet-4-6`. Observer delegates real requests and returns original responses;
it records request/response payloads and IDs, never authentication headers or credential values.
The parser can fall back to regex and the validator can default on model failure. Such runs do not
qualify as successful model-backed baseline cases.

## State/history

Prior lookup passes an existing row's identity, body, subject, classification, confidence and type
into validation. SQLite supports prior_notice_id and get_notice_chain. Supplied evaluation processes
ascending notice IDs. Prior IDs 46705 and 46857 are absent from the labeled corpus; 46507 is present
for termination 46732. Sorting IDs is an execution convention, not proof of event chronology.
There is no observable external signal-delivery acknowledgement in the chosen boundary.
Do not equate an is_signal classification or JSON report row with a newly delivered alert.
Historical model decisions need run evidence beyond the mutable application database.

## Verified execution

Preflight: `evidence/preflight/20260926T183551.336689Z/`.
Notice 46624: saved HTML read, extraction and impact model calls successful, structured output,
DB insert, history lookup, and close/reopen persistence verified. Prior-history transitions beyond
a single root notice remain baseline evaluation work.

## Documentation mismatches and unknowns

- README says every CLI action runs the full pipeline; fetch branch only scrapes.
- README's report description differs from save_signals_report, which filters signal positives
  and resolves relative output under the notices directory.
- evaluation/run_eval.py and normal parser have different fallback behavior; harness uses the normal
  parser consistently and labels independently, not the historical evaluator's reported accuracy.
- Calibration prose says 8 positives / all seven negatives; the table and LABELS contain 7 each.
- Label 46725 and termination prose need human clarification; it is retained as supplied ground truth.
- Operational lateness, exact materiality, timezone interpretation, alert delivery, and missing-history
  resolution are not fully specified. PDFs and live scraping are not evaluated here.

## Source inspection scope

Agent inspection covered instructions, supplied docs, module definitions/configuration, parser and
orchestrator entry points, evaluation labels/runner, and SQLite interfaces. This was runtime discovery
and boundary mapping, not a broad line-by-line review or repair. No human source inspection requested.
