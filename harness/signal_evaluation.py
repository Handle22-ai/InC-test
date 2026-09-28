"""Execute parser -> actual report seams, with synthetic SDK responses and real SQLite."""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import anthropic

from harness import live
from harness.adapter import InheritedAdapter, NoticeInput, database, llm_utils, notice_parser
from harness.requirements import load_requirements
from harness.runtime import ROOT, create_run, digest, integrity, new_run, provenance, write_json
from rebuilt.signals import Authorization, RecommendationPublisher, SemanticEvidence

CONTRACT = ROOT / "requirements/signal-safety.yaml"
NOTICE_IDS = {
    "root": 800001,
    "unchanged_revision": 800002,
    "distinct": 800003,
    "extraction_failure": 800004,
    "missing_history": 800005,
    "unauthorized": 800006,
    "routine": 800007,
    "unsupported_format": 800008,
}


def load_contract() -> dict:
    from harness.behavior_contract import load

    contract = load()["state_safety"]
    requirements = {r["id"] for r in load_requirements()}
    if contract["version"] != 1 or not set(contract["requirements"]) <= requirements:
        raise ValueError("Unsupported signal-safety contract")
    if any(s["notice"] not in NOTICE_IDS for s in contract["steps"]):
        raise ValueError("Unsupported sequence generator")
    if any(k not in contract["relations"] for s in contract["steps"] for k in s["expected"]):
        raise ValueError("Unsupported relation")
    return contract


def fixture(name: str) -> str:
    if name == "unsupported_format":
        return "%PDF-1.4\nSynthetic unsupported document; no PDF extraction is implemented.\n"
    id = NOTICE_IDS[name]
    prior = (
        NOTICE_IDS["root"]
        if name == "unchanged_revision"
        else (899999 if name == "missing_history" else "")
    )
    status = "SUPERSEDE" if prior else "INITIATE"
    location = "8200" if name == "distinct" else "8100"
    body = f"LOC {location} Louisiana Zone. Secondary Firm UNAVAILABLE; current operational capacity restriction until further notice."
    if name == "routine":
        body = "Administrative project list update. No operational restriction or flow change."
    fields = {
        "Notice ID": id,
        "Notice Type Desc (1)": "CAPACITY CONSTRAINT",
        "Notice Stat Desc": status,
        "Prior Notice": prior,
        "Notice Eff Date/Time": "01/14/2026",
        "Notice End Date/Time": "",
        "Post Date/Time": "01/14/2026",
        "Subject": "Synthetic controlled notice",
    }
    return (
        "<html>"
        + "".join(f"<p>{k}: {v}</p>" for k, v in fields.items())
        + f"<p>Notice Text:</p><p>{body}</p></html>"
    )


def provider(name: str, mode: str):
    """A stub at the SDK boundary, not a label lookup or patched application decision."""

    def create(**kwargs):
        if "tools" in kwargs:
            data = {"information_only": mode == "information_only", "locations": []}
            if mode != "information_only":
                data["locations"] = [
                    {
                        "loc_codes": ["8200" if name == "distinct" else "8100"],
                        "loc_names": ["Synthetic constraint"],
                        "zones": ["Louisiana Zone"],
                        "segments": ["24"],
                        "system": None,
                        "restrictions": [
                            {
                                "service_type": "SECONDARY_INPATH_FIRM",
                                "restriction_type": "UNAVAILABLE",
                                "restriction_value": None,
                                "restriction_unit": None,
                                "flow_direction": "DELIVERY",
                                "start_datetime": "2026-01-14T00:00:00+00:00",
                                "end_datetime": "TBD",
                            }
                        ],
                    }
                ]
            content: list[dict] = (
                [{"type": "text", "text": "Extraction unavailable"}]
                if mode == "unavailable_extraction"
                else [
                    {
                        "type": "tool_use",
                        "id": "synthetic-tool",
                        "name": "extract_notice_data",
                        "input": data,
                    }
                ]
            )
        else:
            prompt = kwargs["messages"][0]["content"]
            # Deliberately wrong model suggestion for unchanged revisions. The D2
            # deterministic facts check, not this suggestion, must suppress publication.
            answer = (
                "YES"
                if "PRIOR NOTICE:" in prompt
                else ("No usable verdict" if mode == "unusable_impact" else "large")
            )
            content = [{"type": "text", "text": answer}]
        return anthropic.types.Message.model_validate(
            {
                "id": "synthetic-message",
                "type": "message",
                "role": "assistant",
                "model": "synthetic-provider",
                "content": content,
                "stop_reason": "end_turn",
                "usage": {"input_tokens": 1, "output_tokens": 1},
            }
        )

    return SimpleNamespace(messages=SimpleNamespace(create=create), close=lambda: None)


