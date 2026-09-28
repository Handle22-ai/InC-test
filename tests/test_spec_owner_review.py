"""Exact-byte owner review cannot change policy, activate a rejection or clear UNKNOWN."""

from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from pathlib import Path

from harness.rule_invariants import enforce
from harness.runtime import ROOT, digest
from harness.spec_compiler import artifacts, compile_spec
from harness.spec_ownership import PIN, REVIEW_LIMITS, reread, verify


class ExactSpecOwnerReviewTests(unittest.TestCase):
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
        self.name = "context/synthetic-owner-review.json"
        spec = self.root / "spec.md"
        spec.write_text(spec.read_text().replace(" | Thomas Hand | ", " | PENDING_PERSON | "))
        self.c = compile_spec(self.root)
        self.record = {
            "kind": "exact-spec-owner-review-v1",
            "spec_sha256": self.c["source_spec_sha256"],
            "repository_owner": "Synthetic Reviewer",
            "reviewer": "Synthetic Reviewer",
            "status": "reviewed-for-assessment",
            "decision_bodies": {
                row["ID"]: {k: v for k, v in row.items() if k != "_line"}
                for row in self.c["decisions"]
                if row["ID"] in {"ARCH-SOURCE-001", "TZ-NGPL-002"}
            },
            "limits": dict(REVIEW_LIMITS),
            "user_statement": "SYNTHETIC TEST ONLY. Review the exact spec for assessment.",
        }
        self.save_record()

    def save_record(self):
        (self.root / self.name).write_text(json.dumps(self.record))

    def read(self, decision="TZ-NGPL-002", person="Synthetic Reviewer"):
        return reread(decision, person, self.root, review_record=self.name)

    def test_identity_binding_preserves_spec_artifacts_and_unknown(self):
        before = (self.root / "spec.md").read_bytes()
        checks = enforce(self.c)
        generated = artifacts(self.c, self.root)
        pin = self.read()
        self.assertEqual(verify(self.root), pin)
        self.assertFalse(pin["approval"])
        self.assertEqual(pin["spec_sha256"], digest(self.root / "spec.md"))
        self.assertEqual((self.root / "spec.md").read_bytes(), before)
        self.assertEqual(artifacts(compile_spec(self.root), self.root), generated)
        self.assertEqual(enforce(compile_spec(self.root)), checks)
        self.assertTrue(any(row["status"] == "UNKNOWN" for row in checks))
        self.assertEqual(self.read("ARCH-SOURCE-001")["person"], "Synthetic Reviewer")

    def test_wrong_or_pending_name_and_rejected_decision_refuse(self):
        for person in ("", "PENDING_PERSON", "Another Reviewer"):
            with self.subTest(person=person), self.assertRaisesRegex(ValueError, "REVIEW_RECORD"):
                self.read(person=person)
        rejected = next(r for r in self.c["decisions"] if r["ID"] == "TZ-NGPL-001")
        self.record["decision_bodies"]["TZ-NGPL-001"] = {
            k: v for k, v in rejected.items() if k != "_line"
        }
        self.save_record()
        with self.assertRaisesRegex(ValueError, "REVIEW_RECORD"):
            self.read("TZ-NGPL-001")

    def test_other_covered_decision_body_cannot_drift(self):
        self.record["decision_bodies"]["ARCH-SOURCE-001"]["Decision"] = "Changed architecture"
        self.save_record()
        with self.assertRaisesRegex(ValueError, "REVIEW_RECORD"):
            self.read()

    def test_no_authority_or_unknown_escalation_in_record(self):
        for key in REVIEW_LIMITS:
            with self.subTest(key=key):
                self.record["limits"] = {**REVIEW_LIMITS, key: True}
                self.save_record()
                with self.assertRaisesRegex(ValueError, "REVIEW_RECORD"):
                    self.read()

    def test_altered_record_or_receipt_refuse(self):
        pin = self.read()
        self.record["user_statement"] += " changed"
        self.save_record()
        with self.assertRaisesRegex(ValueError, "REVIEW_RECORD"):
            verify(self.root)
        pin["review_record"]["sha256"] = digest(self.root / self.name)
        pin["person"] = "Another Reviewer"
        (self.root / PIN).write_text(json.dumps(pin))
        with self.assertRaisesRegex(ValueError, "REVIEW_RECORD"):
            verify(self.root)
        pin["person"] = "Synthetic Reviewer"
        pin["approval"] = True
        (self.root / PIN).write_text(json.dumps(pin))
        with self.assertRaisesRegex(ValueError, "not approval"):
            verify(self.root)

    def test_any_spec_edit_stales_receipt_and_review_record(self):
        self.read()
        with (self.root / "spec.md").open("a") as stream:
            stream.write("\n")
        with self.assertRaisesRegex(ValueError, "STALE_SPEC_PIN"):
            verify(self.root)
        with self.assertRaisesRegex(ValueError, "REVIEW_RECORD"):
            self.read()

    def test_missing_and_escaping_review_record_refuse(self):
        pin = self.read()
        for name in ("../outside.json", str((self.root / self.name).resolve())):
            pin["review_record"]["path"] = name
            (self.root / PIN).write_text(json.dumps(pin))
            with self.assertRaisesRegex(ValueError, "REVIEW_RECORD"):
                verify(self.root)
        (self.root / self.name).unlink()
        with self.assertRaisesRegex(ValueError, "review record missing"):
            self.read()
