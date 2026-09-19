#!/usr/bin/env python3
"""Authenticated loopback MCP facade for Ordivon Agent Automation."""

from __future__ import annotations

import argparse
import asyncio
import hmac
import json
import os
import stat
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Annotated, Any

from mcp.server import MCPServer
from mcp.server.transport_security import TransportSecuritySettings
from mcp.types import CallToolResult, TextContent, ToolAnnotations
from pydantic import BaseModel, ConfigDict, Field

DEFAULT_SOURCE_ROOT = Path(__file__).resolve().parents[1]
ROOT = Path(
    os.environ.get("ORDIVON_AGENT_AUTOMATION_SOURCE_ROOT", str(DEFAULT_SOURCE_ROOT))
).resolve()
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from agent_automation_registry import AgentAutomationRegistryError, CampaignRegistry  # noqa: E402
from standard_identifiers import UUID7_PATTERN  # noqa: E402
from agent_automation_browserless import (  # noqa: E402
    BrowserlessAutomationConfig,
    BrowserlessAutomationAmbiguous,
    BrowserlessAutomationConflict,
    BrowserlessAutomationHold,
    BrowserlessAutomationService,
    _read_json,
)

DEFAULT_BIND = "127.0.0.1"
DEFAULT_PORT = 8896
DEFAULT_TOKEN_FILE = Path("/etc/ordivon/agent-automation-mcp.token")
DEFAULT_CONFIG_FILE = Path("/etc/ordivon/agent-automation-browserless.json")
DEFAULT_BODY_LIMIT = 1_048_576


class RoleCardInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    agentId: str = Field(min_length=1, max_length=128)
    roleCard: str = Field(min_length=1, max_length=16384)


class CampaignSpecInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    campaignId: str = Field(min_length=1, max_length=512)
    sharedPrompt: str = Field(min_length=1, max_length=32768)
    roster: list[RoleCardInput] = Field(min_length=1, max_length=256)


@dataclass(frozen=True, slots=True)
class McpSettings:
    config_file: Path
    token_file: Path = DEFAULT_TOKEN_FILE
    bind_host: str = DEFAULT_BIND
    port: int = DEFAULT_PORT
    body_limit_bytes: int = DEFAULT_BODY_LIMIT
    log_level: str = "INFO"

    def __post_init__(self) -> None:
        if not self.config_file.is_absolute() or not self.token_file.is_absolute():
            raise ValueError("MCP config/token paths must be absolute")
        if self.bind_host not in {"127.0.0.1", "::1"}:
            raise ValueError("Agent Automation MCP must bind literal loopback only")
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
        raise RuntimeError("Agent Automation MCP token must be one regular non-symlink file")
    mode = stat.S_IMODE(path.stat().st_mode)
    if mode & 0o077:
        raise RuntimeError(
            "Agent Automation MCP token file must have no group/other permission bits"
        )
    value = path.read_text(encoding="utf-8").strip()
    if len(value) < 32 or any(ch.isspace() for ch in value):
        raise RuntimeError(
            "Agent Automation MCP token must be at least 32 non-whitespace characters"
        )
    return value


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


_HTTP_PROBLEM_TITLES = {
    401: "Unauthorized",
    413: "Content Too Large",
}


def _http_problem_value(status: int, detail: str) -> dict[str, Any]:
    title = _HTTP_PROBLEM_TITLES.get(status)
    if title is None:
        raise ValueError(f"unsupported HTTP problem status {status}")
    return {
        "type": "about:blank",
        "title": title,
        "status": status,
        "detail": detail[:1000],
    }


async def _http_problem(send, status: int, detail: str, *, authenticate: bool = False) -> None:
    raw = json.dumps(_http_problem_value(status, detail), separators=(",", ":")).encode()
    headers = [
        (b"content-type", b"application/problem+json"),
        (b"content-length", str(len(raw)).encode()),
    ]
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
                return await _http_problem(send, 413, "Request body exceeds the configured limit.")
            return await _http_problem(
                send, 401, "A valid Bearer credential is required.", authenticate=True
            )
        return await self.app(scope, receive, send)


