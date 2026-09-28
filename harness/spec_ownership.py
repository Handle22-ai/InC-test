"""Review records are byte-read receipts. Required spec review lives outside the repo."""

from __future__ import annotations

import argparse
import json
from contextlib import contextmanager
from contextvars import ContextVar
from pathlib import Path

from harness.runtime import ROOT, digest
from harness.spec_compiler import compile_spec, fail

PIN = "context/spec-read-pin.json"
_PROPOSAL: ContextVar[tuple[Path, str] | None] = ContextVar("proposal_spec", default=None)


@contextmanager
def proposal_scope(root: Path = ROOT):
    """Explicit measurement only; never writes or impersonates a human read receipt."""
    import os

    from rebuilt.rule_engine import MEASUREMENT_ENV

    spec = digest(root / "spec.md")
    token = _PROPOSAL.set((root.resolve(), spec))
    previous = os.environ.get(MEASUREMENT_ENV)
    os.environ[MEASUREMENT_ENV] = spec  # the component's explicit measurement switch
    try:
        yield
    finally:
        _PROPOSAL.reset(token)
        if previous is None:
            os.environ.pop(MEASUREMENT_ENV, None)
        else:
            os.environ[MEASUREMENT_ENV] = previous


REVIEW_LIMITS = {
    "incommodities_approval": False,
    "production_authorization": False,
    "cryptographic_authentication": False,
    "materiality_approval": False,
    "recommendation_authorization": False,
    "delivery_authorization": False,
    "unknown_lifecycle_obligations_pass": False,
}


def _review_record(root: Path, c: dict, decision: str, person: str, reference: dict) -> dict:
    """Bind a supplied identity assertion without changing the reviewed spec bytes."""
    row = next((r for r in c["decisions"] if r["ID"] == decision), None)

    def refuse():
        return fail(
            "spec-decisions",
            decision,
            row["_line"] if row else 1,
            "INVALID_REVIEW_RECORD: exact spec, decision, named reviewer and assessment limits required",
        )

    try:
        name = reference["path"]
        path = root / name
        if (
            not isinstance(name, str)
            or Path(name).is_absolute()
            or ".." in Path(name).parts
            or not path.resolve().is_relative_to((root / "context").resolve())
            or digest(path) != reference["sha256"]
        ):
            raise refuse()
        record = json.loads(path.read_text())
        if (
            record["kind"] != "exact-spec-owner-review-v1"
            or record["spec_sha256"] != c["source_spec_sha256"]
            or not isinstance(person, str)
            or not person.strip()
            or "PENDING" in person
            or record["repository_owner"] != person
            or record["reviewer"] != person
            or record["status"] != "reviewed-for-assessment"
            or record["limits"] != REVIEW_LIMITS
            or any(value is not False for value in record["limits"].values())
            or not isinstance(record["user_statement"], str)
            or not record["user_statement"].strip()
            or decision not in record["decision_bodies"]
        ):
            raise refuse()
        for identity, body in record["decision_bodies"].items():
            covered = next((r for r in c["decisions"] if r["ID"] == identity), None)
            if (
                covered is None
                or body != {k: v for k, v in covered.items() if k != "_line"}
                or covered["Status"] not in {"approved", "owner-requested"}
                or covered["Person"] not in {person, "PENDING_PERSON"}
            ):
                raise refuse()
        return record
    except (OSError, ValueError, KeyError, TypeError, AttributeError) as exc:
        raise refuse() from exc


def spec_text_with_hash(root: Path, sha256: str) -> str | None:
    """The spec bytes with this SHA-256: the working file or a committed version."""
    import hashlib
    import subprocess

    current = (root / "spec.md").read_text()
    if hashlib.sha256(current.encode()).hexdigest() == sha256:
        return current
    try:
        commits = subprocess.check_output(
            ["git", "log", "--format=%H", "--", "spec.md"],
            cwd=root,
            text=True,
            stderr=subprocess.DEVNULL,
        ).split()
        for commit in commits:
            text = subprocess.check_output(
                ["git", "show", f"{commit}:spec.md"], cwd=root, text=True, stderr=subprocess.DEVNULL
            )
            if hashlib.sha256(text.encode()).hexdigest() == sha256:
                return text
    except OSError, subprocess.CalledProcessError:
        return None
    return None


