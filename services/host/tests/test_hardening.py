from __future__ import annotations

import hashlib
import os
from uuid import uuid4

import pytest

from ordivon_host_v2 import CheckpointInput, HostV2
from ordivon_host_v2.board import (
    _TASK_ROUTE_ANCHOR_AUTHOR_LABEL,
    _TASK_ROUTE_ANCHOR_ID_PREFIX,
    _TASK_ROUTE_ANCHOR_MESSAGE_PREFIX,
    _TASK_ROUTE_ANCHOR_MESSAGE_SUFFIX,
    _TASK_ROUTE_ANCHOR_TOPIC,
    BoardStore,
)

DSN = os.environ.get("ORDIVON_HOST_V2_TEST_DSN")
pytestmark = pytest.mark.skipif(not DSN, reason="ORDIVON_HOST_V2_TEST_DSN not set")


def stores() -> tuple[HostV2, BoardStore]:
    assert DSN is not None
    host = HostV2(DSN)
    host.initialize()
    return host, BoardStore(DSN)


def test_board_filtered_incremental_exhaustion_advances_fence() -> None:
    _, board = stores()
    marker = uuid4().hex
    first = board.post(
        client_message_id=f"msg:{marker}:1", author_label="agent:a", message="a", topic="a"
    )
    board.post(client_message_id=f"msg:{marker}:2", author_label="agent:b", message="b", topic="b")
    third = board.post(
        client_message_id=f"msg:{marker}:3", author_label="agent:b", message="c", topic="b"
    )
    after = int(first["message"]["sequence"])
    high = int(third["message"]["sequence"])
    page = board.list(after_sequence=after, limit=10, topic="a")
    assert page["messages"] == []
    assert page["hasMore"] is False
    assert page["nextAfterSequence"] == high


def test_board_list_rejects_invalid_query_coordinates() -> None:
    _, board = stores()
    with pytest.raises(ValueError, match="afterSequence"):
        board.list(after_sequence=-1)
    with pytest.raises(ValueError, match="topic"):
        board.list(topic=" bad ")
    with pytest.raises(ValueError, match="clientMessageId"):
        board.list(client_message_id=" bad ")
    with pytest.raises(ValueError, match="replyToAuthorLabel"):
        board.list(reply_to_author_label=" bad ")


def test_reserved_task_route_anchor_rejects_squatting_and_attention_routes_reply() -> None:
    host, board = stores()
    task_id = f"task:v2:attention:{uuid4().hex}"
    host.adopt(
        task_id=task_id,
        checkpoint=CheckpointInput(
            payload={"frontier": "resume me", "runtime": {"workspaceId": "ws:test"}}
        ),
        client_request_id=f"adopt:{task_id}",
    )
    suffix = hashlib.sha256(task_id.encode("utf-8")).hexdigest()
    anchor_id = _TASK_ROUTE_ANCHOR_ID_PREFIX + suffix
    anchor_message = _TASK_ROUTE_ANCHOR_MESSAGE_PREFIX + task_id + _TASK_ROUTE_ANCHOR_MESSAGE_SUFFIX

    with pytest.raises(ValueError, match="reserved task-route-anchor-v1"):
        board.post(
            client_message_id=anchor_id,
            author_label="squatter",
            message=anchor_message,
            topic=_TASK_ROUTE_ANCHOR_TOPIC,
        )

    anchor = board.post(
        client_message_id=anchor_id,
        author_label=_TASK_ROUTE_ANCHOR_AUTHOR_LABEL,
        message=anchor_message,
        message_kind="note",
        topic=_TASK_ROUTE_ANCHOR_TOPIC,
    )
    assert anchor["admission"] == "existing"
    board.post(
        client_message_id=f"reply:{uuid4().hex}",
        author_label="agent:peer",
        message="continue from exact Host revision",
        message_kind="reply",
        topic="coordination",
        reply_to_client_message_id=anchor_id,
    )
    delta = host.attention_delta(
        after_sequence=max(0, int(anchor["message"]["sequence"]) - 1), limit=10
    )
    assert delta["kind"] == "ordivon.host-current-attention-delta"
    assert delta["summary"]["infrastructureMessageCount"] == 1
    assert delta["summary"]["newMessageCount"] == 1
    assert delta["summary"]["routedTaskCount"] == 1
    routed = delta["routedTasks"][0]
    assert routed["taskId"] == task_id
    assert routed["taskRevision"] == 1
    assert routed["reentry"] == {
        "requiredBeforeActing": True,
        "operation": "task.resume",
        "taskId": task_id,
        "expectedRevision": 1,
        "reason": "Board collaboration does not update Task truth; resume the exact Host revision before acting",
    }
