from __future__ import annotations

import os
from typing import Any, Literal

from mcp.server import MCPServer

from .board import BoardStore
from .canonical import canonical_digest
from .models import CheckpointInput, TaskState
from .news import NewsStore
from .service import HostV2


def _request_id(prefix: str, value: dict[str, Any]) -> str:
    return f"{prefix}:{canonical_digest(value).removeprefix('sha256:')}"


def build_server(dsn: str | None = None) -> MCPServer:
    effective_dsn = dsn or os.environ["ORDIVON_HOST_V2_DSN"]
    service = HostV2(effective_dsn)
    board = BoardStore(effective_dsn)
    news = NewsStore(effective_dsn)
    mcp = MCPServer("ordivon-host-v2")

    @mcp.tool(name="host.status")
    def host_status() -> dict[str, Any]:
        """Report Host-v2-owned PostgreSQL authority status only."""
        return service.status().model_dump(mode="json")

    @mcp.tool(name="attention.delta")
    def attention_delta(afterSequence: int, limit: int = 100) -> dict[str, Any]:
        """Return durable Host change navigation after one global activity sequence."""
        return service.attention_delta(after_sequence=afterSequence, limit=limit)

    @mcp.tool(name="board.list")
    def board_list(
        afterSequence: int | None = None,
        limit: int = 50,
        topic: str | None = None,
        clientMessageId: str | None = None,
        replyToClientMessageId: str | None = None,
        replyToAuthorLabel: str | None = None,
    ) -> dict[str, Any]:
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
    def board_search(query: str, limit: int = 20) -> dict[str, Any]:
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
    ) -> dict[str, Any]:
        """Persist one replay-safe collaboration message with self-asserted author label."""
        return board.post(
            client_message_id=clientMessageId,
            author_label=authorLabel,
            message=message,
            message_kind=messageKind,
            topic=topic,
            reply_to_client_message_id=replyToClientMessageId,
        )

    @mcp.tool(name="news.list")
    def news_list(
        limit: int = 30,
        cursor: str | None = None,
        fromDate: str | None = None,
        toDate: str | None = None,
    ) -> dict[str, Any]:
        """List durable external-news publication revisions."""
        return news.list(limit=limit, cursor=cursor, from_date=fromDate, to_date=toDate)

    @mcp.tool(name="news.read")
    def news_read(
        editionId: str | None = None,
        revision: int | None = None,
        sections: list[str] | None = None,
        categories: list[str] | None = None,
        threadKeys: list[str] | None = None,
        includeRenderedBrief: bool = False,
    ) -> dict[str, Any]:
        """Read the latest or one exact external-news edition revision."""
        return news.read(
            edition_id=editionId,
            revision=revision,
            sections=sections,
            categories=categories,
            thread_keys=threadKeys,
            include_rendered_brief=includeRenderedBrief,
        )

    @mcp.tool(name="news.publish")
    def news_publish(
        clientPublishId: str,
        editionId: str,
        expectedRevision: int,
        edition: dict[str, Any],
    ) -> dict[str, Any]:
        """Publish one revision-fenced external-news edition."""
        return news.publish(
            client_publish_id=clientPublishId,
            edition_id=editionId,
            expected_revision=expectedRevision,
            edition=edition,
        )

    @mcp.tool(name="task.observe")
    def task_observe(
        taskId: str,
        expectedRevision: int | None = None,
        eventLimit: int = 5,
    ) -> dict[str, Any]:
        """Observe one revision-coherent Host task with recent semantic event metadata."""
        return service.observe(taskId, expectedRevision, eventLimit)

    @mcp.tool(name="task.list")
    def task_list(
        goalId: str | None = None,
        runtimeWorkspaceId: str | None = None,
        limit: int = 50,
        cursor: str | None = None,
        includeTerminal: bool = False,
    ) -> dict[str, Any]:
        """List Host semantic-continuity tasks; not a priority or ownership surface."""
        tasks, has_more, next_cursor = service.list_tasks_page(
            include_terminal=includeTerminal,
            limit=limit,
            goal_id=goalId,
            runtime_workspace_id=runtimeWorkspaceId,
            cursor=cursor,
        )
        return {
            "schemaVersion": 3,
            "kind": "ordivon.host-task-list",
            "tasks": [item.model_dump(mode="json") for item in tasks],
            "hasMore": has_more,
            "nextCursor": next_cursor,
            "truthBoundary": "continuity inventory only; not work priority, owner standing, or domain truth",
        }

    @mcp.tool(name="task.resume")
    def task_resume(taskId: str, expectedRevision: int | None = None) -> dict[str, Any]:
        """Recover one exact semantic checkpoint without querying foreign owners."""
        task = service.resume(taskId, expectedRevision)
        return {
            "schemaVersion": 3,
            "kind": "ordivon.host-external-continuity-resume",
            "task": task.model_dump(mode="json"),
            "handoff": service._handoff(task),
            "checkpoint": task.checkpoint,
            "writerLabel": task.writer_label,
            "truthBoundary": "semantic working claim only; foreign Runtime/Git/domain references must be revalidated",
        }

    @mcp.tool(name="task.adopt")
    def task_adopt(
        taskId: str,
        goalId: str,
        initialCheckpoint: dict[str, Any],
        writerLabel: str | None = None,
    ) -> dict[str, Any]:
        """Create or recover one external-continuity task and initial checkpoint."""
        request = {
            "taskId": taskId,
            "goalId": goalId,
            "initialCheckpoint": initialCheckpoint,
            "writerLabel": writerLabel,
        }
        result = service.adopt(
            task_id=taskId,
            goal_id=goalId,
            checkpoint=CheckpointInput(payload=initialCheckpoint, writer_label=writerLabel),
            client_request_id=_request_id("task-adopt", request),
        )
        return {
            "schemaVersion": 3,
            "kind": "ordivon.host-external-continuity-adopt",
            "admission": result.admission.value,
            "task": result.task.model_dump(mode="json"),
            "handoff": service._handoff(result.task),
            "checkpoint": result.task.checkpoint,
            "writerLabel": result.task.writer_label,
        }

    @mcp.tool(name="task.checkpoint")
    def task_checkpoint(
        taskId: str,
        expectedRevision: int,
        checkpoint: dict[str, Any],
        continuityDisposition: Literal["continue", "complete", "abandon"] = "continue",
        writerLabel: str | None = None,
    ) -> dict[str, Any]:
        """Commit one exact-revision semantic checkpoint; disposition closes Host tracking only."""
        state = {
            "continue": TaskState.OPEN,
            "complete": TaskState.COMPLETED,
            "abandon": TaskState.ABANDONED,
        }[continuityDisposition]
        request = {
            "taskId": taskId,
            "expectedRevision": expectedRevision,
            "checkpoint": checkpoint,
            "continuityDisposition": continuityDisposition,
            "writerLabel": writerLabel,
        }
        result = service.checkpoint(
            task_id=taskId,
            expected_revision=expectedRevision,
            checkpoint=CheckpointInput(payload=checkpoint, writer_label=writerLabel),
            client_request_id=_request_id("task-checkpoint", request),
            state=state,
        )
        return {
            "schemaVersion": 3,
            "kind": "ordivon.host-external-continuity-checkpoint",
            "admission": result.admission.value,
            "task": result.task.model_dump(mode="json"),
            "handoff": service._handoff(result.task),
            "checkpoint": result.task.checkpoint,
            "writerLabel": result.task.writer_label,
        }

    return mcp


def main() -> None:
    build_server().run()
