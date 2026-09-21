from __future__ import annotations

import asyncio
from typing import Any

import pytest
from mcp import Client
from mcp.types import Tool

from ordivon_gateway.mcp_server import build_server
from ordivon_gateway.service import GatewayError, GatewayService


class FakeOwnerCaller:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str, dict[str, Any]]] = []
        self.responses: dict[tuple[str, str], dict[str, Any]] = {}

    async def call_tool(
        self, owner_id: str, tool_name: str, arguments: dict[str, Any]
    ) -> dict[str, Any]:
        self.calls.append((owner_id, tool_name, arguments))
        key = (owner_id, tool_name)
        if key not in self.responses:
            raise AssertionError(f"unexpected owner call: {key}")
        return self.responses[key]


def test_current_mcp_sdk_accepts_runtime_tool_outcome_union_schema() -> None:
    schema = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$defs": {
            "Success": {
                "type": "object",
                "properties": {"jobId": {"type": "string"}},
                "required": ["jobId"],
            },
            "Error": {
                "type": "object",
                "properties": {"error": {"type": "object"}},
                "required": ["error"],
            },
        },
        "oneOf": [{"$ref": "#/$defs/Success"}, {"$ref": "#/$defs/Error"}],
    }
    tool = Tool.model_validate(
        {
            "name": "runtime.synthetic",
            "description": "Runtime ToolOutcome compatibility fixture",
            "inputSchema": {"type": "object"},
            "outputSchema": schema,
        }
    )
    assert tool.output_schema is not None
    assert tool.output_schema.get("type") is None
    assert len(tool.output_schema["oneOf"]) == 2


def test_windows_context_is_dynamic_data_not_gateway_schema_enum() -> None:
    caller = FakeOwnerCaller()
    service = GatewayService(caller)

    async def scenario() -> None:
        async with Client(build_server(service), raise_exceptions=True) as client:
            tools = await client.list_tools()
            by_name = {tool.name: tool for tool in tools.tools}
            assert "capability.list" not in by_name
            assert "capability.describe" in by_name
            submit = by_name["execution.submit"].input_schema
            assert "enum" not in submit["properties"]["context"]
            assert "enum" not in submit["properties"]["capability"]

    asyncio.run(scenario())


def test_execution_submit_lowers_linux_without_leaking_owner_schema() -> None:
    caller = FakeOwnerCaller()
    caller.responses[("runtime.linux", "workspace.exec")] = {
        "jobId": "job-linux-1",
        "status": "working",
        "executionTerminal": False,
        "deliveryDisposition": "in_progress",
        "someFutureRuntimeField": {"must": "not leak"},
    }
    service = GatewayService(caller)

    receipt = asyncio.run(
        service.execution_submit(
            capability="execution.linux",
            request_id="req-1",
            workspace_id="ws-1",
            executable="/usr/bin/python3",
            args=["-V"],
            cwd_relative=".",
            context="contained_local",
            timeout_ms=30_000,
        )
    )

    assert receipt.operation_ref == "ordivon-exec:v1:runtime.linux:job-linux-1"
    assert receipt.native_id == "job-linux-1"
    assert receipt.state == "working"
    assert receipt.terminal is False
    assert not hasattr(receipt, "someFutureRuntimeField")
    owner, tool, payload = caller.calls[-1]
    assert (owner, tool) == ("runtime.linux", "workspace.exec")
    assert payload["clientRequestId"] == "req-1"
    execution = payload["execution"]
    assert execution["executionTarget"] == "local_linux"
    assert execution["executionProfile"] == "contained_local"
    assert "windowsAuthority" not in execution


def test_execution_submit_windows_context_passes_through_as_string() -> None:
    caller = FakeOwnerCaller()
    caller.responses[("runtime.windows", "workspace.exec")] = {
        "jobId": "job-win-1",
        "status": "accepted",
        "executionTerminal": False,
        "deliveryDisposition": "committed",
    }
    service = GatewayService(caller)

    asyncio.run(
        service.execution_submit(
            capability="execution.windows",
            request_id="req-win",
            workspace_id="ws-win",
            executable=r"C:\Windows\System32\whoami.exe",
            args=[],
            context="active_user",
        )
    )
    _, _, payload = caller.calls[-1]
    assert payload["execution"]["executionTarget"] == "windows_native"
    assert payload["execution"]["executionProfile"] == "trusted_local"
    assert payload["execution"]["windowsAuthority"] == "active_user"

    caller.responses[("runtime.windows", "workspace.exec")]["jobId"] = "job-win-2"
    asyncio.run(
        service.execution_submit(
            capability="execution.windows",
            request_id="req-future",
            workspace_id="ws-win",
            executable=r"C:\Windows\System32\whoami.exe",
            args=[],
            context="future_provider_context",
        )
    )
    assert caller.calls[-1][2]["execution"]["windowsAuthority"] == "future_provider_context"


