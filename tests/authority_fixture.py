"""Disposable synthetic requirement promotion; never applied to repository policy."""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

from harness.requirement_trace import normative
from harness.runtime import ROOT, digest


def copy_requirement_authority(root: Path) -> None:
    # Preserve real ancestor approval objects, but copy only the authority data needed
    # by these tests. No historical model execution or application code is run.
    subprocess.run(
        ["git", "clone", "--shared", "--no-checkout", "--quiet", str(ROOT), str(root)], check=True
    )
    reference = json.loads((ROOT / "context/authority-reference.json").read_text())
    baseline = json.loads(
        (ROOT / "context/decisions/010-requirement-baseline.record.json").read_text()
    )
    names = set(reference["registered_context"]) | {
        "spec.md",
        "requirements/rule-block.schema.json",
        "requirements/normalized-witnesses.json",
        "requirements/compiled-build.json",
        "requirements/replay-expectations.json",
        "requirements/normalized-input.schema.json",
        "requirements/normalized-output.schema.json",
        "docs/system-contract.md",
        "requirements/requirement-revisions.json",
        baseline["source_requirements"],
        "context/temporal-approval.json",
        "context/assumptions.md",
        "context/assumptions-register.json",
        "context/authority-reference.json",
        *[
            str(p.relative_to(ROOT))
            for p in (ROOT / "context/approvals/011/files").rglob("*")
            if p.is_file()
        ],
        *json.loads((ROOT / "context/decisions/011-boundary-approval.json").read_text())[
            "approved_artifacts"
        ],
    }
    if (ROOT / "context/spec-read-pin.json").exists():
        names.add("context/spec-read-pin.json")
        pin = json.loads((ROOT / "context/spec-read-pin.json").read_text())
        if pin.get("review_record"):
            names.add(pin["review_record"]["path"])
    for name in names:
        target = root / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / name, target)


def promote(root: Path, row: dict) -> None:
    reference_path = root / "context/authority-reference.json"
    reference = json.loads(reference_path.read_text())
    registry_path = root / "requirements/requirement-revisions.json"
    registry = json.loads(registry_path.read_text())
    original = registry[row["id"]]
    revision = original["revision"] + 1
    record_name = "context/decisions/synthetic-requirement.record.json"
    decision = "context/decisions/synthetic-requirement.md"
    owner = "evidence/synthetic-owner.txt"
    (root / owner).write_text("SYNTHETIC UNIT FIXTURE approval only; never a real policy change.\n")
    (root / decision).write_text(
        "Status: owner-approved\n\n## "
        + row["id"]
        + "@"
        + str(revision)
        + "\n\n```json\n"
        + json.dumps(normative(row), indent=2)
        + "\n```\n"
    )
    record = {
        "kind": "synthetic-requirement-promotion",
        "status": "owner-approved",
        "supersedes": original["decision_record"],
        "decision": decision,
        "decision_sha256": digest(root / decision),
        "owner_record": owner,
        "owner_sha256": digest(root / owner),
        "approved_rows": {row["id"]: {"revision": revision, "normative": normative(row)}},
    }
    (root / record_name).write_text(json.dumps(record))
    for name, status in (
        (record_name, "owner-approved"),
        (decision, "owner-approved"),
        (owner, "owner-instruction"),
    ):
        reference["registered_context"][name] = {"status": status, "sha256": digest(root / name)}
    registry[row["id"]] = {
        **original,
        "revision": revision,
        "identity": row["id"] + "@" + str(revision),
        "decision_record": record_name,
    }
    registry_path.write_text(json.dumps(registry))
    reference["requirement_revisions_sha256"] = digest(registry_path)
    reference_path.write_text(json.dumps(reference))
