"""Bounded contract derivation, retained evidence and spec-only package preparation."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import tempfile
import time
from pathlib import Path
from unittest.mock import patch

import anthropic
import yaml
from bs4 import BeautifulSoup

from harness import behavior_contract as behavior
from harness import live
from harness.adapter import InheritedAdapter, NoticeInput, database, llm_utils
from harness.captures import verified_capture
from harness.runtime import ROOT, create_run, digest, new_run, provenance, write_json
from harness.signal_evaluation import provider
from harness.storage_evaluation import CAPTURE
from rebuilt.normalized_classifier import classify


def fixtures() -> list[dict]:
    """Frozen witnesses are independently retained data, never derived from rules."""
    path = ROOT / "requirements/normalized-witnesses.json"
    reference = json.loads((ROOT / "context/authority-reference.json").read_text())
    if digest(path) != reference.get("normalized_witnesses_sha256"):
        raise ValueError(
            "Unregistered normalized witness edit; expectations must remain independent"
        )
    examples = json.loads(path.read_text())
    for example in examples:
        value = example["input"]
        if (
            hashlib.sha256(value["source"]["fields"]["body"].encode()).hexdigest()
            != value["source"]["sha256"]
        ):
            raise ValueError("Frozen witness source bytes do not match their identity")
        if example["prospective_expectation"] != example["prospective_action"]["classification"]:
            raise ValueError("Frozen witness has contradictory prospective expectations")
        if support := example.get("source_support"):
            if digest(ROOT / support["path"]) != support["sha256"]:
                raise ValueError("Frozen witness supporting source has changed")
    return examples


def evaluate_witness(contract: dict, example: dict) -> dict:
    observed = behavior.derive(contract, example["input"])
    contradiction = observed["action"] != example["prospective_action"]
    return {
        **copy.deepcopy(example),
        "active_expectation": observed,
        "builder_executed": False,
        "evaluation_status": "FAIL" if contradiction else "READY",
        "finding": {
            "code": "CONTRACT_CONTRADICTS_FIXTURE",
            "status": "FAIL",
            "fixture": example["id"],
            "requirements": example["requirements"],
            "expected": example["prospective_action"],
            "observed": observed["action"],
            "winning_rule": observed["rule"],
            "risk": "Active canonical rule contradicts an independently frozen witness; do not rewrite the expectation",
        }
        if contradiction
        else None,
    }


def evaluate_runtime_witness(contract: dict, example: dict) -> dict:
    """Observe the real classifier, then compare to separately frozen answers."""
    observation = evaluate_witness(contract, example)
    decision = classify(example["input"])
    expected = example["prospective_action"]
    outcome = {key: decision.proposal[key] for key in expected}
    observation["runtime"] = {"matched_rule": decision.matched_rule, "output": decision.proposal}
    if outcome != expected:
        observation["evaluation_status"] = "FAIL"
        observation["finding"] = {
            "code": "CONTRACT_CONTRADICTS_FIXTURE",
            "status": "FAIL",
            "fixture": example["id"],
            "requirements": example["requirements"],
            "expected": expected,
            "observed": outcome,
            "winning_rule": decision.matched_rule,
            "risk": "Runtime classification contradicts the frozen witness",
        }
    return observation


def synthetic_variant(contract: dict, *, kind: str) -> dict:
    variant = copy.deepcopy(contract)
    variant["policy_id"] = "SYNTHETIC-DERIVATION-ONLY-" + kind
    variant["variant_of"] = hashlib.sha256(
        json.dumps(contract, sort_keys=True).encode()
    ).hexdigest()
    if kind == "action":
        next(r for r in variant["rules"] if r["id"] == "BR-ROUTINE")["action"]["classification"] = (
            "UNRESOLVED"
        )
    elif kind == "bound":
        variant["bounds"]["OUTPUT-001.confidence_max"] *= 0.8
    elif kind == "precedence":
        next(r for r in variant["rules"] if r["id"] == "BR-ROUTINE")["priority"] = 5
    else:
        raise ValueError("Unsupported derivation demonstration")
    return variant


def derivations(contract: dict, examples: list[dict]) -> dict:
    selected = {x["id"]: x["input"] for x in examples}
    result: dict = {}
    for kind, witness in [
        ("action", "routine-negative"),
        ("precedence", "overlap-unusable-routine"),
    ]:
        variant = synthetic_variant(contract, kind=kind)
        result[kind] = {
            "variant": variant,
            "witness": witness,
            "before": behavior.derive(contract, selected[witness]),
            "after": behavior.derive(variant, selected[witness]),
            "assertion_code_changed": False,
            "approved_for_application": False,
        }
    variant = synthetic_variant(contract, kind="bound")
    name = "OUTPUT-001.confidence_max"
    lower, upper = variant["bounds"][name], contract["bounds"][name]
    witness = (lower + upper) / 2
    unchanged = lower / 2
    result["bound"] = {
        "variant": variant,
        "name": name,
        "original": upper,
        "variant_bound": lower,
        "distinguishing_observation": witness,
        "before": behavior.check_bound(contract, name, witness),
        "after": behavior.check_bound(variant, name, witness),
        "unchanged_witness": {
            "observation": unchanged,
            "before": behavior.check_bound(contract, name, unchanged),
            "after": behavior.check_bound(variant, name, unchanged),
        },
        "meaning": "Synthetic representation bound, not materiality threshold; valid observations need not all change",
    }
    controls = {}
    for mode in ["unregistered-action", "inconsistent-view"]:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "requirements").mkdir()
            (root / "context").mkdir()
            (root / "docs").mkdir()
            for path in [
                "spec.md",
                "requirements/rule-block.schema.json",
                "requirements/normalized-witnesses.json",
                "requirements/behavior.yaml",
                "requirements/signal-safety.yaml",
                "context/authority-reference.json",
                "docs/signal-contract.md",
            ]:
                (root / path).write_bytes((ROOT / path).read_bytes())
            if mode == "unregistered-action":
                altered = copy.deepcopy(contract)
                altered["rules"][0]["action"]["classification"] = "NON_SIGNAL"
                (root / "requirements/behavior.yaml").write_text(yaml.safe_dump(altered))
            else:
                (root / "docs/signal-contract.md").write_text("Inconsistent view")
            with (
                patch.object(behavior, "ROOT", root),
                patch.object(behavior, "CONTRACT", root / "requirements/behavior.yaml"),
            ):
                try:
                    behavior.load()
                except ValueError as exc:
                    controls[mode] = {"refused": True, "reason": str(exc)}
                else:
                    controls[mode] = {"refused": False}
    result["controls"] = controls
    return result


def prior_loaded(destination: Path) -> dict:
    """Actual inherited parser, same captured extraction response, empty vs loaded prior."""
    capture = verified_capture(CAPTURE)
    cases = {c["case_id"]: c for c in capture["cases"]}
    first, current = cases["46507"], cases["46732"]
    source = ROOT / current["input"]
    header = BeautifulSoup(source.read_bytes(), "html.parser").find(
        id=lambda v: v and v.endswith("lblPriorNotice")
    )
    if (
        header is None
        or header.get_text(strip=True) != "46507"
        or digest(source) != current["input_sha256"]
    ):
        raise ValueError("Supplied predecessor evidence is inconsistent")
    extraction = next(
        c["response"] for c in current["model_calls"] if c.get("request", {}).get("tools")
    )
    results = {}
    for mode in ["prior-loaded"]:
        folder = destination / mode
        folder.mkdir(parents=True)
        conn = database.init_db(str(folder / "state.sqlite"))
        try:
            if mode == "prior-loaded":
                database.insert_notice(
                    conn,
                    first["output"]["notice"],
                    first["output"]["locations"],
                    first["output"]["restrictions"],
                )
            stub = provider("root", "valid")

            def replay(**kwargs):
                if not kwargs.get("tools"):
                    raise RuntimeError(
                        "No fabricated helper response in historical extraction replay"
                    )
                response = anthropic.types.Message.model_validate(copy.deepcopy(extraction))
                response._request_id = "replayed-extraction-not-new-model-call"
                return response

            stub.messages.create = replay
            with (
                patch.object(llm_utils, "get_client", return_value=stub),
                patch.object(llm_utils, "_API_KEY", "synthetic-only"),
                patch.object(llm_utils, "_ENABLED", True),
                patch.object(live, "_remaining", None),
                patch.object(live, "_blocker", None),
            ):
                record = InheritedAdapter().process(
                    NoticeInput(mode, source, 46732), conn, folder / "case.json"
                )
            results[mode] = {
                "is_signal": record["output"]["notice"]["is_signal"],
                "score": record["output"]["notice"]["confidence_score"],
                "flags": json.loads(record["output"]["notice"]["validity_flags"]),
                "observed_prior_ids": [n["notice_id"] for n in record["state_before"]["notices"]],
                "execution_outcome": record["outcome"],
                "case": str((folder / "case.json").relative_to(ROOT)),
            }
        finally:
            conn.close()
    return {
        "kind": "new deterministic parser execution with replayed captured extraction; not a new model capture or runtime authorization",
        "source": str(source.relative_to(ROOT)),
        "source_sha256": digest(source),
        "source_prior_header": "46507",
        "prior_source": first["input"],
        "prior_sha256": first["input_sha256"],
        "capture": str(CAPTURE.relative_to(ROOT)),
        "capture_sha256": digest(CAPTURE),
        "cases": results,
        "prior_not_loaded_preserved": "evidence/correction/20260927T220352.636265Z/final-checks/registered-demo/rebuilt/cases/46732.json",
        "comparison_limit": "Only the captured extraction required by the loaded-prior path is replayed. No unavailable impact helper response is invented for the empty-prior path.",
        "corpus_absent_cases_preserved": ["46725→46705", "46881→46857"],
    }


def baseline_fallback() -> dict:
    source = ROOT / "evidence/legacy/20260926T185618.823020Z/results.json"
    data = verified_capture(source)
    case = next(c for c in data["cases"] if c["case_id"] == "46864")
    row = case["output"]["notice"]
    stored = next(n for n in case["state_after"]["notices"] if n["notice_id"] == 46864)
    return {
        "source": str(source.relative_to(ROOT)),
        "source_sha256": digest(source),
        "case_evidence": case["evidence_ref"],
        "outcome": case["outcome"],
        "label": True,
        "persisted_decision": stored["is_signal"],
        "persisted_score": stored["confidence_score"],
        "inherited_threshold": 0.5,
        "threshold_margin": stored["confidence_score"] - 0.5,
        "threshold_basis": "unchanged inherited design/validity documentation; not an approved materiality threshold",
        "helper_results": case["helper_results"],
        "validity_flags": json.loads(row["validity_flags"]),
        "meaning": "Unsafe normal-looking persisted positive with an unusable verdict; positive label means this is NOT a false positive; classification accuracy unscorable, extraction/state observable",
    }


def run(destination: Path) -> dict:
    contract = behavior.load()
    examples = fixtures()
    evaluated = []
    timings = []
    for example in examples:
        behavior.validate_input(example["input"])
        start = time.perf_counter_ns()
        observation = evaluate_runtime_witness(contract, example)
        elapsed = (time.perf_counter_ns() - start) / 1e6
        source = destination / example["input"]["source"]["bytes_reference"]
        source.parent.mkdir(exist_ok=True)
        source.write_text(example["input"]["source"]["fields"]["body"])
        evaluated.append(observation)
        timings.append({"fixture": example["id"], "derivation_ms": elapsed})
    write_json(destination / "builder-evaluation-fixtures.json", evaluated)
    write_json(destination / "timings.json", timings)
    findings = [example["finding"] for example in evaluated if example["finding"]]
    write_json(destination / "findings.json", findings)
    write_json(
        destination / "derivations.json",
        {"replacement": "spec-row scratch proofs; no writable canonical YAML"},
    )
    write_json(destination / "prior-loaded.json", prior_loaded(destination / "prior-loaded"))
    write_json(destination / "baseline-b-46864.json", baseline_fallback())
    result = {
        "status": "FAIL" if findings else "PASS",
        "classification": "CONTRACT_CONTRADICTS_FIXTURE"
        if findings
        else "CONTRACT_WITNESSES_AGREE",
        "findings": findings,
        "provenance": provenance(),
        "canonical_contract_sha256": digest(behavior.CONTRACT),
        "fixture_sha256": digest(destination / "builder-evaluation-fixtures.json"),
        "pending_rules": [r["id"] for r in contract["rules"] if r["status"] == "pending-owner"],
        "scope": "spec derivation and retained observation review; independent builder not run",
        "machine_derivation_ms": [x["derivation_ms"] for x in timings],
        "fixture_identity_excludes": ["timing", "run path", "provenance timestamps"],
        "latency_excludes": ["human response", "real provider", "network"],
        "evidence": str(destination.relative_to(ROOT)),
    }
    write_json(destination / "summary.json", result)
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--render", action="store_true")
    args = parser.parse_args()
    if args.render:
        from harness.spec_compiler import build

        build()
        return
    destination = create_run(args.output or new_run("specification-checks"))
    result = run(destination)
    print(
        json.dumps(
            {
                "measurement_completed": True,
                "status": result["status"],
                "classification": result["classification"],
                "pending_rules": result["pending_rules"],
                "builder_executed": False,
                "evidence": str(destination),
                "failure_evidence": str(destination / "summary.json"),
                "fixture_sha256": result["fixture_sha256"],
            }
        )
    )
    if result["status"] == "FAIL":
        raise SystemExit(2)


if __name__ == "__main__":
    main()
