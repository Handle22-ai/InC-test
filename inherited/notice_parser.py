"""
Parses downloaded NGPL HTML notices into structured records matching the
3-table SQLite schema (notices, notice_locations, notice_restrictions).
"""
import json
import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from bs4 import BeautifulSoup
from llm_utils import llm_extract_notice
from notice_validator import validate_notice

logger = logging.getLogger(__name__)

# ── header field labels as they appear in the EBB HTML ──────────────────────
_HEADER_LABELS = {
    "tsp":                    re.compile(r"TSP/TSP Name", re.I),
    "critical":               re.compile(r"Critical\s*:", re.I),
    "type1":                  re.compile(r"Notice Type Desc \(1\)", re.I),
    "type2":                  re.compile(r"Notice Type Desc \(2\)", re.I),
    "notice_effective_date":  re.compile(r"Notice Eff Date/Time", re.I),
    "notice_end_date":        re.compile(r"Notice End Date/Time", re.I),
    "post_date":              re.compile(r"Post Date/Time", re.I),
    "notice_id":              re.compile(r"Notice ID\s*:", re.I),
    "req_rsp":                re.compile(r"Reqrd Rsp\s*:", re.I),
    "rsp_date":               re.compile(r"Rsp Date\s*:", re.I),
    "status":                 re.compile(r"Notice Stat Desc\s*:", re.I),
    "prior_notice_id":        re.compile(r"Prior Notice\s*:", re.I),
    "subject":                re.compile(r"Subject\s*:", re.I),
}

_DATETIME_FMTS = [
    "%m/%d/%Y %I:%M:%S%p",
    "%m/%d/%Y %I:%M:%S %p",
    "%m/%d/%Y  %I:%M:%S%p",
    "%m/%d/%Y  %I:%M:%S %p",
    "%m/%d/%Y",
]

# ── service type patterns for restriction extraction ─────────────────────────
_SERVICE_PATTERNS = [
    (re.compile(r"Primary\s+Firm", re.I),                        "PRIMARY_FIRM"),
    (re.compile(r"Secondary\s+in[- ]?path\s+Firm", re.I),        "SECONDARY_INPATH_FIRM"),
    (re.compile(r"Secondary\s+out[- ]?of[- ]?path\s+Firm", re.I),"SECONDARY_OUTPATH_FIRM"),
    (re.compile(r"AOR/ITS|interruptible\s+service", re.I),       "AOR_ITS"),
    (re.compile(r"\binterruptible\b", re.I),                      "INTERRUPTIBLE"),
    (re.compile(r"no[- ]notice", re.I),                           "NO_NOTICE"),
]

_MDQ_PCT_RE   = re.compile(r"no\s+less\s+than\s+(\d+(?:\.\d+)?)\s*%\s+of\s+(?:contract\s+)?MDQ", re.I)
_HOURLY_RE    = re.compile(r"(\d+(?:\.\d+)?)\s*%\s+of\s+(?:their\s+)?(?:firm|interruptible)\s+service\s+rights?", re.I)
_DIRECTION_RE = re.compile(r"\b(northbound|southbound|eastbound|westbound)\b", re.I)

# LOC code: "LOC 12345" or "LOC 12345 -"
_LOC_RE       = re.compile(r"\bLOC\s+(\d+)\s*[-–]?\s*([^\n\r,;]+)?", re.I)
# Compressor station: "CS 342" / "Compressor Station 342"
_CS_RE        = re.compile(r"(?:Compressor\s+Station\s+|CS\s+)(\d+)", re.I)
# Segment number: "Segment 23" / "Segments 23 and 24"
_SEG_RE       = re.compile(r"\bSegments?\s+([\d/,\s]+(?:and\s+\d+)?)", re.I)
# Zone names
_ZONE_RE      = re.compile(
    r"(Louisiana Zone|Permian Zone|Amarillo (?:System|Zone)|"
    r"Gulf Coast (?:System|Zone|Mainline)|Market Delivery Zone|"
    r"South Texas Zone|Midcontinent Zone|Texok Zone)", re.I
)
_TARIFF_RE    = re.compile(r"GT&C\s+Section\s+[\d.()a-z]+", re.I)
_OUTAGE_REF_RE = re.compile(r"X\d{2}-\d+", re.I)

# Validity condition thresholds
_MIN_BODY_WORDS = 40


