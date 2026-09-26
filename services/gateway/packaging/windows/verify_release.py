from __future__ import annotations

import asyncio
import json
from importlib.metadata import version

from mcp import Client

from ordivon_gateway.mcp_server import build_server

EXPECTED = [
    "actor.declare",
    "artifact.read",
    "attention.ack",
    "attention.delta",
    "attention.get",
    "capability.describe",
    "execution.cancel",
    "execution.get",
    "execution.resolve",
    "execution.submit",
    "host.status",
    "message.post",
    "message.relation.add",
    "message.search",
    "space.create",
    "space.get",
    "space.list",
    "space.participation.set",
    "subscription.follow",
    "subscription.list",
    "subscription.unfollow",
    "system.describe",
    "topic.create",
    "topic.resume",
    "work.create",
    "work.get",
    "work.list",
    "work.snapshot.commit",
]


async def main() -> None:
    async with Client(build_server(), raise_exceptions=True) as client:
        listed = await client.list_tools()
        names = sorted(tool.name for tool in listed.tools)
        result = {
            "packageVersion": version("ordivon-gateway"),
            "serverVersion": client.server_info.version if client.server_info else None,
            "toolCount": len(names),
            "tools": names,
            "matchesExpected": names == EXPECTED,
        }
        print(json.dumps(result, sort_keys=True))
        if result["packageVersion"] != "0.4.0":
            raise SystemExit("unexpected package version")
        if result["serverVersion"] != "0.4.0":
            raise SystemExit("unexpected server version")
        if not result["matchesExpected"]:
            raise SystemExit("Gateway MCP surface drift")


if __name__ == "__main__":
    asyncio.run(main())
