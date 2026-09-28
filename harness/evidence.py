"""Render the review surface and retain failure candidates without altering policy."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

from harness.gates import aggregate
from harness.runtime import ROOT, digest, write_json


def measured(result: dict, findings: list[dict]) -> bool:
    """The measurement is valid when every model call was made and answered, the
    inherited files are unchanged and the harness itself did not fail. A usable call
    that returns an unusable verdict (MODEL_FAILURE) is the inherited system's own
    behavior: a finding, not an invalid measurement.
    """
    calls = [call for case in result["cases"] for call in case.get("model_calls", [])]
    return (
        bool(result["cases"])
        and all(call.get("success") for call in calls)
        and not result["manifest"]["integrity_after"]["changed"]
        and not any(f["failure_domain"] == "HARNESS_FAILURE" for f in findings)
    )


def metrics(cases: list[dict], findings: list[dict]) -> dict:
    labeled = [c for c in cases if c["category"] == "labeled"]
    valid = [c for c in labeled if c["outcome"] == "SUCCESS"]
    false_positive = [
        c["notice_id"]
        for c in valid
        if c["output"]["notice"]["is_signal"] and not c["annotations"]["expected_signal"]
    ]
    false_negative = [
        c["notice_id"]
        for c in valid
        if not c["output"]["notice"]["is_signal"] and c["annotations"]["expected_signal"]
    ]

    def failures(req):
        selected = [
            f for f in findings if f["requirement_id"] == req and f["status"] in {"PASS", "FAIL"}
        ]
        return {
            "coverage": "scored" if selected else "unscored",
            "scored_assertions": len(selected),
            "failures": [f["case_id"] for f in selected if f["status"] == "FAIL"]
            if selected
            else None,
        }

    return {
        "labeled_total": len(labeled),
        "labeled_valid": len(valid),
        "execution_failures": [
            {"case": c["case_id"], "domain": c["outcome"]}
            for c in cases
            if c["outcome"] != "SUCCESS"
        ],
        "correct": len(valid) - len(false_positive) - len(false_negative),
        "false_trading_signals": false_positive,
        "missed_labeled_signals": false_negative,
        "missed_critical_unplanned": failures("SIGNAL-003"),
        "routine_notices_incorrectly_signaled": failures("SIGNAL-002"),
        "duplicate_revision_classifications": failures("STATE-004"),
        "duplicate_delivered_signals": "UNKNOWN: no emission interface",
        "curtailment_volume_extraction_failures": failures("OUTPUT-004"),
        "pipeline_segment_extraction_failures": failures("OUTPUT-005"),
        "geography_extraction_failures": failures("OUTPUT-006"),
        "geographic_price_relevance": "UNKNOWN: no independent price-impact oracle",
        "ambiguous_unsupported_ood": {
            "observed_cases": [
                c["case_id"]
                for c in cases
                if c.get("category") in {"ood", "unsupported", "ambiguous"}
            ],
            "coverage": "scored"
            if any(c.get("category") in {"ood", "unsupported", "ambiguous"} for c in cases)
            else "unscored",
        },
    }


def render(run: Path, result: dict, requirements: list[dict]) -> None:
    fingerprints = result["manifest"]["provenance"]["files"]
    for path in ("spec.md", "requirements/requirements.yaml", "requirements/dataset.json"):
        if fingerprints.get(path) != digest(ROOT / path):
            raise ValueError(
                "Policy or dataset changed; cannot reinterpret this run with current rules"
            )
    policy_id = requirements[0]["policy_id"]
    unavailable = [r["id"] for r in requirements if r["check_status"] == "not_available"]
    if (run / "summary.json").exists() or (run / "summary.md").exists():
        raise FileExistsError("Never overwrite an existing report")
    findings = result["findings"]
    stats = metrics(result["cases"], findings)
    gates = {
        str(g): aggregate([f["status"] for f in findings if f["gate"] == g]) for g in (1, 2, 3)
    }
    coverage = []
    for req in requirements:
        selected = [f for f in findings if f["requirement_id"] == req["id"]]
        coverage.append(
            {
                "requirement_id": req["id"],
                "status": aggregate([f["status"] for f in selected]),
                "counts": dict(Counter(f["status"] for f in selected)),
                "strategy": req["validation"]["type"],
                "check": req["validation"]["check"],
                "governance": req["governance"],
                "approval": req["approval"],
                "enforcement": req["enforcement"],
                "implementation_status": req["implementation_status"],
                "check_status": req["check_status"],
            }
        )
    measurement_valid = measured(result, findings)
    summary = {
        "policy_id": policy_id,
        "measurement_valid": measurement_valid,
        "gates": gates,
        "metrics": stats,
        "coverage": coverage,
    }
    write_json(run / "summary.json", summary)
    blocking = [f for f in findings if f["status"] in {"FAIL", "ERROR"}]
    for f in blocking:
        name = f"{f['requirement_id']}-{f['case_id']}.json"
        retained = {
            **f,
            "input": next(
                (c["input"] for c in result["cases"] if c["case_id"] == f["case_id"]), None
            ),
            "evidence_run": str(run.relative_to(ROOT)),
            "possible_failure_domain": f["failure_domain"],
            "status": "candidate; no diagnosis or repair",
            "requirements_changed": False,
        }
        write_json(run / "failures" / name, retained)
        # Run-scoped durable memory retains all failures, never overwrites older runs.
        write_json(run / "regression-candidates" / name, retained)
    lines = [
        "# Inherited baseline evidence",
        "",
        f"Run: `{run.name}`. Measurement valid: **{measurement_valid}**.",
        f"Assessment policy: `{policy_id}`. Approval is distinct from implementation and proof.",
        "Valid measurement does not mean behavioral acceptance. No production or trading autonomy is authorized.",
        "",
        f"Gate 1 — contracts/invariants: **{gates['1']}**.",
        f"Gate 2 — trading behavior: **{gates['2']}**.",
        f"Gate 3 — regression/change: **{gates['3']}** (first baseline has no trusted comparator).",
        "",
        f"Labeled decisions: {stats['correct']}/{stats['labeled_valid']} correct among {stats['labeled_total']} supplied cases.",
        f"False signals: {stats['false_trading_signals']}; missed signals: {stats['missed_labeled_signals']}.",
        f"Critical/unplanned misses: {stats['missed_critical_unplanned']}; routine false signals: {stats['routine_notices_incorrectly_signaled']}.",
        f"Unchanged-revision signal classifications: {stats['duplicate_revision_classifications']}; delivered-alert duplication: UNKNOWN.",
        f"Field probe failures — volume: {stats['curtailment_volume_extraction_failures']}; segment: {stats['pipeline_segment_extraction_failures']}; zone: {stats['geography_extraction_failures']}.",
        f"Execution failures: {stats['execution_failures']}.",
        "",
        "## Blocking findings",
        "",
    ]
    lines += [
        f"- {f['requirement_id']} / {f['case_id']}: {f['status']}; {f['failure_domain']}. See `{f['evidence_refs'][0]}` and failure record."
        for f in blocking
    ] or ["None observed on executed checks."]
    lines += [
        "",
        "## Requirement coverage",
        "",
        "| Requirement | Status | Strategy / check | Approval / enforcement | Implementation / checks | Counts |",
        "|---|---|---|---|---|---|",
    ]
    lines += [
        f"| {c['requirement_id']} | {c['status']} | {c['strategy']} / {c['check']} | {c['approval']} / {c['enforcement']} | {c['implementation_status']} / {c['check_status']} | {c['counts']} |"
        for c in coverage
    ]
    lines += [
        "",
        "## Assumptions, unknowns and limits",
        "",
        f"Requirements without complete executable checks: {', '.join(unavailable)}. Their approval, implementation and check status are separate in the coverage table; absence of a check does not establish PASS.",
        "This is a small, previously calibrated dataset with no held-out population estimate. Model outputs are stochastic; one run is not a reliability bound.",
        "Field probes cover source-supported selected percentages, segments and zones only. This run does not establish complete extraction, malformed/OOD, PDF or live-scraper coverage.",
        "Missing-history and out-of-order traces are retained. Approved reconciliation/delivery requirements remain unimplemented; no external emission interface is available.",
        "Replay probe reopens SQLite; it is not a process-crash/atomic-delivery test. This evaluation does not establish fresh-agent maintenance completion.",
        "Historical label evaluation is separate from current alert authorization. Approved clock and actionability requirements still lack complete implementation and execution proof.",
        "Human code reads: none requested or reported; agent boundary discovery is documented in artifacts/repo_map.md and evidence/code_reads.md.",
        "Autonomy envelope: local evidence collection only. No source repair, label changes, trading actions, or readiness claim.",
        "",
        "## Traceability",
        "",
        "spec.md → requirements/requirements.yaml → validation.check in harness/gates.py → results.json findings → cases/*.json + raw model requests/responses + SQLite.",
        "manifest.json records hashes and runtime; summary.json holds structured metrics; failures/ retains findings; regression.json records the missing comparator.",
        "context/failures and context/regressions retain candidate records automatically. They do not approve new requirements.",
        "",
    ]
    report = "\n".join(lines)
    (run / "summary.md").write_text(report)


def main() -> None:
    from harness.requirements import load_requirements

    run = ROOT / json.loads((ROOT / "evidence/legacy/latest.json").read_text())["run"]
    render(run, json.loads((run / "results.json").read_text()), load_requirements())


if __name__ == "__main__":
    main()
