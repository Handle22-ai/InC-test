"""Offline tests of evidence validity; no live provider calls or inherited repairs."""

import copy
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

import yaml
from bs4 import BeautifulSoup

from harness.adapter import ModelObserver, notice_parser
from harness.evaluator import transform
from harness.gates import aggregate, check_case, evaluate
from harness.regression import compare
from harness.requirements import load_requirements
from harness.runtime import ROOT, write_json


class RequirementsTests(unittest.TestCase):
    def test_valid_and_bound(self):
        requirements = load_requirements()
        self.assertEqual({r["validation"]["gate"] for r in requirements}, {1, 2, 3})
        self.assertTrue(all(r["statement"] in (ROOT / "spec.md").read_text() for r in requirements))

    def test_duplicate_and_unbound_rejected(self):
        base = yaml.safe_load((ROOT / "requirements/requirements.yaml").read_text())
        for mutate in ("duplicate", "unbound", "drift", "unapproved"):
            data = copy.deepcopy(base)
            if mutate == "duplicate":
                data["requirements"].append(
                    next(r for r in data["requirements"] if r["id"] == "INPUT-001")
                )
            elif mutate == "unbound":
                next(r for r in data["requirements"] if r["id"] == "INPUT-001")["validation"][
                    "check"
                ] = "imaginary"
            elif mutate == "drift":
                next(r for r in data["requirements"] if r["id"] == "INPUT-001")["statement"] = (
                    "Undocumented new policy"
                )
            else:
                next(r for r in data["requirements"] if r["id"] == "INPUT-001")["governance"] = (
                    "proposed"
                )
            with tempfile.TemporaryDirectory() as directory:
                file = Path(directory) / "requirements.yaml"
                file.write_text(yaml.safe_dump(data))
                with self.subTest(mutate=mutate), self.assertRaises(ValueError):
                    load_requirements(file)


class GateTests(unittest.TestCase):
    def test_unobserved_is_never_pass(self):
        self.assertEqual(aggregate([]), "UNKNOWN")
        self.assertEqual(aggregate(["PASS", "UNKNOWN"]), "UNKNOWN")
        self.assertEqual(aggregate(["PASS", "FAIL"]), "FAIL")
        self.assertEqual(aggregate(["FAIL", "ERROR"]), "ERROR")

    def test_execution_failure_is_not_false_negative(self):
        req = next(r for r in load_requirements() if r["id"] == "SIGNAL-001")
        case = {
            "case_id": "bad",
            "notice_id": 1,
            "category": "labeled",
            "outcome": "ENVIRONMENT_FAILURE",
            "evidence_ref": "case.json",
        }
        result = check_case(req, case)
        assert result is not None
        self.assertEqual(result["status"], "ERROR")
        self.assertEqual(result["failure_domain"], "ENVIRONMENT_FAILURE")

    def test_authoritative_oracle_drives_classification(self):
        req = next(r for r in load_requirements() if r["id"] == "SIGNAL-001")
        case: dict = {
            "case_id": "known",
            "notice_id": 46624,
            "category": "labeled",
            "outcome": "SUCCESS",
            "evidence_ref": "case.json",
            "annotations": {"expected_signal": True},
            "output": {"notice": {"is_signal": 0}, "locations": [], "restrictions": []},
        }
        result = check_case(req, case)
        assert result is not None
        self.assertEqual(result["status"], "FAIL")
        self.assertEqual(result["failure_domain"], "BEHAVIORAL_FAILURE")
        case["annotations"]["expected_signal"] = False
        revised = check_case(req, case)
        assert revised is not None
        self.assertEqual(revised["status"], "FAIL")
        case["output"]["notice"]["is_signal"] = 1
        corrected = check_case(req, case)
        assert corrected is not None
        self.assertEqual(corrected["status"], "PASS")

    def test_approved_policy_without_a_check_stays_unknown(self):
        deferred = [r for r in load_requirements() if r["check_status"] == "not_available"]
        self.assertTrue(deferred)
        self.assertTrue(
            all(r["approval"] in {"owner-approved", "existing-contract"} for r in deferred)
        )
        findings = evaluate(deferred, [], {})
        self.assertEqual(len(findings), len(deferred))
        self.assertTrue(all(f["status"] == "UNKNOWN" for f in findings))

    def test_check_errors_do_not_become_behavior(self):
        req = next(r for r in load_requirements() if r["id"] == "OUTPUT-001")
        case = {
            "case_id": "invalid",
            "outcome": "SUCCESS",
            "evidence_ref": "case.json",
            "output": {},
        }
        result = evaluate([req], [case], {})[0]
        self.assertEqual(result["failure_domain"], "HARNESS_FAILURE")


