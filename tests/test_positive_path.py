"""Owner-requested real-data, actionability and temporal approval controls."""

from __future__ import annotations

import copy
import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from harness import specification
from harness.normalized_evaluation import compare
from harness.runtime import ROOT
from harness.temporal_authority import SelfPromotion, record_precedes
from rebuilt.normalization import normalize
from rebuilt.normalized_classifier import classify
from rebuilt.signals import Authorization, RecommendationPublisher, SemanticEvidence


class PositivePathTests(unittest.TestCase):
    def capture(self, case_id):
        name = json.loads((ROOT / "requirements/trading-evidence.json").read_text())["captures"][0]
        return next(
            c
            for c in json.loads((ROOT / name).read_text())["cases"]
            if c["case_id"] == str(case_id)
        )

    def test_unknown_timezone_allows_candidate_but_blocks_authorization(self):
        case = self.capture(46624)
        clock = "2026-09-26T19:17:22+00:00"
        with tempfile.TemporaryDirectory() as directory:
            publisher = RecommendationPublisher(Path(directory) / "state.sqlite")
            try:
                auth = Authorization(
                    actor="synthetic test actor",
                    notice_id=case["notice_id"],
                    source_sha256=case["input_sha256"],
                    reference_time=clock,
                    materiality="MATERIAL",
                    actionable=True,
                    approved=True,
                    source_evidence="synthetic attempted authorization",
                    rationale="negative control",
                )
                for supplied_authorization in (None, auth):
                    result = publisher.decide(
                        case["output"],
                        case["input_sha256"],
                        SemanticEvidence(True, ()),
                        supplied_authorization,
                        clock,
                    )
                    self.assertEqual(result["publication_disposition"], "REVIEW_REQUIRED")
                    self.assertEqual(result["publication_reason"], "UNRESOLVED_SOURCE_TIME")
                    self.assertFalse(result["initial_decision"])
                self.assertEqual(
                    publisher.conn.execute("SELECT count(*) FROM initial_decisions").fetchone()[0],
                    0,
                )
            finally:
                publisher.close()
        self.assertEqual(result["classification"], "SIGNAL_CANDIDATE")
        self.assertFalse(result["recommendation_allowed"])
        self.assertEqual(result["normalized_input"]["facts"]["time_basis"], "UNRESOLVED")
        self.assertIsNone(result["normalized_input"]["facts"]["start_time"])
        self.assertEqual(result["publication_disposition"], "REVIEW_REQUIRED")
        self.assertEqual(result["publication_reason"], "UNRESOLVED_SOURCE_TIME")
        self.assertFalse(result["initial_decision"])
        self.assertEqual(result["actionability"]["source_timezone_status"], "UNKNOWN")
        self.assertFalse(result["actionability"]["automatic_current_future"])
        self.assertFalse(result["actionability"]["recommendation_authorized"])
        self.assertFalse(result["publication_attempted"])
        # Changing a captured final verdict/confidence cannot alter source facts.
        raw = copy.deepcopy(case["output"])
        raw["notice"].update(is_signal=0, confidence_score=0)
        value, _ = normalize(
            raw, case["input_sha256"], {"extraction_usable": True, "helpers": []}, clock, []
        )
        self.assertEqual(classify(value).proposal["classification"], "SIGNAL_CANDIDATE")
        self.assertTrue(value["normalization_trace"])

    def test_trusted_time_evaluates_intervals_without_authorizing_candidates(self):
        base = next(w["input"] for w in specification.fixtures() if w["id"] == "firm-positive")
        for name, basis, start, end, rule in (
            ("unknown", "UNRESOLVED", None, None, "BR-FIRM"),
            ("current", "UTC", "2026-01-01T00:00:00+00:00", "2026-02-01T00:00:00+00:00", "BR-FIRM"),
            ("future", "UTC", "2026-02-01T00:00:00+00:00", "2026-03-01T00:00:00+00:00", "BR-FIRM"),
            (
                "historical",
                "UTC",
                "2026-01-01T00:00:00+00:00",
                "2026-01-15T12:00:00+00:00",
                "BR-HISTORICAL",
            ),
        ):
            value = copy.deepcopy(base)
            value["reference_time"] = "2026-01-15T12:00:00+00:00"
            value["facts"].update(time_basis=basis, start_time=start, end_time=end)
            with self.subTest(case=name):
                decision = classify(value)
                self.assertEqual(decision.matched_rule, rule)
                self.assertFalse(decision.proposal["recommendation_allowed"])

    def test_unknown_row_cannot_hide_known_contradiction(self):
        case = self.capture(46795)
        for extra in (False, True):
            raw = copy.deepcopy(case["output"])
            if extra:
                raw["restrictions"].append(
                    {**raw["restrictions"][0], "restriction_type": "DAILY_LIMIT_PCT"}
                )
            value, _ = normalize(
                raw,
                case["input_sha256"],
                {"extraction_usable": True, "helpers": []},
                "2026-09-26T19:17:22+00:00",
                [],
            )
            with self.subTest(extra=extra):
                self.assertEqual(classify(value).matched_rule, "BR-CONTRADICTION")

    def test_units_and_resolved_historical_time(self):
        base = next(w["input"] for w in specification.fixtures() if w["id"] == "firm-positive")
        for kind in ("ABSOLUTE_CURTAILMENT", "HOURLY_LIMIT_PCT"):
            value = copy.deepcopy(base)
            value["facts"]["quantities"] = [
                {
                    "kind": kind,
                    "value": 20,
                    "unit": "PERCENT_MDQ",
                    "basis": "stated basis",
                    "evidence_ref": "source.fields.body",
                }
            ]
            with (
                self.subTest(kind=kind),
                self.assertRaisesRegex(ValueError, "Incompatible quantity"),
            ):
                classify(value)
        value = copy.deepcopy(base)
        value["facts"]["end_time"] = value["reference_time"]
        self.assertEqual(classify(value).matched_rule, "BR-HISTORICAL")
        value["facts"].update(time_basis="UNRESOLVED", start_time=None, end_time=None)
        self.assertEqual(classify(value).matched_rule, "BR-FIRM")

    def test_three_comparison_outcomes(self):
        previous: dict = {
            "source": {},
            "comparison_identity": {
                "policy": "same",
                "runtime_evaluator_publisher": {
                    "harness/evaluator.py": "v1",
                    "rebuilt/signals.py": "v1",
                },
            },
            "cases": {
                "F": {"status": "PASS", "output": {"count": 0}, "requirements": ["STATE-006"]}
            },
        }
        self.assertEqual(compare(previous, copy.deepcopy(previous))["status"], "PASS")
        current = copy.deepcopy(previous)
        current["cases"]["F"].update(status="FAIL", output={"count": 1})
        current["source"] = {"files": {"rebuilt/signals.py": "v2"}}
        self.assertEqual(compare(previous, current)["status"], "FAIL")
        current["cases"]["F"].update(status="PASS", output={"count": 0})
        current["source"]["files"]["harness/evaluator.py"] = "v2"
        self.assertEqual(
            compare(previous, current)["classification"], "EVALUATOR_OR_ORACLE_CHANGED"
        )


class TemporalApprovalTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.git("init", "-q")
        self.git("config", "user.name", "Synthetic temporal test")
        self.git("config", "user.email", "test@example.invalid")
        (self.root / "spec.md").write_text("old")
        self.commit("old")

    def git(self, *args):
        return subprocess.check_output(
            ["git", *args], cwd=self.root, stderr=subprocess.DEVNULL, text=True
        )

    def commit(self, message):
        self.git("add", ".")
        self.git("commit", "-qm", message)

    def test_uncommitted_and_same_commit_promotion_refused_even_after_later_commit(self):
        (self.root / "approval.json").write_text('{"status":"owner-approved"}')
        (self.root / "spec.md").write_text("new")
        with self.assertRaisesRegex(SelfPromotion, "UNAPPROVED_SELF_PROMOTION"):
            record_precedes(self.root, "approval.json", ("spec.md",))
        self.commit("same change")
        ceiling = self.git("rev-parse", "HEAD").strip()
        with self.assertRaisesRegex(SelfPromotion, "UNAPPROVED_SELF_PROMOTION"):
            record_precedes(self.root, "approval.json", ("spec.md",), approval_ceiling=ceiling)
        (self.root / "report.md").write_text("later evidence")
        self.commit("later evidence")
        with self.assertRaisesRegex(SelfPromotion, "UNAPPROVED_SELF_PROMOTION"):
            record_precedes(self.root, "approval.json", ("spec.md",), approval_ceiling=ceiling)

    def test_prior_approval_then_later_activation_is_allowed(self):
        (self.root / "approval.json").write_text('{"status":"owner-approved"}')
        self.commit("approval only")
        ceiling = self.git("rev-parse", "HEAD").strip()
        (self.root / "spec.md").write_text("new")
        self.commit("strict successor implementation")
        record_precedes(self.root, "approval.json", ("spec.md",), approval_ceiling=ceiling)

    def test_two_new_worker_commits_do_not_create_prior_approval(self):
        ceiling = self.git("rev-parse", "HEAD").strip()
        (self.root / "approval.json").write_text('{"status":"owner-approved"}')
        self.commit("worker calls its proposal approved")
        (self.root / "spec.md").write_text("new")
        self.commit("worker activates proposal")
        with self.assertRaisesRegex(SelfPromotion, "UNAPPROVED_SELF_PROMOTION"):
            record_precedes(self.root, "approval.json", ("spec.md",), approval_ceiling=ceiling)
