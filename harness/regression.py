"""Per-system temporal comparison; paired deltas are a separate operation."""

from __future__ import annotations

import copy
import hashlib
import json


def semantic(case: dict) -> dict:
    output = copy.deepcopy(case.get("readback", case.get("output")))
    if isinstance(output, dict) and isinstance(output.get("notice"), dict):
        for key in ("scraped_at", "html_file", "source_url"):
            output["notice"].pop(key, None)
    return {"execution_outcome": case.get("outcome"), "observed_output": output}


def identity(result: dict) -> dict:
    if "comparison_identity" in result:
        return result["comparison_identity"]
    m = result.get("manifest", {})
    files = m.get("provenance", {}).get("files", {})
    return {
        "implementation": m.get("system"),
        "policy": files.get("spec.md"),
        "oracle": files.get("requirements/dataset.json"),
        "rules": files.get("requirements/requirements.yaml"),
        "evaluation": files.get("harness/gates.py"),
        "model": m.get("configured_model"),
        "protocol": m.get("execution_boundary"),
    }


def compare(previous: dict | None, current: dict) -> dict:
    result: dict = {
        "status": "UNKNOWN",
        "kind": "per-system temporal regression",
        "newly_passing": [],
        "newly_failing": [],
        "unchanged": [],
        "unexpected_differences": [],
        "requirements_affected": [],
        "added": [],
        "removed": [],
        "execution_errors": [],
        "noncomparable_reasons": [],
    }
    if previous is None:
        result["reason"] = "No identified prior result for this implementation"
        return result
    before_id, after_id = identity(previous), identity(current)
    for key in ("policy", "oracle", "rules", "evaluation", "protocol"):
        if (
            not before_id.get(key)
            or not after_id.get(key)
            or before_id.get(key) != after_id.get(key)
        ):
            result["noncomparable_reasons"].append("Missing or changed comparison identity: " + key)
    if before_id.get("inputs") != after_id.get("inputs"):
        result["noncomparable_reasons"].append("Changed frozen input identity")
    if before_id.get("inherited_inventory_observed") != after_id.get(
        "inherited_inventory_observed"
    ):
        result["noncomparable_reasons"].append(
            "Prior and current executable-inventory observations differ; missing historical inventory proof cannot be manufactured by reinterpretation"
        )
    result["identities"] = {
        "previous": before_id,
        "previous_reinterpretation": previous.get("reinterpretation_identity"),
        "current": after_id,
    }
    result["comparison_mapping"] = None
    result["delta_meaning"] = (
        "Descriptive differences only; no justified policy/evaluator mapping"
        if result["noncomparable_reasons"]
        else "Comparable assertion differences"
    )
    result["configuration_changes"] = {
        k: {"before": before_id.get(k), "after": after_id.get(k)}
        for k in set(before_id) | set(after_id)
        if before_id.get(k) != after_id.get(k)
    }

    def index(r):
        findings = [f for f in r["findings"] if f["gate"] != 3]
        pairs = {(f["requirement_id"], f["case_id"]): f for f in findings}
        if len(pairs) != len(findings):
            raise ValueError("Duplicate assertion identity")
        return pairs

    try:
        old, new = index(previous), index(current)
    except ValueError as exc:
        result.update(status="ERROR", reason=str(exc))
        return result
    affected = set()
    for key in sorted(old.keys() | new.keys()):
        name = "/".join(key)
        if key not in old:
            result["added"].append(name)
        elif key not in new:
            result["removed"].append(name)
        else:
            a, b = old[key], new[key]
            if b["status"] == "ERROR":
                result["execution_errors"].append(name)
            if b["status"] == "FAIL" and a["status"] != "FAIL":
                result["newly_failing"].append(name)
            elif b["status"] == "PASS" and a["status"] != "PASS":
                result["newly_passing"].append(name)
            elif a["status"] == b["status"] and a.get("observed") == b.get("observed"):
                result["unchanged"].append(name)
                continue
            else:
                result["unexpected_differences"].append(name)
        affected.add(key[0])
    old_cases = {c["case_id"]: c for c in previous.get("cases", [])}
    new_cases = {c["case_id"]: c for c in current.get("cases", [])}
    for id in sorted(old_cases.keys() - new_cases.keys()):
        result["removed"].append("case/" + id)
    for id in sorted(new_cases):
        c = new_cases[id]
        if c.get("outcome") != "SUCCESS":
            result["execution_errors"].append("case/" + id)
        if id in old_cases and semantic(old_cases[id]) != semantic(c):
            result["unexpected_differences"].append("output/" + id)
            affected.update(
                f["requirement_id"] for f in current["findings"] if f["case_id"].split(":")[0] == id
            )
    result["requirements_affected"] = sorted(affected)
    result["provenance_changed"] = before_id != after_id
    if result["noncomparable_reasons"]:
        result["status"] = "UNKNOWN"
    elif result["execution_errors"]:
        result["status"] = "ERROR"
    elif result["newly_failing"] or result["unexpected_differences"] or result["removed"]:
        result["status"] = "FAIL"
    elif result["added"]:
        result["status"] = "UNKNOWN"
    else:
        result["status"] = "PASS"
    return result


def fingerprint(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()
