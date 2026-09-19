from __future__ import annotations

import os
from typing import Any, Literal

from mcp.server import MCPServer
from mcp.server.transport_security import TransportSecuritySettings

from .board import BoardStore
from .canonical import canonical_digest
from .checkpoint_contract import (
    WorkingCheckpointInput,
    WorkingCheckpointUpdate,
    merge_checkpoint_update,
    validate_full_checkpoint,
)
from .contracts import (
    AttentionResponse,
    BoardListResponse,
    BoardPostResponse,
    BoardSearchResponse,
    HostStatusResponse,
    TaskListResponse,
    TaskMutationResponse,
    TaskObserveResponse,
    TaskResumeResponse,
)
from .models import CheckpointInput, TaskState, TaskView
from .service import HostV2


def _request_id(prefix: str, value: dict[str, Any]) -> str:
    return f"{prefix}:{canonical_digest(value).removeprefix('sha256:')}"


def _task_summary(task: TaskView) -> dict[str, Any]:
    return {
        "task_id": task.task_id,
        "goal_id": task.goal_id,
        "revision": task.revision,
        "state": task.state.value,
        "checkpoint_digest": task.checkpoint_digest,
        "writer_label": task.writer_label,
    }


def build_server(dsn: str | None = None) -> MCPServer:
    effective_dsn = dsn or os.environ["ORDIVON_HOST_V2_DSN"]
    service = HostV2(effective_dsn)
    board = BoardStore(effective_dsn)
    mcp = MCPServer("ordivon-host-v2")

    @mcp.tool(name="host.status")
    def host_status(
        detail: Literal["summary", "integrity", "history"] = "summary",
        recentLimit: int = 5,
    ) -> HostStatusResponse:
        """Report PostgreSQL-native Host-v2 authority and bounded integrity status."""
        return service.status(detail=detail, recent_limit=recentLimit)

    @mcp.tool(name="attention.delta")
    def attention_delta(afterSequence: int, limit: int = 100) -> AttentionResponse:
        """Return Board-sequence change navigation into exact Host Task re-entry."""
        return service.attention_delta(after_sequence=afterSequence, limit=limit)

    @mcp.tool(name="board.list")
    def board_list(
        afterSequence: int | None = None,
        limit: int = 50,
        topic: str | None = None,
        clientMessageId: str | None = None,
        replyToClientMessageId: str | None = None,
        replyToAuthorLabel: str | None = None,
    ) -> BoardListResponse:
        """Read durable Host collaboration messages; not Task priority or authority."""
        return board.list(
            after_sequence=afterSequence,
            limit=limit,
            topic=topic,
            client_message_id=clientMessageId,
            reply_to_client_message_id=replyToClientMessageId,
            reply_to_author_label=replyToAuthorLabel,
        )

    @mcp.tool(name="board.search")
    def board_search(query: str, limit: int = 20) -> BoardSearchResponse:
        """Search Board navigation coordinates using PostgreSQL-native search."""
        return board.search(query=query, limit=limit)

    @mcp.tool(name="board.post")
    def board_post(
        clientMessageId: str,
        authorLabel: str,
        message: str,
        messageKind: Literal["note", "question", "proposal", "warning", "reply"] = "note",
        topic: str | None = None,
        replyToClientMessageId: str | None = None,
        taskId: str | None = None,
    ) -> BoardPostResponse:
        """Persist one replay-safe collaboration message with self-asserted author label."""
        return board.post(
            client_message_id=clientMessageId,
            author_label=authorLabel,
            message=message,
            message_kind=messageKind,
            topic=topic,
            reply_to_client_message_id=replyToClientMessageId,
            task_id=taskId,
        )


    @mcp.tool(name="task.observe")
    def task_observe(
        taskId: str,
        expectedRevision: int | None = None,
        eventLimit: int = 5,
    ) -> TaskObserveResponse:
        """Observe one revision-coherent Host task with recent semantic event metadata."""
        return service.observe(taskId, expectedRevision, eventLimit)

    @mcp.tool(name="task.list")
    def task_list(
        goalId: str | None = None,
        runtimeWorkspaceId: str | None = None,
        limit: int = 50,
        cursor: str | None = None,
        includeTerminal: bool = False,
    ) -> TaskListResponse:
        """List compact Host task inventory; use task.resume for exact checkpoint content."""
        tasks, has_more, next_cursor = service.list_task_summaries_page(
            include_terminal=includeTerminal,
            limit=limit,
            goal_id=goalId,
            runtime_workspace_id=runtimeWorkspaceId,
            cursor=cursor,
        )
        return {
            "schemaVersion": 4,
            "kind": "ordivon.host-task-list",
            "itemView": "basic",
            "tasks": tasks,
            "hasMore": has_more,
            "nextCursor": next_cursor,
            "truthBoundary": "compact continuity inventory only; use task.resume for exact checkpoint content; not work priority, owner standing, or domain truth",
        }

    @mcp.tool(name="task.resume")
    def task_resume(taskId: str, expectedRevision: int | None = None) -> TaskResumeResponse:
        """Recover one exact semantic checkpoint without querying foreign owners."""
        task = service.resume(taskId, expectedRevision)
        return {
            "schemaVersion": 4,
            "kind": "ordivon.host-external-continuity-resume",
            "task": _task_summary(task),
            "handoff": service._handoff(task),
            "checkpoint": task.checkpoint,
            "writerLabel": task.writer_label,
            "truthBoundary": "semantic working claim only; foreign Runtime/Git/domain references must be revalidated",
        }

    @mcp.tool(name="task.adopt")
    def task_adopt(
        taskId: str,
        goalId: str,
        initialCheckpoint: WorkingCheckpointInput,
        writerLabel: str | None = None,
    ) -> TaskMutationResponse:
        """Create or recover one external-continuity task and initial checkpoint."""
        initial = validate_full_checkpoint(taskId, initialCheckpoint)
        request = {
            "taskId": taskId,
            "goalId": goalId,
            "initialCheckpoint": initial,
            "writerLabel": writerLabel,
        }
        result = service.adopt(
            task_id=taskId,
            goal_id=goalId,
            checkpoint=CheckpointInput(payload=initial, writer_label=writerLabel),
            client_request_id=_request_id("task-adopt", request),
        )
        return {
            "schemaVersion": 4,
            "kind": "ordivon.host-external-continuity-adopt",
            "admission": result.admission.value,
            "task": _task_summary(result.task),
            "handoff": service._handoff(result.task),
            "checkpoint": result.task.checkpoint,
            "writerLabel": result.task.writer_label,
        }

    @mcp.tool(name="task.checkpoint")
    def task_checkpoint(
        taskId: str,
        expectedRevision: int,
        checkpoint: WorkingCheckpointUpdate,
        continuityDisposition: Literal["continue", "complete", "abandon"] = "continue",
        writerLabel: str | None = None,
    ) -> TaskMutationResponse:
        """Commit one exact-revision semantic checkpoint; disposition closes Host tracking only."""
        state = {
            "continue": TaskState.OPEN,
            "complete": TaskState.COMPLETED,
            "abandon": TaskState.ABANDONED,
        }[continuityDisposition]
        if checkpoint and not any(
            marker in checkpoint for marker in ("schemaVersion", "kind", "truthRole", "taskId")
        ):
            base = service.resume(taskId, expectedRevision).checkpoint
        else:
            base = {}
        normalized = merge_checkpoint_update(
            task_id=taskId,
            base=base,
            update=checkpoint,
            terminal=continuityDisposition != "continue",
        )
        request = {
            "taskId": taskId,
            "expectedRevision": expectedRevision,
            "checkpoint": normalized,
            "continuityDisposition": continuityDisposition,
            "writerLabel": writerLabel,
        }
        result = service.checkpoint(
            task_id=taskId,
            expected_revision=expectedRevision,
            checkpoint=CheckpointInput(payload=normalized, writer_label=writerLabel),
            client_request_id=_request_id("task-checkpoint", request),
            state=state,
        )
        return {
            "schemaVersion": 4,
            "kind": "ordivon.host-external-continuity-checkpoint",
            "admission": result.admission.value,
            "task": _task_summary(result.task),
            "handoff": service._handoff(result.task),
            "checkpoint": result.task.checkpoint,
            "writerLabel": result.task.writer_label,
        }

    return mcp


