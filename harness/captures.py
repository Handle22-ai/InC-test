"""Read-only verification of explicitly registered evidence and versioned oracle bytes."""

from __future__ import annotations

import copy
import json
from pathlib import Path

from harness.runtime import ROOT, digest


def registry() -> dict:
    return json.loads((ROOT / "requirements/capture-registry.json").read_text())


def oracle() -> dict[int, dict]:
    record = registry()
    for key in ("oracle", "field_support"):
        item = record[key]
        if digest(ROOT / item["path"]) != item["sha256"]:
            raise ValueError(f"{key} identity changed; explicit review required")
    return {
        r["notice_id"]: r
        for r in json.loads((ROOT / record["oracle"]["path"]).read_text())["cases"]
    }


def verified_capture(path: Path) -> dict:
    path = path.resolve()
    try:
        key = str(path.relative_to(ROOT.resolve()))
    except ValueError as exc:
        raise ValueError("Capture outside registered checkout") from exc
    entry = registry()["captures"].get(key)
    if entry is None:
        raise ValueError("Unregistered capture; verification cannot approve or repin new evidence")
    if digest(path) != entry["sha256"]:
        raise ValueError("Capture identity mismatch")
    for name, sha in entry["files"].items():
        p = ROOT / name
        if not p.resolve().is_relative_to(ROOT.resolve()) or not p.is_file() or digest(p) != sha:
            raise ValueError("Referenced evidence bytes changed: " + name)
    data = json.loads(path.read_text())
    cases = data["cases"]
    ids = [c["case_id"] for c in cases]
    if len(ids) != len(set(ids)) or ids != entry["case_ids"]:
        raise ValueError("Required capture case inventory differs")
    labels = oracle()
    if "manifest" in data:
        if not data["manifest"].get("provenance", {}).get("files"):
            raise ValueError("Required capture provenance missing")
        labeled = [c for c in cases if c.get("category") == "labeled"]
        if {c["notice_id"] for c in labeled} != set(labels):
            raise ValueError("Required labeled case inventory incomplete")
        for c in cases:
            if not c.get("input_sha256") or digest(ROOT / c["input"]) != c["input_sha256"]:
                raise ValueError("Captured source identity mismatch")
            if c.get("category") == "labeled" and c.get("annotations") != labels[c["notice_id"]]:
                raise ValueError("Captured annotation differs from authoritative oracle")
    return data


def with_oracle(cases: list[dict]) -> list[dict]:
    """Scoring reads expected answers from the oracle, never from mutable observations."""
    labels = oracle()
    result = copy.deepcopy(cases)
    support = json.loads((ROOT / "requirements/oracle-support.json").read_text())
    for c in result:
        if c.get("category") == "labeled":
            if c["notice_id"] not in labels:
                raise ValueError("No authoritative label for this input")
            c["annotations"] = copy.deepcopy(labels[c["notice_id"]])
        elif c.get("category") == "field_mutation":
            c["annotations"] = {
                "fields": {
                    e["field"]: e["expected"]
                    for e in support["fields"]
                    if e["notice_id"] == c["notice_id"] and e["input_sha256"] == c["input_sha256"]
                }
            }
    return result


def verify_report_source(path: Path, requirements: list[dict]) -> dict:
    """A derived report must retain verified observations and reproducible verdicts."""
    key = str(path.resolve().relative_to(ROOT.resolve()))
    if key in registry()["captures"]:
        return verified_capture(path)
    data = json.loads(path.read_text())
    manifest = data.get("manifest", {})
    source = manifest.get("source_capture")
    if manifest.get("execution_identity") != "captured_output_evaluation" or not source:
        raise ValueError("Unregistered report input; explicit evidence review required")
    original = verified_capture(ROOT / source["path"])
    if digest(ROOT / source["path"]) != source["sha256"] or data["cases"] != with_oracle(
        original["cases"]
    ):
        raise ValueError("Derived observations differ from verified source capture")
    from harness.gates import evaluate

    recomputed = evaluate(requirements, data["cases"], manifest)
    stored = [f for f in data["findings"] if f["requirement_id"] != "OBS-003"]
    if recomputed != stored:
        raise ValueError("Stored verdicts differ from recomputed current checks")
    regression = [f for f in data["findings"] if f["requirement_id"] == "OBS-003"]
    if len(regression) != 1 or regression[0]["status"] != "UNKNOWN":
        raise ValueError("Unverified temporal verdict in frozen-output policy evaluation")
    return data


def evaluation_clock(case: dict, capture: dict) -> tuple[str, str]:
    """Score a labeled notice as of its own posting, never against today (spec D3-011).

    The post time is naive in an unknown timezone. It is rendered with +00:00 only
    as the evaluation reference; spec.md's time.ended_in_any_timezone compares it
    with naive source ends from the same notice plus a margin covering every UTC
    offset, so no timezone is inferred.
    """
    from datetime import datetime

    posted = case.get("output", {}).get("notice", {}).get("post_datetime")
    try:
        naive = datetime.fromisoformat(posted)
        if naive.tzinfo is None:
            return naive.isoformat() + "+00:00", "notice post_datetime"
    except TypeError, ValueError:
        pass
    return capture["manifest"]["provenance"]["timestamp"], "capture execution time (no post time)"