def _parse_dt(raw: str) -> Optional[str]:
    """Parse EBB datetime string to ISO-8601; return None on failure."""
    raw = raw.strip()
    for fmt in _DATETIME_FMTS:
        try:
            return datetime.strptime(raw, fmt).isoformat()
        except ValueError:
            continue
    # Try stripping trailing whitespace variations
    raw2 = re.sub(r"\s+", " ", raw)
    for fmt in _DATETIME_FMTS:
        try:
            return datetime.strptime(raw2, fmt).isoformat()
        except ValueError:
            continue
    return None


_ANY_LABEL_RE = re.compile(
    r"TSP/TSP Name|Critical\s*:|Notice Type Desc|Notice Eff Date|"
    r"Notice End Date|Post Date/Time|Notice ID\s*:|Reqrd Rsp\s*:|"
    r"Rsp Date\s*:|Notice Stat Desc\s*:|Prior Notice\s*:|Subject\s*:",
    re.I,
)


def _extract_header(soup: BeautifulSoup) -> Dict:
    """Pull structured header fields from the Notice Detail table."""
    text = soup.get_text("\n")
    lines = [l.strip() for l in text.splitlines() if l.strip()]

    def _find_value(pattern: re.Pattern) -> str:
        for i, line in enumerate(lines):
            if pattern.search(line):
                after = pattern.sub("", line).strip().lstrip(":").strip()
                if after:
                    return after
                # Look ahead, but stop if we hit another header label (empty field)
                for j in range(i + 1, min(i + 4, len(lines))):
                    candidate = lines[j]
                    if candidate and not _ANY_LABEL_RE.search(candidate):
                        return candidate
        return ""

    raw = {k: _find_value(p) for k, p in _HEADER_LABELS.items()}
    # Prior Notice is always a numeric ID — anything else means the field is empty
    if raw.get("prior_notice_id") and not re.fullmatch(r"\d+", raw["prior_notice_id"].strip()):
        raw["prior_notice_id"] = ""
    return raw


_BODY_TAIL_NOISE_RE = re.compile(
    r"Your session will expire|Click OK to renew|Your download is starting",
    re.I,
)


def _extract_body(soup: BeautifulSoup) -> str:
    """Return cleaned notice body text, stripping nav/menu boilerplate."""
    text = soup.get_text("\n")
    # Find the start boundary
    for marker in ["Notice Text:", "Notice Detail"]:
        idx = text.find(marker)
        if idx != -1:
            body = text[idx + len(marker):]
            # Strip leading nav remnants
            for trim in ["Return To Results", "PDF\nTEXT"]:
                ti = body.find(trim)
                if ti != -1:
                    body = body[ti + len(trim):]
            # Strip trailing session/UI noise
            tail_m = _BODY_TAIL_NOISE_RE.search(body)
            if tail_m:
                body = body[:tail_m.start()]
            return re.sub(r"\n{3,}", "\n\n", body).strip()
    # Fallback
    body = re.sub(r"\n{3,}", "\n\n", text[-4000:]).strip()
    tail_m = _BODY_TAIL_NOISE_RE.search(body)
    if tail_m:
        body = body[:tail_m.start()].strip()
    return body


def _extract_locations(body: str, notice_id: int) -> List[Dict]:
    """Extract location rows from notice body text."""
    locations = []
    seen = set()

    # LOC codes with names
    for m in _LOC_RE.finditer(body):
        loc_code = f"LOC {m.group(1)}"
        loc_name = (m.group(2) or "").strip().rstrip(".,;")
        key = loc_code
        if key in seen:
            continue
        seen.add(key)

        locations.append({
            "notice_id":          notice_id,
            "loc_code":           loc_code,
            "loc_name":           loc_name or None,
            "segment":            None,
            "compressor_station": None,
            "zone":               None,
        })

    # Compressor stations as constraint points (if no LOC code already covers them)
    for m in _CS_RE.finditer(body):
        cs = f"CS {m.group(1)}"
        if cs in seen:
            continue
        seen.add(cs)

        # Segment
        seg = None
        seg_m = _SEG_RE.search(body[max(0, m.start() - 300): m.end() + 300])
        if seg_m:
            seg = seg_m.group(1).strip()

        # Zone
        zone = None
        zone_m = _ZONE_RE.search(body[max(0, m.start() - 400): m.end() + 400])
        if zone_m:
            zone = zone_m.group(1)

        locations.append({
            "notice_id":          notice_id,
            "loc_code":           None,
            "loc_name":           None,
            "segment":            seg,
            "compressor_station": cs,
            "zone":               zone,
        })

    # Zone-level entries (for OFO / Operational Alert with no individual LOC codes)
    if not locations:
        for m in _ZONE_RE.finditer(body):
            zone = m.group(1)
            if zone in seen:
                continue
            seen.add(zone)
            locations.append({
                "notice_id":          notice_id,
                "loc_code":           None,
                "loc_name":           None,
                "segment":            None,
                "compressor_station": None,
                "zone":               zone,
            })

    return locations


