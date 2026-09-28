"""Finite structured behavioral rules and generated views; no NLP or application policy."""

from __future__ import annotations

from datetime import datetime

from harness.runtime import ROOT

CONTRACT = ROOT / "requirements/behavior.yaml"


def load(*, check_view: bool = True) -> dict:
    from harness.rule_invariants import enforce
    from harness.spec_compiler import check_generated
    from harness.spec_ownership import verify

    contract = check_generated(ROOT)
    enforce(contract)
    verify(ROOT, contract)
    return contract


def render(contract: dict) -> str:
    from harness.spec_compiler import render as render_spec

    return render_spec(contract)


def history_observations(value: dict) -> dict:
    from harness.domain_rules import history

    return history(value)


def features(value: dict, *, contract: dict | None = None) -> dict:
    from harness.domain_rules import observe

    result = observe(contract or load(), value)
    return {**result, "firm_disruption": result["Service class"] == "FIRM_DISRUPTION"}


def derive(contract: dict, inputs: dict) -> dict:
    from harness.domain_rules import derive as derive_rule

    validate_input(inputs, contract=contract)
    return derive_rule(contract, inputs)


def check_bound(contract: dict, name: str, observation: float) -> bool:
    return observation <= contract["bounds"][name]


def validate_schema(value: dict, schema: dict) -> None:
    """Validate only the JSON-schema vocabulary used by this bounded interface."""
    import math
    import re

    def visit(item, rule, path):
        kinds = rule.get("type", [])
        kinds = [kinds] if isinstance(kinds, str) else kinds
        matches = {
            "object": type(item) is dict,
            "array": type(item) is list,
            "string": type(item) is str,
            "integer": type(item) is int,
            "number": type(item) in (int, float),
            "boolean": type(item) is bool,
            "null": item is None,
        }
        if kinds and not any(matches[k] for k in kinds):
            raise ValueError(path + ": invalid type")
        if "const" in rule and (
            item != rule["const"] or (isinstance(item, bool) != isinstance(rule["const"], bool))
        ):
            raise ValueError(path + ": invalid constant")
        if "enum" in rule and item not in rule["enum"]:
            raise ValueError(path + ": unsupported value")
        if type(item) in (int, float):
            if not math.isfinite(item) or ("minimum" in rule and item < rule["minimum"]):
                raise ValueError(path + ": invalid quantity")
        if isinstance(item, str) and "pattern" in rule and not re.fullmatch(rule["pattern"], item):
            raise ValueError(path + ": invalid format")
        if isinstance(item, dict):
            if not set(rule.get("required", [])) <= item.keys():
                raise ValueError(path + ": required field missing")
            properties = rule.get("properties", {})
            for k, v in item.items():
                child = properties.get(k, rule.get("additionalProperties", {}))
                if child is False:
                    raise ValueError(path + ": unexpected field " + k)
                if isinstance(child, dict):
                    visit(v, child, path + "." + k)
        if isinstance(item, list):
            if len(item) < rule.get("minItems", 0):
                raise ValueError(path + ": too few items")
            for index, member in enumerate(item):
                visit(member, rule.get("items", {}), path + f"[{index}]")

    visit(value, schema, "input")


def validate_input(value: dict, *, contract: dict | None = None) -> None:
    contract = contract or load()
    schema = contract["normalized_input_schema"]
    validate_schema(value, schema)
    clock = datetime.fromisoformat(value["reference_time"])
    offset = clock.utcoffset()
    if clock.tzinfo is None or offset is None or offset.total_seconds() != 0:
        raise ValueError("reference_time must be explicit UTC")
    for facts in [value["facts"], *[v["facts"] for v in value["history"]]]:
        for key in ["start_time", "end_time"]:
            if facts[key] is not None:
                time = datetime.fromisoformat(facts[key])
                if time.tzinfo is None:
                    raise ValueError("Normalized time must retain an explicit offset")
        for q in facts["quantities"]:
            units = contract["quantity_units"]
            if q["unit"] not in units[q["kind"]]:
                raise ValueError("Incompatible quantity kind/unit")
            if q["kind"] != "UNAVAILABLE" and q["value"] is None:
                raise ValueError("Numeric quantity requires a value")
            if q["kind"] == "ABSOLUTE_CURTAILMENT" and not q["basis"].strip():
                raise ValueError(
                    "Absolute curtailment requires its stated source capacity/time basis"
                )
            if q["kind"] == "SCHEDULED_TO_PCT_MDQ" and (
                q["unit"] != "PERCENT_MDQ" or q["value"] is None or q["value"] > 100
            ):
                raise ValueError("Invalid scheduled-to MDQ quantity or unit")
            if q["kind"] == "UNAVAILABLE" and (q["value"] is not None or q["unit"] != "NONE"):
                raise ValueError("UNAVAILABLE is categorical, not an invented volume")
