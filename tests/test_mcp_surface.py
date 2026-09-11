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


def test_official_mcp_v2_exposes_only_r1_surface_and_runs_vertical_slice() -> None:
    assert DSN is not None
    HostV2(DSN).initialize()
    task_id = f"task:v2:mcp:{uuid4().hex}"

    async def scenario() -> None:
        async with Client(build_server(DSN), raise_exceptions=True) as client:
            listed = await client.list_tools()
            names = {tool.name for tool in listed.tools}
            assert names == {
                "host.status",
                "task.list",
                "task.adopt",
                "task.checkpoint",
                "task.resume",
            }
            adopted = await client.call_tool(
                "task.adopt",
                {
                    "task_id": task_id,
                    "checkpoint": {"objective": "mcp-v2", "frontier": "created"},
                    "client_request_id": f"adopt:{task_id}",
                },
            )
            assert adopted.is_error is False
            assert adopted.structured_content is not None
            assert adopted.structured_content["task"]["revision"] == 1

            updated = await client.call_tool(
                "task.checkpoint",
                {
                    "task_id": task_id,
                    "expected_revision": 1,
                    "checkpoint": {"objective": "mcp-v2", "frontier": "resumable"},
                    "client_request_id": f"cp:{task_id}",
                },
            )
            assert updated.is_error is False
            resumed = await client.call_tool("task.resume", {"task_id": task_id})
            assert resumed.is_error is False
            assert resumed.structured_content is not None
            assert resumed.structured_content["revision"] == 2
            assert resumed.structured_content["checkpoint"]["frontier"] == "resumable"

    asyncio.run(scenario())
