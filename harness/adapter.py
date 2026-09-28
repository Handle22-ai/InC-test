"""Observe the inherited application without replacing its decisions or model responses."""

from __future__ import annotations

import hashlib
import json
import logging
import sqlite3
import sys
from contextlib import ExitStack
from dataclasses import dataclass
from pathlib import Path
from types import SimpleNamespace
from typing import Protocol
from unittest.mock import patch

from dotenv import load_dotenv

from harness.runtime import ROOT, digest, require_pristine, write_json

sys.dont_write_bytecode = True
require_pristine()
sys.path.insert(0, str(ROOT / "inherited"))
load_dotenv(ROOT / ".env", override=False)
import database  # noqa: E402
import llm_utils  # noqa: E402
import notice_parser  # noqa: E402
import notice_validator  # noqa: E402

# Do not emit inherited exception messages or SDK HTTP headers to terminal/log files.
logging.getLogger().addHandler(logging.NullHandler())
logging.disable(logging.CRITICAL)


@dataclass(frozen=True)
class NoticeInput:
    case_id: str
    html_path: Path
    notice_id: int


class SystemUnderTest(Protocol):
    def process(
        self, notice: NoticeInput, history: sqlite3.Connection, destination: Path
    ) -> dict: ...


class ModelObserver:
    """Wrap only Messages.create; delegate every request to the genuine inherited client."""

    def __init__(self) -> None:
        self.calls: list[dict] = []
        self.factory = llm_utils.get_client

    def client(self):
        def create(**kwargs):
            from harness.live import (
                RequestBlocked,
                block_requests,
                consume_request,
                provider_error,
                request_failure,
            )

            record = {
                "provider": "anthropic",
                "configured_model": kwargs["model"],
                "request_sha256": hashlib.sha256(
                    json.dumps(kwargs, sort_keys=True).encode()
                ).hexdigest(),
                "request": kwargs,
                "success": False,
                "attempted": False,
                "stage": "extraction" if "tools" in kwargs else "semantic_helper",
            }
            self.calls.append(record)
            client = None
            try:
                consume_request()
                client = self.factory()
                record["attempted"] = True
                response = client.messages.create(**kwargs)
                record.update(
                    success=True,
                    request_id=getattr(response, "_request_id", None),
                    response=response.model_dump(mode="json"),
                )
                return response
            except Exception as exc:
                # Never persist exception text: provider errors may echo credential material.
                # Only the provider's structured message is kept, redacted (live.provider_error).
                record.update(
                    error_type=type(exc).__name__,
                    status_code=getattr(exc, "status_code", None),
                    provider_error=provider_error(exc),
                    classification="NOT_ATTEMPTED"
                    if isinstance(exc, RequestBlocked)
                    else request_failure(exc),
                    root_cause=request_failure(exc),
                )
                block_requests(request_failure(exc))
                raise
            finally:
                if client is not None:
                    client.close()

        return SimpleNamespace(messages=SimpleNamespace(create=create))


def state_snapshot(conn: sqlite3.Connection) -> dict:
    result = {}
    for table in ("notices", "notice_locations", "notice_restrictions"):
        cursor = conn.execute(f"SELECT * FROM {table} ORDER BY rowid")
        names = [col[0] for col in cursor.description]
        result[table] = [dict(zip(names, row)) for row in cursor.fetchall()]
    result["foreign_key_violations"] = conn.execute("PRAGMA foreign_key_check").fetchall()
    return result


class InheritedAdapter:
    def process(self, notice: NoticeInput, history: sqlite3.Connection, destination: Path) -> dict:
        observer = ModelObserver()
        result: dict = {
            "case_id": notice.case_id,
            "input": str(notice.html_path.relative_to(ROOT)),
            "input_sha256": digest(notice.html_path),
            "notice_id": notice.notice_id,
            "state_before": state_snapshot(history),
            "outcome": "UNKNOWN",
        }
        helper_results = []

        def observe_helper(name, function):
            def call(*args, **kwargs):
                value = function(*args, **kwargs)
                helper_results.append({"helper": name, "result": value})
                return value

            return call

        try:
            with ExitStack() as stack:
                stack.enter_context(patch.object(llm_utils, "get_client", observer.client))
                for name in ("llm_assess_curtailment_impact", "llm_is_supersede_material"):
                    stack.enter_context(
                        patch.object(
                            notice_validator,
                            name,
                            observe_helper(name, getattr(notice_validator, name)),
                        )
                    )
                row, locations, restrictions = notice_parser.parse_notice_html(
                    str(notice.html_path), {"notice_id": notice.notice_id}, db_conn=history
                )
            inserted = database.insert_notice(history, row, locations, restrictions)
            result.update(
                output={"notice": row, "locations": locations, "restrictions": restrictions},
                persistence_insert_succeeded=inserted,
            )
            flags = json.loads(row["validity_flags"])
            model_ok = bool(observer.calls) and all(c["success"] for c in observer.calls)
            model_ok = model_ok and "llm_extraction" in flags
            model_ok = model_ok and all(h["result"] is not None for h in helper_results)
            if not model_ok:
                result["outcome"] = next(
                    (c["root_cause"] for c in observer.calls if c.get("root_cause")),
                    "MODEL_FAILURE",
                )
            elif not inserted:
                result["outcome"] = "UNKNOWN"
            else:
                result["outcome"] = "SUCCESS"
        except (OSError, sqlite3.Error) as exc:
            result.update(outcome="ENVIRONMENT_FAILURE", error_type=type(exc).__name__)
        except Exception as exc:
            result.update(outcome="UNKNOWN", error_type=type(exc).__name__)
        result.update(
            model_calls=observer.calls,
            helper_results=helper_results,
            state_after=state_snapshot(history),
        )
        flags = json.loads(result.get("output", {}).get("notice", {}).get("validity_flags", "[]"))
        result["stages"] = {
            "extraction": {"scorable": "llm_extraction" in flags, "provenance_flags": flags},
            "classification": {"scorable": result["outcome"] == "SUCCESS"},
            "persistence": {
                "observable": "output" in result,
                "insert_succeeded": result.get("persistence_insert_succeeded"),
            },
        }
        write_json(destination, result)
        return result
