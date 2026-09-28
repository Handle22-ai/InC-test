"""Safe evidence I/O, integrity fingerprints, and isolated run directories."""

from __future__ import annotations

import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]


class OutputDestinationError(ValueError):
    """No safe, exclusively owned evidence destination was obtained."""


def create_run(path: Path) -> Path:
    """Claim a fresh run once, before any database/provider work. Never reuse it."""
    try:
        path = validate_output(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.mkdir(exist_ok=False)
    except (OSError, ValueError) as exc:
        raise OutputDestinationError(
            "Choose a new writable directory beneath evidence; existing or invalid destinations are refused"
        ) from exc
    return path


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n")


def new_run(kind: str) -> Path:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ")
    path = ROOT / "evidence" / kind / stamp
    if path.exists():
        raise FileExistsError("Run identity already exists")
    return path


def validate_output(path: Path) -> Path:
    if ".." in path.parts or "\x00" in str(path):
        raise OutputDestinationError("Malformed output destination")
    path = path.resolve()
    evidence = ROOT / "evidence"
    if not path.is_relative_to(evidence) or path == evidence or path.exists():
        raise OutputDestinationError(
            "OUTPUT must be a new directory beneath evidence; existing or protected destinations are refused"
        )
    if any(part in {".", ".."} for part in path.parts):
        raise ValueError("Malformed output destination")
    return path


def integrity() -> dict:
    manifest = json.loads((ROOT / "artifacts/inherited_manifest.json").read_text())
    changed = [
        f["path"]
        for f in manifest["files"]
        if not (ROOT / f["path"]).exists() or digest(ROOT / f["path"]) != f["sha256"]
    ]
    expected = {f["path"] for f in manifest["files"]}
    # Never import an unlisted sibling module that could shadow dependencies.
    additions = [
        str(p.relative_to(ROOT))
        for p in (ROOT / "inherited").rglob("*")
        if p.is_file()
        and "__pycache__" not in p.parts
        and ".venv" not in p.parts
        and "venv" not in p.parts
        and p.suffix not in {".pyc", ".pyo"}
        and p.name not in {".DS_Store", ".env"}
        and (p.suffix in {".py", ".so", ".dylib", ".sh"} or p.stat().st_mode & 0o111)
        and str(p.relative_to(ROOT)) not in expected
    ]
    changed.extend(additions)
    return {
        "inherited_file_count": manifest["file_count"],
        "changed": changed,
        "unexpected_executables": additions,
        "baseline_commit": subprocess.check_output(
            ["git", "rev-list", "--max-parents=0", "HEAD"], cwd=ROOT, text=True
        ).strip(),
        "env_ignored": subprocess.run(["git", "check-ignore", "-q", ".env"], cwd=ROOT).returncode
        == 0,
    }


def require_pristine() -> None:
    if integrity()["changed"]:
        raise ValueError("Inherited inventory changed; use a separately identified candidate")


def provenance() -> dict:
    import importlib.metadata
    import platform

    paths = sorted(
        p
        for folder in ["harness", "requirements"]
        for p in (ROOT / folder).rglob("*")
        if p.suffix in {".py", ".yaml", ".json"}
    )
    paths += [
        ROOT / "spec.md",
        ROOT / "artifacts/dependencies.lock.txt",
        ROOT / "context/authority-reference.json",
    ]
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "integrity": integrity(),
        "python": platform.python_version(),
        "packages": {d.metadata["Name"]: d.version for d in importlib.metadata.distributions()},
        "files": {str(p.relative_to(ROOT)): digest(p) for p in paths if p.exists()},
        "inherited_manifest_sha256": digest(ROOT / "artifacts/inherited_manifest.json"),
        "model_and_prompt_source_sha256": digest(ROOT / "inherited/llm_utils.py"),
    }
