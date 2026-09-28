"""Generic checks driven by requirement strategy and dataset annotations."""

from __future__ import annotations

import json
import math
import re
from dataclasses import asdict, dataclass
from typing import Any

from harness.runtime import ROOT, digest


@dataclass(frozen=True)
class Finding:
    requirement_id: str
    case_id: str
    gate: int
    strategy: str
    status: str
    severity: str
    expected: Any
    observed: Any
    risk: str
    evidence_refs: list[str]
    failure_domain: str | None
    confidence: str


def finding(
    req: dict,
    case: dict,
    status: str,
    observed: Any,
    expected: Any = None,
    domain: str | None = None,
) -> dict:
    return asdict(
        Finding(
            req["id"],
            case["case_id"],
            req["validation"]["gate"],
            req["validation"]["type"],
            status,
            req["severity"],
            req["expected"] if expected is None else expected,
            observed,
            req["rationale"],
            [case["evidence_ref"]],
            domain or ("BEHAVIORAL_FAILURE" if status == "FAIL" else None),
            "direct observation" if status in {"PASS", "FAIL"} else "not established",
        )
    )


def aggregate(statuses: list[str]) -> str:
    statuses = [status for status in statuses if status != "N/A"]
    if "ERROR" in statuses:
        return "ERROR"
    if "FAIL" in statuses:
        return "FAIL"
    if not statuses or "UNKNOWN" in statuses:
        return "UNKNOWN"
    return "PASS"


def normalized(value: Any) -> str:
    return re.sub(r"[^a-z0-9]", "", str(value).lower())


def expected_prior(case: dict) -> int | None:
    """Derive the obligation from verified input, never from persisted output."""
    if "trusted_input_notice" in case:
        return case["trusted_input_notice"]["prior_notice_id"]
    if "input" in case:
        from bs4 import BeautifulSoup

        path = (ROOT / case["input"]).resolve()
        if not path.is_relative_to(ROOT) or digest(path) != case["input_sha256"]:
            raise ValueError("Lineage input identity mismatch")
        node = BeautifulSoup(path.read_text(), "html.parser").find(
            id=lambda value: value and value.endswith("_lblPriorNotice")
        )
        if node is None:
            raise ValueError("Trusted lineage source field unavailable")
        value = node.get_text(strip=True)
        return int(value) if value else None
    raise ValueError("Trusted lineage input unavailable")


def selected(req: dict, case: dict) -> bool:
    check = req["validation"]["check"]
    params = req["validation"]["params"]
    if check == "classification":
        return case.get("category") == "labeled" and (
            "ids" not in params or case["notice_id"] in params["ids"]
        )
    if check == "field_values":
        return params["field"] in case.get("annotations", {}).get("fields", {})
    if check == "stored_idempotency":
        return case.get("category") in {"duplicate", "repeated_revision"}
    if check == "restart":
        return case.get("category") == "restart"
    if check == "revision":
        return case.get("category") in {"revision", "repeated_revision"}
    return True


def oracle_scope_problem(req: dict, case: dict) -> str | None:
    """Approval is conditional on source-supported facts and runtime preconditions."""
    support_path = req["validation"]["params"].get("oracle_support")
    if not support_path:
        return None
    registry = json.loads((ROOT / support_path).read_text())
    # Carry unchanged D6 annotation scope through its exact registered lineage.
    same_scope = registry["policy_id"] == req["policy_id"]
    if not same_scope:
        import yaml

        document = yaml.safe_load((ROOT / "requirements/requirements.yaml").read_text())
        # D6 sentences are unchanged apart from stable IDs/line presentation.
        baseline = json.loads(
            (ROOT / "context/decisions/011-classification-actionability.record.json").read_text()
        )
        same_scope = " ".join(document["policies"]["D6"].split()) == " ".join(
            baseline["approved_body"]["D6"].split()
        )
    if not same_scope or registry["dataset_sha256"] != digest(ROOT / "requirements/dataset.json"):
        return "Oracle registry policy/dataset identity mismatch"
    field = req["validation"]["params"].get("field")
    entries = registry["fields"] if field else registry["revisions"]
    supported = next(
        (
            entry
            for entry in entries
            if entry["notice_id"] == case["notice_id"]
            and entry["input_sha256"] == case["input_sha256"]
            and entry["status"] == "source-supported"
            and (not field or entry["field"] == field)
        ),
        None,
    )
    if supported is None:
        return "No verified source support for this input/oracle; NOT EVALUATED"
    if digest(ROOT / supported["source_path"]) != supported["input_sha256"]:
        return "Verified oracle source bytes have changed"
    if field:
        if supported["expected"] != case["annotations"]["fields"][field]:
            return "Annotation differs from its verified source support"
        return None
    if digest(ROOT / supported["prior_source_path"]) != supported["prior_source_sha256"]:
        return "Verified prior source bytes have changed"
    row = case["output"]["notice"]
    prior = row.get("prior_notice_id")
    if prior != supported["prior_notice_id"]:
        return "Revision prior differs from the source-supported oracle"
    history = {r["notice_id"]: r for r in case["state_before"]["notices"]}
    seen = {row["notice_id"]}
    while prior is not None:
        if prior in seen or prior not in history:
            return "Complete acyclic prior chain required; NOT EVALUATED"
        seen.add(prior)
        prior = history[prior].get("prior_notice_id")
    first = history[supported["prior_notice_id"]]
    if " ".join(first["body_text"].split()) != " ".join(row["body_text"].split()):
        return "Operational body differs; outside unchanged-revision oracle"
    return None


