"""Current integrated executions over registered retained captures, without model calls."""

from __future__ import annotations

import json
from pathlib import Path

from harness.captures import evaluation_clock, oracle, store_before, verified_capture
from harness.requirements import load_requirements
from harness.runtime import ROOT, digest, write_json
from harness.signal_evaluation import classification_scorable
from rebuilt.signals import RecommendationPublisher, SemanticEvidence


def sources() -> list[tuple[str, dict]]:
    path = ROOT / "requirements/trading-evidence.json"
    reference = json.loads((ROOT / "context/authority-reference.json").read_text())
    if digest(path) != reference.get("trading_evidence_sha256"):
        raise ValueError("Unregistered trading-evidence scope")
    return [
        (name, verified_capture(ROOT / name)) for name in json.loads(path.read_text())["captures"]
    ]


def run(destination: Path) -> dict:
    destination.mkdir(parents=True, exist_ok=True)
    labels = oracle()
    requirements = {row["id"]: row for row in load_requirements()}
    result: dict = {
        "scope": "Current classifier -> stateful publisher executions over retained captured assertions. Correlated finite cases; no population accuracy, new extraction or recommendation authorization.",
        "sources": [],
        "observations": [],
        "findings": [],
        "metrics": {},
        "checks_not_applicable": [],
    }
    metrics: dict[str, list] = {
        key: []
        for key in (
            "supplied_label_false_positives",
            "labeled_positives_decided_non_signal",
            "labeled_positives_unresolved",
            "unscored_labeled",
            "routine_admin_signaled",
            "duplicate_replay_recommendations",
            "semantic_execution_refusals",
            "history_required_review",
            "labeled_scored",
            "labeled_total",
        )
    }
    acceptance = spec_acceptance()
    for index, (name, capture) in enumerate(sources()):
        folder = destination / f"capture-{index}"
        folder.mkdir()
        manifest = capture["manifest"]
        result["sources"].append(
            {
                "path": name,
                "sha256": digest(ROOT / name),
                "original_execution_identity": manifest,
                "reference_time": "per notice: its post_datetime (spec D3-011; see captures.evaluation_clock)",
                "current_action": "Re-executed classifier and publisher over these captured assertions; no original execution identity rewritten",
            }
        )
        latest: dict[int, dict] = {}  # most recent captured case per notice ID
        publisher: RecommendationPublisher | None = None
        try:
            for case in capture["cases"]:
                key = f"capture-{index}/{case['case_id']}"
                output = case["output"]
                clock, clock_basis = evaluation_clock(case, capture)
                semantic = semantic_evidence(case)
                # Each case starts from exactly the store it was captured with.
                publisher = RecommendationPublisher(folder / f"{case['case_id']}.sqlite")
                for prior_id in store_before(case):
                    prior = latest.get(prior_id)
                    if prior is not None:
                        try:
                            publisher.decide(
                                prior["output"],
                                prior["input_sha256"],
                                semantic_evidence(prior),
                                None,
                                evaluation_clock(prior, capture)[0],
                            )
                        except ValueError, KeyError, TypeError:
                            pass  # an unusable prior stays absent, exactly as in its own case
                if output.get("notice", {}).get("notice_id") is not None:
                    latest[output["notice"]["notice_id"]] = case
                try:
                    decision = publisher.decide(output, case["input_sha256"], semantic, None, clock)
                    emitted = publisher.save_signals_report(
                        [decision], folder / (case["case_id"] + "-report.json")
                    )
                    replay = publisher.decide(output, case["input_sha256"], semantic, None, clock)
                    repeated = publisher.save_signals_report(
                        [replay], folder / (case["case_id"] + "-replay.json")
                    )
                except (ValueError, KeyError, TypeError) as exc:
                    decision = {
                        "classification": "UNRESOLVED",
                        "disposition": "ERROR",
                        "reason": "NORMALIZED_INPUT_REFUSED",
                        "error_type": type(exc).__name__,
                        "error_reason": str(exc),
                        "initial_decision": False,
                        "normalization_gaps": [str(exc)],
                    }
                    emitted, repeated = [], []
                predicted = decision["classification"]
                labeled = case.get("category") == "labeled"
                expected = labels[case["notice_id"]]["expected_signal"] if labeled else None
                observation = {
                    "id": key,
                    "case_id": case["case_id"],
                    "notice_id": case["notice_id"],
                    "source_capture": name,
                    "source_input": case["input"],
                    "input_sha256": case["input_sha256"],
                    "category": case.get("category"),
                    "expected_signal": expected,
                    "inherited_signal": output["notice"].get("is_signal"),
                    "inherited_execution": case["outcome"],
                    "inherited_system": manifest["system"],
                    "decision": decision,
                    "recommendation_count": len(emitted),
                    "replay_recommendation_count": len(repeated),
                    "evaluation_clock": {"reference_time": clock, "basis": clock_basis},
                    "authorization": "None; evaluation labels never authorize publication",
                }
                result["observations"].append(observation)
                write_json(folder / (case["case_id"] + "-observation.json"), observation)
                scorable = classification_scorable(decision, semantic)
                controls = [
                    ("STATE-003", "UNAUTHORIZED_PUBLICATION", not emitted and not repeated),
                    ("STATE-002", "DUPLICATE_REPLAY_PUBLICATION", not repeated),
                    (
                        "SAFETY-001",
                        "UNUSABLE_SEMANTICS_REFUSED",
                        scorable or (predicted == "UNRESOLVED" and not emitted),
                    ),
                ]
                for requirement, code, passed in controls:
                    if passed and (
                        code in {"UNAUTHORIZED_PUBLICATION", "DUPLICATE_REPLAY_PUBLICATION"}
                        or scorable
                    ):
                        result["checks_not_applicable"].append(
                            {
                                "requirement": requirement,
                                "case": key,
                                "code": code,
                                "reason": "No authorized initial publication to replay"
                                if code != "UNUSABLE_SEMANTICS_REFUSED"
                                else "No semantic failure on this case",
                            }
                        )
                        continue
                    req = requirements[requirement]
                    result["findings"].append(
                        {
                            "requirement": requirement,
                            "gate": req["validation"]["gate"],
                            "case": key,
                            "status": "PASS" if passed else "FAIL",
                            "code": code,
                            "observed": passed,
                        }
                    )
                req = requirements["INPUT-001"]
                if decision.get("notice_id") is not None:  # refused inputs produce no identity
                    result["findings"].append(
                        {
                            "requirement": "INPUT-001",
                            "gate": req["validation"]["gate"],
                            "case": key,
                            "status": "PASS"
                            if decision.get("notice_id") == case["notice_id"]
                            and decision.get("source_sha256", case["input_sha256"])
                            == case["input_sha256"]
                            else "FAIL",
                            "code": "OUTPUT_IDENTITY",
                        }
                    )
                if labeled:
                    metrics["labeled_total"].append(key)
                    metrics[
                        "unscored_labeled" if predicted == "UNRESOLVED" else "labeled_scored"
                    ].append(key)
                    if expected is False and predicted == "SIGNAL_CANDIDATE":
                        metrics["supplied_label_false_positives"].append(key)
                    if expected is True and predicted == "NON_SIGNAL":
                        metrics["labeled_positives_decided_non_signal"].append(key)
                    if expected is True and predicted == "UNRESOLVED":
                        # Sent to review: a miss for the desk (audit 5 #2), not a decided negative.
                        metrics["labeled_positives_unresolved"].append(key)
                    status = (
                        ("COUNTED" if acceptance else "UNKNOWN")
                        if predicted == "UNRESOLVED"
                        else "PASS"
                        if (predicted == "SIGNAL_CANDIDATE") == expected
                        else "FAIL"
                    )
                    req = requirements["SIGNAL-001"]
                    result["findings"].append(
                        {
                            "requirement": req["id"],
                            "gate": req["validation"]["gate"],
                            "case": key,
                            "status": status,
                            "code": {
                                "COUNTED": "LABEL_UNRESOLVED_COUNTED",
                                "UNKNOWN": "CAPTURED_LABEL_UNSCORED",
                            }.get(status, "SUPPLIED_LABEL_COMPARISON"),
                            "expected": expected,
                            "observed": predicted,
                        }
                    )
                # Named classification obligations use their declared source examples.
                # Synthetic witnesses remain separate and cannot establish this coverage.
                for requirement in ("SIGNAL-002", "SIGNAL-003", "SIGNAL-004"):
                    selected = requirements[requirement]["validation"]["params"].get("ids", [])
                    if labeled and case["notice_id"] in selected:
                        declared, code = status, "DECLARED_CASE_COMPARISON"
                        if predicted == "UNRESOLVED" and not acceptance:
                            declared, code = "UNKNOWN", "DECLARED_CASE_UNSCORED"
                        elif predicted == "UNRESOLVED" and requirement in acceptance.get(
                            "review_satisfies", []
                        ):
                            declared, code = "PASS", "DECLARED_CASE_REVIEW_AS_SPECIFIED"
                        elif predicted == "UNRESOLVED":
                            declared, code = "FAIL", "DECLARED_CASE_UNRESOLVED"
                        result["findings"].append(
                            {
                                "requirement": requirement,
                                "gate": 2,
                                "case": key,
                                "status": declared,
                                "code": code,
                                "expected": expected,
                                "observed": predicted,
                            }
                        )
                # Independently source-supported field annotations evaluate the shared
                # retained upstream extraction, not a new model run or downstream classifier.
                from harness.gates import check_case

                for field_requirement in requirements.values():
                    if field_requirement["validation"]["check"] not in {
                        "field_values",
                        "quantities",
                        "links",
                    }:
                        continue
                    field_result = check_case(field_requirement, case)
                    if field_result is not None:
                        result["findings"].append(
                            {
                                "requirement": field_requirement["id"],
                                "gate": field_requirement["validation"]["gate"],
                                "case": key,
                                "status": field_result["status"],
                                "code": "CAPTURED_UPSTREAM_EXTRACTION",
                                "field": field_requirement["validation"]["params"].get(
                                    "field", field_requirement["validation"]["check"]
                                ),
                                "expected": field_result["expected"],
                                "observed": field_result["observed"],
                                "scope": "Shared retained upstream extraction; source-supported annotation and stage availability checked. Not new extraction by the rebuilt classifier.",
                            }
                        )
                if decision.get("normalized_input", {}).get("facts", {}).get("content_kind") in {
                    "ADMINISTRATIVE",
                    "INFORMATIONAL",
                } and (predicted == "SIGNAL_CANDIDATE" or emitted):
                    metrics["routine_admin_signaled"].append(key)
                    req = requirements["SIGNAL-002"]
                    result["findings"].append(
                        {
                            "requirement": req["id"],
                            "gate": req["validation"]["gate"],
                            "case": key,
                            "status": "FAIL",
                            "code": "ROUTINE_ADMIN_SIGNALED",
                            "observed": predicted,
                        }
                    )
                if repeated:
                    metrics["duplicate_replay_recommendations"].append(key)
                if decision["disposition"] == "ERROR":
                    metrics["semantic_execution_refusals"].append(key)
                if decision.get("matched_rule") == "BR-HISTORY":
                    metrics["history_required_review"].append(key)
                publisher.close()
                publisher = None
        finally:
            if publisher is not None:
                publisher.close()
    result["label_outcomes"] = []
    result["label_summaries"] = []
    for index, source in enumerate(result["sources"]):
        labeled = [
            o
            for o in result["observations"]
            if o["category"] == "labeled" and o["id"].startswith(f"capture-{index}/")
        ]
        counts = {"positive": 0, "negative": 0, "unresolved": 0, "error": 0}
        for row in labeled:
            decision = row["decision"]
            outcome = (
                "error"
                if decision["disposition"] == "ERROR"
                else "positive"
                if decision["classification"] == "SIGNAL_CANDIDATE"
                else "negative"
                if decision["classification"] == "NON_SIGNAL"
                else "unresolved"
            )
            counts[outcome] += 1
            result["label_outcomes"].append(
                {
                    "id": row["id"],
                    "notice_id": row["notice_id"],
                    "label": row["expected_signal"],
                    "outcome": outcome,
                    "classification": decision["classification"],
                    "rule": decision.get("matched_rule"),
                    "time_basis": decision.get("normalized_input", {})
                    .get("facts", {})
                    .get("time_basis"),
                    "publication_disposition": decision.get(
                        "publication_disposition", decision["disposition"]
                    ),
                    "recommendation_allowed": decision.get("recommendation_allowed", False),
                }
            )
        result["label_summaries"].append(
            {
                "capture": index,
                "source": source["path"],
                "denominator": len(labeled),
                "scored": counts["positive"] + counts["negative"],
                **counts,
                "scope": "Primary fixed 14-label capture"
                if index == 0
                else "Secondary fixed 14-label replay, reported separately",
            }
        )
    result["capture_differences"] = capture_differences(result)
    result["replay_reconciliation"] = replay_reconciliation(result)
    from harness.proposals import summaries

    cases = [
        {
            "id": r["id"],
            "expected_signal": r["expected_signal"],
            "outcome": {"action": r["decision"]},
            "inherited_signal": r["inherited_signal"],
            "inherited_execution": r["inherited_execution"],
            "inherited_system": r["inherited_system"],
        }
        for r in result["observations"]
    ]
    result["tradeoffs"] = {
        "rebuilt": summaries(cases),
        "inherited": summaries(cases, inherited=True),
    }
    result["metrics"] = {key: {"count": len(ids), "cases": ids} for key, ids in metrics.items()}
    result["acceptance"] = acceptance
    if acceptance:
        result["findings"].extend(budget_findings(result, acceptance, requirements))
    result["metric_definitions"] = {
        "false_negatives": "labeled_positives_decided_non_signal counts positives classified NON_SIGNAL; labeled_positives_unresolved counts positives sent to review. Both are misses for the Gate 2 budget; neither is credited correct.",
        "replay": "Unauthenticated captured scenarios cannot prove positive publication; the separately identified synthetic A–F sequence supplies positive authorization controls.",
        "critical": "Critical source flag on unscored labeled cases; not a new materiality label.",
        "counts": "Each capture/case is counted separately; repeated source notices across captures are not independent samples.",
    }
    write_json(destination / "results.json", result)
    return result


