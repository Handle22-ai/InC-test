"""Audit 5 #32: each gate code harness.md cites as a catch must be raised by a test."""

from __future__ import annotations

import json
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


class UnmeasuredEditTests(unittest.TestCase):
    """Audit 5 #12: owned prose, assumptions and verification scope are policy edits too."""

    def spec(self) -> str:
        return (ROOT / "spec.md").read_text()

    def swap(self, old: str, new: str) -> str:
        text = self.spec()
        self.assertEqual(text.count(old), 1, old)
        return text.replace(old, new)

    def test_prose_and_assumption_edits_are_declaration_changes(self):
        from harness.proposals import declaration_changes

        text = self.spec()
        edited = self.swap(
            "must not exceed PARAM-INITIAL-001", "must be at least PARAM-INITIAL-001"
        )
        edited = edited.replace("block automatic alerts on history gaps", "allow automatic alerts")
        changed = {(c["block"], c["id"]) for c in declaration_changes(text, edited)}
        self.assertEqual(changed, {("spec-prose", "D1-005"), ("spec-assumptions", "A-004")})

    def gate_edits(self, old_text: str, moved: bool) -> dict[str, bool]:
        current = {"gates": {"3": {"changed_decisions": ["x"] if moved else []}}}
        previous = {"comparison_identity": {"spec_sha256": "reference"}}
        with patch("harness.spec_ownership.spec_text_with_hash", return_value=old_text):
            edits = evaluation.spec_edits(previous, current)
        return {e["declaration"]: e["unmeasured"] for e in edits}

    def test_a_prose_edit_stays_unmeasured_even_when_decisions_moved(self):
        # The reference spec had different wording; the current spec is what is on disk.
        old = self.swap("must not exceed PARAM-INITIAL-001", "must be at least PARAM-INITIAL-001")
        self.assertEqual(self.gate_edits(old, moved=True), {"spec-prose / D1-005 (edited)": True})

    def test_scoping_a_requirement_out_is_a_tracked_policy_edit(self):
        old = self.swap(
            "SIGNAL-004 | 2 | labeled_eval | classification |",
            "SIGNAL-004 | 2 | labeled_eval | out_of_scope |",
        )
        self.assertEqual(
            self.gate_edits(old, moved=False), {"spec-verification / SIGNAL-004 (edited)": True}
        )


class ContextReviewTests(unittest.TestCase):
    """Audit 5 #13: an agent's package must say when spec.md is not what the owner reread."""

    def package(self) -> tuple[dict, str]:
        from harness import context

        with tempfile.TemporaryDirectory() as directory:
            out = Path(directory) / "out"
            context.write_package("recommendation-classification-maintenance", out)
            return json.loads((out / "package.json").read_text()), (out / "package.md").read_text()

    def test_the_reviewed_spec_carries_no_warning(self):
        package, text = self.package()
        self.assertEqual(package["spec_review"]["edits_since_reread"], [])
        self.assertNotIn("SPEC UNREVIEWED", text)
        self.assertIn("No check reads the assumptions table", text)

    def test_an_unreviewed_assumption_edit_is_named_at_the_top(self):
        spec = (ROOT / "spec.md").read_text()
        reread = spec.replace("block automatic alerts on history gaps", "allow automatic alerts")
        self.assertNotEqual(reread, spec)
        with (
            patch(
                "harness.context.review_status",
                return_value={
                    "reviewed": False,
                    "status": "REVIEW_PENDING",
                    "reason": "spec.md differs from the last reread.",
                },
            ),
            patch("harness.spec_ownership.spec_text_with_hash", return_value=reread),
        ):
            package, text = self.package()
        self.assertEqual(package["spec_review"]["status"], "REVIEW_PENDING")
        self.assertEqual(
            package["spec_review"]["edits_since_reread"], ["spec-assumptions / A-004 (edited)"]
        )
        self.assertLess(text.index("SPEC UNREVIEWED"), text.index("## Requirements"))
        self.assertIn("- spec-assumptions / A-004 (edited)", text)


class RereadCoverageTests(unittest.TestCase):
    """Audit 5 #14: edits made after the reread must never be listed as covered by it."""

    def test_an_unreviewed_working_edit_is_not_covered_by_the_last_reread(self):
        import hashlib
        import subprocess

        from harness.runtime import write_json

        spec = (ROOT / "spec.md").read_text()
        before = spec.replace(
            '"max_false_positives_per_capture": 0', '"max_false_positives_per_capture": 1'
        )
        working = spec.replace("block automatic alerts on history gaps", "allow automatic alerts")
        self.assertNotEqual(before, spec)
        self.assertNotEqual(working, spec)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "context").mkdir()
            git = ["git", "-c", "user.name=t", "-c", "user.email=t@t"]
            subprocess.run([*git, "init", "-q"], cwd=root, check=True)
            for text, message in ((before, "previous read"), (spec, "reread")):
                (root / "spec.md").write_text(text)
                subprocess.run([*git, "add", "-A"], cwd=root, check=True)
                subprocess.run([*git, "commit", "-qm", message], cwd=root, check=True)
            (root / "spec.md").write_text(working)  # an edit nobody has reread
            write_json(
                root / "context/spec-read-pin.json",
                {
                    "spec_sha256": hashlib.sha256(spec.encode()).hexdigest(),
                    "previous_read": {"spec_sha256": hashlib.sha256(before.encode()).hexdigest()},
                },
            )
            covered = evaluation.edits_covered_by_last_reread(set(), root)
        self.assertEqual(
            [e["declaration"] for e in covered["edits"]], ["spec-settings / acceptance (edited)"]
        )


