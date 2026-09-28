"""Check per-ID specification fields and supported executable bindings; no NLP claims."""

from __future__ import annotations

from pathlib import Path

from harness.runtime import ROOT

FIELDS = {
    "Requirement": "statement",
    "Rationale": "rationale",
    "Severity": "severity",
    "Inputs / preconditions": "preconditions",
    "Expected behavior": "expected",
    "Forbidden behavior": "forbidden",
    "Deterministic or evaluative": "mode",
    "Governance": "governance",
    "Basis": "basis",
    "Approval": "approval",
    "Enforcement": "enforcement",
    "Implementation status": "implementation_status",
    "Check status": "check_status",
    "Demonstrated evidence": "demonstrated_evidence",
    "Source": "source",
    "Policy": "policy_id",
}
PARAMETERS = {
    "decision_shape": {"confidence_min", "confidence_max"},
    "quantities": {"minimum", "maximum_mdq"},
    "classification": {"ids"},
    "field_values": {"field", "oracle_support"},
    "revision": {"oracle_support"},
}


def load_requirements(path: Path = ROOT / "requirements/requirements.yaml") -> list[dict]:
    """Read requirements compiled from the sole editable spec; no two-way sync."""
    from harness.spec_compiler import compile_spec, fail, generated
    from harness.spec_ownership import verify

    contract = compile_spec(ROOT)
    expected = generated(contract, "requirements", contract["requirements_document"])
    if not path.exists() or path.read_text() != expected:
        raise fail(
            "requirements",
            "generated-output",
            1,
            "GENERATED_ARTIFACT_DRIFT: compile spec.md; manual requirement edits are refused",
        )
    verify(ROOT, contract)
    return contract["requirements_document"]["requirements"]
