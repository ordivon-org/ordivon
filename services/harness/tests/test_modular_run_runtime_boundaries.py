"""Contract regressions for split Harness read/policy/Runtime I/O LEGO.

No PostgreSQL or Runtime authority is faked into success by this suite;
real authority/recovery qualification lives in the existing integration tests.
"""
from __future__ import annotations

from collections import deque

import pytest

from ordivon_harness.ordivon.run_continuity import EventSourcedRunContinuity
from ordivon_harness.ordivon.run_source_inspection import RunSourceInspection
from ordivon_harness.ordivon import runtime_bridge
from ordivon_harness.ordivon import runtime_effect_policy, runtime_job_lookup
from ordivon_harness.runtime_port import HarnessRuntimeClientError


def test_run_source_read_only_inspection_uses_one_public_continuity_facade() -> None:
    assert issubclass(EventSourcedRunContinuity, RunSourceInspection)
    for name in (
        "_inspect_original_tool_sources",
        "inspect_unsettled_tool_sources",
        "inspect_issued_tool_sources",
        "inspect_finalization_source",
    ):
        assert getattr(EventSourcedRunContinuity, name) is getattr(RunSourceInspection, name)


def test_runtime_bridge_compatibility_has_one_effect_policy_and_one_job_reader() -> None:
    for name in (
        "_require_exact_owner_effect_handoff", "_runtime_error_value", "_runtime_delivery_state"
    ):
        assert getattr(runtime_bridge, name) is getattr(runtime_effect_policy, name)
    assert (
        runtime_bridge._find_runtime_jobs_by_client_request
        is runtime_job_lookup._find_runtime_jobs_by_client_request
    )


class ReadOnlyRuntime:
    def __init__(self, pages: list[dict[str, object]]):
        self.pages = deque(pages)
        self.calls: list[tuple[str, dict[str, object]]] = []

    def call_tool(self, tool: str, arguments: dict[str, object]) -> dict[str, object]:
        self.calls.append((tool, arguments))
        if tool != "task.list":
            raise AssertionError("recovery lookup attempted a physical effect")
        return self.pages.popleft()


def test_recovery_lookup_returns_only_matching_jobs_and_passes_exact_cursor() -> None:
    cursor = {"createdAtMs": 12, "jobId": "j1"}
    reader = ReadOnlyRuntime([
        {"jobs": [{"clientRequestId": "req", "workspaceId": "ws", "jobId": "j1"}],
         "nextCursor": cursor},
        {"jobs": [{"clientRequestId": "req", "workspaceId": "ws", "jobId": "j2"}],
         "nextCursor": None},
    ])
    result = runtime_job_lookup._find_runtime_jobs_by_client_request(reader, "req", "ws")
    assert [v["jobId"] for v in result] == ["j1", "j2"]
    assert [name for name, _ in reader.calls] == ["task.list", "task.list"]
    assert reader.calls[1][1]["cursor"] == cursor


@pytest.mark.parametrize(
    ("page", "failure"),
    [
        ({"jobs": [{"clientRequestId": "foreign", "workspaceId": "ws"}]}, "clientRequestId"),
        ({"jobs": [{"clientRequestId": "req", "workspaceId": "foreign"}]}, "Workspace"),
        ({"jobs": [], "nextCursor": {"createdAtMs": True, "jobId": "j"}}, "cursor"),
        ({"jobs": [], "nextCursor": {"createdAtMs": -1, "jobId": "j"}}, "cursor"),
        ({"jobs": [], "nextCursor": {"createdAtMs": 1, "jobId": "j", "extra": 1}}, "cursor"),
    ],
)
def test_recovery_lookup_rejects_untrusted_owner_projection(
    page: dict[str, object], failure: str
) -> None:
    reader = ReadOnlyRuntime([page])
    with pytest.raises(HarnessRuntimeClientError, match=failure):
        runtime_job_lookup._find_runtime_jobs_by_client_request(reader, "req", "ws")
    assert [tool for tool, _ in reader.calls] == ["task.list"]


def test_recovery_lookup_rejects_repeated_cursor_and_never_redispatches() -> None:
    cursor = {"createdAtMs": 12, "jobId": "j1"}
    reader = ReadOnlyRuntime([
        {"jobs": [], "nextCursor": cursor},
        {"jobs": [], "nextCursor": cursor},
    ])
    with pytest.raises(HarnessRuntimeClientError, match="repeated"):
        runtime_job_lookup._find_runtime_jobs_by_client_request(reader, "req", "ws")
    assert [tool for tool, _ in reader.calls] == ["task.list", "task.list"]


def test_effect_policy_keeps_reconciliation_distinct_from_domain_success() -> None:
    base = {
        "executionTerminal": True,
        "executionDisposition": "succeeded",
        "deliveryDisposition": "reconciliation_required",
        "recoveryRequired": True,
        "resultAvailable": True,
        "semanticCompletionEvaluated": False,
    }
    assert runtime_effect_policy._runtime_delivery_state(base) == "reconcile"
    with pytest.raises(HarnessRuntimeClientError, match="semantic completion"):
        runtime_effect_policy._runtime_delivery_state(
            {**base, "semanticCompletionEvaluated": True}
        )
    assert runtime_effect_policy._runtime_delivery_state(
        {**base, "deliveryDisposition": "committed", "recoveryRequired": False}
    ) == "terminal"


@pytest.mark.parametrize(
    ("usage", "expected"),
    [
        ({}, None),
        ({"total_tokens": 8}, 8),
        ({"total_tokens": 1, "input_tokens": 4, "output_tokens": 5}, 9),
        ({"totalTokens": True, "promptTokens": 7, "completionTokens": 3}, 10),
        ({"totalTokens": -2}, None),
        ({"input_tokens": 4}, None),
    ],
)
def test_provider_token_budget_projection_stays_in_run_contract(
    usage: dict[str, object], expected: int | None
) -> None:
    from ordivon_harness.ordivon import loop, run_contract

    assert loop._usage_total_tokens is run_contract._usage_total_tokens
    assert run_contract._usage_total_tokens(usage) == expected
