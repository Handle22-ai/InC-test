"""Literal clean successor workflow, retaining gate refusal without a waiver."""

from __future__ import annotations

import argparse
import json
import subprocess
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    destination = args.output.resolve()
    destination.mkdir(parents=True, exist_ok=False)
    revision = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    initial = subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT, text=True)
    commands = [
        ["make", "setup"],
        ["make", "check"],
        ["make", "evaluate-spec"],
        ["make", "context", "TASK=recommendation-classification-maintenance"],
        ["make", "demo"],
        ["make", "evaluate-signals"],
        ["make", "gate"],
    ]
    receipts = []
    for number, command in enumerate(commands):
        folder = destination / f"{number:02}-{command[1]}"
        folder.mkdir()
        start = time.monotonic_ns()
        result = subprocess.run(command, cwd=ROOT, text=True, capture_output=True)
        (folder / "stdout.log").write_text(result.stdout)
        (folder / "stderr.log").write_text(result.stderr)
        receipt = {
            "command": command,
            "cwd": str(ROOT),
            "source_commit": revision,
            "exit_code": result.returncode,
            "elapsed_ns": time.monotonic_ns() - start,
        }
        (folder / "receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
        receipts.append(receipt)
        print(json.dumps(receipt), flush=True)
    summary = {
        "source_commit": revision,
        "initial_status": initial,
        "commands": receipts,
        "measurement_completed": True,
        "all_commands_zero": all(r["exit_code"] == 0 for r in receipts),
        "scope": "Literal offline successor workflow; no separate builder or live model calls",
        "note": "Gate UNKNOWN still returns nonzero. No acceptance waiver.",
    }
    (destination / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    return 0 if summary["all_commands_zero"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
