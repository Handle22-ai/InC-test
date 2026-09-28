"""Release-blocking authority, status extension, context and evidence invariants."""

from __future__ import annotations

import copy
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import yaml

from harness import behavior_contract, context, current_evidence, requirements, specification
from harness import normalized_evaluation as evaluation
from harness.runtime import ROOT, digest, write_json
from rebuilt.normalized_classifier import classify
from tests.authority_fixture import copy_requirement_authority, promote


class RequirementRevisionTests(unittest.TestCase):
    def test_repin_and_same_change_approval_are_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            copy_requirement_authority(root)
            for name in (
                "spec.md",
                "requirements/requirements.yaml",
                "context/authority-reference.json",
            ):
                target = root / name
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(ROOT / name, target)
            path = root / "requirements/requirements.yaml"
            document = yaml.safe_load(path.read_text())
            row = next(r for r in document["requirements"] if r["id"] == "SAFETY-001")
            old = row["preconditions"]
            row["preconditions"] = old.replace("Every execution", "At least one execution")
            self.assertNotEqual(old, row["preconditions"])
            path.write_text(yaml.safe_dump(document, sort_keys=False))
            spec = root / "spec.md"
            spec.write_text(spec.read_text().replace(old, row["preconditions"]))
            reference_path = root / "context/authority-reference.json"
            reference = json.loads(reference_path.read_text())
            reference["registered_row_sha256"][row["id"]] = hashlib.sha256(
                json.dumps(row, sort_keys=True).encode()
            ).hexdigest()
            write_json(reference_path, reference)
            with patch.object(requirements, "ROOT", root):
                with self.assertRaisesRegex(ValueError, "GENERATED_ARTIFACT_DRIFT"):
                    requirements.load_requirements(path)
                promote(root, row)
                with self.assertRaisesRegex(ValueError, "GENERATED_ARTIFACT_DRIFT"):
                    requirements.load_requirements(path)
                decision = root / "context/decisions/synthetic-requirement.md"
                decision.write_text(
                    decision.read_text().replace(
                        row["preconditions"], "Different normative wording"
                    )
                )
                reference = json.loads(reference_path.read_text())
                reference["registered_context"][str(decision.relative_to(root))]["sha256"] = digest(
                    decision
                )
                write_json(reference_path, reference)
                with self.assertRaisesRegex(ValueError, "GENERATED_ARTIFACT_DRIFT"):
                    requirements.load_requirements(path)


