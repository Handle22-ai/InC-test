# Validity Conditions

Each condition is evaluated in order. VC-1 sub-paths can exit early with a hard verdict. VC-2 through VC-5 are confidence adjustments that stack on a base of 0.0; `is_signal = confidence >= 0.5`.

---

## VC-1 — Notice Actionability

Three sub-paths evaluated in order. Any one of them can return immediately.

---

### VC-1a — Information-Only Flag

**Trigger:** Agent 1 sets `information_only=True` during extraction. The flag is set for: retrospective post-event reports (past-tense language, event already ended), weather/demand advisories with no enforceable directive, administrative updates (tariff filings, project lists, regulatory filings), and rolling maintenance plan summaries.

**Action:** Return `(False, 0.0)` immediately. No further conditions evaluated.

**Rationale:** The failure mode this prevents is classifying routine EBB filler as a trading signal. Pipelines post a high volume of administrative and informational content alongside operational notices — these must be suppressed before any scoring begins. The alternative was a separate LLM call in the validator to detect retrospective or advisory content (the previous VC-1c and VC-2a). Consolidating into a single boolean inferred at extraction time eliminates a redundant API call and generalizes: one flag covers retrospective reports, weather advisories, tariff filings, and plan summaries rather than handling each case separately.

---

### VC-1b — SUPERSEDE Materiality

**Trigger:** `status == "SUPERSEDE"` and the prior notice is found in the database.

**Action:** Call `llm_is_supersede_material(current, prior)`. If the LLM returns `False` (not materially different): return `(False, 0.0)` — suppressed as a duplicate. If `True`: continue validation as a potential new signal. If the LLM is unavailable or the prior notice is not in the DB: continue validation conservatively (do not suppress).

**Rationale:** A SUPERSEDE notice replaces a prior notice. If only the effective date or a formatting detail changed, re-alerting a trader on the same restriction is noise. The failure mode prevented is duplicate signal generation from routine administrative updates to active restrictions. The alternative — always treating SUPERSEDE as a new signal — would flood downstream consumers whenever a pipeline extends an existing curtailment's end date. The alternative of always suppressing SUPERSEDE would miss genuinely material updates (e.g., scope expanding to cover additional LOCs). An LLM diff is the only practical approach given the free-text nature of notice bodies.

---

### VC-1c — TERMINATE Inheritance

**Trigger:** `status == "TERMINATE"` and the prior notice is found in the database.

**Action:** Look up the prior notice's `is_signal` and `confidence_score`. If the prior was a signal: return `(True, prior_confidence)` — the lift of a real restriction is itself a tradeable event, inheriting the prior confidence. If the prior was not a signal: return `(False, 0.0)` — no trading relevance. If the prior is not in the DB: continue through VC-2 to VC-5 (cannot assess without history).

**Rationale:** A restriction being lifted is exactly as tradeable as the restriction being imposed — a trader who acted on the original signal needs to know it ended. Inheriting the prior confidence rather than rescoring avoids the problem that a TERMINATE notice has no restriction rows of its own (so VC-3 would always penalize it). The failure mode prevented is either missing the lift signal entirely or misevaluating it based on empty extraction output. The alternative of always scoring TERMINATE notices from scratch would produce `confidence = 0.0` in almost every case due to the absence of restrictions, which is wrong for signals that are genuinely being lifted.

---

## VC-2 — Notice Type Gate

**Trigger:** Every notice that reaches VC-2 (i.e., passed VC-1 without an early exit).

**Action:** Two-phase check. First, hard exit: if `notice_type` is in `{PIPELINE CONDITIONS, REGULATORY, TARIFF, INFORMATIONAL}`, return `(False, 0.0)` immediately — these are by definition non-operational. Second, tiered confidence boost for signal-capable types:

| Type | Boost |
|---|---|
| `FORCE MAJEURE`, `OPERATIONAL FLOW ORDER` | +0.30 |
| `CAPACITY CONSTRAINT` | +0.20 |
| `MAINTENANCE` | +0.10 |
| `OPERATIONAL ALERT`, `STORAGE`, `OTHER`, unknown | +0.00 |

Unknown types (not in either set) are treated as signal-capable with no boost and a flag recorded; downstream conditions determine signal status.

**Rationale:** Notice type is a strong prior for operational impact. Force Majeure and OFOs are categorically enforceable events — an FM is a physical failure, an OFO is a mandatory directive. These carry the highest prior probability of being a signal before content is examined. Capacity Constraints are point-level restrictions but cover a wider severity range. Maintenance is common and often routine. The non-signal types (regulatory, tariff, pipeline conditions, informational) are administrative by definition and have essentially zero false negative cost. The alternative — treating all types uniformly and relying entirely on content — would require VC-3 to carry the full load of type discrimination, which it cannot do when restriction extraction is ambiguous.