def _result(value: dict[str, Any], *, error: bool = False) -> CallToolResult:
    raw = json.dumps(value, sort_keys=True, ensure_ascii=False)
    return CallToolResult(
        content=[TextContent(type="text", text=raw)], structuredContent=value, isError=error
    )


def _tool_error(detail: str, *, effect_commit_state: str | None = None) -> CallToolResult:
    detail = detail[:1000]
    value: dict[str, Any] = {"detail": detail}
    # The only extension retained beyond MCP's tool-error mechanism: standards cannot infer
    # whether an external provider effect may already exist after admission/response loss.
    if effect_commit_state is not None:
        if effect_commit_state != "unknown":
            raise ValueError("effectCommitState extension only admits unknown")
        value["effectCommitState"] = effect_commit_state
    return CallToolResult(
        content=[TextContent(type="text", text=detail)],
        structuredContent=value,
        isError=True,
    )


async def _invoke(fn, *args, **kwargs) -> CallToolResult:
    try:
        value = await asyncio.to_thread(fn, *args, **kwargs)
        return _result(value)
    except BrowserlessAutomationAmbiguous as error:
        return _tool_error(str(error), effect_commit_state="unknown")
    except BrowserlessAutomationHold as error:
        return _tool_error(str(error))
    except (BrowserlessAutomationConflict, AgentAutomationRegistryError, ValueError) as error:
        return _tool_error(str(error))
    except Exception as error:
        # No traceback or hidden implementation detail on the Agent-facing surface. Since a
        # service function can fail after durable Temporal admission, conservatively fence retry.
        return _tool_error(
            f"{type(error).__name__}: operation failed", effect_commit_state="unknown"
        )


