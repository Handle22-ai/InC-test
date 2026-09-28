"""Register a clean observed comparison reference without accepting unknown behavior."""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

from harness.runtime import ROOT, digest, write_json
from harness.temporal_authority import ancestor, committed_digest, git

POINTER = "evidence/current-baseline.json"


def require_observed_run(result: dict) -> None:
    """A comparison needs completed observations, not prior acceptance of them."""
    if (
        not result.get("cases")
        or not result.get("comparison_identity")
        or result.get("mode") not in {"REVIEWED_SPEC", "PROPOSAL_ONLY"}
        or any(
            result["gates"][key].get("classification") == "NOT_RUN"
            or result["gates"][key]["status"] == "ERROR"
            for key in ("1", "2")
        )
    ):
        raise ValueError(
            "INVALID_EVIDENCE_IDENTITY: reference requires completed non-refused observations; UNKNOWN/FAIL are retained, not accepted"
        )


def validate_source(root: Path, result: dict) -> None:
    source = result["source"]
    if source["working_tree_dirty"] or not ancestor(
        root, source["revision"], git(root, "rev-parse", "HEAD")
    ):
        raise ValueError("INVALID_EVIDENCE_IDENTITY: baseline must execute a clean ancestor commit")
    for name, sha in source["files"].items():
        if committed_digest(root, source["revision"], name) != sha:
            raise ValueError("INVALID_EVIDENCE_IDENTITY: baseline source does not match its commit")


def registered(root: Path) -> dict | None:
    pointer = root / POINTER
    if not pointer.exists():
        return None
    from harness.normalized_evaluation import verify_evidence

    record = json.loads(pointer.read_text())
    folder = (root / record["path"]).resolve()
    if not folder.is_relative_to((root / "evidence").resolve()):
        raise ValueError("INVALID_EVIDENCE_IDENTITY: unsafe comparison reference")
    if record["role"] != "observed-comparison-reference-not-release-acceptance":
        raise ValueError("INVALID_EVIDENCE_IDENTITY: comparison reference cannot grant acceptance")
    for name in ("results.json", "manifest.json"):
        if digest(folder / name) != record["sha256"][name]:
            raise ValueError("INVALID_EVIDENCE_IDENTITY: comparison reference bytes changed")
    verify_evidence(folder, json.loads((folder / "manifest.json").read_text()))
    result = json.loads((folder / "results.json").read_text())
    validate_source(root, result)
    if record.get("version") == 2:
        require_observed_run(result)
    elif result["gates"]["1"]["status"] != "PASS":
        raise ValueError("INVALID_EVIDENCE_IDENTITY: legacy reference contracts did not pass")
    return {**result, "registration": record}


def copy_evidence(source: Path, target: Path) -> None:
    from harness.normalized_evaluation import verify_evidence

    manifest = json.loads((source / "manifest.json").read_text())
    verify_evidence(source, manifest)
    target.mkdir(parents=True, exist_ok=False)
    for name in set(manifest["files"]) | {"results.json", "manifest.json"}:
        destination = target / name
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source / name, destination)


def owners(root: Path = ROOT) -> list[str]:
    """Owners of the spec the owner last reread (see spec_ownership.owners_as_of)."""
    from harness.spec_compiler import compile_spec
    from harness.spec_ownership import PIN, owners_as_of

    pin = json.loads((root / PIN).read_text()) if (root / PIN).exists() else {}
    return owners_as_of(root, pin.get("spec_sha256"), compile_spec(root))


def require_owner(person: str, root: Path = ROOT) -> None:
    listed = owners(root)
    if listed and person not in listed:
        raise ValueError(f"{person!r} is not a spec owner (spec-settings owners: {listed})")


def register(source: Path, destination: Path, person: str) -> dict:
    """Register a reference as a named owner, recording the evaluator/oracle files accepted.

    This is still an assertion by whoever runs it, not authentication; CODEOWNERS
    review of evidence/current-baseline.json is what makes it an owner action.
    """
    require_owner(person)
    result = json.loads((source / "results.json").read_text())
    validate_source(ROOT, result)
    require_observed_run(result)
    gate3 = result["gates"].get("3", {})
    if result["comparison_identity"]["spec_sha256"] != digest(ROOT / "spec.md"):
        raise ValueError(
            "Reference spec differs from current spec; no automatic comparison mapping"
        )
    copy_evidence(source, destination)
    record = {
        "version": 2,
        "role": "observed-comparison-reference-not-release-acceptance",
        "path": str(destination.relative_to(ROOT)),
        "source_commit": result["source"]["revision"],
        "spec_sha256": result["comparison_identity"]["spec_sha256"],
        "human_review_asserted": False,
        "registered_by": person,
        "accepted_changes": {
            key: files
            for key, files in gate3.get("changed_files", {}).items()
            if key in {"evaluator", "oracle"}
        },
        "unmeasured_policy_edits": [
            edit["declaration"]
            for edit in result.get("spec_edits_since_reference", [])
            if edit["unmeasured"]
        ],
        "previous_reference_classification": gate3.get("classification"),
        "sha256": {name: digest(destination / name) for name in ("results.json", "manifest.json")},
        "observed_gates": {key: value["status"] for key, value in result["gates"].items()},
        "accepted": False,
        "meaning": "Observation only. UNKNOWN/FAIL remain in their original gates. Registration never asserts human review, policy approval or acceptance.",
    }
    write_json(ROOT / POINTER, record)
    return record


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="python -m harness register-reference", description=register.__doc__
    )
    parser.add_argument("source", type=Path)
    parser.add_argument("destination", type=Path)
    parser.add_argument("--person", required=True, help="A spec owner, as in spec-settings owners")
    args = parser.parse_args()
    print(
        json.dumps(
            register(args.source.resolve(), args.destination.resolve(), args.person), indent=2
        )
    )


if __name__ == "__main__":
    main()
