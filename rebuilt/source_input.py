"""Spec-driven bounded source field parser; absence never fabricates a value."""

from __future__ import annotations

import math
import re
from datetime import datetime, timezone

HEADER_LABELS = {
    "tsp": "TSP/TSP Name",
    "critical": "Critical",
    "type1": "Notice Type Desc (1)",
    "type2": "Notice Type Desc (2)",
    "notice_effective_date": "Notice Eff Date/Time",
    "notice_end_date": "Notice End Date/Time",
    "post_date": "Post Date/Time",
    "notice_id": "Notice ID",
    "req_rsp": "Reqrd Rsp",
    "rsp_date": "Rsp Date/Time",
    "status": "Notice Stat Desc",
    "prior_notice_id": "Prior Notice",
    "subject": "Subject",
}


# Technical read inventory, independent of the editable declarations.
# Adding a parser read requires an input-contract line and a probe.
READ_FIELDS = frozenset(
    (
        "header.tsp",
        "header.critical",
        "header.type1",
        "header.type2",
        "header.notice_effective_date",
        "header.notice_end_date",
        "header.post_date",
        "header.notice_id",
        "header.req_rsp",
        "header.rsp_date",
        "header.status",
        "header.prior_notice_id",
        "header.subject",
        "metadata.notice_id",
        "metadata.notice_type",
        "metadata.subject",
        "metadata.download_date",
        "metadata.source_url",
        "metadata.html_file",
        "body",
        "notice.notice_id",
        "notice.prior_notice_id",
        "notice.status",
        "notice.notice_type",
        "notice.information_only",
        "notice.body_text",
        "notice.effective_datetime",
        "notice.end_datetime",
        "locations",
        "restrictions",
        "locations[].loc_code",
        "locations[].segment",
        "locations[].compressor_station",
        "locations[].zone",
        "locations[].system",
        "restrictions[].service_type",
        "restrictions[].restriction_type",
        "restrictions[].restriction_value",
        "restrictions[].restriction_unit",
        "restrictions[].status",
        "restrictions[].location_index",
        "restrictions[].start_datetime",
        "restrictions[].end_datetime",
        "semantic.extraction_usable",
        "semantic.execution_error",
        "semantic.helpers",
        "semantic.source_media_type",
    )
)


def timestamp(value, contract: dict) -> tuple[str | None, str | None]:
    if value in (None, "", "TBD"):
        return None, None
    if not isinstance(value, str):
        return None, "timestamp must be text"
    parsed = None
    for fmt in contract["date_formats"]:
        try:
            if fmt == "ISO8601":
                if not re.fullmatch(
                    r"\d{4}-\d\d-\d\d(?:[T ]\d\d:\d\d(?::\d\d(?:\.\d+)?)?(?:Z|[+-]\d\d:\d\d)?)?",
                    value.strip(),
                ):
                    continue
                parsed = datetime.fromisoformat(value.strip())
            else:
                parsed = datetime.strptime(" ".join(value.split()), fmt)
            break
        except ValueError:
            pass
    if parsed is None:
        return None, "unrecognized or impossible source date"
    if parsed.tzinfo is None:
        return None, None
    return parsed.astimezone(timezone.utc).isoformat(), None


def parse_field(row: dict, value, contract: dict) -> dict:
    missing = value is None or value == ""
    kind = row["Type"]
    issue = None
    if missing:
        issue = "missing required value" if row["Missing"] == "ERROR" else None
    elif kind == "timestamp":
        _, issue = timestamp(value, contract)
    else:
        good = {
            "text": isinstance(value, str),
            "identifier": (type(value) is int and value > 0)
            or (
                isinstance(value, str)
                and bool(re.fullmatch("[0-9]+", value.strip()))
                and int(value) > 0
            ),
            "integer": type(value) is int and value >= 0,
            "number": type(value) in (float, int) and math.isfinite(value) and value >= 0,
            "flag": type(value) is bool or (type(value) is int and value in (0, 1)),
            "boolean": type(value) is bool,
            "rows": isinstance(value, list) and all(isinstance(r, dict) for r in value),
            "helper_pairs": isinstance(value, list)
            and all(
                isinstance(r, (list, tuple))
                and len(r) == 2
                and isinstance(r[0], str)
                and (r[1] is None or type(r[1]) in (str, bool, int, float))
                for r in value
            ),
            "text_or_integer": isinstance(value, str) or type(value) is int,
        }
        if kind not in good:
            raise ValueError(
                f"spec.md:{row['_line']}: block spec-inputs, row {row['ID']}: unknown type {kind}"
            )
        if not good[kind]:
            issue = "malformed " + kind
    normalized = (
        None
        if missing or issue
        else timestamp(value, contract)[0]
        if kind == "timestamp"
        else value
    )
    return {
        "id": row["ID"],
        "field": row["Field"],
        "raw": value,
        "normalized": normalized,
        "status": "ERROR" if issue else "UNKNOWN" if normalized is None else "KNOWN",
        "issue": issue,
        "spec_line": row["_line"],
    }


def capture_fields(output: dict, semantic: dict, contract: dict) -> list[dict]:
    result: list[dict] = []
    for row in contract["input_contract"]:
        path = row["Field"]
        if path.startswith(("header.", "metadata.")) or path == "body":
            continue
        if "[]." in path:
            collection, name = path.split("[].")
            items = output.get(collection)
            values = (
                [r.get(name) for r in items if isinstance(r, dict)]
                if isinstance(items, list)
                else []
            )
        elif path.startswith("semantic."):
            values = [semantic.get(path.split(".")[1])]
        elif path.startswith("notice."):
            notice = output.get("notice")
            values = [notice.get(path.split(".")[1]) if isinstance(notice, dict) else None]
        else:
            values = [output.get(path)]
        result.extend(parse_field(row, v, contract) for v in values)
    return result


def parse_html(text: str, metadata: dict, contract: dict) -> dict:
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(text, "html.parser")
    for node in soup(["script", "style"]):
        node.decompose()
    lines = [x.strip() for x in soup.get_text("\n").splitlines() if x.strip()]
    header = {}
    for field, label in HEADER_LABELS.items():
        pattern = re.compile("^" + re.escape(label) + r"\s*:?\s*(.*)$", re.I)
        for i, line in enumerate(lines):
            m = pattern.match(line)
            if m:
                following = lines[i + 1] if i + 1 < len(lines) else ""
                is_label = any(following.rstrip(":").strip() == v for v in HEADER_LABELS.values())
                header[field] = m[1] or ("" if is_label else following)
                break
    body = "\n".join(lines[lines.index("Notice Text:") + 1 :]) if "Notice Text:" in lines else None
    results = []
    for row in contract["input_contract"]:
        key = row["Field"]
        if key.startswith("header."):
            value = header.get(key.split(".")[1])
        elif key.startswith("metadata."):
            value = metadata.get(key.split(".")[1])
        elif key == "body":
            value = body
        else:
            continue
        results.append(parse_field(row, value, contract))
    return {
        "fields": results,
        "header": header,
        "body": body,
        "status": "ERROR"
        if any(r["status"] == "ERROR" for r in results)
        else "PARSED_WITH_UNKNOWNS",
    }
