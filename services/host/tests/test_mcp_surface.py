from __future__ import annotations

import asyncio
import os
from uuid import uuid4

import pytest
from mcp import Client

from ordivon_host_v2 import HostV2
from ordivon_host_v2.mcp_server import build_server

DSN = os.environ.get("ORDIVON_HOST_V2_TEST_DSN")
pytestmark = pytest.mark.skipif(not DSN, reason="ORDIVON_HOST_V2_TEST_DSN not set")


def _checkpoint(task_id: str, frontier: str) -> dict[str, object]:
    return {
        "schemaVersion": 1,
        "kind": "ordivon.host-working-checkpoint",
        "truthRole": "semantic-working-claim",
        "taskId": task_id,
        "objective": "mcp-v2 continuity",
        "frontier": frontier,
        "established": ["baseline retained"],
        "unresolved": ["next transition"],
        "rejected": [],
        "constraints": ["exact revision only"],
        "nextActions": ["continue"],
        "runtime": None,
    }


def test_official_mcp_v2_exposes_migrated_host_surface_and_runs_vertical_slice() -> None:
    assert DSN is not None
    HostV2(DSN).initialize()
    task_id = f"task:v2:mcp:{uuid4().hex}"

    async def scenario() -> None:
        async with Client(build_server(DSN), raise_exceptions=True) as client:
            listed = await client.list_tools()
            names = {tool.name for tool in listed.tools}
            assert names == {
                "host.status",
                "attention.delta",
                "board.list",
                "board.search",
                "board.post",
                "news.list",
                "news.read",
                "news.publish",
                "task.observe",
                "task.list",
                "task.resume",
                "task.adopt",
                "task.checkpoint",
            }
            by_name = {tool.name: tool for tool in listed.tools}
            adopt_schema = by_name["task.adopt"].input_schema
            checkpoint_schema = by_name["task.checkpoint"].input_schema
            status_schema = by_name["host.status"].input_schema
            assert len(adopt_schema["properties"]["initialCheckpoint"]["oneOf"]) == 2
            assert len(checkpoint_schema["properties"]["checkpoint"]["oneOf"]) == 3
            assert {"detail", "recentLimit"} <= set(status_schema["properties"])

            status = await client.call_tool(
                "host.status", {"detail": "integrity", "recentLimit": 0}
            )
            assert status.is_error is False
            assert status.structured_content is not None
            assert status.structured_content["detail"] == "integrity"
            assert status.structured_content["authority"]["journalBackend"] == "postgresql"
            assert status.structured_content["doctor"]["healthy"] is True

            adopted = await client.call_tool(
                "task.adopt",
                {
                    "taskId": task_id,
                    "goalId": "goal:mcp-v2",
                    "initialCheckpoint": _checkpoint(task_id, "created"),
                },
            )
            assert adopted.is_error is False
            assert adopted.structured_content is not None
            assert adopted.structured_content["task"]["revision"] == 1

            updated = await client.call_tool(
                "task.checkpoint",
                {
                    "taskId": task_id,
                    "expectedRevision": 1,
                    "checkpoint": {"frontier": "resumable", "unresolved": []},
                },
            )
            assert updated.is_error is False
            resumed = await client.call_tool("task.resume", {"taskId": task_id})
            assert resumed.is_error is False
            assert resumed.structured_content is not None
            assert resumed.structured_content["task"]["revision"] == 2
            assert resumed.structured_content["checkpoint"]["frontier"] == "resumable"

    asyncio.run(scenario())



def test_news_list_keyset_cursor_is_scope_bound_and_complete() -> None:
    assert DSN is not None
    from ordivon_host_v2.news import NewsStore

    HostV2(DSN).initialize()
    store = NewsStore(DSN)
    marker = uuid4().hex
    for index in range(3):
        edition_id = f"news:r4-page:{marker}:{index}"
        store.publish(
            client_publish_id=f"publish:{edition_id}",
            edition_id=edition_id,
            expected_revision=0,
            edition={
                "editionId": edition_id,
                "editionDate": "2099-12-31",
                "timezone": "UTC",
                "items": [],
            },
        )
    first = store.list(limit=2, from_date="2099-12-31", to_date="2099-12-31")
    assert len(first["editions"]) == 2
    assert first["hasMore"] is True
    assert isinstance(first["nextCursor"], str)
    second = store.list(
        limit=2,
        cursor=first["nextCursor"],
        from_date="2099-12-31",
        to_date="2099-12-31",
    )
    assert len(second["editions"]) == 1
    assert second["hasMore"] is False
    assert second["nextCursor"] is None
    ids = {item["editionId"] for item in first["editions"] + second["editions"]}
    assert ids == {f"news:r4-page:{marker}:{index}" for index in range(3)}
    with pytest.raises(ValueError, match="query scope"):
        store.list(
            limit=2,
            cursor=first["nextCursor"],
            from_date="2099-12-30",
            to_date="2099-12-31",
        )



