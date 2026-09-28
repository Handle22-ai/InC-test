"""Three bounded gates over the runtime classifier and independent frozen witnesses."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

from harness import behavior_contract, context, specification
from harness.requirements import load_requirements
from harness.runtime import ROOT, OutputDestinationError, create_run, digest, new_run, write_json
from rebuilt.normalized_classifier import classify

SCOPE = "bounded-integrated-classifier-publisher-v3"


class PreflightRefused(Exception):
    """Collected contract findings prevent component execution."""


def exit_code(result: dict) -> int:
    """Stable CI outcomes; Make itself collapses failed recipes to exit 2."""
    if any(r.get("classification") == "NOT_RUN" for r in result["gates"].values()):
        return 5
    status = aggregate(list(result["gates"].values()))
    if result.get("mode") == "PROPOSAL_ONLY" and status == "PASS":
        return 3
    return {"PASS": 0, "UNKNOWN": 3, "FAIL": 4, "ERROR": 5}[status]


def semantic_hash(value: object) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def source_identity() -> dict:
    paths = [
        p
        for folder in ("harness", "rebuilt", "requirements", "context", "docs", "tests")
        for p in (ROOT / folder).rglob("*")
        if p.is_file() and p.suffix in {".py", ".json", ".yaml", ".md"}
    ]
    paths.extend(
        ROOT / name
        for name in (
            "classifier.py",
            "spec.md",
            "AGENTS.md",
            "README.md",
            "Makefile",
            "pyproject.toml",
            "artifacts/dependencies.lock.txt",
            "artifacts/dependencies-dev.lock.txt",
            "submission/verify_positive_path.py",
        )
    )
    identities = {str(path.relative_to(ROOT)): digest(path) for path in sorted(paths)}
    return {
        "content_sha256": semantic_hash(identities),
        "content_scope": "Code/contracts/context/tests/build inputs; evidence, reports and baseline registration excluded",
        "revision": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip(),
        "working_tree_dirty": bool(
            subprocess.check_output(
                ["git", "status", "--porcelain", "--untracked-files=no"], cwd=ROOT, text=True
            ).strip()
        ),
        "files": identities,
    }


def comparison_identity(contract: dict, witnesses: list[dict]) -> dict:
    from harness.comparison_identity import build

    return build(contract, witnesses)


FILE_CLASSES = (
    ("component", ("rebuilt/", "classifier.py")),
    (
        "spec_and_generated",
        (
            "spec.md",
            "requirements/behavior.yaml",
            "requirements/requirements.yaml",
            "requirements/signal-safety.yaml",
            "requirements/replay-expectations.json",
            "requirements/compiled-build.json",
            "requirements/normalized-input.schema.json",
            "requirements/normalized-output.schema.json",
            "docs/signal-contract.md",
            "docs/system-contract.md",
        ),
    ),
    (
        "oracle",
        (
            "requirements/dataset.json",
            "requirements/oracle-support.json",
            "requirements/normalized-witnesses.json",
            "requirements/publisher-witnesses.json",
            "requirements/real-positive-witnesses.json",
            "requirements/capture-registry.json",
            "requirements/trading-evidence.json",
            "context/authority-reference.json",
        ),
    ),
    ("evaluator", ("harness/", "tests/", "requirements/rule-block.schema.json")),
)


def changed_files(before: dict, after: dict) -> dict[str, list[str]]:
    """Files changed since the reference, by who may change them."""
    classified = {name for _, names in FILE_CLASSES for name in names}
    names = sorted(
        name
        for name in set(before) | set(after)
        if before.get(name) != after.get(name)
        # Context notes and generated docs are reading material, not behavior.
        and (name in classified or not name.startswith(("context/", "docs/")))
    )
    groups: dict[str, list[str]] = {key: [] for key, _ in FILE_CLASSES}
    groups["other"] = []
    for name in names:
        key = next(
            (k for k, prefixes in FILE_CLASSES if any(name.startswith(p) for p in prefixes)),
            "other",
        )
        groups[key].append(name)
    return {key: value for key, value in groups.items() if value}


def compare(previous: dict, current: dict) -> dict:
    """Decisions against the registered reference.

    Identical code, spec and oracle: every case must be unchanged. A spec change: each
    changed captured decision must equal what the current spec derives, and each
    changed witness or publisher case must still pass its frozen check. Harness or
    oracle changes leave the comparison UNKNOWN until a reviewed reference is
    registered, because the yardstick itself moved.
    """
    before, after = previous["cases"], current["cases"]
    derived = current.get("spec_outcomes", {})

    files = changed_files(previous["source"].get("files", {}), current["source"].get("files", {}))
    spec_changed = "spec_and_generated" in files

    def explained(key: str) -> bool:
        """Captured decisions must equal the spec's derivation; other cases may change
        only when the spec changed and they still pass their frozen check."""
        if key in derived:
            action = derived[key]
            return all(
                after[key]["output"].get(k) == action[k] for k in ("classification", "disposition")
            )
        return spec_changed and after[key]["status"] == "PASS"

    new_fail = sorted(
        key
        for key, row in after.items()
        if row["status"] not in {"PASS", "COUNTED"}
        and before.get(key, {}).get("status") in {"PASS", "COUNTED"}
    )
    new_pass = sorted(
        key
        for key, row in after.items()
        if row["status"] == "PASS" and before.get(key, {}).get("status") != "PASS"
    )
    different = sorted(
        key for key in set(before) & set(after) if before[key]["output"] != after[key]["output"]
    )
    unexplained = [key for key in different if not explained(key)]
    missing = sorted(set(before) - set(after))
    files = changed_files(previous["source"].get("files", {}), current["source"].get("files", {}))
    moved_yardstick = sorted(set(files) & {"oracle", "evaluator"})
    status = (
        "FAIL" if new_fail or unexplained or missing else "UNKNOWN" if moved_yardstick else "PASS"
    )
    classification = (
        "REGRESSION"
        if status == "FAIL"
        else "EVALUATOR_OR_ORACLE_CHANGED"
        if status == "UNKNOWN"
        else "NO_CHANGE_SINCE_REFERENCE"
        if not different and not files
        else "CHANGES_EXPLAINED_BY_SPEC"
    )
    return {
        "status": status,
        "classification": classification,
        "reason": {
            "REGRESSION": "Decisions changed that the current spec does not explain, or cases failed or went missing",
            "EVALUATOR_OR_ORACLE_CHANGED": "Harness, tests or evaluation oracle changed since the reference ("
            + ", ".join(moved_yardstick)
            + "); register a reviewed reference before this comparison can pass",
            "NO_CHANGE_SINCE_REFERENCE": "Nothing changed since the reference; this is not a regression test of a change",
            "CHANGES_EXPLAINED_BY_SPEC": "Every changed decision equals the current spec's derivation or still passes its frozen check",
        }[classification],
        "changed_files": files,
        "changed_decisions": different,
        "unexplained_differences": unexplained,
        "newly_passing": new_pass,
        "newly_failing": new_fail,
        "unchanged": sorted(key for key in set(before) & set(after) if before[key] == after[key]),
        "missing_cases": missing,
        "requirements_affected": sorted(
            {
                req
                for key in set(new_fail + unexplained + missing)
                for req in (after.get(key) or before[key])["requirements"]
            }
        ),
        "original_execution_identity": {
            k: v for k, v in previous["source"].items() if k != "files"
        },
        "current_execution_identity": {k: v for k, v in current["source"].items() if k != "files"},
    }


def verify_evidence(directory: Path, manifest: dict) -> None:
    for relative, expected in manifest["files"].items():
        path = (directory / relative).resolve()
        if (
            not path.is_relative_to(directory.resolve())
            or not path.is_file()
            or digest(path) != expected
        ):
            raise ValueError("INVALID_EVIDENCE_IDENTITY: " + relative)


def registered_baseline() -> dict | None:
    from harness.baseline import registered

    return registered(ROOT)


def aggregate(findings: list[dict]) -> str:
    statuses = {row["status"] for row in findings}
    return next((status for status in ("ERROR", "FAIL", "UNKNOWN") if status in statuses), "PASS")


def declared_coverage(requirements: dict, findings: list[dict]) -> tuple[dict, list[dict]]:
    """The verification table owns scope; observations cannot bring a row into scope.

    Rows the spec declares out_of_scope are listed, never gated. An in-scope row with
    no observation is UNKNOWN and blocks its gate.
    """
    coverage, missing = {}, []
    for key, requirement in requirements.items():
        observed = [row for row in findings if row.get("requirement") == key]
        validation = requirement["validation"]
        if validation["check"] == "out_of_scope":
            coverage[key] = {
                "status": "OUT_OF_SCOPE",
                "observations": len(observed),
                "declared_check": validation["check"],
                "gate": validation["gate"],
                "availability": "out_of_scope",
                "scope": "Declared out of scope for this component in spec-verification; not gated and not claimed",
            }
            continue
        status = aggregate(observed) if observed else "UNKNOWN"
        if not observed:
            missing.append(
                {
                    "requirement": key,
                    "gate": validation["gate"],
                    "status": "UNKNOWN",
                    "code": "DECLARED_CHECK_UNOBSERVED",
                    "check": validation["check"],
                    "reason": "No observations for the check declared in spec-verification",
                }
            )
        coverage[key] = {
            "status": status,
            "observations": len(observed),
            "declared_check": validation["check"],
            "gate": validation["gate"],
            "availability": "declared",
            "scope": "Finite observations of the declared check; full obligation completion is not inferred",
        }
    return coverage, missing


def identity_findings(
    result: dict, invariants: list[bool], witnesses: list[dict], requirements: dict
) -> list[dict]:
    """INPUT-001 on every witness, OBS-001 run provenance and OBS-002 inherited integrity."""
    rows = [
        {
            "requirement": "INPUT-001",
            "gate": requirements["INPUT-001"]["validation"]["gate"],
            "case": witness["id"],
            "status": "PASS" if valid else "FAIL",
            "code": "OUTPUT_IDENTITY",
        }
        for witness, valid in zip(witnesses, invariants)
    ]
    trading = result.get("trading_layer", {})
    provenance = {
        "source_content": bool(result["source"].get("content_sha256")),
        "spec": bool(result.get("preflight_identity", {}).get("spec_sha256")),
        "comparison_identity": bool(result.get("comparison_identity")),
        "model_configuration": bool(result.get("model_configuration")),
        "capture_executions": bool(trading.get("sources"))
        and all(s.get("original_execution_identity") for s in trading["sources"]),
    }
    rows.append(
        {
            "requirement": "OBS-001",
            "gate": requirements["OBS-001"]["validation"]["gate"],
            "case": "run-provenance",
            "status": "PASS" if all(provenance.values()) else "FAIL",
            "code": "RUN_PROVENANCE",
            "observed": provenance,
        }
    )
    manifest = json.loads((ROOT / "artifacts/inherited_manifest.json").read_text())
    changed = [
        row["path"]
        for row in manifest["files"]
        if not (ROOT / row["path"]).is_file() or digest(ROOT / row["path"]) != row["sha256"]
    ]
    rows.append(
        {
            "requirement": "OBS-002",
            "gate": requirements["OBS-002"]["validation"]["gate"],
            "case": "inherited-snapshot",
            "status": "FAIL" if changed else "PASS",
            "code": "INHERITED_INTEGRITY",
            "observed": {"files": len(manifest["files"]), "changed": changed},
        }
    )
    return rows


def policy_edit(block: str) -> bool:
    """Every spec declaration except the decision log, including owned prose (audit 5 #12)."""
    return block != "spec-decisions"


def spec_edits(previous: dict | None, current: dict) -> list[dict]:
    """Spec table edits since the reference run, and whether any measured decision moved."""
    if not previous:
        return []
    from harness.proposals import PROSE_BLOCKS, declaration_changes
    from harness.spec_ownership import spec_text_with_hash

    old = spec_text_with_hash(ROOT, previous.get("comparison_identity", {}).get("spec_sha256", ""))
    if old is None:
        return []
    moved = bool(current["gates"].get("3", {}).get("changed_decisions"))
    edits = []
    for change in declaration_changes(old, (ROOT / "spec.md").read_text()):
        if not policy_edit(change["block"]):
            continue
        edits.append(
            {
                "declaration": f"{change['block']} / {change['id']} ({change['change']})",
                "fields": change["fields"],
                # No check reads owned prose, so a decision that moved did not measure it.
                "unmeasured": change["block"] in PROSE_BLOCKS or not moved,
            }
        )
    return edits


def edits_covered_by_last_reread(unmeasured: set[str], root: Path = ROOT) -> dict:
    """Spec edits the last reread covered: from the spec reread before it to the reread bytes.

    A reference registration moves the Gate 3 baseline, so the since-reference list
    empties; this list does not, and it keeps any edit known to be unmeasured flagged.
    It ends at the bytes the owner reread, never the working file: in proposal mode the
    working file holds edits no one has reread (audit 5 #14).
    """
    from harness.proposals import declaration_changes
    from harness.spec_ownership import PIN, spec_text_with_hash

    try:
        pin = json.loads((root / PIN).read_text())
    except OSError, ValueError:
        return {"from_spec_sha256": None, "edits": []}
    base = (pin.get("previous_read") or {}).get("spec_sha256")
    reread = pin.get("spec_sha256")
    old = spec_text_with_hash(root, base) if base else None
    new = spec_text_with_hash(root, reread) if reread else None
    if old is None or new is None:
        return {"from_spec_sha256": base, "to_spec_sha256": reread, "edits": []}
    edits = [
        f"{change['block']} / {change['id']} ({change['change']})"
        for change in declaration_changes(old, new)
        if policy_edit(change["block"])
    ]
    return {
        "from_spec_sha256": base,
        "to_spec_sha256": reread,
        "edits": [{"declaration": e, "unmeasured": e in unmeasured} for e in edits],
    }


def crashed_in_component(exc: BaseException) -> bool:
    """True when the exception was raised inside rebuilt/, the component under test."""
    import traceback

    component = str(ROOT / "rebuilt")
    frames = traceback.extract_tb(exc.__traceback__)
    return bool(frames) and frames[-1].filename.startswith(component)


def run(destination: Path) -> dict:
    result: dict = {
        "run_id": destination.name,
        "scope": SCOPE,
        "source": source_identity(),
        "cases": {},
        "findings": [],
        "gates": {},
        "accepted": False,
        "application_accepted": False,
    }
    try:
        from harness.consequences import run as consequence_run
        from harness.contract_preflight import collect

        preflight, compiled = collect(ROOT, destination)
        result.update(preflight)
        result["source"] = source_identity()
        if result["findings"] or compiled is None:
            result["gates"] = {
                "1": {
                    "name": "contracts_and_invariants",
                    "status": aggregate(result["findings"]),
                    "findings": result["findings"],
                },
                "2": {"name": "trading_behavior", "status": "UNKNOWN", "classification": "NOT_RUN"},
                "3": {
                    "name": "regression_change",
                    "status": "UNKNOWN",
                    "classification": "NOT_RUN",
                },
            }
            raise PreflightRefused
        consequences = consequence_run(compiled, destination)
        result["consequences"] = {k: v for k, v in consequences.items() if k != "cases"}
        result["spec_outcomes"] = {
            row["id"]: row["outcome"]["action"] for row in consequences["cases"]
        }
        package = context.select("recommendation-classification-maintenance")
        result["component_availability"] = {
            row["id"]: row["component_availability"] for row in package["requirements"]
        }
        contract = behavior_contract.load()
        witnesses = specification.fixtures()
        result["comparison_identity"] = comparison_identity(contract, witnesses)
        result["model_configuration"] = result["comparison_identity"]["model_configuration"]
        observations = []
        invariants = []
        for witness in witnesses:
            name = witness["id"]
            folder = destination / "cases" / name
            write_json(folder / "input.json", witness["input"])
            observation = specification.evaluate_runtime_witness(contract, witness)
            output = observation["runtime"]["output"]
            duplicate = classify(witness["input"]).proposal
            valid = (
                output == duplicate
                and output["notice_id"] == witness["input"]["notice"]["notice_id"]
                and output["source_sha256"] == witness["input"]["source"]["sha256"]
                and output["recommendation_allowed"] is False
                and observation["runtime"]["matched_rule"] == output["reason_codes"][0]
            )
            invariants.append(valid)
            write_json(folder / "observation.json", observation)
            result["cases"][name] = {
                "status": "PASS"
                if valid and observation["evaluation_status"] == "READY"
                else "FAIL",
                "input_sha256": digest(folder / "input.json"),
                "output": output,
                "matched_rule": observation["runtime"]["matched_rule"],
                "requirements": witness["requirements"],
            }
            if observation["finding"]:
                result["findings"].append(observation["finding"])
            if not valid:
                result["findings"].append(
                    {
                        "code": "NORMALIZED_INVARIANT_FAILURE",
                        "case": name,
                        "requirements": witness["requirements"],
                    }
                )
            observations.append(observation)
        write_json(destination / "semantic-fixtures.json", observations)
        result["semantic_fixture_sha256"] = digest(destination / "semantic-fixtures.json")
        requirements = {row["id"]: row for row in load_requirements()}
        contract_findings = []
        for observation in observations:
            witness = next(row for row in witnesses if row["id"] == observation["id"])
            for requirement in witness["requirements"]:
                if (
                    requirements[requirement]["validation"]["params"].get("ids")
                    and result["cases"][witness["id"]]["status"] == "PASS"
                ):
                    continue  # Synthetic witnesses do not establish source-example coverage.
                contract_findings.append(
                    {
                        "requirement": requirement,
                        "gate": requirements[requirement]["validation"]["gate"],
                        "case": witness["id"],
                        "status": result["cases"][witness["id"]]["status"],
                        "code": "INDEPENDENT_SEMANTIC_WITNESS",
                    }
                )
        result["semantic_contract_layer"] = {
            "findings": contract_findings,
            "evidence": "semantic-fixtures.json",
        }
        from harness import signal_evaluation, trading_evaluation

        signals = signal_evaluation.run(destination / "signals")
        candidate = signals["implementations"]["candidate"]
        signal_findings = candidate["findings"] + candidate["semantic_findings"]
        result["publisher_layer"] = {
            "status": candidate["status"],
            "findings": signal_findings,
            "evidence": "signals/results.json",
            "fault_controls": signals["fault_controls"],
            "sequence": [
                {key: row[key] for key in ("step", "initial_count", "disposition", "reason")}
                for row in candidate["observations"]
            ],
            "duplicate_replay_recommendations": candidate["attribution"][
                "duplicate_recommendation_steps"
            ],
        }
        for observation in candidate["observations"]:
            step = observation["step"]
            matched = [f for f in signal_findings if f["step"] == step]
            result["cases"]["publisher/" + step] = {
                "status": "PASS" if all(f["status"] == "PASS" for f in matched) else "FAIL",
                "requirements": sorted({f["requirement"] for f in matched}),
                "output": {
                    key: observation[key] for key in ("initial_count", "disposition", "reason")
                },
            }
        trading = trading_evaluation.run(destination / "trading")
        result["trading_layer"] = {
            key: trading[key]
            for key in (
                "scope",
                "sources",
                "metrics",
                "metric_definitions",
                "findings",
                "label_outcomes",
                "label_summaries",
                "tradeoffs",
                "capture_differences",
                "replay_reconciliation",
                "acceptance",
                "checks_not_applicable",
            )
        }
        result["trading_layer"]["evidence"] = "trading/results.json"
        for row in trading["observations"]:
            related = [f for f in trading["findings"] if f["case"] == row["id"]]
            result["cases"][row["id"]] = {
                "status": aggregate(related),
                "requirements": sorted({f["requirement"] for f in related}),
                "output": {
                    "classification": row["decision"]["classification"],
                    "disposition": row["decision"]["disposition"],
                    "recommendations": row["recommendation_count"],
                    "replay_recommendations": row["replay_recommendation_count"],
                },
            }
        from harness.real_positive_evaluation import run as real_positive_run

        real = real_positive_run(trading, destination / "real-positive-traces.json")
        result["real_positive_layer"] = {
            "status": real["status"],
            "evidence": "real-positive-traces.json",
        }
        result["inherited_layer"] = {
            "status": signals["implementations"]["inherited"]["status"],
            "attribution": signals["implementations"]["inherited"]["attribution"],
            "evidence": "signals/results.json",
        }
        findings = contract_findings + signal_findings + trading["findings"]
        from harness.refusal_control import run as refusal_control

        refusal = refusal_control(destination)
        result["direct_refusal"] = {
            "status": refusal["status"],
            "evidence": "direct-refusal.json",
            "scope": refusal["scope"],
        }
        findings.append(
            {
                "requirement": "INPUT-002",
                "gate": 1,
                "case": "direct-unsupported-status",
                "status": refusal["status"],
                "code": "DIRECT_COMPONENT_REFUSAL_RETAINED",
            }
        )
        findings.extend(
            {
                "requirement": "SIGNAL-001",
                "gate": 2,
                "case": row["id"],
                "status": row["status"],
                "code": "REAL_SOURCE_POSITIVE_WITNESS",
            }
            for row in real["witnesses"]
        )
        if not all(invariants):
            findings.append(
                {
                    "requirement": "OUTPUT-001",
                    "gate": requirements["OUTPUT-001"]["validation"]["gate"],
                    "case": "normalized-invariants",
                    "status": "FAIL",
                    "code": "NORMALIZED_INVARIANT_FAILURE",
                }
            )
        for fault, outcome in signals["fault_controls"].items():
            if not outcome["rejected"]:
                findings.append(
                    {
                        "requirement": "STATE-003",
                        "gate": requirements["STATE-003"]["validation"]["gate"],
                        "case": "negative-control/" + fault,
                        "status": "FAIL",
                        "code": "FAULT_CONTROL_SURVIVED",
                    }
                )
        findings.extend(identity_findings(result, invariants, witnesses, requirements))
        previous = registered_baseline()
        from harness.baseline import owners

        registration = (previous or {}).get("registration", {})
        listed = owners()
        result["reference_registration"] = {
            key: registration.get(key)
            for key in (
                "path",
                "source_commit",
                "registered_by",
                "accepted_changes",
                "unmeasured_policy_edits",
            )
        }
        result["gates"]["3"] = {
            "name": "regression_change",
            **(
                compare(previous, result)
                if previous
                else {"status": "UNKNOWN", "classification": "NO_COMPARISON_REFERENCE"}
            ),
        }
        # An unowned reference can stop a PASS, never hide a regression.
        if (
            previous
            and listed
            and registration.get("registered_by") not in listed
            and result["gates"]["3"]["status"] == "PASS"
        ):
            result["gates"]["3"] = {
                "name": "regression_change",
                "status": "UNKNOWN",
                "classification": "REFERENCE_NOT_OWNER_REGISTERED",
                "reason": "The comparison reference names no spec owner; register it with "
                "python -m harness register-reference RUN DEST --person OWNER",
            }
        result["spec_edits_since_reference"] = spec_edits(previous, result)
        unmeasured = [e for e in result["spec_edits_since_reference"] if e["unmeasured"]]
        # Report only: registration must not erase the record of an unmeasured edit.
        result["spec_edits_covered_by_last_reread"] = edits_covered_by_last_reread(
            {e["declaration"] for e in unmeasured}
            | set(registration.get("unmeasured_policy_edits") or [])
        )
        if unmeasured:
            findings.append(
                {
                    "requirement": "OBS-003",
                    "gate": 3,
                    "case": "spec-edits",
                    "status": "UNKNOWN",
                    "code": "UNMEASURED_POLICY_EDIT",
                    "reason": "Policy edits since the reference change no measured decision: "
                    + "; ".join(e["declaration"] for e in unmeasured)
                    + ". Add a witness or labeled case, or have an owner register a reference "
                    "that accepts them",
                }
            )
        if result["model_configuration"]["status"] != "PASS":
            result["gates"]["3"] = {
                "name": "regression_change",
                "status": "UNKNOWN",
                "classification": "MODEL_CONFIG_CHANGED",
                "reason": "Effective configured model differs from retained capture identities; no live model execution or comparison mapping",
                "model_configuration": result["model_configuration"],
            }
        findings.append(
            {
                "requirement": "OBS-003",
                "gate": requirements["OBS-003"]["validation"]["gate"],
                "case": "comparison",
                "status": result["gates"]["3"]["status"],
                "code": "REGRESSION_COMPARISON",
                "reason": result["gates"]["3"].get("reason")
                or result["gates"]["3"]["classification"],
            }
        )
        result["requirement_coverage"], unavailable = declared_coverage(requirements, findings)
        findings.extend(unavailable)
        result["findings"] = findings
        for key, name in (
            ("1", "contracts_and_invariants"),
            ("2", "trading_behavior"),
            ("3", "regression_change"),
        ):
            relevant = [row for row in findings if str(row["gate"]) == key]
            result["gates"][key] = {
                **result["gates"].get(key, {}),
                "name": name,
                "status": aggregate(relevant),
                "findings": relevant,
                "scope": "Current normalized witnesses, integrated publisher sequence, and retained captured trading replay; findings routed to declared requirement gates",
            }
        result["outside_scope"] = {
            "status": "UNKNOWN",
            "implementation": "NOT_IMPLEMENTED_OR_PARTIAL",
            "requirements": [
                row["id"] for row in load_requirements() if row["check_status"] == "not_available"
            ],
            "meaning": "Full lifecycle/delivery/history and semantic extraction are not accepted by this bounded gate",
        }
        result["mode"] = (
            "PROPOSAL_ONLY"
            if result.get("spec_read", {}).get("mode") == "PROPOSAL_ONLY"
            else "REVIEWED_SPEC"
        )
        if result["mode"] == "REVIEWED_SPEC" and result["source"]["working_tree_dirty"]:
            # Acceptance describes a commit; uncommitted bytes have no identity to accept.
            dirty = {
                "requirement": "OBS-001",
                "gate": 1,
                "case": "working-tree",
                "status": "UNKNOWN",
                "code": "UNCOMMITTED_CHANGES",
                "reason": "Tracked files differ from HEAD; commit before an acceptance run",
            }
            result["findings"].append(dirty)
            gate = result["gates"]["1"]
            gate["findings"] = [*gate.get("findings", []), dirty]
            if gate["status"] == "PASS":
                gate["status"] = "UNKNOWN"
                gate["reason"] = dirty["reason"]
        result["accepted"] = result["mode"] == "REVIEWED_SPEC" and all(
            gate["status"] == "PASS" for gate in result["gates"].values()
        )
    except PreflightRefused:
        pass
    except Exception as exc:  # noqa: BLE001 - every failure is classified and retained
        from harness.contract_preflight import trace, unclassified

        reason = f"{type(exc).__name__}: {exc}"
        # Keep the traceback beside the results: a crash reduced to a key name cannot
        # be located without rerunning (audit 5 #11 follow-up).
        write_json(
            destination / "exception.json",
            {"type": type(exc).__name__, "reason": str(exc), "traceback": trace(exc)},
        )
        known = (
            "UNRECORDED_SPEC_CHANGE",
            "STALE_SPEC_PIN",
            "GENERATED_ARTIFACT_DRIFT",
            "BOUNDARY_VIOLATION",
        )
        if crashed_in_component(exc) and not any(code in reason for code in known):
            # The component under test raised: an established failure, not a refused run.
            result["findings"].append(
                {
                    "gate": 1,
                    "status": "FAIL",
                    "code": "COMPONENT_CRASH",
                    "reason": reason,
                    "traceback": "exception.json",
                }
            )
            result["gates"] = {
                "1": {"name": "contracts_and_invariants", "status": "FAIL", "reason": reason},
                "2": {
                    "name": "trading_behavior",
                    "status": "UNKNOWN",
                    "reason": "Component crashed",
                },
                "3": {
                    "name": "regression_change",
                    "status": "UNKNOWN",
                    "reason": "Component crashed",
                },
            }
            result["mode"] = "COMPONENT_CRASHED"
            write_json(destination / "results.json", result)
            write_json(
                destination / "manifest.json",
                {"scope": SCOPE, "source": result["source"], "files": {}},
            )
            return result
        classification = next(
            (
                code
                for code in (
                    "UNRECORDED_SPEC_CHANGE",
                    "STALE_SPEC_PIN",
                    "GENERATED_ARTIFACT_DRIFT",
                    "BOUNDARY_VIOLATION",
                    "UNAPPROVED_SELF_PROMOTION",
                    "UNAPPROVED_REQUIREMENT_CHANGE",
                    "UNAPPROVED_POLICY_CHANGE",
                    "UNAPPROVED_ASSUMPTION_CHANGE",
                    "UNAPPROVED_MANIFEST_CHANGE",
                    "INVALID_EVIDENCE_IDENTITY",
                )
                if code in reason
            ),
            unclassified(exc),
        )
        result["findings"].append(
            {
                "status": "ERROR",
                "code": classification,
                "reason": reason,
                "traceback": "exception.json",
            }
        )
        result["gates"].setdefault("1", {"name": "contracts_and_invariants", "status": "ERROR"})
        result["gates"].setdefault(
            "2", {"name": "trading_behavior", "status": "UNKNOWN", "classification": "NOT_RUN"}
        )
        result["gates"]["3"] = {
            "name": "regression_change",
            "status": "ERROR" if classification == "INVALID_EVIDENCE_IDENTITY" else "UNKNOWN",
            "classification": classification,
        }
    write_json(destination / "results.json", result)
    write_json(
        destination / "manifest.json",
        {
            "scope": SCOPE,
            "source": result["source"],
            "files": {
                str(path.relative_to(destination)): digest(path)
                for path in sorted(destination.rglob("*.json"))
            },
        },
    )
    verify_evidence(destination, json.loads((destination / "manifest.json").read_text()))
    return result


def main() -> None:
    parser = argparse.ArgumentParser(prog="python -m harness gate", description=__doc__)
    parser.add_argument("--output", type=Path)
    parser.add_argument(
        "--proposal",
        action="store_true",
        help="Execute an unreviewed spec for measurement only; never acceptance",
    )
    args = parser.parse_args()
    try:
        destination = create_run(args.output or new_run("normalized"))
    except OutputDestinationError as exc:
        print(
            json.dumps(
                {
                    "status": "ERROR",
                    "code": "OUTPUT_DESTINATION",
                    "reason": str(exc),
                    "gate_exit_code": 5,
                }
            ),
            file=sys.stderr,
        )
        raise SystemExit(5) from exc
    if args.proposal:
        from harness.spec_ownership import proposal_scope

        with proposal_scope():
            result = run(destination)
    else:
        result = run(destination)
    from harness.current_evidence import render

    render(destination, result)
    print(
        json.dumps(
            {
                "scope": SCOPE,
                "mode": result.get("mode", "PREFLIGHT_REFUSED"),
                "accepted": result["accepted"],
                "gates": {key: row["status"] for key, row in result["gates"].items()},
                "gate_exit_code": exit_code(result),
                "nonpassing_finding_records": sum(
                    row["status"] not in {"PASS", "COUNTED"} for row in result["findings"]
                ),
                "distinct_affected_cases": len(
                    {
                        row.get("case", row.get("step"))
                        for row in result["findings"]
                        if row["status"] not in {"PASS", "COUNTED"}
                        and (row.get("case") or row.get("step"))
                    }
                ),
                "finding_codes": sorted(
                    {
                        row.get("code", row.get("relation", ""))
                        for row in result["findings"]
                        if row["status"] not in {"PASS", "COUNTED"}
                    }
                    | {
                        row["classification"]
                        for row in result["gates"].values()
                        if row.get("classification") and row["status"] != "PASS"
                    }
                ),
                "evidence": str(destination),
                "current": str(destination / "CURRENT.md"),
            }
        )
    )
    raise SystemExit(exit_code(result))


if __name__ == "__main__":
    main()
