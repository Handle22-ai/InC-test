"""Collect a fresh inherited baseline after a successful real-provider preflight."""

from __future__ import annotations

import fcntl
import json
import sqlite3
from pathlib import Path
from typing import cast

from bs4 import BeautifulSoup, Tag

from harness.gates import evaluate, finding
from harness.live import LiveParser, add_live_arguments, baseline_path, entry, validate_live
from harness.regression import compare
from harness.requirements import load_requirements
from harness.runtime import ROOT, create_run, digest, integrity, new_run, provenance, write_json


def require_preflight(run: Path | None = None) -> str:
    from harness.live import LiveRefusal
    from harness.preflight import run_preflight
    from harness.runtime import create_run

    if run is None:
        raise ValueError(
            "Current enabled credential/configuration must be verified in this invocation, not by a historical PASS"
        )
    readiness = create_run(run / "readiness")
    record = run_preflight(readiness)
    if record["status"] != "PASS":
        raise LiveRefusal(str(record["classification"]))
    return str(readiness.relative_to(ROOT))


def transform(
    source: Path,
    target: Path,
    notice_id: int,
    prior_id: int | None = None,
    percentage: tuple[int, int] | None = None,
) -> None:
    soup = BeautifulSoup(source.read_text(), "html.parser")
    id_node = soup.find(id=lambda id: id and id.endswith("_lblID"))
    if id_node is None:
        raise ValueError("Fixture missing notice ID field")
    # Attribute selectors match Tags; the stubs expose find's wider text-search union.
    cast(Tag, id_node).string = str(notice_id)
    if prior_id is not None:
        for suffix, value in [("_lblPriorNotice", str(prior_id)), ("_lblStatus", "SUPERSEDE")]:
            node = soup.find(id=lambda id: id and id.endswith(suffix))
            if node is None:
                raise ValueError("Fixture missing revision field")
            cast(Tag, node).string = value
    if percentage:
        old, new = percentage
        matches = list(soup.find_all(string=lambda t: t and f"{old}%" in t))
        if len(matches) != 1:
            raise ValueError("Mutation must target exactly one explicit percentage")
        matches[0].replace_with(matches[0].replace(f"{old}%", f"{new}%"))
    target.write_text(str(soup))


def collect(
    run: Path, dataset: dict, *, notice_ids: set[int] | None = None, include_probes: bool = True
) -> list[dict]:
    from harness.adapter import InheritedAdapter, NoticeInput, database, state_snapshot

    adapter = InheritedAdapter()
    cases = []
    annotations = {c["notice_id"]: c for c in dataset["cases"]}

    def process(
        case_id: str,
        id: int,
        db_path: Path,
        category: str = "labeled",
        path: Path | None = None,
        annotation: dict | None = None,
        transformation: dict | None = None,
    ):
        path = path or ROOT / annotations[id]["path"]
        target = run / "cases" / f"{case_id}.json"
        conn = database.init_db(str(db_path))
        try:
            result = adapter.process(NoticeInput(case_id, path, id), conn, target)
            database.enable_fk(conn)
            result["notice_chain"] = database.get_notice_chain(conn, id)
            saved = state_snapshot(conn)
        finally:
            conn.close()
        with sqlite3.connect(db_path) as restored:
            result["reopened_state_equal"] = saved == state_snapshot(restored)
        result.update(
            category=category,
            annotations=annotation or annotations.get(id, {}),
            transformation=transformation,
            evidence_ref=str(target.relative_to(run)),
            database=str(db_path.relative_to(run)),
        )
        write_json(target, result)
        cases.append(result)
        print(f"{case_id}: {result['outcome']}", flush=True)

    from harness.live import budget_record

    for ann in dataset["cases"]:
        if notice_ids is None or ann["notice_id"] in notice_ids:
            budget = budget_record()
            if budget["blocker"] or budget["sdk_calls_remaining"] == 0:
                write_json(
                    run / "not-attempted.json",
                    {
                        "classification": "NOT_ATTEMPTED",
                        "root_cause": budget["blocker"] or "BUDGET_EXHAUSTED",
                        "remaining_notice_ids": [
                            r["notice_id"]
                            for r in dataset["cases"]
                            if (notice_ids is None or r["notice_id"] in notice_ids)
                            and str(r["notice_id"]) not in {c["case_id"] for c in cases}
                        ],
                        "derived_probes": "not attempted",
                        "budget": budget,
                    },
                )
                return cases
            process(str(ann["notice_id"]), ann["notice_id"], run / "labeled.db")

    if not include_probes:
        return cases
    if budget_record()["blocker"] or budget_record()["sdk_calls_remaining"] == 0:
        write_json(
            run / "not-attempted.json",
            {
                "classification": "NOT_ATTEMPTED",
                "derived_probes": "not attempted",
                "budget": budget_record(),
            },
        )
        return cases

    # Normal parse+model+insert paths; no response replay or forced decisions.
    state = run / "reprocessing.db"
    process("duplicate-seed", 46624, state, "seed")
    process("duplicate-input", 46624, state, "duplicate")
    # Every process call closes and reopens its connection: explicit restart/replay probe.
    process("restart-replay", 46624, state, "restart")
    generated = run / "inputs"
    generated.mkdir()
    revision = generated / "96624_unchanged_supersede.html"
    transform(ROOT / annotations[46624]["path"], revision, 96624, prior_id=46624)
    mutation_info = {
        "source_notice": 46624,
        "operation": "identity and supersede linkage only; operational body unchanged",
    }
    process("unchanged-revision", 96624, state, "revision", revision, transformation=mutation_info)
    process(
        "repeated-revision",
        96624,
        state,
        "repeated_revision",
        revision,
        transformation=mutation_info,
    )

    history_db = run / "out-of-order.db"
    process("missing-prior", 46732, history_db, "missing_history")
    process("late-prior-arrival", 46507, history_db, "out_of_order")
    process("reconcile-termination", 46732, history_db, "out_of_order")

    mutated = generated / "96615_percentage_mutation.html"
    transform(ROOT / annotations[46615]["path"], mutated, 96615, percentage=(55, 65))
    process(
        "field-mutation",
        96615,
        run / "field-mutation.db",
        "field_mutation",
        mutated,
        annotation={"fields": {"firm_mdq": 65}},
        transformation={
            "source_notice": 46615,
            "field": "firm_mdq",
            "before": 55,
            "after": 65,
            "signal_oracle": "No invented signal label for the changed restriction.",
        },
    )
    return cases


