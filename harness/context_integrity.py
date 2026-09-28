"""Exact assumption/index registration and explicitly non-authoritative learning."""

from __future__ import annotations

import json
import re
from pathlib import Path

from harness.runtime import digest


def approved_record(root: Path, reference: dict, name: str) -> dict:
    path = (root / name).resolve()
    entry = reference["registered_context"].get(name, {})
    if (
        not path.is_relative_to(root.resolve())
        or not path.is_file()
        or entry.get("status") != "owner-approved"
        or digest(path) != entry.get("sha256")
    ):
        raise ValueError("UNAPPROVED_CONTEXT_CHANGE: missing/stale approved decision " + name)
    record = json.loads(path.read_text())
    if record.get("status") != "owner-approved":
        raise ValueError("UNAPPROVED_CONTEXT_CHANGE: record is not owner-approved")
    for key, status in (("decision", "owner-approved"), ("owner_record", "owner-instruction")):
        source = record.get(key)
        registration = reference["registered_context"].get(source, {})
        source_path = (root / source).resolve() if isinstance(source, str) else root
        if (
            not source_path.is_relative_to(root.resolve())
            or not source_path.is_file()
            or registration.get("status") != status
            or digest(source_path) != registration.get("sha256")
        ):
            raise ValueError("UNAPPROVED_CONTEXT_CHANGE: missing matching decision/owner record")
    return record


def verify_assumptions(root: Path, reference: dict) -> None:
    path = root / "context/assumptions.md"
    register = json.loads((root / "context/assumptions-register.json").read_text())
    parsed = re.findall(r"^\| (A-\d{3}) \| ([^|]+) \| ([^|]+) \|$", path.read_text(), re.M)
    rows = {key: (text, remaining) for key, text, remaining in parsed}
    ids = {f"A-{number:03}" for number in range(1, 9)}
    if set(rows) != ids or len(parsed) != 8 or set(register) != ids:
        raise ValueError("UNAPPROVED_ASSUMPTION_CHANGE: incomplete/duplicate A-001..A-008")
    for key, row in register.items():
        record = approved_record(root, reference, row["approval_decision"])
        body = {k: v for k, v in row.items() if k != "approval_decision"}
        if body != record.get("approved_body", {}).get(key):
            raise ValueError(
                "UNAPPROVED_ASSUMPTION_CHANGE: "
                + key
                + " needs an exact matching approved body/status/basis"
            )
        if rows[key] != (row["normative_text"], row["remaining_limit"]):
            raise ValueError(
                "UNAPPROVED_ASSUMPTION_CHANGE: " + key + " differs from its approved text"
            )
        if row["status"] != "owner-approved-bounded":
            raise ValueError(
                "UNAPPROVED_ASSUMPTION_CHANGE: " + key + " is not approved for current use"
            )
    if digest(path) != reference.get("assumptions_view_sha256"):
        raise ValueError("UNAPPROVED_ASSUMPTION_CHANGE: unregistered text outside assumption rows")
    from harness.temporal_authority import record_precedes

    for row in register.values():
        record_precedes(
            root,
            row["approval_decision"],
            ("context/assumptions.md", "context/assumptions-register.json"),
        )


def verify_manifest(root: Path, manifest_path: Path, manifest: dict, reference: dict) -> None:
    registration = reference.get("authoritative_manifest", {})
    if digest(manifest_path) != registration.get("sha256"):
        raise ValueError("UNAPPROVED_MANIFEST_CHANGE: reviewed manifest/index update required")
    record = approved_record(root, reference, registration["review_record"])
    if record.get("manifest_sha256") != digest(manifest_path):
        raise ValueError("UNAPPROVED_MANIFEST_CHANGE: re-pin lacks matching reviewed index record")
    core = {
        key: value.get("core_content_paths") for key, value in manifest["task_profiles"].items()
    }
    if record.get("core_content_paths") != core:
        raise ValueError("UNAPPROVED_MANIFEST_CHANGE: core selection differs from approved index")
    from harness.temporal_authority import record_precedes

    record_precedes(root, registration["review_record"], (str(manifest_path.relative_to(root)),))


def pending_learning(root: Path) -> list[dict]:
    result = []
    for path in sorted((root / "context/pending-learning").glob("*.md")):
        if not path.resolve().is_relative_to(root.resolve()):
            raise ValueError("Unsafe pending learning path")
        text = path.read_text()
        result.append(
            {
                "path": str(path.relative_to(root)),
                "sha256": digest(path),
                "status": "unapproved-proposal",
                "authoritative": False,
                "content": text[:32000],
                "truncated": len(text) > 32000,
                "promotion": "Requires an explicit reviewed manifest/index decision; file wording is not approval",
            }
        )
    return result
