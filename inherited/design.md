# Trading Signal Extractor — Design

## What This System Does

It monitors Kinder Morgan's NGPL Electronic Bulletin Board (EBB), extracts structured data from natural-language pipeline notices, and classifies each notice as a trading signal or not. A trading signal is a notice describing a meaningful disruption likely to affect gas flow volumes or regional prices — force majeures, capacity constraints, OFOs, and maintenance outages with measurable shipper impact. Purely informational notices, administrative updates, and retrospective reports are not signals.

---

## Pipeline Architecture

```
EBB website
    │
    ▼
notice_scraper.py   — Selenium scrapes NGPL notice listing, downloads HTML + metadata
    │
    ▼
notice_parser.py    — BeautifulSoup extracts structured header fields and body text
    │
    ├── Agent 1: llm_extract_notice()   — Claude extracts locations + restrictions
    │   └── fallback: regex parser      — used if LLM call fails
    │
    ├── Agent 2: validate_notice()      — deterministic scoring → is_signal, confidence
    │   └── LLM call: llm_assess_curtailment_impact()  — VC-3 impact sizing
    │
    ▼
database.py         — SQLite: notices / notice_locations / notice_restrictions
```

The scraper and parser are decoupled — HTML is saved locally so notices can be re-parsed without re-fetching. The two-agent split keeps responsibilities clean: Agent 1 handles extraction fidelity; Agent 2 handles signal classification.

---

## Model Choice

**Claude claude-sonnet-4-6** (`claude-sonnet-4-6`) via the Anthropic API with tool use (structured JSON output). Claude is used for three tasks:

1. **Extraction (Agent 1)**: Parsing semi-structured natural-language notice bodies into a strict schema. Pipeline notices follow no consistent template — the same restriction type can be expressed as a table, a prose paragraph, or a bulleted list. Claude's instruction-following and long-context comprehension handles this variance reliably; a regex-based approach would require constant maintenance as notice formats evolve.

2. **Curtailment impact assessment (VC-3)**: Given extracted restrictions, determining whether the volume impact is large, medium, or small based on service priority and curtailment percentage. This requires reasoning about domain semantics (Primary Firm service has higher market impact than AOR/ITS) that is difficult to encode as rules.

3. **Supersede materiality (VC-1b)**: Comparing a SUPERSEDE notice to its prior to determine whether the update is material enough to generate a new signal, avoiding duplicate alerts.

Tool use (structured output via `tool_choice={"type": "tool"}`) is used for extraction because it eliminates post-processing of free-text JSON and enforces schema compliance at the API level.

---

## Data Structure

Three normalized SQLite tables joined by `notice_id` and `location_index`:

**notices** — one row per notice. Key fields: `notice_type`, `status`, `prior_notice_id` (supersede chain), `information_only` (Agent 1 flag), `is_signal`, `confidence_score`, `validity_flags` (JSON audit trail).

**notice_locations** — one row per distinct constraint point. Fields: `location_index` (join key), `loc_code`, `loc_name`, `segment`, `compressor_station`, `zone`, `system`. The five identifier fields form a specificity hierarchy: LOC/CS (single physical point) → segment → zone → system.

**notice_restrictions** — one row per (service_type, restriction_type, flow_direction) combination at a location. Fields: `location_index` (joins to notice_locations), `service_type` (PRIMARY_FIRM, AOR_ITS, etc.), `restriction_type` (SCHEDULED_TO_PCT_MDQ, UNAVAILABLE, HOURLY_LIMIT_PCT, etc.), `restriction_value`, `restriction_unit`, `flow_direction`, `start_datetime`, `end_datetime`.

Restrictions are nested inside locations in the LLM schema so the location↔restriction relationship is unambiguous at extraction time. The `location_index` is then denormalized into the flat DB rows for SQL queries.

---

## Signal Scoring (Agent 2)

Confidence starts at 0.0 and accumulates through five validity conditions:

| Condition | Logic | Range |
|---|---|---|
| VC-1 Notice Actionability | Hard exits: information_only flag, SUPERSEDE materiality, TERMINATE inheritance | early return |
| VC-2 Notice Type | FM/OFO +0.30, Capacity Constraint +0.20, Maintenance +0.10; non-signal types exit | 0 to +0.30 |
| VC-3 Curtailment Impact | LLM assesses large/medium/small based on service priority and volume reduction | −0.20 to +0.30 |
| VC-4 Location Granularity | LOC/CS +0.10, segment +0.15, zone +0.20, system +0.30, none −0.10 | −0.10 to +0.30 |
| VC-5 Geographic Relevance | Louisiana Zone / Gulf Coast / Henry Hub +0.20; else no adjustment | 0 to +0.20 |

`is_signal = confidence >= 0.5`. Non-signals are zeroed out. Maximum achievable score is 1.10, clamped to 1.0. Every condition appends a human-readable flag to the audit trail so traders can inspect the reasoning.

---

## Bridging ML Rigor to This Domain

Standard supervised classification in this domain faces a core data problem: labeled examples of true trading signals are expensive to produce, require domain expertise to annotate, and are sparse relative to the volume of routine notices. Rather than fitting a model to a small labeled set and accepting unknown generalization error, the approach is designed to be **auditable by construction**.

The confidence score is not a model output — it is a deterministic sum of interpretable indicators, each grounded in a domain rule that a gas trader would recognize: the notice type encodes prior probability of operational impact; curtailment confirmation and severity encode information content; location granularity encodes actionability; geography encodes price relevance. This mirrors the feature-engineering discipline of classical ML but makes the scoring function transparent rather than learned.

The LLM is used where rule-based approaches are brittle — parsing format-variable text and reasoning about service priority — but its outputs are constrained to categorical verdicts (large/medium/small, yes/no) rather than raw scores. This limits the surface area where model error can propagate undetected.

The threshold (`confidence >= 0.5`) and the adjustment weights are calibrated on a labeled evaluation set of 14 notices spanning all notice types, status codes, and geographic regions present in the NGPL feed. On that set the system achieves 85.7% classification accuracy (see `calibration.md`).
