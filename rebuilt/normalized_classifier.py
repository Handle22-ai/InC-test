"""Bounded normalized classifier: spec-compiled policy at runtime, no witness/label input."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path

from rebuilt.rule_engine import check_schema, decide, load_policy, schema


@dataclass(frozen=True)
class Decision:
    matched_rule: str
    proposal: dict

    @property
    def reason(self) -> str:
        return self.proposal["reason_codes"][1]


def classify(value: dict, policy: dict | None = None) -> Decision:
    """Load the current generated policy for each decision unless one is supplied."""
    policy = policy or load_policy()
    rule, _ = decide(value, policy)
    references = {value["source"]["bytes_reference"], *value["evidence"]["references"]}
    for facts in [value["facts"], *[item["facts"] for item in value["history"]]]:
        for key in ("locations", "quantities"):
            references.update(item["evidence_ref"] for item in facts[key])
    references.update("sha256:" + item["source_sha256"] for item in value["history"])
    proposal = {
        "notice_id": value["notice"]["notice_id"],
        "source_sha256": value["source"]["sha256"],
        **rule["action"],
        "reason_codes": [rule["id"], rule["output_reason"]],
        "evidence_refs": sorted(references),
    }
    check_schema(proposal, schema(policy, "output"), "output")
    return Decision(rule["id"], proposal)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    args = parser.parse_args()
    try:
        value = json.loads(args.input.read_text())
        decision = classify(value)
    except (OSError, ValueError, TypeError, KeyError) as exc:
        review_pending = "STALE_SPEC_PIN" in str(exc) or "UNRECORDED_SPEC_CHANGE" in str(exc)
        print(
            json.dumps(
                {
                    "status": "REVIEW_PENDING" if review_pending else "ERROR",
                    "classification": "REVIEW_PENDING"
                    if review_pending
                    else "INPUT_OR_CONTRACT_ERROR",
                    "reason": str(exc),
                }
            ),
            file=sys.stderr,
        )
        return 3 if review_pending else 2
    # Preserve the frozen stdout schema. The explicit matched_rule API field is
    # also represented by reason_codes[0] and retained in evaluation receipts.
    print(json.dumps(decision.proposal, sort_keys=True, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