def main() -> None:
    transport = os.environ.get("ORDIVON_HOST_V2_TRANSPORT", "stdio")
    server = build_server()
    if transport == "stdio":
        server.run()
        return
    if transport != "streamable-http":
        raise RuntimeError("ORDIVON_HOST_V2_TRANSPORT must be stdio or streamable-http")
    host = os.environ.get("ORDIVON_HOST_V2_HOST", "127.0.0.1")
    if host not in {"127.0.0.1", "::1", "localhost"}:
        raise RuntimeError("Host v2 HTTP transport must remain loopback-bound")
    port = int(os.environ.get("ORDIVON_HOST_V2_PORT", "8898"))
    path = os.environ.get("ORDIVON_HOST_V2_PATH", "/mcp")
    if not path.startswith("/"):
        raise RuntimeError("ORDIVON_HOST_V2_PATH must start with /")

    allowed_hosts = ["127.0.0.1:*", "localhost:*", "[::1]:*"]
    allowed_origins = ["http://127.0.0.1:*", "http://localhost:*", "http://[::1]:*"]
    public_origin = os.environ.get("ORDIVON_HOST_V2_PUBLIC_ORIGIN")
    if public_origin:
        from urllib.parse import urlsplit

        parsed = urlsplit(public_origin)
        if (
            parsed.scheme != "https"
            or not parsed.hostname
            or parsed.username is not None
            or parsed.password is not None
            or parsed.path not in ("", "/")
            or parsed.query
            or parsed.fragment
        ):
            raise RuntimeError(
                "ORDIVON_HOST_V2_PUBLIC_ORIGIN must be one canonical HTTPS origin without path/query/fragment"
            )
        canonical_public_origin = f"https://{parsed.netloc}"
        allowed_hosts.append(parsed.netloc)
        allowed_origins.append(canonical_public_origin)

    server.run(
        transport="streamable-http",
        host=host,
        port=port,
        streamable_http_path=path,
        stateless_http=True,
        json_response=True,
        max_sessions=256,
        transport_security=TransportSecuritySettings(
            enable_dns_rebinding_protection=True,
            allowed_hosts=allowed_hosts,
            allowed_origins=allowed_origins,
        ),
    )