def owners_as_of(root: Path, reviewed_sha256: str | None, current: dict) -> list[str]:
    """Owners declared by an already reread spec, so an edit cannot name its own reviewer.

    Only when that spec declared no owners (the reread that introduces the list) does
    the list in the spec being reread apply.
    """
    if reviewed_sha256:
        text = spec_text_with_hash(root, reviewed_sha256)
        if text is not None:
            try:
                listed = compile_spec(root, text).get("owners")
            except ValueError:
                listed = None
            if listed:
                return list(listed)
    return list(current.get("owners", []))


def acceptance_loosening(root: Path, contract: dict) -> list[str]:
    """Gate 2 budgets loosened relative to the spec last reread (audit 4 #3)."""
    pin_path = root / PIN
    if not pin_path.exists():
        return []
    reviewed = spec_text_with_hash(root, json.loads(pin_path.read_text())["spec_sha256"])
    if reviewed is None:
        return []
    try:
        old = compile_spec(root, reviewed).get("acceptance") or {}
    except ValueError:
        return []
    new = contract.get("acceptance") or {}
    loosened = [
        f"{key}: {old[key]} -> {new.get(key)}"
        for key in old
        if key.startswith("max_") and new.get(key, old[key]) > old[key]
    ]
    added = sorted(set(new.get("review_satisfies", [])) - set(old.get("review_satisfies", [])))
    if added:
        loosened.append(f"review_satisfies adds {added}")
    return loosened


def check_acceptance(root: Path, contract: dict) -> None:
    """Refuse a loosened budget unless a new decision row says LOOSENS_ACCEPTANCE."""
    loosened = acceptance_loosening(root, contract)
    if not loosened:
        return
    pin = json.loads((root / PIN).read_text())
    declared = any(
        row["Previous spec SHA256"] == pin["spec_sha256"]
        and "LOOSENS_ACCEPTANCE" in row["Decision"]
        for row in contract["decisions"]
    )
    if not declared:
        raise fail(
            "spec-settings",
            "acceptance",
            1,
            "ACCEPTANCE_LOOSENED: "
            + "; ".join(loosened)
            + ". A decision row must say LOOSENS_ACCEPTANCE; budgets only tighten silently",
        )


def verify(root: Path = ROOT, contract: dict | None = None) -> dict:
    c = contract or compile_spec(root)
    if _PROPOSAL.get() == (root.resolve(), c["source_spec_sha256"]):
        return {
            "spec_sha256": c["source_spec_sha256"],
            "mode": "PROPOSAL_ONLY",
            "reviewed": False,
            "approval": False,
            "meaning": "Execution for measurement; exact human review remains pending",
        }
    try:
        pin = json.loads((root / PIN).read_text())
    except (OSError, ValueError) as exc:
        raise fail(
            "spec-decisions",
            c["decisions"][0]["ID"],
            c["decisions"][0]["_line"],
            "STALE_SPEC_PIN: reread required; hash is not approval",
        ) from exc
    row = next((r for r in c["decisions"] if r["ID"] == pin.get("decision")), None)
    if row is None or pin.get("spec_sha256") != c["source_spec_sha256"]:
        row = next(
            (
                r
                for r in reversed(c["decisions"])
                if r["Previous spec SHA256"] == pin.get("spec_sha256")
            ),
            row,
        )
        raise fail(
            "spec-decisions",
            row["ID"] if row else str(pin.get("decision", "missing")),
            row["_line"] if row else 1,
            "UNRECORDED_SPEC_CHANGE / STALE_SPEC_PIN: current spec bytes are not covered by the previous read receipt; actual human reread required",
        )
    if pin.get("review_record") is not None:
        _review_record(root, c, row["ID"], pin.get("person"), pin["review_record"])
    elif (
        row["Status"] not in {"approved", "owner-requested"}
        or not row["Person"].strip()
        or "PENDING" in row["Person"]
        or pin.get("person") != row["Person"]
    ):
        raise fail(
            "spec-decisions",
            row["ID"],
            row["_line"],
            "UNRECORDED_SPEC_CHANGE: decision status and person required; pending is not authority",
        )
    current = {r["ID"]: {k: v for k, v in r.items() if k != "_line"} for r in c["decisions"]}
    if pin.get("decision_body") != current[row["ID"]] or any(
        current.get(key) != body for key, body in pin.get("decisions", {}).items()
    ):
        raise fail(
            "spec-decisions", row["ID"], row["_line"], "decision differs from reread receipt"
        )
    if pin.get("approval") is not False:
        raise fail("spec-decisions", row["ID"], row["_line"], "read receipt is not approval")
    previous = pin.get("previous_read") or {}
    listed = owners_as_of(root, previous.get("spec_sha256"), c)
    if listed and pin.get("person") not in listed:
        raise fail(
            "spec-settings",
            "owners",
            1,
            "UNRECORDED_SPEC_CHANGE / STALE_SPEC_PIN: the read receipt names "
            f"{pin.get('person')!r}, who is not a spec owner ({listed})",
        )
    return pin


