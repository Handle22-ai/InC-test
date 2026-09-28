"""Bounded application publication decisions; no network sender or delivery claim.

Consumes the existing parser's proposal plus explicit execution evidence. The
caller observes helpers; it must not repair/deduplicate proposals. This component
owns refusal, history, durable initial-decision keys and the signals-report seam.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal
from uuid import uuid4

from rebuilt.normalization import normalize
from rebuilt.normalized_classifier import classify
from rebuilt.snapshot import InvalidSnapshot, NoticeSnapshot
from rebuilt.store import ContentConflict, SnapshotStore, StorageError


@dataclass(frozen=True)
class Authorization:
    actor: str
    notice_id: int
    source_sha256: str
    reference_time: str
    materiality: Literal["MATERIAL", "NONMATERIAL", "UNRESOLVED"]
    actionable: bool | None
    approved: bool
    source_evidence: str
    rationale: str


@dataclass(frozen=True)
class SemanticEvidence:
    extraction_usable: bool
    helpers: tuple[tuple[str, str | bool | None], ...]
    execution_error: str | None = None
    source_media_type: str = "text/html"

    def refusal(self) -> str | None:
        if self.source_media_type not in {"text/html", "application/vnd.ngpl.normalized+json"}:
            return "UNSUPPORTED_FORMAT"
        if not self.extraction_usable:
            return "EXTRACTION_UNAVAILABLE"
        for name, result in self.helpers:
            if name == "llm_assess_curtailment_impact" and result not in {
                "large",
                "medium",
                "small",
            }:
                return "IMPACT_UNUSABLE"
            if name == "llm_is_supersede_material" and type(result) is not bool:
                return "MATERIALITY_UNUSABLE"
        return self.execution_error


class RecommendationPublisher:
    """Single SQLite transaction reserves each initial publication decision once.

    Report writes are not delivery acknowledgements. A crash after reservation
    can lose a report; it cannot mint a second initial decision. Recovery/delivery
    retries and material updates remain outside this bounded implementation.
    """

    def __init__(self, database: Path) -> None:
        self.store = SnapshotStore(database)
        self.conn = self.store.connection
        self.conn.executescript("""
            CREATE TABLE IF NOT EXISTS normalized_versions (notice_id INTEGER PRIMARY KEY, record TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS initial_decisions (
                event_key TEXT PRIMARY KEY, decision_id TEXT NOT NULL,
                notice_id INTEGER NOT NULL, source_sha256 TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS signal_decisions (
                decision_id TEXT PRIMARY KEY, record TEXT NOT NULL);
        """)
        self.conn.commit()

    def close(self) -> None:
        self.store.close()

    def decide(
        self,
        output: dict,
        source_sha256: str,
        semantic: SemanticEvidence,
        authorization: Authorization | None,
        reference_time: str,
    ) -> dict:
        try:
            return self._decide(output, source_sha256, semantic, authorization, reference_time)
        except (ValueError, KeyError, TypeError) as exc:
            notice = output.get("notice", {}) if isinstance(output, dict) else {}
            result = {
                "decision_id": str(uuid4()),
                "notice_id": notice.get("notice_id") if isinstance(notice, dict) else None,
                "source_sha256": source_sha256,
                "reference_time": reference_time,
                "raw_proposal": output,
                "semantic_evidence": asdict(semantic),
                "classification": "UNRESOLVED",
                "disposition": "ERROR",
                "reason": "INPUT_OR_CONTRACT_REFUSED",
                "reason_codes": ["INPUT_OR_CONTRACT_REFUSED"],
                "error_type": type(exc).__name__,
                "error_reason": str(exc),
                "normalized_input": {},
                "normalization_gaps": [str(exc)],
                "matched_rule": "INPUT-REFUSED",
                "recommendation_allowed": False,
                "publication_disposition": "ERROR",
                "publication_reason": "INPUT_OR_CONTRACT_REFUSED",
                "initial_decision": False,
                "publication_attempted": False,
                "delivery_acknowledged": None,
            }
            with self.conn:
                self._retain(result)
            return result

    def _decide(
        self,
        output: dict,
        source_sha256: str,
        semantic: SemanticEvidence,
        authorization: Authorization | None,
        reference_time: str,
    ) -> dict:
        clock = datetime.fromisoformat(reference_time)
        if clock.tzinfo is None or clock.utcoffset() != timezone.utc.utcoffset(clock):
            raise ValueError("An explicit UTC reference time is required")
        history = [
            json.loads(row[0])
            for row in self.conn.execute(
                "SELECT record FROM normalized_versions WHERE notice_id != ? ORDER BY notice_id",
                (output["notice"]["notice_id"],),
            )
        ]
        normalized, gaps = normalize(
            output,
            source_sha256,
            {**asdict(semantic), "helpers": list(semantic.helpers)},
            reference_time,
            history,
        )
        classified = classify(normalized)
        proposal = classified.proposal
        result = {
            "decision_id": str(uuid4()),
            "notice_id": output["notice"]["notice_id"],
            "source_sha256": source_sha256,
            "reference_time": reference_time,
            "raw_proposal": output,
            "semantic_evidence": asdict(semantic),
            "normalized_input": normalized,
            "normalization_gaps": gaps,
            "actionability": {
                "status": "UNRESOLVED"
                if normalized["facts"]["time_basis"] != "UTC"
                else "REQUIRES_AUTHORIZATION",
                "source_timezone_known": normalized["facts"]["time_basis"] == "UTC",
                "source_timezone_status": "KNOWN"
                if normalized["facts"]["time_basis"] == "UTC"
                else "UNKNOWN",
                "automatic_current_future": False,
                "recommendation_authorized": False,
            },
            "classifier_decision": proposal,
            "matched_rule": classified.matched_rule,
            "classification": proposal["classification"],
            "disposition": proposal["disposition"],
            "reason": classified.reason,
            "reason_codes": proposal["reason_codes"],
            "recommendation_allowed": proposal["recommendation_allowed"],
            "candidate_classification": None
            if proposal["classification"] == "UNRESOLVED"
            else proposal["classification"] == "SIGNAL_CANDIDATE",
            "authorization": asdict(authorization) if authorization else None,
            "publication_disposition": proposal["disposition"],
            "publication_reason": classified.reason,
            "initial_decision": False,
            "publication_attempted": False,
            "delivery_acknowledged": None,
        }
        if proposal["classification"] != "UNRESOLVED" and semantic.refusal() is not None:
            # A decision the rules could make without the failed helper still stands, but
            # its output must not replace the last valid snapshot or be published (D5-002).
            result.update(
                publication_disposition="REVIEW_REQUIRED", publication_reason="SEMANTICS_INCOMPLETE"
            )
        elif proposal["classification"] != "UNRESOLVED":
            try:
                snapshot = NoticeSnapshot.from_output(output, source_sha256)
                self.store.write(snapshot)
                with self.conn:
                    self.conn.execute("BEGIN IMMEDIATE")
                    self.conn.execute(
                        "INSERT OR REPLACE INTO normalized_versions VALUES (?, ?)",
                        (
                            snapshot.notice.notice_id,
                            json.dumps(
                                {
                                    "notice": normalized["notice"],
                                    "facts": normalized["facts"],
                                    "source_sha256": source_sha256,
                                },
                                sort_keys=True,
                            ),
                        ),
                    )
                    self._resolve(snapshot, authorization, result)
                    self._retain(result)
                return result
            except (InvalidSnapshot, ContentConflict, StorageError) as exc:
                result.update(
                    publication_disposition="REVIEW_REQUIRED", publication_reason=type(exc).__name__
                )
        with self.conn:
            self._retain(result)
        return result

    def _retain(self, result: dict) -> None:
        self.conn.execute(
            "INSERT INTO signal_decisions VALUES (?, ?)",
            (result["decision_id"], json.dumps(result, sort_keys=True)),
        )

    def _resolve(self, snapshot: NoticeSnapshot, auth: Authorization | None, result: dict) -> None:
        chain = self.store.chain(snapshot.notice.notice_id)
        event_key = f"{snapshot.notice.pipeline_code}:{chain.snapshots[0].notice.notice_id}"
        result["event_key"] = event_key
        # A branch has disputed successor ordering; never guess which branch wins.
        ids = {s.notice.notice_id for s in chain.snapshots}
        if any(
            s.notice.prior_notice_id in ids and s.notice.notice_id not in ids
            for s in self.store.all()
        ):
            result.update(
                publication_disposition="REVIEW_REQUIRED",
                publication_reason="CONFLICTING_SUCCESSOR",
            )
            return
        prior_decision = self.conn.execute(
            "SELECT decision_id FROM initial_decisions WHERE event_key=?", (event_key,)
        ).fetchone()
        if (
            result["classification"] != "SIGNAL_CANDIDATE"
            or result["disposition"] != "CANDIDATE_ONLY"
        ):
            return
        if result["normalized_input"]["facts"]["time_basis"] != "UTC":
            result.update(
                publication_disposition="REVIEW_REQUIRED",
                publication_reason="UNRESOLVED_SOURCE_TIME",
            )
            return
        if (
            auth is None
            or not auth.actor.strip()
            or not auth.source_evidence.strip()
            or not auth.rationale.strip()
            or not auth.approved
            or auth.notice_id != snapshot.notice.notice_id
            or auth.source_sha256 != snapshot.source_sha256
            or auth.reference_time != result["reference_time"]
            or auth.materiality != "MATERIAL"
            or auth.actionable is not True
        ):
            result.update(
                publication_disposition="REVIEW_REQUIRED",
                publication_reason="AUTHORIZATION_REQUIRED",
            )
            return
        result["actionability"].update(status="AUTHORIZED", recommendation_authorized=True)
        if prior_decision:
            result.update(
                publication_disposition="SUPPRESSED",
                publication_reason="INITIAL_ALREADY_RECORDED",
                initial_decision_reference=prior_decision[0],
            )
            if len(chain.snapshots) > 1:
                result.update(
                    publication_disposition="REVIEW_REQUIRED",
                    publication_reason="MATERIAL_UPDATE_NOT_IMPLEMENTED",
                )
            return
        self.conn.execute(
            "INSERT INTO initial_decisions VALUES (?, ?, ?, ?)",
            (event_key, result["decision_id"], snapshot.notice.notice_id, snapshot.source_sha256),
        )
        result.update(
            publication_disposition="INITIAL_RECOMMENDATION",
            publication_reason="AUTHORIZED_INITIAL",
            initial_decision=True,
        )

    def save_signals_report(self, decisions: list[dict], destination: Path) -> list[dict]:
        """Actual candidate outbound report; recorder does no filtering/deduplication."""
        selected = [d for d in decisions if d["initial_decision"]]
        destination.write_text(json.dumps(selected, indent=2) + "\n")
        return selected
