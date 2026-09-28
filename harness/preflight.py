"""Current-invocation representative execution; historical PASS is never readiness."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from harness.live import (
    LiveParser,
    action_for,
    add_live_arguments,
    budget_record,
    entry,
    record_refusal,
    validate_live,
)
from harness.runtime import ROOT, create_run, integrity, new_run, provenance, write_json


def run_preflight(run: Path) -> dict:
    """Caller owns the directory and the invocation budget; no historical lookup."""
    from harness.adapter import InheritedAdapter, NoticeInput, database, llm_utils, state_snapshot

    record = {
        "run_id": run.name,
        "status": "ERROR",
        "classification": "UNKNOWN",
        "provenance": provenance(),
        "credential_detected": bool(llm_utils._API_KEY),
        "llm_enabled": llm_utils._ENABLED,
        "configured_model": llm_utils._MODEL,
        "provider": "anthropic",
        "readiness_scope": "Current invocation only; representative parse, model response and real SQLite readback, not application acceptance",
        "semantic_evaluations_completed": False,
        "output_shape_valid": "N/A",
        "output_shape_scope": "N/A until a usable semantic result exists; fallback fields do not establish validity",
        "dataset_count": len(list((ROOT / "inherited/evaluation/notices").glob("*.html"))),
    }
    try:
        if integrity()["changed"] or not integrity()["env_ignored"]:
            record["classification"] = "ENVIRONMENT_FAILURE"
        elif not llm_utils.is_llm_available():
            record["classification"] = "CREDENTIALS_MISSING"
        else:
            conn = database.init_db(str(run / "state.db"))
            try:
                result = InheritedAdapter().process(
                    NoticeInput(
                        "preflight-46624",
                        ROOT / "inherited/evaluation/notices/46624_CAPACITY CONSTRAINT.html",
                        46624,
                    ),
                    conn,
                    run / "case.json",
                )
                database.enable_fk(conn)
                chain = database.get_notice_chain(conn, 46624)
                before_close = state_snapshot(conn)
            finally:
                conn.close()
            reopened = sqlite3.connect(run / "state.db")
            try:
                restored = state_snapshot(reopened)
            finally:
                reopened.close()
            output = result.get("output", {})
            row = output.get("notice", {})
            # Every helper the inherited system asked for must have answered; a call the
            # budget blocked leaves a fallback that must not read as a real signal.
            helpers_complete = all(
                h.get("result") is not None for h in result.get("helper_results", [])
            ) and not any(c.get("classification") == "NOT_ATTEMPTED" for c in result["model_calls"])
            scorable = bool(result.get("stages", {}).get("classification", {}).get("scorable"))
            record.update(
                real_model_request_verified=bool(result["model_calls"])
                and all(
                    c["success"] and c.get("request_id") and c.get("response", {}).get("id")
                    for c in result["model_calls"]
                ),
                representative_notice_processed=result["outcome"] == "SUCCESS",
                output_shape_valid=(
                    isinstance(row.get("notice_id"), int)
                    and row.get("is_signal") in (0, 1)
                    and isinstance(row.get("confidence_score"), (float, int))
                    and 0 <= row.get("confidence_score", -1) <= 1
                    and isinstance(output.get("locations"), list)
                    and isinstance(output.get("restrictions"), list)
                )
                if result.get("stages", {}).get("classification", {}).get("scorable")
                else "N/A",
                history_lookup_verified=bool(chain) and chain[-1]["notice_id"] == 46624,
                persistence_verified=before_close == restored and len(restored["notices"]) == 1,
                helpers_complete=helpers_complete,
                observed_signal=bool(row.get("is_signal"))
                if scorable and helpers_complete
                else None,
                stages=result["stages"],
                state=restored,
            )
            if result["outcome"] != "SUCCESS":
                record["classification"] = result["outcome"]
            elif not helpers_complete:
                record["classification"] = "BUDGET_EXHAUSTED"
            elif all(
                record[k] is True
                for k in [
                    "real_model_request_verified",
                    "representative_notice_processed",
                    "output_shape_valid",
                    "history_lookup_verified",
                    "persistence_verified",
                    "helpers_complete",
                ]
            ):
                record.update(status="PASS", classification=None)
    except (OSError, sqlite3.Error) as exc:
        record.update(classification="ENVIRONMENT_FAILURE", error_type=type(exc).__name__)
    record["budget"] = budget_record()
    if record["classification"]:
        record["action"] = action_for(str(record["classification"]))
    write_json(run / "result.json", record)
    return record


def main() -> int:
    parser = LiveParser()
    add_live_arguments(parser)
    args = parser.parse_args()
    validate_live(args)
    run = create_run(args.output or new_run("preflight"))
    record = run_preflight(run)
    if record["status"] != "PASS":
        record["failure_evidence"] = record_refusal(
            str(record["classification"]),
            "Current readiness refused: "
            + str(record["classification"])
            + "; details: "
            + str(run.relative_to(ROOT) / "result.json"),
            "ReadinessFailure",
        )
    print(
        json.dumps({k: v for k, v in record.items() if k not in {"provenance", "state"}}, indent=2)
    )
    return 0 if record["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(entry(main))