class FaultPublisher(RecommendationPublisher):
    fault = ""

    def _resolve(self, snapshot, auth, result):
        super()._resolve(snapshot, auth, result)
        if self.fault == "duplicate":
            result["initial_decision"] = bool(result["candidate_classification"])
        if self.fault == "never":
            result["initial_decision"] = False


def classification_scorable(decision: dict, semantic: SemanticEvidence) -> bool:
    """Scorable when spec.md's Oracle answer is USABLE for the normalized input (D5-008).

    Semantics the rules never read cannot make a classification unscorable. Without a
    normalized input (the inherited system, or a refused normalization) fall back to
    the semantic evidence itself.
    """
    normalized = decision.get("normalized_input")
    if not normalized:
        return semantic.refusal() is None
    from harness.domain_rules import observe
    from harness.spec_compiler import compile_spec

    features = observe(compile_spec(ROOT), normalized)
    return features["Format"] == "SUPPORTED" and features["Oracle answer"] == "USABLE"


def execute(contract: dict, destination: Path, implementation: str, fault: str = "") -> list[dict]:
    destination.mkdir(parents=True)
    connection = database.init_db(str(destination / "parser.sqlite"))
    publisher = (
        FaultPublisher(destination / "decisions.sqlite")
        if fault
        else RecommendationPublisher(destination / "decisions.sqlite")
    )
    if isinstance(publisher, FaultPublisher):
        publisher.fault = fault
    observations = []
    try:
        for step in contract["steps"]:
            started = time.perf_counter_ns()
            if step.get("restart"):
                connection.close()
                publisher.close()
                connection = database.init_db(str(destination / "parser.sqlite"))
                publisher = (
                    FaultPublisher(destination / "decisions.sqlite")
                    if fault
                    else RecommendationPublisher(destination / "decisions.sqlite")
                )
                if isinstance(publisher, FaultPublisher):
                    publisher.fault = fault
                if fault == "memory":
                    with publisher.conn:
                        publisher.conn.execute("DELETE FROM initial_decisions")
            folder = destination / step["id"]
            folder.mkdir()
            name = step["notice"]
            path = folder / ("input.pdf" if name == "unsupported_format" else "input.html")
            path.write_text(fixture(name))
            with (
                patch.object(
                    llm_utils,
                    "get_client",
                    return_value=provider(name, step.get("provider", "valid")),
                ),
                patch.object(llm_utils, "_API_KEY", "synthetic-only"),
                patch.object(llm_utils, "_ENABLED", True),
                patch.object(llm_utils, "_MODEL", "synthetic-provider"),
                patch.object(live, "_remaining", None),
                patch.object(live, "_blocker", None),
            ):
                record = InheritedAdapter().process(
                    NoticeInput(step["id"], path, NOTICE_IDS[name]),
                    connection,
                    folder / "parser.json",
                )
            auth = (
                Authorization(
                    "Synthetic fixture adjudicator (not real approval)",
                    NOTICE_IDS[name],
                    digest(path),
                    contract["reference_time"],
                    "MATERIAL",
                    True,
                    True,
                    str(path.relative_to(ROOT)),
                    "Synthetic firm service unavailability materially affects flow; actionability stipulated at the fixed reference time.",
                )
                if step.get("authorization", True)
                else None
            )
            semantic = SemanticEvidence(
                record["stages"]["extraction"]["scorable"],
                tuple((h["helper"], h["result"]) for h in record["helper_results"]),
                None if record["outcome"] == "SUCCESS" else record["outcome"],
                "application/pdf" if name == "unsupported_format" else "text/html",
            )
            report_path = folder / "signals.json"
            if implementation == "inherited":
                notice_parser.NoticeProcessor(str(folder)).save_signals_report(
                    [record["output"]], "signals.json"
                )
                decision = {
                    "disposition": "LEGACY_BINARY",
                    "reason": "NO_EXPLICIT_REFUSAL_CONTRACT",
                    "candidate_classification": bool(record["output"]["notice"]["is_signal"]),
                }
            else:
                decision = publisher.decide(
                    record["output"], digest(path), semantic, auth, contract["reference_time"]
                )
                publisher.save_signals_report([decision], report_path)
            # Passive: count every item actually produced by the application report.
            observed = {
                "step": step["id"],
                "machine_latency_ms": (time.perf_counter_ns() - started) / 1_000_000,
                "latency_scope": "parser + synthetic SDK + SQLite + report; no human/provider/network wait",
                "initial_count": len(json.loads(report_path.read_text())),
                "disposition": decision.get("publication_disposition", decision["disposition"]),
                "reason": decision.get("publication_reason", decision["reason"]),
                "extraction_scorable": semantic.extraction_usable
                and semantic.source_media_type
                in {"text/html", "application/vnd.ngpl.normalized+json"},
                "classification_scorable": classification_scorable(decision, semantic)
                if implementation != "inherited"
                else semantic.refusal() is None,
                "classification_presented_as_valid": decision["candidate_classification"]
                is not None,
                "decision": decision,
                "authorization": as_authorization(auth),
                "parser_evidence": f"{step['id']}/parser.json",
                "report": f"{step['id']}/signals.json",
            }
            write_json(folder / "observation.json", observed)
            observations.append(observed)
    finally:
        connection.close()
        publisher.close()
    return observations


