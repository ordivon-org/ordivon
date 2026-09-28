from __future__ import annotations

import asyncio
import json
from importlib.metadata import version
from pathlib import Path

from mcp import Client

from ordivon_gateway.mcp_server import build_server

SURFACE_PATH = Path(__file__).resolve().parents[2] / "mcp-surface.json"
SURFACE = json.loads(SURFACE_PATH.read_text(encoding="utf-8"))
EXPECTED_VERSION = SURFACE["packageVersion"]
EXPECTED = list(SURFACE["tools"])


async def main() -> None:
    async with Client(build_server(), raise_exceptions=True) as client:
        listed = await client.list_tools()
        names = sorted(tool.name for tool in listed.tools)
        result = {
            "packageVersion": version("ordivon-gateway"),
            "serverVersion": client.server_info.version if client.server_info else None,
            "toolCount": len(names),
            "tools": names,
            "surfaceEpoch": SURFACE["surfaceEpoch"],
            "matchesExpected": names == EXPECTED,
        }
        print(json.dumps(result, sort_keys=True))
        if result["packageVersion"] != EXPECTED_VERSION:
            raise SystemExit("package version differs from mcp-surface.json")
        if result["serverVersion"] != EXPECTED_VERSION:
            raise SystemExit("server version differs from mcp-surface.json")
        if not result["matchesExpected"]:
            raise SystemExit("Gateway MCP surface drift")


if __name__ == "__main__":
    asyncio.run(main())
