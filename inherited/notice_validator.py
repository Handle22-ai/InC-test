"""
Validity / signal assessment agent (Agent 2).

Receives the structured extraction output from llm_utils.llm_extract_notice()
and decides whether the notice constitutes a trading signal, assigns a
confidence score, and returns validity flags for trader audit.

Signal definition:
  A notice describing a meaningful disruption likely to affect gas flow volumes
  or regional prices. Strong signals have: critical/unplanned events (force
  majeure, urgent disruptions), planned outages with material impact on flow,
  identifiable pipeline segment or zone, measurable curtailment, and geographic
  relevance (Louisiana pipelines, Henry Hub, LNG export terminals).
  Routine notices, administrative updates, and purely informational notices
  are not signals. Superseding notices must not generate duplicate signals.
"""
import re
from typing import Dict, List, Optional, Tuple

from llm_utils import llm_is_supersede_material, llm_assess_curtailment_impact


# ── Signal classification sets ───────────────────────────────────────────────

_SIGNAL_TYPES = frozenset({
    "FORCE MAJEURE",
    "CAPACITY CONSTRAINT",
    "OPERATIONAL FLOW ORDER",
    "OPERATIONAL ALERT",
    "MAINTENANCE",
    "STORAGE",
    "OTHER",
})

_NON_SIGNAL_TYPES = frozenset({
    "PIPELINE CONDITIONS",
    "REGULATORY",
    "TARIFF",
    "INFORMATIONAL",
})

# VC-2 type boosts — tiered by certainty of operational impact
_VC2_HIGH = frozenset({"FORCE MAJEURE", "OPERATIONAL FLOW ORDER"})   # +0.30
_VC2_MED  = frozenset({"CAPACITY CONSTRAINT"})                         # +0.20
_VC2_LOW  = frozenset({"MAINTENANCE"})                                 # +0.10

# ── Regex patterns ───────────────────────────────────────────────────────────

# Henry Hub / Louisiana / LNG export terminal zones
_HH_ZONE_RE = re.compile(
    r"louisiana\s*zone|gulf\s*coast\s*(zone|system|mainline)|henry\s*hub",
    re.I,
)


# ── Helpers ──────────────────────────────────────────────────────────────────

def _type_matches(notice_type: str, type_set: frozenset) -> bool:
    t = notice_type.upper()
    return any(s in t for s in type_set)


def _location_granularity(locations: list) -> Tuple[float, str]:
    """
    Score location specificity. More specific = higher confidence that the
    signal is actionable and the constraint point is known.

    Hierarchy (most → least specific):
      LOC codes  (specific meter/delivery point)
      segments   (pipeline segment number)
      zones      (named zone within a system)
      system     (system-level only, no finer detail)
      empty      (no locations at all)

    Returns (delta, flag_message).
    """
    if not locations:
        return -0.10, (
            "VC-4: no locations extracted — constraint point unknown (-0.10 confidence)"
        )

    has_loc    = any(loc.get("loc_code") for loc in locations)
    has_cs     = any(loc.get("compressor_station") for loc in locations)
    has_seg    = any(loc.get("segment") for loc in locations)
    has_zone   = any(loc.get("zone") for loc in locations)
    has_system = any(loc.get("system") for loc in locations)

    if has_loc or has_cs:
        return +0.10, (
            "VC-4: specific LOC code(s) or compressor station identified — precise constraint point known (+0.10 confidence)"
        )
    if has_seg:
        return +0.15, (
            "VC-4: pipeline segment identified — constraint point known (+0.15 confidence)"
        )
    if has_zone:
        return +0.20, (
            "VC-4: named zone(s) identified — regional constraint known (+0.20 confidence)"
        )
    if has_system:
        return +0.30, (
            "VC-4: system-level location identified — broad constraint scope (+0.30 confidence)"
        )
    # locations list is non-empty but all fields are null
    return -0.10, (
        "VC-4: locations extracted but no identifiable point, segment, zone, or system — "
        "constraint point effectively unknown (-0.10 confidence)"
    )


