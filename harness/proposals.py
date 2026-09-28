"""Measure proposed spec consequences without adopting, compiling outputs or rereading it."""

from __future__ import annotations

import argparse
import html
import json
import re
import subprocess
from difflib import unified_diff
from pathlib import Path

from harness.consequences import observations, render
from harness.rule_invariants import evaluate
from harness.runtime import ROOT, create_run, digest, new_run, write_json
from harness.spec_compiler import blocks, compile_spec, table
from harness.spec_compiler import render as render_rules


def declarations(text: str) -> dict[tuple[str, str], dict]:
    """Index fixed table declarations, preserving source lines but ignoring line shifts."""
    found = blocks(text)
    result = {}
    for name, (start, lines) in found.items():
        if name == "spec-settings":
            for offset, line in enumerate(lines):
                stripped = line.strip().rstrip(",")
                if not stripped.startswith('"') or ":" not in stripped:
                    continue
                key, value = stripped.split(":", 1)
                result[name, json.loads(key)] = {
                    "line": start + offset,
                    "fields": {"Value": value.strip()},
                }
            continue
        if name == "spec-predicates":
            for offset, line in enumerate(lines[1:], start + 1):
                column, value, condition = (part.strip() for part in line.split("|", 2))
                result[name, f"{column} = {value}"] = {
                    "line": offset,
                    "fields": {"Condition": condition},
                }
            continue
        columns = [value.strip() for value in lines[0].split("|")]
        for row in table(found, name, columns):
            result[name, row[columns[0]]] = {
                "line": row["_line"],
                "fields": {column: row[column] for column in columns[1:]},
            }
        for offset, line in enumerate(lines):
            if line.startswith("Precedence:"):
                result[name, "Precedence"] = {
                    "line": start + offset,
                    "fields": {"Order": line.removeprefix("Precedence:").strip()},
                }
    result.update(prose_declarations(text))
    return result


# Owned prose that no check reads: an edit to it can never be measured (audit 5 #12).
PROSE_BLOCKS = {"spec-prose", "spec-assumptions"}
D_SENTENCE = re.compile(r"^\[(D\d-\d{3})\] (.*)$")
ASSUMPTION = re.compile(r"^\| (A-\d{3}) \| (.*) \| (.*) \|$")


def prose_declarations(text: str) -> dict[tuple[str, str], dict]:
    """Index D-sentences and assessment-assumption rows, which live outside fenced blocks."""
    result = {}
    for number, line in enumerate(text.splitlines(), start=1):
        if match := D_SENTENCE.match(line):
            result["spec-prose", match[1]] = {"line": number, "fields": {"Sentence": match[2]}}
        elif match := ASSUMPTION.match(line):
            result["spec-assumptions", match[1]] = {
                "line": number,
                "fields": {"Scope": match[2], "Limit": match[3]},
            }
    return result


def declaration_changes(before: str, after: str) -> list[dict]:
    old, new = declarations(before), declarations(after)
    changes = []
    for block, key in sorted(old.keys() | new.keys()):
        previous, proposed = old.get((block, key)), new.get((block, key))
        old_fields = previous["fields"] if previous is not None else {}
        new_fields = proposed["fields"] if proposed is not None else {}
        if previous is not None and proposed is not None and old_fields == new_fields:
            continue
        changes.append(
            {
                "block": block,
                "id": key,
                "change": "added"
                if previous is None
                else "removed"
                if proposed is None
                else "edited",
                "baseline_line": previous["line"] if previous is not None else None,
                "proposal_line": proposed["line"] if proposed is not None else None,
                "fields": {
                    field: {"before": old_fields.get(field), "after": new_fields.get(field)}
                    for field in dict.fromkeys([*old_fields, *new_fields])
                    if old_fields.get(field) != new_fields.get(field)
                },
            }
        )
    return changes