class DeskCountTests(unittest.TestCase):
    """Audit 5 #2: the observed counts must reconcile with the desk table's missed positives."""

    def test_missed_positives_are_decided_negatives_plus_unresolved(self):
        with tempfile.TemporaryDirectory() as directory:
            result = trading_evaluation.run(Path(directory))
        metrics = result["metrics"]
        self.assertNotIn("supplied_label_false_negatives", metrics)
        missed = sum(
            f["observed"] for f in result["findings"] if f["code"] == "LABELED_MISSED_POSITIVES"
        )
        counted = (
            metrics["labeled_positives_decided_non_signal"]["count"]
            + metrics["labeled_positives_unresolved"]["count"]
        )
        self.assertEqual(counted, missed)
        self.assertGreater(missed, 0)  # today's captures miss 46732 and 46881 in each


class RefusalStageTests(unittest.TestCase):
    """Audit 5 #10: the consequences headline must name the stage that refuses."""

    def consequences(self, old: str, new: str) -> tuple[dict, str]:
        from harness.proposals import run

        text = (ROOT / "spec.md").read_text()
        self.assertEqual(text.count(old), 1, old)
        with tempfile.TemporaryDirectory(dir=ROOT / "evidence") as directory:
            proposal = Path(directory) / "proposal.md"
            proposal.write_text(text.replace(old, new))
            result = run(proposal, str(ROOT / "spec.md"), Path(directory) / "out")
            return result, (Path(directory) / "out/REPORT.md").read_text()

    def test_a_witness_contradiction_is_refused_by_the_gate_not_compile(self):
        result, report = self.consequences(
            "FIRM_DISRUPTION | ANY | FIRM_CANDIDATE", "FIRM_DISRUPTION | ANY | UNRESOLVED"
        )
        self.assertEqual(result["refused_by"]["compile"], [])
        self.assertTrue(result["refused_by"]["gate"])
        self.assertIn("by the gate only", report)
        self.assertNotIn("by `make compile` (boundary checks)", report)

    def test_a_boundary_violation_is_refused_by_compile(self):
        result, report = self.consequences("BR-HISTORY > BR-UNCHANGED", "BR-UNCHANGED > BR-HISTORY")
        self.assertTrue(result["refused_by"]["compile"])
        self.assertIn("by `make compile` (boundary checks)", report)


class HarnessExceptionTests(unittest.TestCase):
    """Audit 5 #11 follow-up: a harness defect is not a spec problem, and keeps its traceback."""

    def test_only_deliberate_refusals_are_spec_integrity_errors(self):
        from harness.contract_preflight import refusal

        def raised(exc: Exception) -> Exception:
            try:
                raise exc
            except Exception as caught:  # noqa: BLE001 - the probe needs a real traceback
                return caught

        defect = refusal(raised(KeyError("candidate_classification")))
        self.assertEqual(defect["code"], "HARNESS_EXCEPTION")
        self.assertIn("Traceback", defect["traceback"])
        spec = refusal(raised(ValueError("spec.md:300: block spec-decisions, row X: bad status")))
        self.assertEqual(spec["code"], "SPECIFICATION_INTEGRITY_ERROR")
        self.assertNotIn("traceback", spec)

    def test_a_harness_crash_in_the_gate_is_named_and_traced(self):
        with tempfile.TemporaryDirectory(dir=ROOT / "evidence") as directory:
            out = Path(directory) / "run"
            with patch.object(trading_evaluation, "run", side_effect=KeyError("probe")):
                result = evaluation.run(out)
            codes = {f.get("code") for f in result["findings"]}
            self.assertIn("HARNESS_EXCEPTION", codes)
            self.assertNotIn("SPECIFICATION_INTEGRITY_ERROR", codes)
            self.assertEqual(evaluation.exit_code(result), 5)
            traced = json.loads((out / "exception.json").read_text())
            self.assertEqual(traced["type"], "KeyError")
            self.assertIn("Traceback (most recent call last)", traced["traceback"])
            self.assertIn("normalized_evaluation.py", traced["traceback"])
            manifest = json.loads((out / "manifest.json").read_text())
            self.assertIn("exception.json", manifest["files"])
