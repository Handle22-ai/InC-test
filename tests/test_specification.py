"""Reproductions of temporal attribution and presented-invalid-semantic defects."""

import json
import tempfile
import unittest
from pathlib import Path

from harness.runtime import ROOT
from harness.signal_evaluation import check, load_contract
from harness.storage_evaluation import fixtures_from_capture, reinterpret_prior


class SpecificationEvidenceTests(unittest.TestCase):
    def test_historical_policy_is_read_from_original_manifest(self):
        baseline = ROOT / "evidence/integrity/20260927T021057.685073Z/storage-release"
        original = json.loads((baseline / "manifest.json").read_text())
        with tempfile.TemporaryDirectory() as directory:
            result = reinterpret_prior(
                baseline, "rebuilt", fixtures_from_capture(), Path(directory)
            )
        self.assertEqual(
            result["comparison_identity"]["policy"], original["provenance"]["files"]["spec.md"]
        )
        self.assertIn("reinterpretation_identity", result)

    def test_unusable_semantics_are_checked_at_application_boundary(self):
        previous = json.loads(
            (
                ROOT
                / "evidence/correction/20260927T220352.636265Z/final-checks/signals-release/results.json"
            ).read_text()
        )
        for name, status in [("inherited", "FAIL"), ("candidate", "PASS")]:
            findings = check(load_contract(), previous["implementations"][name]["observations"])
            rows = [
                f
                for f in findings
                if f["step"] == "unavailable-extraction" and f["requirement"] == "SAFETY-001"
            ]
            self.assertTrue(rows)
            self.assertEqual({f["status"] for f in rows}, {status})
            self.assertEqual({f["gate"] for f in rows}, {1})


class BehavioralDerivationTests(unittest.TestCase):
    def test_action_bound_and_precedence_change_expectations(self):
        from harness.behavior_contract import load
        from harness.specification import derivations, fixtures

        result = derivations(load(), fixtures())
        for kind in ("action", "precedence"):
            self.assertNotEqual(result[kind]["before"]["action"], result[kind]["after"]["action"])
            self.assertFalse(result[kind]["approved_for_application"])
        self.assertNotEqual(result["bound"]["before"], result["bound"]["after"])
        self.assertTrue(result["bound"]["unchanged_witness"]["before"])
        self.assertTrue(result["bound"]["unchanged_witness"]["after"])
        self.assertTrue(all(c["refused"] for c in result["controls"].values()))

    def test_normalized_boundary_refuses_labels_and_retains_missing_volume(self):
        import copy

        from harness.behavior_contract import features, validate_input
        from harness.specification import fixtures

        value = fixtures()[0]["input"]
        validate_input(value)
        self.assertEqual(value["facts"]["quantities"], [])
        self.assertTrue(features(value)["firm_disruption"])
        altered = copy.deepcopy(value)
        altered["expected_label"] = True
        with self.assertRaisesRegex(ValueError, "unexpected field"):
            validate_input(altered)

    def test_gate_mapping_is_derived_consistently_and_contract_failures_separate(self):
        from harness.requirements import load_requirements
        from harness.signal_evaluation import check, load_contract

        old = json.loads(
            (
                ROOT
                / "evidence/correction/20260927T220352.636265Z/final-checks/signals-release/results.json"
            ).read_text()
        )
        rows = {r["id"]: r for r in load_requirements()}
        findings = check(load_contract(), old["implementations"]["inherited"]["observations"])
        for f in findings:
            self.assertEqual(f["gate"], rows[f["requirement"]]["validation"]["gate"])
            if f["relation"] in {"disposition", "reason"}:
                self.assertEqual(f["kind"], "output_contract")
                self.assertNotEqual(f["relation"], "initial")

    def test_policy_change_is_noncomparable_even_for_equal_outputs(self):
        import copy

        from harness.regression import compare

        previous: dict = {
            "comparison_identity": {
                k: "same" for k in ("policy", "oracle", "rules", "evaluation", "protocol")
            },
            "cases": [],
            "findings": [],
        }
        current = copy.deepcopy(previous)
        self.assertEqual(compare(previous, current)["status"], "PASS")
        current["comparison_identity"]["policy"] = "new approved policy"
        result = compare(previous, current)
        self.assertEqual(result["status"], "UNKNOWN")
        self.assertIn("policy", result["configuration_changes"])
        self.assertIsNone(result["comparison_mapping"])
