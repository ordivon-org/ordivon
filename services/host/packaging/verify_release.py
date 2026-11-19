from __future__ import annotations

"""Native Host MCP input/output schema gate for immutable releases.

Reuse the Gateway's mature official-SDK contract projection, scoped to Host.
No database connection, credential, new registry or external effect is needed.
"""

import asyncio
import hashlib
import json
from importlib.metadata import version
from pathlib import Path

from mcp import Client

from ordivon_host_v2.mcp_server import build_server

SURFACE_PATH = Path(__file__).resolve().parents[1] / "mcp-surface.json"
SURFACE = json.loads(SURFACE_PATH.read_text(encoding="utf-8"))
EXPECTED_VERSION = SURFACE["packageVersion"]
EXPECTED_TOOLS = list(SURFACE["tools"])
EXPECTED_CONTRACT_DIGEST = SURFACE["contractDigest"]


def native_tool_contract_digest(tools: list) -> str:
    """Native MCP tools/list signatures, not hand-maintained source hints."""
    contracts = []
    for tool in tools:
        data = tool.model_dump(mode="json", by_alias=True, exclude_none=True)
        contracts.append(
            {
                "name": data["name"],
                "inputSchema": data["inputSchema"],
                "outputSchema": data.get("outputSchema"),
            }
        )
    encoded = json.dumps(
        sorted(contracts, key=lambda row: row["name"]),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


async def main() -> None:
    # tools/list is protocol discovery; it does not require any Host DB query.
    async with Client(build_server("postgresql://unused.invalid/unused"), raise_exceptions=True) as client:
        listed = await client.list_tools()
        names = sorted(tool.name for tool in listed.tools)
        digest = native_tool_contract_digest(listed.tools)
        result = {
            "packageVersion": version("ordivon-host-v2"),
            "serverVersion": client.server_info.version if client.server_info else None,
            "toolCount": len(names),
            "surfaceEpoch": SURFACE["surfaceEpoch"],
            "matchesExpected": names == EXPECTED_TOOLS,
            "contractDigest": digest,
            "contractMatchesExpected": digest == EXPECTED_CONTRACT_DIGEST,
        }
        print(json.dumps(result, sort_keys=True))
        if result["packageVersion"] != EXPECTED_VERSION:
            raise SystemExit("Host package version differs from mcp-surface.json")
        if result["serverVersion"] != EXPECTED_VERSION:
            raise SystemExit("Host native MCP server version drift")
        if not result["matchesExpected"]:
            raise SystemExit("Host native MCP tool names drift")
        if not result["contractMatchesExpected"]:
            raise SystemExit("Host native MCP input/output schema drift")


if __name__ == "__main__":
    asyncio.run(main())
