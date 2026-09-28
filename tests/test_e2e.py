"""Live execution proof must reject empty successes, fallback and missing persistence."""

import copy
import unittest
from typing import Any

from harness.e2e import completion_checks


class E2ECompletionTests(unittest.TestCase):
    def setUp(self):
        self.metadata = [{"notice_id": 42}]
        self.results: list[dict[str, Any]] = [
            {
                "notice": {"notice_id": 42, "is_signal": 0, "validity_flags": '["llm_extraction"]'},
                "locations": [],
                "restrictions": [],
            }
        ]
        self.calls = [
            {"success": True, "request_id": "request-test", "response": {"id": "response-test"}}
        ]
        self.helpers = [{"result": "none"}]
        self.state = {"notices": [{"notice_id": 42}], "foreign_key_violations": []}

    def checks(self, **overrides):
        arguments: dict[str, Any] = dict(
            metadata=self.metadata,
            results=self.results,
            calls=self.calls,
            helpers=self.helpers,
            state=self.state,
            report=[],
            cli_exit=0,
        )
        arguments.update(overrides)
        return completion_checks(**arguments)

    def test_successful_negative_notice_may_have_empty_signal_report(self):
        self.assertTrue(all(self.checks().values()))

    def test_zero_exit_with_no_inputs_is_not_success(self):
        checks = self.checks(metadata=[], results=[], calls=[], helpers=[], state={}, report=[])
        self.assertFalse(all(checks.values()))

    def test_api_success_does_not_hide_fallback_or_lost_state(self):
        results = copy.deepcopy(self.results)
        results[0]["notice"]["validity_flags"] = '["regex_fallback"]'
        overrides: list[dict[str, Any]] = [
            {"results": results},
            {"helpers": [{"result": None}]},
            {"calls": [{"success": True, "response": {"id": "response-test"}}]},
            {"state": {"notices": [], "foreign_key_violations": []}},
            {"report": None},
            {"cli_exit": 1},
        ]
        for override in overrides:
            with self.subTest(override=override):
                self.assertFalse(all(self.checks(**override).values()))


if __name__ == "__main__":
    unittest.main()