def as_authorization(auth: Authorization | None) -> dict | None:
    from dataclasses import asdict

    return asdict(auth) if auth else None


def check(contract: dict, observations: list[dict]) -> list[dict]:
    by_id = {o["step"]: o for o in observations}
    requirements = {r["id"]: r for r in load_requirements()}
    findings = []
    for step in contract["steps"]:
        observation = by_id.get(step["id"], {})
        for relation, expected in step["expected"].items():
            rule = contract["relations"][relation]
            requirement = rule.get("requirement") or step["requirement"]
            actual = observation.get(rule["field"])
            kind = rule.get("kind", "behavior")
            if relation == "semantic_safety":
                usable = observation.get("classification_scorable")
                presented = observation.get("classification_presented_as_valid")
                count = observation.get("initial_count")
                actual = (
                    None
                    if usable is None or presented is None or count is None
                    else (usable or (not presented and count == 0))
                )
            if observation.get("disposition") == "LEGACY_BINARY" and relation in {
                "disposition",
                "reason",
            }:
                actual = None  # Observer vocabulary is not an application contract field.
            findings.append(
                {
                    "step": step["id"],
                    "requirement": requirement,
                    "gate": requirements[requirement]["validation"]["gate"],
                    "relation": relation,
                    "kind": kind,
                    "expected": expected,
                    "observed": actual,
                    "status": "UNKNOWN"
                    if actual is None
                    else "PASS"
                    if type(actual) is type(expected) and actual == expected
                    else "FAIL",
                }
            )
    return findings


def semantic_checks(observations: list[dict]) -> list[dict]:
    """Frozen boundary witnesses are separate from canonical runtime rules."""
    path = ROOT / "requirements/publisher-witnesses.json"
    reference = json.loads((ROOT / "context/authority-reference.json").read_text())
    if digest(path) != reference.get("publisher_witnesses_sha256"):
        raise ValueError("Unregistered publisher witness change")
    witnesses = json.loads(path.read_text())
    requirements = {row["id"]: row for row in load_requirements()}
    result = []
    for observation in observations:
        decision = observation["decision"]
        if "classifier_decision" not in decision:
            continue
        witness = witnesses[observation["step"]]
        expected = witness["expected"]
        actual = {key: decision[key] for key in expected}
        agreement = all(
            decision[key] == decision["classifier_decision"][key]
            for key in ("classification", "disposition", "reason_codes", "recommendation_allowed")
        )
        for requirement, relation, observed, target in [
            (witness["requirement"], "frozen_classifier_witness", actual, expected),
            ("OUTPUT-001", "classifier_publisher_semantic_agreement", agreement, True),
        ]:
            result.append(
                {
                    "step": observation["step"],
                    "requirement": requirement,
                    "gate": requirements[requirement]["validation"]["gate"],
                    "relation": relation,
                    "expected": target,
                    "observed": observed,
                    "status": "PASS" if observed == target else "FAIL",
                    "code": "CONTRACT_CONTRADICTS_FIXTURE"
                    if observed != target
                    else "FROZEN_WITNESS_MATCH"
                    if relation == "frozen_classifier_witness"
                    else "PUBLISHER_CLASSIFIER_CONSISTENT",
                }
            )
    return result


