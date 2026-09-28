"""Rebuilt-only technical extension checks; fixtures are explicitly synthetic.

These do not add requirements to the unchanged shared storage acceptance suite.
"""

from __future__ import annotations

import hashlib
import json
import shutil
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path
from typing import Any
from unittest.mock import patch

from rebuilt.snapshot import InvalidSnapshot, NoticeSnapshot
from rebuilt.store import ContentConflict, SnapshotStore, StorageError

ROOT = Path(__file__).resolve().parents[1]
OLD_FIXTURE = ROOT / "evidence/maintenance/20260926T201903.969882Z"


class CaptureReferenceTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.path = Path(self.directory.name) / "synthetic.sqlite"
        fixture = json.loads((OLD_FIXTURE / "pre_change_synthetic.json").read_text())
        old_database = OLD_FIXTURE / "pre_change_synthetic.sqlite"
        self.assertTrue(fixture["synthetic"])
        self.assertEqual(
            hashlib.sha256(old_database.read_bytes()).hexdigest(), fixture["database_sha256"]
        )
        shutil.copyfile(old_database, self.path)
        self.snapshot = NoticeSnapshot.from_output(fixture["output"], fixture["source_sha256"])
        self.store = SnapshotStore(self.path)
        self.addCleanup(lambda: self.store.close())

    def reopen(self):
        self.store.close()
        self.store = SnapshotStore(self.path)

    def read_existing(self) -> NoticeSnapshot:
        snapshot = self.store.read(990001)
        assert snapshot is not None, "Expected the synthetic persisted notice"
        return snapshot

    def test_prechange_writer_record_and_existing_callers_default_to_none(self):
        stored_document = json.loads(
            self.store.connection.execute("SELECT payload FROM snapshots").fetchone()[0]
        )
        self.assertNotIn("capture_reference", stored_document)
        positional = NoticeSnapshot(
            self.snapshot.source_sha256,
            self.snapshot.notice,
            self.snapshot.locations,
            self.snapshot.restrictions,
        )
        self.assertIsNone(positional.capture_reference)
        self.assertEqual(self.store.read(990001), positional)
        self.assertEqual(self.store.write(positional).disposition, "replayed")
        self.reopen()
        self.assertIsNone(self.read_existing().capture_reference)

    def test_reference_roundtrips_verbatim_and_is_never_dereferenced(self):
        for reference in ("synthetic://maintenance/capture-001", "", "SYNTHETIC opaque\n雪"):
            with (
                self.subTest(reference=reference),
                patch("socket.socket", side_effect=AssertionError("No network")),
            ):
                snapshot = NoticeSnapshot.from_output(
                    self.snapshot.output(), self.snapshot.source_sha256, capture_reference=reference
                )
                self.store.write(snapshot)
                self.reopen()
                actual = self.read_existing()
                self.assertEqual(actual.capture_reference, reference)
                self.assertEqual(actual.output(), self.snapshot.output())
                self.assertEqual(self.store.all(), (snapshot,))

    def test_exact_envelope_replay_after_restart_does_not_duplicate(self):
        snapshot = replace(self.snapshot, capture_reference="synthetic://maintenance/replay")
        self.store.write(snapshot)
        self.reopen()
        receipt = self.store.write(snapshot)
        self.assertEqual(receipt.disposition, "replayed")
        self.assertEqual(receipt.notice_id, self.snapshot.notice.notice_id)
        self.assertEqual(receipt.source_sha256, self.snapshot.source_sha256)
        self.assertEqual(self.store.all(), (snapshot,))

    def test_metadata_only_refresh_preserves_identity_and_shared_payload(self):
        for reference in ("synthetic://maintenance/first", "synthetic://maintenance/second", None):
            snapshot = replace(self.snapshot, capture_reference=reference)
            receipt = self.store.write(snapshot)
            self.assertEqual(receipt.disposition, "refreshed")
            self.assertEqual(
                (receipt.notice_id, receipt.source_sha256), (990001, self.snapshot.source_sha256)
            )
            self.reopen()
            actual = self.read_existing()
            self.assertEqual(actual.capture_reference, reference)
            self.assertEqual(actual.output(), self.snapshot.output())
            self.assertEqual(len(self.store.all()), 1)

    def test_same_source_extraction_refresh_keeps_supplied_reference(self):
        snapshot = replace(self.snapshot, capture_reference="synthetic://maintenance/refresh")
        self.store.write(snapshot)
        updated = replace(snapshot, restrictions=snapshot.restrictions[:1])
        self.assertEqual(self.store.write(updated).disposition, "refreshed")
        self.reopen()
        self.assertEqual(self.store.read(990001), updated)

    def test_changed_source_conflict_preserves_payload_and_reference(self):
        snapshot = replace(self.snapshot, capture_reference="synthetic://maintenance/original")
        self.store.write(snapshot)
        with self.assertRaises(ContentConflict):
            self.store.write(
                replace(
                    snapshot,
                    source_sha256="b" * 64,
                    capture_reference="synthetic://maintenance/rejected",
                )
            )
        self.reopen()
        self.assertEqual(self.store.all(), (snapshot,))

    def test_invalid_reference_rejected_before_mutation(self):
        # Deliberately malformed runtime inputs; the constructor contract is under test.
        invalid_values: tuple[Any, ...] = (123, True, ["synthetic"], {"reference": "synthetic"})
        for invalid in invalid_values:
            with self.subTest(invalid=invalid), self.assertRaises(InvalidSnapshot):
                self.store.write(replace(self.snapshot, capture_reference=invalid))
        self.assertEqual(self.store.read(990001), self.snapshot)

    def test_explicit_null_is_compatible_but_corrupt_type_is_reported(self):
        for value in (None, 123):
            document = {**self.snapshot.output(), "capture_reference": value}
            self.store.connection.execute("UPDATE snapshots SET payload=?", (json.dumps(document),))
            self.store.connection.commit()
            self.reopen()
            if value is None:
                self.assertIsNone(self.read_existing().capture_reference)
            else:
                with self.assertRaises(StorageError):
                    self.store.read(990001)

    def test_distinct_notice_chain_preserves_each_reference(self):
        prior = replace(self.snapshot, capture_reference="synthetic://maintenance/prior")
        self.store.write(prior)
        current = replace(
            prior,
            source_sha256="b" * 64,
            capture_reference="synthetic://maintenance/current",
            notice=replace(prior.notice, notice_id=990002, prior_notice_id=990001),
            locations=tuple(replace(row, notice_id=990002) for row in prior.locations),
            restrictions=tuple(replace(row, notice_id=990002) for row in prior.restrictions),
        )
        self.store.write(current)
        self.reopen()
        self.assertEqual(self.store.chain(990002).snapshots, (prior, current))
        self.assertEqual(self.store.read(990001), prior)

    def test_failed_refresh_retains_entire_previous_envelope(self):
        snapshot = replace(self.snapshot, capture_reference="synthetic://maintenance/committed")
        self.store.write(snapshot)
        self.store.connection.execute("""CREATE TRIGGER synthetic_abort BEFORE UPDATE ON snapshots
            BEGIN SELECT RAISE(ABORT, 'SYNTHETIC extension fault injection'); END""")
        with self.assertRaises(StorageError):
            self.store.write(
                replace(
                    snapshot, restrictions=(), capture_reference="synthetic://maintenance/rejected"
                )
            )
        self.reopen()
        self.assertEqual(self.store.read(990001), snapshot)


if __name__ == "__main__":
    unittest.main()