def _extract_restrictions(body: str, notice_id: int, effective_dt: Optional[str], end_dt: Optional[str]) -> List[Dict]:
    """Extract service-type restriction rows from notice body text."""
    restrictions = []

    # Direction
    dir_m = _DIRECTION_RE.search(body)
    flow_dir = dir_m.group(1).upper() if dir_m else "ALL"

    # MDQ-percentage restrictions (Maintenance / Force Majeure pattern)
    for m in _MDQ_PCT_RE.finditer(body):
        pct = float(m.group(1))
        ctx = body[max(0, m.start() - 300): m.start()]
        # Which service types does this apply to?
        applied = []
        for pat, svc in _SERVICE_PATTERNS:
            if pat.search(ctx):
                applied.append(svc)
        if not applied:
            applied = ["PRIMARY_FIRM"]

        for svc in applied:
            restrictions.append({
                "notice_id":         notice_id,
                "service_type":      svc,
                "restriction_type":  "SCHEDULED_TO_PCT_MDQ",
                "restriction_value": pct,
                "restriction_unit":  "PCT_MDQ",
                "flow_direction":    flow_dir,
                "start_datetime":    effective_dt,
                "end_datetime":      end_dt,
            })

        # AOR/ITS / secondary out-of-path typically flagged UNAVAILABLE alongside MDQ restriction
        unavail_ctx = body[m.start(): m.end() + 500].lower()
        if "aor/its" in unavail_ctx or "out-of-path" in unavail_ctx or "not be available" in unavail_ctx:
            restrictions.append({
                "notice_id":         notice_id,
                "service_type":      "AOR_ITS",
                "restriction_type":  "UNAVAILABLE",
                "restriction_value": None,
                "restriction_unit":  None,
                "flow_direction":    flow_dir,
                "start_datetime":    effective_dt,
                "end_datetime":      end_dt,
            })

    # Hourly-percentage restrictions (OFO / Operational Alert pattern)
    for m in _HOURLY_RE.finditer(body):
        pct = float(m.group(1))
        ctx = body[max(0, m.start() - 200): m.start()]
        svc = "PRIMARY_FIRM"
        for pat, s in _SERVICE_PATTERNS:
            if pat.search(ctx):
                svc = s
                break

        restrictions.append({
            "notice_id":         notice_id,
            "service_type":      svc,
            "restriction_type":  "HOURLY_LIMIT_PCT",
            "restriction_value": pct,
            "restriction_unit":  "PCT_HOURLY",
            "flow_direction":    "ALL",
            "start_datetime":    effective_dt,
            "end_datetime":      end_dt,
        })

    # Force majeure fully unavailable (no MDQ percentage stated)
    if not restrictions and any(
        w in body.lower() for w in ["unavailable", "shut in", "not be available"]
    ):
        restrictions.append({
            "notice_id":         notice_id,
            "service_type":      "ALL",
            "restriction_type":  "UNAVAILABLE",
            "restriction_value": None,
            "restriction_unit":  None,
            "flow_direction":    flow_dir,
            "start_datetime":    effective_dt,
            "end_datetime":      end_dt,
        })

    return restrictions


# ── Validity conditions ──────────────────────────────────────────────────────

