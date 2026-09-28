"""Deterministic, closed-format spec compiler. No model or predicate language."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import math
import re
from functools import lru_cache
from pathlib import Path

from harness.runtime import ROOT

# Every check name spec-verification may declare. tests/test_check_registry.py
# requires each one to have an executor in both the offline gate and the live path.
CHECK_NAMES = frozenset(
    {
        "identity",
        "out_of_scope",
        "refusal",
        "replay",
        "decision_shape",
        "quantities",
        "links",
        "field_values",
        "classification",
        "persistence",
        "stored_idempotency",
        "revision",
        "restart",
        "lineage",
        "model_proof",
        "provenance",
        "integrity",
        "regression",
    }
)


def sha(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


def fail(block: str, row: str, line: int, message: str) -> ValueError:
    return ValueError(f"spec.md:{line}: block {block}, row {row}: {message}")


def blocks(text: str) -> dict:
    found = {}
    lines = text.splitlines()
    for i, line in enumerate(lines):
        if not line.startswith("```spec-"):
            continue
        name = line[3:]
        if name in found:
            raise fail(name, "-", i + 1, "duplicate block")
        end = next((j for j in range(i + 1, len(lines)) if lines[j] == "```"), None)
        if end is None:
            raise fail(name, "-", i + 1, "unterminated block")
        found[name] = (i + 2, lines[i + 1 : end])
    return found


def table(found: dict, name: str, columns: list[str]) -> list[dict]:
    if name not in found:
        raise fail(name, "-", 1, "required block missing")
    start, lines = found[name]
    if not lines or [x.strip() for x in lines[0].split("|")] != columns:
        raise fail(name, "header", start, "expected columns: " + ", ".join(columns))
    rows: list[dict] = []
    for i, line in enumerate(lines[1:], start + 1):
        if line.startswith("Precedence:"):
            continue
        values = [x.strip() for x in line.split("|")]
        if len(values) != len(columns) or any(not v for v in values):
            raise fail(name, values[0], i, "one value per domain column required")
        row = dict(zip(columns, values))
        row["_line"] = i
        if any(r[columns[0]] == values[0] for r in rows):
            raise fail(name, values[0], i, "duplicate row ID")
        rows.append(row)
    return rows


def requirements(text: str, settings: dict) -> dict:
    from harness.requirements import FIELDS, PARAMETERS

    rows: list[dict] = []

    # Preserve line numbers while ignoring commented-out obligations.
    def without_comment(match: re.Match[str]) -> str:
        return "\n" * match[0].count("\n")

    text = re.sub(r"<!--.*?-->", without_comment, text, flags=re.S)
    row_lines: dict[str, int] = {}
    if "```spec-requirements" in text:
        from harness.spec_tables import requirement_sections

        text, row_lines = requirement_sections(text, settings)
    for match in re.finditer(
        r"^## ((?:INPUT|OUTPUT|SIGNAL|STATE|HISTORY|SAFETY|OBS)-\d{3}) — ([^\n]+)\n(.*?)(?=^## |\Z)",
        text,
        re.M | re.S,
    ):
        key, title, body = match.groups()
        line = row_lines.get(key, text[: match.start()].count("\n") + 1)

        def value(label):
            found = re.findall("^" + re.escape(label) + r": (.*)$", body, re.M)
            if len(found) != 1:
                raise fail("requirements", key, line, "one " + label + " line required")
            return found[0]

        row = {
            "id": key,
            "title": title,
            **{field: value(label) for label, field in FIELDS.items()},
        }
        row["evidence"] = value("Required evidence").split("; ")
        row["decisions"] = (
            []
            if value("Decisions") == "Existing contract retained"
            else value("Decisions").split(", ")
        )
        try:
            gate, kind, check = value("Validation").split(" / ")
            params = json.loads(value("Executable parameters"))
        except ValueError as exc:
            raise fail("requirements", key, line, "malformed validation declaration") from exc
        if (
            gate not in {"Gate 1", "Gate 2", "Gate 3"}
            or kind
            not in {"contract", "invariant", "metamorphic", "labeled_eval", "negative_control"}
            or check not in CHECK_NAMES
        ):
            raise fail("requirements", key, line, "unsupported hand-authored check binding")
        if not isinstance(params, dict) or set(params) - PARAMETERS.get(check, set()):
            raise fail("requirements", key, line, "Unsupported executable parameters")
        if check in {"decision_shape", "quantities"} and (
            set(params) != PARAMETERS[check]
            or any(type(v) not in (int, float) or not math.isfinite(v) for v in params.values())
        ):
            raise fail("requirements", key, line, "finite numeric parameters required")
        if "ids" in params and (
            not isinstance(params["ids"], list)
            or not params["ids"]
            or any(type(v) is not int for v in params["ids"])
        ):
            raise fail("requirements", key, line, "nonempty integer case selection required")
        if "field" in params and params["field"] not in {"firm_mdq", "segments", "zones"}:
            raise fail("requirements", key, line, "unsupported field oracle")
        if (
            "oracle_support" in params
            and params["oracle_support"] != "requirements/oracle-support.json"
        ):
            raise fail("requirements", key, line, "unsupported source support file")
        if any(r["id"] == key for r in rows):
            raise fail("requirements", key, line, "duplicate requirement")
        row["validation"] = {
            "gate": int(gate.removeprefix("Gate ")),
            "type": kind,
            "check": check,
            "params": params,
        }
        rows.append(row)
    policies = {}
    for i in range(1, 7):
        lines = re.findall(rf"^\[D{i}-\d{{3}}\] (.*)$", text, re.M)
        if not lines:
            raise fail("decisions", f"D{i}", 1, "stable sentence IDs required")
        policies[f"D{i}"] = "\n".join(lines)
    return {
        "version": 2,
        "policy_id": settings["policy_id"],
        "policy_version": 4,
        "policy_decision": "spec.md#spec-ownership-and-decisions",
        "policies": policies,
        "requirements": rows,
    }


@lru_cache(maxsize=8)
def _compile(text: str, schema_text: str) -> dict:
    found = blocks(text)
    grammar = json.loads(schema_text)
    compact = "spec-requirements" in found
    extra = (
        {
            "spec-requirements",
            "spec-verification",
            "spec-interfaces",
            "spec-parameters",
            "spec-checks",
        }
        if compact
        else set()
    )
    if (
        set(found) - {"spec-predicates"}
        != {
            "spec-rules",
            "spec-actions",
            "spec-replays",
            "spec-replay-actions",
            "spec-settings",
            "spec-inputs",
            "spec-decisions",
        }
        | extra
    ):
        raise fail(
            "document",
            "-",
            1,
            "exact fixed block inventory required; new operators are not supported",
        )
    start, body = found["spec-settings"]
    try:
        settings = json.loads("\n".join(body))
    except ValueError as exc:
        raise fail("spec-settings", "-", start, str(exc)) from exc

    def no_operators(value):
        if isinstance(value, dict):
            if "operator" in value or "feature_predicates" in value:
                raise fail(
                    "spec-settings",
                    "-",
                    start,
                    "new predicate operators are forbidden; use an identified prose check",
                )
            for v in value.values():
                no_operators(v)
        elif isinstance(value, list):
            for v in value:
                no_operators(v)

    no_operators(settings)
    if compact:
        from harness.spec_tables import expand

        settings.update(expand(found))
    columns = grammar["columns"]
    if not compact and grammar.get("historical_columns"):
        columns = grammar["historical_columns"]
    rows = table(found, "spec-rules", ["ID", *columns, "Action"])
    if {r["ID"] for r in rows} != set(grammar["rule_ids"]):
        raise fail(
            "spec-rules",
            "inventory",
            found["spec-rules"][0],
            "every supported rule must appear once",
        )
    precedence = [x for x in found["spec-rules"][1] if x.startswith("Precedence:")]
    order = (
        precedence[0].removeprefix("Precedence:").strip().split(" > ")
        if len(precedence) == 1
        else []
    )
    if len(order) != len(rows) or set(order) != {r["ID"] for r in rows}:
        raise fail(
            "spec-rules", "Precedence", found["spec-rules"][0], "order every row exactly once"
        )
    action_rows = table(
        found, "spec-actions", ["Action", "Classification", "Disposition", "Reason"]
    )
    actions = {}
    for r in action_rows:
        if r["Classification"] not in {"UNRESOLVED", "NON_SIGNAL", "SIGNAL_CANDIDATE"} or r[
            "Disposition"
        ] not in {"REVIEW_REQUIRED", "ERROR", "SUPPRESSED", "NO_SIGNAL", "CANDIDATE_ONLY"}:
            raise fail("spec-actions", r["Action"], r["_line"], "unsupported named action result")
        actions[r["Action"]] = {
            "classification": r["Classification"],
            "disposition": r["Disposition"],
            "recommendation_allowed": False,
        }
    if set(actions) != set(grammar["actions"]):
        raise fail(
            "spec-actions",
            "inventory",
            found["spec-actions"][0],
            "named action inventory differs from grammar",
        )
    rules = []
    for row in rows:
        for col, allowed in columns.items():
            if row[col] not in allowed:
                raise fail("spec-rules", row["ID"], row["_line"], f"{col} must be one of {allowed}")
        if row["Action"] not in actions:
            raise fail("spec-rules", row["ID"], row["_line"], "unknown named action")
        rules.append(
            {
                "id": row["ID"],
                "priority": order.index(row["ID"]) * 10 + 10,
                "when": {c: row[c] for c in columns if row[c] != "ANY"},
                "action_name": row["Action"],
                "action": actions[row["Action"]],
                "requirements": settings["rule_requirements"][row["ID"]],
                "status": "spec-recorded",
                "oracle": "spec-derived, not independent",
                "basis": "spec.md:" + str(row["_line"]),
                "output_reason": next(
                    r["Reason"] for r in action_rows if r["Action"] == row["Action"]
                ),
                "spec_line": row["_line"],
            }
        )
    replay_actions = {}
    for row in table(
        found,
        "spec-replay-actions",
        ["Action", "Initial alerts", "Disposition", "Reason", "Semantic safety"],
    ):
        if row["Initial alerts"] not in {"0", "1"} or row["Semantic safety"] not in {"YES", "-"}:
            raise fail(
                "spec-replay-actions", row["Action"], row["_line"], "invalid bounded observation"
            )
        expected = {"initial": int(row["Initial alerts"]), "disposition": row["Disposition"]}
        if row["Reason"] != "-":
            expected["reason"] = row["Reason"]
        if row["Semantic safety"] == "YES":
            expected["semantic_safety"] = True
        replay_actions[row["Action"]] = expected
    steps = []
    for row in table(
        found,
        "spec-replays",
        [
            "ID",
            "Arriving notice",
            "Restart",
            "Oracle answer",
            "Authorization",
            "Action",
            "Requirement",
        ],
    ):
        for column, allowed in grammar["replay_columns"].items():
            if row[column] not in allowed:
                raise fail(
                    "spec-replays", row["ID"], row["_line"], f"{column} must be one of {allowed}"
                )
        if (
            row["Restart"] not in {"YES", "NO"}
            or row["Authorization"] not in {"YES", "NO"}
            or row["Action"] not in replay_actions
        ):
            raise fail("spec-replays", row["ID"], row["_line"], "unknown replay value/action")
        steps.append(
            {
                "id": row["ID"],
                "notice": row["Arriving notice"],
                "restart": row["Restart"] == "YES",
                "provider": row["Oracle answer"],
                "authorization": row["Authorization"] == "YES",
                "expected": replay_actions[row["Action"]],
                "requirement": row["Requirement"],
                "spec_line": row["_line"],
            }
        )
    if {r["id"] for r in steps} != set(grammar["replay_ids"]) or set(replay_actions) != set(
        grammar["replay_actions"]
    ):
        raise fail(
            "spec-replays",
            "inventory",
            found["spec-replays"][0],
            "every supported replay row and action must appear exactly once",
        )
    inputs = table(
        found, "spec-inputs", ["ID", "Field", "Type", "Missing", "Malformed", "Supplier"]
    )
    for row in inputs:
        for column, allowed in grammar["input_columns"].items():
            if row[column] not in allowed:
                raise fail(
                    "spec-inputs", row["ID"], row["_line"], f"{column} must be one of {allowed}"
                )
    if len({r["Field"] for r in inputs}) != len(inputs):
        raise fail("spec-inputs", "inventory", found["spec-inputs"][0], "duplicate source field")
    decisions = table(
        found, "spec-decisions", ["ID", "Status", "Person", "Previous spec SHA256", "Decision"]
    )
    for section in re.finditer(r"^### D[1-6] — [^\n]+\n(.*?)(?=^##|\Z)", text, re.M | re.S):
        for offset, line in enumerate(section[1].splitlines()):
            if line.strip() and not re.fullmatch(r"\[D[1-6]-\d{3}\] .+", line):
                raise fail(
                    "D-invariants",
                    "unidentified-sentence",
                    text[: section.start()].count("\n") + offset + 1,
                    "every D sentence needs a stable ID and hand-authored check",
                )
    for column, allowed in columns.items():
        if "- " + column + ": " + ", ".join(allowed) + "." not in text:
            raise fail(
                "spec-rules",
                "allowed-values",
                found["spec-rules"][0],
                "spec allowed values differ from the fixed grammar for " + column,
            )
    sentences = []
    for n, line in enumerate(text.splitlines(), 1):
        match = re.fullmatch(r"\[(D[1-6]-\d{3})\] (.+)", line)
        if match:
            sentences.append({"id": match[1], "sentence": match[2], "spec_line": n})
    if len({s["id"] for s in sentences}) != len(sentences):
        raise fail("decisions", "-", 1, "duplicate D sentence ID")
    if compact:
        declared = {r["ID"] for r in settings["check_declarations"]}
        sentence_ids = {s["id"] for s in sentences}
        if declared != sentence_ids:
            raise fail(
                "spec-checks",
                "inventory",
                found["spec-checks"][0],
                "each D sentence requires exactly one scope declaration; use UNCHECKED for new prose",
            )
    from harness.predicate_table import compile_predicates

    predicates, sets = compile_predicates(found, settings, columns, fail)
    contract = {
        **settings,
        "rules": rules,
        "columns": columns,
        "predicates": predicates,
        "sets": sets,
        "source_spec_sha256": sha(text),
        "normative_role": "Generated from spec.md; never edit",
        "precedence": " > ".join(order),
        "state_safety": {**settings["state_safety"], "steps": steps},
        "input_contract": inputs,
        "decisions": decisions,
        "sentences": sentences,
        "input_time_line": next(
            (
                i
                for i, line in enumerate(text.splitlines(), 1)
                if line.startswith("[INPUT-TIME-001]")
            ),
            found["spec-settings"][0],
        ),
    }
    contract["requirements_document"] = requirements(text, settings)
    acceptance = settings.get("acceptance")
    if acceptance is not None:
        ids = {r["id"] for r in contract["requirements_document"]["requirements"]}
        limits = ("max_missed_positives_per_capture", "max_false_positives_per_capture")
        if (
            set(acceptance) != {*limits, "review_satisfies"}
            or any(type(acceptance[k]) is not int or acceptance[k] < 0 for k in limits)
            or not set(acceptance["review_satisfies"]) <= ids
        ):
            raise fail(
                "spec-settings",
                "acceptance",
                start,
                "acceptance needs nonnegative integer budgets and known review_satisfies IDs",
            )
    obligations = {r["id"]: r for r in contract["requirements_document"]["requirements"]}
    for bound, value in settings["bounds"].items():
        requirement, parameter = bound.split(".", 1)
        if (
            requirement not in obligations
            or obligations[requirement]["validation"]["params"].get(parameter) != value
        ):
            raise fail(
                "spec-settings",
                bound,
                start,
                "representation bound contradicts the identified requirement's executable parameters",
            )
    for rule in rules:
        if not set(rule["requirements"]) <= obligations.keys():
            raise fail("spec-rules", rule["id"], rule["spec_line"], "unknown requirement ID")
    for step in steps:
        if step["requirement"] not in obligations:
            raise fail("spec-replays", step["id"], step["spec_line"], "unknown requirement ID")
    return contract


def compile_spec(root: Path = ROOT, text: str | None = None) -> dict:
    return copy.deepcopy(
        _compile(
            text if text is not None else (root / "spec.md").read_text(),
            (root / "requirements/rule-block.schema.json").read_text(),
        )
    )


def generated(contract: dict, label: str, data: dict) -> str:
    return (
        f"# Generated from spec.md; spec-sha256: {contract['source_spec_sha256']}; {label}; DO NOT EDIT\n"
        + json.dumps(data, indent=2, ensure_ascii=False)
        + "\n"
    )


def artifacts(contract: dict, root: Path = ROOT) -> dict[str, str]:
    from harness.domain_rules import derive

    c = {
        k: v
        for k, v in contract.items()
        if k not in {"requirements_document", "normalized_input_schema", "normalized_output_schema"}
    }
    table_text = render(contract)
    witnesses = json.loads((root / "requirements/normalized-witnesses.json").read_text())
    replay = {
        "source_spec_sha256": contract["source_spec_sha256"],
        "role": "generated consequences, not independent oracle",
        "normalized": {w["id"]: derive(contract, w["input"]) for w in witnesses},
        "stateful": contract["state_safety"]["steps"],
    }
    return {
        "requirements/behavior.yaml": generated(contract, "behavior", c),
        "requirements/requirements.yaml": generated(
            contract, "requirements", contract["requirements_document"]
        ),
        "requirements/signal-safety.yaml": generated(contract, "replay", contract["state_safety"]),
        "requirements/replay-expectations.json": json.dumps(replay, indent=2) + "\n",
        "requirements/normalized-input.schema.json": json.dumps(
            contract["normalized_input_schema"], indent=2
        )
        + "\n",
        "requirements/normalized-output.schema.json": json.dumps(
            contract["normalized_output_schema"], indent=2
        )
        + "\n",
        "docs/signal-contract.md": table_text,
        "docs/system-contract.md": "# Generated input contract\n\nSource: spec.md SHA256 "
        + contract["source_spec_sha256"]
        + "\n\n"
        + render_inputs(contract),
    }


def render_inputs(contract: dict) -> str:
    lines = [
        "| ID | Source field | Type | Missing | Malformed | Supplier |",
        "|---|---|---|---|---|---|",
    ]
    lines += [
        "| "
        + " | ".join(row[c] for c in ["ID", "Field", "Type", "Missing", "Malformed", "Supplier"])
        + " |"
        for row in contract["input_contract"]
    ]
    return "\n".join(lines) + "\n"


def render(contract: dict) -> str:
    columns = list(contract["columns"])
    lines = [
        "# Rules generated from spec.md",
        "",
        f"Spec SHA256: `{contract['source_spec_sha256']}`",
        "",
        contract["boundary"],
        "",
        "| Rule | " + " | ".join(columns) + " | Action |",
        "|---|" + "---|" * (len(columns) + 1),
    ]
    for r in sorted(contract["rules"], key=lambda r: r["priority"]):
        lines.append(
            "| "
            + r["id"]
            + " | "
            + " | ".join(r["when"].get(c, "ANY") for c in columns)
            + " | "
            + r["action_name"]
            + " |"
        )
    lines += [
        "",
        "Precedence: " + contract["precedence"],
        "",
        "No generated consequence is independent evaluation or approval.",
        "",
    ]
    return "\n".join(lines)


def drift(contract: dict, name: str, root: Path) -> ValueError:
    block, row, line = "generated-artifacts", name, 1
    if (
        name in {"requirements/behavior.yaml", "requirements/replay-expectations.json"}
        and (root / name).exists()
    ):
        try:
            import yaml

            observed = yaml.safe_load((root / name).read_text())
            if observed.get("source_spec_sha256") != contract["source_spec_sha256"]:
                block, row = "document", "spec identity"
            else:
                expected_steps = contract["state_safety"]["steps"]
                steps = observed.get("stateful", observed.get("state_safety", {}).get("steps", []))
                by_id = {r.get("id"): r for r in steps}
                step = next((r for r in expected_steps if by_id.get(r["id"]) != r), None)
                if step:
                    block, row, line = "spec-replays", step["id"], step["spec_line"]
                elif "rules" in observed:
                    by_id = {r.get("id"): r for r in observed["rules"]}
                    rule = next((r for r in contract["rules"] if by_id.get(r["id"]) != r), None)
                    predicates = observed.get("predicates", [])
                    changed = next(
                        (
                            p
                            for i, p in enumerate(contract["predicates"])
                            if i >= len(predicates) or predicates[i] != p
                        ),
                        None,
                    )
                    if rule:
                        block, row, line = "spec-rules", rule["id"], rule["spec_line"]
                    elif changed:
                        block, line = "spec-predicates", changed["spec_line"]
                        row = f"{changed['column']}={changed['value']}"
        except ValueError, AttributeError, TypeError, yaml.YAMLError:
            pass
    return fail(
        block,
        row,
        line,
        f"GENERATED_ARTIFACT_DRIFT: {name} differs from fresh compile or lacks its header; run compile explicitly after an authorized spec edit",
    )


def check_generated(root: Path = ROOT) -> dict:
    c = compile_spec(root)
    for name, expected in artifacts(c, root).items():
        if not (root / name).exists() or (root / name).read_text() != expected:
            raise drift(c, name, root)
    name = "requirements/compiled-build.json"
    expected_manifest = {
        "spec_sha256": c["source_spec_sha256"],
        "files": {name: sha(body) for name, body in artifacts(c, root).items()},
    }
    if not (root / name).exists() or json.loads((root / name).read_text()) != expected_manifest:
        raise drift(c, name, root)
    return c


def build(root: Path = ROOT) -> dict:
    from harness.rule_invariants import enforce
    from harness.spec_ownership import check_acceptance

    c = compile_spec(root)
    enforce(c)  # compile refuses a spec the gate would refuse
    check_acceptance(root, c)
    for name, body in artifacts(c, root).items():
        (root / name).parent.mkdir(parents=True, exist_ok=True)
        (root / name).write_text(body)
    (root / "requirements/compiled-build.json").write_text(
        json.dumps(
            {
                "spec_sha256": c["source_spec_sha256"],
                "files": {name: sha(body) for name, body in artifacts(c, root).items()},
            },
            indent=2,
        )
        + "\n"
    )
    return c


def refresh_for_gate(root: Path = ROOT) -> dict:
    """Compatibility entry point; gates validate but never build tracked artifacts."""
    return check_generated(root)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    try:
        c = check_generated() if args.check else build()
        print(
            json.dumps(
                {
                    "status": "PASS",
                    "spec_sha256": c["source_spec_sha256"],
                    "rules": len(c["rules"]),
                    "approval": False,
                }
            )
        )
    except ValueError as exc:
        print(json.dumps({"status": "ERROR", "reason": str(exc)}))
        raise SystemExit(2)


if __name__ == "__main__":
    main()
