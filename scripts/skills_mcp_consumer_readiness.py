#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import urllib.error
import urllib.request
from pathlib import Path

EXPECTED_TOOLS = ("skills.list", "skills.read", "skills.resolve", "skills.search")
DEFAULT_PUBLIC = "https://skills-mcp.ordivon.com/mcp"
DEFAULT_LOCAL = "http://127.0.0.1:8895/mcp"
DEFAULT_TOKEN = Path("/etc/ordivon/skills-mcp.token")


def _post(url: str, body: dict, headers: dict[str, str]) -> tuple[int, dict[str, str], bytes]:
    request = urllib.request.Request(
        url,
        data=json.dumps(body, separators=(",", ":")).encode(),
        headers=headers,
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            return response.status, dict(response.headers.items()), response.read()
    except urllib.error.HTTPError as exc:
        return exc.code, dict(exc.headers.items()), exc.read()


def _meta() -> dict:
    return {
        "io.modelcontextprotocol/protocolVersion": "2026-07-28",
        "io.modelcontextprotocol/clientCapabilities": {},
    }


def public_boundary(url: str) -> dict:
    status, headers, body = _post(
        url,
        {"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {"_meta": _meta()}},
        {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "MCP-Protocol-Version": "2026-07-28",
            "Mcp-Method": "tools/list",
            "User-Agent": "ordivon-skills-consumer-readiness/1",
        },
    )
    challenge = next((value for key, value in headers.items() if key.lower() == "www-authenticate"), "")
    ok = status == 401 and challenge.lower().startswith("bearer")
    return {
        "ok": ok,
        "status": status,
        "wwwAuthenticate": challenge,
        "bodyBytes": len(body),
    }


def local_tools(url: str, token_file: Path) -> dict:
    token = token_file.read_text(encoding="utf-8").strip()
    status, _headers, body = _post(
        url,
        {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {"_meta": _meta()}},
        {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "MCP-Protocol-Version": "2026-07-28",
            "Mcp-Method": "tools/list",
        },
    )
    if status != 200:
        return {"ok": False, "status": status, "tools": []}
    payload = json.loads(body)
    tools = tuple(sorted(tool["name"] for tool in payload["result"]["tools"]))
    return {"ok": tools == EXPECTED_TOOLS, "status": status, "tools": list(tools)}


def main() -> int:
    parser = argparse.ArgumentParser(description="Non-secret consumer-readiness check for Ordivon Skills MCP")
    parser.add_argument("--public-url", default=DEFAULT_PUBLIC)
    parser.add_argument("--local-url", default=DEFAULT_LOCAL)
    parser.add_argument("--token-file", type=Path, default=DEFAULT_TOKEN)
    args = parser.parse_args()

    public = public_boundary(args.public_url)
    local = local_tools(args.local_url, args.token_file)
    result = {
        "kind": "ordivon.skills-mcp-consumer-readiness",
        "schemaVersion": 1,
        "endpoint": args.public_url,
        "credentialKind": "static_bearer",
        "protocolVersion": "2026-07-28",
        "expectedTools": list(EXPECTED_TOOLS),
        "portableConfigContainsSecret": False,
        "publicBoundary": public,
        "localToolSurface": local,
        "status": "ready" if public["ok"] and local["ok"] else "not-ready",
    }
    print(json.dumps(result, sort_keys=True))
    return 0 if result["status"] == "ready" else 1


if __name__ == "__main__":
    raise SystemExit(main())
