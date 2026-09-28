"""Paired deterministic evaluation of current storage using frozen real parser outputs."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import tempfile
from collections.abc import Callable
from pathlib import Path

from harness.captures import verified_capture, with_oracle
from harness.gates import aggregate, check_case, evaluate, finding
from harness.regression import compare as temporal_compare
from harness.requirements import load_requirements
from harness.runtime import (
    ROOT,
    digest,
    integrity,
    new_run,
    provenance,
    validate_output,
    write_json,
)
from harness.storage_ports import (
    CapturedPayload,
    InheritedStorage,
    RebuiltStorage,
    StoragePort,
    readback,
)

CAPTURE = ROOT / "evidence/candidates/impact-budget-512/full/20260926T191722.363460Z/results.json"
STORAGE_IDS = {
    "INPUT-001",
    "OUTPUT-003",
    "STATE-001",
    "STATE-002",
    "STATE-006",
    "HISTORY-001",
    "OBS-001",
    "OBS-002",
}


def fingerprint(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, allow_nan=False).encode()).hexdigest()


def fixtures_from_capture(path: Path = CAPTURE) -> list[dict]:
    capture = verified_capture(path)
    by_id = {case["case_id"]: case for case in capture["cases"]}
    fixtures = []

    def add(source: str, case_id: str, category: str, group: str) -> None:
        case = by_id[source]
        if not case.get("output"):
            raise ValueError("Capture has no observable storage input")
        fixtures.append(
            {
                "case_id": case_id,
                "category": category,
                "group": group,
                "notice_id": case["notice_id"],
                "input_sha256": case["input_sha256"],
                "output": case["output"],
                "annotations": case.get("annotations", {}),
                "capture_ref": str(path.parent.relative_to(ROOT) / case["evidence_ref"]),
                "capture_sha256": digest(path.parent / case["evidence_ref"]),
                "synthetic": case["notice_id"] == 96624,
                "semantic_outcome": case["outcome"],
            }
        )

    for case in capture["cases"]:
        if case["category"] == "labeled":
            add(case["case_id"], case["case_id"], "labeled", f"label-{case['case_id']}")
    for source, case_id, category in [
        ("duplicate-seed", "seed", "seed"),
        ("duplicate-seed", "duplicate-input", "duplicate"),
        ("duplicate-seed", "restart-replay", "restart"),
        ("unchanged-revision", "unchanged-revision", "revision"),
        ("unchanged-revision", "repeated-revision", "repeated_revision"),
    ]:
        add(source, case_id, category, "replay-and-revision")
    add("46507", "available-prior", "seed", "available-history")
    add("46732", "termination-with-prior", "history", "available-history")
    return fixtures


def run_system(
    factory: Callable[[Path], StoragePort], fixtures: list[dict], destination: Path
) -> list[dict]:
    """Each group starts empty. Every operation closes/reopens; no cross-run database."""
    cases = []
    with tempfile.TemporaryDirectory(prefix="notice-storage-") as directory:
        for fixture in fixtures:
            # Shared harness envelope validation only; no rebuilt business rules.
            if (
                not all(
                    re.fullmatch(r"[A-Za-z0-9_-]+", str(fixture.get(key, "")))
                    for key in ("case_id", "group")
                )
                or not isinstance(fixture.get("output"), dict)
                or not isinstance(fixture["output"].get("notice"), dict)
                or not all(
                    isinstance(fixture["output"].get(k), list)
                    for k in ("locations", "restrictions")
                )
            ):
                raise ValueError(
                    "HARNESS_FAILURE: invalid shared fixture envelope; no store invoked"
                )
            path = Path(directory) / f"{fixture['group']}.sqlite"
            port: StoragePort = factory(path)
            case = {
                **fixture,
                "trusted_input_notice": fixture["output"]["notice"],
                "evidence_ref": f"cases/{fixture['case_id']}.json",
                "state_before": port.state(),
                "outcome": "UNKNOWN",
                "execution_kind": "frozen normalized snapshot; no new model execution",
                "available_corpus_ids": sorted({f["notice_id"] for f in fixtures}),
            }
            try:
                snapshot = CapturedPayload(fixture["output"], fixture["input_sha256"])
                case["write_receipt"] = port.write(snapshot)
                case.update(
                    persistence_insert_succeeded=True,
                    readback=port.read(fixture["notice_id"]),
                    state_after=port.state(),
                    notice_chain=port.chain(fixture["notice_id"]),
                    outcome="SUCCESS",
                )
            except Exception as exc:
                case.update(
                    outcome="STORAGE_FAILURE",
                    error_type=type(exc).__name__,
                    state_after=port.state(),
                )
            finally:
                port.close()
            reopened = factory(path)
            try:
                case["reopened_state_equal"] = reopened.state() == case["state_after"]
                case["reopened_readback"] = reopened.read(fixture["notice_id"])
                case["reopened_notice_chain"] = reopened.chain(fixture["notice_id"])
            except Exception as exc:
                case.update(
                    outcome="STORAGE_FAILURE",
                    reopen_error_type=type(exc).__name__,
                    reopened_state_equal=False,
                    reopened_readback=None,
                )
            finally:
                reopened.close()
            write_json(destination / case["evidence_ref"], case)
            cases.append(case)
    return cases


def storage_checks(cases: list[dict], manifest: dict) -> list[dict]:
    requirements = [r for r in load_requirements() if r["id"] in STORAGE_IDS]
    findings = evaluate(requirements, cases, manifest)
    by_id = {r["id"]: r for r in requirements}
    for case in cases:
        # These supplement, never replace, the original count/reopen checks. Exact
        # normalized readback is the observable meaning of acknowledged persistence.
        read_case = {**case, "case_id": case["case_id"] + ":readback"}
        if case["outcome"] != "SUCCESS":
            findings.append(finding(by_id["STATE-001"], read_case, "ERROR", case["outcome"]))
            continue
        passed = case["readback"] == case["output"] == case["reopened_readback"]
        findings.append(
            finding(
                by_id["STATE-001"],
                read_case,
                "PASS" if passed else "FAIL",
                {
                    "readback_sha256": fingerprint(case["readback"]),
                    "reopened_sha256": fingerprint(case["reopened_readback"]),
                },
                {"expected_snapshot_sha256": fingerprint(case["output"])},
            )
        )
        persisted = {
            **read_case,
            "output": case["reopened_readback"],
            "trusted_input_notice": case["output"]["notice"],
            "notice_chain": case.get("reopened_notice_chain", []),
        }
        link_check = (
            check_case(by_id["OUTPUT-003"], persisted)
            if persisted["output"]
            else finding(
                by_id["OUTPUT-003"],
                persisted,
                "ERROR",
                {"reason": "Missing persisted readback"},
                domain="STORAGE_FAILURE",
            )
        )
        if link_check is not None:
            findings.append(link_check)
        if persisted["output"]:
            lineage_check = check_case(by_id["HISTORY-001"], persisted)
            if lineage_check is not None:
                findings.append(lineage_check)
        prior_ids = {r["notice_id"] for r in case["state_before"]["notices"]} - {case["notice_id"]}
        preserved = all(
            readback(case["state_before"], id) == readback(case["state_after"], id)
            for id in prior_ids
        )
        findings.append(
            finding(
                by_id["STATE-001"],
                {**case, "case_id": case["case_id"] + ":other-notices"},
                "PASS" if preserved else "FAIL",
                {
                    "retained_other_notice_ids": sorted(prior_ids),
                    "other_notices_unchanged": preserved,
                },
                "Existing distinct notices and all their child observations preserved unchanged",
            )
        )
    return findings


def compare(left: list[dict], right: list[dict]) -> dict:
    def index(rows: list[dict]) -> dict:
        return {(r["requirement_id"], r["case_id"]): r for r in rows}

    before, after = index(left), index(right)
    changed, unchanged = [], []
    for key in sorted(before.keys() | after.keys()):
        old, new = before.get(key), after.get(key)
        item = {
            "requirement_id": key[0],
            "case_id": key[1],
            "before": old["status"] if old else "ABSENT",
            "after": new["status"] if new else "ABSENT",
        }
        if item["before"] == item["after"]:
            unchanged.append(item)
        else:
            changed.append(item)
    unexpected = [r for r in changed if not (r["before"] == "FAIL" and r["after"] == "PASS")]
    status = "UNKNOWN" if not left else "PASS" if not unexpected else "FAIL"
    return {
        "status": status,
        "scope": "Paired captured storage behavior only",
        "newly_passing": [r for r in changed if r["after"] == "PASS"],
        "newly_failing": [r for r in changed if r["after"] in {"FAIL", "ERROR"}],
        "unchanged": unchanged,
        "unexpected": unexpected,
        "requirements_affected": sorted({r["requirement_id"] for r in changed}),
    }


def evaluate_pair(
    fixtures: list[dict], destination: Path, source: dict, baseline: Path | None = None
) -> dict:
    destination = validate_output(destination)
    if baseline is not None:
        for name in ("inherited", "rebuilt"):
            verified_capture(baseline / name / "results.json")
    if not fixtures or len({f["case_id"] for f in fixtures}) != len(fixtures):
        raise ValueError("Missing or duplicated fixture inventory")
    manifest = {
        "run_id": destination.name,
        "input_kind": "captured normalized snapshots",
        "source": source,
        "fixtures_sha256": fingerprint(fixtures),
        "provenance": provenance(),
        "model_variant": "impact-budget-512 frozen outputs; no new model execution or token-causality claim",
        "implementations": {
            "inherited": "pristine database.insert_notice",
            "rebuilt": "SnapshotStore",
        },
        "component_files": {
            str(p.relative_to(ROOT)): digest(p) for p in sorted((ROOT / "rebuilt").glob("*.py"))
        },
        "initial_state": "empty database per group, per implementation; same fixture order; reopen every write",
    }
    write_json(destination / "fixtures.json", fixtures)
    factories: list[tuple[str, type[InheritedStorage] | type[RebuiltStorage]]] = [
        ("inherited", InheritedStorage),
        ("rebuilt", RebuiltStorage),
    ]
    cases = {name: run_system(factory, fixtures, destination / name) for name, factory in factories}
    manifest["integrity_after"] = integrity()
    write_json(destination / "manifest.json", manifest)
    results: dict[str, dict] = {}
    label_requirements = [
        r for r in load_requirements() if r["validation"]["check"] == "classification"
    ]
    for name, observed in cases.items():
        checks = storage_checks(observed, manifest)
        # Score persisted decisions, not predictions invented by this component test.
        labeled = [
            {
                **c,
                "output": c.get("readback"),
                "outcome": c.get("semantic_outcome", "SUCCESS")
                if c.get("readback")
                else "STORAGE_FAILURE",
            }
            for c in observed
            if c["category"] == "labeled"
        ]
        behavior = evaluate(label_requirements, labeled, manifest) if labeled else []
        results[name] = {
            "cases": observed,
            "storage_findings": checks,
            "behavior_findings": behavior,
            "gates": {
                "1": aggregate([r["status"] for r in checks]),
                "2": aggregate([r["status"] for r in behavior]),
            },
            "gate2_scope": "Persisted decisions from the full 512-token candidate capture; no new classification execution",
            "comparison_identity": comparison_identity(name, fixtures, manifest),
        }
        write_json(destination / name / "results.json", results[name])
        retained = []
        for check in checks + behavior:
            if check["status"] not in {"FAIL", "ERROR"}:
                continue
            source_case = next(
                (c for c in observed if c["case_id"] == check["case_id"].split(":")[0]), None
            )
            retained.append(
                {
                    "requirement": check["requirement_id"],
                    "input": source_case,
                    "expected": check["expected"],
                    "observed": check["observed"],
                    "risk": check["risk"],
                    "evidence": check["evidence_refs"],
                    "possible_failure_domain": check["failure_domain"],
                    "confidence": check["confidence"],
                }
            )
        write_json(destination / name / "failures.json", retained)
        write_json(
            destination / name / "regression_candidates.json",
            [
                {
                    "requirement": r["requirement"],
                    "case_id": r["input"]["case_id"] if r["input"] else "run",
                    "input_sha256": r["input"]["input_sha256"] if r["input"] else None,
                    "status": "retained example; no requirement or policy change",
                    "evidence": r["evidence"],
                }
                for r in retained
            ],
        )
    comparison = compare(
        results["inherited"]["storage_findings"] + results["inherited"]["behavior_findings"],
        results["rebuilt"]["storage_findings"] + results["rebuilt"]["behavior_findings"],
    )
    same_decisions = all(
        (a.get("readback") or {}).get("notice") == (b.get("readback") or {}).get("notice")
        for a, b in zip(cases["inherited"], cases["rebuilt"])
    )
    comparison["persisted_notice_decisions_equal"] = same_decisions
    if not same_decisions:
        comparison["unexpected"].append({"difference": "Persisted notice decision fields differ"})
        comparison["status"] = "FAIL"
    write_json(destination / "comparison.json", comparison)
    temporal = {}
    for name, result in results.items():
        current = {**result, "findings": result["storage_findings"] + result["behavior_findings"]}
        prior = reinterpret_prior(baseline, name, fixtures, destination) if baseline else None
        temporal[name] = temporal_compare(prior, current)
    write_json(destination / "temporal.json", temporal)
    unavailable = evaluate(
        [r for r in load_requirements() if r["check_status"] == "not_available"], [], manifest
    )
    write_json(destination / "unavailable-proof.json", unavailable)
    summary = {
        "run": str(destination.relative_to(ROOT)),
        "cases_per_system": len(fixtures),
        "gates": {
            name: {**r["gates"], "3": temporal[name]["status"]} for name, r in results.items()
        },
        "storage_acceptance": aggregate(
            [r["status"] for r in results["rebuilt"]["storage_findings"]]
        ),
        "acceptance_scope": "Current-snapshot component checks, including required missing history proof; temporal comparison is additionally required for acceptance",
        "paired": comparison,
        "temporal": temporal,
        "unavailable_application_requirements": [r["requirement_id"] for r in unavailable],
        "unknown_checks": [
            {k: r[k] for k in ("requirement_id", "case_id", "observed")}
            for r in results["rebuilt"]["storage_findings"]
            if r["status"] == "UNKNOWN"
        ],
        "application_acceptance": "NOT ESTABLISHED: "
        + str(sum(f["status"] == "FAIL" for r in results.values() for f in r["behavior_findings"]))
        + " failed frozen classification assertions across both stores; "
        + str(len(unavailable))
        + " unavailable application requirements",
        "newly_passing": len(comparison["newly_passing"]),
        "newly_failing": len(comparison["newly_failing"]),
        "unchanged": len(comparison["unchanged"]),
        "unexpected": comparison["unexpected"],
    }
    write_json(destination / "summary.json", summary)
    return summary


def comparison_identity(name: str, fixtures: list[dict], manifest: dict) -> dict:
    files = manifest["provenance"]["files"]
    return {
        "implementation": name,
        "implementation_files": manifest.get("component_files", {})
        if name == "rebuilt"
        else manifest["provenance"].get("inherited_manifest_sha256"),
        "policy": files["spec.md"],
        "rules": files["requirements/requirements.yaml"],
        "oracle": fingerprint(
            {p: files[p] for p in ("requirements/dataset.json", "requirements/oracle-support.json")}
        ),
        "evaluation": fingerprint(
            {
                p: files[p]
                for p in (
                    "harness/gates.py",
                    "harness/storage_evaluation.py",
                    "harness/regression.py",
                )
            }
        ),
        "protocol": manifest["initial_state"],
        "model": {
            "frozen_capture_sha256": manifest["source"].get("sha256"),
            "configuration": "Recorded in verified capture manifest",
        },
        "required_cases": [f["case_id"] for f in fixtures],
        "inputs": fingerprint(
            [{k: f[k] for k in ("case_id", "input_sha256", "output", "group")} for f in fixtures]
        ),
        "comparator": files["harness/regression.py"],
        "inherited_inventory_observed": "unexpected_executables"
        in manifest.get("integrity_after", {}),
    }


def reinterpret_prior(baseline: Path, name: str, fixtures: list[dict], destination: Path) -> dict:
    original = verified_capture(baseline / name / "results.json")
    old_manifest = json.loads((baseline / "manifest.json").read_text())
    old_fixtures = json.loads((baseline / "fixtures.json").read_text())
    manifest = {**old_manifest, "provenance": provenance()}
    cases = json.loads(json.dumps(original["cases"]))
    for c in cases:
        c["available_corpus_ids"] = sorted({f["notice_id"] for f in old_fixtures})
        c["trusted_input_notice"] = c["output"]["notice"]
    checks = storage_checks(cases, manifest)
    labels = [
        {
            **c,
            "output": c.get("readback"),
            "outcome": c.get("semantic_outcome", "SUCCESS")
            if c.get("readback")
            else "STORAGE_FAILURE",
        }
        for c in cases
        if c["category"] == "labeled"
    ]
    behavior = evaluate(
        [r for r in load_requirements() if r["validation"]["check"] == "classification"],
        with_oracle(labels),
        manifest,
    )
    result = {
        "cases": cases,
        "findings": checks + behavior,
        "comparison_identity": comparison_identity(name, old_fixtures, old_manifest),
        "reinterpretation_identity": comparison_identity(name, old_fixtures, manifest),
        "interpretation": {
            "source": str(baseline / name / "results.json"),
            "source_sha256": digest(baseline / name / "results.json"),
            "original_evaluator": old_manifest["provenance"]["files"],
            "current_evaluator": manifest["provenance"]["files"],
            "meaning": "New evaluation of retained observations; original findings remain unchanged",
        },
    }
    write_json(destination / "temporal-baseline" / name / "results.json", result)
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    parser.add_argument("--baseline", type=Path)
    args = parser.parse_args()
    run = args.output or new_run("storage")
    if (run / "manifest.json").exists():
        raise FileExistsError("Never overwrite an evaluation run")
    result = evaluate_pair(
        fixtures_from_capture(),
        run,
        {"path": str(CAPTURE.relative_to(ROOT)), "sha256": digest(CAPTURE)},
        args.baseline,
    )
    print(json.dumps(result))


if __name__ == "__main__":
    main()