def _assess_signal_and_validity(
    notice_type: str,
    status: str,
    body: str,
    locations: List[Dict],
    restrictions: List[Dict],
) -> Tuple[bool, float, List[str]]:
    """
    Apply validity conditions. Returns (is_signal, confidence, validity_flags).

    VC-1 Thin Notice: body too short → low confidence, not a signal
    VC-2 Supersede: status=SUPERSEDE → not a new signal
    VC-3 Keyword-without-volume: signal keywords present but no measurable
         restriction extracted → downgrade confidence
    VC-4 Geography: no Louisiana/Henry Hub adjacent location → lower priority
    """
    flags = []
    word_count = len(body.split())

    # VC-1: Thin notice
    if word_count < _MIN_BODY_WORDS:
        flags.append("thin_notice")

    # VC-2: Superseded update — not a new signal
    if status == "SUPERSEDE":
        flags.append("superseded_update")
        return False, 0.0, flags

    # Determine raw signal intent from notice type
    signal_types = {
        "FORCE MAJEURE", "OPERATIONAL FLOW ORDER",
        "CAPACITY CONSTRAINT", "MAINTENANCE", "OPERATIONAL ALERT",
    }
    type_upper = notice_type.upper()
    has_signal_type = any(t in type_upper for t in signal_types)

    # Routine/admin maintenance notices (outage impact report summaries)
    is_routine = bool(re.search(r"outage impact report", body, re.I)) and \
                 not any(r["restriction_type"] != "UNAVAILABLE" or r["restriction_value"]
                         for r in restrictions)

    if is_routine:
        flags.append("routine_admin")
        return False, 0.2, flags

    # VC-3: Keyword-without-volume — signal keywords present but nothing quantified
    has_volume = any(
        r["restriction_value"] is not None for r in restrictions
    ) or bool(re.search(r"\d+\s*(?:mmbtu|dth|mdth)\b", body, re.I))

    has_signal_keywords = bool(re.search(
        r"\b(curtailment|force majeure|shut in|unavailable|OFO|constraint|restriction)\b",
        body, re.I
    ))

    if has_signal_keywords and not has_volume and "thin_notice" not in flags:
        flags.append("keyword_without_volume")

    # VC-4: Geography relevance — Louisiana / Henry Hub / LNG export
    henry_hub_relevant = any(
        loc.get("zone") and re.search(r"Louisiana|Gulf Coast|South Texas", loc["zone"], re.I)
        or loc.get("loc_name") and "HENRY HUB" in (loc["loc_name"] or "").upper()
        for loc in locations
    )

    if locations and not henry_hub_relevant:
        flags.append("low_geo_relevance")

    # Compute confidence
    confidence = 1.0
    if "thin_notice" in flags:
        confidence -= 0.4
    if "keyword_without_volume" in flags:
        confidence -= 0.25
    if "low_geo_relevance" in flags:
        confidence -= 0.2
    if not locations:
        confidence -= 0.15
        flags.append("no_locations_extracted")
    confidence = max(0.0, round(confidence, 2))

    is_signal = has_signal_type and has_signal_keywords and "thin_notice" not in flags

    return is_signal, confidence, flags


# ── Public parser interface ──────────────────────────────────────────────────

def _fetch_prior_notice(db_conn, prior_id: Optional[int]) -> Optional[Dict]:
    """Look up a prior notice row from the DB. Returns None if not found or no connection."""
    if db_conn is None or prior_id is None:
        return None
    try:
        row = db_conn.execute(
            "SELECT notice_id, notice_type, subject, body_text, is_signal, confidence_score "
            "FROM notices WHERE notice_id = ?",
            (prior_id,),
        ).fetchone()
        if row is None:
            return None
        cols = ["notice_id", "notice_type", "subject", "body_text", "is_signal", "confidence_score"]
        return dict(zip(cols, row))
    except Exception as e:
        logger.warning(f"Failed to fetch prior notice {prior_id}: {e}")
        return None


