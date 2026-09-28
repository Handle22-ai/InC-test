"""
LLM utilities for the trading signal extractor.

Provides a single configured Anthropic client, shared helper functions
(notice type classification, supersede materiality, retrospective detection),
and the primary extraction agent (llm_extract_notice).
"""
import json
import logging
import os
import re as _re
from typing import Dict, List, Optional, Tuple

from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
_MODEL   = os.getenv("LLM_MODEL", "claude-sonnet-4-6")
_ENABLED = os.getenv("LLM_ENABLED", "true").lower() not in ("false", "0", "no")


def is_llm_available() -> bool:
    return _ENABLED and bool(_API_KEY) and _API_KEY != "your-api-key-here"


def get_client():
    import anthropic
    return anthropic.Anthropic(api_key=_API_KEY)


# ── Extraction agent (Agent 1) ────────────────────────────────────────────────

_RESTRICTION_SCHEMA = {
    "type": "object",
    "required": ["service_type", "restriction_type"],
    "properties": {
        "service_type": {
            "type": ["string", "null"],
            "description": (
                "Which transportation service type is restricted. "
                "Common values: PRIMARY_FIRM, SECONDARY_INPATH_FIRM, "
                "SECONDARY_OUTPATH_FIRM, AOR_ITS, INTERRUPTIBLE, NO_NOTICE, ALL. "
                "Use the exact wording from the notice if it doesn't fit these categories."
            )
        },
        "restriction_type": {
            "type": ["string", "null"],
            "description": (
                "The nature of the restriction. Common values: "
                "SCHEDULED_TO_PCT_MDQ (scheduled to no less than X% of MDQ), "
                "UNAVAILABLE (service completely unavailable), "
                "HOURLY_LIMIT_PCT (hourly takes limited to X% of rights), "
                "DAILY_LIMIT_PCT (daily takes limited to X%). "
                "Use a descriptive string if none of these fit."
            )
        },
        "restriction_value": {
            "type": ["number", "null"],
            "description": "Numeric value of the restriction e.g. 46.0 for 46% MDQ. Null if UNAVAILABLE."
        },
        "restriction_unit": {
            "type": ["string", "null"],
            "description": (
                "Unit for restriction_value. Common values: "
                "PCT_MDQ, PCT_HOURLY, MMBTU, DTH. Null if not applicable."
            )
        },
        "flow_direction": {
            "type": ["string", "null"],
            "description": (
                "The direction or side this restriction applies to. "
                "Use ON_TO_PIPE for gas injected into the pipeline (receipts/injections). "
                "Use OFF_OF_PIPE for gas taken off the pipeline (deliveries/withdrawals). "
                "Use a compass direction (NORTHBOUND, SOUTHBOUND, EASTBOUND, WESTBOUND) for directional flow restrictions. "
                "Use RECEIPT or DELIVERY when the notice uses those terms explicitly. "
                "Use ALL if it applies system-wide or direction is unspecified. "
                "Use null if not mentioned in the notice."
            )
        },
        "start_datetime": {
            "type": ["string", "null"],
            "description": (
                "The date this restriction takes effect, extracted from the notice body. "
                "Return as YYYY-MM-DD if the date is explicit. "
                "Return null if no start date is stated."
            )
        },
        "end_datetime": {
            "type": ["string", "null"],
            "description": (
                "The date this restriction ends, extracted from the notice body. "
                "Return as YYYY-MM-DD if an explicit end date is stated. "
                "Return 'TBD' if the notice says 'until further notice' or equivalent. "
                "Return null if no end date is mentioned at all."
            )
        }
    }
}