def build_server(settings: McpSettings) -> MCPServer:
    # Validate once at startup, but never retain mutable provider/network binding for the
    # lifetime of the MCP process. Every tool call re-enters the current config authority.
    BrowserlessAutomationConfig.from_dict(_read_json(settings.config_file))

    def current_config() -> BrowserlessAutomationConfig:
        return BrowserlessAutomationConfig.from_dict(_read_json(settings.config_file))

    def current_service() -> BrowserlessAutomationService:
        return BrowserlessAutomationService(current_config())

    def current_registry() -> CampaignRegistry:
        return CampaignRegistry(current_config().state_root)

    server = MCPServer(
        name="ordivon-agent-automation-mcp",
        title="Ordivon Agent Automation",
        description="Temporal-controlled, Browserless-backed campaign materialization and continuation facade.",
        instructions=(
            "Use campaign.register only for controller-classified L0 Direct work. L1/L2 campaign registration is intentionally unavailable until authoritative current Host Inquiry standing can be verified; L1/L2 work MUST NOT fall back to campaign.register. "
            "campaign.launch and materialization.reconcile admit deterministic Temporal workflows; Browserless owns browser lifecycle. "
            "A challenge/auth gate may become HUMAN_REQUIRED without crossing ChatGPT SEND. Use materialization.humanHandoff to obtain the bounded interactive operator URL, then materialization.humanResume only after a bounded self-hosted handoff expires or current-session absence is proven. "
            "The SQLite effect fence remains authoritative at ChatGPT SEND, so UNKNOWN/ambiguous never authorizes blind resend. "
            "Use provider.preflight for one explicit read-only endpoint admission observation."
        ),
        version="1",
        log_level=settings.log_level,
    )

    @server.tool(
        name="automation.doctor",
        title="Qualify Agent Automation",
        description="Read current Browserless substrate and provider-effect ledger health without provider effects.",
        annotations=ToolAnnotations(
            readOnlyHint=True, destructiveHint=False, idempotentHint=True, openWorldHint=False
        ),
    )
    async def automation_doctor() -> CallToolResult:
        return await _invoke(current_service().doctor)

    @server.tool(
        name="campaign.register",
        title="Register direct campaign spec",
        description="Freeze one controller-classified L0 Direct CampaignSpec into immutable local registry bytes and return a stable campaignRef. No provider effect. L1/L2 registration is unavailable and MUST NOT fall back to this L0 surface.",
        annotations=ToolAnnotations(
            readOnlyHint=False, destructiveHint=False, idempotentHint=True, openWorldHint=False
        ),
    )
    async def campaign_register(spec: CampaignSpecInput) -> CallToolResult:
        return await _invoke(current_registry().register, spec.model_dump(exclude_none=True))

    @server.tool(
        name="campaign.inspect",
        title="Inspect registered campaign",
        description="Read one exact registered campaignRef identity without provider effects.",
        annotations=ToolAnnotations(
            readOnlyHint=True, destructiveHint=False, idempotentHint=True, openWorldHint=False
        ),
    )
    async def campaign_inspect(campaignRef: str) -> CallToolResult:
        return await _invoke(current_registry().inspect, campaignRef)

    @server.tool(
        name="campaign.launch",
        title="Launch registered campaign",
        description="Materialize all missing materializations of one registered campaignRef. READY proceeds normally; challenge/auth admission may enter a bounded HUMAN_REQUIRED handoff without filling the composer or crossing SEND. Existing effects remain idempotent and ambiguous states never blind-resend.",
        annotations=ToolAnnotations(
            readOnlyHint=False, destructiveHint=False, idempotentHint=True, openWorldHint=True
        ),
    )
    async def campaign_launch(campaignRef: str) -> CallToolResult:
        try:
            path = current_registry().resolve(campaignRef)
        except Exception as error:
            return _tool_error(str(error))
        return await _invoke(current_service().launch_campaign, path)

    @server.tool(
        name="campaign.census",
        title="Read campaign materialization census",
        description="Read exact provider-effect materialization standing for one registered campaignRef. No provider effect.",
        annotations=ToolAnnotations(
            readOnlyHint=True, destructiveHint=False, idempotentHint=True, openWorldHint=False
        ),
    )
    async def campaign_census(campaignRef: str) -> CallToolResult:
        try:
            path = current_registry().resolve(campaignRef)
        except Exception as error:
            return _tool_error(str(error))
        return await _invoke(current_service().census, path)

    @server.tool(
        name="materialization.reconcile",
        title="Reconcile materialization",
        description="Converge one exact materialization toward its materialization target. Unrecorded materializations start the stable Temporal workflow; ambiguous materializations reconcile the same durable effect identity; blind provider resend is never authorized.",
        annotations=ToolAnnotations(
            readOnlyHint=False, destructiveHint=False, idempotentHint=True, openWorldHint=True
        ),
    )
    async def materialization_reconcile(campaignRef: str, agentId: str) -> CallToolResult:
        try:
            path = current_registry().resolve(campaignRef)
        except Exception as error:
            return _tool_error(str(error))
        return await _invoke(current_service().launch_reconcile, path, agentId)

    @server.tool(
        name="materialization.humanHandoff",
        title="Open human provider verification",
        description="Read the private interactive URL for one currently active HUMAN_REQUIRED provider-admission session. This is an operator handoff only: it never fills the composer, clicks the provider challenge, or crosses SEND.",
        annotations=ToolAnnotations(
            readOnlyHint=True, destructiveHint=False, idempotentHint=True, openWorldHint=False
        ),
    )
    async def materialization_human_handoff(campaignRef: str, agentId: str) -> CallToolResult:
        try:
            path = current_registry().resolve(campaignRef)
        except Exception as error:
            return _tool_error(str(error))
        return await _invoke(current_service().human_handoff_info, path, agentId)

    @server.tool(
        name="materialization.humanResume",
        title="Resume after human provider verification",
        description="Re-enter provider admission for the same frozen materialization effect after a prior HUMAN_REQUIRED handoff window expired. The materializer atomically claims the same effect identity and never blind-resends an UNKNOWN outcome.",
        annotations=ToolAnnotations(
            readOnlyHint=False, destructiveHint=False, idempotentHint=False, openWorldHint=True
        ),
    )
    async def materialization_human_resume(campaignRef: str, agentId: str) -> CallToolResult:
        try:
            path = current_registry().resolve(campaignRef)
        except Exception as error:
            return _tool_error(str(error))
        return await _invoke(current_service().launch_human_resume, path, agentId)

    @server.tool(
        name="conversation.continue",
        title="Continue provider conversation",
        description="Send exactly one continuation turn to the same provider-bound conversation. The routed Browserless endpoint must pass read-only READY preflight before Temporal admission; turnRequestId is an RFC 9562 UUIDv7 and provider SEND remains fenced by the turn ledger.",
        annotations=ToolAnnotations(
            readOnlyHint=False, destructiveHint=False, idempotentHint=True, openWorldHint=True
        ),
    )
    async def conversation_continue(
        campaignRef: str,
        agentId: str,
        turnRequestId: Annotated[str, Field(pattern=UUID7_PATTERN)],
        prompt: str,
    ) -> CallToolResult:
        try:
            path = current_registry().resolve(campaignRef)
        except Exception as error:
            return _tool_error(str(error))
        return await _invoke(
            current_service().launch_continue,
            path,
            agentId,
            prompt=prompt,
            turn_request_id=turnRequestId,
        )

    @server.tool(
        name="provider.preflight",
        title="Read one provider admission state",
        description="Observe one explicit Browserless endpoint without filling, clicking or sending. This never rotates across profiles and never authorizes bypass of provider challenges.",
        annotations=ToolAnnotations(
            readOnlyHint=True, destructiveHint=False, idempotentHint=True, openWorldHint=True
        ),
    )
    async def provider_preflight(endpointId: str) -> CallToolResult:
        return await _invoke(current_service().provider_preflight, endpointId)

    return server


