from __future__ import annotations

import os
from typing import Any

from mcp.server import MCPServer

from .models import CheckpointInput, TaskState
from .service import HostV2


def build_server(dsn: str | None = None) -> MCPServer:
    service = HostV2(dsn or os.environ["ORDIVON_HOST_V2_DSN"])
    mcp = MCPServer("ordivon-host-v2")

    @mcp.tool(name="host.status")
    def host_status() -> dict[str, Any]:
        """Report Host-v2-owned authority status only."""
        return service.status().model_dump(mode="json")

    @mcp.tool(name="task.list")
    def task_list(include_terminal: bool = False, limit: int = 100) -> list[dict[str, Any]]:
        """List durable Host-v2 task continuity; does not infer external owner truth."""
        return [
            item.model_dump(mode="json")
            for item in service.list_tasks(include_terminal=include_terminal, limit=limit)
        ]

    @mcp.tool(name="task.adopt")
    def task_adopt(
        task_id: str,
        checkpoint: dict[str, Any],
        client_request_id: str,
        writer_label: str | None = None,
    ) -> dict[str, Any]:
        """Create or exactly replay one task with an immediately recoverable checkpoint."""
        return service.adopt(
            task_id=task_id,
            checkpoint=CheckpointInput(payload=checkpoint, writer_label=writer_label),
            client_request_id=client_request_id,
        ).model_dump(mode="json")

    @mcp.tool(name="task.checkpoint")
    def task_checkpoint(
        task_id: str,
        expected_revision: int,
        checkpoint: dict[str, Any],
        client_request_id: str,
        state: TaskState = TaskState.OPEN,
        writer_label: str | None = None,
    ) -> dict[str, Any]:
        """Revision-fenced semantic checkpoint; terminality is Host tracking only."""
        return service.checkpoint(
            task_id=task_id,
            expected_revision=expected_revision,
            checkpoint=CheckpointInput(payload=checkpoint, writer_label=writer_label),
            client_request_id=client_request_id,
            state=state,
        ).model_dump(mode="json")

    @mcp.tool(name="task.resume")
    def task_resume(task_id: str, expected_revision: int | None = None) -> dict[str, Any]:
        """Read one revision-coherent semantic checkpoint without querying external owners."""
        return service.resume(task_id, expected_revision).model_dump(mode="json")

    return mcp


def main() -> None:
    build_server().run()
