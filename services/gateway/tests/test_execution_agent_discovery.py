from __future__ import annotations

import asyncio

from mcp import Client

from ordivon_gateway.mcp_server import build_server


def test_agent_execution_discovery_exposes_provider_context_and_resume_coordinates() -> None:
    """An Agent must discover the existing rules before making a failing RPC."""

    async def run() -> None:
        async with Client(build_server(), raise_exceptions=True) as client:
            by_name = {tool.name: tool for tool in (await client.list_tools()).tools}
            submit = by_name["execution.submit"].description or ""
            assert "execution.linux" in submit and "string" in submit
            assert "execution.harness" in submit
            assert "execution.windows" in submit and "object" in submit
            assert "requestId" in submit and "capability.describe" in submit
            for name in ("execution.get", "execution.cancel", "artifact.read"):
                text = by_name[name].description or ""
                assert "HTTP" in text and "original requestId" in text
                assert "capability" in text and "operationRef" in text
            resolve = by_name["execution.resolve"].description or ""
            assert "original requestId" in resolve and "capability" in resolve
            assert "before retry" in resolve

    asyncio.run(run())
