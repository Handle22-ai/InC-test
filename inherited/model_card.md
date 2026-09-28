# Model Card — NGPL Trading Signal Extractor
**Version:** Phase 1 Outline (pre-calibration)  
**Phase 3 update:** Replace all `[TBD]` fields with measured numbers from the full evaluation set.

---

## What This System Does

Classifies Kinder Morgan NGPL Electronic Bulletin Board notices as trading signals or non-signals, and assigns a confidence score (0.0–1.0) to each signal. A trading signal is a notice describing a meaningful disruption to gas flow volumes or regional prices — force majeures, capacity constraints, OFOs, and maintenance outages with measurable shipper impact.

For each signal, the system extracts:
- **Where:** constraint point (LOC code, compressor station, segment, zone, or system)
- **Who:** affected service types (Primary Firm, Secondary Firm, AOR/ITS, Interruptible)
- **How much:** restriction type and value (% MDQ, UNAVAILABLE, hourly limit)
- **When:** effective and end datetimes
- **Why it scored as it did:** a human-readable audit trail of validity conditions fired

---

## System Architecture and Data Flow

```
┌─────────────────────────────────────────────────────────────────┐
│  Scraper (notice_scraper.py)                                    │
│  Input:  Kinder Morgan EBB URL, notice type filter              │
│  Output: HTML files + metadata.json (notice_id, type, URL)      │
│  Decision: which notices to download (type filter, max count)   │
└────────────────────────────┬────────────────────────────────────┘
                             │ HTML files + metadata
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│  HTML Parser (notice_parser.py — _extract_header, _extract_body)│
│  Input:  Raw HTML file                                          │
│  Output: header dict (notice_id, type1, type2, status,          │
│          prior_notice_id, effective/end dates, subject)         │
│          body string (plain text of notice body)                │
│  Decision: none — deterministic field extraction via regex      │
│            and BeautifulSoup label matching                     │
└────────────────────────────┬────────────────────────────────────┘
                             │ header + body
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│  Agent 1 — LLM Extraction (llm_utils.llm_extract_notice)        │
│  Input:  header dict, body string, notice_id, effective/end dt  │
│  Output: locations list, restrictions list, information_only    │
│  Key decisions:                                                 │
│    · information_only: is this notice purely informational?     │
│    · change_indicator: which symbol marks changed rows?         │
│    · Which locations are constraint points (not causes)?        │
│    · Which service types are restricted at each location?       │
│    · What is the restriction type, value, unit, direction?      │
│  Fallback: regex parser if LLM call fails                       │
└────────────────────────────┬────────────────────────────────────┘
                             │ locations, restrictions, information_only
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│  Agent 2 — Validator (notice_validator.validate_notice)         │
│  Input:  notice_type, status, header, body, locations,          │
│          restrictions, prior_notice_row, information_only       │
│  Output: is_signal (bool), confidence (0.0–1.0), flags (list)   │
│  Key decisions (in order):                                      │
│    · VC-1a: suppress if information_only=True                   │
│    · VC-1b: suppress SUPERSEDE if not materially different      │
│             (LLM call: llm_is_supersede_material)               │
│    · VC-1c: inherit prior signal for TERMINATE                  │
│    · VC-2:  hard exit for non-signal types;                     │
│             +0.30/+0.20/+0.10 boost by type tier               │
│    · VC-3:  score curtailment impact via LLM                    │
│             (llm_assess_curtailment_impact → large/medium/small)│
│    · VC-4:  score location granularity (breadth of impact)      │
│    · VC-5:  +0.20 if Louisiana/Gulf Coast/Henry Hub geography   │
│    · Final: is_signal = confidence >= 0.5                       │
└────────────────────────────┬────────────────────────────────────┘
                             │ notice_row, locations, restrictions
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│  Database (database.py — SQLite)                                │
│  Input:  notice_row, locations list, restrictions list          │
│  Output: persisted rows in notices / notice_locations /         │
│          notice_restrictions tables                             │
│  Decision: upsert on notice_id (re-parsing is idempotent)       │
│  Role: provides prior_notice_row to Agent 2 for TERMINATE and   │
│        SUPERSEDE lookups in subsequent runs                     │
└─────────────────────────────────────────────────────────────────┘
```

