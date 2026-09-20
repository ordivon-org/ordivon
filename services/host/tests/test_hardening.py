from __future__ import annotations

import os
from uuid import uuid4

import pytest

from ordivon_host_v2 import CheckpointInput, ConflictError, HostV2
from ordivon_host_v2.board import BoardStore

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


def test_explicit_task_route_and_reply_inheritance_drive_attention() -> None:
    host, board = stores()
    task_id = f"task:v2:attention:{uuid4().hex}"
    other_task_id = f"task:v2:attention-other:{uuid4().hex}"
    for current in (task_id, other_task_id):
        host.adopt(
            task_id=current,
            checkpoint=CheckpointInput(
                payload={"frontier": "resume me", "runtime": {"workspaceId": "ws:test"}}
            ),
            client_request_id=f"adopt:{current}",
        )

    root = board.post(
        client_message_id=f"msg:{uuid4().hex}",
        author_label="agent:peer",
        message="coordinate this exact Task",
        message_kind="note",
        topic="coordination",
        task_id=task_id,
    )
    reply = board.post(
        client_message_id=f"reply:{uuid4().hex}",
        author_label="agent:peer",
        message="continue from exact Host revision",
        message_kind="reply",
        topic="coordination",
        reply_to_client_message_id=root["message"]["clientMessageId"],
    )
    assert reply["message"]["taskId"] == task_id

    with pytest.raises(ConflictError, match="conflicts with parent taskId"):
        board.post(
            client_message_id=f"reply:{uuid4().hex}",
            author_label="agent:peer",
            message="wrong Task route",
            message_kind="reply",
            topic="coordination",
            reply_to_client_message_id=root["message"]["clientMessageId"],
            task_id=other_task_id,
        )

    delta = host.attention_delta(after_sequence=int(root["message"]["sequence"]), limit=10)
    assert delta["kind"] == "ordivon.host-current-attention-delta"
    assert delta["schemaVersion"] == 3
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