_EXTRACT_TOOL = {
    "name": "extract_notice_data",
    "description": (
        "Extract changed locations and their associated capacity restrictions from a "
        "natural gas pipeline notice. Use only information explicitly stated in the text. "
        "Return null for any field not present. "
        "Restrictions are nested inside each location they apply to."
    ),
    "input_schema": {
        "type": "object",
        "required": ["locations", "reasoning"],
        "properties": {
            "locations": {
                "type": "array",
                "description": (
                    "Each element is one impacted location group with its own restrictions. "
                    "IMPORTANT: if the notice uses a change indicator symbol (e.g. 'è Indicates Change'), "
                    "extract ONLY the locations and restrictions that are marked with that symbol — "
                    "all unmarked rows are unchanged from the prior notice and must be omitted. "
                    "If no change indicator is used, extract all impacted locations. "
                    "Create one location object per distinct (system, zone/segment/CS/LOC) grouping. "
                    "If a notice covers multiple systems (e.g. Amarillo System and Gulf Coast System), "
                    "create separate location objects for each system. "
                    "Nest the restrictions that apply specifically to that location inside it."
                ),
                "items": {
                    "type": "object",
                    "required": ["restrictions"],
                    "properties": {
                        "loc_codes": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": (
                                "List of numeric LOC identifiers (numbers only, no 'LOC' prefix) "
                                "that are directly impacted. e.g. ['3592', '25085']. "
                                "Empty list if no LOC codes are stated. "
                                "Do NOT include LOC codes explicitly stated as 'not impacted' or 'not affected'."
                            )
                        },
                        "loc_names": {
                            "type": "array",
                            "items": {"type": ["string", "null"]},
                            "description": (
                                "Human-readable names one-to-one with loc_codes. "
                                "Use null for a code whose name is not stated. "
                                "Empty list if no LOC codes."
                            )
                        },
                        "segments": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": (
                                "Pipeline segment numbers e.g. ['23', '24']. "
                                "Empty list if none mentioned."
                            )
                        },
                        "compressor_stations": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": (
                                "Compressor station identifiers, numbers only, no 'CS' prefix. "
                                "e.g. ['302', '343']. Empty list if none mentioned."
                            )
                        },
                        "zones": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": (
                                "Named pipeline zones e.g. ['Louisiana Zone', 'Texok Zone', "
                                "'Gulf Coast Mainline', 'Market Delivery Zone']. "
                                "Empty list if none mentioned."
                            )
                        },
                        "system": {
                            "type": ["string", "null"],
                            "description": (
                                "The named pipeline system this location belongs to, "
                                "e.g. 'Amarillo System', 'Gulf Coast System', 'Midcontinent System'. "
                                "Null if no system name is stated."
                            )
                        },
                        "restrictions": {
                            "type": "array",
                            "description": (
                                "All capacity or flow restrictions that apply to THIS location. "
                                "Include one entry per (service_type, restriction_type, flow_direction) combination."
                            ),
                            "items": _RESTRICTION_SCHEMA,
                        },
                    }
                }
            },
            "change_indicator": {
                "type": ["string", "null"],
                "description": (
                    "The exact change indicator symbol used in this notice (e.g. 'è', '*'), "
                    "as identified from its legend line (e.g. 'è Indicates Change'). "
                    "Null if no change indicator legend is present."
                )
            },
            "information_only": {
                "type": "boolean",
                "description": (
                    "True if this notice is purely informational and describes no active operational restriction. "
                    "Set to true for: retrospective post-event reports (describing something that already happened), "
                    "weather/demand advisories with no enforceable directive, administrative updates "
                    "(project lists, tariff filings, regulatory notices), and rolling maintenance plan summaries. "
                    "Set to false if the notice announces or enforces a current or upcoming restriction, "
                    "curtailment, force majeure, OFO, or maintenance outage with shipper impact."
                )
            },
            "reasoning": {
                "type": "string",
                "description": (
                    "One sentence explaining what this notice describes and "
                    "what the primary operational impact is."
                )
            }
        }
    }
}