def spec_acceptance() -> dict:
    """Gate 2 acceptance budgets declared in spec-settings; empty for older specs."""
    from harness.spec_compiler import compile_spec

    return compile_spec(ROOT).get("acceptance", {})


def budget_findings(result: dict, acceptance: dict, requirements: dict) -> list[dict]:
    """Per capture: labeled positives not candidated, and labeled negatives candidated.

    An unresolved positive is a miss for the desk even though it is sent to review.
    """
    gate = requirements["SIGNAL-001"]["validation"]["gate"]
    rows = []
    for index, _ in enumerate(result["sources"]):
        labeled = [
            o
            for o in result["observations"]
            if o["category"] == "labeled" and o["id"].startswith(f"capture-{index}/")
        ]
        candidate = [o for o in labeled if o["decision"]["classification"] == "SIGNAL_CANDIDATE"]
        missed = [o["id"] for o in labeled if o["expected_signal"] and o not in candidate]
        false = [o["id"] for o in candidate if o["expected_signal"] is False]
        for code, cases, limit in (
            ("LABELED_MISSED_POSITIVES", missed, acceptance["max_missed_positives_per_capture"]),
            ("LABELED_FALSE_POSITIVES", false, acceptance["max_false_positives_per_capture"]),
        ):
            rows.append(
                {
                    "requirement": "SIGNAL-001",
                    "gate": gate,
                    "case": f"capture-{index}",
                    "status": "PASS" if len(cases) <= limit else "FAIL",
                    "code": code,
                    "observed": len(cases),
                    "limit": limit,
                    "cases": cases,
                }
            )
    return rows


