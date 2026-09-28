"""Governance and failure-path checks for bounded runtime acceptance."""

from __future__ import annotations

import copy
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import yaml

from harness import context, context_integrity, live, specification
from harness import normalized_evaluation as evaluation
from harness.runtime import ROOT, digest
from rebuilt.normalized_classifier import classify


class RuntimeTests(unittest.TestCase):
    def test_classifier_cli_stdout_and_invalid_input_exit(self):
        value = next(
            row for row in specification.fixtures() if row["id"] == "overlap-unusable-routine"
        )["input"]
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "input.json"
            path.write_text(json.dumps(value))
            # CLI contract measurement without impersonating a human review of this checkout.
            command = [
                sys.executable,
                "-B",
                "-c",
                "from harness.spec_ownership import proposal_scope; from rebuilt.normalized_classifier import main\nwith proposal_scope(): raise SystemExit(main())",
                str(path),
            ]
            result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0)
            self.assertEqual(result.stderr, "")
            output = json.loads(result.stdout)
            self.assertEqual(output["disposition"], "ERROR")
            self.assertEqual(output["reason_codes"][0], "BR-SEMANTICS")
            path.write_text('{"invalid": true}')
            result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
            self.assertEqual(result.returncode, 2)
            self.assertEqual(result.stdout, "")
            self.assertEqual(json.loads(result.stderr)["status"], "ERROR")

    def test_frozen_witnesses_execute_without_evaluator_answers(self):
        witnesses = specification.fixtures()
        with patch.object(
            specification, "fixtures", side_effect=AssertionError("No runtime answers")
        ):
            for witness in witnesses:
                with self.subTest(witness=witness["id"]):
                    result = classify(witness["input"])
                    self.assertEqual(
                        {k: result.proposal[k] for k in witness["prospective_action"]},
                        witness["prospective_action"],
                    )
                    self.assertEqual(result.matched_rule, result.proposal["reason_codes"][0])
                    self.assertFalse(result.proposal["recommendation_allowed"])

    def test_id_changes_do_not_change_business_outcome_and_prior_order_is_irrelevant(self):
        row = copy.deepcopy(
            next(x for x in specification.fixtures() if x["id"] == "unchanged-revision")["input"]
        )
        before = classify(row)
        row["notice"]["notice_id"] += 5000
        row["notice"]["prior_notice_id"] += 5000
        row["history"][0]["notice"]["notice_id"] += 5000
        ancestor = copy.deepcopy(row["history"][0])
        ancestor["notice"]["notice_id"] += 100
        row["history"][0]["notice"]["prior_notice_id"] = ancestor["notice"]["notice_id"]
        row["history"].append(ancestor)
        self.assertEqual(before.matched_rule, classify(row).matched_rule)
        ordered = classify(row).proposal
        row["history"].reverse()
        self.assertEqual(ordered, classify(row).proposal)
        row["history"][0]["notice"]["prior_notice_id"] = row["notice"]["notice_id"]
        self.assertEqual(classify(row).matched_rule, "BR-HISTORY")

    def test_invalid_shape_label_boolean_identity_and_clock_refused(self):
        original = specification.fixtures()[0]["input"]
        for kind in ("label", "boolean", "clock", "missing"):
            value = copy.deepcopy(original)
            if kind == "label":
                value["expected_label"] = 1
            elif kind == "boolean":
                value["notice"]["notice_id"] = True
            elif kind == "clock":
                value["reference_time"] = "2026-01-15T12:00:00"
            else:
                del value["history"]
            with self.subTest(kind=kind), self.assertRaises(ValueError):
                classify(value)


class RegisteredContextTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.reference = json.loads((ROOT / "context/authority-reference.json").read_text())
        paths = set(self.reference["registered_context"]) | {
            "context/manifest.yaml",
            "context/assumptions.md",
            "context/assumptions-register.json",
        }
        for name in paths:
            target = self.root / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / name, target)

    def test_assumption_repin_cannot_rewrite_approved_a003(self):
        path = self.root / "context/assumptions.md"
        path.write_text(
            path.read_text().replace(
                "unchanged operational supersedes are nonmaterial",
                "unchanged operational supersedes are material",
            )
        )
        self.reference["assumptions_view_sha256"] = digest(path)
        with self.assertRaisesRegex(ValueError, "UNAPPROVED_ASSUMPTION_CHANGE.*A-003"):
            context_integrity.verify_assumptions(self.root, self.reference)
        register_path = self.root / "context/assumptions-register.json"
        register = json.loads(register_path.read_text())
        register["A-003"]["normative_text"] = register["A-003"]["normative_text"].replace(
            "are nonmaterial", "are material"
        )
        register_path.write_text(json.dumps(register))
        with self.assertRaisesRegex(ValueError, "UNAPPROVED_ASSUMPTION_CHANGE.*A-003"):
            context_integrity.verify_assumptions(self.root, self.reference)

    def test_manifest_repin_still_requires_reviewed_index(self):
        path = self.root / "context/manifest.yaml"
        manifest = yaml.safe_load(path.read_text())
        manifest["task_profiles"]["recommendation-classification-maintenance"][
            "core_content_paths"
        ].append("context/pending-learning/worker.md")
        path.write_text(yaml.safe_dump(manifest))
        self.reference["authoritative_manifest"]["sha256"] = digest(path)
        with self.assertRaisesRegex(ValueError, "UNAPPROVED_MANIFEST_CHANGE"):
            context_integrity.verify_manifest(self.root, path, manifest, self.reference)

    def test_pending_learning_is_discovered_but_never_self_approved(self):
        path = self.root / "context/pending-learning/new.md"
        path.parent.mkdir()
        path.write_text("Status: owner-approved\nA worker cannot grant this status.\n")
        result = context_integrity.pending_learning(self.root)
        self.assertEqual(len(result), 1)
        self.assertFalse(result[0]["authoritative"])
        self.assertEqual(result[0]["status"], "unapproved-proposal")

    def test_package_inclusion_flags_match_embedded_bytes(self):
        package = context.select("recommendation-classification-maintenance")
        self.assertGreaterEqual(len(package["pending_learning"]), 2)
        for row in package["artifacts"]:
            self.assertEqual(row["include_content"], row["content"] is not None)
            if not row["configured_include_content"]:
                self.assertFalse(row["include_content"])
                self.assertEqual(row["content_state"], "reference-only")