def changes_since_last_read(c: dict, root: Path) -> list[dict]:
    """Decision rows that record a change made after the previous reread."""
    if not (root / PIN).exists():
        raise fail(
            "spec-decisions", "-", 1, "first reread: name the decision it covers with --decision"
        )
    previous = json.loads((root / PIN).read_text())
    covered = [
        r
        for r in c["decisions"]
        if r["Previous spec SHA256"] == previous["spec_sha256"]
        and r["ID"] not in {previous["decision"], *previous.get("decisions", {})}
    ]
    if not covered:
        raise fail(
            "spec-decisions",
            "-",
            c["decisions"][-1]["_line"],
            "no decision row records a change since the last reread "
            f"(Previous spec SHA256 {previous['spec_sha256']})",
        )
    return covered


def reread(
    decision: str | None, person: str, root: Path = ROOT, review_record: str | None = None
) -> dict:
    """Record that person reread the exact spec bytes.

    Without decision, the receipt covers every row that records a change since the
    previous reread; each must be approved (or owner-requested) and name person.
    """
    c = compile_spec(root)
    last = json.loads((root / PIN).read_text()) if (root / PIN).exists() else {}
    listed = owners_as_of(root, last.get("spec_sha256"), c)
    if listed and person not in listed:
        raise fail(
            "spec-settings",
            "owners",
            1,
            f"{person!r} is not a spec owner; a reread must name one of {listed}",
        )
    check_acceptance(root, c)  # against the previous receipt, before a new one replaces it
    covered = [] if decision is not None else changes_since_last_read(c, root)
    for other in covered:
        if other["Person"] != person or other["Status"] not in {"approved", "owner-requested"}:
            raise fail(
                "spec-decisions",
                other["ID"],
                other["_line"],
                f"row must be approved and name {person!r} before a reread can cover it",
            )
    if decision is None:
        decision = covered[-1]["ID"]
    row = next((r for r in c["decisions"] if r["ID"] == decision), None)
    reference = None
    if review_record is not None:
        try:
            reference = {"path": review_record, "sha256": digest(root / review_record)}
        except OSError as exc:
            raise fail(
                "spec-decisions", decision, row["_line"] if row else 1, "review record missing"
            ) from exc
        _review_record(root, c, decision, person, reference)
    if row is None or (
        reference is None
        and (
            row["Person"] != person
            or not person.strip()
            or "PENDING" in person
            or row["Status"] not in {"approved", "owner-requested"}
        )
    ):
        raise fail(
            "spec-decisions",
            decision,
            row["_line"] if row else 1,
            f"named recorded decision required: supplied reviewer {person!r} must match the decision person; status must be approved or owner-requested",
        )
    previous = json.loads((root / PIN).read_text()) if (root / PIN).exists() else None
    if previous and previous["spec_sha256"] != c["source_spec_sha256"]:
        if (
            previous["decision"] == decision
            or row["Previous spec SHA256"] != previous["spec_sha256"]
        ):
            raise fail(
                "spec-decisions",
                decision,
                row["_line"],
                "new decision must refer to previous read spec hash",
            )
    pin = {
        "spec_sha256": c["source_spec_sha256"],
        "decision": decision,
        "person": person,
        "decision_body": {k: v for k, v in row.items() if k != "_line"},
        "decisions": {
            r["ID"]: {k: v for k, v in r.items() if k != "_line"} for r in covered or [row]
        },
        "previous_read": previous,
        "approval": False,
        "meaning": "Exact bytes reread; person/status are assertions, not authentication. Required review on spec.md must be enforced outside this repo.",
    }
    if reference is not None:
        pin["review_record"] = reference
    (root / PIN).write_text(json.dumps(pin, indent=2) + "\n")
    return pin


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "--decision",
        help="Only for the first reread; otherwise every row added since the last reread is covered",
    )
    p.add_argument("--person", required=True)
    p.add_argument(
        "--review-record",
        help="Exact-spec owner identity assertion in context/; preserves the reviewed spec bytes",
    )
    a = p.parse_args()
    try:
        print(json.dumps(reread(a.decision, a.person, review_record=a.review_record), indent=2))
    except ValueError as exc:
        print(str(exc))
        raise SystemExit(2)


if __name__ == "__main__":
    main()
