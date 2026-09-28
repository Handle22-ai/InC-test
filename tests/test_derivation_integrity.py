"""Independent witness and approval-trace mutations; never adopt their policy."""

from __future__ import annotations

import copy
import json
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from harness import behavior_contract as behavior
from harness import context, predicates, specification
from harness.runtime import ROOT


class PredicateWitnessTests(unittest.TestCase):
    def setUp(self):
        self.contract = behavior.load()
        self.examples = {row["id"]: row for row in specification.fixtures()}

    def test_restored_semantics_and_candidate_scope(self):
        row = specification.evaluate_witness(
            self.contract, self.examples["overlap-unusable-routine"]
        )
        self.assertEqual(row["active_expectation"]["action"]["disposition"], "ERROR")
        self.assertEqual(row["evaluation_status"], "READY")
        for name in ("firm-positive", "planned-positive", "primary-only-positive"):
            row = specification.evaluate_witness(self.contract, self.examples[name])
            self.assertEqual(row["evaluation_status"], "READY")
            self.assertEqual(
                row["active_expectation"]["action"],
                {
                    "classification": "SIGNAL_CANDIDATE",
                    "disposition": "CANDIDATE_ONLY",
                    "recommendation_allowed": False,
                },
            )

    def test_domain_column_mutations_cannot_rewrite_frozen_witnesses(self):
        originals = copy.deepcopy(self.examples)
        for column, value, affected in [
            ("Service class", "OTHER", "firm-positive"),
            ("Service class", "OTHER", "primary-only-positive"),
            ("Source clock", "UNRESOLVED", "firm-positive"),
        ]:
            variant = copy.deepcopy(self.contract)
            next(r for r in variant["rules"] if r["id"] == "BR-FIRM")["when"][column] = value
            with self.subTest(column=column, affected=affected):
                after = specification.evaluate_witness(variant, self.examples[affected])
                self.assertEqual(after["evaluation_status"], "FAIL")
                self.assertEqual(after["finding"]["code"], "CONTRACT_CONTRADICTS_FIXTURE")
                self.assertEqual(after["prospective_expectation"], "SIGNAL_CANDIDATE")
                self.assertEqual(
                    after["active_expectation"]["action"]["classification"], "UNRESOLVED"
                )
        self.assertEqual(originals, self.examples)

    def test_routine_action_and_history_precedence_cannot_rewrite_expectations(self):
        for name, rule_id, mutation in [
            ("routine-negative", "BR-ROUTINE", "action"),
            ("missing-prior", "BR-HISTORY", "priority"),
        ]:
            variant = copy.deepcopy(self.contract)
            rule = next(row for row in variant["rules"] if row["id"] == rule_id)
            if mutation == "action":
                rule["action"]["classification"] = "SIGNAL_CANDIDATE"
            else:
                rule["priority"] = 85
            result = specification.evaluate_witness(variant, self.examples[name])
            self.assertEqual(result["evaluation_status"], "FAIL")
            self.assertEqual(result["finding"]["code"], "CONTRACT_CONTRADICTS_FIXTURE")
            self.assertEqual(
                result["prospective_expectation"], self.examples[name]["prospective_expectation"]
            )

    def test_remains_wording_does_not_authorize_a_disposition_change(self):
        variant = copy.deepcopy(self.contract)
        rule = next(row for row in variant["rules"] if row["id"] == "BR-SEMANTICS")
        rule["basis"] = "Owner said unusable semantics remains REVIEW_REQUIRED"
        rule["action"]["disposition"] = "REVIEW_REQUIRED"
        result = specification.evaluate_witness(variant, self.examples["overlap-unusable-routine"])
        self.assertEqual(result["evaluation_status"], "FAIL")

    def test_generic_operators_and_unknown_syntax(self):
        values = {
            "left": "x",
            "other": "x",
            "array": ["x", "y"],
            "later": "2026-02-01T00:00:01Z",
            "earlier": "2026-02-01T00:00:00Z",
        }
        expressions: list[dict] = [
            {"operator": "eq", "field": "left", "value_field": "other"},
            {"operator": "in", "field": "left", "values": ["x"]},
            {"operator": "contains_any", "field": "array", "values": ["y"]},
            {"operator": "after", "field": "later", "value_field": "earlier"},
        ]
        for expression in expressions:
            predicates.validate(expression)
            self.assertTrue(predicates.evaluate(expression, values))
        with self.assertRaisesRegex(ValueError, "Unsupported predicate"):
            predicates.validate({"operator": "python", "value": "anything"})
        with self.assertRaisesRegex(ValueError, "exactly one"):
            predicates.validate(
                {"operator": "eq", "field": "left", "value": "x", "value_field": "other"}
            )
        with self.assertRaisesRegex(ValueError, "nonempty"):
            predicates.validate({"operator": "any", "conditions": []})
        self.assertFalse(
            predicates.evaluate({"operator": "eq", "field": "n", "value": True}, {"n": 1})
        )

    def test_semantic_fixture_hash_excludes_timing_and_run_identity(self):
        with tempfile.TemporaryDirectory(dir=ROOT / "evidence") as directory:
            results = []
            for name in ("one", "two"):
                destination = Path(directory) / name
                destination.mkdir()
                with (
                    patch.object(specification, "prior_loaded", return_value={}),
                    patch.object(specification, "baseline_fallback", return_value={}),
                    patch.object(specification, "provenance", return_value={}),
                    patch.object(specification, "derivations", return_value={}),
                ):
                    results.append(specification.run(destination))
                rows = json.loads((destination / "builder-evaluation-fixtures.json").read_text())
                self.assertTrue(all("derivation_ms" not in row for row in rows))
                self.assertEqual(
                    len(json.loads((destination / "timings.json").read_text())), len(rows)
                )
            self.assertEqual(results[0]["fixture_sha256"], results[1]["fixture_sha256"])

    def test_context_refuses_contract_and_generated_view_drift(self):
        for name in ("requirements/behavior.yaml", "docs/signal-contract.md"):
            with tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                for source in [
                    "spec.md",
                    "requirements/rule-block.schema.json",
                    "requirements/normalized-witnesses.json",
                    "requirements/behavior.yaml",
                    "requirements/signal-safety.yaml",
                    "context/authority-reference.json",
                    "docs/signal-contract.md",
                ]:
                    target = root / source
                    target.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copyfile(ROOT / source, target)
                path = root / name
                path.write_text(path.read_text() + "\n# unregistered drift\n")
                with (
                    patch.object(behavior, "ROOT", root),
                    patch.object(behavior, "CONTRACT", root / "requirements/behavior.yaml"),
                ):
                    with self.assertRaisesRegex(ValueError, "GENERATED_ARTIFACT_DRIFT"):
                        context.select("recommendation-classification-maintenance")