def check_case(req: dict, case: dict) -> dict | None:
    check = req["validation"]["check"]
    if check in {"out_of_scope", "integrity", "provenance", "regression"} or not selected(
        req, case
    ):
        return None
    if check == "field_values":
        flags = json.loads(case.get("output", {}).get("notice", {}).get("validity_flags", "[]"))
        extraction = (
            case.get("stages", {}).get("extraction", {}).get("scorable", "llm_extraction" in flags)
        )
        if not extraction:
            return finding(
                req,
                case,
                "ERROR",
                {"stage": "extraction", "scorable": False, "execution_outcome": case["outcome"]},
                domain=case["outcome"]
                if case["outcome"] != "SUCCESS"
                else "EXTRACTION_UNAVAILABLE",
            )
    observable = {
        "identity",
        "decision_shape",
        "quantities",
        "links",
        "persistence",
        "stored_idempotency",
        "restart",
        "lineage",
        "model_proof",
        "field_values",
    }
    if case["outcome"] != "SUCCESS" and not (case.get("output") and check in observable):
        return finding(
            req, case, "ERROR", {"execution_outcome": case["outcome"]}, domain=case["outcome"]
        )
    scope_problem = oracle_scope_problem(req, case)
    if scope_problem:
        return finding(req, case, "UNKNOWN", scope_problem, domain="UNKNOWN")
    output = case["output"]
    row, locations, restrictions = output["notice"], output["locations"], output["restrictions"]
    observed: Any = None
    expected: Any = None
    passed = False
    if check == "identity":
        observed, expected = row["notice_id"], case["notice_id"]
        passed = observed == expected and bool(case["input_sha256"])
    elif check == "decision_shape":
        if (
            case.get("stages", {}).get("classification", {}).get("scorable") is False
            or case["outcome"] != "SUCCESS"
        ):
            return finding(
                req,
                case,
                "N/A",
                "No usable semantic result; fallback fields do not establish decision validity",
            )
        score = row.get("confidence_score")
        flags = json.loads(row.get("validity_flags", "null"))
        passed = (
            type(row.get("is_signal")) in {int, bool}
            and row["is_signal"] in (0, 1)
            and type(score) in {int, float}
            and math.isfinite(score)
            and req["validation"]["params"]["confidence_min"]
            <= score
            <= req["validation"]["params"]["confidence_max"]
            and isinstance(flags, list)
            and bool(flags)
            and all(isinstance(f, str) for f in flags)
            and isinstance(locations, list)
            and isinstance(restrictions, list)
        )
        observed = {"is_signal": row.get("is_signal"), "confidence": score, "flags": flags}
    elif check == "quantities":
        problems = []
        for r in restrictions:
            value, unit = r.get("restriction_value"), r.get("restriction_unit")
            if value is not None and (
                type(value) not in {float, int}
                or not math.isfinite(value)
                or value < req["validation"]["params"]["minimum"]
                or not isinstance(unit, str)
                or not unit.strip()
            ):
                problems.append(r)
            elif (
                value is not None
                and r["restriction_type"] == "SCHEDULED_TO_PCT_MDQ"
                and value > req["validation"]["params"]["maximum_mdq"]
            ):
                problems.append(r)
        passed, observed = not problems, problems
    elif check == "links":
        indexes = [r["location_index"] for r in locations]
        passed = (
            len(indexes) == len(set(indexes))
            and all(r["notice_id"] == row["notice_id"] for r in locations + restrictions)
            and all(r["location_index"] in indexes for r in restrictions)
        )
        observed = {
            "location_indexes": indexes,
            "restriction_indexes": [r["location_index"] for r in restrictions],
        }
    elif check == "classification":
        from harness.captures import oracle

        expected = oracle()[case["notice_id"]]["expected_signal"]
        observed = bool(row["is_signal"])
        passed = observed == expected
    elif check == "field_values":
        field = req["validation"]["params"]["field"]
        expected = case["annotations"]["fields"][field]
        if field == "firm_mdq":
            observed = [
                r["restriction_value"]
                for r in restrictions
                if normalized(r["service_type"]) == "primaryfirm"
                and r["restriction_type"] == "SCHEDULED_TO_PCT_MDQ"
            ]
            passed = bool(observed) and all(v == expected for v in observed)
        else:
            key = {"segments": "segment", "zones": "zone"}[field]
            observed = [str(r[key]) for r in locations if r.get(key) is not None]
            passed = all(any(normalized(e) == normalized(o) for o in observed) for e in expected)
    elif check == "persistence":
        passed = case.get("reopened_state_equal", False) and any(
            r["notice_id"] == row["notice_id"] for r in case["state_after"]["notices"]
        )
        observed = {
            "insert": case.get("persistence_insert_succeeded"),
            "reopened_equal": case.get("reopened_state_equal"),
        }
    elif check in {"stored_idempotency", "restart"}:
        observed = {
            k: sum(r["notice_id"] == row["notice_id"] for r in case["state_after"][table])
            for k, table in [
                ("notices", "notices"),
                ("locations", "notice_locations"),
                ("restrictions", "notice_restrictions"),
            ]
        }
        expected = {"notices": 1, "locations": len(locations), "restrictions": len(restrictions)}
        passed = observed == expected
    elif check == "revision":
        observed, expected = bool(row["is_signal"]), False
        passed = observed == expected
    elif check == "lineage":
        prior = expected_prior(case)
        if row.get("prior_notice_id") != prior:
            return finding(
                req,
                case,
                "FAIL",
                {
                    "stored_prior": row.get("prior_notice_id"),
                    "field_present": "prior_notice_id" in row,
                },
                {"required_prior": prior},
            )
        if prior is None:
            return None
        if not any(r["notice_id"] == prior for r in case["state_before"]["notices"]):
            return finding(
                req,
                case,
                "UNKNOWN",
                {
                    "missing_prior": prior,
                    "availability": "present_in_corpus_not_loaded"
                    if prior in case.get("available_corpus_ids", [])
                    else "absent_from_available_corpus",
                },
                domain="UNKNOWN",
            )
        observed = [r["notice_id"] for r in case.get("notice_chain", [])]
        history = {r["notice_id"]: r for r in case["state_before"]["notices"]}
        expected = [row["notice_id"]]
        while prior is not None:
            if prior in expected or prior not in history:
                return finding(
                    req,
                    case,
                    "UNKNOWN",
                    {"reason": "Incomplete or cyclic available chain", "prior": prior},
                    domain="UNKNOWN",
                )
            expected.insert(0, prior)
            prior = history[prior].get("prior_notice_id")
        passed = observed == expected
    elif check == "model_proof":
        observed = {
            "calls": len(case["model_calls"]),
            "all_requests_identified": all(
                c["success"] and c.get("request_id") and c.get("response", {}).get("id")
                for c in case["model_calls"]
            ),
            "helper_results": case.get("helper_results", []),
        }
        passed = (
            bool(case["model_calls"])
            and observed["all_requests_identified"]
            and "llm_extraction" in json.loads(row["validity_flags"])
            and all(h.get("result") is not None for h in case.get("helper_results", []))
        )
    else:
        raise ValueError(f"No executable check: {check}")
    return finding(req, case, "PASS" if passed else "FAIL", observed, expected)


