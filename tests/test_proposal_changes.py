"""Proposal evidence must reveal declarations that captured outcomes cannot exercise."""

from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from harness.proposals import compare_cases, declaration_changes, run
from harness.runtime import ROOT


class ProposalChangeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.spec = (ROOT / "spec.md").read_text()

    def report(self, proposal: str) -> tuple[dict, Path]:
        baseline, proposed = self.root / "base.md", self.root / "proposed.md"
        baseline.write_text(self.spec)
        proposed.write_text(proposal)
        destination = self.root / "report"
        destination.mkdir()
        return run(proposed, str(baseline), destination), destination

    def edit(self, text: str, key: str, column: int, value: str) -> str:
        lines = text.splitlines(keepends=True)
        index = next(i for i, line in enumerate(lines) if line.startswith(key + " |"))
        fields = lines[index].strip().split(" | ")
        fields[column] = value
        lines[index] = " | ".join(fields) + "\n"
        return "".join(lines)

    def line(self, text: str, key: str) -> int:
        return next(i for i, line in enumerate(text.splitlines(), 1) if line.startswith(key))

    def test_unmatched_rule_edit_has_exact_snapshot_lines_and_saved_diff(self):
        proposal = "\n\n" + self.edit(self.spec, "BR-FORMAT", 2, "USABLE")
        result, destination = self.report(proposal)
        self.assertEqual(result["changed_outcomes"], [])
        rule = next(row for row in result["rules"] if row["id"] == "BR-FORMAT")
        self.assertEqual((rule["matches"], rule["wins"]), (0, 0))
        before_line = self.line(self.spec, "BR-FORMAT |")
        after_line = self.line(proposal, "BR-FORMAT |")
        self.assertEqual(
            result["declaration_changes"],
            [
                {
                    "block": "spec-rules",
                    "id": "BR-FORMAT",
                    "change": "edited",
                    "baseline_line": before_line,
                    "proposal_line": after_line,
                    "fields": {"Oracle answer": {"before": "ANY", "after": "USABLE"}},
                }
            ],
        )
        report = (destination / "REPORT.md").read_text()
        self.assertIn("Oracle answer: ANY → USABLE", report)
        for label, line in (("baseline", before_line), ("proposal", after_line)):
            self.assertIn(f"[spec.md:{line}]({label}-spec.md#L{line})", report)
        diff = (destination / "spec.diff").read_text()
        self.assertIn("--- baseline-spec.md\n+++ proposal-spec.md\n", diff)
        self.assertIn("-BR-FORMAT | UNSUPPORTED | ANY", diff)
        self.assertIn("+BR-FORMAT | UNSUPPORTED | USABLE", diff)
        manifest = json.loads((destination / "manifest.json").read_text())
        self.assertEqual(manifest["files"]["spec.diff"], hashlib.sha256(diff.encode()).hexdigest())
        self.assertEqual((destination / "baseline-spec.md").read_text(), self.spec)
        self.assertEqual((destination / "proposal-spec.md").read_text(), proposal)
        self.assertFalse(result["accepted"])
        self.assertFalse(result["review_recorded"])

    def test_parameter_and_input_declarations_are_visible_without_outcome_changes(self):
        proposal = self.edit(self.spec, "PARAM-INITIAL-001", 2, "0")
        proposal = self.edit(proposal, "INPUT-SOURCE-001", 3, "ERROR")
        proposal = self.edit(proposal, "IF-INPUT-014", 11, '"Reworded declaration."')
        result, destination = self.report(proposal)
        self.assertEqual(result["changed_outcomes"], [])
        changes = {row["id"]: row for row in result["declaration_changes"]}
        for key, field, value in (
            ("PARAM-INITIAL-001", "Value", "0"),
            ("INPUT-SOURCE-001", "Missing", "ERROR"),
            ("IF-INPUT-014", "Meaning", '"Reworded declaration."'),
        ):
            with self.subTest(declaration=key):
                self.assertEqual(changes[key]["fields"][field]["after"], value)
                self.assertEqual(changes[key]["baseline_line"], self.line(self.spec, key + " |"))
                self.assertEqual(changes[key]["proposal_line"], self.line(proposal, key + " |"))
                self.assertIn(key, (destination / "REPORT.md").read_text())
        self.assertEqual(set(changes), {"PARAM-INITIAL-001", "INPUT-SOURCE-001", "IF-INPUT-014"})
        self.assertEqual(
            result["parameter_changes"]["max_initial_alerts_per_event"],
            {"before": 1, "after": 0},
        )

    def test_precedence_edits_are_visible_and_line_shifts_are_not_edits(self):
        self.assertEqual(declaration_changes(self.spec, "\n\n" + self.spec), [])
        proposal = self.spec.replace(
            "Precedence: BR-FORMAT > BR-SEMANTICS",
            "Precedence: BR-SEMANTICS > BR-FORMAT",
        )
        changes = declaration_changes(self.spec, proposal)
        self.assertEqual(len(changes), 1)
        self.assertEqual(changes[0]["id"], "Precedence")
        self.assertEqual(changes[0]["baseline_line"], self.line(self.spec, "Precedence:"))
        self.assertTrue(changes[0]["fields"]["Order"]["after"].startswith("BR-SEMANTICS"))

    def test_added_and_removed_input_rows_have_only_existing_snapshot_references(self):
        old = "```spec-inputs\nID | Field\nINPUT-A | old\n```\n"
        new = "\n```spec-inputs\nID | Field\nINPUT-B | new\n```\n"
        changes = declaration_changes(old, new)
        self.assertEqual(
            [(r["id"], r["change"], r["baseline_line"], r["proposal_line"]) for r in changes],
            [("INPUT-A", "removed", 3, None), ("INPUT-B", "added", None, 4)],
        )

    def test_rule_identity_changes_are_distinct_from_action_changes(self):
        def case(key, rule, classification):
            return {
                "id": key,
                "notice_id": 1,
                "outcome": {"rule": rule, "action": {"classification": classification}},
            }

        changes = compare_cases(
            [case("rule", "A", "UNRESOLVED"), case("action", "A", "UNRESOLVED")],
            [case("rule", "B", "UNRESOLVED"), case("action", "A", "NON_SIGNAL")],
        )
        self.assertEqual(
            {r["id"]: (r["rule_changed"], r["action_changed"]) for r in changes},
            {"rule": (True, False), "action": (False, True)},
        )

    def test_prose_edits_and_missing_final_newline_are_retained_in_full_diff(self):
        proposal = self.spec + "\nProposed explanation outside the fixed tables."
        result, destination = self.report(proposal)
        self.assertEqual(result["declaration_changes"], [])
        self.assertEqual(result["changed_outcomes"], [])
        diff = (destination / "spec.diff").read_text()
        self.assertIn("+Proposed explanation outside the fixed tables.", diff)
        self.assertIn("\\ No newline at end of file", diff)
        self.assertIn("No fixed table declaration changed", (destination / "REPORT.md").read_text())


if __name__ == "__main__":
    unittest.main()
