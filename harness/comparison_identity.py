"""Semantic identities for comparison; historical executions keep their own identities."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

from harness import behavior_contract
from harness.requirement_trace import normative
from harness.requirements import load_requirements
from harness.runtime import ROOT, digest
from harness.trading_evaluation import sources


def files(paths: list[Path]) -> dict[str, str]:
    return {str(path.relative_to(ROOT)): digest(path) for path in sorted(set(paths))}


def build(contract: dict, witnesses: list[dict]) -> dict:
    from harness.adapter import llm_utils
    from harness.normalized_evaluation import semantic_hash

    revisions = json.loads((ROOT / "requirements/requirement-revisions.json").read_text())
    captured_models = sorted({capture["manifest"]["configured_model"] for _, capture in sources()})
    effective_model = os.environ.get("LLM_MODEL", llm_utils._MODEL)
    # The inherited system loads inherited/.env for live runs; offline commands never
    # read credential files, so a model set there would be invisible (audit 2 #3).
    unreadable_config = (ROOT / "inherited/.env").exists()
    return {
        "scope": "bounded-integrated-classifier-publisher-v3",
        "python_runtime": sys.version,
        "policy_id": contract["policy_id"],
        "policy_version": contract["requirements_document"]["policy_version"],
        "policy_wording": {
            k: semantic_hash(v) for k, v in contract["requirements_document"]["policies"].items()
        },
        "spec_sha256": digest(ROOT / "spec.md"),
        "requirements_sha256": digest(ROOT / "requirements/requirements.yaml"),
        "requirement_rows": {
            row["id"]: {
                "revision": revisions.get(row["id"]),
                "normative_sha256": semantic_hash(normative(row)),
            }
            for row in load_requirements()
        },
        "behavior_contract_sha256": digest(behavior_contract.CONTRACT),
        "schemas": files(list((ROOT / "requirements").glob("*.schema.json"))),
        "witness_semantic_sha256": semantic_hash(witnesses),
        "independent_witnesses": files(
            [
                ROOT / name
                for name in (
                    "requirements/normalized-witnesses.json",
                    "requirements/publisher-witnesses.json",
                    "requirements/real-positive-witnesses.json",
                    "requirements/signal-safety.yaml",
                )
            ]
        ),
        # Include evaluators, generic predicates/schema machinery, adapters and state
        # code even when a particular change happens to leave these cases unchanged.
        "runtime_evaluator_publisher": files(
            list((ROOT / "harness").glob("*.py"))
            + list((ROOT / "harness").glob("*.json"))
            + list((ROOT / "rebuilt").glob("*.py"))
            + list((ROOT / "inherited").glob("*.py"))
            + [ROOT / "classifier.py", ROOT / "submission/verify_positive_path.py"]
        ),
        "capture_registry_oracle_config": files(
            [
                ROOT / name
                for name in (
                    "requirements/trading-evidence.json",
                    "requirements/capture-registry.json",
                    "requirements/dataset.json",
                    "requirements/oracle-support.json",
                    "artifacts/dependencies.lock.txt",
                    "artifacts/dependencies-dev.lock.txt",
                )
            ]
        ),
        "authority_context": files(
            [
                ROOT / "context/authority-reference.json",
                ROOT / "requirements/requirement-revisions.json",
            ]
        ),
        "context_scope": "Normative spec and oracle references are bound above. Pending learning, reading indexes and review assertions are not behavioral policy and cannot invalidate or authorize a comparison.",
        "captured_execution_identities": [
            {"path": name, "sha256": digest(ROOT / name), "original_manifest": capture["manifest"]}
            for name, capture in sources()
        ],
        "capture_interpretation": "Original manifests retain captured model/prompt/config identities. Current adapter/evaluator source hashes describe replay only; historical identities are never restamped.",
        "model_configuration": {
            "status": "PASS"
            if captured_models == [effective_model] and not unreadable_config
            else "UNKNOWN",
            "unverifiable_config_file": "inherited/.env" if unreadable_config else None,
            "requested_model_environment": os.environ.get("LLM_MODEL"),
            "effective_configured_model": effective_model,
            "captured_configured_models": captured_models,
            "live_model_executed": False,
            "synthetic_provider": "synthetic-provider",
            "meaning": "Configuration comparison only; captures keep their original identities and synthetic execution uses no live model",
        },
    }
