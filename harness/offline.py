"""Process-local isolation for documented offline commands; no SUT policy changes."""

from __future__ import annotations

import argparse
import os
import runpy
import sys
from contextlib import nullcontext
from unittest.mock import patch

from harness.credential_guard import reject_external_access


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "action",
        choices=("test", "context", "normalized", "consequences"),
    )
    # Only parse our action. Help and all other flags belong to the selected command.
    arguments = parser.parse_args(sys.argv[1:2])
    remaining = sys.argv[2:]
    modules = {
        "test": "unittest",
        "context": "harness.context",
        "normalized": "harness.normalized_evaluation",
        "consequences": "harness.proposals",
    }
    module = modules[arguments.action]
    sys.dont_write_bytecode = True
    sys.addaudithook(reject_external_access)
    # python-dotenv 1.0.0 does not honor PYTHON_DOTENV_DISABLED. Disable its
    # loader before the unchanged inherited modules are imported. A process
    # boundary keeps this restriction separate from authorized live commands.
    with (
        patch.dict(os.environ, {"ANTHROPIC_API_KEY": "", "LLM_ENABLED": "false"}),
        patch("dotenv.load_dotenv", return_value=False),
        patch("dotenv.main.load_dotenv", return_value=False),
        patch(
            "dotenv.dotenv_values", side_effect=RuntimeError("Offline credential loading disabled")
        ),
        patch(
            "dotenv.main.dotenv_values",
            side_effect=RuntimeError("Offline credential loading disabled"),
        ),
        patch(
            "dotenv.main.DotEnv.dict",
            side_effect=RuntimeError("Offline credential loading disabled"),
        ),
    ):
        sys.argv = [
            module,
            *(["discover", "-s", "tests", "-v"] if arguments.action == "test" else []),
            *remaining,
        ]
        from harness.spec_ownership import proposal_scope

        # Infrastructure tests are measurement, not a human spec review or acceptance.
        with proposal_scope() if arguments.action == "test" else nullcontext():
            runpy.run_module(module, run_name="__main__")


if __name__ == "__main__":
    main()