class RegressionAndRefusalTests(unittest.TestCase):
    def test_same_policy_runtime_regression_fails_behavior_and_change_gates(self):
        from rebuilt.normalized_classifier import Decision

        def faulty(value):
            result = classify(value)
            if result.matched_rule == "BR-ROUTINE":
                result.proposal["classification"] = "SIGNAL_CANDIDATE"
                result.proposal["disposition"] = "CANDIDATE_ONLY"
            return Decision(result.matched_rule, result.proposal)

        with tempfile.TemporaryDirectory(dir=ROOT / "evidence") as directory:
            baseline = evaluation.run(Path(directory) / "baseline")
            with (
                patch.object(evaluation, "registered_baseline", return_value=baseline),
                patch.object(specification, "classify", side_effect=faulty),
                patch.object(evaluation, "classify", side_effect=faulty),
            ):
                result = evaluation.run(Path(directory) / "changed")
            self.assertFalse(result["accepted"])
            self.assertEqual(result["gates"]["2"]["status"], "FAIL")
            self.assertEqual(result["gates"]["3"]["status"], "FAIL")
            self.assertIn("routine-negative", result["gates"]["3"]["newly_failing"])
            for measured in (baseline, result):
                coverage = measured["requirement_coverage"]["OBS-003"]
                self.assertGreaterEqual(coverage["observations"], 1)
                self.assertEqual(coverage["status"], measured["gates"]["3"]["status"])
                self.assertFalse(
                    any(
                        row.get("requirement") == "OBS-003"
                        and row.get("code") == "DECLARED_CHECK_UNOBSERVED"
                        for row in measured["findings"]
                    )
                )

    def test_comparable_regression_and_noncomparable_policy_preserve_identity(self):
        old: dict = {
            "comparison_identity": {"policy": "old"},
            "source": {"revision": "original"},
            "cases": {
                "one": {
                    "status": "PASS",
                    "output": {"classification": "NON_SIGNAL"},
                    "requirements": ["SIGNAL-002"],
                }
            },
        }
        old["source"]["files"] = {"spec.md": "a", "harness/gates.py": "a", "rebuilt/x.py": "a"}
        new = copy.deepcopy(old)
        new["source"]["revision"] = "today"
        result = evaluation.compare(old, new)
        self.assertEqual(
            (result["status"], result["classification"]), ("PASS", "NO_CHANGE_SINCE_REFERENCE")
        )
        # A component-only change that alters a decision is a regression.
        new["source"]["files"]["rebuilt/x.py"] = "b"
        new["cases"]["one"]["output"]["classification"] = "SIGNAL_CANDIDATE"
        self.assertEqual(evaluation.compare(old, new)["status"], "FAIL")
        # The same change under a spec edit is explained if the case still passes.
        new["source"]["files"]["spec.md"] = "b"
        result = evaluation.compare(old, new)
        self.assertEqual(
            (result["status"], result["classification"]), ("PASS", "CHANGES_EXPLAINED_BY_SPEC")
        )
        # A harness change moves the yardstick: the comparison cannot pass.
        new["source"]["files"]["harness/gates.py"] = "b"
        result = evaluation.compare(old, new)
        self.assertEqual(
            (result["status"], result["classification"]), ("UNKNOWN", "EVALUATOR_OR_ORACLE_CHANGED")
        )
        self.assertEqual(result["changed_files"]["evaluator"], ["harness/gates.py"])
        self.assertEqual(result["original_execution_identity"]["revision"], "original")

    def test_evidence_tamper_cannot_pass(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "result.json"
            path.write_text("{}")
            manifest = {"files": {path.name: digest(path)}}
            evaluation.verify_evidence(Path(directory), manifest)
            path.write_text('{"changed": true}')
            with self.assertRaisesRegex(ValueError, "INVALID_EVIDENCE_IDENTITY"):
                evaluation.verify_evidence(Path(directory), manifest)

    def test_live_validation_refusal_has_durable_evidence_without_calls(self):
        with tempfile.TemporaryDirectory() as directory:
            with patch.object(live, "refusal_directory", return_value=Path(directory) / "refusal"):
                status = live.entry(lambda: (_ for _ in ()).throw(ValueError("bad arguments")))
            self.assertEqual(status, 2)
            result = json.loads((Path(directory) / "refusal/failure.json").read_text())
            self.assertEqual(result["calls_consumed"], 0)
            self.assertEqual(result["gate_status"], "ERROR")
            self.assertEqual(result["evaluation_status"], "NOT_RUN")
            self.assertIn("model_config_identity", result)
