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
        self.responses: dict[tuple[str, str], dict[str, Any] | list[dict[str, Any]]] = {}

    async def call_tool(
        self, owner_id: str, tool_name: str, arguments: dict[str, Any]
    ) -> dict[str, Any]:
        self.calls.append((owner_id, tool_name, arguments))
        key = (owner_id, tool_name)
        if key not in self.responses:
            raise AssertionError(f"unexpected owner call: {key}")
        response = self.responses[key]
        if isinstance(response, list):
            if not response:
                raise AssertionError(f"exhausted owner response sequence: {key}")
            return response.pop(0)
        return response


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


def test_gateway_server_registers_sdk_open_telemetry_middleware() -> None:
    from mcp.server._otel import OpenTelemetryMiddleware

    server = build_server(GatewayService(FakeOwnerCaller()))
    assert any(isinstance(item, OpenTelemetryMiddleware) for item in server.middleware)


def test_windows_context_is_dynamic_data_not_gateway_schema_enum() -> None:
    caller = FakeOwnerCaller()
    service = GatewayService(caller)

    async def scenario() -> None:
        async with Client(build_server(service), raise_exceptions=True) as client:
            tools = await client.list_tools()
            by_name = {tool.name: tool for tool in tools.tools}
            assert client.server_info is not None
            assert client.server_info.name == "ordivon-gateway"
            assert client.server_info.version == "0.4.0"
            assert set(by_name) == {
                "system.describe",
                "capability.describe",
                "execution.submit",
                "execution.resolve",
                "execution.get",
                "execution.cancel",
                "artifact.read",
                "continuity.get",
                "continuity.list",
                "continuity.find",
                "continuity.observe",
                "continuity.adopt",
                "continuity.checkpoint",
                "continuity.changes",
                "continuity.attention",
                "collaboration.list",
                "collaboration.search",
                "collaboration.post",
                "collaboration.publish",
            }
            assert tools.ttl_ms == 0
            assert tools.cache_scope == "private"
            assert "capability.list" not in by_name
            assert "capability.describe" in by_name
            submit = by_name["execution.submit"].input_schema
            assert "enum" not in submit["properties"]["context"]
            context_schema = submit["properties"]["context"]
            assert "string" in str(context_schema)
            assert "object" in str(context_schema)
            assert "enum" not in submit["properties"]["capability"]

    asyncio.run(scenario())


def test_system_description_uses_package_release_identity() -> None:
    service = GatewayService(FakeOwnerCaller())
    assert service.system_describe().gateway_version == "0.4.0"


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
            authority_references=[
                {
                    "namespace": "ordivon.harness",
                    "type": "dispatch_fence",
                    "id": "fence:1",
                    "digest": "sha256:fence",
                }
            ],
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
    assert execution["foreignReferences"] == [
        {
            "namespace": "ordivon.harness",
            "type": "dispatch_fence",
            "id": "fence:1",
            "digest": "sha256:fence",
        }
    ]


def test_execution_submit_windows_context_routes_legacy_or_structured_without_interpretation() -> None:
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

    caller.responses[("runtime.windows", "workspace.exec")]["jobId"] = "job-win-structured"
    structured_context = {"identity": "active_user", "privilege": "elevated"}
    asyncio.run(
        service.execution_submit(
            capability="execution.windows",
            request_id="req-structured",
            workspace_id="ws-win",
            executable=r"C:\Windows\System32\whoami.exe",
            args=[],
            context=structured_context,
        )
    )
    structured_execution = caller.calls[-1][2]["execution"]
    assert structured_execution["windowsContext"] == structured_context
    assert "windowsAuthority" not in structured_execution

    caller.responses[("runtime.windows", "workspace.exec")]["jobId"] = "job-win-3"
    asyncio.run(
        service.execution_submit(
            capability="execution.windows",
            request_id="req-env",
            workspace_id="ws-win",
            executable=r"C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe",
            args=["-NoProfile"],
            context="active_user",
            env={
                "ORDIVON_JEV_TYPESAFE_DPAPI_FILE": r"C:\Users\u\secret.dpapi",
                "PYTHONUTF8": "1",
            },
        )
    )
    assert caller.calls[-1][2]["execution"]["env"] == {
        "ORDIVON_JEV_TYPESAFE_DPAPI_FILE": r"C:\Users\u\secret.dpapi",
        "PYTHONUTF8": "1",
    }