---

## VC-3 — Curtailment Impact

**Trigger:** Every notice that reaches VC-3.

**Action:** First, check whether any measurable restriction exists: any restriction row with a non-null `restriction_value`, or any `restriction_type == "UNAVAILABLE"`. If no measurable restriction: `−0.20`. If measurable restrictions exist: call `llm_assess_curtailment_impact(body, restrictions)` to determine impact size — `large` (+0.30), `medium` (+0.20), or `small` (+0.10). If the LLM is unavailable, default to `small`.

Impact sizing criteria:
- **Large**: Primary Firm or Secondary Firm affected AND >10% volume reduction, or any `UNAVAILABLE` restriction
- **Medium**: Firm service affected with <10% reduction, or interruptible-only with large reduction
- **Small**: Only interruptible/AOR service with minor reduction

**Rationale:** Measurable curtailment is the core criterion for a trading signal. A notice without quantified restrictions or UNAVAILABLE service types is advisory — it describes conditions but does not impose them. The three-tier sizing reflects that a 45% Primary Firm curtailment has a fundamentally different market impact than a 5% interruptible-only restriction. Treating all curtailments equally would over-weight minor operational adjustments. The alternative of using only the structured `restriction_value` field without LLM assessment would miss the service priority dimension: a 6% reduction of Primary Firm is more significant than a 100% reduction of interruptible service, and that requires domain reasoning the LLM handles well.

---

## VC-4 — Location Granularity

**Trigger:** Every notice that reaches VC-4.

**Action:** Inspect the extracted location rows for the most specific identifier present across all locations:

| Most specific field found | Adjustment |
|---|---|
| `loc_code` or `compressor_station` | +0.10 |
| `segment` | +0.15 |
| `zone` | +0.20 |
| `system` | +0.30 |
| Locations present but all identifier fields null | −0.10 |
| No location rows at all | −0.10 |

The highest-priority (most specific) level found across all location rows is used.

**Rationale:** Location granularity is a proxy for the breadth of market impact. A curtailment at a single LOC code affects one meter point — one shipper, one delivery location. A curtailment described at segment level affects all deliveries along that section of pipe. A zone-level or system-level event affects every shipper and interconnect across the entire zone or system, with corresponding price impact across a much wider set of positions. The scoring reflects this directly: broader geographic scope = larger market impact = higher confidence that the notice is a tradeable signal. The failure mode prevented is under-weighting system-wide events that a trader with exposure across the zone needs to act on immediately, while appropriately discounting single-point curtailments that may affect only one counterparty.

---

## VC-5 — Geographic Relevance

**Trigger:** Location rows are present.

**Action:** Check `zone`, `loc_name`, and `system` fields across all location rows against the pattern: `louisiana zone | gulf coast (zone|system|mainline) | henry hub`. If any location matches: `+0.20`. If locations exist but none match: no adjustment. If no locations: no adjustment (VC-4 already handles the empty case).

**Rationale:** The signal definition explicitly prioritizes Louisiana pipelines connected to Henry Hub or LNG export terminals. A curtailment at a Gulf Coast Mainline location has immediate NYMEX front-month price relevance; the same event in Permian or Midcontinent affects only regional basis spreads. The +0.20 boost lifts HH-relevant notices toward maximum confidence without penalizing non-HH notices — basis traders care about those too. The alternative of penalizing non-HH locations (previously implemented as −0.10) was removed because it disproportionately suppressed legitimate signals in large Midcontinent systems where NGPL has significant capacity.

---

## Signal Threshold and Confidence Zeroing

`is_signal = confidence >= 0.5`. The threshold is inclusive to avoid edge cases where a Force Majeure with medium curtailment and LOC-level location scores exactly 0.50 and is incorrectly suppressed.

Non-signals are zeroed out (`confidence = 0.0`). Confidence is only meaningful for signals — reporting a confidence of 0.35 for a non-signal would imply it is "almost a signal," which is misleading for downstream consumers.

**Maximum achievable score:** `0.30 (VC-2 FM/OFO) + 0.30 (VC-3 large) + 0.30 (VC-4 system) + 0.20 (VC-5 HH) = 1.10`, clamped to 1.0.

**Minimum signal score:** 0.50 — any combination of adjustments that reaches this threshold with `is_signal=True`.
