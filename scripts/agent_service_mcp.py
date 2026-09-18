#!/usr/bin/env python3
"""Read-only authenticated loopback MCP canary for Ordivon Agent Service."""

from __future__ import annotations

import argparse
import hmac
import importlib.util
import json
import os
import stat
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from mcp.server import MCPServer
from mcp.server.transport_security import TransportSecuritySettings
from mcp.types import CallToolResult, TextContent, ToolAnnotations

DEFAULT_SOURCE_ROOT = Path(__file__).resolve().parents[1]
ROOT = Path(os.environ.get("ORDIVON_AGENT_SERVICE_SOURCE_ROOT", str(DEFAULT_SOURCE_ROOT))).resolve()
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

DEFAULT_BIND = "127.0.0.1"
DEFAULT_PORT = 8894
DEFAULT_TOKEN_FILE = Path("/etc/ordivon/agent-service-mcp.token")
DEFAULT_BODY_LIMIT = 1_048_576

R15_ACCEPTANCE = Path("evidence/acceptance/agent-service-effect-authority-r15.json")
R15_GRAPH = Path("knowledge/graphs/ordivon-agent-service-r15-effect-authority-delta.json")
GRAPH_CHECKER = Path("scripts/check_agent_service_graph_identity_r1.py")


@dataclass(frozen=True, slots=True)
class McpSettings:
    source_root: Path = ROOT
    token_file: Path = DEFAULT_TOKEN_FILE
    bind_host: str = DEFAULT_BIND
    port: int = DEFAULT_PORT
    body_limit_bytes: int = DEFAULT_BODY_LIMIT
    log_level: str = "INFO"

    def __post_init__(self) -> None:
        if not self.source_root.is_absolute() or not self.token_file.is_absolute():
            raise ValueError("Agent Service MCP source/token paths must be absolute")
        if self.bind_host not in {"127.0.0.1", "::1"}:
            raise ValueError("Agent Service canary MCP must bind literal loopback only")
        if type(self.port) is not int or not (1 <= self.port <= 65535):
            raise ValueError("MCP port must be in [1,65535]")
        if type(self.body_limit_bytes) is not int or self.body_limit_bytes < 1:
            raise ValueError("MCP body limit must be positive")
        if self.log_level not in {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}:
            raise ValueError("invalid MCP log level")

    @property
    def endpoint(self) -> str:
        host = f"[{self.bind_host}]" if ":" in self.bind_host else self.bind_host
        return f"http://{host}:{self.port}/mcp"


def _read_token(path: Path) -> str:
    if path.is_symlink() or not path.is_file():
        raise RuntimeError("Agent Service MCP token must be one regular non-symlink file")
    mode = stat.S_IMODE(path.stat().st_mode)
    if mode & 0o077:
        raise RuntimeError("Agent Service MCP token file must have no group/other permission bits")
    value = path.read_text(encoding="utf-8").strip()
    if len(value) < 32 or any(ch.isspace() for ch in value):
        raise RuntimeError("Agent Service MCP token must be at least 32 non-whitespace characters")
    return value


def _read_json(root: Path, relative: Path) -> dict[str, Any]:
    path = root / relative
    if not path.is_file():
        raise RuntimeError(f"required Agent Service artifact missing: {relative}")
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"required Agent Service artifact is not an object: {relative}")
    return value


