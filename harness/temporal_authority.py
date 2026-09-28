"""Committed approval must precede activation; this does not authenticate an owner."""

from __future__ import annotations

import hashlib
import json
import subprocess
from functools import lru_cache
from pathlib import Path

# Freeze the approval window before implementation. A worker cannot manufacture
# two commits in its candidate change and call the first one prior approval.
# Moving this ceiling is a verifier/approval-boundary change, not a hash repin.
APPROVAL_CEILING = "b69a466dd4322ecc3ba083af4d268ccc0f44ded4"


class SelfPromotion(ValueError):
    pass


def git(root: Path, *args: str) -> str:
    try:
        return subprocess.check_output(
            ["git", *args], cwd=root, text=True, stderr=subprocess.DEVNULL
        ).strip()
    except subprocess.CalledProcessError as exc:
        raise SelfPromotion("UNAPPROVED_SELF_PROMOTION: committed approval unavailable") from exc


@lru_cache(maxsize=4096)
def committed_digest(root: Path, revision: str, name: str) -> str:
    try:
        data = subprocess.check_output(
            ["git", "show", f"{revision}:{name}"], cwd=root, stderr=subprocess.DEVNULL
        )
    except subprocess.CalledProcessError as exc:
        raise SelfPromotion(
            "UNAPPROVED_SELF_PROMOTION: approval absent in ancestor: " + name
        ) from exc
    return hashlib.sha256(data).hexdigest()


@lru_cache(maxsize=4096)
def changed_at(root: Path, head: str, name: str) -> str:
    return git(root, "log", "-1", "--format=%H", head, "--", name)


@lru_cache(maxsize=4096)
def ancestor(root: Path, earlier: str, later: str) -> bool:
    return (
        subprocess.run(
            ["git", "merge-base", "--is-ancestor", earlier, later],
            cwd=root,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        ).returncode
        == 0
    )


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def record_precedes(
    root: Path,
    name: str,
    active_paths: tuple[str, ...] = (),
    *,
    approval_ceiling: str = APPROVAL_CEILING,
) -> None:
    """Also reject same-commit promotion after later evidence-only commits."""
    head = git(root, "rev-parse", "HEAD")
    sha = digest(root / name)
    if committed_digest(root, head, name) != sha:
        raise SelfPromotion("UNAPPROVED_SELF_PROMOTION: uncommitted approval: " + name)
    approval = changed_at(root, head, name)
    if not ancestor(root, approval, approval_ceiling):
        raise SelfPromotion(
            "UNAPPROVED_SELF_PROMOTION: approval was created after the frozen approval window"
        )
    if ancestor(root, approval, "b9cd042ab7313e6ad519089836768e470922c42b"):
        return  # Previously active approvals are retained; new promotions are prospective.
    for active in active_paths:
        path = root / active
        try:
            active_sha = committed_digest(root, head, active)
        except SelfPromotion:
            continue  # Proposed activation in a working tree, not committed acceptance.
        if active_sha != digest(path):
            continue
        activation = changed_at(root, head, active)
        if approval == activation or not ancestor(root, approval, activation):
            raise SelfPromotion(
                "UNAPPROVED_SELF_PROMOTION: approval must precede activation of " + active
            )


def verify(root: Path) -> dict:
    try:
        pin = json.loads((root / "context/temporal-approval.json").read_text())
        head = git(root, "rev-parse", "HEAD")
        approval = pin["approval_commit"]
        name = pin["approval_record"]
        if not ancestor(root, approval, APPROVAL_CEILING):
            raise SelfPromotion(
                "UNAPPROVED_SELF_PROMOTION: new candidate approval cannot promote itself"
            )
        if not ancestor(root, approval, head):
            raise SelfPromotion("UNAPPROVED_SELF_PROMOTION: approval is not an ancestor")
        if committed_digest(root, approval, name) != digest(root / name):
            raise SelfPromotion("UNAPPROVED_SELF_PROMOTION: approval record changed")
        record = json.loads((root / name).read_text())
        for key in ("policy_id", "policy_version"):
            if pin[key] != record[key]:
                raise SelfPromotion("UNAPPROVED_SELF_PROMOTION: policy revision mismatch")
        owner = record["owner_record"]
        if committed_digest(root, approval, owner) != record["owner_sha256"]:
            raise SelfPromotion("UNAPPROVED_SELF_PROMOTION: owner wording/hash mismatch")
        for target, expected in record["approved_artifacts"].items():
            frozen = "context/approvals/011/files/" + target
            if (
                committed_digest(root, approval, frozen) != expected
                or digest(root / target) != expected
            ):
                raise SelfPromotion(
                    "UNAPPROVED_SELF_PROMOTION: unapproved normative bytes: " + target
                )
            try:
                at_head = committed_digest(root, head, target)
            except SelfPromotion:
                at_head = None
            if at_head == expected:
                activation = changed_at(root, head, target)
                if activation == approval or not ancestor(root, approval, activation):
                    raise SelfPromotion(
                        "UNAPPROVED_SELF_PROMOTION: implementation must follow approval: " + target
                    )
        revisions = json.loads((root / "requirements/requirement-revisions.json").read_text())
        if any(
            revisions[key]["revision"] != value
            for key, value in record["requirement_revisions"].items()
        ):
            raise SelfPromotion("UNAPPROVED_SELF_PROMOTION: requirement revision mismatch")
        return {
            "approval_commit": approval,
            "implementation_head": head,
            "human_authenticated": False,
        }
    except (KeyError, OSError, TypeError, json.JSONDecodeError) as exc:
        raise SelfPromotion("UNAPPROVED_SELF_PROMOTION: incomplete approval boundary") from exc
