from __future__ import annotations

import asyncio
import hashlib
import json
from importlib.metadata import version
from pathlib import Path

from mcp import Client

from ordivon_gateway.mcp_server import build_server

SURFACE_PATH = Path(__file__).resolve().parents[2] / "mcp-surface.json"
SURFACE = json.loads(SURFACE_PATH.read_text(encoding="utf-8"))
EXPECTED_VERSION = SURFACE["packageVersion"]
EXPECTED = list(SURFACE["tools"])
EXPECTED_CONTRACT_DIGEST = SURFACE["contractDigest"]


def native_tool_contract_digest(tools: list) -> str:
    """Hash the MCP SDK's actual wire input/output contracts, not source hints."""
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
    canonical = json.dumps(
        sorted(contracts, key=lambda row: row["name"]),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(canonical).hexdigest()


async def main() -> None:
    async with Client(build_server(), raise_exceptions=True) as client:
        listed = await client.list_tools()
        names = sorted(tool.name for tool in listed.tools)
        contract_digest = native_tool_contract_digest(listed.tools)
        result = {
            "packageVersion": version("ordivon-gateway"),
            "serverVersion": client.server_info.version if client.server_info else None,
            "toolCount": len(names),
            "tools": names,
            "surfaceEpoch": SURFACE["surfaceEpoch"],
            "matchesExpected": names == EXPECTED,
            "contractDigest": contract_digest,
            "contractMatchesExpected": contract_digest == EXPECTED_CONTRACT_DIGEST,
        }
        print(json.dumps(result, sort_keys=True))
        if result["packageVersion"] != EXPECTED_VERSION:
            raise SystemExit("package version differs from mcp-surface.json")
        if result["serverVersion"] != EXPECTED_VERSION:
            raise SystemExit("server version differs from mcp-surface.json")
        if not result["matchesExpected"]:
            raise SystemExit("Gateway MCP surface drift")
        if not result["contractMatchesExpected"]:
            raise SystemExit("Gateway MCP tool input/output schema drift")


if __name__ == "__main__":
    asyncio.run(main())
