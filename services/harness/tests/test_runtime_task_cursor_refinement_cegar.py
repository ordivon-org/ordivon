"""CEGAR: RuntimeJobListCursor must refine the exact Rust wire representation.

No live Runtime is called: the fake produces the same decoded JSON page that
the Harness recovery boundary consumes after transport response loss.
"""

from __future__ import annotations

from typing import Any

import pytest

from ordivon_harness.ordivon.sqlite_runtime_bridge import (
    _find_runtime_jobs_by_client_request,
)
from ordivon_harness.runtime_port import HarnessRuntimeClientError


class TaskPages:
    def __init__(self, first_cursor: dict[str, Any]) -> None:
        self.calls: list[dict[str, Any]] = []
        self.first_cursor = first_cursor

    def call_tool(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        assert name == "task.list"
        self.calls.append(arguments)
        if len(self.calls) == 1:
            return {"schemaVersion": 1, "jobs": [], "nextCursor": self.first_cursor}
        return {"schemaVersion": 1, "jobs": [], "nextCursor": None}


@pytest.mark.parametrize(
    "bad_cursor",
    [
        {"createdAtMs": True, "jobId": "job-test"},
        {"createdAtMs": "100", "jobId": "job-test"},
        {"createdAtMs": -1, "jobId": "job-test"},
        {"createdAtMs": 2**64, "jobId": "job-test"},
        {"createdAtMs": 1, "jobId": 4},
        {"createdAtMs": 1, "jobId": ""},
        {"createdAtMs": 1},
        {"createdAtMs": 1, "jobId": "job-test", "extra": 0},
    ],
)
def test_recovery_refuses_nonruntime_cursor_before_reattachment(
    bad_cursor: dict[str, Any],
) -> None:
    runtime = TaskPages(bad_cursor)
    with pytest.raises(HarnessRuntimeClientError, match="cursor"):
        _find_runtime_jobs_by_client_request(runtime, "harness-r10-client-lookup")
    assert len(runtime.calls) == 1, (
        "forged Runtime cursor must not be replayed to another physical call"
    )


def test_exact_runtime_cursor_allows_bounded_reconciliation() -> None:
    runtime = TaskPages({"createdAtMs": 1, "jobId": "job-test"})
    assert _find_runtime_jobs_by_client_request(runtime, "harness-r10-client-lookup") == []
    assert len(runtime.calls) == 2
    assert runtime.calls[1]["cursor"] == {"createdAtMs": 1, "jobId": "job-test"}
