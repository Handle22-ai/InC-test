"""The engineer can measure adverse proposals without adopting them."""

from __future__ import annotations

import shutil
import tempfile
import unittest
from pathlib import Path

from harness.normalized_evaluation import exit_code
from harness.proposals import run
from harness.refusal_control import run as refusal_probe
from harness.rule_invariants import enforce, evaluate
from harness.runtime import ROOT, digest
from harness.spec_compiler import compile_spec
from harness.spec_ownership import proposal_scope, verify


class FeedbackLoopTests(unittest.TestCase):
    def test_proposal_exposes_lost_true_negatives_without_mutating_authority(self):
        names = [
            "spec.md",
            "context/spec-read-pin.json",
            "context/spec-owner-review.json",
            "requirements/behavior.yaml",
            "requirements/replay-expectations.json",
        ]
        before = {name: digest(ROOT / name) for name in names}
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            proposal = root / "proposal.md"
            lines = (ROOT / "spec.md").read_text().splitlines()
            index = next(i for i, line in enumerate(lines) if line.startswith("BR-ROUTINE |"))
            lines[index] = lines[index].rsplit(" | ", 1)[0] + " | UNRESOLVED"
            proposal.write_text("\n".join(lines) + "\n")
            out = root / "run"
            out.mkdir()
            result = run(proposal, str(ROOT / "spec.md"), out)
            self.assertFalse(result["accepted"])
            self.assertFalse(result["review_recorded"])
            self.assertEqual(len(result["changed_outcomes"]), 6)
            self.assertEqual([r["true_negative"] for r in result["before_labels"]], [3, 3])
            self.assertEqual([r["true_negative"] for r in result["after_labels"]], [0, 0])
            self.assertEqual(
                [r["true_positive"] for r in result["before_labels"]],
                [r["true_positive"] for r in result["after_labels"]],
            )
        self.assertEqual(before, {name: digest(ROOT / name) for name in names})

    def test_parameter_controls_the_check_and_prose_cannot_invert_it(self):
        text = (ROOT / "spec.md").read_text()
        first = compile_spec(text=text)
        next(r for r in first["state_safety"]["steps"] if r["id"] == "F")["expected"]["initial"] = 1
        with self.assertRaisesRegex(ValueError, "BOUNDARY_VIOLATION: .* one_initial"):
            enforce(first)
        counterfactual = compile_spec(
            text=text.replace("Maximum initial alerts | 1 |", "Maximum initial alerts | 2 |")
        )
        next(r for r in counterfactual["state_safety"]["steps"] if r["id"] == "F")["expected"][
            "initial"
        ] = 1
        with self.assertRaisesRegex(ValueError, "BOUNDARY_VIOLATION: .* one_initial"):
            enforce(counterfactual)
        inverted = compile_spec(
            text=text.replace(
                "must not exceed PARAM-INITIAL-001", "must be at least PARAM-INITIAL-001"
            )
        )
        prose = [r for r in evaluate(inverted) if r["kind"] == "prose_obligation"]
        self.assertTrue(all(r["status"] == r["constraint_status"] == "UNKNOWN" for r in prose))
        # Prose cannot redefine the parameter or its fixed no-duplicate boundary.
        self.assertEqual(inverted["parameters"]["max_initial_alerts_per_event"], 1)

    def test_proposal_scope_is_exact_temporary_and_does_not_write_a_receipt(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "requirements").mkdir()
            shutil.copyfile(ROOT / "spec.md", root / "spec.md")
            shutil.copyfile(
                ROOT / "requirements/rule-block.schema.json",
                root / "requirements/rule-block.schema.json",
            )
            with self.assertRaisesRegex(ValueError, "STALE_SPEC_PIN"):
                verify(root)
            with proposal_scope(root):
                result = verify(root)
                self.assertEqual(result["mode"], "PROPOSAL_ONLY")
                self.assertFalse(result["reviewed"])
                (root / "spec.md").write_text((root / "spec.md").read_text() + "\n")
                with self.assertRaisesRegex(ValueError, "STALE_SPEC_PIN"):
                    verify(root)
            self.assertFalse((root / "context/spec-read-pin.json").exists())
            with self.assertRaisesRegex(ValueError, "STALE_SPEC_PIN"):
                verify(root)

    def test_refusal_is_returned_and_retained_by_component_after_reopen(self):
        with tempfile.TemporaryDirectory() as directory:
            result = refusal_probe(Path(directory))
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(len(result["retained_after_reopen"]), 1)
        self.assertEqual(result["decision"]["classification"], "UNRESOLVED")
        self.assertEqual(result["accepted_snapshot_count"], 0)

    def test_skipped_validation_and_proposal_cannot_exit_as_acceptance(self):
        self.assertEqual(
            exit_code(
                {
                    "gates": {
                        "1": {"status": "UNKNOWN"},
                        "2": {"status": "UNKNOWN", "classification": "NOT_RUN"},
                    }
                }
            ),
            5,
        )
        self.assertEqual(
            exit_code(
                {"mode": "PROPOSAL_ONLY", "gates": {str(i): {"status": "PASS"} for i in (1, 2, 3)}}
            ),
            3,
        )
