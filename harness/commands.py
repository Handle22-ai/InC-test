"""Make transfers raw values through environment variables, never shell interpolation."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

from harness.runtime import ROOT, OutputDestinationError, validate_output


def main() -> int:
    if len(sys.argv) != 2:
        raise ValueError("Exactly one command argument required")
    command = sys.argv[1]
    values = {
        k: os.environ.get("HARNESS_" + k, "")
        for k in ("TASK", "OUTPUT", "RUN", "BASELINE", "LIVE", "MAX_CALLS", "SPEC", "BASE")
    }
    # Newlines/NUL and shell/make control syntax are not valid task/path names here.
    for key, value in values.items():
        if any(c in value for c in ("\n", "\r", "\x00", "$", "`", ";", "|", "&", "<", ">")):
            raise ValueError("Invalid command value: " + key)
    if values["OUTPUT"]:
        validate_output(Path(values["OUTPUT"]))
    for key in ("BASELINE", "RUN"):
        if values[key] and not (ROOT / values[key]).exists():
            raise ValueError("Missing " + key)
    offline = {"gate": "normalized", "consequences": "consequences", "context": "context"}
    # Live runs of the inherited system; each needs LIVE=1 and a call budget.
    live = {"preflight": "preflight", "evaluate-inherited": "evaluator", "e2e-live": "e2e"}
    if command in offline:
        args = [sys.executable, "-B", "-m", "harness.offline", offline[command]]
        if command == "consequences":
            if values["SPEC"]:
                args += ["--spec", values["SPEC"]]
            if values["BASE"]:
                args += ["--base", values["BASE"]]
        if command == "context":
            args += ["--task", values["TASK"]]
        if values["OUTPUT"]:
            args += ["--output", values["OUTPUT"]]
        if values["RUN"]:
            args += ["--run", values["RUN"]]
        if values["BASELINE"]:
            args += ["--baseline", values["BASELINE"]]
    else:
        if command not in live:
            raise ValueError("Unknown command")
        if (
            values["LIVE"] != "1"
            or not values["MAX_CALLS"].isdigit()
            or int(values["MAX_CALLS"]) < 1
        ):
            raise ValueError(
                "LIVE=1 and a positive MAX_CALLS required; historical approval is not current authorization"
            )
        args = [
            sys.executable,
            "-B",
            "-m",
            "harness." + live[command],
            "--live",
            "--max-calls",
            values["MAX_CALLS"],
        ]
        if command.startswith("e2e-"):
            args += [command.removeprefix("e2e-")]
        if values["OUTPUT"]:
            args += ["--output", values["OUTPUT"]]
        if values["BASELINE"]:
            args += ["--compare-to", values["BASELINE"]]
    return subprocess.run(args, cwd=ROOT).returncode


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        failure = None
        if len(sys.argv) > 1 and sys.argv[1] in {
            "preflight",
            "evaluate-inherited",
            "e2e-live",
        }:
            from harness.live import record_refusal

            failure = record_refusal(
                "COMMAND_VALIDATION", "Live entrypoint refused before execution", type(exc).__name__
            )
        print(
            json.dumps(
                {
                    "status": "ERROR",
                    "classification": "OUTPUT_DESTINATION"
                    if isinstance(exc, OutputDestinationError)
                    else "COMMAND_VALIDATION",
                    "reason": str(exc),
                    "failure_evidence": failure,
                }
            ),
            file=sys.stderr,
        )
        raise SystemExit(2)