def parse_notice_html(
    html_file: str,
    metadata: Dict,
    db_conn=None,
) -> Tuple[Dict, List[Dict], List[Dict]]:
    """
    Parse one HTML notice file.
    Returns (notice_row, locations_list, restrictions_list) ready for DB insert.
    """
    soup = BeautifulSoup(open(html_file, encoding="utf-8").read(), "html.parser")
    header = _extract_header(soup)
    body = _extract_body(soup)

    # Resolve notice_id (prefer from metadata, fall back to header)
    raw_id = metadata.get("notice_id") or header.get("notice_id", "")
    try:
        notice_id = int(re.sub(r"\D", "", str(raw_id)))
    except ValueError:
        logger.warning(f"Cannot parse notice_id from {html_file}")
        notice_id = 0

    # Datetimes
    effective_dt = _parse_dt(header.get("notice_effective_date", ""))
    end_dt       = _parse_dt(header.get("notice_end_date", ""))
    post_dt      = _parse_dt(header.get("post_date", "")) or metadata.get("download_date")

    # Prior notice
    prior_raw = header.get("prior_notice_id", "").strip()
    try:
        prior_id = int(re.sub(r"\D", "", prior_raw)) if prior_raw else None
    except ValueError:
        prior_id = None

    # Status
    status_raw = header.get("status", "INITIATE").strip().upper()
    if not status_raw:
        status_raw = "INITIATE"

    notice_type = (
        metadata.get("notice_type")
        or header.get("type1", "")
        or "UNKNOWN"
    ).upper()

    # Sub-type
    notice_subtype = header.get("type2", "").strip().upper() or None

    # Tariff / outage report refs
    tariff_m = _TARIFF_RE.search(body)
    outage_m = _OUTAGE_REF_RE.search(body)

    # Agent 1: LLM extraction (with regex fallback)
    llm_result = llm_extract_notice(header, body, notice_id, effective_dt, end_dt)
    if llm_result is not None:
        locations, restrictions, information_only = llm_result
        provenance_flag = "llm_extraction"
    else:
        locations    = _extract_locations(body, notice_id)
        restrictions = _extract_restrictions(body, notice_id, effective_dt, end_dt)
        information_only = False
        provenance_flag = "regex_fallback"

    # Agent 2: validity / signal assessment
    prior_notice_row = _fetch_prior_notice(db_conn, prior_id)
    is_signal, confidence, flags = validate_notice(
        notice_type, status_raw, header, body, locations, restrictions,
        prior_notice_row=prior_notice_row,
        information_only=information_only,
    )
    flags.append(provenance_flag)

    notice_row = {
        "notice_id":          notice_id,
        "tsp_name":           header.get("tsp", "NATURAL GAS PIPELINE CO.").strip(),
        "pipeline_code":      "NGPL",
        "is_critical":        1 if header.get("critical", "").upper() == "Y" else 0,
        "notice_type":        notice_type,
        "notice_subtype":     notice_subtype,
        "effective_datetime": effective_dt or post_dt,
        "end_datetime":       end_dt,
        "post_datetime":      post_dt or datetime.utcnow().isoformat(),
        "response_required":  1 if header.get("req_rsp", "").strip() not in ("", "0") else 0,
        "response_due_date":  _parse_dt(header.get("rsp_date", "").strip()),
        "status":             status_raw,
        "prior_notice_id":    prior_id,
        "subject":            header.get("subject", metadata.get("subject", "")).strip(),
        "body_text":          body,
        "outage_report_ref":  outage_m.group(0) if outage_m else None,
        "tariff_section":     tariff_m.group(0) if tariff_m else None,
        "information_only":   1 if information_only else 0,
        "is_signal":          1 if is_signal else 0,
        "confidence_score":   confidence,
        "validity_flags":     json.dumps(flags),
        "source_url":         metadata.get("source_url"),
        "scraped_at":         metadata.get("download_date") or datetime.utcnow().isoformat(),
        "html_file":          str(html_file),
    }

    return notice_row, locations, restrictions


# ── Batch processor ──────────────────────────────────────────────────────────

class NoticeProcessor:
    """Reads metadata.json, parses all HTML notices, writes to DB and JSON."""

    def __init__(self, notices_dir: str = "notices"):
        self.notices_dir = Path(notices_dir)

    def process_all_notices(self, db_conn=None) -> List[Dict]:
        """
        Parse every notice in notices_dir/metadata.json.
        If db_conn is provided, inserts into SQLite.
        Returns list of (notice_row, locations, restrictions) tuples as dicts.
        """
        import json as _json
        from database import insert_notice

        metadata_file = self.notices_dir / "metadata.json"
        if not metadata_file.exists():
            logger.error(f"metadata.json not found at {metadata_file}")
            return []

        with open(metadata_file) as f:
            metadata_list = _json.load(f)

        results = []
        for entry in metadata_list:
            html_path = entry.get("html_file")
            if not html_path or not Path(html_path).exists():
                logger.warning(f"HTML file missing: {html_path}")
                continue
            try:
                notice_row, locations, restrictions = parse_notice_html(html_path, entry, db_conn=db_conn)
                results.append({
                    "notice":       notice_row,
                    "locations":    locations,
                    "restrictions": restrictions,
                })
                if db_conn:
                    insert_notice(db_conn, notice_row, locations, restrictions)
                logger.info(
                    f"Parsed {notice_row['notice_id']} "
                    f"[{notice_row['notice_type']}] "
                    f"signal={bool(notice_row['is_signal'])} "
                    f"conf={notice_row['confidence_score']} "
                    f"flags={notice_row['validity_flags']}"
                )
            except Exception as e:
                logger.error(f"Failed to parse {html_path}: {e}", exc_info=True)

        return results

    def save_signals_report(
        self,
        results: List[Dict],
        output_file: str = "trading_signals.json",
    ):
        """Save signal-positive notices (with locations + restrictions) to JSON."""
        import json as _json

        signals = [r for r in results if r["notice"]["is_signal"]]
        report_path = self.notices_dir / output_file
        with open(report_path, "w") as f:
            _json.dump(signals, f, indent=2)
        logger.info(f"Saved {len(signals)} signals to {report_path}")
