"""One atomic SQLite document per current notice, with explicit replay receipts."""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from rebuilt.snapshot import InvalidSnapshot, NoticeSnapshot


class StorageError(RuntimeError):
    """Storage did not acknowledge the requested operation."""


class ContentConflict(StorageError):
    """Same ID, different source content: requires an approved version policy."""


@dataclass(frozen=True)
class WriteReceipt:
    notice_id: int
    source_sha256: str
    disposition: Literal["created", "replayed", "refreshed"]
    locations: int
    restrictions: int


@dataclass(frozen=True)
class NoticeChain:
    snapshots: tuple[NoticeSnapshot, ...]
    missing_prior_id: int | None


class SnapshotStore:
    def __init__(self, path: Path) -> None:
        self.connection = sqlite3.connect(path)
        self.connection.execute("""CREATE TABLE IF NOT EXISTS snapshots (
            notice_id INTEGER PRIMARY KEY, source_sha256 TEXT NOT NULL, payload TEXT NOT NULL)""")
        self.connection.commit()

    def close(self) -> None:
        self.connection.close()

    @staticmethod
    def _decode(row: tuple) -> NoticeSnapshot:
        try:
            payload = json.loads(row[2])
            if not isinstance(payload, dict):
                raise InvalidSnapshot("Stored payload must be an object")
            if "captureReference" in payload:
                alias = payload.pop("captureReference")
                if "capture_reference" in payload and payload["capture_reference"] != alias:
                    raise StorageError("Conflicting capture_reference and captureReference values")
                payload["capture_reference"] = alias
            capture_reference = payload.pop("capture_reference", None)
            snapshot = NoticeSnapshot.from_output(
                payload, row[1], capture_reference=capture_reference
            )
            if snapshot.notice.notice_id != row[0]:
                raise InvalidSnapshot("Stored key differs from payload identity")
            return snapshot
        except (ValueError, TypeError) as exc:
            raise StorageError("Stored snapshot is invalid") from exc

    def read(self, notice_id: int) -> NoticeSnapshot | None:
        row = self.connection.execute(
            "SELECT notice_id, source_sha256, payload FROM snapshots WHERE notice_id=?",
            (notice_id,),
        ).fetchone()
        return None if row is None else self._decode(row)

    def all(self) -> tuple[NoticeSnapshot, ...]:
        return tuple(
            self._decode(row)
            for row in self.connection.execute(
                "SELECT notice_id, source_sha256, payload FROM snapshots ORDER BY notice_id"
            )
        )

    def write(self, snapshot: NoticeSnapshot) -> WriteReceipt:
        snapshot.validate()
        document = snapshot.output()
        if snapshot.capture_reference is not None:
            document["capture_reference"] = snapshot.capture_reference
        payload = json.dumps(document, sort_keys=True, allow_nan=False, separators=(",", ":"))
        disposition: Literal["created", "replayed", "refreshed"]
        try:
            with self.connection:
                # Serialize the identity check and write together, including competing connections.
                self.connection.execute("BEGIN IMMEDIATE")
                previous = self.read(snapshot.notice.notice_id)
                if previous is not None and previous.source_sha256 != snapshot.source_sha256:
                    raise ContentConflict(
                        f"Notice {snapshot.notice.notice_id}: changed source content is unsupported"
                    )
                if previous == snapshot:
                    disposition = "replayed"
                else:
                    disposition = "created" if previous is None else "refreshed"
                    self.connection.execute(
                        """INSERT INTO snapshots (notice_id, source_sha256, payload)
                        VALUES (?, ?, ?) ON CONFLICT(notice_id) DO UPDATE SET
                        source_sha256=excluded.source_sha256, payload=excluded.payload""",
                        (snapshot.notice.notice_id, snapshot.source_sha256, payload),
                    )
            # A receipt is emitted only after the transaction context commits successfully.
            return WriteReceipt(
                snapshot.notice.notice_id,
                snapshot.source_sha256,
                disposition,
                len(snapshot.locations),
                len(snapshot.restrictions),
            )
        except sqlite3.Error as exc:
            raise StorageError("Snapshot transaction failed; no write receipt issued") from exc

    def chain(self, notice_id: int) -> NoticeChain:
        found: list[NoticeSnapshot] = []
        seen: set[int] = set()
        current: int | None = notice_id
        while current is not None:
            if current in seen:
                raise StorageError("Cycle in stored prior-notice links")
            seen.add(current)
            snapshot = self.read(current)
            if snapshot is None:
                return NoticeChain(tuple(reversed(found)), current)
            found.append(snapshot)
            current = snapshot.notice.prior_notice_id
        return NoticeChain(tuple(reversed(found)), None)
