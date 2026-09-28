"""Regressions from the supplied 51b74ca audit; no synthetic authority is promoted."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from harness import live
from harness.contract_preflight import collect
from harness.rule_invariants import enforce, evaluate
from harness.runtime import ROOT
from harness.spec_compiler import build, compile_spec
from harness.spec_ownership import PIN, reread
from tests.authority_fixture import copy_requirement_authority


class AuditControls(unittest.TestCase):
    def test_quantifier_inversion_stays_unknown_after_named_reread(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            copy_requirement_authority(root)
            spec = root / "spec.md"
            spec.write_text(
                spec.read_text()
                .replace("must not exceed PARAM-INITIAL-001", "must be at least PARAM-INITIAL-001")
                .replace(" | Thomas Hand | ", " | Synthetic Audit Person | ")
            )
            (root / PIN).unlink()
            compiled = build(root)
            reread("ARCH-SOURCE-001", "Synthetic Audit Person", root)
            row = next(r for r in evaluate(compiled) if r["id"] == "D1-005")
            self.assertEqual((row["status"], row["code"]), ("UNKNOWN", "D_SENTENCE_UNCHECKED"))
            self.assertEqual(row["constraint_status"], "UNKNOWN")
            enforce(compiled)

    def test_preflight_collects_contradiction_and_stale_receipt(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            copy_requirement_authority(root)
            spec = root / "spec.md"
            text = spec.read_text()
            lines = text.splitlines()
            i = next(i for i, line in enumerate(lines) if line.startswith("BR-CONTRADICTION |"))
            lines[i] = lines[i].rsplit(" | ", 1)[0] + " | FIRM_CANDIDATE"
            spec.write_text("\n".join(lines) + "\n")
            output = root / "probe"
            output.mkdir()
            data, _ = collect(root, output)
            self.assertIn("UNRECORDED_SPEC_CHANGE", {r["code"] for r in data["findings"]})
            contradictions = [r for r in data["findings"] if r["code"] == "BOUNDARY_VIOLATION"]
            self.assertIn("D5-001", {r["row"] for r in contradictions})
            self.assertTrue(all("spec.md:" in r["reason"] for r in contradictions))

    def test_assumption_mutation_is_a_preflight_refusal(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            copy_requirement_authority(root)
            path = root / "spec.md"
            path.write_text(
                path.read_text().replace(
                    "block automatic alerts on history gaps",
                    "allow automatic alerts on history gaps",
                )
            )
            output = root / "probe"
            output.mkdir()
            data, _ = collect(root, output)
            self.assertTrue(any(r["code"] == "UNRECORDED_SPEC_CHANGE" for r in data["findings"]))

    def test_date_refusal_names_field_raw_value_and_capture(self):
        from harness.input_contract_checks import run

        contract = compile_spec()
        contract["date_formats"] = ["%d/%m/%Y %I:%M:%S%p", "ISO8601"]
        with tempfile.TemporaryDirectory() as directory:
            result = run(contract, Path(directory) / "input.json")
        self.assertEqual(result["status"], "FAIL")
        self.assertTrue(any(r.get("field", "").startswith("header.") for r in result["findings"]))
        self.assertTrue(any("01/14/2026" in r["reason"] for r in result["findings"]))
        self.assertTrue(
            any("notice inherited/evaluation/notices/" in r["reason"] for r in result["findings"])
        )

    def test_one_refusal_per_invocation_preserves_original_cause(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)

            def sink():
                path = root / str(len(list(root.iterdir())))
                path.mkdir()
                return path

            def failed_preflight():
                live.record_refusal(
                    "CREDENTIALS_MISSING", "Synthetic missing credentials", "ReadinessFailure"
                )
                return 1

            with patch.object(live, "refusal_directory", side_effect=sink):
                for _ in range(2):
                    self.assertEqual(live.entry(failed_preflight), 1)
            receipts = list(root.glob("*/failure.json"))
            self.assertEqual(len(receipts), 2)
            self.assertTrue(
                all(
                    json.loads(p.read_text())["error_domain"] == "CREDENTIALS_MISSING"
                    for p in receipts
                )
            )

    def test_config_change_does_not_masquerade_as_synthetic_execution(self):
        from harness.adapter import llm_utils
        from harness.behavior_contract import load
        from harness.comparison_identity import build as identity
        from harness.signal_evaluation import execute
        from harness.specification import fixtures

        contract = load()
        with patch.dict("os.environ", {"LLM_MODEL": "audit-nonexistent-model"}):
            config = identity(contract, fixtures())["model_configuration"]
        self.assertEqual(config["status"], "UNKNOWN")
        self.assertFalse(config["live_model_executed"])
        # Use evidence as required by the signal observer's relative-path contract.
        with tempfile.TemporaryDirectory(dir=ROOT / "evidence") as directory:
            path = Path(directory) / "signals"
            one_step = {**contract["state_safety"], "steps": contract["state_safety"]["steps"][:1]}
            with patch.object(llm_utils, "_MODEL", "audit-nonexistent-model"):
                execute(one_step, path, "candidate")
            parsed = json.loads((path / "A/parser.json").read_text())
            self.assertTrue(parsed["model_calls"])
            self.assertEqual(
                {c["configured_model"] for c in parsed["model_calls"]}, {"synthetic-provider"}
            )
