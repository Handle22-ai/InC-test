"""Typed NGPL snapshot boundary; decisions are opaque to persistence."""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass, fields
from typing import Any, get_args, get_type_hints


class InvalidSnapshot(ValueError):
    """Malformed normalized input; nothing has been acknowledged or written."""


@dataclass(frozen=True)
class Notice:
    notice_id: int
    tsp_name: str
    pipeline_code: str
    is_critical: int
    notice_type: str
    notice_subtype: str | None
    effective_datetime: str | None
    end_datetime: str | None
    post_datetime: str | None
    response_required: int
    response_due_date: str | None
    status: str
    prior_notice_id: int | None
    subject: str
    body_text: str
    outage_report_ref: str | None
    tariff_section: str | None
    information_only: int
    is_signal: int
    confidence_score: float | int
    validity_flags: str
    source_url: str | None
    scraped_at: str
    html_file: str


@dataclass(frozen=True)
class Location:
    location_index: int
    notice_id: int
    loc_code: str | None
    loc_name: str | None
    segment: str | None
    compressor_station: str | None
    zone: str | None
    system: str | None


@dataclass(frozen=True)
class Restriction:
    notice_id: int
    location_index: int
    service_type: str
    restriction_type: str
    restriction_value: float | int | None
    restriction_unit: str | None
    flow_direction: str | None
    start_datetime: str | None
    end_datetime: str | None


def validate_scalars(record: Notice | Location | Restriction) -> None:
    hints = get_type_hints(type(record))
    for field in fields(record):
        allowed = get_args(hints[field.name]) or (hints[field.name],)
        if type(getattr(record, field.name)) not in allowed:
            raise InvalidSnapshot(f"{type(record).__name__}.{field.name}: wrong scalar type")


@dataclass(frozen=True)
class NoticeSnapshot:
    source_sha256: str
    notice: Notice
    locations: tuple[Location, ...]
    restrictions: tuple[Restriction, ...]
    capture_reference: str | None = None

    def validate(self) -> None:
        if type(self.capture_reference) not in (str, type(None)):
            raise InvalidSnapshot("capture_reference must be a string or None")
        if not isinstance(self.source_sha256, str) or not re.fullmatch(
            "[0-9a-f]{64}", self.source_sha256
        ):
            raise InvalidSnapshot("A source-content SHA256 is required")
        records: tuple[Notice | Location | Restriction, ...] = (
            self.notice,
            *self.locations,
            *self.restrictions,
        )
        for record in records:
            validate_scalars(record)
        if self.notice.pipeline_code != "NGPL":
            raise InvalidSnapshot("Only the bounded NGPL identity namespace is supported")
        indexes = [row.location_index for row in self.locations]
        if len(set(indexes)) != len(indexes):
            raise InvalidSnapshot("Location indexes must be unique per notice")
        children: tuple[Location | Restriction, ...] = (*self.locations, *self.restrictions)
        if any(row.notice_id != self.notice.notice_id for row in children):
            raise InvalidSnapshot("Child records must belong to this notice")
        if any(row.location_index not in indexes for row in self.restrictions):
            raise InvalidSnapshot("Restriction references an absent location")

    @classmethod
    def from_output(
        cls, output: dict[str, Any], source_sha256: str, *, capture_reference: str | None = None
    ) -> NoticeSnapshot:
        try:
            if set(output) != {"notice", "locations", "restrictions"}:
                raise InvalidSnapshot("Expected notice, locations, restrictions")
            snapshot = cls(
                source_sha256,
                Notice(**output["notice"]),
                tuple(Location(**row) for row in output["locations"]),
                tuple(Restriction(**row) for row in output["restrictions"]),
                capture_reference,
            )
            snapshot.validate()
            return snapshot
        except (KeyError, TypeError) as exc:
            raise InvalidSnapshot("Incomplete or unexpected snapshot fields") from exc

    def output(self) -> dict[str, Any]:
        """Shared normalized payload; rebuilt-only envelope metadata is not projected."""
        return {
            "notice": asdict(self.notice),
            "locations": [asdict(row) for row in self.locations],
            "restrictions": [asdict(row) for row in self.restrictions],
        }
