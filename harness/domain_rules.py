"""The harness oracle: evaluates the spec-predicates table independently of the component."""

from __future__ import annotations

import copy
from datetime import datetime, timedelta

from harness.predicates import equal

FEATURE_ORDER = [
    "Format",
    "Oracle answer",
    "Conflict",
    "History",
    "Arriving status",
    "Prior",
    "Operational change",
    "Information-only",
    "Restriction",
    "Service class",
    "Source clock",
    "Restriction current",
]


def history(value: dict) -> dict:
    notice = value["notice"]
    prior = {p["notice"]["notice_id"]: p for p in value["history"]}
    seen = {notice["notice_id"]}
    key = notice["prior_notice_id"]
    statuses = [notice["status"]]
    complete = len(prior) == len(value["history"])
    while key is not None:
        if key in seen or key not in prior:
            complete = False
            break
        seen.add(key)
        statuses.append(prior[key]["notice"]["status"])
        key = prior[key]["notice"]["prior_notice_id"]
    return {
        "chain_complete": complete,
        "root_status": statuses[-1],
        "statuses": statuses,
        "predecessor": prior.get(notice["prior_notice_id"]),
    }


def derived(value: dict, margin: float = 14) -> dict:
    """Derived observations as defined in spec.md; the harness's own computation."""
    f = value["facts"]
    h = history(value)
    previous = h["predecessor"]
    resolved = f["time_basis"] == "UTC"
    ended = (
        resolved
        and f["end_time"] is not None
        and datetime.fromisoformat(f["end_time"]) <= datetime.fromisoformat(value["reference_time"])
    )
    return {
        "history.complete": h["chain_complete"],
        "history.root_status": h["root_status"],
        "history.statuses": h["statuses"],
        "predecessor.present": previous is not None,
        "predecessor.status": previous["notice"]["status"] if previous else None,
        "predecessor.facts_equal": previous is not None and equal(f, previous["facts"]),
        "time.ended": ended,
        "time.current": resolved and f["start_time"] is not None and not ended,
        "time.ended_in_any_timezone": _ended_everywhere(value, margin),
    }


def _naive_end(text) -> datetime | None:
    """A naive source end; a date alone ends at the following midnight."""
    if not isinstance(text, str):
        return None
    try:
        if len(text) == 10:
            return datetime.fromisoformat(text) + timedelta(days=1)
        moment = datetime.fromisoformat(text)
    except ValueError:
        return None
    return moment if moment.tzinfo is None else None


def _ended_everywhere(value: dict, margin: float) -> bool:
    f = value["facts"]
    if f["time_basis"] == "UTC":
        return False
    rows = f.get("restrictions", [])
    texts = (
        [r["source_end"] for r in rows] if rows else [value["source"]["fields"].get("end_datetime")]
    )
    parsed = [_naive_end(t) for t in texts]
    ends = [e for e in parsed if e is not None]
    if not ends or len(ends) != len(parsed):
        return False
    reference = datetime.fromisoformat(value["reference_time"]).replace(tzinfo=None)
    return max(ends) + timedelta(hours=margin) <= reference


def _read(value: dict, observations: dict, path: str):
    if path in observations:
        return observations[path]
    section, key = path.split(".", 1)
    if path == "facts.restrictions":
        return value[section].get(key, [])  # optional for v1 normalized witnesses
    return value[section][key]


def holds(tree: dict, value: dict, observations: dict, sets: dict, row: dict | None = None) -> bool:
    op = tree["op"]

    def get(path):
        return row[path] if row is not None else _read(value, observations, path)

    if op == "otherwise":
        return True
    if op == "and":
        return all(holds(t, value, observations, sets, row) for t in tree["args"])
    if op == "or":
        return any(holds(t, value, observations, sets, row) for t in tree["args"])
    if op == "not":
        return not holds(tree["arg"], value, observations, sets, row)
    if op == "column":
        return observations["column:" + tree["column"]] == tree["value"]
    if op == "any":
        return any(
            holds(tree["cond"], value, observations, sets, item)
            for item in _read(value, observations, tree["path"])
        )
    if op == "flag":
        return get(tree["path"]) is True
    if op == "eq":
        return get(tree["path"]) == tree["value"]
    if op == "in":
        return get(tree["path"]) in sets[tree["set"]]
    if op == "overlaps":
        return bool(set(get(tree["path"])) & set(sets[tree["set"]]))
    if op == "within":
        # An empty list is never "within" a set: no evidence is not firm evidence.
        values = set(get(tree["path"]))
        return bool(values) and values <= set(sets[tree["set"]])
    raise ValueError("unsupported predicate node " + op)


def observe(contract: dict, value: dict) -> dict:
    observations = derived(value, contract.get("unresolved_time_margin_hours", 14))
    features: dict = {}
    for row in contract["predicates"]:
        column = row["column"]
        if column in features:
            continue
        if holds(row["ast"], value, observations, contract["sets"]):
            features[column] = row["value"]
            observations["column:" + column] = row["value"]
    # Explanatory features only; no rule reads them.
    features["Arriving status"] = value["notice"]["status"]
    features["Prior"] = "PRESENT" if observations["predecessor.present"] else "ABSENT"
    features["Source clock"] = "RESOLVED" if value["facts"]["time_basis"] == "UTC" else "UNRESOLVED"
    return {key: features[key] for key in FEATURE_ORDER if key in features}


def explain(contract: dict, value: dict) -> list[dict]:
    observed = observe(contract, value)
    result = []
    for rule in sorted(contract["rules"], key=lambda r: r["priority"]):
        first = next(
            (
                {"condition": k, "required": v, "observed": observed[k]}
                for k, v in rule["when"].items()
                if observed[k] != v
            ),
            None,
        )
        result.append(
            {
                "rule": rule["id"],
                "spec_line": rule.get("spec_line"),
                "matched": first is None,
                "first_failed": first,
            }
        )
    return result


def derive(contract: dict, value: dict) -> dict:
    matches = [r["rule"] for r in explain(contract, value) if r["matched"]]
    if not matches:
        raise ValueError("spec.md: spec-rules requires an unconditional fallback")
    row = next(r for r in contract["rules"] if r["id"] == matches[0])
    return {
        "rule": row["id"],
        "action": copy.deepcopy(row["action"]),
        "matched_rules": matches,
        "features": observe(contract, value),
    }
