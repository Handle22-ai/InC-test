"""Live and offline paths stay bound to the spec's check names (second audit, live run)."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from harness import gates, live
from harness.captures import verified_capture, with_oracle
from harness.requirements import load_requirements
from harness.runtime import ROOT
from harness.spec_compiler import CHECK_NAMES

LEGACY = ROOT / "evidence/legacy/20260926T185618.823020Z/results.json"


class CheckRegistryTests(unittest.TestCase):
    def test_every_check_name_has_a_live_branch(self):
        handled = gates.RUN_CHECKS | gates.CASE_CHECKS | gates.COMPONENT_ONLY_CHECKS
        self.assertEqual(set(CHECK_NAMES) - handled, set(), "check names with no live branch")
        self.assertEqual(handled - set(CHECK_NAMES), set(), "live branches for unknown checks")

    def test_every_declared_check_is_scored_on_a_retained_live_capture(self):
        """The live evaluator's scoring, run over a retained live capture, has no gaps."""
        capture = verified_capture(LEGACY)
        manifest = {**capture["manifest"], "integrity_after": {"changed": []}}
        findings = gates.evaluate(load_requirements(), with_oracle(capture["cases"]), manifest)
        broken = [
            (f["requirement_id"], f["observed"])
            for f in findings
            if f["failure_domain"] == "HARNESS_FAILURE"
        ]
        self.assertEqual(broken, [])


class ManifestTests(unittest.TestCase):
    def test_every_manifest_path_exists(self):
        import re

        import yaml

        def paths(value):
            if isinstance(value, dict):
                for item in value.values():
                    yield from paths(item)
            elif isinstance(value, list):
                for item in value:
                    yield from paths(item)
            elif isinstance(value, str) and re.fullmatch(r"[\w./-]+\.(md|json|yaml|py|txt)", value):
                yield value

        manifest = yaml.safe_load((ROOT / "context/manifest.yaml").read_text())
        missing = [p for p in paths(manifest) if not (ROOT / p).exists()]
        self.assertEqual(missing, [])


class ModelSettingTests(unittest.TestCase):
    def test_only_llm_model_is_read_from_a_dotenv_file(self):
        from harness.credential_guard import model_setting, reject_external_access

        with tempfile.TemporaryDirectory() as tmp:
            # Named like a dotenv file but not .env*, so the test can write it offline.
            path = Path(tmp) / "settings.dotenv"
            path.write_text("ANTHROPIC_API_KEY=sk-secret\nexport LLM_MODEL='claude-x' # note\n")
            self.assertEqual(model_setting(path), "claude-x")
            path.write_text("ANTHROPIC_API_KEY=sk-secret\n")
            self.assertIsNone(model_setting(path))
            # Outside model_setting(), the offline guard still refuses the file.
            with self.assertRaisesRegex(RuntimeError, "credential-file access"):
                reject_external_access("open", (str(Path(tmp) / ".env"),))


class CaptureRegistrationTests(unittest.TestCase):
    def test_a_live_run_registers_as_a_verified_capture_and_rolls_back_on_failure(self):
        import shutil

        from harness import capture_registration as cr

        originals = {p: p.read_text() for p in (cr.REGISTRY, cr.TRADING, cr.AUTHORITY)}
        with tempfile.TemporaryDirectory(dir=ROOT / "evidence", prefix="capture-test-") as tmp:
            copy = Path(tmp) / "run"
            shutil.copytree(LEGACY.parent, copy)
            try:
                record = cr.register(copy / "results.json")
                self.assertEqual(record["cases"], 23)
                verified_capture(copy / "results.json")
                with self.assertRaisesRegex(ValueError, "already registered"):
                    cr.register(copy / "results.json")
            finally:
                for file, text in originals.items():
                    file.write_text(text)
            (copy / "execution_error.json").write_text("{}")
            with self.assertRaisesRegex(ValueError, "HARNESS_FAILURE"):
                cr.register(copy / "results.json")
        for file, text in originals.items():
            self.assertEqual(file.read_text(), text)


class PreflightBudgetTests(unittest.TestCase):
    def run_preflight(self, budget: int) -> dict:
        from harness.adapter import llm_utils
        from harness.preflight import run_preflight
        from harness.signal_evaluation import provider

        synthetic = provider("root", "valid")
        create = synthetic.messages.create

        def with_request_id(**kwargs):
            response = create(**kwargs)
            response._request_id = "req_synthetic"  # a real provider always returns one
            return response

        synthetic.messages.create = with_request_id
        with (
            tempfile.TemporaryDirectory(dir=ROOT / "evidence", prefix="preflight-test-") as tmp,
            patch.object(llm_utils, "get_client", return_value=synthetic),
            patch.object(llm_utils, "_API_KEY", "synthetic-only"),
            patch.object(llm_utils, "_ENABLED", True),
            patch.object(live, "_remaining", budget),
            patch.object(live, "_limit", budget),
            patch.object(live, "_blocker", None),
        ):
            return run_preflight(Path(tmp))

    def test_a_blocked_helper_call_never_passes_or_reports_a_signal(self):
        record = self.run_preflight(1)
        self.assertNotEqual(record["status"], "PASS")
        self.assertIsNone(record.get("observed_signal"))

    def test_the_documented_budget_is_enough(self):
        record = self.run_preflight(2)
        self.assertEqual(record["status"], "PASS", record.get("classification"))


if __name__ == "__main__":
    unittest.main()
