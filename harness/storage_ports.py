"""Observation ports only: no deduplication, repair, filtering or policy decisions."""

from __future__ import annotations

from dataclasses import asdict, dataclass, fields
from pathlib import Path
from typing import Protocol

from rebuilt.snapshot import Location, Notice, NoticeSnapshot, Restriction
from rebuilt.store import SnapshotStore, StorageError


class SnapshotPayload(Protocol):
    @property
    def source_sha256(self) -> str: ...
    def output(self) -> dict: ...


@dataclass
class CapturedPayload:
    payload: dict
    source_sha256: str

    def output(self) -> dict:
        return self.payload


class StoragePort(Protocol):
    def write(self, snapshot: SnapshotPayload) -> dict: ...
    def read(self, notice_id: int) -> dict | None: ...
    def state(self) -> dict: ...
    def chain(self, notice_id: int) -> list[dict]: ...
    def close(self) -> None: ...


def readback(state: dict, notice_id: int) -> dict | None:
    """Project documented payload columns; retain ALL rows, including duplicates.

    Inherited database-generated surrogate IDs have no normalized-input counterparts.
    Full raw state including those IDs remains in each case's evidence.
    """
    notices = [row for row in state["notices"] if row["notice_id"] == notice_id]
    if not notices:
        return None
    if len(notices) != 1:
        raise StorageError("Readback contains multiple parent identities")
    result = {}
    for key, table, model in [
        ("notice", "notices", Notice),
        ("locations", "notice_locations", Location),
        ("restrictions", "notice_restrictions", Restriction),
    ]:
        rows = [
            {field.name: row[field.name] for field in fields(model)}
            for row in state[table]
            if row["notice_id"] == notice_id
        ]
        result[key] = rows[0] if key == "notice" else rows
    return result


class InheritedStorage:
    def __init__(self, path: Path) -> None:
        # Lazy import permits the integration runner to choose its fixed model variant first.
        from harness.adapter import database, state_snapshot

        self.database = database
        self.snapshot_state = state_snapshot
        self.connection = database.init_db(str(path))

    def close(self) -> None:
        self.connection.close()

    def write(self, snapshot: SnapshotPayload) -> dict:
        output = snapshot.output()
        acknowledged = self.database.insert_notice(
            self.connection,
            **{
                "notice": output["notice"],
                "locations": output["locations"],
                "restrictions": output["restrictions"],
            },
        )
        if not acknowledged:
            raise StorageError("Inherited insert returned false")
        # Match the preserved application protocol: FK enforcement follows insertion.
        self.database.enable_fk(self.connection)
        return {"acknowledged": True, "native_receipt": None}

    def state(self) -> dict:
        return self.snapshot_state(self.connection)

    def read(self, notice_id: int) -> dict | None:
        return readback(self.state(), notice_id)

    def chain(self, notice_id: int) -> list[dict]:
        return self.database.get_notice_chain(self.connection, notice_id)


class RebuiltStorage:
    def __init__(self, path: Path) -> None:
        self.store = SnapshotStore(path)

    def close(self) -> None:
        self.store.close()

    def write(self, snapshot: SnapshotPayload) -> dict:
        value = (
            snapshot
            if isinstance(snapshot, NoticeSnapshot)
            else NoticeSnapshot.from_output(snapshot.output(), snapshot.source_sha256)
        )
        return {"acknowledged": True, "native_receipt": asdict(self.store.write(value))}

    def read(self, notice_id: int) -> dict | None:
        snapshot = self.store.read(notice_id)
        return None if snapshot is None else snapshot.output()

    def state(self) -> dict:
        state: dict[str, list] = {
            "notices": [],
            "notice_locations": [],
            "notice_restrictions": [],
            "foreign_key_violations": [],
        }
        for snapshot in self.store.all():
            output = snapshot.output()
            state["notices"].append(output["notice"])
            state["notice_locations"].extend(output["locations"])
            state["notice_restrictions"].extend(output["restrictions"])
        # This document schema has no SQL child foreign keys. Semantic links are checked
        # on write AND independently against actual readback by the existing gate.
        return state

    def chain(self, notice_id: int) -> list[dict]:
        return [snapshot.output()["notice"] for snapshot in self.store.chain(notice_id).snapshots]
