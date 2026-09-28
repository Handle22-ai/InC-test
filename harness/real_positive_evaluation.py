"""Source-supported positive witnesses independent of binary capture verdicts."""

from __future__ import annotations

import json
from pathlib import Path

from harness.runtime import ROOT, digest, write_json


def run(trading: dict, destination: Path) -> dict:
    witnesses = json.loads((ROOT / "requirements/real-positive-witnesses.json").read_text())
    observations = {row["id"]: row for row in trading["observations"]}
    records = []
    for witness in witnesses:
        capture_index = next(
            i for i, source in enumerate(trading["sources"]) if source["path"] == witness["capture"]
        )
        observed = observations[f"capture-{capture_index}/{witness['case_id']}"]
        decision = observed["decision"]
        value = decision.get("normalized_input", {})
        actual = {
            "classification": decision["classification"],
            "recommendation_allowed": decision.get("recommendation_allowed"),
            "time_basis": value.get("facts", {}).get("time_basis"),
            "publication_disposition": decision.get("publication_disposition"),
            "initial_decision": decision["initial_decision"],
        }
        source_supported = digest(ROOT / witness["source_path"]) == witness[
            "source_sha256"
        ] and witness["source_quote"] in value.get("source", {}).get("fields", {}).get("body", "")
        expected = dict(witness["expected"])
        record = {
            "id": witness["id"],
            "status": "PASS" if source_supported and actual == expected else "FAIL",
            "source": {
                "path": witness["source_path"],
                "sha256": witness["source_sha256"],
                "capture": witness["capture"],
                "quote": witness["source_quote"],
                "verified": source_supported,
            },
            "normalized": value,
            "expected": expected,
            "expected_basis": "Unchanged frozen source-grounded witness; TZ-NGPL-002 separates classification from time actionability",
            "observed": actual,
            "decision": decision["classifier_decision"],
            "actionability": decision.get("actionability"),
            "publication_reason": decision.get("publication_reason"),
            "basis": witness["basis"],
        }
        records.append(record)
    result = {
        "status": "PASS" if all(r["status"] == "PASS" for r in records) else "FAIL",
        "witnesses": records,
        "scope": "Existing source facts to normalized candidate; no synthetic timezone, new extraction, materiality or publication approval",
    }
    write_json(destination, result)
    return result
