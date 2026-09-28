"""Audit 5 #32: each gate code harness.md cites as a catch must be raised by a test."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from harness import normalized_evaluation as evaluation
from harness import trading_evaluation
from harness.input_contract_checks import run as input_contract
from harness.runtime import ROOT
from harness.spec_compiler import compile_spec
from rebuilt.normalized_classifier import Decision, classify

REQUIREMENTS = {"SIGNAL-001": {"validation": {"gate": 2}}}


def labeled(index: int, case: str, expected: bool, classification: str) -> dict:
    return {
        "id": f"capture-{index}/{case}",
        "category": "labeled",
        "expected_signal": expected,
        "decision": {"classification": classification},
    }


def budget(observations: list[dict], missed: int, false: int) -> dict[str, dict]:
    result = {"sources": [{}], "observations": observations}
    acceptance = {
        "max_missed_positives_per_capture": missed,
        "max_false_positives_per_capture": false,
    }
    return {
        r["code"]: r for r in trading_evaluation.budget_findings(result, acceptance, REQUIREMENTS)
    }


class GateCodeTests(unittest.TestCase):
    def test_budgets_pass_at_the_limit_and_fail_one_over(self):
        rows = [
            labeled(0, "p1", True, "SIGNAL_CANDIDATE"),
            labeled(0, "p2", True, "UNRESOLVED"),  # sent to review: a miss
            labeled(0, "p3", True, "NON_SIGNAL"),
            labeled(0, "n1", False, "SIGNAL_CANDIDATE"),
            labeled(0, "n2", False, "UNRESOLVED"),  # review is not a false positive
        ]
        at_limit = budget(rows, missed=2, false=1)
        self.assertEqual(at_limit["LABELED_MISSED_POSITIVES"]["status"], "PASS")
        self.assertEqual(at_limit["LABELED_FALSE_POSITIVES"]["status"], "PASS")
        over = budget(rows, missed=1, false=0)
        self.assertEqual(over["LABELED_MISSED_POSITIVES"]["status"], "FAIL")
        self.assertEqual(
            over["LABELED_MISSED_POSITIVES"]["cases"], ["capture-0/p2", "capture-0/p3"]
        )
        self.assertEqual(over["LABELED_FALSE_POSITIVES"]["status"], "FAIL")
        self.assertEqual(over["LABELED_FALSE_POSITIVES"]["cases"], ["capture-0/n1"])

    def test_routine_notices_turned_candidates_are_named(self):
        def faulty(value):
            result = classify(value)
            if result.matched_rule == "BR-ROUTINE":
                result.proposal["classification"] = "SIGNAL_CANDIDATE"
                result.proposal["disposition"] = "CANDIDATE_ONLY"
            return Decision(result.matched_rule, result.proposal)

        with tempfile.TemporaryDirectory() as directory:
            with patch("rebuilt.signals.classify", side_effect=faulty):
                result = trading_evaluation.run(Path(directory))
        routine = [f for f in result["findings"] if f["code"] == "ROUTINE_ADMIN_SIGNALED"]
        self.assertTrue(routine)
        self.assertTrue(
            all(f["status"] == "FAIL" and f["requirement"] == "SIGNAL-002" for f in routine)
        )
        false = [f for f in result["findings"] if f["code"] == "LABELED_FALSE_POSITIVES"]
        self.assertTrue(any(f["status"] == "FAIL" for f in false))

    def test_day_first_date_format_is_named_against_its_spec_row(self):
        text = (ROOT / "spec.md").read_text()
        old = '"%m/%d/%Y %I:%M:%S%p"'
        self.assertEqual(text.count(old), 1)
        contract = compile_spec(ROOT, text.replace(old, '"%d/%m/%Y %I:%M:%S%p"'))
        with tempfile.TemporaryDirectory() as directory:
            report = input_contract(contract, Path(directory) / "input-contract.json")
        mismatches = [f for f in report["findings"] if f["code"] == "INPUT_DATE_FORMAT_MISMATCH"]
        self.assertTrue(mismatches)
        self.assertTrue(all(f["row"] == "INPUT-TIME-001" for f in mismatches))

    def test_a_changed_model_leaves_gate_3_unknown_and_says_why(self):
        with tempfile.TemporaryDirectory(dir=ROOT / "evidence") as directory:
            with patch.dict("os.environ", {"LLM_MODEL": "audit-nonexistent-model"}):
                result = evaluation.run(Path(directory) / "run")
        self.assertFalse(result["accepted"])
        self.assertEqual(result["gates"]["3"]["status"], "UNKNOWN")
        self.assertEqual(result["gates"]["3"]["classification"], "MODEL_CONFIG_CHANGED")


if __name__ == "__main__":
    unittest.main()
