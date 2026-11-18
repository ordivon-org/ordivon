#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import urllib.error
import urllib.request
from pathlib import Path
from urllib.parse import urlsplit

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
    lowered = challenge.lower()
    ok = (
        status == 401
        and lowered.startswith("bearer")
        and "resource_metadata=" in lowered
        and "cloudflare-access-protected-resource" in lowered
    )
    return {
        "ok": ok,
        "status": status,
        "wwwAuthenticate": challenge,
        "bodyBytes": len(body),
    }


def _is_loopback(url: str) -> bool:
    parsed = urlsplit(url)
    return parsed.scheme == "http" and parsed.hostname in {"127.0.0.1", "localhost", "::1"}


def _local_rpc(
    url: str,
    token: str,
    method: str,
    params: dict,
    request_id: int,
) -> tuple[int, dict | None]:
    if not _is_loopback(url):
        raise ValueError("authenticated readiness checks are restricted to loopback URLs")
    meta = _meta()
    if method == "server/discover":
        meta["io.modelcontextprotocol/clientInfo"] = {
            "name": "ordivon-skills-consumer-readiness",
            "version": "1",
        }
    rpc_params = dict(params)
    rpc_params["_meta"] = meta
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Accept": "application/json",
        "MCP-Protocol-Version": "2026-07-28",
        "Mcp-Method": method,
        "User-Agent": "ordivon-skills-consumer-readiness/1",
    }
    if method == "resources/read":
        headers["Mcp-Name"] = params["uri"]
    status, _headers, body = _post(
        url,
        {"jsonrpc": "2.0", "id": request_id, "method": method, "params": rpc_params},
        headers,
    )
    if status != 200:
        return status, None
    payload = json.loads(body)
    if "error" in payload:
        return status, None
    return status, payload["result"]


def local_tools(url: str, token_file: Path) -> dict:
    token = token_file.read_text(encoding="utf-8").strip()
    status, result = _local_rpc(url, token, "tools/list", {}, 2)
    if status != 200 or result is None:
        return {"ok": False, "status": status, "tools": []}
    tools = tuple(sorted(tool["name"] for tool in result["tools"]))
    return {"ok": tools == EXPECTED_TOOLS, "status": status, "tools": list(tools)}


def local_sep2640(url: str, token_file: Path) -> dict:
    token = token_file.read_text(encoding="utf-8").strip()
    status, discover = _local_rpc(url, token, "server/discover", {}, 10)
    if status != 200 or discover is None:
        return {"ok": False, "stage": "server/discover", "status": status}
    extensions = discover.get("capabilities", {}).get("extensions", {})
    if "io.modelcontextprotocol/skills" not in extensions:
        return {"ok": False, "stage": "server/discover", "status": status}

    status, listed = _local_rpc(url, token, "skills/list", {}, 11)
    if status != 200 or listed is None:
        return {"ok": False, "stage": "skills/list", "status": status}
    skills = listed.get("skills", [])
    if (
        not skills
        or listed.get("resultType") != "complete"
        or listed.get("cacheScope") != "private"
    ):
        return {"ok": False, "stage": "skills/list", "status": status}
    selected = next(
        (
            skill
            for skill in skills
            if skill.get("frontmatter", {}).get("name") == "test-driven-development"
        ),
        skills[0],
    )
    uri = selected["uri"]

    status, got = _local_rpc(url, token, "skills/get", {"uri": uri}, 12)
    if status != 200 or got is None or got.get("skill") != selected:
        return {"ok": False, "stage": "skills/get", "status": status}

    status, read = _local_rpc(url, token, "resources/read", {"uri": uri}, 13)
    if status != 200 or read is None:
        return {"ok": False, "stage": "resources/read", "status": status}
    contents = read.get("contents", [])
    if len(contents) != 1 or contents[0].get("uri") != uri or "text" not in contents[0]:
        return {"ok": False, "stage": "resources/read", "status": status}
    data = contents[0]["text"].encode("utf-8")
    manifest = {item["uri"]: item for item in selected.get("resources", [])}
    manifest_entry = manifest.get(uri)
    digest = "sha256:" + hashlib.sha256(data).hexdigest()
    if (
        manifest_entry is None
        or manifest_entry.get("digest") != digest
        or manifest_entry.get("size") != len(data)
    ):
        return {"ok": False, "stage": "resource-integrity", "status": status}

    names = [skill.get("frontmatter", {}).get("name") for skill in skills]
    return {
        "ok": True,
        "status": status,
        "extension": "io.modelcontextprotocol/skills",
        "resultType": listed.get("resultType"),
        "cacheScope": listed.get("cacheScope"),
        "skillsListed": len(skills),
        "uniqueNames": len(set(names)),
        "selectedName": selected.get("frontmatter", {}).get("name"),
        "selectedUri": uri,
        "resourceDigest": digest,
        "resourceSize": len(data),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Non-secret consumer-readiness check for Ordivon Skills MCP")
    parser.add_argument("--public-url", default=DEFAULT_PUBLIC)
    parser.add_argument("--local-url", default=DEFAULT_LOCAL)
    parser.add_argument("--token-file", type=Path, default=DEFAULT_TOKEN)
    args = parser.parse_args()

    public = public_boundary(args.public_url)
    local = local_tools(args.local_url, args.token_file)
    sep2640 = local_sep2640(args.local_url, args.token_file)
    result = {
        "kind": "ordivon.skills-mcp-consumer-readiness",
        "schemaVersion": 1,
        "endpoint": args.public_url,
        "credentialKind": "mcp_oauth",
        "oauthProvider": "cloudflare_access_managed_oauth",
        "localOperatorCredential": "static_bearer_loopback_only",
        "protocolVersion": "2026-07-28",
        "expectedTools": list(EXPECTED_TOOLS),
        "portableConfigContainsSecret": False,
        "publicBoundary": public,
        "localToolSurface": local,
        "localSep2640": sep2640,
        "status": "ready" if public["ok"] and local["ok"] and sep2640["ok"] else "not-ready",
    }
    print(json.dumps(result, sort_keys=True))
    return 0 if result["status"] == "ready" else 1


if __name__ == "__main__":
    raise SystemExit(main())