def test_execution_get_and_cancel_route_by_operation_reference() -> None:
    caller = FakeOwnerCaller()
    caller.responses[("runtime.windows", "job.get")] = {
        "schemaVersion": 2,
        "job": {
            "jobId": "job-9",
            "desiredState": "run",
            "resolution": "succeeded",
            "mechanicallyConverged": True,
            "semanticCompletionEvaluated": False,
        },
        "attempts": [
            {
                "attemptId": "attempt-1",
                "attemptNumber": 1,
                "state": "succeeded",
                "exitCode": 0,
                "conditions": [
                    {
                        "conditionType": "recovery_required",
                        "status": "false",
                    }
                ],
            }
        ],
        "artifacts": {
            "count": 2,
            "bytes": 42,
            "truncated": 0,
            "byKind": {"stdout": 1, "terminal_evidence": 1},
        },
    }
    caller.responses[("runtime.windows", "job.cancel")] = {
        "jobId": "job-9",
        "status": "cancelled",
        "executionTerminal": True,
        "deliveryDisposition": "committed",
    }
    service = GatewayService(caller)
    ref = "ordivon-exec:v1:runtime.windows:job-9"

    observed = asyncio.run(service.execution_get(ref))
    assert observed.native_id == "job-9"
    assert observed.exit_code == 0
    assert observed.artifact_count == 2
    assert observed.artifact_ids == []
    assert observed.recovery_required is False
    assert caller.calls[-1] == (
        "runtime.windows",
        "job.get",
        {"schemaVersion": 1, "jobId": "job-9", "eventLimit": 10},
    )

    cancelled = asyncio.run(service.execution_cancel(ref))
    assert cancelled.state == "cancelled"
    assert caller.calls[-1] == (
        "runtime.windows",
        "job.cancel",
        {"schemaVersion": 1, "jobId": "job-9"},
    )


def test_artifact_read_is_bound_to_execution_owner() -> None:
    caller = FakeOwnerCaller()
    caller.responses[("runtime.linux", "artifact.read")] = {
        "jobId": "job-1",
        "artifactId": "artifact-1",
        "offset": 0,
        "nextOffset": 3,
        "eof": True,
        "digest": "sha256:abc",
        "content": "abc",
    }
    service = GatewayService(caller)
    chunk = asyncio.run(
        service.artifact_read(
            "ordivon-exec:v1:runtime.linux:job-1",
            "artifact-1",
            offset=0,
            max_bytes=1024,
        )
    )
    assert chunk.content == "abc"
    assert chunk.digest == "sha256:abc"
    assert caller.calls[-1][0:2] == ("runtime.linux", "artifact.read")


def test_continuity_reads_route_to_host_and_normalize_projection() -> None:
    caller = FakeOwnerCaller()
    caller.responses[("host", "task.resume")] = {
        "task": {
            "task_id": "task:x",
            "goal_id": "goal:x",
            "revision": 3,
            "state": "open",
            "checkpoint_digest": "sha256:c",
        },
        "checkpoint": {"frontier": "continue"},
        "truthBoundary": "semantic working claim only",
    }
    caller.responses[("host", "task.list")] = {
        "tasks": [
            {
                "task_id": "task:x",
                "goal_id": "goal:x",
                "revision": 3,
                "state": "open",
                "checkpoint_digest": "sha256:c",
            }
        ],
        "hasMore": False,
        "nextCursor": None,
    }
    service = GatewayService(caller)

    one = asyncio.run(service.continuity_get("task:x"))
    assert one.task_id == "task:x"
    assert one.checkpoint == {"frontier": "continue"}

    page = asyncio.run(service.continuity_list(goal_id="goal:x", limit=10))
    assert page.items[0].task_id == "task:x"
    assert page.has_more is False


def test_unknown_capability_fails_closed_before_owner_call() -> None:
    caller = FakeOwnerCaller()
    service = GatewayService(caller)

    with pytest.raises(GatewayError, match="unknown capability"):
        asyncio.run(
            service.execution_submit(
                capability="execution.unknown",
                request_id="req",
                workspace_id="ws",
                executable="/bin/true",
                args=[],
            )
        )
    assert caller.calls == []