def _geo_adjustment(locations: list) -> Tuple[float, str]:
    """
    +0.20 if any location is in a Henry Hub / Louisiana / LNG-connected zone.
    -0.10 if locations exist but none are in those zones.
     0.00 if no locations (VC-4 already handles the empty case).
    """
    if not locations:
        return 0.0, ""

    for loc in locations:
        zone   = loc.get("zone") or ""
        name   = loc.get("loc_name") or ""
        system = loc.get("system") or ""
        if _HH_ZONE_RE.search(zone) or _HH_ZONE_RE.search(name) or _HH_ZONE_RE.search(system):
            return +0.20, (
                "VC-5: Henry Hub / Gulf Coast / Louisiana zone location — "
                "direct price impact on NYMEX front-month (+0.20 confidence)"
            )

    return 0.0, ""


# ── Public interface ─────────────────────────────────────────────────────────

def validate_notice(
    notice_type: str,
    status: str,
    header: dict,
    body: str,
    locations: list,
    restrictions: list,
    prior_notice_row: Optional[Dict] = None,
    information_only: bool = False,
) -> Tuple[bool, float, List[str]]:
    """
    Assess whether a notice is a trading signal.

    Returns (is_signal, confidence_score 0.0–1.0, validity_flags).
    Flags are human-readable strings forming the trader audit trail.

    prior_notice_row : DB row for the prior notice, or None.
    information_only : flag set by Agent 1 when the notice is purely informational.

    Validity conditions:
      VC-1  Notice Actionability: information_only flag + SUPERSEDE/TERMINATE status handling
      VC-2  Notice type gate; +0.10 for high-confidence types
      VC-3  Measurable curtailment: +0.10 if present, -0.30 if absent
      VC-4  Location granularity: -0.10 to +0.30 based on specificity
      VC-5  Geographic relevance: +0.20 / -0.10
    """
    flags: List[str] = []
    type_upper = notice_type.upper().strip()
    status_upper = status.upper().strip()

    # ── VC-1a: Information-only check ────────────────────────────────────────
    if information_only:
        flags.append(
            "VC-1: information-only notice — Agent 1 determined this notice is purely "
            "informational (retrospective report, advisory, or administrative update); "
            "not a current operational restriction"
        )
        return False, 0.0, flags

    # ── VC-1b: SUPERSEDE ─────────────────────────────────────────────────────
    if status_upper == "SUPERSEDE":
        if prior_notice_row is None:
            flags.append(
                "VC-1: superseded notice — prior notice not in DB, "
                "cannot compare; continuing validation"
            )
        else:
            current_row = {
                "notice_type": notice_type,
                "subject":     header.get("subject", ""),
                "body_text":   body,
            }
            is_material = llm_is_supersede_material(current_row, prior_notice_row)

            if is_material is False:
                flags.append(
                    f"VC-1: superseded notice — LLM assessed as not materially "
                    f"different from prior notice {prior_notice_row.get('notice_id')}; "
                    "suppressed to avoid duplicate signal"
                )
                return False, 0.0, flags
            elif is_material is True:
                flags.append(
                    f"VC-1: superseded notice — LLM assessed as materially different "
                    f"from prior notice {prior_notice_row.get('notice_id')}; "
                    "continuing as potential new signal"
                )
            else:
                flags.append(
                    "VC-1: superseded notice — LLM unavailable for comparison; "
                    "treated as non-material update to prior notice"
                )
                return False, 0.0, flags

    # ── VC-1c: TERMINATE ─────────────────────────────────────────────────────
    elif status_upper == "TERMINATE":
        if prior_notice_row is None:
            flags.append(
                "VC-1: terminated notice — prior notice not in DB; "
                "cannot assess signal impact of lift; continuing validation"
            )
        else:
            prior_is_signal = bool(prior_notice_row.get("is_signal"))
            prior_confidence = float(prior_notice_row.get("confidence_score") or 0.0)

            if prior_is_signal:
                flags.append(
                    f"VC-1: terminated notice — prior notice "
                    f"{prior_notice_row.get('notice_id')} was a signal "
                    f"(confidence {prior_confidence:.2f}); "
                    "restriction lifted, inheriting confidence as termination signal"
                )
                return True, prior_confidence, flags
            else:
                flags.append(
                    f"VC-1: terminated notice — prior notice "
                    f"{prior_notice_row.get('notice_id')} was not a signal; "
                    "termination has no trading relevance"
                )
                return False, 0.0, flags

    # ── VC-2: Notice type gate ────────────────────────────────────────────────
    if _type_matches(type_upper, _NON_SIGNAL_TYPES):
        flags.append(
            f"VC-2: non-signal notice type ({notice_type}) — "
            "administrative or tariff notice, no operational disruption"
        )
        return False, 0.0, flags

    is_signal_capable = _type_matches(type_upper, _SIGNAL_TYPES)
    if not is_signal_capable:
        flags.append(
            f"VC-2: unknown notice type '{notice_type}' — treating as signal-capable; "
            "downstream validators will assess operational impact"
        )

    base = 0.0
    adjustment = 0.0

    if _type_matches(type_upper, _VC2_HIGH):
        adjustment += 0.30
        flags.append(
            f"VC-2: high-confidence notice type ({notice_type}) — "
            "force majeure or OFO (+0.30 confidence)"
        )
    elif _type_matches(type_upper, _VC2_MED):
        adjustment += 0.20
        flags.append(
            f"VC-2: high-confidence notice type ({notice_type}) — "
            "capacity constraint (+0.20 confidence)"
        )
    elif _type_matches(type_upper, _VC2_LOW):
        adjustment += 0.10
        flags.append(
            f"VC-2: high-confidence notice type ({notice_type}) — "
            "maintenance outage (+0.10 confidence)"
        )

    # ── VC-3: Measurable curtailment ─────────────────────────────────────────
    has_measurable_impact = bool(restrictions) and (
        any(r.get("restriction_value") is not None for r in restrictions)
        or any((r.get("restriction_type") or "").upper() == "UNAVAILABLE" for r in restrictions)
    )

    if has_measurable_impact:
        impact = llm_assess_curtailment_impact(body, restrictions)
        if impact == "large":
            adjustment += 0.30
            flags.append(
                "VC-3: large curtailment impact — primary/secondary firm affected or "
                ">10% volume reduction or UNAVAILABLE (+0.30 confidence)"
            )
        elif impact == "medium":
            adjustment += 0.20
            flags.append(
                "VC-3: medium curtailment impact — firm service affected with 10–30% "
                "reduction (+0.20 confidence)"
            )
        else:
            # "small" or LLM unavailable — default to small
            adjustment += 0.10
            flags.append(
                "VC-3: small curtailment impact — interruptible/lower-priority service "
                "only or <10% reduction (+0.10 confidence)"
            )
    else:
        adjustment -= 0.20
        flags.append(
            "VC-3: no measurable curtailment — no restriction value and no UNAVAILABLE "
            "restriction type extracted; advisory notice only (-0.20 confidence)"
        )

    # ── VC-4: Location granularity ────────────────────────────────────────────
    loc_delta, loc_flag = _location_granularity(locations)
    adjustment += loc_delta
    flags.append(loc_flag)

    # ── VC-5: Geographic relevance ────────────────────────────────────────────
    geo_delta, geo_flag = _geo_adjustment(locations)
    if geo_flag:
        adjustment += geo_delta
        flags.append(geo_flag)

    # ── Final confidence and is_signal ───────────────────────────────────────
    confidence = min(1.0, max(0.0, round(base + adjustment, 2)))
    is_signal = confidence >= 0.5  # noqa: E225 — inclusive lower bound

    if not is_signal:
        confidence = 0.0

    return is_signal, confidence, flags
