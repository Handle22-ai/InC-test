"""Bounded real-provider CLI smoke runs, with saved or freshly fetched HTML."""

from __future__ import annotations

import argparse
import importlib.util
import json
import shutil
import sqlite3
import sys
from contextlib import ExitStack
from pathlib import Path
from unittest.mock import patch

from harness.gates import check_case
from harness.live import LiveParser, add_live_arguments, validate_live
from harness.live import entry as live_entry
from harness.requirements import load_requirements
from harness.runtime import (
    ROOT,
    create_run,
    digest,
    integrity,
    new_run,
    provenance,
    validate_output,
    write_json,
)


def completion_checks(
    metadata: list[dict],
    results: list[dict],
    calls: list[dict],
    helpers: list[dict],
    state: dict,
    report: object,
    cli_exit: int,
) -> dict[str, bool]:
    """A zero CLI exit, empty output or regex fallback cannot certify live execution."""
    ids = [int(entry["notice_id"]) for entry in metadata]
    observed_ids = [entry["notice"]["notice_id"] for entry in results]
    flags = [json.loads(entry["notice"]["validity_flags"]) for entry in results]
    return {
        "cli_exit_zero": cli_exit == 0,
        "one_notice_fetched_or_staged": len(ids) == 1,
        "every_input_processed": bool(ids) and observed_ids == ids,
        "real_api_responses": bool(calls)
        and all(
            call["success"] and call.get("request_id") and call.get("response", {}).get("id")
            for call in calls
        ),
        "no_extraction_or_helper_fallback": bool(flags)
        and all("llm_extraction" in value for value in flags)
        and all(helper["result"] is not None for helper in helpers),
        "persisted_notice_ids": bool(ids)
        and sorted(row["notice_id"] for row in state.get("notices", [])) == sorted(ids),
        "foreign_keys_valid": not state.get("foreign_key_violations", ["no state"]),
        "signal_report_matches_processed_results": report
        == [entry for entry in results if entry["notice"]["is_signal"]],
    }


