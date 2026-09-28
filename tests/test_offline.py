"""Verify offline isolation before the inherited configuration is imported."""

import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


class OfflineLaunchTests(unittest.TestCase):
    def test_launcher_blocks_credentials_and_external_access(self):
        # A synthetic module replaces only the dispatch target in this child.
        # The production launcher and inherited imports execute unchanged.
        script = """
import os, runpy, socket, sys
from pathlib import Path
from unittest.mock import patch
from harness.offline import main
def probe(module, run_name):
    from harness.adapter import llm_utils
    assert not llm_utils.is_llm_available()
    assert llm_utils._API_KEY == ''
    for action in [lambda: Path('.env').read_text(),
                   lambda: Path('.env.synthetic').read_text(),
                   lambda: __import__('dotenv').dotenv_values('alternate-synthetic-config'),
                   lambda: socket.getaddrinfo('example.invalid', 443)]:
        try:
            action()
        except RuntimeError:
            pass
        else:
            raise AssertionError('Offline boundary allowed forbidden access')
    print('offline boundary verified')
sys.argv = ['offline', 'context', '--task', 'unused-dispatch-probe']
with patch.object(runpy, 'run_module', probe):
    main()
"""
        environment = dict(os.environ, ANTHROPIC_API_KEY="synthetic-test-only", LLM_ENABLED="true")
        result = subprocess.run(
            [sys.executable, "-B", "-c", script],
            env=environment,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), "offline boundary verified")
        self.assertNotIn("synthetic-test-only", result.stdout + result.stderr)

    def test_documented_context_dispatch_produces_real_package(self):
        with tempfile.TemporaryDirectory() as directory:
            result = subprocess.run(
                [
                    sys.executable,
                    "-B",
                    "-m",
                    "harness.offline",
                    "context",
                    "--task",
                    "notice-snapshot-maintenance",
                    "--output",
                    directory,
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue((Path(directory) / "package.json").is_file())


if __name__ == "__main__":
    unittest.main()
