"""Fixed tables for owned requirements, interface fields and bounded parameters."""

from __future__ import annotations

import copy
import json
import math
import re

from harness.spec_compiler import blocks, fail, table

REQUIREMENT_COLUMNS = [
    "ID",
    "Title",
    "Requirement",
    "Rationale",
    "Severity",
    "Inputs",
    "Expected",
    "Forbidden",
    "Evidence",
    "Mode",
    "Authority",
    "Decisions",
]
VERIFICATION_COLUMNS = ["ID", "Gate", "Check type", "Check", "Parameters"]
INTERFACE_COLUMNS = [
    "ID",
    "Interface",
    "Field",
    "Type",
    "Required fields",
    "Allowed values",
    "Constant",
    "Minimum",
    "Minimum items",
    "Pattern",
    "Extra fields",
    "Meaning",
]
SCHEMA_FIELDS = {
    "Type": "type",
    "Required fields": "required",
    "Allowed values": "enum",
    "Constant": "const",
    "Minimum": "minimum",
    "Minimum items": "minItems",
    "Pattern": "pattern",
    "Extra fields": "additionalProperties",
    "Meaning": "description",
}
BOUNDARY_CHECKS = {
    "source_identity",
    "explicit_history",
    "domain_identity",
    "history_refusal",
    "one_initial",
    "replay_suppression",
    "unchanged_suppression",
    "unresolved_refusal",
    "conflict_refusal",
    "time_schema",
    "no_timezone_inference",
    "historical_precedence",
    "no_age_cutoff",
    "clock_boundary",
    "no_labels_or_authorization",
    "output_provenance",
    "invalid_refusal",
    "optional_unknown",
    "semantics_refusal",
    "disposition_vocabulary",
    "candidate_only",
    "no_quantity_checklist",
    "no_absolute_inference",
}


def cell(row: dict, column: str, block: str):
    try:
        return json.loads(row[column])
    except ValueError as exc:
        raise fail(block, row["ID"], row["_line"], f"{column}: JSON scalar/list required") from exc


def requirement_sections(text: str, settings: dict) -> tuple[str, dict[str, int]]:
    found = blocks(text)
    checks = {r["ID"]: r for r in table(found, "spec-verification", VERIFICATION_COLUMNS)}
    rows = table(found, "spec-requirements", REQUIREMENT_COLUMNS)
    if set(checks) != {r["ID"] for r in rows}:
        raise fail(
            "spec-verification",
            "inventory",
            found["spec-verification"][0],
            "one check binding per requirement required",
        )
    sections = [text.split("## Requirements", 1)[0]]
    locations = {}
    for row in rows:
        key = row["ID"]
        if not re.fullmatch(r"(?:INPUT|OUTPUT|SIGNAL|STATE|HISTORY|SAFETY|OBS)-\d{3}", key):
            raise fail("spec-requirements", key, row["_line"], "invalid stable requirement ID")
        check = checks[key]
        authority = row["Authority"].split(" / ")
        if (
            len(authority) != 2
            or authority[0] not in {"grounded", "assessment-assumption"}
            or authority[1] not in {"owner-approved", "existing-contract"}
        ):
            raise fail(
                "spec-requirements", key, row["_line"], "retain explicit requirement authority"
            )
        locations[key] = row["_line"]
        sections.append(f"## {key} — {row['Title']}")
        fields = {
            "Requirement": row["Requirement"],
            "Rationale": row["Rationale"],
            "Severity": row["Severity"],
            "Inputs / preconditions": row["Inputs"],
            "Expected behavior": row["Expected"],
            "Forbidden behavior": row["Forbidden"],
            "Required evidence": row["Evidence"],
            "Deterministic or evaluative": row["Mode"],
            "Governance": authority[0],
            "Approval": authority[1],
            "Enforcement": "binding",
            "Basis": "Retained assessment contract; original rationale/provenance in the historical spec",
            "Implementation status": "not_established",
            "Check status": "not_available"
            if check["Check"] == "out_of_scope"
            else "executable_scoped",
            "Demonstrated evidence": "Generated coverage only; a check binding is not observed success",
            "Source": "spec.md",
            "Policy": settings["policy_id"],
            "Decisions": row["Decisions"],
            "Validation": f"Gate {check['Gate']} / {check['Check type']} / {check['Check']}",
            "Executable parameters": check["Parameters"],
        }
        sections.extend(f"{k}: {v}" for k, v in fields.items())
    return "\n".join(sections) + "\n", locations


