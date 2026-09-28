"""The offline credential guard, kept in its own module so the hook and its single
exception share one state even when harness.offline runs as __main__."""

from __future__ import annotations

import os
from contextvars import ContextVar
from pathlib import Path

_MODEL_SETTING_READ: ContextVar[str | None] = ContextVar("model_setting_read", default=None)


def reject_external_access(event: str, arguments: tuple) -> None:
    if event in {"socket.connect", "socket.getaddrinfo", "socket.bind"}:
        raise RuntimeError("Offline harness command: network access is disabled")
    if event == "open" and isinstance(arguments[0], (str, bytes)):
        path = os.fsdecode(arguments[0])
        if str(Path(path).resolve()) == _MODEL_SETTING_READ.get():
            return  # the single read model_setting() performs
        if Path(path).name.startswith(".env") or Path(path).resolve().name.startswith(".env"):
            raise RuntimeError("Offline harness command: credential-file access is disabled")


def model_setting(path: Path) -> str | None:
    """Return only LLM_MODEL from a dotenv file; every other line is discarded unread.

    The inherited system loads such a file for live runs, so the offline gate must know
    the model it names. Credentials in the same file are never kept or returned.
    """
    token = _MODEL_SETTING_READ.set(str(path.resolve()))
    try:
        with path.open() as handle:
            for line in handle:
                key, sep, value = line.strip().removeprefix("export ").partition("=")
                if sep and key.strip() == "LLM_MODEL":
                    return value.split("#", 1)[0].strip().strip("'\"") or None
    finally:
        _MODEL_SETTING_READ.reset(token)
    return None
