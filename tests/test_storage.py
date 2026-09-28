"""Synthetic boundary/fault tests plus real captured storage regression assertions."""

from __future__ import annotations

import copy
import json
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

import yaml

from harness.context import select, write_package
from harness.runtime import ROOT
from harness.storage_evaluation import compare, fixtures_from_capture
from rebuilt.snapshot import InvalidSnapshot, NoticeSnapshot
from rebuilt.store import ContentConflict, SnapshotStore, StorageError


def synthetic_snapshot() -> NoticeSnapshot:
    """Shape seeded from a capture; all test identities/content are explicitly synthetic."""
    fixture = next(row for row in fixtures_from_capture() if row["case_id"] == "seed")
    output = copy.deepcopy(fixture["output"])
    output["notice"].update(
        notice_id=800001,
        body_text="SYNTHETIC test notice",
        prior_notice_id=None,
        html_file="synthetic.html",
        subject="SYNTHETIC",
        scraped_at="synthetic",
    )
    for row in output["locations"] + output["restrictions"]:
        row["notice_id"] = 800001
    return NoticeSnapshot.from_output(output, "a" * 64)


class SnapshotTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.path = Path(self.directory.name) / "store.sqlite"
        self.store = SnapshotStore(self.path)
        self.addCleanup(lambda: self.store.close())
        self.snapshot = synthetic_snapshot()

    def test_identical_replay_and_restart_receipt(self):
        self.assertEqual(self.store.write(self.snapshot).disposition, "created")
        self.assertEqual(self.store.write(self.snapshot).disposition, "replayed")
        self.store.close()
        self.store = SnapshotStore(self.path)
        self.assertEqual(self.store.write(self.snapshot).disposition, "replayed")
        self.assertEqual(self.store.read(800001), self.snapshot)
        self.assertEqual(len(self.store.all()), 1)

    def test_same_source_refresh_replaces_current_observations(self):
        self.store.write(self.snapshot)
        updated = replace(self.snapshot, restrictions=self.snapshot.restrictions[:1])
        self.assertEqual(self.store.write(updated).disposition, "refreshed")
        self.assertEqual(self.store.read(800001), updated)

    def test_changed_source_conflict_is_explicit_and_nonmutating(self):
        self.store.write(self.snapshot)
        with self.assertRaises(ContentConflict):
            self.store.write(replace(self.snapshot, source_sha256="b" * 64))
        self.assertEqual(self.store.read(800001), self.snapshot)
        self.store.close()
        self.store = SnapshotStore(self.path)
        self.assertEqual(self.store.read(800001), self.snapshot)

    def test_invalid_joins_do_not_write_partial_snapshot(self):
        malformed = replace(self.snapshot, locations=())
        with self.assertRaises(InvalidSnapshot):
            self.store.write(malformed)
        self.assertEqual(self.store.all(), ())

    def test_duplicate_location_and_cross_notice_child_rejected(self):
        for bad in [
            replace(self.snapshot, locations=self.snapshot.locations * 2),
            replace(
                self.snapshot, restrictions=(replace(self.snapshot.restrictions[0], notice_id=7),)
            ),
        ]:
            with self.assertRaises(InvalidSnapshot):
                self.store.write(bad)
        self.assertEqual(self.store.all(), ())

    def test_runtime_schema_and_unknown_fields_rejected(self):
        for key, value in [("notice_id", "800001"), ("unexpected", "field")]:
            output = self.snapshot.output()
            output["notice"][key] = value
            with self.assertRaises(InvalidSnapshot):
                NoticeSnapshot.from_output(output, "a" * 64)

    def test_transaction_failure_has_no_receipt_or_partial_refresh(self):
        self.store.write(self.snapshot)
        self.store.connection.execute("""CREATE TRIGGER synthetic_failure BEFORE UPDATE ON snapshots
            BEGIN SELECT RAISE(ABORT, 'synthetic injected write failure'); END""")
        with self.assertRaises(StorageError):
            self.store.write(replace(self.snapshot, restrictions=()))
        self.assertEqual(self.store.read(800001), self.snapshot)
        self.store.close()
        self.store = SnapshotStore(self.path)
        self.assertEqual(self.store.read(800001), self.snapshot)

    def test_distinct_revision_retains_prior_and_children(self):
        self.store.write(self.snapshot)
        output = self.snapshot.output()
        output["notice"].update(notice_id=800002, prior_notice_id=800001, status="SUPERSEDE")
        for row in output["locations"] + output["restrictions"]:
            row["notice_id"] = 800002
        revision = NoticeSnapshot.from_output(output, "b" * 64)
        self.store.write(revision)
        self.store.write(revision)
        self.assertEqual(self.store.read(800001), self.snapshot)
        self.assertEqual(self.store.chain(800002).snapshots, (self.snapshot, revision))

    def test_missing_prior_and_cycle_are_visible(self):
        missing = replace(
            self.snapshot, notice=replace(self.snapshot.notice, prior_notice_id=700001)
        )
        self.store.write(missing)
        self.assertEqual(self.store.chain(800001).missing_prior_id, 700001)
        cycle = replace(missing, notice=replace(missing.notice, prior_notice_id=800001))
        self.store.write(cycle)
        with self.assertRaises(StorageError):
            self.store.chain(800001)

    def test_corrupt_readback_is_not_silent(self):
        self.store.write(self.snapshot)
        self.store.connection.execute("UPDATE snapshots SET payload='{}'")
        self.store.connection.commit()
        with self.assertRaises(StorageError):
            self.store.read(800001)


