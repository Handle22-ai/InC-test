# Trading Signal Extractor

Classifies Kinder Morgan NGPL Electronic Bulletin Board (EBB) notices as trading signals or non-signals. A trading signal is a notice describing a meaningful disruption to gas flow volumes or regional prices — force majeures, capacity constraints, OFOs, and maintenance outages with measurable shipper impact.

For each signal the system extracts: constraint point, affected service types, restriction type and value, effective and end datetimes, and a human-readable audit trail of the scoring logic.

On the labeled evaluation set the system achieves **85.7% classification accuracy** with zero false positives.

See `model_card.md` for full system documentation, `design.md` for architecture decisions, and `validity.md` for the scoring rules.

---

## Architecture

```
notice_scraper.py   — Selenium: downloads HTML notices + metadata from NGPL EBB
notice_parser.py    — BeautifulSoup: extracts header fields and body text
llm_utils.py        — Agent 1: LLM extracts locations, restrictions, information_only
notice_validator.py — Agent 2: deterministic scoring → is_signal, confidence, flags
database.py         — SQLite: persists notices, locations, restrictions
main.py             — CLI orchestrator
```

**Two-agent design:** Agent 1 (LLM) converts free-text notice bodies into a structured schema. Agent 2 scores that schema using five deterministic validity conditions (VC-1 through VC-5), with one LLM call for curtailment impact sizing (VC-3).

---

## Installation

```bash
pip install -r requirements.txt
```

Requires Chrome/Chromium for Selenium. Set your Anthropic API key:

```bash
export ANTHROPIC_API_KEY=sk-ant-...
```

---

## Usage

### Fetch notices from the EBB
```bash
python main.py fetch --max-notices 10 --output-dir notices
```

### Parse downloaded notices, write to DB, and save signal report
```bash
python main.py parse --output-dir notices --db notices.db --signal-output trading_signals.json
```

### Full pipeline (fetch + Agent 1 extraction + Agent 2 validation)
```bash
python main.py fetch-and-parse --max-notices 10 --output-dir notices --db notices.db --signal-output trading_signals.json
```

All three actions run the full pipeline including LLM extraction (Agent 1) and signal validation (Agent 2).

**Output locations:**
- SQLite database: `<output-dir>/<db>` (default: `notices/notices.db`)
- Signal JSON report: `<signal-output>` path, relative to the working directory (default: `trading_signals.json`)

### Run evaluation on labeled notice set
```bash
python evaluation/run_eval.py
```

---

## Output

### SQLite database (`notices.db`)

Three tables joined by `notice_id` and `location_index`:

| Table | Key fields |
|---|---|
| `notices` | `notice_id`, `notice_type`, `status`, `is_signal`, `confidence_score`, `validity_flags` |
| `notice_locations` | `location_index`, `loc_code`, `compressor_station`, `segment`, `zone`, `system` |
| `notice_restrictions` | `location_index`, `service_type`, `restriction_type`, `restriction_value`, `start_datetime`, `end_datetime` |

### Signal JSON (`trading_signals.json`)

One entry per notice processed. Key fields:

```json
{
  "notice_id": 46624,
  "notice_type": "CAPACITY CONSTRAINT",
  "status": "INITIATE",
  "is_signal": true,
  "confidence_score": 0.7,
  "validity_flags": [
    "VC-2: CAPACITY CONSTRAINT → +0.20",
    "VC-3: large curtailment impact (AOR + Secondary UNAVAILABLE) → +0.30",
    "VC-4: specific LOC code(s) or compressor station → +0.10",
    "VC-5: Henry Hub / Gulf Coast / Louisiana geography → +0.20"
  ],
  "locations": [...],
  "restrictions": [...]
}
```

---

## Signal Scoring

Confidence starts at 0.0 and accumulates through five conditions. `is_signal = confidence >= 0.5`.

| Condition | What it checks | Range |
|---|---|---|
| VC-1a | `information_only` flag from Agent 1 — suppress retrospective/advisory notices | hard exit |
| VC-1b | SUPERSEDE materiality — suppress if not materially different from prior | hard exit |
| VC-1c | TERMINATE inheritance — inherit prior confidence if prior was a signal | hard exit |
| VC-2 | Notice type: FM/OFO +0.30, Capacity Constraint +0.20, Maintenance +0.10 | 0 to +0.30 |
| VC-3 | Curtailment impact (LLM): large +0.30, medium +0.20, small +0.10, none −0.20 | −0.20 to +0.30 |
| VC-4 | Location breadth: system +0.30, zone +0.20, segment +0.15, LOC/CS +0.10, none −0.10 | −0.10 to +0.30 |
| VC-5 | Geography: Louisiana Zone / Gulf Coast / Henry Hub +0.20, else no adjustment | 0 to +0.20 |

Maximum achievable score: 1.10 (clamped to 1.0).

---

## Evaluation

Labeled evaluation set: `evaluation/notices/` (14 notices spanning all notice types, statuses, and geographies).

Unlabeled sample notices: `samples/notices/` (25 raw scraper downloads with impact-report PDFs, see `samples/README.md`). These are not scored by `run_eval.py`.

Phase 1 results (14 notices):

| Metric | Value |
|---|---|
| Precision | 1.00 |
| Recall | 0.71 |
| F1 | 0.83 |
| False positives | 0 |
| False negatives | 2 |

See `evaluation/Calibration.md` for per-notice breakdown and failure analysis.

---

## Testing

All test scripts live in `tests/`. Generated output (JSON files) goes to `tests/output/` (git-ignored).

```bash
# Integration: download 1 live notice into tests/output/notices/
python tests/test_scraper.py scraper 1

# Parser: process notices downloaded by scraper test
python tests/test_scraper.py parser

# Full scraper + parser
python tests/test_scraper.py all 3

# HTML header/body extraction on saved notices
python tests/test_extraction.py

# LLM extraction on a single notice (verbose, shows full LLM I/O)
python tests/test_llm_parser.py

# Validator: runs validate_notice() on all llm_parse_*.json in tests/output/
python tests/test_validator.py

# Batch evaluation against labeled ground truth (14 notices)
python evaluation/run_eval.py
```

---

## Configuration

**Scraper selectors** — if the EBB website structure changes, update XPath constants in `NoticeScraperConfig` in `notice_scraper.py` and validate with:

```bash
python test_scraper.py validate path/to/notice.html
```

**Notice types in scope:** FORCE MAJEURE, CAPACITY CONSTRAINT, OPERATIONAL FLOW ORDER, OPERATIONAL ALERT, MAINTENANCE, STORAGE, OTHER

**Notice types excluded:** PIPELINE CONDITIONS, REGULATORY, TARIFF, INFORMATIONAL

---

## Scope

- Covers NGPL (Kinder Morgan) notices
- Batch mode: notices are fetched and processed on demand
- Does not predict price impact