def run(destination: Path) -> dict:
    contract = load_contract()
    result = {
        "scope": contract["scope"],
        "kind": "downstream state/safety execution; extracted facts and helper proposals supplied by SDK stubs, not raw-text classification evidence",
        "contract_sha256": digest(CONTRACT),
        "provenance": provenance(),
        "application_files": {
            str(p.relative_to(ROOT)): digest(p) for p in (ROOT / "rebuilt").glob("*.py")
        },
        "implementations": {},
        "fault_controls": {},
    }
    for implementation in ("inherited", "candidate"):
        observations = execute(contract, destination / implementation, implementation)
        findings = check(contract, observations)
        semantic_findings = semantic_checks(observations)
        result["implementations"][implementation] = {
            "observations": observations,
            "findings": findings,
            "semantic_findings": semantic_findings,
            "status": "FAIL"
            if any(f["status"] == "FAIL" for f in findings + semantic_findings)
            else "PASS",
            "attribution": {
                "duplicate_recommendation_steps": [
                    f["step"]
                    for f in findings
                    if f["relation"] == "initial"
                    and f["status"] == "FAIL"
                    and f["step"] in {"B", "C", "D", "F"}
                ],
                "behavioral_findings": [
                    f for f in findings if f["status"] == "FAIL" and f["kind"] == "behavior"
                ],
                "output_contract_findings": [
                    f for f in findings if f["status"] == "FAIL" and f["kind"] == "output_contract"
                ],
                "interface_unavailable": [f for f in findings if f["status"] == "UNKNOWN"],
            },
        }
    for fault in ("duplicate", "never", "memory"):
        observations = execute(contract, destination / ("fault-" + fault), "candidate", fault)
        findings = check(contract, observations)
        result["fault_controls"][fault] = {
            "rejected": any(f["status"] == "FAIL" for f in findings),
            "findings": findings,
        }
    result["integrity_after"] = integrity()
    write_json(destination / "results.json", result)
    write_json(destination / "contract.json", contract)
    return result


def probe(record_path: Path, destination: Path) -> dict:
    """Execute the existing downstream publication boundary on one saved observation."""
    record = json.loads(record_path.read_text())
    semantic = SemanticEvidence(
        record["stages"]["extraction"]["scorable"],
        tuple((h["helper"], h["result"]) for h in record["helper_results"]),
        None if record["outcome"] == "SUCCESS" else record["outcome"],
        record.get("source_media_type", "text/html"),
    )
    publisher = RecommendationPublisher(destination / "state.sqlite")
    try:
        decision = publisher.decide(
            record["output"],
            record["input_sha256"],
            semantic,
            None,
            load_contract()["reference_time"],
        )
        emitted = publisher.save_signals_report([decision], destination / "signals.json")
    finally:
        publisher.close()
    result = {
        "kind": "single saved-proposal probe; no raw-text classifier or model executed",
        "source": str(record_path),
        "source_sha256": digest(record_path),
        "decision": decision,
        "recommendation_count": len(emitted),
        "authorization": "None supplied; probe cannot authorize recommendations",
        "semantic_safety": classification_scorable(decision, semantic)
        or (decision["candidate_classification"] is None and not emitted),
    }
    write_json(destination / "input.json", record)
    write_json(destination / "results.json", result)
    write_json(
        destination / "learning.json",
        {
            "status": "nonbinding retained observation; not a requirement or approval",
            "input": "input.json",
            "evidence": "results.json",
            "reason": decision.get("publication_reason", decision["reason"]),
            "requirement": "STATE-003"
            if classification_scorable(decision, semantic)
            else "SAFETY-001",
        },
    )
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    parser.add_argument(
        "--input", type=Path, help="Saved observation at the existing proposal/publication boundary"
    )
    args = parser.parse_args()
    output = create_run(args.output or new_run("signals"))
    if args.input:
        result = probe(args.input, output)
        print(
            json.dumps(
                {
                    "evidence": str(output / "results.json"),
                    "learning": str(output / "learning.json"),
                    "semantic_safety": result["semantic_safety"],
                }
            )
        )
        return 0 if result["semantic_safety"] else 2
    result = run(output)
    print(
        json.dumps(
            {
                "output": str(output),
                "failure_evidence": str(output / "results.json"),
                "inherited": result["implementations"]["inherited"]["status"],
                "candidate": result["implementations"]["candidate"]["status"],
                "faults_rejected": {k: v["rejected"] for k, v in result["fault_controls"].items()},
            }
        )
    )
    return (
        0
        if result["implementations"]["candidate"]["status"] == "PASS"
        and all(v["rejected"] for v in result["fault_controls"].values())
        else 2
    )


if __name__ == "__main__":
    raise SystemExit(main())