class ContextAndEvaluationTests(unittest.TestCase):
    def test_selector_distinguishes_component_checks_from_specified_only_policy(self):
        package = select("notice-snapshot-rebuild")
        self.assertEqual(len(package["required_gates"]), 3)
        self.assertTrue(
            all(
                r["validation"]["check"] != "out_of_scope"
                for r in package["requirements"]
                if r["role"] == "binding"
            )
        )
        self.assertTrue(
            any(
                r["id"] == "STATE-005"
                and r["role"] == "specified_only"
                and r["approval"] == "owner-approved"
                and r["check_status"] == "not_available"
                for r in package["requirements"]
            )
        )
        self.assertTrue(all(a["why"] and a["sha256"] for a in package["artifacts"]))
        self.assertNotIn("superseded", [a["status"] for a in package["artifacts"]])

    def test_unknown_task_fails_closed(self):
        with self.assertRaises(ValueError):
            select("invented task")

    def test_selector_derives_deferred_scope_even_if_manifest_calls_it_binding(self):
        manifest = yaml.safe_load((ROOT / "context/manifest.yaml").read_text())
        manifest["task_profiles"]["notice-snapshot-rebuild"]["binding_requirements"].append(
            "STATE-005"
        )
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "manifest.yaml"
            path.write_text(yaml.safe_dump(manifest))
            package = select("notice-snapshot-rebuild", path)
            row = next(r for r in package["requirements"] if r["id"] == "STATE-005")
            self.assertEqual(row["role"], "specified_only")

    def test_package_retains_selected_content_and_cannot_overwrite(self):
        with tempfile.TemporaryDirectory() as directory:
            destination = Path(directory)
            package = write_package("notice-snapshot-rebuild", destination)
            self.assertEqual(json.loads((destination / "package.json").read_text()), package)
            with self.assertRaises(FileExistsError):
                write_package("notice-snapshot-rebuild", destination)

    def test_regression_reports_removed_or_new_failure(self):
        finding = {"requirement_id": "STATE-002", "case_id": "synthetic", "status": "PASS"}
        self.assertEqual(compare([finding], [])["status"], "FAIL")
        self.assertEqual(
            len(compare([finding], [{**finding, "status": "FAIL"}])["newly_failing"]), 1
        )
        self.assertEqual(compare([], [finding])["status"], "UNKNOWN")


if __name__ == "__main__":
    unittest.main()
