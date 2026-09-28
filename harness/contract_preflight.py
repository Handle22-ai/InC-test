"""Collect independent contract refusals before executing any component."""

from __future__ import annotations

from pathlib import Path

from harness.runtime import digest, write_json
from harness.spec_compiler import fail


def refusal(exc: Exception) -> dict:
    reason = str(exc)
    code = next(
        (
            name
            for name in (
                "D_SENTENCE_CHANGED",
                "UNRECORDED_SPEC_CHANGE",
                "STALE_SPEC_PIN",
                "GENERATED_ARTIFACT_DRIFT",
                "UNAPPROVED_ASSUMPTION_CHANGE",
                "INVALID_REVIEW_RECORD",
                "INVALID_EVIDENCE_IDENTITY",
                "ACCEPTANCE_LOOSENED",
            )
            if name in reason
        ),
        "BOUNDARY_VIOLATION" if "BOUNDARY_VIOLATION" in reason else "SPECIFICATION_INTEGRITY_ERROR",
    )
    return {"gate": 1, "status": "ERROR", "code": code, "reason": reason}


def collect(root: Path, destination: Path) -> tuple[dict, dict | None]:
    from harness.input_contract_checks import run as check_input
    from harness.rule_invariants import evaluate, violation
    from harness.spec_compiler import compile_spec, refresh_for_gate
    from harness.spec_ownership import verify

    data: dict = {"findings": [], "preflight_identity": {"spec_sha256": digest(root / "spec.md")}}

    def attempt(function):
        try:
            return function()
        except (ValueError, OSError, KeyError, TypeError) as exc:
            data["findings"].append(refusal(exc))
            return None

    compiled = attempt(lambda: refresh_for_gate(root))
    if compiled is None:
        compiled = attempt(lambda: compile_spec(root))
    if compiled is None:
        return data, None
    data["preflight_identity"]["policy_id"] = compiled["policy_id"]
    data["preflight_identity"]["policy_version"] = compiled["requirements_document"][
        "policy_version"
    ]
    data["preflight_identity"]["scope"] = (
        "Known spec identity before components; unavailable comparison fields remain unverified"
    )
    checks = attempt(lambda: evaluate(compiled))
    if checks is not None:
        data["rule_invariants"] = checks
        data["rule_invariant_coverage"] = {
            status: sum(r["status"] == status for r in checks)
            for status in ("PASS", "FAIL", "UNKNOWN")
        }
        write_json(destination / "rule-invariants.json", checks)
        for row in checks:
            if row["status"] == "FAIL" or row["code"] == "D_SENTENCE_CHANGED":
                key = (row.get("references") or [row["id"]])[0]
                reason = (
                    violation(row)
                    if row["status"] == "FAIL"
                    else f"{row['sentence']} — {row['scope']}"
                )
                data["findings"].append(
                    {
                        "gate": 1,
                        "status": "ERROR",
                        "code": row["code"],
                        "row": key,
                        "spec_line": row["spec_line"],
                        "reason": str(fail("spec-checks", key, row["spec_line"], reason)),
                    }
                )
    from harness.spec_ownership import check_acceptance

    attempt(lambda: check_acceptance(root, compiled))
    receipt = attempt(lambda: verify(root, compiled))
    if receipt is not None:
        data["spec_read"] = receipt
    inputs = attempt(lambda: check_input(compiled, destination / "input-contract.json"))
    if inputs is not None:
        data["input_contract"] = inputs
        data["findings"].extend(inputs["findings"])
    return data, compiled