def run(
    source: str, output: str | None = None, *, live: bool = False, max_calls: int | None = None
) -> tuple[Path, dict]:
    if source not in {"saved", "live"}:
        raise ValueError("Unknown source")
    destination = validate_output(ROOT / output) if output else new_run(f"e2e-{source}")
    validate_live(argparse.Namespace(live=live, max_calls=max_calls))
    # Import only in the explicitly live entry point; offline infrastructure tests
    # never load credentials or initialize the application/provider.
    from harness.adapter import (
        ModelObserver,
        llm_utils,
        notice_parser,
        notice_validator,
        state_snapshot,
    )
    from harness.evaluator import require_preflight
    from harness.storage_ports import readback

    destination = create_run(destination)
    readiness = require_preflight(destination)
    notices = destination / "notices"
    notices.mkdir(parents=True)
    argv = [
        "inherited/main.py",
        "parse" if source == "saved" else "fetch-and-parse",
        "--output-dir",
        str(notices),
        "--db",
        "state.sqlite",
        "--signal-output",
        "signals.json",
        "--max-notices",
        "1",
    ]
    record = {
        "source": source,
        "readiness": readiness,
        "cli_argv": argv,
        "provenance": provenance(),
        "credential_present": llm_utils.is_llm_available(),
        "model": llm_utils._MODEL,
        "model_configuration": "unchanged inherited client and request parameters",
        "scope": "One complete CLI notice flow; inherited store; JSON report, no external alert delivery",
        "authorization": "Explicit live invocation budget includes current readiness and one CLI notice; SDK transport retries are not counted separately",
    }
    write_json(destination / "manifest.json", record)
    if not record["credential_present"]:
        summary: dict = {"status": "BLOCKED", "reason": "Enabled Anthropic credential required"}
        write_json(destination / "summary.json", summary)
        return destination, summary
    if integrity()["changed"]:
        raise ValueError("Inherited integrity check failed")

    annotation = {}
    if source == "saved":
        dataset = json.loads((ROOT / "requirements/dataset.json").read_text())
        annotation = next(row for row in dataset["cases"] if row["notice_id"] == 46624)
        original = ROOT / annotation["path"]
        target = notices / original.name
        shutil.copy2(original, target)
        write_json(notices / "metadata.json", [{"notice_id": 46624, "html_file": str(target)}])

    observer = ModelObserver()
    results: list[dict] = []
    helpers: list[dict] = []
    events: list[dict] = []
    original_process = notice_parser.NoticeProcessor.process_all_notices

    def observe_process(processor, *args, **kwargs):
        values = original_process(processor, *args, **kwargs)
        results.extend(values)
        return values

    def observe_helper(name, function):
        def invoke(*args, **kwargs):
            value = function(*args, **kwargs)
            helpers.append({"helper": name, "result": value})
            return value

        return invoke

    def bounded_client():
        if len(observer.calls) >= 6:
            raise RuntimeError("E2E model call budget exceeded")
        return observer.client()

    spec = importlib.util.spec_from_file_location("inherited_e2e_cli", ROOT / "inherited/main.py")
    if spec is None or spec.loader is None:
        raise RuntimeError("Cannot load the existing CLI")
    cli = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(cli)
    cli_exit = 1
    try:
        with ExitStack() as stack:
            stack.enter_context(patch.object(sys, "argv", argv))
            stack.enter_context(patch.object(llm_utils, "get_client", bounded_client))
            stack.enter_context(
                patch.object(notice_parser.NoticeProcessor, "process_all_notices", observe_process)
            )
            for name in ("llm_assess_curtailment_impact", "llm_is_supersede_material"):
                stack.enter_context(
                    patch.object(
                        notice_validator,
                        name,
                        observe_helper(name, getattr(notice_validator, name)),
                    )
                )
            # Record operational failures by type only; exception text can contain secrets.
            original_fetch = cli.NoticeScraper.fetch_notices

            def observe_fetch(scraper, *args, **kwargs):
                try:
                    value = original_fetch(scraper, *args, **kwargs)
                    events.append({"stage": "fetch", "notices": len(scraper.metadata)})
                    return value
                except Exception as exc:
                    events.append({"stage": "fetch", "error_type": type(exc).__name__})
                    raise

            stack.enter_context(patch.object(cli.NoticeScraper, "fetch_notices", observe_fetch))
            cli_exit = cli.main()
    except Exception as exc:
        events.append({"stage": "cli", "error_type": type(exc).__name__})
    finally:
        write_json(destination / "model-calls.json", observer.calls)
        write_json(destination / "helper-results.json", helpers)
        write_json(destination / "processed.json", results)
        write_json(destination / "events.json", events)

    metadata_path = notices / "metadata.json"
    metadata = json.loads(metadata_path.read_text()) if metadata_path.exists() else []
    report_path = notices / "signals.json"
    report = json.loads(report_path.read_text()) if report_path.exists() else None
    state = {}
    database_path = notices / "state.sqlite"
    if database_path.exists():
        with sqlite3.connect(f"file:{database_path}?mode=ro", uri=True) as connection:
            state = state_snapshot(connection)
    write_json(destination / "reopened-state.json", state)
    checks = completion_checks(metadata, results, observer.calls, helpers, state, report, cli_exit)
    checks["persisted_payload_matches"] = bool(results) and all(
        readback(state, item["notice"]["notice_id"]) == item for item in results
    )
    checks["inherited_unchanged"] = not integrity()["changed"]
    findings = []
    safe_checks = {"identity", "decision_shape", "quantities", "links", "model_proof"}
    if source == "saved":
        safe_checks |= {"classification", "field_values"}
    for entry, metadata_entry in zip(results, metadata, strict=False):
        case = {
            "case_id": str(metadata_entry["notice_id"]),
            "notice_id": int(metadata_entry["notice_id"]),
            "input_sha256": digest(Path(metadata_entry["html_file"])),
            "output": entry,
            "outcome": "SUCCESS"
            if all(checks.values())
            else next(
                (c["root_cause"] for c in observer.calls if c.get("root_cause")), "MODEL_FAILURE"
            ),
            "model_calls": observer.calls,
            "helper_results": helpers,
            "annotations": annotation,
            "category": "labeled" if source == "saved" else "unlabeled",
            "evidence_ref": "processed.json",
        }
        for requirement in load_requirements():
            if requirement["validation"]["check"] in safe_checks:
                result = check_case(requirement, case)
                if result is not None:
                    findings.append(result)
    write_json(destination / "findings.json", findings)
    record["inputs"] = [
        {
            "path": str(Path(row["html_file"]).relative_to(ROOT)),
            "sha256": digest(Path(row["html_file"])),
            "notice_id": row["notice_id"],
        }
        for row in metadata
    ]
    write_json(destination / "manifest.json", record)
    summary = {
        "status": "PASS" if all(checks.values()) else "FAIL",
        "checks": checks,
        "cli_exit_code": cli_exit,
        "notices_processed": len(results),
        "model_calls": len(observer.calls),
        "signals_written": len(report) if isinstance(report, list) else None,
        "finding_counts": {
            status: sum(f["status"] == status for f in findings)
            for status in ("PASS", "FAIL", "ERROR", "UNKNOWN")
        },
        "application_acceptance": "NOT ESTABLISHED; one-notice execution smoke, not full behavioral acceptance",
        "rebuilt_store_in_cli": False,
        "external_alert_delivery": "No interface; not exercised",
    }
    write_json(destination / "summary.json", summary)
    return destination, summary


def main() -> int:
    parser = LiveParser(description=__doc__)
    add_live_arguments(parser)
    parser.add_argument("source", choices=("saved", "live"))
    args = parser.parse_args()
    destination, summary = run(args.source, args.output, live=args.live, max_calls=args.max_calls)
    checks = summary.get("checks", {})
    (destination / "report.md").write_text(
        f"# Live CLI E2E: {args.source}\n\n"
        f"Execution status: **{summary['status']}**.\n\n"
        "This is one notice through the unchanged inherited CLI, real Anthropic calls, "
        "SQLite and the local signal JSON report. It does not establish full application "
        "acceptance, live alert delivery, or production integration of the rebuilt store.\n\n"
        + "\n".join(f"- {name}: {'PASS' if passed else 'FAIL'}" for name, passed in checks.items())
        + "\n\n[Summary](summary.json), [provenance](manifest.json), "
        "[model calls](model-calls.json), [processed results](processed.json), "
        "[reopened state](reopened-state.json), [requirement findings](findings.json).\n"
    )
    print(json.dumps({"run": str(destination.relative_to(ROOT)), **summary}, indent=2))
    return 0 if summary["status"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(live_entry(main))
