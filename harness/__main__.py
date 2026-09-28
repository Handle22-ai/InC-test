"""python -m harness compile | reread | gate; all commands are offline."""

import runpy
import sys

command = sys.argv.pop(1) if len(sys.argv) > 1 else ""
modules = {
    "compile": "harness.spec_compiler",
    "reread": "harness.spec_ownership",
    "register-capture": "harness.capture_registration",
    "register-reference": "harness.baseline",
}
if command in modules:
    runpy.run_module(modules[command], run_name="__main__")
elif command in {"gate", "consequences"}:
    sys.argv.insert(1, "normalized" if command == "gate" else "consequences")
    runpy.run_module("harness.offline", run_name="__main__")
else:
    raise SystemExit(
        "Usage: python -m harness {compile|reread|gate|consequences|register-capture|register-reference}"
    )