### Data passed between sections

| Hand-off | What is passed | Why |
|---|---|---|
| Scraper → Parser | HTML file path + metadata dict | Decoupled so notices can be re-parsed without re-fetching |
| Parser → Agent 1 | header dict + body string | Structured header reduces LLM context; body carries the operational content |
| Agent 1 → Agent 2 | locations list, restrictions list, information_only bool | Agent 1 converts free text to a schema; Agent 2 scores the schema without re-reading the body (except for VC-3 LLM call) |
| DB → Agent 2 | prior_notice_row (notice_id, is_signal, confidence_score, body_text) | Required for TERMINATE inheritance and SUPERSEDE materiality diff |
| Agent 2 → DB | is_signal, confidence_score, validity_flags | Stored alongside extraction output so the full notice record is self-contained |

### Where LLM calls happen

| Call | Section | Trigger | Output |
|---|---|---|---|
| `llm_extract_notice` | Agent 1 | Every notice | locations, restrictions, information_only |
| `llm_assess_curtailment_impact` | Agent 2 VC-3 | Measurable restrictions present | large / medium / small |
| `llm_is_supersede_material` | Agent 2 VC-1b | SUPERSEDE + prior in DB | yes / no |

---

## Validity Range

The system is designed and evaluated for:

- **Pipeline:** NGPL (Natural Gas Pipeline Company of America)
- **Notice types in scope:** FORCE MAJEURE, CAPACITY CONSTRAINT, OPERATIONAL FLOW ORDER, OPERATIONAL ALERT, MAINTENANCE, STORAGE, OTHER
- **Notice types explicitly excluded:** PIPELINE CONDITIONS, REGULATORY, TARIFF, INFORMATIONAL
- **Geographies with highest confidence:** Louisiana Zone, Gulf Coast Zone/System/Mainline, Henry Hub-connected points (VC-5 boost applies)
- **Geographies with standard confidence:** Amarillo System, Permian Zone, Texok Zone, Midcontinent, Iowa-Illinois (no VC-5 boost, but signals are still classified)
- **Status types handled:** INITIATE, SUPERSEDE (with prior in DB), TERMINATE (with prior in DB)
- **Confidence threshold for signal classification:** ≥ 0.5

**Classification accuracy (evaluation set):** 85.7% (12/14)  
**Evaluation set size:** 14 notices

---

## What a Downstream User Needs to Know

**Confidence score meaning:**  
Confidence ≥ 0.5 is the signal threshold. Scores between 0.5 and 0.7 indicate the notice meets the signal criteria but has lower actionability — typically a single-point curtailment in a non-HH geography with moderate volume impact. Scores above 0.7 indicate high-confidence: measurable firm service curtailment, known constraint point, and price-relevant geography. A score of 0.0 means non-signal — confidence is not reported for non-signals because it carries no interpretive meaning.

**Audit trail:**  
Every output includes `validity_flags`, a list of human-readable strings explaining which conditions fired and what score each contributed. Review these flags before acting on borderline signals (confidence 0.5–0.6). The flags identify whether the signal was driven by curtailment volume, notice type, geography, or a combination.

**Prior notice dependency:**  
TERMINATE and SUPERSEDE classifications depend on the prior notice being in the database. If the prior is absent, the system falls back to scoring the current notice on its own merits. The validity flag explicitly states when this fallback occurs.

**Not a real-time system:**  
Signal generation latency equals scraping latency. The system does not push alerts — downstream consumers must poll the database or signal output file.

**Single operator coverage:**  
All signals relate to NGPL capacity. Confidence scores are not comparable to signals from other pipeline systems.