def semantic_evidence(case: dict) -> SemanticEvidence:
    flags = json.loads(case["output"].get("notice", {}).get("validity_flags", "[]"))
    return SemanticEvidence(
        case.get("stages", {}).get("extraction", {}).get("scorable", "llm_extraction" in flags),
        tuple((row["helper"], row["result"]) for row in case.get("helper_results", [])),
        None if case["outcome"] == "SUCCESS" else case["outcome"],
    )


def capture_differences(result: dict) -> list[dict]:
    """Labeled notices whose inherited execution or rebuilt decision differs across captures.

    Captures of the same notices are repeated runs of the inherited system (different
    token budget, model or date). Where they disagree, the notice depends on the run.
    """
    rows: dict[int, dict] = {}
    for o in result["observations"]:
        if o["category"] != "labeled":
            continue
        capture = o["id"].split("/")[0]
        rows.setdefault(
            o["notice_id"],
            {"notice_id": o["notice_id"], "label": o["expected_signal"], "captures": {}},
        )
        rows[o["notice_id"]]["captures"][capture] = {
            "inherited": o["inherited_execution"]
            if o["inherited_execution"] != "SUCCESS"
            else ("signal" if o["inherited_signal"] else "no signal"),
            "rebuilt": o["decision"]["classification"],
        }
    return [
        row
        for _, row in sorted(rows.items())
        if len({json.dumps(v, sort_keys=True) for v in row["captures"].values()}) > 1
    ]