def test_mcp_checkpoint_patch_terminal_and_writer_replay_contract() -> None:
    assert DSN is not None
    HostV2(DSN).initialize()
    task_id = f"task:v2:mcp-contract:{uuid4().hex}"

    async def scenario() -> None:
        async with Client(build_server(DSN), raise_exceptions=True) as client:
            adopted = await client.call_tool(
                "task.adopt",
                {
                    "taskId": task_id,
                    "goalId": "goal:mcp-v2-contract",
                    "initialCheckpoint": _checkpoint(task_id, "baseline"),
                    "writerLabel": "writer:a",
                },
            )
            assert adopted.structured_content is not None
            assert adopted.structured_content["writerLabel"] == "writer:a"

            patched = await client.call_tool(
                "task.checkpoint",
                {
                    "taskId": task_id,
                    "expectedRevision": 1,
                    "checkpoint": {
                        "frontier": "patch-proven",
                        "unresolved": [],
                        "nextActions": ["terminalize"],
                    },
                    "writerLabel": "writer:b",
                },
            )
            assert patched.structured_content is not None
            assert patched.structured_content["admission"] == "committed"
            assert patched.structured_content["checkpoint"]["frontier"] == "patch-proven"
            assert patched.structured_content["checkpoint"]["established"] == [
                "baseline retained"
            ]
            assert patched.structured_content["checkpoint"]["constraints"] == [
                "exact revision only"
            ]
            assert patched.structured_content["writerLabel"] == "writer:b"

            replay = await client.call_tool(
                "task.checkpoint",
                {
                    "taskId": task_id,
                    "expectedRevision": 1,
                    "checkpoint": {
                        "frontier": "patch-proven",
                        "unresolved": [],
                        "nextActions": ["terminalize"],
                    },
                    "writerLabel": "writer:c",
                },
            )
            assert replay.structured_content is not None
            assert replay.structured_content["admission"] == "existing"
            assert replay.structured_content["writerLabel"] == "writer:b"

            rejected_terminal = await client.call_tool(
                "task.checkpoint",
                {
                    "taskId": task_id,
                    "expectedRevision": 2,
                    "checkpoint": {"frontier": "done"},
                    "continuityDisposition": "complete",
                },
            )
            assert rejected_terminal.is_error is True

            current = await client.call_tool(
                "task.resume", {"taskId": task_id, "expectedRevision": 2}
            )
            assert current.structured_content is not None
            terminal = dict(current.structured_content["checkpoint"])
            terminal["frontier"] = "done"
            terminal["unresolved"] = []
            terminal["nextActions"] = []
            completed = await client.call_tool(
                "task.checkpoint",
                {
                    "taskId": task_id,
                    "expectedRevision": 2,
                    "checkpoint": terminal,
                    "continuityDisposition": "complete",
                    "writerLabel": "writer:terminal",
                },
            )
            assert completed.structured_content is not None
            assert completed.structured_content["task"]["state"] == "completed"

    asyncio.run(scenario())


def test_mcp_checkpoint_rejects_task_identity_mismatch() -> None:
    assert DSN is not None
    HostV2(DSN).initialize()
    task_id = f"task:v2:mcp-mismatch:{uuid4().hex}"

    async def scenario() -> None:
        async with Client(build_server(DSN), raise_exceptions=True) as client:
            bad = _checkpoint("task:v2:wrong", "bad")
            rejected = await client.call_tool(
                "task.adopt",
                {
                    "taskId": task_id,
                    "goalId": "goal:mcp-v2-contract",
                    "initialCheckpoint": bad,
                },
            )
            assert rejected.is_error is True

    asyncio.run(scenario())