class BoundaryAndEvidenceTests(unittest.TestCase):
    def test_enum_extension_alone_never_grants_root_or_linked_semantics(self):
        witness = copy.deepcopy(
            next(row for row in specification.fixtures() if row["id"] == "firm-positive")["input"]
        )
        contract = behavior_contract.load()
        # Change only the disposable compiled schema; production artifacts are untouched.
        schema = contract["normalized_input_schema"]

        def extend(value):
            if isinstance(value, dict):
                if value.get("enum") == ["INITIATE", "SUPERSEDE", "TERMINATE"]:
                    value["enum"].append("WITHDRAWN")
                for child in value.values():
                    extend(child)
            elif isinstance(value, list):
                for child in value:
                    extend(child)

        extend(schema)

        # The disposable contract is supplied explicitly to the component.
        witness["notice"]["status"] = "WITHDRAWN"
        self.assertEqual(classify(witness, contract).proposal["disposition"], "REVIEW_REQUIRED")
        self.assertEqual(classify(witness, contract).matched_rule, "BR-HISTORY")
        prior = {
            "notice": copy.deepcopy(witness["notice"]),
            "facts": copy.deepcopy(witness["facts"]),
            "source_sha256": witness["source"]["sha256"],
        }
        prior["notice"]["notice_id"] -= 1
        witness["notice"]["prior_notice_id"] = prior["notice"]["notice_id"]
        witness["history"] = [prior]
        self.assertEqual(classify(witness, contract).proposal["disposition"], "REVIEW_REQUIRED")
        witness["notice"]["status"] = "SUPERSEDE"
        self.assertEqual(classify(witness, contract).proposal["disposition"], "REVIEW_REQUIRED")

    def test_complete_rows_retained_with_compact_markdown_index(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)
            package = context.write_package("recommendation-classification-maintenance", path)
            text = (path / "package.md").read_text()
            for row in package["requirements"]:
                self.assertIn(row["id"], text)
            self.assertEqual(
                json.loads((path / "package.json").read_text())["requirements"],
                package["requirements"],
            )
            self.assertIn("preconditions", text)
            self.assertIn("component availability", text)
            self.assertIn("unapproved", text)

    def test_renderer_is_run_data_only_and_does_not_touch_tracked_current(self):
        result: dict = {
            "scope": "synthetic-renderer-test",
            "source": {"revision": "synthetic", "working_tree_dirty": False},
            "accepted": False,
            "application_accepted": False,
            "gates": {"1": {"name": "contracts", "status": "FAIL"}},
            "findings": [],
            "trading_layer": {"scope": "synthetic", "metrics": {"sentinel": {"count": 7}}},
            "publisher_layer": {
                "sequence": [
                    {
                        "step": "F",
                        "initial_count": 1,
                        "disposition": "INITIAL_RECOMMENDATION",
                        "reason": "synthetic regression",
                    }
                ],
                "duplicate_replay_recommendations": ["F"],
            },
        }
        before = digest(ROOT / "evidence/CURRENT.md")
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)
            write_json(path / "manifest.json", {"files": {}})
            current_evidence.render(path, result)
            first = (path / "CURRENT.md").read_text()
            self.assertIn("| sentinel | 7 |", first)
            result["trading_layer"]["metrics"]["sentinel"]["count"] = 19
            current_evidence.render(path, result)
            second = (path / "CURRENT.md").read_text()
            self.assertEqual(first.replace("| sentinel | 7 |", "| sentinel | 19 |"), second)
            evaluation.verify_evidence(path, json.loads((path / "manifest.json").read_text()))
        self.assertEqual(before, digest(ROOT / "evidence/CURRENT.md"))

    def test_registering_a_reference_does_not_erase_an_unmeasured_edit(self):
        from harness.normalized_evaluation import edits_covered_by_last_reread

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "context").mkdir()
            spec = (ROOT / "spec.md").read_text()
            before = spec.replace(
                '"max_false_positives_per_capture": 0', '"max_false_positives_per_capture": 1'
            )
            self.assertNotEqual(before, spec)
            (root / "spec.md").write_text(before)
            git = ["git", "-c", "user.name=t", "-c", "user.email=t@t"]
            subprocess.run([*git, "init", "-q"], cwd=root, check=True)
            subprocess.run([*git, "add", "-A"], cwd=root, check=True)
            subprocess.run([*git, "commit", "-qm", "before"], cwd=root, check=True)
            (root / "spec.md").write_text(spec)
            pin = {
                "spec_sha256": hashlib.sha256(spec.encode()).hexdigest(),
                "previous_read": {"spec_sha256": hashlib.sha256(before.encode()).hexdigest()},
            }
            write_json(root / "context/spec-read-pin.json", pin)
            covered = edits_covered_by_last_reread(set(), root)
            first = "spec-settings / acceptance (edited)"
            self.assertEqual(covered["edits"], [{"declaration": first, "unmeasured": False}])
            flagged = edits_covered_by_last_reread({first}, root)
            self.assertTrue(flagged["edits"][0]["unmeasured"])
        result: dict = {
            "scope": "synthetic-renderer-test",
            "source": {"revision": "synthetic", "working_tree_dirty": False},
            "accepted": False,
            "gates": {"3": {"name": "regression_change", "status": "PASS"}},
            "findings": [],
            "reference_registration": {
                "path": "evidence/reference-x",
                "source_commit": "abcdef0",
                "registered_by": "Owner A",
                "unmeasured_policy_edits": [first],
            },
            "spec_edits_since_reference": [],
            "spec_edits_covered_by_last_reread": flagged,
        }
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)
            write_json(path / "manifest.json", {"files": {}})
            current_evidence.render(path, result)
            text = (path / "CURRENT.md").read_text()
        self.assertIn("Unmeasured policy edits this reference was registered over", text)
        self.assertIn(f"- {first} — **UNMEASURED**", text)

    def test_extra_command_arguments_are_rejected_before_execution(self):
        result = subprocess.run(
            [sys.executable, "-B", "-m", "harness.commands", "evaluate-spec", "--unknown"],
            cwd=ROOT,
            text=True,
            capture_output=True,
        )
        self.assertEqual(result.returncode, 2)
        self.assertIn("COMMAND_VALIDATION", result.stderr)