_EXTRACT_SYSTEM_PROMPT = """\
You are a structured data extractor for natural gas pipeline EBB (Electronic Bulletin Board) notices.

Your job is to extract locations and their associated capacity restrictions from the notice body into a strict schema.

Before filling in the schema, reason carefully about the notice:
1. Is this notice INFORMATION ONLY? Set information_only=true if it is a retrospective post-event report, a weather/demand advisory with no enforceable directive, an administrative update (tariff filing, project list, regulatory notice), or a rolling maintenance plan summary. Set false if it announces or enforces a current or upcoming restriction, curtailment, force majeure, OFO, or maintenance outage with shipper impact.
2. Does this notice use a CHANGE INDICATOR symbol? Look for a legend line such as "è Indicates Change" or "* Indicates Change". If found, identify the exact symbol used (e.g. "è"). Only rows marked with that specific symbol represent changes — all other rows are unchanged from the prior notice and must be omitted.
3. What is the ROOT CAUSE of the restriction (e.g. maintenance at CS 343)?
4. What are the CONSTRAINT POINTS — the specific locations where the capacity limit is enforced? If a change indicator was found in step 2, only include locations that carry that symbol.
5. Which shippers / service types are SUBJECT TO the restriction at each constraint point?
6. Does the notice cover multiple named systems (e.g. Amarillo System, Gulf Coast System)? If so, create a separate location object for each system.

Schema structure: restrictions are nested inside each location they apply to. This makes the location↔restriction relationship explicit.

Rules:
- Extract only what is explicitly stated. Do not infer or hallucinate values.
- Never fabricate LOC codes, compressor station numbers, or segment numbers. If a location identifier does not appear verbatim in the notice text, leave that field null.
- Use null for any field not present in the text.
- Change indicators: if the notice uses a symbol such as "è" followed by "Indicates Change", extract ONLY the entries marked with that symbol. All unmarked rows are unchanged from the prior notice — omit them entirely.
- For locations: include ONLY the constraint point(s) that are marked as changed (or all impacted locations if no change indicator is used). Do not include locations that are the cause of the restriction, mentioned as positional context, or explicitly stated as unaffected.
- For system: capture the named pipeline system (e.g. "Amarillo System", "Gulf Coast System") when stated. Place it as the last identifier field, after zones. Use null if no system name appears.
- For flow_direction: use ON_TO_PIPE for "ON to the Pipe" sections, OFF_OF_PIPE for "OFF of the Pipe" sections. Use compass directions (NORTHBOUND etc.) for directional flow. Use RECEIPT/DELIVERY when the notice uses those terms. Use ALL for system-wide. Null if unspecified.
- For restrictions: nest inside the location they apply to. Only include service types explicitly restricted or unavailable. Include one entry per (service_type, restriction_type, flow_direction) combination.\
"""


def _clean_body_for_llm(body: str) -> str:
    body = _re.sub(r"\n{2,}", "\x00", body)
    body = _re.sub(r"(?<=[,\w])\n[ \t]*(?=\w)", " ", body)
    body = body.replace("\x00", "\n\n")
    return body.strip()


def _build_extract_prompt(header: Dict, body: str) -> str:
    return (
        "## Notice Header (pre-parsed)\n"
        f"Notice ID: {header.get('notice_id', 'unknown')}\n"
        f"Notice Type: {header.get('type1', '')} / {header.get('type2', '')}\n"
        f"Status: {header.get('status', '')}\n"
        f"Critical: {header.get('critical', '')}\n"
        f"Effective: {header.get('notice_effective_date', '')}\n"
        f"End: {header.get('notice_end_date', '')}\n"
        f"Subject: {header.get('subject', '')}\n"
        f"Prior Notice: {header.get('prior_notice_id', '') or 'None'}\n"
        "\n"
        "## Notice Body\n"
        f"{_clean_body_for_llm(body)}"
    )