class EvidenceTests(unittest.TestCase):
    def test_roundtrip_and_nonfinite_rejection(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "result.json"
            payload = {"decision": False, "risk": "test", "value": None}
            write_json(path, payload)
            self.assertEqual(json.loads(path.read_text()), payload)
            with self.assertRaises(ValueError):
                write_json(path, {"bad": float("nan")})

    def test_observer_delegates_original_response(self):
        sent = []
        response = SimpleNamespace(
            _request_id="request-test", model_dump=lambda **k: {"id": "message-test"}
        )

        def create(**kwargs):
            sent.append(kwargs)
            return response

        real_for_test = SimpleNamespace(messages=SimpleNamespace(create=create), close=lambda: None)
        observer = ModelObserver()
        observer.factory = lambda: real_for_test
        returned = observer.client().messages.create(model="test-model", messages=[])
        self.assertIs(returned, response)
        self.assertEqual(len(sent), 1)
        self.assertTrue(observer.calls[0]["success"])

    def test_observer_never_persists_error_text(self):
        def fail(**kwargs):
            raise RuntimeError("synthetic-secret-value")

        observer = ModelObserver()
        observer.factory = lambda: SimpleNamespace(
            messages=SimpleNamespace(create=fail), close=lambda: None
        )
        with self.assertRaises(RuntimeError):
            observer.client().messages.create(model="test-model")
        self.assertNotIn("synthetic-secret-value", json.dumps(observer.calls))

    def test_provider_failures_keep_their_cause_but_not_secrets(self):
        from harness.live import provider_error, request_failure

        class ProviderError(Exception):
            def __init__(self, status, kind, message):
                super().__init__("raw text sk-ant-api03-secret")
                self.status_code = status
                self.body = {"type": "error", "error": {"type": kind, "message": message}}

        billing = ProviderError(
            400,
            "invalid_request_error",
            "Your credit balance is too low to access the Anthropic API. key sk-ant-api03-abc",
        )
        self.assertEqual(request_failure(billing), "BILLING")
        kept = provider_error(billing)
        assert kept is not None
        self.assertIn("credit balance is too low", kept["message"])
        self.assertNotIn("sk-ant", json.dumps(kept))
        missing = ProviderError(404, "not_found_error", "model: claude-nonexistent")
        self.assertEqual(request_failure(missing), "MODEL_NOT_FOUND")
        other = ProviderError(500, "api_error", "Internal server error")
        self.assertEqual(request_failure(other), "PROVIDER_FAILURE")

        def fail(**kwargs):
            raise billing

        import harness.live as live

        observer = ModelObserver()
        observer.factory = lambda: SimpleNamespace(
            messages=SimpleNamespace(create=fail), close=lambda: None
        )
        blocker = live._blocker
        try:
            with self.assertRaises(ProviderError):
                observer.client().messages.create(model="test-model")
            self.assertEqual(live._blocker, "BILLING")
        finally:
            live._blocker = blocker
        record = observer.calls[0]
        self.assertEqual((record["classification"], record["status_code"]), ("BILLING", 400))
        self.assertIn("credit balance", record["provider_error"]["message"])
        self.assertNotIn("sk-ant", json.dumps(observer.calls))

    def test_revision_changes_only_header_semantics(self):
        source = ROOT / "inherited/evaluation/notices/46624_CAPACITY CONSTRAINT.html"
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "revision.html"
            transform(source, target, 96624, prior_id=46624)
            old, new = [BeautifulSoup(p.read_text(), "html.parser") for p in (source, target)]
            self.assertEqual(notice_parser._extract_body(old), notice_parser._extract_body(new))
            header = notice_parser._extract_header(new)
            self.assertEqual(header["status"], "SUPERSEDE")
            self.assertEqual(header["prior_notice_id"], "46624")
            self.assertEqual(header["notice_id"], "96624")

    def test_percentage_mutation_has_one_target(self):
        source = ROOT / "inherited/evaluation/notices/46615_MAINTENANCE.html"
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "mutation.html"
            transform(source, target, 96615, percentage=(55, 65))
            body = notice_parser._extract_body(BeautifulSoup(target.read_text(), "html.parser"))
            self.assertIn("65%", body)
            self.assertNotIn("55%", body)


class RegressionTests(unittest.TestCase):
    def test_no_comparator_unknown(self):
        self.assertEqual(compare(None, {})["status"], "UNKNOWN")

    def test_new_pass_fail_unchanged_and_output_drift(self):
        def item(id, status):
            return dict(requirement_id=id, case_id="one", gate=1, status=status, observed=0)

        old: dict = {
            "findings": [item("A", "PASS"), item("B", "FAIL"), item("C", "PASS")],
            "cases": [],
        }
        new: dict = {
            "findings": [item("A", "FAIL"), item("B", "PASS"), item("C", "PASS")],
            "cases": [],
        }
        # Synthetic comparator fixture explicitly declares identical evaluation semantics.
        reference = {
            k: "synthetic-fixed" for k in ("policy", "oracle", "rules", "evaluation", "protocol")
        }
        old["comparison_identity"] = reference
        new["comparison_identity"] = reference
        result = compare(old, new)
        self.assertEqual(result["newly_failing"], ["A/one"])
        self.assertEqual(result["newly_passing"], ["B/one"])
        self.assertEqual(result["unchanged"], ["C/one"])
        self.assertEqual(result["status"], "FAIL")

    def test_removed_checks_do_not_pass(self):
        old = {
            "findings": [
                dict(requirement_id="A", case_id="x", gate=1, status="PASS", observed=True)
            ]
        }
        self.assertEqual(compare(old, {"findings": []})["status"], "UNKNOWN")


if __name__ == "__main__":
    unittest.main()
