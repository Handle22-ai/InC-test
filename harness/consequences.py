"""Visible spec consequences over every registered capture case, without model calls."""

from __future__ import annotations

import json
import subprocess
from collections import Counter
from pathlib import Path

from harness.domain_rules import derive, explain
from harness.runtime import ROOT, write_json
from harness.spec_compiler import compile_spec
from rebuilt.normalization import normalize


def observations(contract: dict) -> list[dict]:
    from harness.captures import evaluation_clock, oracle, store_before, verified_capture
    from harness.trading_evaluation import semantic_evidence

    labels = oracle()
    result = []
    for index, name in enumerate(
        json.loads((ROOT / "requirements/trading-evidence.json").read_text())["captures"]
    ):
        capture = verified_capture(ROOT / name)
        retained: dict[int, dict] = {}
        for case in capture["cases"]:
            flags = json.loads(case["output"]["notice"].get("validity_flags", "[]"))
            semantic = {
                "extraction_usable": case.get("stages", {})
                .get("extraction", {})
                .get("scorable", "llm_extraction" in flags),
                "helpers": [(r["helper"], r["result"]) for r in case.get("helper_results", [])],
                "execution_error": None if case["outcome"] == "SUCCESS" else case["outcome"],
            }
            key = f"capture-{index}/{case['case_id']}"
            try:
                value, gaps = normalize(
                    case["output"],
                    case["input_sha256"],
                    semantic,
                    evaluation_clock(case, capture)[0],
                    [retained[i] for i in store_before(case) if i in retained],
                    contract=contract,
                )
                from harness.behavior_contract import validate_input

                validate_input(value, contract=contract)
                outcome = derive(contract, value)
                conditions = explain(contract, value)
                result.append(
                    {
                        "id": key,
                        "notice_id": case["notice_id"],
                        "source": case["input"],
                        "source_sha256": case["input_sha256"],
                        "outcome": outcome,
                        "conditions": conditions,
                        "normalization_gaps": gaps,
                        "normalized": value,
                    }
                )
                # History holds what the publisher stores: a decided (not UNRESOLVED)
                # notice whose semantic evidence is usable. Any other version leaves the
                # last valid one unchanged (spec D5-002), exactly as the gate replays it.
                if (
                    outcome["action"]["classification"] != "UNRESOLVED"
                    and semantic_evidence(case).refusal() is None
                ):
                    retained[value["notice"]["notice_id"]] = {
                        "notice": value["notice"],
                        "facts": value["facts"],
                        "source_sha256": value["source"]["sha256"],
                    }
            except (ValueError, KeyError, TypeError) as exc:
                result.append(
                    {
                        "id": key,
                        "notice_id": case["notice_id"],
                        "outcome": {
                            "rule": "INPUT-REFUSED",
                            "action": {
                                "classification": "UNRESOLVED",
                                "disposition": "ERROR",
                                "recommendation_allowed": False,
                            },
                        },
                        "conditions": [
                            {
                                "rule": r["id"],
                                "matched": False,
                                "first_failed": {
                                    "condition": "Input contract",
                                    "required": "usable fields",
                                    "observed": str(exc),
                                },
                            }
                            for r in contract["rules"]
                        ],
                    }
                )
        for row in result:
            if not row["id"].startswith(f"capture-{index}/"):
                continue
            source = next(
                case
                for case in capture["cases"]
                if f"capture-{index}/{case['case_id']}" == row["id"]
            )
            row["expected_signal"] = (
                labels[row["notice_id"]]["expected_signal"]
                if source.get("category") == "labeled"
                else None
            )
            row["inherited_signal"] = source["output"]["notice"].get("is_signal")
            row["inherited_execution"] = source["outcome"]
            row["inherited_system"] = capture["manifest"]["system"]
            row["source_critical"] = source["output"]["notice"].get("is_critical")
    return result


def spec_moved(
    before: dict,
    after: dict,
    before_rows: list[dict] | None = None,
    after_rows: list[dict] | None = None,
) -> list[str]:
    """Decisions that differ between two specs under the same evaluator (audit 5).

    Compares every captured case, every frozen classifier witness and every replay
    expectation. A decision is its rule, action name, reason and action, so an edit that
    changes only the reason still counts. Evaluator or oracle changes cannot appear
    here, because both specs are evaluated by the current code.
    """

    def signature(contract: dict, outcome: dict) -> tuple:
        rule: dict = next((r for r in contract["rules"] if r["id"] == outcome["rule"]), {})
        return (
            outcome["rule"],
            rule.get("action_name"),
            rule.get("output_reason"),
            json.dumps(outcome["action"], sort_keys=True),
        )

    moved = []
    old = {r["id"]: r for r in (before_rows if before_rows is not None else observations(before))}
    new = {r["id"]: r for r in (after_rows if after_rows is not None else observations(after))}
    for key in sorted(old.keys() | new.keys()):
        if key not in old or key not in new:
            moved.append(key)
        elif signature(before, old[key]["outcome"]) != signature(after, new[key]["outcome"]):
            moved.append(key)
    witnesses = json.loads((ROOT / "requirements/normalized-witnesses.json").read_text())
    for witness in witnesses:
        outcomes = []
        for contract in (before, after):
            try:
                outcomes.append(signature(contract, derive(contract, witness["input"])))
            except (ValueError, KeyError, TypeError) as exc:
                outcomes.append(("REFUSED", type(exc).__name__))
        if outcomes[0] != outcomes[1]:
            moved.append("witness/" + witness["id"])
    steps = [
        {s["id"]: s.get("expected") for s in c.get("state_safety", {}).get("steps", [])}
        for c in (before, after)
    ]
    moved += [
        "publisher/" + step
        for step in sorted(steps[0].keys() | steps[1].keys())
        if steps[0].get(step) != steps[1].get(step)
    ]
    return moved