def llm_extract_notice(
    header: Dict,
    body: str,
    notice_id: int,
    effective_dt: Optional[str],
    end_dt: Optional[str],
) -> Optional[Tuple[List[Dict], List[Dict], bool]]:
    """
    Call Claude to extract locations and restrictions.
    Returns (locations, restrictions, information_only) on success, None on failure/disabled.
    """
    if not is_llm_available():
        logger.warning("LLM unavailable — falling back to regex parser")
        return None

    try:
        client = get_client()
        user_prompt = _build_extract_prompt(header, body)

        logger.info(f"[LLM INPUT] Notice {notice_id} — model={_MODEL}")
        logger.info(f"[LLM INPUT] system prompt:\n{_EXTRACT_SYSTEM_PROMPT}")
        logger.info(f"[LLM INPUT] user prompt:\n{user_prompt}")

        response = client.messages.create(
            model=_MODEL,
            max_tokens=2048,
            system=_EXTRACT_SYSTEM_PROMPT,
            tools=[_EXTRACT_TOOL],
            tool_choice={"type": "tool", "name": "extract_notice_data"},
            messages=[{"role": "user", "content": user_prompt}],
        )

        logger.info(
            f"[LLM OUTPUT] Notice {notice_id} — "
            f"stop_reason={response.stop_reason} "
            f"input_tokens={response.usage.input_tokens} "
            f"output_tokens={response.usage.output_tokens}"
        )

        tool_use_block = next(
            (b for b in response.content if b.type == "tool_use"), None
        )
        if tool_use_block is None:
            logger.warning(f"[LLM OUTPUT] Notice {notice_id}: no tool call in response")
            return None

        data = tool_use_block.input
        logger.info(f"[LLM OUTPUT] Notice {notice_id} raw tool output:\n{json.dumps(data, indent=2)}")

        locations = []
        restrictions = []

        for loc in data.get("locations", []):
            system     = loc.get("system")
            loc_codes  = loc.get("loc_codes", []) or []
            loc_names  = loc.get("loc_names", []) or []
            segments   = loc.get("segments", []) or []
            cs_list    = loc.get("compressor_stations", []) or []
            zones      = loc.get("zones", []) or []
            loc_restrictions = loc.get("restrictions", []) or []

            # Build location rows; location_index is the position in the locations list
            loc_row_indices = []

            for i, code in enumerate(loc_codes):
                idx = len(locations)
                loc_row = {
                    "location_index":     idx,
                    "notice_id":          notice_id,
                    "loc_code":           code,
                    "loc_name":           loc_names[i] if i < len(loc_names) else None,
                    "segment":            segments[0] if segments else None,
                    "compressor_station": cs_list[0] if cs_list else None,
                    "zone":               zones[0] if zones else None,
                    "system":             system,
                }
                loc_row_indices.append(idx)
                locations.append(loc_row)

            if not loc_codes:
                for seg in segments or [None]:
                    for cs in cs_list or [None]:
                        for zone in zones or [None]:
                            if seg or cs or zone:
                                idx = len(locations)
                                loc_row = {
                                    "location_index":     idx,
                                    "notice_id":          notice_id,
                                    "loc_code":           None,
                                    "loc_name":           None,
                                    "segment":            seg,
                                    "compressor_station": cs,
                                    "zone":               zone,
                                    "system":             system,
                                }
                                loc_row_indices.append(idx)
                                locations.append(loc_row)

            # Attach a location_index to each restriction so callers can join them
            for r in loc_restrictions:
                for idx in loc_row_indices:
                    restrictions.append({
                        "notice_id":         notice_id,
                        "location_index":    idx,
                        "service_type":      r.get("service_type"),
                        "restriction_type":  r.get("restriction_type"),
                        "restriction_value": r.get("restriction_value"),
                        "restriction_unit":  r.get("restriction_unit"),
                        "flow_direction":    r.get("flow_direction"),
                        "start_datetime":    r.get("start_datetime") or effective_dt,
                        "end_datetime":      r.get("end_datetime") or end_dt,
                    })

        information_only = bool(data.get("information_only", False))
        return locations, restrictions, information_only

    except Exception as e:
        logger.error(f"Notice {notice_id}: LLM extraction failed — {e}")
        return None


# ── Validation helpers (used by notice_validator) ─────────────────────────────

