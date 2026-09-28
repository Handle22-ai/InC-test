"""Gate-time probes of every declared parser field and date format."""

from __future__ import annotations

from pathlib import Path

from harness.runtime import ROOT, digest, write_json
from rebuilt.source_input import HEADER_LABELS, READ_FIELDS, parse_field, parse_html, timestamp


def run(contract: dict, destination: Path) -> dict:
    results = []
    bad = {
        "text": 17,
        "identifier": "12x",
        "integer": True,
        "number": -1,
        "flag": "yes",
        "boolean": 1,
        "rows": [17],
        "helper_pairs": [["name"]],
        "text_or_integer": [],
        "timestamp": "02/30/2026",
    }
    good = {
        "text": "retained",
        "identifier": "46624",
        "integer": 1,
        "number": 0.5,
        "flag": False,
        "boolean": True,
        "rows": [],
        "helper_pairs": [["name", True]],
        "text_or_integer": "24",
        "timestamp": "01/14/2026 12:00:00PM",
    }
    for row in contract["input_contract"]:
        observations = {
            name: parse_field(row, value, contract)
            for name, value in [
                ("valid", good[row["Type"]]),
                ("missing", None),
                ("malformed", bad[row["Type"]]),
            ]
        }
        valid = (
            observations["valid"]["status"] != "ERROR"
            and observations["malformed"]["status"] == "ERROR"
            and observations["missing"]["status"]
            == ("ERROR" if row["Missing"] == "ERROR" else "UNKNOWN")
        )
        results.append(
            {
                "id": row["ID"],
                "spec_line": row["_line"],
                "field": row["Field"],
                "status": "PASS" if valid else "FAIL",
                "observations": observations,
            }
        )
    dates = [
        "01/14/2026 12:00:00PM",
        "01/14/2026 12:00:00 PM",
        "01/14/2026",
        "2026-01-14",
        "2026-01-14T12:00:00",
        "2026-01-14T12:00:00+00:00",
    ]
    date_checks = [
        {"raw": v, "utc": timestamp(v, contract)[0], "issue": timestamp(v, contract)[1]}
        for v in dates
    ]
    inventory = {
        r["Field"].removeprefix("header.")
        for r in contract["input_contract"]
        if r["Field"].startswith("header.")
    }
    captures = []
    for path in sorted((ROOT / "inherited/evaluation/notices").glob("*.html")):
        parsed = parse_html(path.read_text(), {}, contract)
        captures.append({"path": str(path.relative_to(ROOT)), "sha256": digest(path), **parsed})
    ambiguous = [
        {"raw": raw, "formats": readings}
        for raw in [*dates, "03/04/2026 12:00:00PM", "03/04/2026"]
        + [
            field["raw"]
            for capture in captures
            for field in capture["fields"]
            if field["raw"] and "date" in field["field"]
        ]
        if len(readings := matching_formats(raw, contract["date_formats"])) > 1
    ]
    unlabeled = unlabeled_samples(contract)
    result = {
        "status": "PASS"
        if all(r["status"] == "PASS" for r in results)
        and all(p["status"] != "ERROR" for p in captures)
        and {r["Field"] for r in contract["input_contract"]} == READ_FIELDS
        and inventory == set(HEADER_LABELS)
        and all(r["issue"] is None for r in date_checks)
        and not ambiguous
        else "FAIL",
        "fields": results,
        "date_formats": date_checks,
        "source_inventory_complete": {r["Field"] for r in contract["input_contract"]}
        == READ_FIELDS,
        "header_inventory_complete": inventory == set(HEADER_LABELS),
        "captured_headers": captures,
        "ambiguous_dates": ambiguous,
        "unlabeled_samples": unlabeled,
        "scope": "Bounded parser contract and retained raw fields; not extraction accuracy or inherited parser acceptance",
        "inherited_known_conflicts": [
            "Malformed ID digits are stripped; missing status defaults INITIATE; post time can use download/wall clock. These remain inherited failures, never the input contract."
        ],
    }
    findings = []
    for row in results:
        if row["status"] != "PASS":
            findings.append(
                {
                    "gate": 1,
                    "status": "ERROR",
                    "code": "INPUT_CONTRACT_MISMATCH",
                    "row": row["id"],
                    "spec_line": row["spec_line"],
                    "field": row["field"],
                    "reason": f"spec.md:{row['spec_line']}: block spec-inputs, row {row['id']}: parser contradicts {row['field']}; observations: {row['observations']}",
                }
            )
    for row in date_checks:
        if row["issue"] is not None:
            findings.append(
                {
                    "gate": 1,
                    "status": "ERROR",
                    "code": "INPUT_DATE_FORMAT_MISMATCH",
                    "row": "INPUT-TIME-001",
                    "reason": f"spec.md:{contract['input_time_line']}: block spec-settings, row INPUT-TIME-001: date {row['raw']!r}: {row['issue']}; declared formats: {contract['date_formats']}",
                }
            )
    for row in ambiguous:
        findings.append(
            {
                "gate": 1,
                "status": "ERROR",
                "code": "INPUT_DATE_FORMAT_AMBIGUOUS",
                "row": "INPUT-TIME-001",
                "reason": f"spec.md:{contract['input_time_line']}: block spec-settings, row INPUT-TIME-001: date {row['raw']!r} parses under more than one declared format {row['formats']} with different meanings",
            }
        )
    for row in unlabeled["html_contract_errors"]:
        findings.append(
            {
                "gate": 1,
                "status": "ERROR",
                "code": "UNLABELED_INPUT_CONTRACT_MISMATCH",
                "source_capture": row["path"],
                "reason": f"spec.md: block spec-inputs: recent unlabeled notice {row['path']} violates the input contract in {row['errors']}",
            }
        )
    for capture in captures:
        for field in capture["fields"]:
            if field["status"] != "ERROR":
                continue
            findings.append(
                {
                    "gate": 1,
                    "status": "ERROR",
                    "code": "CAPTURED_INPUT_CONTRACT_MISMATCH",
                    "row": field["id"],
                    "spec_line": field["spec_line"],
                    "field": field["field"],
                    "source_capture": capture["path"],
                    "reason": f"spec.md:{field['spec_line']}: block spec-inputs, row {field['id']}: notice {capture['path']}, field {field['field']}, raw {field['raw']!r}: {field['issue']}",
                }
            )
    if not result["source_inventory_complete"] or not result["header_inventory_complete"]:
        findings.append(
            {
                "gate": 1,
                "status": "ERROR",
                "code": "INPUT_FIELD_INVENTORY_MISMATCH",
                "reason": "spec.md: block spec-inputs: parser field inventory differs from declared source fields",
            }
        )
    result["findings"] = findings
    write_json(destination, result)
    return result


