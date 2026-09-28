"""Stateful application seam checks and independent fault discrimination."""

from __future__ import annotations

import json
import sqlite3
import tempfile
import unittest
from pathlib import Path

from harness.runtime import ROOT
from harness.signal_evaluation import load_contract, run
from rebuilt.signals import SemanticEvidence


class SignalSafetyTests(unittest.TestCase):
    temporary: tempfile.TemporaryDirectory
    folder: Path
    result: dict

    @classmethod
    def setUpClass(cls):
        cls.temporary = tempfile.TemporaryDirectory(dir=ROOT / "evidence", prefix="signal-test-")
        cls.folder = Path(cls.temporary.name)
        cls.result = run(cls.folder)

    @classmethod
    def tearDownClass(cls):
        cls.temporary.cleanup()

    def test_same_derived_relations_preserve_inherited_failures(self):
        self.assertEqual(self.result["implementations"]["candidate"]["status"], "PASS")
        self.assertEqual(self.result["implementations"]["inherited"]["status"], "FAIL")
        for key in ["inherited", "candidate"]:
            actual = self.result["implementations"][key]["findings"]
            expected = sum(len(s["expected"]) for s in load_contract()["steps"])
            self.assertEqual(len(actual), expected)

    def test_all_three_application_faults_are_detected(self):
        for name in ("duplicate", "never", "memory"):
            with self.subTest(name=name):
                self.assertTrue(self.result["fault_controls"][name]["rejected"])
        failures = self.result["fault_controls"]["memory"]["findings"]
        self.assertTrue(
            any(
                f["step"] == "F" and f["relation"] == "initial" and f["status"] == "FAIL"
                for f in failures
            )
        )

    def test_unusable_helper_does_not_replace_last_valid_snapshot(self):
        first = json.loads((self.folder / "candidate/A/parser.json").read_text())
        with sqlite3.connect(self.folder / "candidate/decisions.sqlite") as conn:
            row = conn.execute(
                "SELECT source_sha256, payload FROM snapshots WHERE notice_id=?",
                (first["notice_id"],),
            ).fetchone()
            keys = conn.execute("SELECT event_key FROM initial_decisions").fetchall()
        self.assertEqual(row[0], first["input_sha256"])
        self.assertEqual(
            json.loads(row[1])["notice"]["validity_flags"],
            first["output"]["notice"]["validity_flags"],
        )
        expected_initials = sum(s["expected"]["initial"] for s in load_contract()["steps"])
        self.assertEqual(len(keys), expected_initials)
        bad = json.loads((self.folder / "candidate/unusable-impact/observation.json").read_text())
        # A firm disruption the rules decide without the failed helper stays a candidate
        # (spec-predicates Oracle answer), but is neither stored nor published.
        self.assertEqual(bad["decision"]["reason"], "FIRM_CANDIDATE")
        self.assertTrue(bad["decision"]["candidate_classification"])
        self.assertEqual(bad["decision"]["publication_reason"], "SEMANTICS_INCOMPLETE")
        self.assertEqual(bad["initial_count"], 0)

    def test_stage_failure_and_optional_fields_are_separate(self):
        self.assertEqual(SemanticEvidence(False, ()).refusal(), "EXTRACTION_UNAVAILABLE")
        self.assertEqual(
            SemanticEvidence(True, (("llm_assess_curtailment_impact", None),)).refusal(),
            "IMPACT_UNUSABLE",
        )
        self.assertIsNone(
            SemanticEvidence(True, (("llm_assess_curtailment_impact", "small"),)).refusal()
        )
        self.assertIsNone(SemanticEvidence(True, ()).refusal())


if __name__ == "__main__":
    unittest.main()
