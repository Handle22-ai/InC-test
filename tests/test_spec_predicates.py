"""The spec owns predicate meaning; the component evaluates it without harness code."""

from __future__ import annotations

import json
import re
import subprocess
import sys
import unittest

from harness.domain_rules import derive
from harness.runtime import ROOT
from harness.spec_compiler import compile_spec
from rebuilt.normalized_classifier import classify

WITNESSES = json.loads((ROOT / "requirements/normalized-witnesses.json").read_text())


def witness(name: str) -> dict:
    return next(row["input"] for row in WITNESSES if row["id"] == name)


def edited(old: str, new: str) -> dict:
    text = (ROOT / "spec.md").read_text()
    if text.count(old) != 1:
        raise AssertionError("fixture edit must match exactly once: " + old)
    return compile_spec(ROOT, text.replace(old, new))


class SpecPredicateTests(unittest.TestCase):
    def test_component_imports_no_harness_module(self):
        probe = (
            "import json, sys\n"
            "from rebuilt.normalized_classifier import classify\n"
            "from rebuilt.rule_engine import load_policy\n"
            "print(json.dumps(sorted(m for m in sys.modules if m.split('.')[0] == 'harness')))\n"
        )
        loaded = subprocess.run(
            [sys.executable, "-B", "-c", probe], cwd=ROOT, capture_output=True, text=True
        )
        self.assertEqual(loaded.returncode, 0, loaded.stderr)
        self.assertEqual(json.loads(loaded.stdout), [])

    def test_component_and_harness_oracle_agree_on_every_witness(self):
        contract = compile_spec(ROOT)
        for row in WITNESSES:
            with self.subTest(witness=row["id"]):
                try:
                    expected = derive(contract, row["input"])["rule"]
                except ValueError:
                    with self.assertRaises(ValueError):
                        classify(row["input"], contract)
                    continue
                self.assertEqual(classify(row["input"], contract).matched_rule, expected)

    def test_a_set_edit_in_the_spec_changes_behavior_without_code(self):
        value = witness("firm-positive")  # secondary firm service, unavailable
        self.assertEqual(classify(value, compile_spec(ROOT)).matched_rule, "BR-FIRM")
        text = (ROOT / "spec.md").read_text()
        current = re.search(r'"FIRM_SERVICES": \[[^\]]*\]', text)
        assert current is not None
        narrowed = compile_spec(ROOT, text.replace(current[0], '"FIRM_SERVICES": ["PRIMARY_FIRM"]'))
        self.assertEqual(classify(value, narrowed).matched_rule, "BR-UNRESOLVED")
        self.assertEqual(derive(narrowed, value)["rule"], "BR-UNRESOLVED")

    def test_a_condition_edit_in_the_spec_changes_behavior_without_code(self):
        value = witness("firm-positive")
        value = {**value, "evidence": {**value["evidence"], "helpers_usable": False}}
        self.assertEqual(classify(value, compile_spec(ROOT)).matched_rule, "BR-FIRM")
        strict = edited(
            "evidence.extraction_usable and (evidence.helpers_usable or [Service class] = FIRM_DISRUPTION)",
            "evidence.extraction_usable and evidence.helpers_usable",
        )
        self.assertEqual(classify(value, strict).matched_rule, "BR-SEMANTICS")

    def test_a_restriction_ended_under_every_timezone_is_historical(self):
        value = witness("firm-positive")
        naive = {
            **value,
            "facts": {
                **value["facts"],
                "time_basis": "UNRESOLVED",
                "start_time": None,
                "end_time": None,
                "restrictions": [
                    {
                        "service": "PRIMARY_FIRM",
                        "availability": "UNAVAILABLE",
                        "restriction_type": "UNAVAILABLE",
                        "status": "UNKNOWN",
                        "location_index": 0,
                        "source_start": "2026-01-01T09:00:00",
                        "source_end": "2026-01-10T09:00:00",
                        "evidence_ref": "synthetic",
                    }
                ],
            },
        }
        contract = compile_spec(ROOT)
        cases = {
            "2026-01-10T20:00:00+00:00": "BR-FIRM",  # within 14 h: some zone still current
            "2026-01-10T23:00:00+00:00": "BR-HISTORICAL",  # ended in every zone
        }
        for clock, expected in cases.items():
            with self.subTest(reference=clock):
                probe = {**naive, "reference_time": clock}
                self.assertEqual(classify(probe, contract).matched_rule, expected)
                self.assertEqual(derive(contract, probe)["rule"], expected)
        tbd = {**naive, "reference_time": "2027-01-01T00:00:00+00:00"}
        tbd["facts"] = {
            **naive["facts"],
            "restrictions": [{**naive["facts"]["restrictions"][0], "source_end": "TBD"}],
        }
        self.assertEqual(classify(tbd, contract).matched_rule, "BR-FIRM")

    def test_a_margin_below_every_utc_offset_is_a_boundary_violation(self):
        with self.assertRaisesRegex(ValueError, "no_timezone_inference"):
            from harness.rule_invariants import enforce

            enforce(
                edited('"unresolved_time_margin_hours": 14', '"unresolved_time_margin_hours": 6')
            )

    def test_ambiguous_date_formats_are_refused(self):
        from harness.input_contract_checks import matching_formats

        month_first = ["%m/%d/%Y %I:%M:%S%p", "%m/%d/%Y", "ISO8601"]
        self.assertEqual(matching_formats("03/04/2026", month_first), [])
        both = ["%d/%m/%Y", *month_first]
        self.assertEqual(len(matching_formats("03/04/2026", both)), 2)
        self.assertEqual(matching_formats("03/31/2026", both), [])

    def test_unlabeled_samples_are_reported_without_classification(self):
        from harness.input_contract_checks import unlabeled_samples

        report = unlabeled_samples(compile_spec(ROOT))
        self.assertEqual((report["html_notices"], report["pdf_notices"]), (25, 7))
        self.assertEqual(report["html_contract_errors"], [])
        self.assertEqual(report["pdf_unsupported"], 7)

    def test_each_captured_case_sees_only_the_store_it_was_captured_with(self):
        from harness import consequences
        from harness.captures import store_before, verified_capture

        rows = {row["id"]: row for row in consequences.observations(compile_spec(ROOT))}
        for name in ("capture-0", "capture-1"):
            missing = rows[f"{name}/missing-prior"]["outcome"]
            self.assertEqual(missing["features"]["History"], "GAP")
            self.assertEqual(missing["rule"], "BR-HISTORY")
        registry = json.loads((ROOT / "requirements/trading-evidence.json").read_text())
        capture = verified_capture(ROOT / registry["captures"][0])
        for case in capture["cases"]:
            history = rows[f"capture-0/{case['case_id']}"].get("normalized", {}).get("history", [])
            ids = {entry["notice"]["notice_id"] for entry in history}
            self.assertTrue(ids <= set(store_before(case)), case["case_id"])

    def test_audit3_mutations_are_boundary_violations(self):
        from harness.rule_invariants import enforce

        text = (ROOT / "spec.md").read_text()
        precedence = next(line for line in text.splitlines() if line.startswith("Precedence:"))
        swapped = precedence.replace("BR-HISTORY > BR-UNCHANGED", "BR-UNCHANGED > BR-HISTORY")
        self.assertNotEqual(swapped, precedence)
        with self.assertRaisesRegex(ValueError, "refusals_first"):
            enforce(compile_spec(ROOT, text.replace(precedence, swapped)))
        status = next(line for line in text.splitlines() if "| header.status |" in line)
        relaxed = status.replace("| text | ERROR | ERROR |", "| text | UNKNOWN | ERROR |")
        self.assertNotEqual(relaxed, status)
        with self.assertRaisesRegex(ValueError, "required_inputs"):
            enforce(compile_spec(ROOT, text.replace(status, relaxed)))

    def test_an_empty_list_is_never_within_a_set(self):
        """Audit 4 #6: unknown services must not satisfy a `within` condition vacuously."""
        text = (ROOT / "spec.md").read_text()
        within = compile_spec(
            ROOT,
            text.replace(
                "facts.services overlaps FIRM_SERVICES and",
                "facts.services within FIRM_SERVICES and",
            ),
        )
        value = witness("firm-positive")
        value = {
            **value,
            "facts": {**value["facts"], "services": [], "restrictions": []},
        }
        self.assertNotEqual(classify(value, within).matched_rule, "BR-FIRM")
        self.assertNotEqual(derive(within, value)["rule"], "BR-FIRM")

    def test_malformed_predicates_name_the_spec_row(self):
        cases = {
            "unknown path": (
                "facts.content_kind = RESTRICTION and",
                "facts.kind = RESTRICTION and",
            ),
            "unknown set": ("service in FIRM_SERVICES", "service in FIRM"),
            "earlier column": (
                "[Information-only] = YES and [Restriction] = KNOWN",
                "[Service class] = OTHER",
            ),
            "otherwise": (
                "Format | UNSUPPORTED | otherwise",
                "Format | UNSUPPORTED | facts.time_basis = UTC",
            ),
        }
        for name, (old, new) in cases.items():
            with self.subTest(case=name), self.assertRaisesRegex(ValueError, "spec-predicates"):
                edited(old, new)


if __name__ == "__main__":
    unittest.main()