class SpecDecisionTraceTests(unittest.TestCase):
    """Named read receipts replace the historical writable ADR promotion authority."""

    def setUp(self):
        from harness.spec_compiler import build
        from harness.spec_ownership import PIN, reread
        from tests.authority_fixture import copy_requirement_authority

        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        copy_requirement_authority(self.root)
        (self.root / PIN).unlink(missing_ok=True)
        self.path = self.root / "spec.md"
        text = self.path.read_text()
        lines = text.splitlines()
        index = next(i for i, s in enumerate(lines) if s.startswith("ARCH-SOURCE-001 |"))
        fields = lines[index].split(" | ")
        fields[2] = "Synthetic Test Person"
        lines[index] = " | ".join(fields)
        self.path.write_text("\n".join(lines) + "\n")
        build(self.root)
        self.pin = reread("ARCH-SOURCE-001", "Synthetic Test Person", self.root)

    def test_exact_named_receipt_has_no_approval_claim(self):
        from harness.spec_ownership import verify

        self.assertEqual(verify(self.root), self.pin)
        self.assertFalse(self.pin["approval"])

    def test_standalone_artifact_repin_is_not_authority(self):
        from harness.spec_compiler import check_generated

        path = self.root / "requirements/behavior.yaml"
        path.write_text(path.read_text().replace('"priority": 10', '"priority": 11', 1))
        with self.assertRaisesRegex(ValueError, "GENERATED_ARTIFACT_DRIFT"):
            check_generated(self.root)

    def test_any_spec_edit_stales_receipt_even_after_compile(self):
        from harness.spec_compiler import build
        from harness.spec_ownership import verify

        self.path.write_text(self.path.read_text() + "\n")
        build(self.root)
        with self.assertRaisesRegex(ValueError, "STALE_SPEC_PIN"):
            verify(self.root)

    def test_unrecorded_edit_cannot_reuse_old_decision(self):
        from harness.spec_ownership import reread

        self.path.write_text(self.path.read_text() + "\n")
        with self.assertRaisesRegex(ValueError, "new decision"):
            reread("ARCH-SOURCE-001", "Synthetic Test Person", self.root)

    def test_new_decision_requires_previous_read_hash(self):
        from harness.spec_ownership import reread

        text = self.path.read_text()
        row = "NEW-DECISION | owner-requested | Synthetic Test Person | WRONG | Synthetic editorial change"
        text = text.replace("TZ-NGPL-001 |", row + "\nTZ-NGPL-001 |")
        self.path.write_text(text)
        with self.assertRaisesRegex(ValueError, "previous read spec hash"):
            reread("NEW-DECISION", "Synthetic Test Person", self.root)
        self.path.write_text(text.replace(" | WRONG |", " | " + self.pin["spec_sha256"] + " |"))
        new = reread("NEW-DECISION", "Synthetic Test Person", self.root)
        self.assertEqual(new["previous_read"], self.pin)
        self.assertFalse(new["approval"])

    def test_wrong_person_and_inactive_decision_refused(self):
        from harness.spec_ownership import reread

        with self.assertRaisesRegex(ValueError, "named recorded decision"):
            reread("ARCH-SOURCE-001", "Different Person", self.root)
        with self.assertRaisesRegex(ValueError, "named recorded decision"):
            reread("TZ-NGPL-001", "Synthetic Test Person", self.root)

    def test_missing_and_tampered_receipts_refused(self):
        from harness.spec_ownership import PIN, verify

        path = self.root / PIN
        pin = json.loads(path.read_text())
        pin["person"] = "Different Person"
        path.write_text(json.dumps(pin))
        with self.assertRaisesRegex(ValueError, "UNRECORDED_SPEC_CHANGE"):
            verify(self.root)
        path.unlink()
        with self.assertRaisesRegex(ValueError, "STALE_SPEC_PIN"):
            verify(self.root)


if __name__ == "__main__":
    unittest.main()