def declaration_table(changes: list[dict]) -> str:
    def cell(value: str | None) -> str:
        return html.escape(value if value is not None else "(absent)").replace("|", "&#124;")

    def reference(line: int | None, snapshot: str) -> str:
        return f"[spec.md:{line}]({snapshot}-spec.md#L{line})" if line is not None else "—"

    lines = [
        "## Edited declarations",
        "",
        "Fixed table changes are shown even when no captured outcome changes. Line references point to the saved baseline and proposal snapshots. Prose and fixed settings are covered by the [complete textual spec diff](spec.diff).",
        "",
        "| Block / declaration | Change | Baseline | Proposal | Edited fields (before → after) |",
        "|---|---|---|---|---|",
    ]
    for row in changes:
        fields = "; ".join(
            f"{cell(field)}: {cell(values['before'])} → {cell(values['after'])}"
            for field, values in row["fields"].items()
        )
        lines.append(
            f"| {cell(row['block'])} / {cell(row['id'])} | {row['change']} | {reference(row['baseline_line'], 'baseline')} | {reference(row['proposal_line'], 'proposal')} | {fields} |"
        )
    if not changes:
        lines.append("| — | No fixed table declaration changed | — | — | — |")
    return "\n".join(lines) + "\n"


def summaries(cases: list[dict], *, inherited: bool = False) -> list[dict]:
    result = []
    for capture in sorted({r["id"].split("/")[0] for r in cases}):
        rows = [
            r
            for r in cases
            if r["id"].startswith(capture + "/") and r.get("expected_signal") is not None
        ]
        counts = {
            k: 0
            for k in (
                "true_positive",
                "false_positive",
                "true_negative",
                "false_negative",
                "positive_unresolved",
                "negative_unresolved",
                "errors",
            )
        }
        for row in rows:
            action = row["outcome"]["action"]
            failed = (
                row.get("inherited_execution") != "SUCCESS"
                if inherited
                else action["disposition"] == "ERROR"
            )
            predicted = (
                (
                    "SIGNAL_CANDIDATE"
                    if row.get("inherited_signal") in (True, 1)
                    else "NON_SIGNAL"
                    if row.get("inherited_signal") in (False, 0)
                    else "UNRESOLVED"
                )
                if inherited
                else action["classification"]
            )
            if failed:
                predicted = "UNRESOLVED"
            if predicted == "UNRESOLVED":
                key = "positive_unresolved" if row["expected_signal"] else "negative_unresolved"
            elif predicted == "SIGNAL_CANDIDATE":
                key = "true_positive" if row["expected_signal"] else "false_positive"
            else:
                key = "false_negative" if row["expected_signal"] else "true_negative"
            counts[key] += 1
            counts["errors"] += failed
        positives = sum(r["expected_signal"] for r in rows)
        result.append(
            {
                "capture": capture,
                "implementation": (
                    "inherited + 512-token variant"
                    if rows and rows[0].get("inherited_system") == "impact-budget-512"
                    else "unmodified inherited captured output"
                    if rows and rows[0].get("inherited_system") == "inherited"
                    else "unidentified inherited capture"
                )
                if inherited
                else "spec-derived classifier",
                "labeled": len(rows),
                "positives": positives,
                "negatives": len(rows) - positives,
                "unresolved": counts["positive_unresolved"] + counts["negative_unresolved"],
                **counts,
            }
        )
    return result


