"""Explicit manifest task profiles; selection never changes requirement authority."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

import yaml

from harness.behavior_contract import load as load_behavior_contract
from harness.context_integrity import pending_learning
from harness.requirements import load_requirements
from harness.runtime import ROOT, digest, new_run, write_json


def review_status() -> dict:
    """The owner's read receipt for the current spec bytes, or why there is none."""
    from harness.spec_ownership import verify

    try:
        return verify(ROOT)
    except ValueError as exc:
        return {"reviewed": False, "status": "REVIEW_PENDING", "reason": str(exc)}


def select(task: str, manifest_path: Path = ROOT / "context/manifest.yaml") -> dict:
    from harness.spec_ownership import proposal_scope

    review = review_status()
    with proposal_scope(ROOT):
        package = _select(task, manifest_path)
    review["edits_since_reread"] = edits_since_reread()
    package["spec_review"] = review
    return package


def _select(task: str, manifest_path: Path = ROOT / "context/manifest.yaml") -> dict:
    manifest = yaml.safe_load(manifest_path.read_text())
    contract = load_behavior_contract()
    profiles = manifest["task_profiles"]
    if task not in profiles:
        raise ValueError(f"Unknown task {task!r}; choose one of {sorted(profiles)}")
    profile = profiles[task]
    by_id = {row["id"]: row for row in load_requirements()}
    ids = dict.fromkeys(
        profile["binding_requirements"]
        + profile["specified_only_requirements"]
        + profile.get("related_requirements", [])
    )
    rows: list[dict] = [
        {
            "role": "specified_only"
            if by_id[key]["validation"]["check"] == "out_of_scope"
            else "binding",
            "why": profile["requirement_reason"],
            **by_id[key],
        }
        for key in ids
    ]
    for row in rows:
        rules = [
            rule["id"]
            for rule in contract["rules"]
            if row["id"] in rule["requirements"] and rule["status"] != "pending-owner"
        ]
        steps = [
            step["id"]
            for step in contract["state_safety"]["steps"]
            if step.get("requirement") == row["id"]
            or any(
                contract["state_safety"]["relations"][relation].get("requirement") == row["id"]
                for relation in step["expected"]
            )
        ]
        row["component_availability"] = {
            "full_requirement_row": {
                "implementation": row["implementation_status"],
                "check": row["check_status"],
            },
            "normalized_boundary": {
                "implementation": "partial" if rules else "not_established",
                "check": "executable_scoped" if rules else "not_available",
                "rule_ids": rules,
                "scope": "Accepted normalized facts only; no raw extraction or full lifecycle claim",
            },
            "stateful_publisher": {
                "implementation": "partial" if steps else "not_established",
                "check": "executable_scoped" if steps else "not_available",
                "steps": steps,
                "scope": "Initial reservation/replay and refusal controls; no delivery or full lifecycle claim",
            },
        }
    artifacts = []
    for name in (
        "spec.md",
        "requirements/behavior.yaml",
        "requirements/rule-block.schema.json",
        "docs/system-contract.md",
        "docs/signal-contract.md",
        "harness.md",
    ):
        path = ROOT / name
        full = path.read_text()
        if name == "spec.md":
            from harness.spec_compiler import blocks

            selected = blocks(full)
            content = "## Rule block\n\n```\n" + "\n".join(selected["spec-rules"][1]) + "\n```\n"
            if "### Closed vocabulary and refusal boundary" in full:
                content += full.split("### Closed vocabulary and refusal boundary", 1)[1].split(
                    "## Interface fields", 1
                )[0]
            content += (
                "\n## Parameters\n\n```\n"
                + "\n".join(selected.get("spec-parameters", (0, []))[1])
                + "\n```\n"
            )
            selection = "Exact rules, input vocabulary/refusal boundary and parameters. Read spec.md for full normative requirements and D sentences."
        else:
            content, selection = "", "Hashed reference; read when the task needs this source"
        artifacts.append(
            {
                "path": name,
                "status": "sole-authority"
                if name == "spec.md"
                else "derived-or-check-implementation",
                "why": "Spec-source architecture: historical ADRs are not competing active policy",
                "sha256": digest(path),
                "configured_include_content": bool(content),
                "include_content": bool(content),
                "content_state": "selected-excerpts"
                if name == "spec.md"
                else "embedded"
                if content
                else "reference-only",
                "selection": selection,
                "content": content or None,
            }
        )
    return {
        "task": task,
        "approval_boundary": "Local reference checks byte/status consistency only. Owner must compare exact proposed changes against the original conversation outside the worker checkout before promotion. No authenticated or protected in-repository approval service.",
        "learning_selection": "Spec is the sole policy authority. Pending learning is automatically surfaced as unapproved evidence/proposals and cannot promote itself.",
        "pending_learning": pending_learning(ROOT),
        "manifest_sha256": digest(manifest_path),
        "policy_id": next(iter(by_id.values()))["policy_id"],
        "authority": "spec.md is the sole editable policy; generated requirements are consequences; external required spec review controls approval",
        "requirements": rows,
        "approved_policies": yaml.safe_load((ROOT / "requirements/requirements.yaml").read_text())[
            "policies"
        ]
        if "core_content_paths" in profile
        else {},
        "artifacts": artifacts,
        "source_scope": profile["source_scope"],
        "required_gates": manifest["required_gates"],
        "checks": [
            {"requirement": r["id"], "validation": r["validation"]}
            for r in rows
            if r["role"] == "binding"
        ],
        "excluded_context": manifest["excluded_context"],
        "known_failures": known_failures(),
        "decisions": [
            {k: v for k, v in row.items() if k != "_line"} for row in contract["decisions"]
        ],
        "assumptions": spec_section("## Assessment assumptions", "## Requirements"),
        "instructions": "Use a proposal copy of spec.md and make consequences first. Check losses as well as improvements. Compile after adopting an authorized edit. A human reread is separate and must not be invented. No live model calls.",
    }


