"""Direct component probe for existing D4-005/D5-001, without a repair wrapper."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from harness.runtime import write_json
from rebuilt.signals import RecommendationPublisher, SemanticEvidence


def run(destination: Path) -> dict:
    body = "Synthetic source with an unsupported status; no new status policy is inferred."
    value = {
        "notice": {
            "notice_id": 88001,
            "status": "WITHDRAWN",
            "notice_type": "SYNTHETIC",
            "body_text": body,
            "prior_notice_id": None,
        },
        "restrictions": [],
        "locations": [],
    }
    database = destination / "refusal.sqlite"
    publisher = RecommendationPublisher(database)
    try:
        decision = publisher.decide(
            value,
            hashlib.sha256(body.encode()).hexdigest(),
            SemanticEvidence(True, ()),
            None,
            "2026-01-15T12:00:00+00:00",
        )
    finally:
        publisher.close()
    publisher = RecommendationPublisher(database)
    try:
        retained = [
            json.loads(r[0]) for r in publisher.conn.execute("SELECT record FROM signal_decisions")
        ]
        snapshots = publisher.conn.execute("SELECT count(*) FROM normalized_versions").fetchone()[0]
    finally:
        publisher.close()
    passed = (
        decision["classification"] == "UNRESOLVED"
        and decision["disposition"] == "ERROR"
        and not decision["initial_decision"]
        and retained == [json.loads(json.dumps(decision))]
        and retained[0]["raw_proposal"] == value
        and snapshots == 0
    )
    result = {
        "status": "PASS" if passed else "FAIL",
        "input": value,
        "decision": decision,
        "retained_after_reopen": retained,
        "accepted_snapshot_count": snapshots,
        "scope": "Direct malformed-status refusal retained across reopen; not WITHDRAWN business semantics or complete lifecycle retention",
    }
    write_json(destination / "direct-refusal.json", result)
    return result
