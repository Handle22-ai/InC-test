"""Explicit live invocation and process-local request budget; not owner authentication."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from harness.runtime import (
    ROOT,
    OutputDestinationError,
    create_run,
    digest,
    new_run,
    require_pristine,
    write_json,
)

_remaining: int | None = None
_limit: int | None = None
_blocker: str | None = None
_refusal: str | None = None


class LiveRefusal(RuntimeError):
    def __init__(self, classification: str):
        self.classification = classification
        super().__init__(classification)


class RequestBlocked(RuntimeError):
    def __init__(self, classification: str):
        self.classification = classification
        super().__init__(
            "SDK request budget exhausted"
            if classification == "BUDGET_EXHAUSTED"
            else "SDK request blocked"
        )


def request_failure(exc: Exception) -> str:
    if isinstance(exc, RequestBlocked):
        return exc.classification
    status = getattr(exc, "status_code", None)
    if status in {401, 403}:
        return "AUTHENTICATION_FAILURE"
    if status == 404:
        return "MODEL_UNAVAILABLE"
    if type(exc).__name__ in {"APIConnectionError", "APITimeoutError"}:
        return "PROVIDER_UNREACHABLE"
    return "PROVIDER_FAILURE"


def block_requests(classification: str) -> None:
    global _blocker
    if classification in {"AUTHENTICATION_FAILURE", "MODEL_UNAVAILABLE", "PROVIDER_UNREACHABLE"}:
        _blocker = classification


def budget_record() -> dict:
    return {
        "sdk_call_limit": _limit,
        "sdk_calls_used": None if _remaining is None or _limit is None else _limit - _remaining,
        "sdk_calls_remaining": _remaining,
        "blocker": _blocker,
        "boundary": "Current invocation SDK create calls, including readiness; transport retries are not independently counted",
    }


def action_for(classification: str) -> str:
    return {
        "CREDENTIALS_MISSING": "Enable the provider and supply a credential through the operator environment; never paste it into evidence.",
        "AUTHENTICATION_FAILURE": "Check credential validity and model permissions outside the evidence directory; no downstream evaluation was authorized by this readiness failure.",
        "MODEL_UNAVAILABLE": "Check the configured model identifier and account access before an explicitly authorized retry.",
        "BUDGET_EXHAUSTED": "Review the retained attempted/not-attempted calls; any larger budget needs a new explicit invocation.",
        "PROVIDER_UNREACHABLE": "Check provider connectivity before an explicitly authorized retry.",
        "OUTPUT_DESTINATION": "Choose a new writable directory beneath evidence; existing destinations are never reused.",
    }.get(
        classification,
        "Inspect the retained error type and stage evidence; do not treat incomplete execution as acceptance.",
    )


class LiveParser(argparse.ArgumentParser):
    def __init__(self, **kwargs):
        kwargs["allow_abbrev"] = False
        super().__init__(**kwargs)

    def error(self, message):
        failure = record_refusal(
            "COMMAND_VALIDATION", "Live argument validation failed: " + message, "ArgumentError"
        )
        self.exit(
            2,
            json.dumps(
                {
                    "status": "ERROR",
                    "classification": "COMMAND_VALIDATION",
                    "reason": message,
                    "failure_evidence": failure,
                }
            )
            + "\n",
        )


def add_live_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--output", type=Path)
    parser.add_argument(
        "--live",
        action="store_true",
        help="Explicit live invocation; owner authorization is still required",
    )
    parser.add_argument(
        "--max-calls",
        type=int,
        help="Maximum SDK create calls in this process; SDK transport retries are not observed",
    )


def validate_live(args) -> None:
    global _remaining, _limit, _blocker
    if not args.live or args.max_calls is None or args.max_calls < 1:
        raise ValueError("Explicit --live and positive --max-calls required")
    require_pristine()
    from harness.captures import oracle

    # Provider readiness and immutable inherited inputs do not depend on the
    # rebuilt classifier's human spec-read receipt. Evaluation remains separate.
    labels = oracle()
    if any(not (ROOT / row["path"]).is_file() for row in labels.values()):
        raise ValueError("Required source input missing")
    _remaining = args.max_calls
    _limit = args.max_calls
    _blocker = None


def consume_request() -> None:
    global _remaining
    if _blocker:
        raise RequestBlocked(_blocker)
    if _remaining is not None:
        if _remaining <= 0:
            raise RequestBlocked("BUDGET_EXHAUSTED")
        _remaining -= 1


def baseline_path(path: Path | None) -> dict | None:
    if path is None:
        return None
    resolved = path.resolve()
    if not resolved.is_relative_to(ROOT / "evidence") or not resolved.is_file():
        raise ValueError("Comparator must be an existing evidence result file")
    value = json.loads(resolved.read_text())
    if not isinstance(value, dict) or not {"cases", "findings", "manifest"} <= value.keys():
        raise ValueError("Malformed comparator result")
    return value


def refusal_directory() -> Path:
    """Tests inject a temporary sink; normal invocations retain append-only evidence."""
    return create_run(new_run("live-refusals"))


def record_refusal(domain: str, reason: str, error_type: str) -> str | None:
    """Append a minimal safe receipt even when the requested destination is invalid."""
    global _refusal
    if _refusal is not None:
        return _refusal
    try:
        destination = refusal_directory()
        configuration = {
            "provider": "anthropic",
            "requested_model_environment": os.environ.get("LLM_MODEL"),
            "effective_model": getattr(
                sys.modules.get("llm_utils") or sys.modules.get("inherited.llm_utils"),
                "_MODEL",
                "NOT_LOADED_OR_UNVERIFIED",
            ),
            "model_source_sha256": digest(ROOT / "inherited/llm_utils.py"),
            "dependencies_sha256": digest(ROOT / "artifacts/dependencies.lock.txt"),
        }
        record = {
            "error_domain": domain,
            "reason": reason,
            "error_type": error_type,
            "model_config_identity": configuration,
            "calls_consumed": budget_record()["sdk_calls_used"] or 0,
            "budget": budget_record(),
            "gate_status": "ERROR",
            "evaluation_status": "NOT_RUN",
            "action": action_for(domain),
        }
        write_json(destination / "failure.json", record)
        (destination / "report.md").write_text(
            "# Refused live entrypoint\n\n"
            + reason
            + "\n\nGate: ERROR. Evaluation: NOT_RUN.\n\n[Failure and configuration identity](failure.json). No successful evaluation is claimed.\n"
        )
        _refusal = str(destination)
        return _refusal
    except OSError, OutputDestinationError:
        return None


def entry(function) -> int:
    global _remaining, _limit, _blocker, _refusal
    _remaining, _limit, _blocker, _refusal = None, None, None, None
    try:
        status = function()
        if status:
            failure = record_refusal(
                "LIVE_EXECUTION_REFUSED",
                "Live readiness or execution did not complete successfully; inspect the original run and budget",
                "NonzeroExit",
            )
            print(json.dumps({"status": "ERROR", "failure_evidence": failure}), file=sys.stderr)
        return status
    except Exception as exc:
        classification = (
            "OUTPUT_DESTINATION"
            if isinstance(exc, OutputDestinationError)
            else exc.classification
            if isinstance(exc, LiveRefusal)
            else "EXECUTION_OR_VALIDATION_FAILURE"
        )
        reason = (
            str(exc)
            if isinstance(exc, (ValueError, OutputDestinationError, LiveRefusal))
            else "Live entrypoint failed with "
            + type(exc).__name__
            + "; provider message is not copied into the safe refusal receipt"
        )
        failure = record_refusal(classification, reason, type(exc).__name__)
        print(
            json.dumps(
                {
                    "status": "ERROR",
                    "classification": classification,
                    "error_type": type(exc).__name__,
                    "action": action_for(classification),
                    "failure_evidence": failure,
                }
            ),
            file=sys.stderr,
        )
        return 2