# Scenario cases in every real-model capture that mirror a synthetic replay step.
# "Signal" is what the inherited system itself output on that case (is_signal).
MIRRORED = {
    "B identical reprocessing": ("duplicate-input", True),
    "D/F reprocessing after restart": ("restart-replay", True),
    "C unchanged revision": ("unchanged-revision", True),
    "C repeated revision": ("repeated-revision", True),
    "missing-history": ("missing-prior", True),
}


def replay_reconciliation(result: dict) -> list[dict]:
    """Which synthetic-replay failures of the inherited system the real captures reproduce."""
    by_case: dict[str, list[dict]] = {}
    for o in result["observations"]:
        by_case.setdefault(o["case_id"], []).append(o)
    rows = []
    for step, (case_id, failure_if_signal) in MIRRORED.items():
        runs = by_case.get(case_id, [])
        signals = [bool(o["inherited_signal"]) == failure_if_signal for o in runs]
        rows.append(
            {
                "replay_step": step,
                "real_case": case_id,
                "real_runs": len(runs),
                "reproduced_in": sum(signals),
                "outcomes": [
                    f"{o['id'].split('/')[0]}: {'signal' if o['inherited_signal'] else 'no signal'}"
                    + (
                        ""
                        if o["inherited_execution"] == "SUCCESS"
                        else f" ({o['inherited_execution']})"
                    )
                    for o in runs
                ],
            }
        )
    failed = [o for o in result["observations"] if o["inherited_execution"] == "MODEL_FAILURE"]
    rows.append(
        {
            "replay_step": "unusable-impact (verdict failed, still signals)",
            "real_case": "every case whose real verdict failed",
            "real_runs": len(failed),
            "reproduced_in": sum(bool(o["inherited_signal"]) for o in failed),
            "outcomes": [
                f"{o['id']}: {'signal' if o['inherited_signal'] else 'no signal'}" for o in failed
            ],
        }
    )
    return rows