def previous(contract: dict) -> tuple[str, list[dict], str]:
    def git(*args):
        return subprocess.check_output(
            ["git", *args], cwd=ROOT, text=True, stderr=subprocess.DEVNULL
        )

    current_text = (ROOT / "spec.md").read_text()
    head_spec = git("show", "HEAD:spec.md")
    try:
        revision = git("rev-parse", "HEAD" if head_spec != current_text else "HEAD^").strip()
    except subprocess.CalledProcessError:  # a single-commit history has no parent spec
        revision = git("rev-parse", "HEAD").strip()
    old = git("show", revision + ":spec.md")
    if "```spec-rules" in old:
        prior = compile_spec(ROOT, text=old)
        return (
            revision,
            observations(prior),
            "Spec-to-spec consequences with current fixed compiler; not a runtime regression mapping",
        )
    stored = json.loads(git("show", revision + ":evidence/current/trading/results.json"))
    rows = []
    for row in stored["observations"]:
        d = row["decision"]
        proposal = d.get("classifier_decision", d)
        rows.append(
            {
                "id": row["id"],
                "notice_id": row["notice_id"],
                "outcome": {
                    "rule": proposal.get("reason_codes", [d.get("matched_rule", "UNKNOWN")])[0],
                    "action": {
                        k: proposal.get(k)
                        for k in ("classification", "disposition", "recommendation_allowed")
                    },
                },
            }
        )
    return (
        revision,
        rows,
        "Previous committed execution retained verbatim; legacy spec has no compilable domain block. Different semantic identities remain noncomparable in Gate 3.",
    )


def render(result: dict, *, details: bool = True) -> str:
    lines = [
        "## Generated consequences of this spec",
        "",
        f"Captured cases: **{result['denominator']}** ({result['denominator'] // 23} captures of 23 cases; 14 labels per capture). No abstention is a correct negative.",
        "",
        "| Rule | Matches / cases | Wins / cases | First failed conditions (counts) |",
        "|---|---:|---:|---|",
    ]
    for row in result["rules"]:
        lines.append(
            f"| {row['id']} | {row['matches']}/{result['denominator']} | {row['wins']}/{result['denominator']} | "
            + "; ".join(f"{k}: {v}" for k, v in row["first_failed_counts"].items())
            + " |"
        )
    lines += [
        "",
        f"Previous commit: `{result.get('previous_commit', 'UNAVAILABLE')}`. {result['comparison_scope']}",
        "",
        "| Notice/capture | From | To |",
        "|---|---|---|",
    ]

    def outcome_label(value):
        if value is None:
            return "Unavailable"
        action = value["action"]
        return f"{action['classification']} / {action['disposition']} ({value['rule']})"

    for row in result["changed_outcomes"]:
        lines.append(
            f"| {row['id']} | {outcome_label(row['before'])} | {outcome_label(row['after'])} |"
        )
    if not result["changed_outcomes"]:
        lines.append("| — | No changed outcome observed | — |")
    if not details:
        return "\n".join(lines) + "\n"
    lines += [
        "",
        "### Every nonmatch: first failed domain condition",
        "",
        "| Notice/capture | Rule | First failed condition | Required | Observed |",
        "|---|---|---|---|---|",
    ]
    for row in result["cases"]:
        for observation in row["conditions"]:
            if not observation["matched"]:
                f = observation["first_failed"]
                lines.append(
                    f"| {row['id']} | {observation['rule']} | {f['condition']} | {f['required']} | {f['observed']} |"
                )
    return "\n".join(lines) + "\n"


def run(contract: dict, destination: Path) -> dict:
    cases = observations(contract)
    rules = []
    for rule in contract["rules"]:
        conditions = [
            next(r for r in case["conditions"] if r["rule"] == rule["id"]) for case in cases
        ]
        rules.append(
            {
                "id": rule["id"],
                "spec_line": rule["spec_line"],
                "matches": sum(r["matched"] for r in conditions),
                "wins": sum(c["outcome"]["rule"] == rule["id"] for c in cases),
                "first_failed_counts": dict(
                    Counter(r["first_failed"]["condition"] for r in conditions if not r["matched"])
                ),
            }
        )
    try:
        revision, before, scope = previous(contract)
    except (ValueError, KeyError, subprocess.CalledProcessError) as exc:
        revision, before, scope = (
            None,
            [],
            f"UNKNOWN: previous commit comparison unavailable: {type(exc).__name__}",
        )
    by_id = {c["id"]: c["outcome"] for c in before}
    changed = [
        {
            "id": c["id"],
            "notice_id": c["notice_id"],
            "before": by_id.get(c["id"]),
            "after": c["outcome"],
        }
        for c in cases
        if by_id.get(c["id"], {}).get("action") != c["outcome"]["action"]
        or by_id.get(c["id"], {}).get("rule") != c["outcome"]["rule"]
    ]
    result = {
        "spec_sha256": contract["source_spec_sha256"],
        "denominator": len(cases),
        "rules": rules,
        "cases": cases,
        "previous_commit": revision,
        "comparison_scope": scope,
        "changed_outcomes": changed,
        "meaning": "Spec consequences derived from retained facts; generated expectations are not independent evaluation labels or approval",
    }
    write_json(destination / "consequences.json", result)
    write_json(
        destination / "replay-expectations.json",
        {
            "source_spec_sha256": contract["source_spec_sha256"],
            "cases": {c["id"]: c["outcome"] for c in cases},
            "independent_oracle": False,
        },
    )
    rendered = render(result)
    (destination / "consequences.md").write_text(rendered)
    (destination / "spec-rendered.md").write_text((ROOT / "spec.md").read_text() + "\n" + rendered)
    return result