def llm_classify_notice_type(notice_type: str, subject: str, body: str) -> Optional[str]:
    """
    Ask the LLM to map an unknown notice type to the semantically closest
    known type. Returns the resolved type string, or None if unavailable.
    """
    if not is_llm_available():
        return None

    known_types = [
        "FORCE MAJEURE", "CAPACITY CONSTRAINT", "OPERATIONAL FLOW ORDER",
        "OPERATIONAL ALERT", "MAINTENANCE", "STORAGE",
        "PIPELINE CONDITIONS", "REGULATORY", "TARIFF", "INFORMATIONAL",
    ]

    prompt = (
        f"A natural gas pipeline notice has the type label: \"{notice_type}\"\n"
        f"Subject: {subject}\n\n"
        f"Body (first 500 chars): {body[:500]}\n\n"
        f"Known notice types: {', '.join(known_types)}\n\n"
        "Which known type is semantically closest to this notice? "
        "Reply with ONLY the exact type string from the list above, nothing else."
    )

    try:
        client = get_client()
        response = client.messages.create(
            model=_MODEL,
            max_tokens=20,
            messages=[{"role": "user", "content": prompt}],
        )
        result = response.content[0].text.strip().upper()
        for t in known_types:
            if t in result:
                logger.info(f"LLM resolved unknown type '{notice_type}' → '{t}'")
                return t
        logger.warning(f"LLM returned unrecognised type for '{notice_type}': {result!r}")
        return None
    except Exception as e:
        logger.error(f"llm_classify_notice_type failed: {e}")
        return None


def llm_is_supersede_material(
    new_notice: dict,
    prior_notice: dict,
) -> Optional[bool]:
    """
    Ask the LLM whether a SUPERSEDE notice is materially different from its
    prior notice in a way that would require traders to adjust their positions.

    Returns True (materially different → treat as new signal),
            False (routine update → suppress),
            None (LLM unavailable or error → caller should proceed conservatively).
    """
    if not is_llm_available():
        return None

    prompt = (
        "You are assessing whether a natural gas pipeline notice update "
        "represents a material change that would require energy traders to "
        "adjust their positions.\n\n"
        "PRIOR NOTICE:\n"
        f"Type: {prior_notice.get('notice_type')}\n"
        f"Subject: {prior_notice.get('subject')}\n"
        f"Body: {prior_notice.get('body_text', '')[:800]}\n\n"
        "NEW NOTICE (supersedes the prior):\n"
        f"Type: {new_notice.get('notice_type')}\n"
        f"Subject: {new_notice.get('subject')}\n"
        f"Body: {new_notice.get('body_text', '')[:800]}\n\n"
        "Is the new notice materially different from the prior notice in terms of "
        "affected locations, restriction severity, scope, or operational impact? "
        "Answer with ONLY 'YES' or 'NO'."
    )

    try:
        client = get_client()
        response = client.messages.create(
            model=_MODEL,
            max_tokens=5,
            messages=[{"role": "user", "content": prompt}],
        )
        answer = response.content[0].text.strip().upper()
        logger.info(f"LLM supersede diff: prior={prior_notice.get('notice_id')} → {answer}")
        return answer.startswith("Y")
    except Exception as e:
        logger.error(f"llm_is_supersede_material failed: {e}")
        return None