def tradeoff_table(rows: list[dict]) -> str:
    lines = [
        "| Capture / system | Detected positives | False positives | True negatives | Negative on positive | Positive unresolved | Negative unresolved | Errors | Unresolved / labeled |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for r in rows:
        lines.append(
            f"| {r['capture']} / {r['implementation']} | {r['true_positive']}/{r['positives']} | {r['false_positive']} | {r['true_negative']}/{r['negatives']} | {r['false_negative']} | {r['positive_unresolved']} | {r['negative_unresolved']} | {r['errors']} | {r['unresolved']}/{r['labeled']} |"
        )
    return "\n".join(lines) + "\n"


def compare_cases(before: list[dict], after: list[dict]) -> list[dict]:
    old = {r["id"]: r for r in before}
    new = {r["id"]: r for r in after}
    return [
        {
            "id": key,
            "notice_id": (new.get(key) or old[key])["notice_id"],
            "expected_signal": (new.get(key) or old[key]).get("expected_signal"),
            "before": old.get(key, {}).get("outcome"),
            "after": new.get(key, {}).get("outcome"),
            "action_changed": old.get(key, {}).get("outcome", {}).get("action")
            != new.get(key, {}).get("outcome", {}).get("action"),
            "rule_changed": old.get(key, {}).get("outcome", {}).get("rule")
            != new.get(key, {}).get("outcome", {}).get("rule"),
        }
        for key in sorted(old.keys() | new.keys())
        if old.get(key, {}).get("outcome") != new.get(key, {}).get("outcome")
    ]


def read_spec(name: str) -> tuple[str, str]:
    path = Path(name)
    if path.is_file():
        return path.read_text(), str(path.resolve())
    if name == "HEAD:spec.md":
        return subprocess.check_output(["git", "show", name], cwd=ROOT, text=True), name
    if name == "REVIEWED":
        return reviewed_spec()
    raise ValueError("Use an existing spec file, HEAD:spec.md or REVIEWED as the baseline")


def reviewed_spec() -> tuple[str, str]:
    """The spec bytes named by the owner's current read receipt, found in Git history."""
    import hashlib

    pin = json.loads((ROOT / "context/spec-read-pin.json").read_text())
    for commit in subprocess.check_output(
        ["git", "log", "--format=%H", "--", "spec.md"], cwd=ROOT, text=True
    ).split():
        text = subprocess.check_output(["git", "show", f"{commit}:spec.md"], cwd=ROOT, text=True)
        if hashlib.sha256(text.encode()).hexdigest() == pin["spec_sha256"]:
            return text, f"{commit[:7]}:spec.md (last reread)"
    raise ValueError("The reread spec is not in this repository's history; pass --base")


def supplied_inputs(path: Path, contract: dict) -> list[dict]:
    """Evaluate operator-supplied normalized examples separately, without labels."""
    from harness.behavior_contract import derive

    examples = json.loads(path.read_text())
    if not isinstance(examples, list) or not examples:
        raise ValueError("--inputs requires a nonempty JSON array of {id, input} examples")
    rows, seen = [], set()
    for example in examples:
        if not isinstance(example, dict) or set(example) != {"id", "input"}:
            raise ValueError("Each supplied example must contain exactly id and input; no labels")
        key = example["id"]
        if not isinstance(key, str) or not key.strip() or key in seen:
            raise ValueError("Supplied example IDs must be nonempty and unique")
        seen.add(key)
        if not isinstance(example["input"], dict):
            raise ValueError("Supplied normalized input must be an object")
        try:
            outcome = derive(contract, example["input"])
        except (ValueError, KeyError, TypeError) as exc:
            outcome = {
                "rule": "INPUT_CONTRACT",
                "action": {
                    "classification": "UNRESOLVED",
                    "disposition": "ERROR",
                    "recommendation_allowed": False,
                },
                "reason": str(exc),
            }
        rows.append(
            {
                "id": key,
                "notice_id": example.get("input", {}).get("notice", {}).get("notice_id"),
                "outcome": outcome,
            }
        )
    return rows


def run(spec: Path, base: str, destination: Path, inputs_path: Path | None = None) -> dict:
    text = spec.read_text()
    old_text, old_name = read_spec(base)
    after_contract, before_contract = compile_spec(text=text), compile_spec(text=old_text)
    before, after = observations(before_contract), observations(after_contract)
    checks = evaluate(after_contract)
    from harness.input_contract_checks import run as check_input

    inputs = check_input(after_contract, destination / "input-contract.json")
    from collections import Counter

    rules = []
    for rule in after_contract["rules"]:
        conditions = [
            next(r for r in case["conditions"] if r["rule"] == rule["id"]) for case in after
        ]
        rules.append(
            {
                "id": rule["id"],
                "spec_line": rule["spec_line"],
                "matches": sum(r["matched"] for r in conditions),
                "wins": sum(r["outcome"]["rule"] == rule["id"] for r in after),
                "first_failed_counts": dict(
                    Counter(r["first_failed"]["condition"] for r in conditions if not r["matched"])
                ),
            }
        )
    result = {
        "mode": "PROPOSAL_ONLY",
        "accepted": False,
        "review_recorded": False,
        "spec": str(spec.resolve()),
        "spec_sha256": after_contract["source_spec_sha256"],
        "baseline": old_name,
        "baseline_sha256": before_contract["source_spec_sha256"],
        "denominator": len(after),
        "rules": rules,
        "cases": after,
        "changed_outcomes": compare_cases(before, after),
        "declaration_changes": declaration_changes(old_text, text),
        "parameter_changes": {
            key: {
                "before": before_contract.get(
                    "parameters", {"max_initial_alerts_per_event": 1}
                ).get(key),
                "after": value,
            }
            for key, value in after_contract.get("parameters", {}).items()
            if before_contract.get("parameters", {"max_initial_alerts_per_event": 1}).get(key)
            != value
        },
        "replay_changes": [
            {
                "id": row["id"],
                "before": next(
                    (
                        r["expected"]
                        for r in before_contract["state_safety"]["steps"]
                        if r["id"] == row["id"]
                    ),
                    None,
                ),
                "after": row["expected"],
            }
            for row in after_contract["state_safety"]["steps"]
            if next(
                (
                    r["expected"]
                    for r in before_contract["state_safety"]["steps"]
                    if r["id"] == row["id"]
                ),
                None,
            )
            != row["expected"]
        ],
        "before_labels": summaries(before),
        "after_labels": summaries(after),
        "inherited_labels": summaries(after, inherited=True),
        "checks": checks,
        "input_findings": inputs["findings"],
        "comparison_scope": "Same verified captures and compiler; generated consequences, not independent evaluation or policy approval.",
    }
    if inputs_path is not None:
        supplied_before = supplied_inputs(inputs_path, before_contract)
        supplied_after = supplied_inputs(inputs_path, after_contract)
        result["supplied_inputs"] = {
            "sha256": digest(inputs_path),
            "before": supplied_before,
            "after": supplied_after,
            "changed": compare_cases(supplied_before, supplied_after),
            "scope": "Unlabeled normalized examples, separate from captured accuracy. Raw HTML/date parsing is not exercised.",
        }
        (destination / "supplied-inputs.json").write_bytes(inputs_path.read_bytes())
    write_json(destination / "consequences.json", result)
    (destination / "proposal-spec.md").write_text(text)
    (destination / "baseline-spec.md").write_text(old_text)
    diff = unified_diff(
        old_text.splitlines(keepends=True),
        text.splitlines(keepends=True),
        fromfile="baseline-spec.md",
        tofile="proposal-spec.md",
    )
    (destination / "spec.diff").write_text(
        "".join(
            line if line.endswith("\n") else line + "\n\\ No newline at end of file\n"
            for line in diff
        )
    )
    from harness.rule_invariants import violation
    from harness.specification import evaluate_witness, fixtures

    witness_failures = []
    for witness in fixtures():
        try:
            observed = evaluate_witness(after_contract, witness)
        except (ValueError, KeyError, TypeError) as exc:
            witness_failures.append(f"frozen witness {witness['id']}: {exc}")
            continue
        if observed["evaluation_status"] == "FAIL":
            want = witness["prospective_action"]
            got = observed["active_expectation"]["action"]
            witness_failures.append(
                f"CONTRACT_CONTRADICTS_FIXTURE: frozen witness {witness['id']} expects "
                f"{want['classification']}/{want['disposition']}; the proposal gives "
                f"{got['classification']}/{got['disposition']} ({observed['active_expectation']['rule']})"
            )
    # Which stage refuses matters: make compile enforces the boundary checks, while input
    # contract findings and frozen-witness contradictions stop only the gate (audit 5 #10).
    result["refused_by"] = {
        "compile": [violation(r) for r in checks if r["status"] == "FAIL"],
        "gate": [r["reason"] for r in inputs["findings"]] + witness_failures,
    }
    result["would_be_refused"] = result["refused_by"]["compile"] + result["refused_by"]["gate"]
    # Examples supplied with --inputs are the author's own; they illustrate an edit but
    # do not count as independent evidence (audit 3 #9).
    result["unmeasured_edits"] = [
        f"{c['block']} / {c['id']}"
        for c in result["declaration_changes"]
        if c["block"] != "spec-decisions"
        and (c["block"] in PROSE_BLOCKS or not result["changed_outcomes"])
    ]
    (destination / "rules.md").write_text(render_rules(after_contract))
    (destination / "nonmatches.md").write_text(render(result))
    lines = [
        "# Proposed spec consequences",
        "",
        "**PROPOSAL ONLY — no policy adoption, read receipt or acceptance.**",
        "",
        *(
            ["**WOULD BE REFUSED** by `make compile` (boundary checks) and so by the gate:", ""]
            + [f"- {reason}" for reason in result["refused_by"]["compile"]]
            + [""]
            if result["refused_by"]["compile"]
            else []
        ),
        *(
            [
                "**WOULD BE REFUSED** by the gate only (`make compile` accepts these bytes; "
                "the input contract and frozen witnesses are checked at gate time):",
                "",
            ]
            + [f"- {reason}" for reason in result["refused_by"]["gate"]]
            + [""]
            if result["refused_by"]["gate"]
            else []
        ),
        *(
            [
                "**UNMEASURED:** these edits change no captured outcome, so no independent "
                "evidence shows whether they are right. Examples supplied with `--inputs` are "
                "author-supplied illustrations, not evidence. Add a labeled case or a frozen "
                "witness (an owner action):",
                "",
            ]
            + [f"- {edit}" for edit in result["unmeasured_edits"]]
            + [""]
            if result["unmeasured_edits"]
            else []
        ),
        f"Proposal `{result['spec_sha256']}`; baseline `{result['baseline_sha256']}`.",
        "",
        f"Changed captured outcomes: **{len(result['changed_outcomes'])}/{len(after)}**; action changes: **{sum(r['action_changed'] for r in result['changed_outcomes'])}**; matched rule-ID changes: **{sum(r['rule_changed'] for r in result['changed_outcomes'])}**. Counts may overlap. Rule match counts are not accuracy scores.",
        "",
        declaration_table(result["declaration_changes"]),
        "## Outcome tradeoffs",
        "",
        "Before:",
        "",
        tradeoff_table(result["before_labels"]),
        "After:",
        "",
        tradeoff_table(result["after_labels"]),
        "Inherited saved predictions:",
        "",
        tradeoff_table(result["inherited_labels"]),
        "Unresolved positives are not detected positives; abstentions are never credited as correct negatives. Captures are correlated and reported separately. No live model ran.",
        "",
        render(result, details=False),
        "## Validation limits",
        "",
        f"Parameter changes: `{json.dumps(result['parameter_changes'])}`. Replay changes: `{json.dumps(result['replay_changes'])}`.",
        "",
    ]
    for row in checks:
        if row["status"] == "FAIL" or row["code"] == "D_SENTENCE_CHANGED":
            lines.append(
                f"- spec.md:{row['spec_line']} {row['id']}: contradicts {row['id'].split('-')[0]} — {row['sentence']}"
            )
    lines += [f"- {r['reason']}" for r in inputs["findings"]]
    lines += [
        "",
        f"Unchecked prose obligations: {sum(r['kind'] == 'prose_obligation' for r in checks)}. Compiled boundary checks are separate and do not interpret prose.",
        "",
        "[Every case and first failed condition](nonmatches.md) · [Generated rules](rules.md) · [Machine results](consequences.json)",
        "",
    ]
    if inputs_path is not None:
        supplied = result["supplied_inputs"]
        lines += [
            "## Supplied normalized examples",
            "",
            supplied["scope"],
            "",
            "| Example | Before | After |",
            "|---|---|---|",
        ]
        for before_row, after_row in zip(supplied["before"], supplied["after"]):

            def label(row):
                return row["outcome"]["rule"] + " / " + row["outcome"]["action"]["disposition"]

            lines.append(
                f"| {html.escape(after_row['id'])} | {label(before_row)} | {label(after_row)} |"
            )
        lines += [
            "",
            "[Supplied inputs](supplied-inputs.json); full refusal reasons are in consequences.json.",
            "",
        ]
    (destination / "REPORT.md").write_text("\n".join(lines))
    write_json(
        destination / "manifest.json",
        {
            "mode": "PROPOSAL_ONLY",
            "files": {p.name: digest(p) for p in sorted(destination.iterdir()) if p.is_file()},
        },
    )
    return result


def main() -> None:
    parser = argparse.ArgumentParser(prog="python -m harness consequences", description=__doc__)
    parser.add_argument("--spec", type=Path, default=ROOT / "spec.md")
    parser.add_argument(
        "--base",
        default="REVIEWED",
        help="Baseline spec: REVIEWED (the last reread, default), HEAD:spec.md or a file",
    )
    parser.add_argument("--output", type=Path)
    parser.add_argument(
        "--inputs", type=Path, help="JSON array of unlabeled {id, input} normalized examples"
    )
    args = parser.parse_args()
    try:
        destination = create_run(args.output or new_run("proposals"))
        result = run(args.spec, args.base, destination, args.inputs)
        print(
            json.dumps(
                {
                    "mode": result["mode"],
                    "accepted": False,
                    "changed_outcomes": len(result["changed_outcomes"]),
                    "would_be_refused": len(result["would_be_refused"]),
                    "unmeasured_edits": len(result["unmeasured_edits"]),
                    "report": str(destination / "REPORT.md"),
                }
            )
        )
        if result["would_be_refused"]:
            raise SystemExit(4)
    except (ValueError, OSError, KeyError, TypeError, subprocess.CalledProcessError) as exc:
        print(json.dumps({"status": "ERROR", "reason": str(exc), "accepted": False}))
        raise SystemExit(2) from exc


if __name__ == "__main__":
    main()
