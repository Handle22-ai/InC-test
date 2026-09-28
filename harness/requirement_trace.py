"""Exact per-requirement approval lineage; hashes alone never promote wording."""

from __future__ import annotations

import json
import re
from pathlib import Path

import yaml

from harness.context_integrity import approved_record
from harness.runtime import digest

# Observational availability belongs to a component, not to normative intent.
OBSERVATIONAL = {"implementation_status", "check_status", "demonstrated_evidence", "policy_id"}


def normative(row: dict) -> dict:
    return {key: value for key, value in row.items() if key not in OBSERVATIONAL}


def verify(rows: list[dict], reference: dict, root: Path) -> None:
    try:
        path = root / "requirements/requirement-revisions.json"
        if digest(path) != reference.get("requirement_revisions_sha256"):
            raise ValueError("unregistered requirement revision registry")
        registry = json.loads(path.read_text())
        records = {}
        sources = {}

        def decision(name):
            if name not in records:
                records[name] = approved_record(root, reference, name)
            return records[name]

        binding = {row["id"] for row in rows if row["enforcement"] == "binding"}
        if not binding <= registry.keys():
            raise ValueError("binding requirement has no approved revision")
        for row in rows:
            if row["id"] not in registry:
                continue
            item = registry[row["id"]]
            record = decision(item["decision_record"])
            approved = record["approved_rows"][row["id"]]
            if approved["normative"] != normative(row):
                raise ValueError(row["id"] + " exact normative body differs from approved decision")
            if item["revision"] != approved["revision"] or item["identity"] != row[
                "id"
            ] + "@" + str(item["revision"]):
                raise ValueError("requirement revision identity mismatch")
            visited = set()
            while record.get("supersedes"):
                if record["supersedes"] in visited:
                    raise ValueError("cyclic requirement decision lineage")
                visited.add(record["supersedes"])
                previous = decision(record["supersedes"])
                older = previous["approved_rows"][row["id"]]
                newer = record["approved_rows"][row["id"]]
                if newer["revision"] <= older["revision"]:
                    raise ValueError("new requirement revision must advance")
                if (
                    record["decision"] == previous["decision"]
                    or record["owner_record"] == previous["owner_record"]
                ):
                    raise ValueError(
                        "changed requirement needs a new approved decision and owner record"
                    )
                text = re.sub(
                    r"<!--.*?-->", "", (root / record["decision"]).read_text(), flags=re.S
                )
                heading = re.escape(row["id"] + "@" + str(newer["revision"]))
                bodies = re.findall(
                    r"^## " + heading + r"\n\n```json\n(.*?)\n```", text, re.M | re.S
                )
                if (
                    len(bodies) != 1
                    or json.loads(bodies[0]) != newer["normative"]
                    or not re.search(r"^Status: owner-approved$", text, re.M)
                ):
                    raise ValueError("exact new requirement text absent from approved decision")
                record = previous
            if (
                record.get("kind") != "unchanged-requirement-baseline"
                or record.get("source_commit") != registry[row["id"]]["baseline_commit"]
            ):
                raise ValueError("registered original requirement identity missing")
            source = root / record["source_requirements"]
            if digest(source) != record["source_requirements_sha256"]:
                raise ValueError("historical requirement source changed")
            if source not in sources:
                sources[source] = {
                    item["id"]: item for item in yaml.safe_load(source.read_text())["requirements"]
                }
            original = sources[source][row["id"]]
            if normative(original) != record["approved_rows"][row["id"]]["normative"]:
                raise ValueError("baseline approval body does not match original normative text")
    except (ValueError, KeyError, OSError, TypeError) as exc:
        raise ValueError("UNAPPROVED_REQUIREMENT_CHANGE: " + str(exc)) from exc
