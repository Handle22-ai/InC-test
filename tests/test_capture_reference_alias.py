"""SYNTHETIC serialized-format compatibility, tested only on the rebuilt store."""

from __future__ import annotations

import json
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch

from rebuilt.snapshot import InvalidSnapshot, NoticeSnapshot
from rebuilt.store import ContentConflict, SnapshotStore, StorageError

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "evidence/maintenance/20260926T201903.969882Z/pre_change_synthetic.json"


class CaptureReferenceAliasTests(unittest.TestCase):
    def setUp(self):
        fixture = json.loads(FIXTURE.read_text())
        self.assertTrue(fixture["synthetic"])
        self.snapshot = NoticeSnapshot.from_output(fixture["output"], fixture["source_sha256"])
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.path = Path(self.directory.name) / "synthetic.sqlite"
        self.store = SnapshotStore(self.path)
        self.addCleanup(lambda: self.store.close())
        self.store.write(self.snapshot)

    def install_document(self, metadata, snapshot=None):
        snapshot = snapshot or self.snapshot
        document = {**snapshot.output(), **metadata}
        self.store.connection.execute(
            "UPDATE snapshots SET payload=? WHERE notice_id=?",
            (json.dumps(document), snapshot.notice.notice_id),
        )
        self.store.connection.commit()
        self.store.close()
        self.store = SnapshotStore(self.path)

    def raw_document(self):
        return self.store.connection.execute(
            "SELECT payload FROM snapshots WHERE notice_id=990001"
        ).fetchone()[0]

    def read_existing(self) -> NoticeSnapshot:
        snapshot = self.store.read(990001)
        assert snapshot is not None, "Expected the synthetic persisted notice"
        return snapshot

    def test_alias_only_values_use_native_optional_field_without_fetching(self):
        for value in (None, "", "synthetic://format/capture-001", "SYNTHETIC opaque\n雪"):
            with (
                self.subTest(value=value),
                patch("socket.socket", side_effect=AssertionError("No network")),
            ):
                self.install_document({"captureReference": value})
                expected = replace(self.snapshot, capture_reference=value)
                self.assertEqual(self.store.read(990001), expected)
                self.assertEqual(self.store.all(), (expected,))
                self.assertEqual(self.store.chain(990001).snapshots, (expected,))

    def test_existing_canonical_and_missing_records_remain_compatible(self):
        for metadata, value in [
            ({}, None),
            ({"capture_reference": None}, None),
            ({"capture_reference": "SYNTHETIC canonical"}, "SYNTHETIC canonical"),
        ]:
            with self.subTest(metadata=metadata):
                self.install_document(metadata)
                self.assertEqual(
                    self.store.read(990001), replace(self.snapshot, capture_reference=value)
                )

    def test_both_equal_valid_values_are_accepted(self):
        for value in (None, "", "synthetic://format/equal"):
            with self.subTest(value=value):
                self.install_document({"capture_reference": value, "captureReference": value})
                self.assertEqual(
                    self.store.read(990001), replace(self.snapshot, capture_reference=value)
                )

    def test_different_values_raise_explicit_error_without_selecting_or_writing(self):
        for canonical, alias in [
            ("SYNTHETIC a", "SYNTHETIC b"),
            (None, ""),
            ("", None),
            ("SYNTHETIC valid", 1),
            (False, None),
        ]:
            with self.subTest(canonical=canonical, alias=alias):
                self.install_document({"capture_reference": canonical, "captureReference": alias})
                before = self.raw_document()
                for action in (
                    lambda: self.store.read(990001),
                    lambda: self.store.write(self.snapshot),
                ):
                    with self.assertRaisesRegex(
                        StorageError, "Conflicting capture_reference and captureReference"
                    ):
                        action()
                self.assertEqual(self.raw_document(), before)

    def test_invalid_types_are_rejected_even_if_values_compare_equal(self):
        invalid_values: tuple[object, ...] = (False, 0, 1.0, [], {"SYNTHETIC": "value"})
        for invalid in invalid_values:
            for metadata in (
                {"captureReference": invalid},
                {"capture_reference": invalid, "captureReference": invalid},
            ):
                with self.subTest(metadata=metadata):
                    self.install_document(metadata)
                    with self.assertRaises(StorageError) as raised:
                        self.store.read(990001)
                    self.assertIsInstance(raised.exception.__cause__, InvalidSnapshot)

    def test_replay_receipt_and_canonical_refresh_writes_are_unchanged(self):
        self.install_document({"captureReference": "synthetic://format/original"})
        native = self.read_existing()
        before = self.raw_document()
        replay = self.store.write(native)
        self.assertEqual(replay.disposition, "replayed")
        self.assertEqual(self.raw_document(), before)  # Replay does not migrate stored bytes.
        self.assertEqual(
            (replay.notice_id, replay.source_sha256), (990001, self.snapshot.source_sha256)
        )
        updated = replace(native, capture_reference="synthetic://format/refreshed")
        self.assertEqual(self.store.write(updated).disposition, "refreshed")
        document = json.loads(self.raw_document())
        self.assertNotIn("captureReference", document)
        self.assertEqual(document.pop("capture_reference"), updated.capture_reference)
        self.assertEqual(document, self.snapshot.output())
        self.assertEqual(self.store.all(), (updated,))

    def test_alias_does_not_change_source_conflict_policy(self):
        self.install_document({"captureReference": "synthetic://format/source-conflict"})
        native = self.read_existing()
        before = self.raw_document()
        with self.assertRaises(ContentConflict):
            self.store.write(replace(native, source_sha256="b" * 64))
        self.assertEqual(self.raw_document(), before)
        self.assertEqual(self.store.read(990001), native)

    def test_mixed_spellings_preserve_distinct_prior_chain_and_children(self):
        self.install_document({"captureReference": "synthetic://format/prior"})
        prior = self.store.read(990001)
        current = replace(
            self.snapshot,
            source_sha256="b" * 64,
            notice=replace(self.snapshot.notice, notice_id=990002, prior_notice_id=990001),
            locations=tuple(replace(row, notice_id=990002) for row in self.snapshot.locations),
            restrictions=tuple(
                replace(row, notice_id=990002) for row in self.snapshot.restrictions
            ),
            capture_reference="synthetic://format/current",
        )
        self.store.write(current)
        self.install_document(
            {
                "captureReference": current.capture_reference,
                "capture_reference": current.capture_reference,
            },
            current,
        )
        self.assertEqual(self.store.chain(990002).snapshots, (prior, current))
        self.assertEqual(self.read_existing().output(), self.snapshot.output())

    def test_unrelated_unknown_fields_still_fail(self):
        self.install_document({"captureReference": None, "unexpectedSyntheticField": "ignored?"})
        with self.assertRaises(StorageError):
            self.store.read(990001)


if __name__ == "__main__":
    unittest.main()