def main() -> int:
    parser = LiveParser()
    add_live_arguments(parser)
    parser.add_argument("--compare-to", type=Path)
    args = parser.parse_args()
    prior = baseline_path(args.compare_to)
    validate_live(args)
    from harness.adapter import llm_utils

    requirements = load_requirements()
    with (ROOT / ".harness.lock").open("w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        run = create_run(args.output or new_run("legacy"))
        preflight = require_preflight(run)
        dataset = json.loads((ROOT / "requirements/dataset.json").read_text())
        manifest = {
            "run_id": run.name,
            "system": "inherited",
            "preflight": preflight,
            "provenance": provenance(),
            "configured_model": llm_utils._MODEL,
            "dataset_sha256": digest(ROOT / "requirements/dataset.json"),
            "execution_boundary": "notice_parser.parse_notice_html + database.insert_notice",
        }
        write_json(run / "manifest.json", manifest)
        try:
            cases = collect(run, dataset)
            manifest["integrity_after"] = integrity()
            write_json(run / "manifest.json", manifest)
            findings = evaluate(requirements, cases, manifest)
            result = {"manifest": manifest, "cases": cases, "findings": findings}
            regression = compare(prior, result)
            result["regression"] = regression
            regression_req = next(
                r for r in requirements if r["validation"]["check"] == "regression"
            )
            findings.append(
                finding(
                    regression_req,
                    {"case_id": "run", "evidence_ref": "regression.json"},
                    regression["status"],
                    regression,
                    domain="UNKNOWN" if prior is None else None,
                )
            )
            write_json(run / "regression.json", regression)
            write_json(run / "results.json", result)
            from harness.evidence import render

            render(run, result, requirements)
            print(f"Preserved baseline: {run.relative_to(ROOT)}", flush=True)
            return (
                0
                if cases
                and all(c["outcome"] == "SUCCESS" for c in cases)
                and not (run / "not-attempted.json").exists()
                else 2
            )
        except Exception as exc:
            write_json(
                run / "execution_error.json",
                {
                    "classification": "HARNESS_FAILURE",
                    "error_type": type(exc).__name__,
                    "reason": str(exc),
                },
            )
            print(
                f"HARNESS_FAILURE: {type(exc).__name__}: {exc}; partial evidence retained.",
                flush=True,
            )
            return 2


if __name__ == "__main__":
    raise SystemExit(entry(main))