def test_execution_resolve_projects_request_identity_without_redispatch() -> None:
    caller = FakeOwnerCaller()
    caller.responses[("runtime.linux", "job.list")] = {
        "jobs": [
            {
                "jobId": "job-resolved",
                "clientRequestId": "req-resolved",
            }
        ],
        "nextCursor": None,
    }
    service = GatewayService(caller)

    resolved = asyncio.run(
        service.execution_resolve(
            capability="execution.linux",
            request_id="req-resolved",
        )
    )
    assert resolved.resolution == "found"
    assert resolved.operation_ref == "ordivon-exec:v1:runtime.linux:job-resolved"
    assert resolved.native_id == "job-resolved"
    assert caller.calls == [
        (
            "runtime.linux",
            "job.list",
            {"limit": 2, "clientRequestId": "req-resolved"},
        )
    ]

    caller.responses[("runtime.linux", "job.list")] = {
        "jobs": [],
        "nextCursor": None,
    }
    absent = asyncio.run(
        service.execution_resolve(
            capability="execution.linux",
            request_id="req-absent",
        )
    )
    assert absent.resolution == "absent"
    assert absent.operation_ref is None

    caller.responses[("runtime.linux", "job.list")] = {
        "jobs": [
            {"jobId": "job-a", "clientRequestId": "req-many"},
            {"jobId": "job-b", "clientRequestId": "req-many"},
        ],
        "nextCursor": None,
    }
    ambiguous = asyncio.run(
        service.execution_resolve(
            capability="execution.linux",
            request_id="req-many",
        )
    )
    assert ambiguous.resolution == "ambiguous"
    assert ambiguous.operation_ref is None


