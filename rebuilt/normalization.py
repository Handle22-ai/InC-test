"""Translate retained extracted assertions into the normalized classifier boundary.

No classification label or numeric model score enters this translation. Ambiguous
values/timezones remain explicit gaps instead of guessed semantic facts.
"""

from __future__ import annotations

import json

from rebuilt.rule_engine import load_policy, same


def normalize(
    output: dict,
    source_sha256: str,
    semantic: dict,
    reference_time: str,
    history: list[dict],
    *,
    contract: dict | None = None,
) -> tuple[dict, list[str]]:
    active = contract or load_policy()
    mapping = active["normalization"]
    from rebuilt.source_input import capture_fields, timestamp

    input_observations = capture_fields(output, semantic, active)
    malformed = next((r for r in input_observations if r["status"] == "ERROR"), None)
    if malformed:
        raise ValueError(
            f"spec.md:{malformed['spec_line']}: block spec-inputs, row {malformed['id']}: {malformed['field']}: {malformed['issue']}"
        )
    notice = output["notice"]
    restrictions = output.get("restrictions", [])
    reference = "source.fields.body"
    gaps = [
        f"{row['id']} {row['field']}: {row['issue']}"
        for row in input_observations
        if row["status"] == "ERROR"
    ]
    services = sorted(
        {mapping["services"].get(row.get("service_type"), "UNKNOWN") for row in restrictions}
    )
    availability = {
        mapping["availability"].get(row.get("restriction_type"), "UNKNOWN") for row in restrictions
    }
    availability_value = next(iter(availability)) if len(availability) == 1 else "UNKNOWN"
    information = notice.get("information_only") in (True, 1)
    content = mapping["content"][
        "information_only" if information else "restrictions" if restrictions else "otherwise"
    ]
    locations = []
    for row in output.get("locations", []):
        for field, kind in mapping["locations"].items():
            if row.get(field) is not None:
                item = {"kind": kind, "value": str(row[field]), "evidence_ref": reference}
                if item not in locations:
                    locations.append(item)
    quantities = []
    for row in restrictions:
        kind = mapping["quantities"].get(row.get("restriction_type"))
        value = row.get("restriction_value")
        if kind and value is not None:
            quantities.append(
                {
                    **kind,
                    "value": value,
                    "basis": str(row.get("restriction_unit") or "source restriction"),
                    "evidence_ref": reference,
                }
            )
        elif kind and value is None:
            gaps.append("Missing numeric value for " + str(row.get("restriction_type")))

    def instant(value):
        if not value or value == "TBD":
            return None
        resolved, issue = timestamp(value, active)
        if resolved is not None:
            return resolved
        if issue:
            gaps.append("Malformed source timestamp: " + str(value))
        gaps.append("Unresolved source timestamp: " + str(value))
        return None

    starts = [instant(row.get("start_datetime")) for row in restrictions] or [
        instant(notice.get("effective_datetime"))
    ]
    ends = [instant(row.get("end_datetime")) for row in restrictions] or [
        instant(notice.get("end_datetime"))
    ]
    start = starts[0] if len(set(starts)) == 1 else None
    end = ends[0] if len(set(ends)) == 1 else None
    if len(set(starts)) != 1 or len(set(ends)) != 1:
        gaps.append("Mixed effective intervals cannot be collapsed")
    helpers_usable = not semantic.get("execution_error") and not any(
        r["status"] == "ERROR" for r in input_observations
    )
    for name, result in semantic.get("helpers", []):
        if name in mapping["helper_values"] and not any(
            same(result, permitted) for permitted in mapping["helper_values"][name]
        ):
            helpers_usable = False
    body = notice.get("body_text") or ""
    facts = {
        "content_kind": content,
        "services": services,
        "availability": availability_value,
        "locations": locations,
        "quantities": quantities,
        "operational_assertions": [" ".join(body.split())],
        "start_time": start,
        "end_time": end,
        "time_basis": "UTC"
        if start and not any("timestamp" in gap or "interval" in gap for gap in gaps)
        else "UNRESOLVED",
    }
    facts["restrictions"] = [
        {
            "service": mapping["services"].get(row.get("service_type"), "UNKNOWN"),
            "availability": mapping["availability"].get(row.get("restriction_type"), "UNKNOWN"),
            "restriction_type": str(row.get("restriction_type") or "UNKNOWN"),
            "status": str(row.get("status") or "UNKNOWN"),
            "location_index": row.get("location_index"),
            "source_start": row.get("start_datetime"),
            "source_end": row.get("end_datetime"),
            "evidence_ref": reference,
        }
        for row in restrictions
    ]
    if len(availability) > 1:
        gaps.append("Mixed availability retained per restriction; scalar UNKNOWN")
    if "UNKNOWN" in availability or "UNKNOWN" in services:
        gaps.append("Unsupported restriction/service vocabulary retained as UNKNOWN")
    trace = []

    def explain(field, original, normalized, supplier, basis, unknown):
        trace.append(
            {
                "field": field,
                "source_basis": basis,
                "source_value": original,
                "normalized_value": normalized,
                "supplied_by": supplier,
                "unknown_handling": unknown,
            }
        )

    explain(
        "content_kind",
        {
            "information_only": notice.get("information_only"),
            "restriction_count": len(restrictions),
        },
        content,
        "model",
        "Captured notice.information_only and restrictions; validate against source.fields.body",
        "Missing content meaning stays UNKNOWN; information plus a known restriction is contradictory",
    )
    for key, original in (
        ("availability", [r.get("restriction_type") for r in restrictions]),
        ("services", [r.get("service_type") for r in restrictions]),
        ("restrictions", restrictions),
        ("locations", output.get("locations", [])),
        ("quantities", restrictions),
    ):
        explain(
            key,
            original,
            facts[key],
            "model",
            "Retained extraction rows and source.fields.body; deterministic canonical mapping",
            "Keep unrecognized values and row associations; no label, confidence or final-classification input",
        )
    explain(
        "restriction_status",
        notice.get("status"),
        notice.get("status"),
        "source_parser",
        "Notice Stat Desc header retained in notice.status",
        "Unrecognized status has no inferred lifecycle semantics",
    )
    explain(
        "source_time",
        {
            "effective_datetime": notice.get("effective_datetime"),
            "end_datetime": notice.get("end_datetime"),
            "restriction_intervals": [
                [r.get("start_datetime"), r.get("end_datetime")] for r in restrictions
            ],
        },
        {
            "start_time": start,
            "end_time": end,
            "time_basis": facts["time_basis"],
            "timezone_known": facts["time_basis"] == "UTC",
        },
        "normalizer",
        "Source-parser header strings plus model-extracted restriction intervals; only explicit offsets converted",
        "Naive/date-only strings and mixed intervals remain UNRESOLVED; no gas-day or timezone inference",
    )
    explain(
        "history",
        {"status": notice.get("status"), "prior_notice_id": notice.get("prior_notice_id")},
        {
            "prior_notice_id": notice.get("prior_notice_id"),
            "available_notice_ids": [h["notice"]["notice_id"] for h in history],
        },
        "retained_history",
        "Explicit source-parser prior header and supplied retained history",
        "Missing, unsupported or conflicting chain remains review; no ID-order inference",
    )
    value = {
        "version": 1,
        "normalization_trace": trace,
        "source": {
            "pipeline": "NGPL",
            "media_type": semantic.get("source_media_type", "text/html"),
            "sha256": source_sha256,
            "bytes_reference": "sha256:" + source_sha256,
            "fields": {
                "body": body,
                "effective_datetime": str(notice.get("effective_datetime")),
                "end_datetime": str(notice.get("end_datetime")),
                "retained_extraction": json.dumps(
                    {"locations": output.get("locations", []), "restrictions": restrictions},
                    sort_keys=True,
                ),
            },
        },
        "notice": {
            "notice_id": notice["notice_id"],
            "prior_notice_id": notice.get("prior_notice_id"),
            "status": notice["status"],
            "notice_type": notice["notice_type"],
        },
        "facts": facts,
        "history": history,
        "reference_time": reference_time,
        "evidence": {
            "extraction_usable": semantic["extraction_usable"],
            "helpers_usable": helpers_usable,
            "contradictory": False,
            "references": [reference],
        },
    }
    return value, sorted(set(gaps))