def edits_since_reread(root: Path = ROOT) -> list[str]:
    """Declarations changed since the spec an owner last reread (audit 5 #13).

    An agent reads the package as its context; unreviewed declarations must not look like
    policy. The package is still written: a session may need context before the reread.
    """
    from harness.proposals import declaration_changes
    from harness.spec_ownership import PIN, spec_text_with_hash

    try:
        reread = json.loads((root / PIN).read_text()).get("spec_sha256")
    except OSError, ValueError:
        reread = None
    old = spec_text_with_hash(root, reread) if reread else None
    if old is None:
        return ["(no reread spec found in the working file or git history)"]
    text = (root / "spec.md").read_text()
    return [f"{c['block']} / {c['id']} ({c['change']})" for c in declaration_changes(old, text)]


def spec_section(start: str, end: str) -> str:
    text = (ROOT / "spec.md").read_text()
    return text[text.index(start) : text.index(end)].strip()


def known_failures() -> list[str]:
    """Labeled misses, false positives and capture disagreements from the published run."""
    path = ROOT / "evidence/run-20260928/results.json"
    if not path.exists():
        return ["No published run; run make gate and read CURRENT.md."]
    trading = json.loads(path.read_text()).get("trading_layer", {})
    rows = [
        f"{o['id']}: labeled {'signal' if o['label'] else 'no signal'}, rebuilt "
        f"{o['classification']} ({o['rule']})"
        for o in trading.get("label_outcomes", [])
        if (o["label"] and o["classification"] != "SIGNAL_CANDIDATE")
        or (o["label"] is False and o["classification"] == "SIGNAL_CANDIDATE")
    ]
    rows += [
        f"notice {d['notice_id']}: inherited runs disagree across captures"
        for d in trading.get("capture_differences", [])
    ]
    return rows or ["None in the published run."]


def write_package(task: str, destination: Path) -> dict:
    package = select(task)
    destination.mkdir(parents=True, exist_ok=True)
    if any((destination / name).exists() for name in ("package.json", "package.md")):
        raise FileExistsError("Context packages are append-only; choose a fresh output directory")
    write_json(destination / "package.json", package)
    review = package["spec_review"]
    lines = [f"# Selected task: {task}", ""]
    if review.get("status") == "REVIEW_PENDING":
        lines += [
            f"**SPEC UNREVIEWED.** {review.get('reason', '').rstrip('.')}. These declarations have no owner "
            "approval yet; treat them as proposals, not requirements, and do not build on them:",
            "",
            *[f"- {edit}" for edit in review["edits_since_reread"]],
            "",
        ]
    lines += [
        package["authority"],
        "",
        package["instructions"],
        "",
        "## Requirements and derived checks",
        "",
        "Complete selected requirement rows, including preconditions, component availability and validation parameters, are in package.json. This table is a reading index, not a substitute contract.",
        "",
        "| Requirement | Role | Title | Declared check |",
        "|---|---|---|---|",
    ]

    def clean(value):
        return re.sub(r"\s+", " ", str(value)).replace("|", "\\|")

    for row in package["requirements"]:
        lines.append(
            f"| {row['id']} | {row['role']} | {clean(row['title'])} | {row['validation']['check']} |"
        )
    lines.extend(
        [
            "## Source scope",
            "",
            *[f"- {p}" for p in package["source_scope"]],
            "",
            "## Artifacts",
            "",
        ]
    )
    for artifact in package["artifacts"]:
        lines.extend(
            [
                f"### {artifact['path']} ({artifact['status']})",
                "",
                artifact["why"],
                artifact["selection"],
                f"SHA256: {artifact['sha256']}",
                "",
                artifact["content"]
                if artifact["include_content"]
                else "(Reference-only; content is not embedded.)",
                "",
            ]
        )
    lines.extend(
        [
            "## Excluded / superseded guidance",
            "",
            json.dumps(package["excluded_context"], indent=2),
            "",
        ]
    )
    lines.extend(["## Known failures (current evidence)", ""])
    lines.extend(f"- {row}" for row in package["known_failures"])
    lines.extend(["", "## Decisions (spec-decisions)", ""])
    lines.extend(f"- {d['ID']} ({d['Status']}): {d['Decision']}" for d in package["decisions"])
    lines.extend(
        [
            "",
            package["assumptions"],
            "",
            "No check reads the assumptions table; an edit to it is reported only as "
            "UNMEASURED_POLICY_EDIT.",
            "",
        ]
    )
    lines.extend(["## Pending learning — unapproved, not requirements", ""])
    for item in package["pending_learning"]:
        lines.extend(
            [f"- {item['path']} — UNAPPROVED; see package.json for its content and identity."]
        )
    (destination / "package.md").write_text("\n".join(lines).rstrip() + "\n")
    return package


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--task", required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    destination = args.output or new_run("context")
    package = write_package(args.task, destination)
    print(
        json.dumps(
            {
                "package": str(destination),
                "task": args.task,
                "binding": [r["id"] for r in package["requirements"] if r["role"] == "binding"],
                "artifacts": len(package["artifacts"]),
                "gates": package["required_gates"],
            }
        )
    )


if __name__ == "__main__":
    main()
