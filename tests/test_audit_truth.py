"""Reproduced audit failures: exits, immutable gate inputs and honest observations."""

from __future__ import annotations

import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from harness.baseline import require_observed_run
from harness.behavior_contract import validate_input
from harness.consequences import observations
from harness.contract_preflight import collect
from harness.normalized_evaluation import declared_coverage
from harness.proposals import declaration_changes, run, summaries
from harness.rule_invariants import evaluate
from harness.runtime import ROOT, digest
from harness.spec_compiler import artifacts, build, compile_spec
from rebuilt.normalized_classifier import classify
from tests.authority_fixture import copy_requirement_authority


class AuditTruthTests(unittest.TestCase):
    def test_refused_gate_cannot_use_measure_override_and_help_is_local(self):
        for argument, expected in [("--measure", 2), ("--help", 0)]:
            run = subprocess.run(
                [sys.executable, "-B", "-m", "harness", "gate", argument],
                cwd=ROOT,
                text=True,
                capture_output=True,
            )
            self.assertEqual(run.returncode, expected)
            if argument == "--help":
                self.assertIn("--proposal", run.stdout)
                self.assertNotIn("{test,context", run.stdout)
            else:
                self.assertIn("unrecognized arguments: --measure", run.stderr)

    def test_gate_never_repairs_stale_generated_files(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            copy_requirement_authority(root)
            compiled = build(root)
            guarded = [*artifacts(compiled, root), "requirements/compiled-build.json"]
            before = {name: digest(root / name) for name in guarded}
            path = root / "spec.md"
            path.write_text(
                path.read_text().replace(
                    "Maximum initial alerts | 1 |", "Maximum initial alerts | 0 |"
                )
            )
            out = root / "run"
            out.mkdir()
            result, _ = collect(root, out)
            self.assertIn("GENERATED_ARTIFACT_DRIFT", {r["code"] for r in result["findings"]})
            self.assertEqual(before, {name: digest(root / name) for name in guarded})

    def test_retained_model_failures_cannot_be_correct_classifications(self):
        rows = observations(compile_spec())
        result = summaries(rows, inherited=True)
        original = next(r for r in result if r["capture"] == "capture-1")
        self.assertEqual(
            (original["true_positive"], original["true_negative"], original["errors"]), (6, 5, 2)
        )
        for key in ("capture-1/46528", "capture-1/46864"):
            row = next(r for r in rows if r["id"] == key)
            self.assertEqual(row["inherited_execution"], "MODEL_FAILURE")
            isolated = summaries([row], inherited=True)[0]
            self.assertEqual(isolated["true_positive"] + isolated["true_negative"], 0)
            self.assertEqual(isolated["errors"], 1)

    def test_unobserved_checks_block_and_out_of_scope_rows_are_never_claimed(self):
        requirements = {
            key: {"validation": {"gate": 1, "check": check}}
            for key, check in [("INPUT-001", "identity"), ("STATE-005", "out_of_scope")]
        }
        coverage, findings = declared_coverage(
            requirements, [{"requirement": "STATE-005", "status": "PASS"}]
        )
        self.assertEqual(coverage["INPUT-001"]["status"], "UNKNOWN")
        # An observation cannot bring an out-of-scope row into scope or make it PASS.
        self.assertEqual(coverage["STATE-005"]["status"], "OUT_OF_SCOPE")
        self.assertEqual([r["code"] for r in findings], ["DECLARED_CHECK_UNOBSERVED"])

    def test_new_unchecked_prose_compiles_and_inversion_never_claims_a_pass(self):
        text = (
            (ROOT / "spec.md")
            .read_text()
            .replace(
                "### D2 —",
                "[D1-012] Additional retention obligation needs evidence.\n\n### D2 —",
                1,
            )
        )
        text = text.replace(
            "D1-011 | - | UNCHECKED", "D1-011 | - | UNCHECKED\nD1-012 | - | UNCHECKED"
        )
        text = text.replace("blocks automatic alerting", "permits automatic alerting")
        rows = evaluate(compile_spec(text=text))
        for key in ("D1-004", "D1-012"):
            row = next(r for r in rows if r["id"] == key)
            self.assertEqual((row["status"], row["constraint_status"]), ("UNKNOWN", "UNKNOWN"))

    def test_candidate_reasons_exclude_fallback_and_absolute_volume_needs_basis(self):
        value = copy.deepcopy(
            next(
                r["input"]
                for r in json.loads((ROOT / "requirements/normalized-witnesses.json").read_text())
                if r["id"] == "firm-positive"
            )
        )
        proposal = classify(value).proposal
        self.assertEqual(proposal["classification"], "SIGNAL_CANDIDATE")
        self.assertNotIn("BR-UNRESOLVED", proposal["reason_codes"])
        value["facts"]["quantities"] = [
            {
                "kind": "ABSOLUTE_CURTAILMENT",
                "value": 150,
                "unit": "Dth",
                "basis": "",
                "evidence_ref": "source.fields.body",
            }
        ]
        with self.assertRaisesRegex(ValueError, "stated source"):
            validate_input(value)

    def test_settings_change_has_declaration_evidence(self):
        text = (ROOT / "spec.md").read_text()
        after = text.replace("%m/%d/%Y", "%d/%m/%Y")
        changes = declaration_changes(text, after)
        self.assertTrue(
            any(r["block"] == "spec-settings" and r["id"] == "date_formats" for r in changes)
        )

    def test_supplied_inputs_expose_a_zero_capture_format_change(self):
        text = (ROOT / "spec.md").read_text()
        lines = text.splitlines()
        index = next(i for i, line in enumerate(lines) if line.startswith("BR-FORMAT |"))
        lines[index] = lines[index].rsplit(" | ", 1)[0] + " | FIRM_CANDIDATE"
        value = copy.deepcopy(
            json.loads((ROOT / "requirements/normalized-witnesses.json").read_text())[0]["input"]
        )
        value["source"]["media_type"] = "application/pdf"
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            proposal, inputs = root / "proposal.md", root / "inputs.json"
            proposal.write_text("\n".join(lines) + "\n")
            inputs.write_text(json.dumps([{"id": "new-format", "input": value}]))
            output = root / "out"
            output.mkdir()
            result = run(proposal, str(ROOT / "spec.md"), output, inputs)
            self.assertEqual(len(result["changed_outcomes"]), 0)
            self.assertEqual(len(result["supplied_inputs"]["changed"]), 1)
            self.assertFalse(result["accepted"])

    def test_unknown_reference_is_observation_and_refused_run_is_not_reference(self):
        result: dict = {
            "mode": "PROPOSAL_ONLY",
            "cases": {"case": {}},
            "comparison_identity": {"spec": "x"},
            "gates": {key: {"status": "UNKNOWN"} for key in ("1", "2", "3")},
        }
        require_observed_run(result)
        self.assertEqual(result["gates"]["1"]["status"], "UNKNOWN")
        result["gates"]["2"]["classification"] = "NOT_RUN"
        with self.assertRaisesRegex(ValueError, "completed non-refused"):
            require_observed_run(result)
