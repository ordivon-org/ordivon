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
            adopted = await client.call_tool(
                "task.adopt",
                {
                    "taskId": task_id,
                    "goalId": "goal:mcp-v2",
                    "initialCheckpoint": {"objective": "mcp-v2", "frontier": "created"},
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
                    "checkpoint": {"objective": "mcp-v2", "frontier": "resumable"},
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