def _transport_security() -> TransportSecuritySettings:
    return TransportSecuritySettings(
        enable_dns_rebinding_protection=True,
        allowed_hosts=["127.0.0.1:*", "localhost:*", "[::1]:*"],
        allowed_origins=[
            "http://127.0.0.1:*",
            "http://localhost:*",
            "http://[::1]:*",
        ],
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
    # Validate config/service construction before opening a listener.
    build_server(settings)
    app = build_app(settings, token)
    import uvicorn

    uvicorn.run(
        app,
        host=settings.bind_host,
        port=settings.port,
        log_level=settings.log_level.lower(),
        access_log=False,
    )


def _parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--config", type=Path, default=DEFAULT_CONFIG_FILE)
    p.add_argument("--token-file", type=Path, default=DEFAULT_TOKEN_FILE)
    p.add_argument("--bind", default=DEFAULT_BIND)
    p.add_argument("--port", type=int, default=DEFAULT_PORT)
    p.add_argument("--body-limit-bytes", type=int, default=DEFAULT_BODY_LIMIT)
    p.add_argument("--log-level", default="INFO")
    p.add_argument("--check", action="store_true")
    return p


def main() -> int:
    a = _parser().parse_args()
    settings = McpSettings(
        config_file=a.config.resolve(),
        token_file=a.token_file.resolve(),
        bind_host=a.bind,
        port=a.port,
        body_limit_bytes=a.body_limit_bytes,
        log_level=a.log_level.upper(),
    )
    _read_token(settings.token_file)
    server = build_server(settings)
    if a.check:
        tools = server._tool_manager.list_tools()
        value = {
            "schemaVersion": 1,
            "kind": "ordivon.agent-automation-mcp-check",
            "status": "ok",
            "endpoint": settings.endpoint,
            "configFile": str(settings.config_file),
            "tokenFile": str(settings.token_file),
            "toolNames": sorted(tool.name for tool in tools),
            "toolCount": len(tools),
        }
        print(json.dumps(value, sort_keys=True))
        return 0
    run(settings)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
