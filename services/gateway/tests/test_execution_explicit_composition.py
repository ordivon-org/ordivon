"""Gateway execution composition must not rely on a multiple-inheritance shell."""

from __future__ import annotations

import asyncio
from typing import Any

from ordivon_gateway.capabilities.execution.commands import ExecutionCommandMethods
from ordivon_gateway.capabilities.execution.observations import ExecutionObservationMethods
from ordivon_gateway.service import GatewayService


class RecordedOwner:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str, dict[str, Any]]] = []

    async def call_tool(
        self, owner_id: str, tool_name: str, arguments: dict[str, Any]
    ) -> dict[str, Any]:
        self.calls.append((owner_id, tool_name, arguments))
        assert owner_id == "runtime.linux"
        job_id = "job-composed"
        if tool_name == "workspace.exec":
            return {"jobId": job_id, "status": "queued", "executionTerminal": False}
        if tool_name == "job.list":
            return {
                "jobs": [{"jobId": job_id, "clientRequestId": "rid", "workspaceId": "ws"}],
                "nextCursor": None,
            }
        if tool_name == "job.observe":
            return {
                "jobId": job_id,
                "status": "succeeded",
                "executionTerminal": True,
                "artifactsAvailable": True,
                "artifacts": [{"artifactId": "attempt-composed.stdout"}],
                "exitCode": 0,
            }
        if tool_name == "job.get":
            return {
                "job": {"jobId": job_id},
                "artifacts": {"count": 1},
            }
        if tool_name == "artifact.read":
            return {
                "jobId": job_id,
                "artifactId": "attempt-composed.stdout",
                "offset": 0,
                "nextOffset": 2,
                "eof": True,
                "digest": "sha256:test",
                "content": "OK",
            }
        if tool_name == "job.cancel":
            return {"jobId": job_id, "status": "succeeded", "executionTerminal": True}
        raise AssertionError(f"unexpected Owner tool: {tool_name}")


def test_execution_parts_have_explicit_owner_dependencies_not_mixin_state() -> None:
    owner = RecordedOwner()
    service = GatewayService(owner)
    commands = service._execution_commands
    observations = service._execution_observations

    assert type(commands) is ExecutionCommandMethods
    assert type(observations) is ExecutionObservationMethods
    assert commands._caller is observations._caller is owner
    assert commands._routes is observations._routes is service._routes
    assert not hasattr(service, "_execution")
    assert not issubclass(ExecutionCommandMethods, ExecutionObservationMethods)
    assert not issubclass(ExecutionObservationMethods, ExecutionCommandMethods)


def test_execution_command_and_observation_composition_keeps_one_owner_job() -> None:
    owner = RecordedOwner()
    service = GatewayService(owner)

    async def consume() -> None:
        receipt = await service.execution_submit(
            capability="execution.linux",
            request_id="rid",
            workspace_id="ws",
            executable="/usr/bin/printf",
            args=["OK"],
        )
        assert receipt.native_id == "job-composed"
        resolved = await service.execution_resolve(capability="execution.linux", request_id="rid")
        assert resolved.operation_ref == receipt.operation_ref
        observed = await service.execution_get(receipt.operation_ref)
        assert observed.terminal and observed.exit_code == 0
        assert observed.artifact_projection_complete is True
        content = await service.artifact_read(receipt.operation_ref, "attempt-composed.stdout")
        assert content.content == "OK" and content.eof
        cancelled = await service.execution_cancel(receipt.operation_ref)
        assert cancelled.terminal
        assert cancelled.native_id == receipt.native_id

    asyncio.run(consume())
    assert [call[1] for call in owner.calls] == [
        "workspace.exec",
        "job.list",
        "job.observe",
        "job.get",
        "artifact.read",
        "job.cancel",
    ]