def _graph_identity(root: Path) -> dict[str, Any]:
    path = root / GRAPH_CHECKER
    if not path.is_file():
        raise RuntimeError("Agent Service graph checker is missing")
    spec = importlib.util.spec_from_file_location("_ordivon_agent_service_graph_check", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("Agent Service graph checker cannot be loaded")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    value = module.validate()
    if value.get("status") != "PASS":
        raise RuntimeError("Agent Service graph identity check did not pass")
    return value


def _contract(root: Path) -> dict[str, Any]:
    acceptance = _read_json(root, R15_ACCEPTANCE)
    standings = acceptance.get("standings") or {}
    source_ready = standings.get("sourceImplementation") == "READY_TO_INTEGRATE_MAIN"
    authority_resolved = standings.get("authorityLifetimeQuestion") == "RESOLVED_BY_EXPLICIT_SEPARATION"
    production_blocked = standings.get("productionDeployment") == "NOT_ADMITTED"
    if not (source_ready and authority_resolved and production_blocked):
        raise RuntimeError("R15 acceptance standing is incompatible with read-only deployment canary")
    graph = _graph_identity(root)
    from agent_service import AgentServiceR15  # local source import; no service instance is created

    return {
        "schemaVersion": 1,
        "kind": "ordivon.agent-service-readonly-canary-contract",
        "status": "PASS",
        "compositionRoot": AgentServiceR15.__name__,
        "sourceImplementation": standings["sourceImplementation"],
        "authorityLifetimeQuestion": standings["authorityLifetimeQuestion"],
        "productionDeployment": standings["productionDeployment"],
        "graphFiles": graph["graphFiles"],
        "graphNodeCount": graph["nodeCount"],
        "writeSurfaceEnabled": False,
        "providerEffectSurfaceEnabled": False,
        "runtimeMutationSurfaceEnabled": False,
        "hostMutationSurfaceEnabled": False,
    }


async def _drain(receive, *, max_bytes: int) -> bool:
    total = 0
    while True:
        message = await receive()
        if message.get("type") == "http.disconnect":
            return True
        if message.get("type") != "http.request":
            continue
        body = message.get("body", b"")
        if not isinstance(body, bytes):
            return False
        total += len(body)
        if total > max_bytes:
            return False
        if message.get("more_body") is not True:
            return True


async def _problem(send, status: int, detail: str, *, authenticate: bool = False) -> None:
    raw = json.dumps(
        {"type": "about:blank", "title": "Unauthorized" if status == 401 else "Content Too Large",
         "status": status, "detail": detail[:1000]},
        separators=(",", ":"),
    ).encode()
    headers = [(b"content-type", b"application/problem+json"), (b"content-length", str(len(raw)).encode())]
    if authenticate:
        headers.append((b"www-authenticate", b"Bearer"))
    await send({"type": "http.response.start", "status": status, "headers": headers})
    await send({"type": "http.response.body", "body": raw})


class BearerAuthApp:
    def __init__(self, app, token: str, *, body_limit_bytes: int) -> None:
        self.app = app
        self.expected = f"Bearer {token}".encode()
        self.body_limit_bytes = body_limit_bytes

    async def __call__(self, scope, receive, send):
        if scope.get("type") != "http":
            return await self.app(scope, receive, send)
        authorization = b""
        for name, value in scope.get("headers", []):
            if name.lower() == b"authorization":
                authorization = value
                break
        if not hmac.compare_digest(authorization, self.expected):
            if not await _drain(receive, max_bytes=self.body_limit_bytes):
                return await _problem(send, 413, "Request body exceeds the configured limit.")
            return await _problem(send, 401, "A valid Bearer credential is required.", authenticate=True)
        return await self.app(scope, receive, send)


def _result(value: dict[str, Any]) -> CallToolResult:
    raw = json.dumps(value, sort_keys=True, ensure_ascii=False)
    return CallToolResult(content=[TextContent(type="text", text=raw)], structuredContent=value)


def build_server(settings: McpSettings) -> MCPServer:
    contract = _contract(settings.source_root)
    server = MCPServer(
        name="ordivon-agent-service-canary-mcp",
        title="Ordivon Agent Service Read-Only Canary",
        description="Read-only deployment qualification surface for the Agent Service R15 source composition.",
        instructions=(
            "This is a read-only deployment canary. It exposes no Session, Delegation, routing, delivery, "
            "credential, Runtime mutation, Host mutation, or provider-effect operation. Production deployment "
            "remains NOT_ADMITTED by the R15 acceptance contract."
        ),
        version="1",
        log_level=settings.log_level,
    )
    ro = ToolAnnotations(readOnlyHint=True, destructiveHint=False, idempotentHint=True, openWorldHint=False)

    @server.tool(name="service.doctor", title="Qualify Agent Service canary", annotations=ro)
    def service_doctor() -> CallToolResult:
        value = _contract(settings.source_root)
        value.update({"healthy": True, "endpoint": settings.endpoint, "deploymentMode": "READ_ONLY_CANARY"})
        return _result(value)

    @server.tool(name="service.contract", title="Read Agent Service authority contract", annotations=ro)
    def service_contract() -> CallToolResult:
        return _result(dict(contract))

    @server.tool(name="architecture.identity", title="Read Agent Service graph identity standing", annotations=ro)
    def architecture_identity() -> CallToolResult:
        return _result(_graph_identity(settings.source_root))

    @server.tool(name="deployment.snapshot", title="Read deployment canary surface", annotations=ro)
    def deployment_snapshot() -> CallToolResult:
        return _result({
            "schemaVersion": 1,
            "kind": "ordivon.agent-service-deployment-snapshot",
            "mode": "READ_ONLY_CANARY",
            "endpoint": settings.endpoint,
            "toolCount": 4,
            "writeSurfaceEnabled": False,
            "providerEffectSurfaceEnabled": False,
            "productionDeployment": "NOT_ADMITTED",
        })

    return server


def _transport_security() -> TransportSecuritySettings:
    return TransportSecuritySettings(
        enable_dns_rebinding_protection=True,
        allowed_hosts=["127.0.0.1:*", "localhost:*", "[::1]:*"],
        allowed_origins=["http://127.0.0.1:*", "http://localhost:*", "http://[::1]:*"],
    )


def build_app(settings: McpSettings, token: str):
    server = build_server(settings)
    app = server.streamable_http_app(
        streamable_http_path="/mcp",
        json_response=True,
        stateless_http=True,
        max_request_body_size=settings.body_limit_bytes,
        transport_security=_transport_security(),
        host=settings.bind_host,
    )
    return BearerAuthApp(app, token, body_limit_bytes=settings.body_limit_bytes)


def run(settings: McpSettings) -> None:
    token = _read_token(settings.token_file)
    app = build_app(settings, token)
    import uvicorn

    uvicorn.run(app, host=settings.bind_host, port=settings.port, log_level=settings.log_level.lower(), access_log=False)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, default=ROOT)
    parser.add_argument("--token-file", type=Path, default=DEFAULT_TOKEN_FILE)
    parser.add_argument("--bind", default=DEFAULT_BIND)
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    parser.add_argument("--body-limit-bytes", type=int, default=DEFAULT_BODY_LIMIT)
    parser.add_argument("--log-level", default="INFO")
    parser.add_argument("--check", action="store_true")
    return parser


def main() -> int:
    args = _parser().parse_args()
    settings = McpSettings(
        source_root=args.source_root.resolve(),
        token_file=args.token_file.resolve(),
        bind_host=args.bind,
        port=args.port,
        body_limit_bytes=args.body_limit_bytes,
        log_level=args.log_level.upper(),
    )
    _read_token(settings.token_file)
    server = build_server(settings)
    if args.check:
        tools = server._tool_manager.list_tools()
        value = {
            "schemaVersion": 1,
            "kind": "ordivon.agent-service-canary-mcp-check",
            "status": "ok",
            "endpoint": settings.endpoint,
            "toolNames": sorted(tool.name for tool in tools),
            "toolCount": len(tools),
            "readOnlyCanary": True,
            "productionDeployment": "NOT_ADMITTED",
        }
        print(json.dumps(value, sort_keys=True))
        return 0
    run(settings)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