def evaluate(requirements: list[dict], cases: list[dict], manifest: dict) -> list[dict]:
    findings = []
    run_case = {"case_id": "run", "evidence_ref": "manifest.json"}
    for req in requirements:
        check = req["validation"]["check"]
        if check == "out_of_scope":
            findings.append(
                finding(
                    req,
                    run_case,
                    "UNKNOWN",
                    {
                        "approval": req["approval"],
                        "implementation_status": req["implementation_status"],
                        "check_status": req["check_status"],
                        "evaluation": "NOT EVALUATED: no complete executable check or sufficient fixture; implementation status is reported separately",
                    },
                    domain="UNKNOWN",
                )
            )
        elif check == "regression":
            continue
        elif check == "integrity":
            good = not manifest["integrity_after"]["changed"]
            findings.append(
                finding(
                    req,
                    run_case,
                    "PASS" if good else "ERROR",
                    manifest["integrity_after"],
                    domain=None if good else "HARNESS_FAILURE",
                )
            )
        elif check == "provenance":
            good = bool(manifest.get("provenance", {}).get("files")) and all(
                c.get("input_sha256") and "state_before" in c for c in cases
            )
            findings.append(
                finding(
                    req,
                    run_case,
                    "PASS" if good else "ERROR",
                    {"case_count": len(cases), "hashes_present": good},
                    domain=None if good else "HARNESS_FAILURE",
                )
            )
        else:
            before = len(findings)
            for case in cases:
                try:
                    result = check_case(req, case)
                except Exception as exc:
                    result = finding(
                        req,
                        case,
                        "ERROR",
                        {"check_error": type(exc).__name__},
                        domain="HARNESS_FAILURE",
                    )
                if result is not None:
                    findings.append(result)
            if before == len(findings):
                findings.append(
                    finding(
                        req, run_case, "UNKNOWN", "No applicable cases executed.", domain="UNKNOWN"
                    )
                )
    return findings
