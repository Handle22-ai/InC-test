# Runtime requirements

Discovered from supplied docs and execution boundaries; inherited files remain unchanged.

- Runtime: Python >=3.14 in both supplied pyproject files; local `.venv/bin/python` is 3.14.7.
- Install: `.venv/bin/python -m ensurepip`, then `.venv/bin/python -m pip install -r inherited/requirements.txt -r requirements-harness.txt`.
- Inherited dependencies: Selenium 4.15.2, webdriver-manager 4.0.1, BeautifulSoup 4.12.2,
  requests 2.31.0, python-dotenv 1.0.0, anthropic >=0.40.0. SQLite is in Python's standard library.
  The pyproject files list no dependencies; use the supplied requirements.txt.
- Environment: `ANTHROPIC_API_KEY` required for real extraction; `LLM_MODEL` defaults to
  `claude-sonnet-4-6`; `LLM_ENABLED` defaults true (false/0/no disable). `llm_utils.py`
  calls python-dotenv. Harness explicitly loads root `.env` before importing the application.
  Only credential presence is recorded. Secret values must never enter evidence.
- Provider: Anthropic Messages API. Forced tool use for extraction, text responses for
  curtailment sizing and supersede comparison. Actual selected model and provider response
  identity are recorded at runtime. No claim of availability until a successful request.
- Datasets: 14 HTML files in `inherited/evaluation/notices/`; binary labels in
  `inherited/evaluation/run_eval.py`, rationales in `inherited/calibration.md`.
  `inherited/samples/notices/` contains 25 unlabeled HTML files and PDF attachments.
  Supplied `inherited/evaluation/results/` is unvalidated historical material, not new evidence.
- Persistence: SQLite notices, notice_locations, notice_restrictions; prior_notice_id links.
  No database server required. All new runs use isolated databases outside inherited/.
- External services: Anthropic required for baseline. Live scraping additionally needs
  Chrome/Chromium, Selenium driver downloads, and NGPL EBB network access. Live scraping
  and PDF ingestion are outside this saved-notice baseline.
- Main CLI: `python inherited/main.py parse --output-dir <metadata-directory> --db notices.db
  --signal-output signals.json`. Metadata entries must point at existing HTML files.
- One notice: use `notice_parser.parse_notice_html(html, metadata, db_conn)` followed by
  `database.insert_notice`; these are the same functions used by NoticeProcessor.
  Reproducible instrumented command: `.venv/bin/python -m harness.preflight`.
- Supplied labeled command: `python inherited/evaluation/run_eval.py`; it writes/deletes
  files inside inherited/evaluation/results, so do not run it in place for this exercise.
  Baseline harness will use the normal parser boundary and copied label data with isolated state.
- Caveat: supplied evaluator uses empty extraction on model failure; normal parser uses regex
  fallback. Harness distinguishes model/environment failures from behavioral verdicts and
  refuses to count either fallback as successful preflight.

Initial environment: virtual environment exists but pip and application packages were absent.
Installed pip using ensurepip. Dependency versions will be frozen after successful installation.
