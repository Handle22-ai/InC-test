"""Component-owned policy loading, input validation and rule evaluation.

The component reads only the generated policy files compiled from spec.md. It
imports nothing from the harness, so harness checks observe an independent
implementation of the spec tables instead of re-running their own code.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import re
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
# Set by the harness's explicit proposal measurement to the exact spec SHA-256.
# It lets an unreviewed spec execute for measurement; it never records review.
MEASUREMENT_ENV = "NGPL_MEASURE_UNREVIEWED_SPEC"


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_policy(root: Path = ROOT) -> dict:
    """Load the generated policy, refusing drifted artifacts or an unreviewed spec."""
    spec = _sha(root / "spec.md")
    manifest = json.loads((root / "requirements/compiled-build.json").read_text())
    stale = manifest.get("spec_sha256") != spec or any(
        not (root / name).exists() or _sha(root / name) != digest
        for name, digest in manifest.get("files", {}).items()
    )
    if stale:
        raise ValueError(
            "GENERATED_ARTIFACT_DRIFT: generated policy does not match spec.md; run make compile"
        )
    if os.environ.get(MEASUREMENT_ENV) != spec:
        try:
            pin = json.loads((root / "context/spec-read-pin.json").read_text())
        except OSError, ValueError:
            pin = {}
        if pin.get("spec_sha256") != spec:
            raise ValueError(
                "UNRECORDED_SPEC_CHANGE / STALE_SPEC_PIN: current spec bytes are not covered "
                "by the previous read receipt; actual human reread required"
            )
    text = (root / "requirements/behavior.yaml").read_text()
    policy = json.loads(text.split("\n", 1)[1])
    policy["input_schema"] = json.loads(
        (root / "requirements/normalized-input.schema.json").read_text()
    )
    policy["output_schema"] = json.loads(
        (root / "requirements/normalized-output.schema.json").read_text()
    )
    return policy


def same(left, right) -> bool:
    """JSON equality where booleans and numbers are not interchangeable."""
    if isinstance(left, bool) or isinstance(right, bool):
        return type(left) is type(right) and left == right
    if isinstance(left, (int, float)) and isinstance(right, (int, float)):
        return left == right
    if type(left) is not type(right):
        return False
    if isinstance(left, dict):
        return left.keys() == right.keys() and all(same(left[k], right[k]) for k in left)
    if isinstance(left, list):
        return len(left) == len(right) and all(same(a, b) for a, b in zip(left, right))
    return left == right


TYPES = {
    "object": lambda v: type(v) is dict,
    "array": lambda v: type(v) is list,
    "string": lambda v: type(v) is str,
    "integer": lambda v: type(v) is int,
    "number": lambda v: type(v) in (int, float),
    "boolean": lambda v: type(v) is bool,
    "null": lambda v: v is None,
}


def check_schema(value, schema: dict, where: str = "input") -> None:
    kinds = schema.get("type", [])
    kinds = [kinds] if isinstance(kinds, str) else kinds
    if kinds and not any(TYPES[k](value) for k in kinds):
        raise ValueError(where + ": invalid type")
    if "const" in schema and not same(value, schema["const"]):
        raise ValueError(where + ": invalid constant")
    if "enum" in schema and value not in schema["enum"]:
        raise ValueError(where + ": unsupported value")
    if type(value) in (int, float) and (
        not math.isfinite(value) or value < schema.get("minimum", -math.inf)
    ):
        raise ValueError(where + ": invalid quantity")
    if type(value) is str and "pattern" in schema and not re.fullmatch(schema["pattern"], value):
        raise ValueError(where + ": invalid format")
    if type(value) is dict:
        if not set(schema.get("required", [])) <= value.keys():
            raise ValueError(where + ": required field missing")
        for key, member in value.items():
            child = schema.get("properties", {}).get(key, schema.get("additionalProperties", {}))
            if child is False:
                raise ValueError(where + ": unexpected field " + key)
            if isinstance(child, dict):
                check_schema(member, child, where + "." + key)
    if type(value) is list:
        if len(value) < schema.get("minItems", 0):
            raise ValueError(where + ": too few items")
        for index, member in enumerate(value):
            check_schema(member, schema.get("items", {}), f"{where}[{index}]")


def schema(policy: dict, interface: str) -> dict:
    """Schemas come from the generated files, or from a compiled contract supplied directly."""
    return policy.get(interface + "_schema") or policy[f"normalized_{interface}_schema"]


def check_input(value: dict, policy: dict) -> None:
    check_schema(value, schema(policy, "input"))
    clock = datetime.fromisoformat(value["reference_time"])
    offset = clock.utcoffset()
    if offset is None or offset.total_seconds() != 0:
        raise ValueError("reference_time must be explicit UTC")
    units = policy["quantity_units"]
    for facts in [value["facts"], *[item["facts"] for item in value["history"]]]:
        for key in ("start_time", "end_time"):
            if facts[key] is not None and datetime.fromisoformat(facts[key]).tzinfo is None:
                raise ValueError("Normalized time must retain an explicit offset")
        for q in facts["quantities"]:
            if q["unit"] not in units[q["kind"]]:
                raise ValueError("Incompatible quantity kind/unit")
            if q["kind"] != "UNAVAILABLE" and q["value"] is None:
                raise ValueError("Numeric quantity requires a value")
            if q["kind"] == "ABSOLUTE_CURTAILMENT" and not q["basis"].strip():
                raise ValueError(
                    "Absolute curtailment requires its stated source capacity/time basis"
                )
            if q["kind"] == "SCHEDULED_TO_PCT_MDQ" and (q["value"] is None or q["value"] > 100):
                raise ValueError("Invalid scheduled-to MDQ quantity or unit")
            if q["kind"] == "UNAVAILABLE" and (q["value"] is not None or q["unit"] != "NONE"):
                raise ValueError("UNAVAILABLE is categorical, not an invented volume")


def source_end(text) -> datetime | None:
    """Parse a naive source end. A bare date ends at the next midnight; TBD is unknown."""
    if type(text) is not str:
        return None
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    if parsed.tzinfo is not None:
        return None
    return parsed + timedelta(days=1) if len(text) == 10 else parsed


def ended_in_any_timezone(value: dict, margin_hours: float) -> bool:
    facts = value["facts"]
    if facts["time_basis"] == "UTC":
        return False
    rows = facts.get("restrictions") or []
    raw = (
        [row["source_end"] for row in rows]
        if rows
        else [value["source"]["fields"].get("end_datetime")]
    )
    ends = [source_end(text) for text in raw]
    if None in ends or not ends:
        return False
    now = datetime.fromisoformat(value["reference_time"]).replace(tzinfo=None)
    return max(e for e in ends if e is not None) + timedelta(hours=margin_hours) <= now


def observations(value: dict, margin_hours: float = 14) -> dict:
    """Derived observations, as defined in spec.md, computed by the component."""
    notice, facts = value["notice"], value["facts"]
    by_id: dict = {}
    for entry in value["history"]:
        by_id.setdefault(entry["notice"]["notice_id"], entry)
    complete = len(by_id) == len(value["history"])
    chain, seen, cursor = [notice["status"]], {notice["notice_id"]}, notice["prior_notice_id"]
    while cursor is not None:
        if cursor in seen or cursor not in by_id:
            complete = False
            break
        seen.add(cursor)
        chain.append(by_id[cursor]["notice"]["status"])
        cursor = by_id[cursor]["notice"]["prior_notice_id"]
    predecessor = by_id.get(notice["prior_notice_id"])
    utc = facts["time_basis"] == "UTC"
    reference = datetime.fromisoformat(value["reference_time"])
    ended = (
        utc
        and facts["end_time"] is not None
        and datetime.fromisoformat(facts["end_time"]) <= reference
    )
    return {
        "history.complete": complete,
        "history.root_status": chain[-1],
        "history.statuses": chain,
        "predecessor.present": predecessor is not None,
        "predecessor.status": None if predecessor is None else predecessor["notice"]["status"],
        "predecessor.facts_equal": predecessor is not None and same(facts, predecessor["facts"]),
        "time.ended": ended,
        "time.current": utc and facts["start_time"] is not None and not ended,
        "time.ended_in_any_timezone": ended_in_any_timezone(value, margin_hours),
    }


class Evaluator:
    def __init__(self, value: dict, policy: dict):
        self.value, self.sets = value, policy["sets"]
        self.known = observations(value, policy.get("unresolved_time_margin_hours", 14))
        self.columns: dict[str, str] = {}

    def read(self, path: str, row: dict | None):
        if row is not None:
            return row[path]
        if path in self.known:
            return self.known[path]
        section, key = path.split(".", 1)
        default: list | None = [] if path == "facts.restrictions" else None
        return self.value[section].get(key, default)

    def test(self, node: dict, row: dict | None = None) -> bool:
        kind = node["op"]
        if kind == "otherwise":
            return True
        if kind == "and":
            return all(self.test(n, row) for n in node["args"])
        if kind == "or":
            return any(self.test(n, row) for n in node["args"])
        if kind == "not":
            return not self.test(node["arg"], row)
        if kind == "column":
            return self.columns.get(node["column"]) == node["value"]
        if kind == "any":
            return any(self.test(node["cond"], item) for item in self.read(node["path"], None))
        found = self.read(node["path"], row)
        if kind == "flag":
            return found is True
        if kind == "eq":
            return found == node["value"]
        members = self.sets[node["set"]]
        if kind == "in":
            return found in members
        if kind == "overlaps":
            return any(item in members for item in found)
        if kind == "within":
            return bool(found) and all(item in members for item in found)
        raise ValueError("Unsupported predicate node: " + kind)

    def features(self, predicates: list[dict]) -> dict:
        for row in predicates:
            if row["column"] not in self.columns and self.test(row["ast"]):
                self.columns[row["column"]] = row["value"]
        return dict(self.columns)


def decide(value: dict, policy: dict) -> tuple[dict, dict]:
    """Validate the input, then return (winning rule, column values)."""
    check_input(value, policy)
    features = Evaluator(value, policy).features(policy["predicates"])
    for rule in sorted(policy["rules"], key=lambda r: r["priority"]):
        if all(features[column] == wanted for column, wanted in rule["when"].items()):
            return rule, features
    raise ValueError("spec.md: spec-rules requires an unconditional fallback")
