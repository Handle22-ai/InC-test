"""A short decision surface; detailed receipts stay linked and machine-readable."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

from harness.consequences import render as render_consequences
from harness.proposals import tradeoff_table
from harness.runtime import digest, write_json


def desk_summary(result: dict) -> list[str]:
    """What a trader would feel: missed positives, false positives, review workload."""
    rows = [
        r
        for r in result.get("findings", [])
        if r.get("code") in {"LABELED_MISSED_POSITIVES", "LABELED_FALSE_POSITIVES"}
    ]
    if not rows:
        return []
    outcomes = result.get("trading_layer", {}).get("label_outcomes", [])
    lines = [
        "| Capture | Labeled positives missed (limit) | Labeled negatives signaled (limit) "
        "| Labeled negatives sent to review |",
        "|---|---|---|---|",
    ]
    for capture in sorted({r["case"] for r in rows}):
        cells = []
        for code in ("LABELED_MISSED_POSITIVES", "LABELED_FALSE_POSITIVES"):
            row = next(r for r in rows if r["case"] == capture and r["code"] == code)
            cases = ", ".join(c.split("/")[-1] for c in row["cases"]) or "none"
            cells.append(f"{row['observed']}/7 ({row['limit']}) — {cases}")
        review = [
            o["notice_id"]
            for o in outcomes
            if o["id"].startswith(capture + "/")
            and o["label"] is False
            and o["classification"] == "UNRESOLVED"
        ]
        cells.append(f"{len(review)}/7 — {', '.join(map(str, review)) or 'none'}")
        lines.append(f"| {capture} | {cells[0]} | {cells[1]} | {cells[2]} |")
    lines += [
        "",
        "A positive sent to review counts as missed: nobody on the desk receives review items "
        "today. Limits are spec-settings `acceptance`. Negatives sent to review have no budget "
        "yet; that needs a desk decision on review capacity.",
    ]
    return lines


def render(destination: Path, result: dict) -> None:
    identity = result.get("comparison_identity", result.get("preflight_identity", {}))
    source = result["source"]
    mode = result.get("mode", "PREFLIGHT_REFUSED")
    codes = sorted(
        {
            r.get("code", "ERROR")
            for r in result.get("findings", [])
            if r["status"] not in {"PASS", "COUNTED"}
        }
        | {
            g["classification"]
            for g in result["gates"].values()
            if g.get("classification") and g["status"] != "PASS"
        }
    )
    review = {
        "PROPOSAL_ONLY": "PENDING — measured without the owner's reread of these spec bytes",
        "REVIEWED_SPEC": "read receipt matches these spec bytes (an assertion, not authentication)",
    }.get(mode, "not reached")
    coverage_rows = result.get("requirement_coverage", {})
    out_of_scope = sorted(k for k, v in coverage_rows.items() if v["status"] == "OUT_OF_SCOPE")
    lines = [
        "# Evidence for the engineer's next decision",
        "",
        f"Mode **{mode}** · human review: {review} · accepted: **{result['accepted']}**.",
        "",
        f"Non-passing finding codes: **{', '.join(codes) or 'none'}**. CI accepts only exit 0 "
        "from a reviewed run.",
        "",
        "Gates judge the **rebuilt component**. The inherited system is measured below, "
        "not gated"
        + (
            f" (12-step replay: **{result['inherited_layer']['status']}**)."
            if result.get("inherited_layer")
            else "."
        ),
        "",
        "| Gate | Status | Why |",
        "|---|---|---|",
    ]
    for key in ("1", "2", "3"):
        gate = result["gates"].get(key, {"name": "-", "status": "NOT_RUN"})
        default = (
            "All in-scope findings passed" if gate["status"] == "PASS" else "See findings below"
        )
        why = gate.get("reason", gate.get("classification", default))
        lines.append(f"| {key} — {gate['name']} | {gate['status']} | {why} |")
    lines += [
        "",
        f"Run `{destination.name}` · commit `{source['revision']}` · tracked changes "
        f"`{source['working_tree_dirty']}` · spec `{identity.get('spec_sha256', 'UNVERIFIED')}`.",
        "",
    ]
    if out_of_scope:
        lines += [
            "**Not claimed by this gate** (spec-verification `out_of_scope`): "
            + ", ".join(out_of_scope)
            + ". All 73 D prose obligations are unchecked prose; 23 code-owned boundary checks "
            "constrain the tables.",
            "",
        ]
    lines += ["## For the desk", ""]
    summary = desk_summary(result)
    lines += summary or ["NOT_RUN — no trading evidence was produced by this run."]
    trading = result.get("trading_layer", {})
    tradeoffs = trading.get("tradeoffs", {})
    if tradeoffs:
        lines += [
            "",
            tradeoff_table(tradeoffs["inherited"] + tradeoffs["rebuilt"]),
            "Both captures carry the same 14 labels and are not independent samples. capture-1 is "
            "the unmodified inherited run; capture-0 raised its impact-verdict token budget to 512. "
            "Unresolved cases are never counted as correct.",
        ]
        extraction = [
            r for r in result.get("findings", []) if r.get("code") == "CAPTURED_UPSTREAM_EXTRACTION"
        ]
        if extraction:
            lines += [
                "",
                "Upstream extraction retained from the inherited runs (no new model call):",
                "",
                "| Check | PASS | FAIL | ERROR | UNKNOWN |",
                "|---|---:|---:|---:|---:|",
            ]
            for field in sorted({r["field"] for r in extraction}):
                counts = Counter(r["status"] for r in extraction if r["field"] == field)
                lines.append(
                    f"| {field} | "
                    + " | ".join(str(counts[s]) for s in ("PASS", "FAIL", "ERROR", "UNKNOWN"))
                    + " |"
                )
    if trading.get("metrics"):
        lines += ["", "| Observed count | Cases |", "|---|---:|"]
        lines += [f"| {name} | {row['count']} |" for name, row in trading["metrics"].items()]
    inherited = result.get("inherited_layer", {})
    if inherited:
        attribution = inherited.get("attribution", {})
        lines += [
            "",
            f"Inherited system on the 12-step replay: **{inherited['status']}** — "
            f"{len(attribution.get('behavioral_findings', []))} behavioral failures, "
            f"{len(attribution.get('interface_unavailable', []))} observations it has no "
            "interface for (UNKNOWN). [Observations](signals/results.json).",
        ]
    unlabeled = result.get("input_contract", {}).get("unlabeled_samples")
    if unlabeled:
        lines += [
            "",
            f"Unlabeled recent NGPL notices: {unlabeled['html_notices']} HTML headers, "
            f"{len(unlabeled['html_contract_errors'])} input-contract errors; "
            f"{unlabeled['pdf_unsupported']}/{unlabeled['pdf_notices']} PDF outage reports "
            "are an unsupported format and go to review. Classifying them needs live extraction.",
        ]
    if result.get("consequences"):
        lines += [
            "",
            render_consequences(result["consequences"], details=False),
            "[Every notice's first failed condition](consequences.md). Generated consequences are "
            "not independent labels.",
        ]
    lines += [
        "",
        "## Open domain questions",
        "",
        "- Unzoned NGPL times stay UNKNOWN: no automatic actionability or recommendation.",
        "- WITHDRAWN status, geography priority and absolute-volume meaning need desk rulings "
        "(spec A-009).",
        "",
        "[Raw results](results.json) · [Coverage](coverage.md) · "
        "[Boundary checks](rule-invariants.json) · [Artifact hashes](manifest.json)",
        "",
    ]
    preflight = [
        r
        for r in result.get("findings", [])
        if r.get("gate") == 1 and r["status"] not in {"PASS", "COUNTED"}
    ]
    if preflight:
        lines += (
            ["## Contract refusals", ""]
            + [
                f"- {r.get('code', r.get('relation', 'CONTRACT_FAILURE'))}: "
                f"{r.get('reason', r.get('case', r.get('step', r.get('requirement'))))}"
                for r in preflight
            ]
            + [""]
        )
    coverage = [
        "# Requirement coverage",
        "",
        f"Run `{destination.name}` · spec `{identity.get('spec_sha256', 'UNVERIFIED')}` · mode "
        f"`{mode}` · commit `{source['revision']}`.",
        "",
        "PASS means the declared check passed on the listed observations, not that the whole "
        "obligation is proven. OUT_OF_SCOPE rows are declared in spec-verification and never gated.",
        "",
        "| Requirement | Check | Result | Observations | Evidence kinds |",
        "|---|---|---|---:|---|",
    ]
    for key in sorted(set(result.get("component_availability", {})) | set(coverage_rows)):
        row = coverage_rows.get(key, {})
        kinds = Counter(
            r.get("code", r.get("relation", "unspecified"))
            for r in result.get("findings", [])
            if r.get("requirement") == key
        )
        coverage.append(
            f"| {key} | {row.get('declared_check', 'NOT_RUN')} | "
            f"{row.get('status', 'NOT_EVALUATED')} | {row.get('observations', 0)} | "
            f"{'; '.join(f'{k}: {v}' for k, v in sorted(kinds.items()))} |"
        )
    coverage += ["", "[Exact observations](results.json)", ""]
    (destination / "coverage.md").write_text("\n".join(coverage))
    write_json(destination / "comparison-identity.json", identity)
    (destination / "CURRENT.md").write_text("\n".join(lines))
    manifest_path = destination / "manifest.json"
    manifest = json.loads(manifest_path.read_text())
    for name in (
        "comparison-identity.json",
        "CURRENT.md",
        "coverage.md",
        "consequences.md",
        "spec-rendered.md",
    ):
        if (destination / name).exists():
            manifest["files"][name] = digest(destination / name)
    write_json(manifest_path, manifest)