def matching_formats(raw: str, formats: list[str]) -> list[str]:
    """Declared formats that read raw, when they disagree about the instant."""
    from datetime import datetime

    readings = {}
    for form in formats:
        try:
            value = (
                datetime.fromisoformat(raw) if form == "ISO8601" else datetime.strptime(raw, form)
            )
        except ValueError:
            continue
        readings[form] = value
    return list(readings) if len(set(readings.values())) > 1 else []


def unlabeled_samples(contract: dict) -> dict:
    """Recent unlabeled NGPL notices: header contract and format support only, no model run."""
    folder = ROOT / "inherited/samples/notices"
    html, other = [], []
    for path in sorted(folder.glob("*")):
        if path.suffix == ".html":
            parsed = parse_html(path.read_text(), {}, contract)
            html.append(
                {
                    "path": str(path.relative_to(ROOT)),
                    "status": parsed["status"],
                    "errors": [f["field"] for f in parsed["fields"] if f["status"] == "ERROR"],
                }
            )
        elif path.suffix == ".pdf":
            supported = "application/pdf" in contract["formats"]["supported"]
            other.append({"path": str(path.relative_to(ROOT)), "supported": supported})
    return {
        "html_notices": len(html),
        "html_contract_errors": [row for row in html if row["errors"]],
        "pdf_notices": len(other),
        "pdf_unsupported": sum(not row["supported"] for row in other),
        "scope": "Header input contract and format support only. Classification needs live "
        "extraction, which this offline gate never runs; no label exists for these notices.",
    }
