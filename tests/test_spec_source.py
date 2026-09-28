"""Spec-source compiler, rule contradictions, input contract and ownership controls."""

from __future__ import annotations

import copy
import json
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from harness import consequences
from harness.domain_rules import derive
from harness.rule_invariants import enforce
from harness.runtime import ROOT
from harness.spec_compiler import artifacts, build, check_generated, compile_spec, refresh_for_gate
from harness.spec_ownership import reread, verify
from rebuilt.source_input import parse_field, timestamp


class SpecSourceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        for name in (
            "spec.md",
            "requirements/rule-block.schema.json",
            "requirements/normalized-witnesses.json",
        ):
            target = self.root / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / name, target)
        (self.root / "context").mkdir()

    def test_one_for_one_migration_and_no_predicate_language(self):
        c = compile_spec(self.root)
        self.assertEqual(len(c["rules"]), 9)
        self.assertEqual(len(c["state_safety"]["steps"]), 12)
        self.assertNotIn("feature_predicates", c)
        self.assertEqual(
            sum(r["kind"] == "prose_obligation" for r in enforce(c)), len(c["sentences"])
        )
        self.assertEqual(next(r for r in enforce(c) if r["id"] == "D1-010")["status"], "UNKNOWN")
        self.assertEqual(len({s["id"] for s in c["sentences"]}), len(c["sentences"]))

    def test_contradictory_spec_bounds_fail_at_the_spec_block(self):
        text = (
            (self.root / "spec.md")
            .read_text()
            .replace('"OUTPUT-002.maximum_mdq": 100', '"OUTPUT-002.maximum_mdq": 80')
        )
        with self.assertRaisesRegex(
            ValueError,
            r"spec.md:\d+: block spec-settings, row OUTPUT-002.maximum_mdq:.*contradicts",
        ):
            compile_spec(self.root, text)

    def test_input_declaration_and_malformed_collection_refuse(self):
        from rebuilt.normalization import normalize

        text = (
            (self.root / "spec.md")
            .read_text()
            .replace("header.notice_id | identifier", "header.notice_id | guess")
        )
        with self.assertRaisesRegex(ValueError, r"block spec-inputs, row INPUT-SOURCE-008"):
            compile_spec(self.root, text)
        c = compile_spec(self.root)
        with self.assertRaisesRegex(ValueError, "INPUT-SOURCE-030"):
            normalize(
                {
                    "notice": {
                        "notice_id": 1,
                        "status": "INITIATE",
                        "notice_type": "TEST",
                        "body_text": "body",
                    },
                    "restrictions": [17],
                },
                "0" * 64,
                {"extraction_usable": True},
                "2026-01-01T00:00:00+00:00",
                [],
                contract=c,
            )

    def test_domain_error_names_row_and_spec_line(self):
        text = (
            (self.root / "spec.md")
            .read_text()
            .replace("BR-FORMAT | UNSUPPORTED", "BR-FORMAT | NEW_OPERATOR", 1)
        )
        with self.assertRaisesRegex(ValueError, r"spec.md:\d+: block spec-rules, row BR-FORMAT"):
            compile_spec(self.root, text)

    def test_row_change_generates_all_views_and_expectations(self):
        before = build(self.root)
        old = artifacts(before, self.root)
        path = self.root / "spec.md"
        lines = path.read_text().splitlines()
        i = next(i for i, v in enumerate(lines) if v.startswith("BR-ROUTINE |"))
        lines[i] = lines[i].rsplit(" | ", 1)[0] + " | UNRESOLVED"
        path.write_text("\n".join(lines) + "\n")
        with self.assertRaisesRegex(ValueError, "GENERATED_ARTIFACT_DRIFT"):
            refresh_for_gate(self.root)
        after = build(self.root)
        new = artifacts(after, self.root)
        for name in (
            "requirements/behavior.yaml",
            "requirements/replay-expectations.json",
            "docs/signal-contract.md",
        ):
            self.assertNotEqual(old[name], new[name])
        enforce(after)
        value = next(
            r["input"]
            for r in json.loads((ROOT / "requirements/normalized-witnesses.json").read_text())
            if r["id"] == "routine-negative"
        )
        self.assertNotEqual(derive(before, value)["action"], derive(after, value)["action"])

    def test_manual_artifact_and_header_edit_refused(self):
        build(self.root)
        path = self.root / "requirements/behavior.yaml"
        original = path.read_text()
        for text in (
            "\n".join(original.splitlines()[1:]) + "\n",
            original.replace('"priority": 10', '"priority": 11', 1),
        ):
            path.write_text(text)
            with self.assertRaisesRegex(ValueError, "GENERATED_ARTIFACT_DRIFT"):
                check_generated(self.root)
        path.write_text(original)
        check_generated(self.root)

    def test_step_f_weakening_contradicts_named_d1_sentence(self):
        c = compile_spec(self.root)
        next(s for s in c["state_safety"]["steps"] if s["id"] == "F")["expected"]["initial"] = 1
        with self.assertRaisesRegex(ValueError, r"row D1-\d+: BOUNDARY_VIOLATION: .* one_initial"):
            enforce(c)

    def test_classification_clock_veto_and_unsafe_precedence_refused(self):
        c = compile_spec(self.root)
        next(r for r in c["rules"] if r["id"] == "BR-FIRM")["when"]["Source clock"] = "RESOLVED"
        with self.assertRaisesRegex(ValueError, "BOUNDARY_VIOLATION"):
            enforce(c)
        c = compile_spec(self.root)
        next(r for r in c["rules"] if r["id"] == "BR-ROUTINE")["priority"] = 1
        with self.assertRaisesRegex(ValueError, "BOUNDARY_VIOLATION"):
            enforce(c)

    def test_pin_is_a_read_receipt_and_stales_on_any_edit(self):
        path = self.root / "spec.md"
        text = path.read_text().replace(" | Thomas Hand | ", " | Synthetic Test Person | ")
        text = text.replace('  "owners": ["Thomas Hand"],\n', "")
        path.write_text(text)
        # This is a synthetic name in a disposable test, not authenticated approval.
        record = reread("ARCH-SOURCE-001", "Synthetic Test Person", self.root)
        self.assertFalse(record["approval"])
        verify(self.root)
        path.write_text(text + "\n")
        with self.assertRaisesRegex(ValueError, "STALE_SPEC_PIN"):
            verify(self.root)
        with self.assertRaisesRegex(ValueError, "new decision"):
            reread("ARCH-SOURCE-001", "Synthetic Test Person", self.root)

    def test_reread_without_decision_covers_every_change_since_the_last_read(self):
        path = self.root / "spec.md"
        path.write_text(
            path.read_text()
            .replace(" | Thomas Hand | ", " | Synthetic Test Person | ")
            .replace('  "owners": ["Thomas Hand"],\n', "")
        )
        first = reread("ARCH-SOURCE-001", "Synthetic Test Person", self.root)
        text = path.read_text()
        rows = [
            f"CHANGE-{n} | {status} | Synthetic Test Person | {first['spec_sha256']} | Test change {n}."
            for n, status in ((1, "approved"), (2, "proposed"))
        ]
        anchor = next(line for line in text.splitlines() if line.startswith("ARCH-SOURCE-001 |"))
        path.write_text(text.replace(anchor, anchor + "\n" + "\n".join(rows)))
        with self.assertRaisesRegex(ValueError, "CHANGE-2: row must be approved"):
            reread(None, "Synthetic Test Person", self.root)
        path.write_text(path.read_text().replace("CHANGE-2 | proposed", "CHANGE-2 | approved"))
        pin = reread(None, "Synthetic Test Person", self.root)
        self.assertEqual(sorted(pin["decisions"]), ["CHANGE-1", "CHANGE-2"])
        verify(self.root)
        # Editing a covered row after the reread makes the receipt stale.
        path.write_text(path.read_text().replace("Test change 1.", "Test change one."))
        with self.assertRaises(ValueError):
            verify(self.root)

    def test_hand_edited_predicate_names_its_spec_row(self):
        build(self.root)
        path = self.root / "requirements/behavior.yaml"
        path.write_text(path.read_text().replace('"op": "within"', '"op": "overlaps"', 1))
        with self.assertRaisesRegex(ValueError, r"block spec-predicates, row History=COMPLETE"):
            check_generated(self.root)

    def test_a_crash_inside_the_component_is_a_failure_not_a_refusal(self):
        from harness.normalized_evaluation import crashed_in_component
        from rebuilt.rule_engine import check_schema

        try:
            check_schema({"x": 1}, {"type": "object", "additionalProperties": False})
        except ValueError as exc:
            self.assertTrue(crashed_in_component(exc))
        try:
            compile_spec(self.root, "not a spec")
        except ValueError as exc:
            self.assertFalse(crashed_in_component(exc))

    def test_only_a_listed_owner_can_reread_or_register(self):
        from harness import baseline

        path = self.root / "spec.md"
        text = path.read_text().replace(" | Thomas Hand | ", " | Synthetic Test Person | ")
        if '"owners"' not in text:
            text = text.replace(
                '  "sets": {', '  "owners": ["Synthetic Test Person"],\n  "sets": {', 1
            )
        else:
            text = text.replace('"owners": ["Thomas Hand"]', '"owners": ["Synthetic Test Person"]')
        path.write_text(text)
        with self.assertRaisesRegex(ValueError, "not a spec owner"):
            reread("ARCH-SOURCE-001", "Somebody Else", self.root)
        reread("ARCH-SOURCE-001", "Synthetic Test Person", self.root)
        with self.assertRaisesRegex(ValueError, "not a spec owner"):
            baseline.require_owner("Somebody Else", self.root)
        baseline.require_owner("Synthetic Test Person", self.root)

    def test_declared_types_and_dates_refuse_fabrication(self):
        c = compile_spec(self.root)
        self.assertEqual(timestamp("2026-01-14", c), (None, None))
        self.assertEqual(timestamp("01/14/2026 12:00:00PM", c), (None, None))
        self.assertEqual(timestamp("2026-01-14T12:00:00-06:00", c)[0], "2026-01-14T18:00:00+00:00")
        self.assertIsNotNone(timestamp("02/30/2026", c)[1])
        row = next(r for r in c["input_contract"] if r["Field"] == "header.notice_id")
        self.assertEqual(parse_field(row, "id12", c)["status"], "ERROR")
        self.assertEqual(parse_field(row, None, c)["status"], "ERROR")

    def test_consequences_cover_every_case_rule_and_first_failure(self):
        c = compile_spec(self.root)
        rows = consequences.observations(c)
        self.assertEqual(len(rows), 46)
        firm = [next(x for x in row["conditions"] if x["rule"] == "BR-FIRM") for row in rows]
        self.assertGreater(sum(x["matched"] for x in firm), 0)
        for row in rows:
            self.assertEqual(len(row["conditions"]), 9)
            for condition in row["conditions"]:
                self.assertEqual(condition["first_failed"] is None, condition["matched"])
        other = copy.deepcopy(c)
        next(r for r in other["rules"] if r["id"] == "BR-UNRESOLVED")["action"]["disposition"] = (
            "ERROR"
        )
        self.assertNotEqual(
            [r["outcome"] for r in rows], [r["outcome"] for r in consequences.observations(other)]
        )

    def test_invariants_run_before_any_component(self):
        from harness.normalized_evaluation import run

        c = compile_spec(self.root)
        next(r for r in c["state_safety"]["steps"] if r["id"] == "F")["expected"]["initial"] = 1
        destination = self.root / "run"
        destination.mkdir()
        with (
            patch("harness.spec_compiler.refresh_for_gate", return_value=c),
            patch("harness.consequences.run") as component,
        ):
            result = run(destination)
        component.assert_not_called()
        self.assertIn("BOUNDARY_VIOLATION", result["findings"][0]["reason"])
