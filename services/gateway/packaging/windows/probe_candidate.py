from __future__ import annotations

import asyncio
import json
import sys

from mcp import Client
from mcp.client.streamable_http import create_mcp_http_client, streamable_http_client


async def main() -> None:
    endpoint = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:18999/mcp"
    async with create_mcp_http_client() as http_client:
        transport = streamable_http_client(endpoint, http_client=http_client)
        async with Client(transport, mode="auto", raise_exceptions=False) as client:
            listed = await client.list_tools()
            tools = sorted(tool.name for tool in listed.tools)
            system_result = await client.call_tool("system.describe", {})
            capability_result = await client.call_tool("capability.describe", {})
            server_version = client.server_info.version if client.server_info else None

    def structured(result):
        if isinstance(result.structured_content, dict):
            return result.structured_content
        raise RuntimeError("candidate returned no structured content")

    payload = {
        "endpoint": endpoint,
        "serverVersion": server_version,
        "toolCount": len(tools),
        "tools": tools,
        "system": structured(system_result),
        "capabilities": structured(capability_result),
    }
    print(json.dumps(payload, sort_keys=True))


if __name__ == "__main__":
    asyncio.run(main())
