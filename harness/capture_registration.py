"""Register a finished live run of the inherited system as a scored capture.

    python -m harness register-capture evidence/legacy/<run>/results.json

This is an oracle change. It edits requirements/capture-registry.json,
requirements/trading-evidence.json and the trading-evidence hash in
context/authority-reference.json, all of which CODEOWNERS assigns to the owner.
Afterwards the gate scores the new capture next to the retained ones and lists every
labeled notice where the captures disagree. Gate 3 reports EVALUATOR_OR_ORACLE_CHANGED
until the owner registers a new reference.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from harness.runtime import ROOT, digest

REGISTRY = ROOT / "requirements/capture-registry.json"
TRADING = ROOT / "requirements/trading-evidence.json"
AUTHORITY = ROOT / "context/authority-reference.json"


def register(results: Path) -> dict:
    from harness.captures import verified_capture

    path = results.resolve()
    if not path.is_file() or not path.is_relative_to((ROOT / "evidence").resolve()):
        raise ValueError("A capture must be a results.json under evidence/")
    key = str(path.relative_to(ROOT.resolve()))
    data = json.loads(path.read_text())
    manifest = data.get("manifest", {})
    if manifest.get("system") != "inherited" or not manifest.get("provenance", {}).get("files"):
        raise ValueError("Not a live inherited run with provenance (make evaluate-inherited)")
    if (path.parent / "execution_error.json").exists():
        raise ValueError("The run recorded a HARNESS_FAILURE; it is not a complete capture")
    registry = json.loads(REGISTRY.read_text())
    trading = json.loads(TRADING.read_text())
    if key in registry["captures"] or key in trading["captures"]:
        raise ValueError("Capture already registered: " + key)
    originals = {p: p.read_text() for p in (REGISTRY, TRADING, AUTHORITY)}
    registry["captures"][key] = {
        "sha256": digest(path),
        "case_ids": [case["case_id"] for case in data["cases"]],
        "files": {
            str(p.relative_to(ROOT)): digest(p)
            for p in sorted(path.parent.rglob("*"))
            if p.is_file() and p != path
        },
    }
    trading["captures"].append(key)
    try:
        REGISTRY.write_text(json.dumps(registry, indent=2) + "\n")
        TRADING.write_text(json.dumps(trading, indent=2) + "\n")
        authority = json.loads(AUTHORITY.read_text())
        old = authority["trading_evidence_sha256"]
        AUTHORITY.write_text(originals[AUTHORITY].replace(old, digest(TRADING)))
        verified_capture(path)  # the same verification the gate performs
    except Exception:
        for file, text in originals.items():
            file.write_text(text)
        raise
    return {
        "registered": key,
        "cases": len(data["cases"]),
        "configured_model": manifest.get("configured_model"),
        "next": "Commit the run directory and these three files; run the gate. Gate 3 stays "
        "UNKNOWN (EVALUATOR_OR_ORACLE_CHANGED) until the owner registers a new reference.",
    }


def main() -> None:
    parser = argparse.ArgumentParser(prog="python -m harness register-capture", description=__doc__)
    parser.add_argument("results", type=Path)
    args = parser.parse_args()
    try:
        print(json.dumps(register(args.results), indent=2))
    except (ValueError, OSError, KeyError) as exc:
        print(json.dumps({"status": "ERROR", "reason": str(exc)}))
        raise SystemExit(2) from exc


if __name__ == "__main__":
    main()