def llm_assess_curtailment_impact(body: str, restrictions: list) -> Optional[str]:
    """
    Ask the LLM to assess the volume impact of a curtailment.

    Returns 'large', 'medium', or 'small', or None if LLM unavailable/error.

    Criteria:
    - Who is affected: Primary Firm and Secondary Firm are high-priority service
      classes; if they are curtailed the impact is larger.
    - How much: >30% reduction = large, 10-30% = medium, <10% = small.
      UNAVAILABLE is always large.
    - 'large'  → +0.30 in VC-3
    - 'medium' → +0.20 in VC-3
    - 'small'  → +0.10 in VC-3
    """
    if not is_llm_available():
        return None

    restrictions_summary = json.dumps(
        [
            {k: v for k, v in r.items() if k in
             ("service_type", "restriction_type", "restriction_value", "restriction_unit")}
            for r in restrictions
        ],
        indent=2,
    )

    prompt = (
        "You are assessing the volume impact of a natural gas pipeline curtailment notice.\n\n"
        "## Extracted restrictions\n"
        f"{restrictions_summary}\n\n"
        "## Notice body\n"
        f"{body[:2000]}\n\n"
        "Assess the curtailment impact using these two criteria:\n"
        "1. WHO is affected: Primary Firm and Secondary Firm nominations are the highest-priority "
        "service classes. If they are curtailed, the impact is inherently larger. Interruptible "
        "and AOR/ITS service are lower priority and their curtailment has less market impact.\n"
        "2. HOW MUCH: If the restriction is expressed as a percentage of MDQ or hourly rights, "
        "a reduction of more than 30% of normal volumes counts as a large impact. 30% - 10% coutns as a medium impact, <10% counts as a small impact "
        "UNAVAILABLE (complete outage) is always a large impact.\n\n"
        "Definitions:\n"
        "- large: Primary Firm >10% volume reduction or UNAVAILABLE\n"
        "- medium: Firm service affected but <10% reduction, OR interruptible-only with large reduction(or UNAVAILABLE)\n"
        "- small: Only interruptible AND/OR service affected with minor OR medium reduction\n\n"
        "First explain your reasoning in 2-3 sentences, then on the last line write ONLY the verdict word: 'large', 'medium', or 'small'."
    )

    try:
        client = get_client()
        response = client.messages.create(
            model=_MODEL,
            max_tokens=200,
            messages=[{"role": "user", "content": prompt}],
        )
        full_response = response.content[0].text.strip()
        logger.info(f"LLM curtailment impact reasoning:\n{full_response}")

        # Verdict is the last non-empty line
        # Scan all lines bottom-up for a verdict word, stripping markdown/punctuation
        for line in reversed(full_response.split("\n")):
            word = line.strip().lower().strip("*_`.,;: ")
            if word in ("large", "medium", "small"):
                return word
        logger.warning(f"LLM returned no recognisable verdict: {full_response!r}")
        return None
    except Exception as e:
        logger.error(f"llm_assess_curtailment_impact failed: {e}")
        return None


def llm_is_retrospective(body: str) -> Optional[bool]:
    """
    Ask the LLM whether a notice body is a retrospective report for an event
    that has already ended, rather than a current operational restriction.

    Returns True (retrospective → not a live signal),
            False (current event → continue validation),
            None (LLM unavailable or error).
    """
    if not is_llm_available():
        return None

    prompt = (
        "Read the following natural gas pipeline notice body carefully.\n\n"
        f"Notice body:\n{body}\n\n"
        "Determine whether this notice is PURELY a retrospective compliance report "
        "describing an OFO or operational event that has ALREADY ENDED AND BEEN REMOVED — "
        "for example, a post-event report filed under GT&C Section 23.6 that recounts "
        "what happened during a past OFO.\n\n"
        "Key signals that it IS retrospective: past-tense language throughout "
        "('Natural issued', 'The OFO was issued', 'did not result in', 'OFO was removed'), "
        "the event dates are entirely in the past, and the notice reads like a summary "
        "of a completed event rather than an active restriction.\n\n"
        "Key signals that it is NOT retrospective: the restriction is currently active, "
        "or the notice is announcing an upcoming or ongoing restriction.\n\n"
        "Is this notice purely a retrospective report of a past, already-ended event? "
        "Answer with ONLY 'YES' or 'NO'."
    )

    try:
        client = get_client()
        response = client.messages.create(
            model=_MODEL,
            max_tokens=5,
            messages=[{"role": "user", "content": prompt}],
        )
        answer = response.content[0].text.strip().upper()
        logger.info(f"LLM retrospective check: {answer}")
        return answer.startswith("Y")
    except Exception as e:
        logger.error(f"llm_is_retrospective failed: {e}")
        return None
