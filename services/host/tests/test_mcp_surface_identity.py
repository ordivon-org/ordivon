from __future__ import annotations

import asyncio

from mcp import Client

from ordivon_host_v2.mcp_server import build_server


def test_host_server_identity_and_exact_static_tool_surface() -> None:
    async def scenario() -> None:
        async with Client(build_server("postgresql://unused.invalid/unused"), raise_exceptions=True) as client:
            listed = await client.list_tools()
            assert client.server_info is not None
            assert client.server_info.name == "ordivon-host-v2"
            assert client.server_info.version == "0.2.0"
            assert listed.ttl_ms == 0
            assert listed.cache_scope == "private"
            assert {tool.name for tool in listed.tools} == {
                "host.status",
                "attention.delta",
                "board.list",
                "board.search",
                "board.post",
                "task.observe",
                "task.list",
                "task.resume",
                "task.adopt",
                "task.checkpoint",
            }
            assert "news.list" not in {tool.name for tool in listed.tools}

    asyncio.run(scenario())