def expand(found: dict) -> dict:
    nodes: dict[tuple[str, str], dict] = {}
    for row in table(found, "spec-interfaces", INTERFACE_COLUMNS):
        interface, path = row["Interface"], row["Field"]
        if interface not in {"input", "output"} or not re.fullmatch(
            r"\$(?:\.[a-z_][a-z_0-9]*|\[\])*", path
        ):
            raise fail(
                "spec-interfaces", row["ID"], row["_line"], "unknown interface or field path"
            )
        if (interface, path) in nodes:
            raise fail("spec-interfaces", row["ID"], row["_line"], "duplicate interface field")
        node = {
            key: cell(row, col, "spec-interfaces")
            for col, key in SCHEMA_FIELDS.items()
            if row[col] != "-"
        }
        kinds = node.get("type", [])
        kinds = [kinds] if isinstance(kinds, str) else kinds
        if not isinstance(kinds, list) or any(not isinstance(k, str) for k in kinds):
            raise fail(
                "spec-interfaces",
                row["ID"],
                row["_line"],
                "Type must be a JSON string or list of strings",
            )
        for key in ("required", "enum"):
            if key in node and (
                not isinstance(node[key], list)
                or not node[key]
                or (key == "required" and any(not isinstance(v, str) for v in node[key]))
            ):
                raise fail(
                    "spec-interfaces", row["ID"], row["_line"], key + " must be a nonempty list"
                )
        for key in ("minimum", "minItems"):
            if key in node and (
                type(node[key]) not in (int, float)
                or not math.isfinite(node[key])
                or (key == "minItems" and (type(node[key]) is not int or node[key] < 0))
            ):
                raise fail(
                    "spec-interfaces",
                    row["ID"],
                    row["_line"],
                    key + " requires a finite bound (nonnegative integer for item count)",
                )
        if "additionalProperties" in node and node["additionalProperties"] not in (
            True,
            False,
            {"type": "string"},
        ):
            raise fail(
                "spec-interfaces",
                row["ID"],
                row["_line"],
                "Extra fields must be true, false or a string-valued map",
            )
        if "pattern" in node:
            try:
                re.compile(node["pattern"])
            except (TypeError, re.error) as exc:
                raise fail(
                    "spec-interfaces",
                    row["ID"],
                    row["_line"],
                    "Pattern must be a valid literal regex string",
                ) from exc
        if not set(kinds) <= {"object", "array", "string", "integer", "number", "boolean", "null"}:
            raise fail(
                "spec-interfaces", row["ID"], row["_line"], "closed JSON type vocabulary required"
            )
        if "object" in kinds:
            node["properties"] = {}
        nodes[interface, path] = node
        if path == "$":
            node["$schema"] = "https://json-schema.org/draft/2020-12/schema"
            node["title"] = (
                "NGPL normalized classifier input v1"
                if interface == "input"
                else "Normalized classifier proposal v1"
            )
            continue
        parent_path = path[:-2] if path.endswith("[]") else path.rsplit(".", 1)[0]
        parent = nodes.get((interface, parent_path))
        if parent is None:
            raise fail(
                "spec-interfaces", row["ID"], row["_line"], "parent field must precede child"
            )
        if path.endswith("[]"):
            if parent.get("type") != "array":
                raise fail(
                    "spec-interfaces", row["ID"], row["_line"], "items require an array parent"
                )
            parent["items"] = node
        else:
            if "properties" not in parent:
                raise fail(
                    "spec-interfaces", row["ID"], row["_line"], "field requires an object parent"
                )
            parent["properties"][path.rsplit(".", 1)[1]] = node
    for (interface, path), node in nodes.items():
        if not set(node.get("required", [])) <= set(node.get("properties", {})):
            raise fail(
                "spec-interfaces",
                path,
                found["spec-interfaces"][0],
                "required field lacks a declaration",
            )
    for node in nodes.values():
        if node.get("properties") == {} and "required" not in node:
            del node["properties"]
    parameters = table(found, "spec-parameters", ["ID", "Meaning", "Value", "Unit", "Requirement"])
    if len(parameters) != 1 or parameters[0]["ID"] != "PARAM-INITIAL-001":
        raise fail(
            "spec-parameters",
            "inventory",
            found["spec-parameters"][0],
            "only the declared initial-alert limit is supported",
        )
    maximum = cell(parameters[0], "Value", "spec-parameters")
    if type(maximum) is not int or maximum < 0:
        raise fail(
            "spec-parameters",
            "PARAM-INITIAL-001",
            parameters[0]["_line"],
            "nonnegative integer maximum required",
        )
    if (
        parameters[0]["Unit"] != "initial alerts per resolved event"
        or parameters[0]["Requirement"] != "D1-005"
    ):
        raise fail(
            "spec-parameters",
            "PARAM-INITIAL-001",
            parameters[0]["_line"],
            "fixed unit and obligation required",
        )
    declarations = table(found, "spec-checks", ["ID", "Check", "Sentence coverage"])
    for row in declarations:
        if row["Check"] not in BOUNDARY_CHECKS | {"-"}:
            raise fail("spec-checks", row["ID"], row["_line"], "unknown code-owned boundary check")
        if row["Sentence coverage"] not in {"PARTIAL", "UNCHECKED", "PARAMETER"}:
            raise fail(
                "spec-checks",
                row["ID"],
                row["_line"],
                "declare PARAMETER, PARTIAL or UNCHECKED; no full prose PASS",
            )
    return {
        "normalized_input_schema": copy.deepcopy(nodes["input", "$"]),
        "normalized_output_schema": copy.deepcopy(nodes["output", "$"]),
        "parameters": {"max_initial_alerts_per_event": maximum},
        "parameter_rows": parameters,
        "check_declarations": declarations,
    }