def test_execution_get_and_cancel_route_by_operation_reference() -> None:
    caller = FakeOwnerCaller()
    caller.responses[("runtime.windows", "job.observe")] = {
        "jobId": "job-9",
        "status": "succeeded",
        "attemptState": "succeeded",
        "executionTerminal": True,
        "deliveryDisposition": "committed",
        "executionDisposition": "succeeded",
        "exitCode": 0,
        "recoveryRequired": False,
        "artifactsAvailable": True,
        "artifacts": [
            {
                "artifactId": "artifact-stdout",
                "kind": "stdout",
                "digest": "sha256:stdout",
            },
            {
                "artifactId": "artifact-terminal",
                "kind": "terminal_evidence",
                "digest": "sha256:terminal",
            },
        ],
    }
    caller.responses[("runtime.windows", "job.get")] = {
        "job": {"jobId": "job-9"},
        "artifacts": {
            "count": 2,
            "bytes": 123,
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

    observed = asyncio.run(service.execution_get(ref, wait_ms=1_234))
    assert observed.native_id == "job-9"
    assert observed.exit_code == 0
    assert observed.artifacts_available is True
    assert observed.artifact_count == 2
    assert observed.artifact_ids == ["artifact-stdout", "artifact-terminal"]
    assert observed.artifact_projection_complete is True
    assert observed.recovery_required is False
    assert caller.calls[-2] == (
        "runtime.windows",
        "job.observe",
        {
            "schemaVersion": 1,
            "jobId": "job-9",
            "waitMs": 1_234,
            "waitUntil": "change_or_terminal",
            "stdoutTailBytes": 0,
            "stderrTailBytes": 0,
        },
    )
    assert caller.calls[-1] == (
        "runtime.windows",
        "job.get",
        {"schemaVersion": 1, "jobId": "job-9", "eventLimit": 1},
    )

    cancelled = asyncio.run(service.execution_cancel(ref))
    assert cancelled.state == "cancelled"
    assert caller.calls[-1] == (
        "runtime.windows",
        "job.cancel",
        {"schemaVersion": 1, "jobId": "job-9"},
    )


def test_execution_get_reobserves_when_terminal_artifacts_lag_summary() -> None:
    caller = FakeOwnerCaller()
    caller.responses[("runtime.windows", "job.observe")] = [
        {
            "jobId": "job-lag",
            "status": "succeeded",
            "executionTerminal": True,
            "executionDisposition": "succeeded",
            "deliveryDisposition": "committed",
            "exitCode": 0,
            "recoveryRequired": False,
            "artifactsAvailable": True,
            "artifacts": [],
        },
        {
            "jobId": "job-lag",
            "status": "succeeded",
            "executionTerminal": True,
            "executionDisposition": "succeeded",
            "deliveryDisposition": "committed",
            "exitCode": 0,
            "recoveryRequired": False,
            "artifactsAvailable": True,
            "artifacts": [
                {"artifactId": "a.stdout", "kind": "stdout", "digest": "sha256:a"},
                {"artifactId": "a.result", "kind": "execution_result", "digest": "sha256:b"},
            ],
        },
    ]
    caller.responses[("runtime.windows", "job.get")] = {
        "job": {"jobId": "job-lag"},
        "artifacts": {"count": 2, "bytes": 10, "truncated": 0, "byKind": {}},
    }
    service = GatewayService(caller)
    observed = asyncio.run(service.execution_get("ordivon-exec:v1:runtime.windows:job-lag"))
    assert observed.artifact_count == 2
    assert observed.artifact_ids == ["a.stdout", "a.result"]
    assert observed.artifact_projection_complete is True
    assert [call[1] for call in caller.calls] == ["job.observe", "job.get", "job.observe"]


def test_execution_get_preserves_incomplete_artifact_projection_without_inventing_ids() -> None:
    caller = FakeOwnerCaller()
    empty = {
        "jobId": "job-lag",
        "status": "succeeded",
        "executionTerminal": True,
        "executionDisposition": "succeeded",
        "deliveryDisposition": "committed",
        "exitCode": 0,
        "recoveryRequired": False,
        "artifactsAvailable": True,
        "artifacts": [],
    }
    caller.responses[("runtime.windows", "job.observe")] = [dict(empty), dict(empty)]
    caller.responses[("runtime.windows", "job.get")] = {
        "job": {"jobId": "job-lag"},
        "artifacts": {"count": 2, "bytes": 10, "truncated": 0, "byKind": {}},
    }
    service = GatewayService(caller)
    observed = asyncio.run(service.execution_get("ordivon-exec:v1:runtime.windows:job-lag"))
    assert observed.artifacts_available is True
    assert observed.artifact_count == 2
    assert observed.artifact_ids == []
    assert observed.artifact_projection_complete is False


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
    assert page.sort_key == "created"

    found = asyncio.run(
        service.continuity_list(
            goal_id="goal:x",
            runtime_workspace_id="ws:x",
            limit=10,
            sort_key="updated",
        )
    )
    assert found.sort_key == "updated"
    assert caller.calls[-1] == (
        "host",
        "task.list",
        {
            "limit": 10,
            "includeTerminal": False,
            "goalId": "goal:x",
            "runtimeWorkspaceId": "ws:x",
            "sortKey": "updated",
        },
    )


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


def test_gateway_public_surface_covers_normal_host_continuity_without_admin_status() -> None:
    service = GatewayService(FakeOwnerCaller())

    async def scenario() -> None:
        async with Client(build_server(service), raise_exceptions=True) as client:
            listed = await client.list_tools()
            names = {tool.name for tool in listed.tools}
            assert {
                "continuity.get",
                "continuity.list",
                "continuity.find",
                "continuity.observe",
                "continuity.adopt",
                "continuity.checkpoint",
                "continuity.changes",
                "continuity.attention",
                "collaboration.list",
                "collaboration.search",
                "collaboration.post",
                "collaboration.publish",
            } <= names
            assert "host.status" not in names
            adopt = next(tool for tool in listed.tools if tool.name == "continuity.adopt")
            checkpoint_schema = adopt.input_schema["properties"]["checkpoint"]
            assert checkpoint_schema["type"] == "object"
            assert "workStanding" not in checkpoint_schema.get("properties", {})

    asyncio.run(scenario())


def test_continuity_mutations_and_observe_route_to_host_without_reowning_checkpoint_schema() -> (
    None
):
    caller = FakeOwnerCaller()
    caller.responses[("host", "task.adopt")] = {
        "admission": "committed",
        "task": {
            "task_id": "task:new",
            "goal_id": "goal:x",
            "revision": 1,
            "state": "open",
            "checkpoint_digest": "sha256:one",
            "someFutureHostField": "must not leak",
        },
        "checkpoint": {"schemaVersion": 9, "frontier": "opaque-to-gateway"},
        "writerLabel": "agent-a",
        "someFutureTopLevelField": True,
    }
    caller.responses[("host", "task.checkpoint")] = {
        "admission": "committed",
        "task": {
            "task_id": "task:new",
            "goal_id": "goal:x",
            "revision": 2,
            "state": "completed",
            "checkpoint_digest": "sha256:two",
        },
        "checkpoint": {"schemaVersion": 9, "frontier": "done"},
        "writerLabel": "agent-a",
    }
    caller.responses[("host", "task.observe")] = {
        "task": {
            "task_id": "task:new",
            "goal_id": "goal:x",
            "revision": 2,
            "state": "completed",
            "checkpoint_digest": "sha256:two",
            "checkpoint": {"schemaVersion": 9, "frontier": "done"},
            "writer_label": "agent-a",
        },
        "recentEvents": [
            {
                "revision": 2,
                "eventType": "checkpoint",
                "state": "completed",
                "createdAt": "2026-09-22T00:00:00+00:00",
            }
        ],
        "truthBoundary": "Host continuity mechanics only",
    }
    service = GatewayService(caller)

    adopted = asyncio.run(
        service.continuity_adopt(
            task_id="task:new",
            goal_id="goal:x",
            checkpoint={"schemaVersion": 9, "frontier": "opaque-to-gateway"},
            writer_label="agent-a",
        )
    )
    assert adopted.task_id == "task:new"
    assert adopted.admission == "committed"
    assert adopted.checkpoint == {"schemaVersion": 9, "frontier": "opaque-to-gateway"}
    assert not hasattr(adopted, "someFutureTopLevelField")
    assert caller.calls[-1] == (
        "host",
        "task.adopt",
        {
            "taskId": "task:new",
            "goalId": "goal:x",
            "initialCheckpoint": {"schemaVersion": 9, "frontier": "opaque-to-gateway"},
            "writerLabel": "agent-a",
        },
    )

    checked = asyncio.run(
        service.continuity_checkpoint(
            task_id="task:new",
            expected_revision=1,
            checkpoint={"schemaVersion": 9, "frontier": "done"},
            disposition="complete",
            writer_label="agent-a",
        )
    )
    assert checked.revision == 2
    assert checked.state == "completed"
    assert caller.calls[-1] == (
        "host",
        "task.checkpoint",
        {
            "taskId": "task:new",
            "expectedRevision": 1,
            "checkpoint": {"schemaVersion": 9, "frontier": "done"},
            "continuityDisposition": "complete",
            "writerLabel": "agent-a",
        },
    )

    observed = asyncio.run(
        service.continuity_observe("task:new", expected_revision=2, event_limit=7)
    )
    assert observed.task_id == "task:new"
    assert observed.checkpoint == {"schemaVersion": 9, "frontier": "done"}
    assert observed.recent_events[0].event_type == "checkpoint"
    assert caller.calls[-1] == (
        "host",
        "task.observe",
        {"taskId": "task:new", "expectedRevision": 2, "eventLimit": 7},
    )


def test_attention_and_collaboration_are_thin_host_projections() -> None:
    caller = FakeOwnerCaller()
    caller.responses[("host", "attention.delta")] = {
        "boardFence": {
            "requestedAfterSequence": 12,
            "lastSequence": 20,
            "nextAfterSequence": 20,
            "hasMore": False,
            "completeThroughNextAfterSequence": True,
        },
        "summary": {
            "newMessageCount": 1,
            "routedTaskCount": 1,
            "routedMessageCount": 1,
            "unroutedMessageCount": 0,
        },
        "routedTasks": [{"taskId": "task:x", "revision": 4}],
        "unroutedMessages": [],
        "truthBoundary": "Board-derived navigation only",
        "futureHostProjection": "must not leak",
    }
    caller.responses[("host", "board.post")] = {
        "admission": "committed",
        "message": {
            "sequence": 21,
            "clientMessageId": "msg:1",
            "authorLabel": "agent-a",
            "authorIdentityRole": "self-asserted-label",
            "messageKind": "note",
            "topic": "host-boundary",
            "message": "hello",
            "replyToClientMessageId": None,
            "taskId": "task:x",
            "recordedAtMs": 123,
            "messageDigest": "sha256:m",
            "truthRole": "coordination-message-not-domain-truth",
        },
        "truthBoundary": "message persistence only",
    }
    caller.responses[("host", "board.list")] = {
        "messages": [caller.responses[("host", "board.post")]["message"]],
        "lastSequence": 21,
        "nextAfterSequence": 21,
        "hasMore": False,
        "truthBoundary": "durable collaboration records only",
    }
    caller.responses[("host", "board.search")] = {
        "sourceSnapshotHighWater": 21,
        "liveHighWater": 21,
        "negativeResultAuthoritative": False,
        "requiresExactSourceReentry": True,
        "results": [{"sequence": 21, "clientMessageId": "msg:1"}],
    }
    service = GatewayService(caller)

    delta = asyncio.run(service.continuity_attention(after_sequence=12, limit=20))
    assert delta.kind == "ordivon.gateway-continuity-attention"
    assert delta.board_fence["lastSequence"] == 20
    assert not hasattr(delta, "futureHostProjection")
    assert caller.calls[-1] == ("host", "attention.delta", {"afterSequence": 12, "limit": 20})

    changes = asyncio.run(service.continuity_changes(after_sequence=12, limit=20))
    assert changes.kind == "ordivon.gateway-continuity-changes"
    assert changes.board_fence["lastSequence"] == 20
    assert caller.calls[-1] == ("host", "attention.delta", {"afterSequence": 12, "limit": 20})

    posted = asyncio.run(
        service.collaboration_post(
            client_message_id="msg:1",
            author_label="agent-a",
            message="hello",
            message_kind="note",
            topic="host-boundary",
            task_id="task:x",
        )
    )
    assert posted.message.client_message_id == "msg:1"
    assert posted.message.author_identity_role == "self-asserted-label"

    published = asyncio.run(
        service.collaboration_publish(
            client_message_id="msg:publish",
            author_label="agent-a",
            message="scoped hello",
            scope="continuity",
            continuity_id="task:x",
        )
    )
    assert published.message.task_id == "task:x"
    assert caller.calls[-1][0:2] == ("host", "board.post")
    assert caller.calls[-1][2]["taskId"] == "task:x"

    with pytest.raises(GatewayError, match="requires continuity_id"):
        asyncio.run(
            service.collaboration_publish(
                client_message_id="msg:bad",
                author_label="agent-a",
                message="bad",
                scope="continuity",
            )
        )

    with pytest.raises(GatewayError, match="cannot reply"):
        asyncio.run(
            service.collaboration_publish(
                client_message_id="msg:global-reply",
                author_label="agent-a",
                message="ambiguous",
                scope="global",
                reply_to_client_message_id="msg:1",
            )
        )

    page = asyncio.run(service.collaboration_list(after_sequence=20, limit=10))
    assert page.messages[0].task_id == "task:x"

    search = asyncio.run(service.collaboration_search("hello", limit=5))
    assert search.results[0].client_message_id == "msg:1"
    assert search.negative_result_authoritative is False
