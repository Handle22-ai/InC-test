"""Explicit code-owned boundary constraints; arbitrary prose is always unchecked."""

from __future__ import annotations

from harness.spec_compiler import fail


def evaluate(contract: dict) -> list[dict]:
    declarations = {r["ID"]: r for r in contract.get("check_declarations", [])}
    rules = {r["id"]: r for r in contract["rules"]}
    steps = contract["state_safety"]["steps"]
    totals: dict[str, int] = {}
    for row in steps:
        if row["id"] in {"A", "B", "C", "D", "E", "F"}:
            event = "root" if row["notice"] in {"root", "unchanged_revision"} else row["notice"]
            totals[event] = totals.get(event, 0) + row["expected"]["initial"]

    def safe(rule):
        return rules[rule]["action"]["classification"] == "UNRESOLVED" and rules[rule]["action"][
            "disposition"
        ] in {"ERROR", "REVIEW_REQUIRED"}

    def before(a, b):
        return rules[a]["priority"] < rules[b]["priority"]

    def guarded(rule, when):
        return rules[rule]["when"] == when and safe(rule) and before(rule, "BR-FIRM")

    checks = {}
    checks["history_refusal"] = guarded("BR-HISTORY", {"History": "GAP"})
    checks["conflict_refusal"] = guarded("BR-CONTRADICTION", {"Conflict": "YES"})
    checks["semantics_refusal"] = guarded("BR-SEMANTICS", {"Oracle answer": "UNUSABLE"}) and before(
        "BR-SEMANTICS", "BR-ROUTINE"
    )
    checks["invalid_refusal"] = (
        guarded("BR-FORMAT", {"Format": "UNSUPPORTED"})
        and checks["conflict_refusal"]
        and checks["semantics_refusal"]
        and before("BR-FORMAT", "BR-ROUTINE")
        and before("BR-CONTRADICTION", "BR-ROUTINE")
    )
    maximum = contract.get("parameters", {}).get("max_initial_alerts_per_event", 1)
    # The assessment's no-duplicate boundary cannot be relaxed by its tuning parameter.
    checks["one_initial"] = maximum <= 1 and all(n <= maximum for n in totals.values())
    checks["replay_suppression"] = all(
        r["expected"]["initial"] == 0 for r in steps if r["restart"] or r["id"] == "B"
    )
    checks["unchanged_suppression"] = (
        rules["BR-UNCHANGED"]["when"] == {"Operational change": "UNCHANGED"}
        and rules["BR-UNCHANGED"]["action"]["disposition"] == "SUPPRESSED"
        and before("BR-UNCHANGED", "BR-FIRM")
        and all(r["expected"]["initial"] == 0 for r in steps if r["notice"] == "unchanged_revision")
    )
    checks["unresolved_refusal"] = (
        safe("BR-UNRESOLVED")
        and rules["BR-UNRESOLVED"]["action"]["disposition"] == "REVIEW_REQUIRED"
        and rules["BR-UNRESOLVED"]["when"] == {}
    )
    checks["historical_precedence"] = (
        rules["BR-HISTORICAL"]["when"].get("Restriction current") == "ENDED"
        and rules["BR-HISTORICAL"]["action"]["classification"] == "NON_SIGNAL"
        and before("BR-HISTORICAL", "BR-FIRM")
    )
    checks["candidate_only"] = all(
        r["action"]["recommendation_allowed"] is False
        and (
            r["action"]["classification"] != "SIGNAL_CANDIDATE"
            or r["action"]["disposition"] == "CANDIDATE_ONLY"
        )
        for r in rules.values()
    ) and all(r["expected"]["initial"] == 0 for r in steps if not r["authorization"])
    # A margin below the largest UTC offset would quietly assume a zone.
    checks["no_timezone_inference"] = (
        contract["timezone"]["active_default"] is None
        and contract.get("unresolved_time_margin_hours", 14) >= 14
    )
    checks["clock_boundary"] = (
        checks["no_timezone_inference"]
        and checks["candidate_only"]
        and "Source clock" not in rules["BR-FIRM"]["when"]
        and "Restriction current" not in rules["BR-FIRM"]["when"]
        and checks["historical_precedence"]
    )
    schema = contract["normalized_input_schema"]
    props = schema["properties"]
    checks["source_identity"] = {"sha256", "pipeline"} <= set(
        props["source"]["required"]
    ) and "notice_id" in props["notice"]["required"]
    checks["explicit_history"] = (
        "history" in schema["required"]
        and "prior_notice_id" in props["notice"]["required"]
        and contract["history_statuses"]
        == {"root": ["INITIATE"], "linked": ["INITIATE", "SUPERSEDE", "TERMINATE"]}
    )
    checks["domain_identity"] = all(
        c not in {"Notice ID", "Subject", "Text similarity"}
        for r in rules.values()
        for c in r["when"]
    )
    checks["time_schema"] = "reference_time" in schema["required"] and {
        "start_time",
        "end_time",
        "time_basis",
    } <= set(props["facts"]["required"])
    checks["no_age_cutoff"] = not any(
        "age" in c.lower() or "sla" in c.lower() for r in rules.values() for c in r["when"]
    )
    checks["output_provenance"] = (
        all(r.get("id") and r.get("spec_line") for r in rules.values())
        and bool(contract.get("source_spec_sha256"))
        and {"notice_id", "source_sha256", "reason_codes", "evidence_refs"}
        <= set(contract["normalized_output_schema"]["required"])
    )
    checks["optional_unknown"] = all(
        r["Missing"] == "UNKNOWN"
        for r in contract["input_contract"]
        if r["Field"].startswith(("restrictions[].", "locations[]."))
    )
    checks["disposition_vocabulary"] = all(
        r["action"]["disposition"] not in {"PASS", "FAIL", "UNKNOWN"} for r in rules.values()
    )
    checks["no_labels_or_authorization"] = checks["candidate_only"] and not any(
        "label" in c.lower() for r in rules.values() for c in r["when"]
    )
    # Keyed on the action, not a rule name: no candidate-producing rule may require a
    # quantity/volume checklist column (none exists in the grammar today).
    checks["no_quantity_checklist"] = all(
        not any("quantity" in c.lower() or "volume" in c.lower() for c in r["when"])
        for r in rules.values()
        if r["action"]["classification"] == "SIGNAL_CANDIDATE"
    )
    # Every row that refuses on a safety condition precedes every row that can decide
    # (audit 3 #4). Keyed on conditions and actions, not rule names, so renaming or
    # adding rules cannot slip past it.
    guards = {
        ("Format", "UNSUPPORTED"),
        ("Oracle answer", "UNUSABLE"),
        ("Conflict", "YES"),
        ("History", "GAP"),
    }
    refusals = [r for r in rules.values() if safe(r["id"]) and guards & set(r["when"].items())]
    deciders = [r for r in rules.values() if r["action"]["classification"] != "UNRESOLVED"]
    checks["refusals_first"] = all(
        a["priority"] < b["priority"] for a in refusals for b in deciders
    )
    # Identity, status and body can never become optional (audit 3 #3): the parser
    # contract check alone compares the parser with the same row it reads.
    required = {
        "header.notice_id",
        "header.status",
        "body",
        "notice.notice_id",
        "notice.status",
        "notice.notice_type",
        "notice.body_text",
        "semantic.extraction_usable",
    }
    checks["required_inputs"] = all(
        r["Missing"] == "ERROR" and r["Malformed"] == "ERROR"
        for r in contract["input_contract"]
        if r["Field"] in required
    ) and required <= {r["Field"] for r in contract["input_contract"]}
    checks["no_absolute_inference"] = (
        contract["normalization"]["quantities"].get("SCHEDULED_TO_PCT_MDQ", {}).get("unit")
        == "PERCENT_MDQ"
    )
    # Arbitrary prose has no executable semantics. Never pair its text with PASS.
    results = [
        {
            **sentence,
            "kind": "prose_obligation",
            "status": "UNKNOWN",
            "constraint_status": "UNKNOWN",
            "code": "D_SENTENCE_UNCHECKED",
            "hand_authored_check": None,
            "sentence_coverage": "UNCHECKED",
            "scope": "Owned prose obligation; no semantic check. Referenced boundary checks are reported separately.",
        }
        for sentence in contract["sentences"]
    ]
    for name, passed in checks.items():
        references = [row for row in declarations.values() if row["Check"] == name]
        row = references[0] if references else {"_line": 1}
        results.append(
            {
                "id": "CHECK-" + name,
                "kind": "compiled_boundary",
                "sentence": name,
                "spec_line": row["_line"],
                "references": [r["ID"] for r in references],
                "status": "PASS" if passed else "FAIL",
                "constraint_status": "PASS" if passed else "FAIL",
                "code": "COMPILED_BOUNDARY_CHECK" if passed else "BOUNDARY_VIOLATION",
                "hand_authored_check": name,
                "sentence_coverage": "TABLE_ONLY",
                "scope": "Code-owned structural boundary listed in spec-checks; does not check the meaning of referenced prose or full runtime behavior",
            }
        )
    return results


def violation(row: dict) -> str:
    """Name the table edit's conflict with a code-owned boundary; prose is not interpreted."""
    return (
        f"BOUNDARY_VIOLATION: the rule, replay or parameter tables break code-owned boundary "
        f"{row['hand_authored_check']} (listed at {', '.join(row['references']) or row['id']})"
    )


def enforce(contract: dict) -> list[dict]:
    results = evaluate(contract)
    failed = [r for r in results if r["status"] == "FAIL"]
    if failed:
        row = next((r for r in failed if r["hand_authored_check"] == "one_initial"), failed[0])
        key = row["references"][0] if row["references"] else row["id"]
        raise fail(
            "spec-checks",
            key,
            row["spec_line"],
            violation(row),
        )
    return results
