from __future__ import annotations

import asyncio
import stat
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol
from urllib.parse import urlsplit

from anc_canonical import JsonValue, validate_json_value
from .ordivon.tool_errors import ToolBridgeError, ToolBridgeErrorKind


class McpHttpEndpoint(Protocol):
    url: str


def _read_private_bearer(path: Path) -> str:
    if not path.is_absolute() or path.is_symlink():
        raise ValueError("MCP bearer credential must be one absolute non-symlink file")
    info = path.stat()
    if not stat.S_ISREG(info.st_mode) or info.st_size > 16_384:
        raise ValueError("MCP bearer credential file is invalid")
    mode = stat.S_IMODE(info.st_mode)
    if mode & 0o007 or mode & 0o030:
        raise ValueError("MCP bearer credential permissions are too broad")
    token = path.read_text(encoding="utf-8").strip()
    if len(token) < 32 or any(ch.isspace() for ch in token):
        raise ValueError("MCP bearer credential is invalid")
    return token


class HarnessMcpClient(Protocol):
    def list_tools(self) -> tuple[dict[str, JsonValue], ...]: ...

    def call_tool(
        self, name: str, arguments: dict[str, JsonValue]
    ) -> tuple[bool, dict[str, JsonValue]]: ...


@dataclass(frozen=True, slots=True)
class LoopbackMcpEndpoint:
    url: str

    def __post_init__(self) -> None:
        parsed = urlsplit(self.url)
        if (
            parsed.scheme != "http"
            or parsed.hostname != "127.0.0.1"
            or parsed.username is not None
            or parsed.password is not None
            or parsed.fragment
            or parsed.path != "/mcp"
            or parsed.query
            or parsed.port is None
        ):
            raise ValueError(
                "internal MCP endpoint must be exact loopback HTTP http://127.0.0.1:<port>/mcp"
            )


@dataclass(slots=True)
class OfficialMcpClient:
    """Synchronous Harness port over the official MCP v2 async Client.

    Endpoint policy is owned by the supplied component. Agent Plugin components remain
    HTTPS-only; internal control-plane callers may use LoopbackMcpEndpoint. Authentication
    remains an embedding concern and is never copied or reinterpreted here.
    """

    component: McpHttpEndpoint
    auth: Any | None = None
    headers: dict[str, str] | None = None
    bearer_token_file: Path | None = None
    timeout_seconds: float = 30.0

    def _request_headers(self) -> dict[str, str] | None:
        headers = dict(self.headers or {})
        if self.bearer_token_file is not None:
            if any(key.lower() == "authorization" for key in headers):
                raise ValueError("MCP bearer credential conflicts with explicit Authorization header")
            headers["Authorization"] = "Bearer " + _read_private_bearer(Path(self.bearer_token_file))
        return headers or None

    def _run(self, coroutine):
        try:
            asyncio.get_running_loop()
        except RuntimeError:
            return asyncio.run(coroutine)
        raise RuntimeError(
            "OfficialMcpClient synchronous port cannot run inside an active event loop"
        )

    @staticmethod
    def _sdk():
        try:
            from mcp import Client
            from mcp.client.streamable_http import (
                create_mcp_http_client,
                streamable_http_client,
            )
        except ImportError as exc:
            raise RuntimeError(
                "OfficialMcpClient requires the standard MCP adapter; install ordivon-harness[mcp]"
            ) from exc
        return Client, create_mcp_http_client, streamable_http_client

    async def _list_tools(self) -> tuple[dict[str, JsonValue], ...]:
        Client, create_mcp_http_client, streamable_http_client = self._sdk()
        async with create_mcp_http_client(headers=self._request_headers(), auth=self.auth) as http_client:
            transport = streamable_http_client(self.component.url, http_client=http_client)
            async with Client(
                transport,
                mode="auto",
                raise_exceptions=False,
                read_timeout_seconds=self.timeout_seconds,
            ) as client:
                result = await client.list_tools()
        values: list[dict[str, JsonValue]] = []
        for tool in result.tools:
            value = tool.model_dump(mode="json", by_alias=True, exclude_none=True)
            validate_json_value(value)
            values.append(value)
        return tuple(values)

    def list_tools(self) -> tuple[dict[str, JsonValue], ...]:
        return self._run(self._list_tools())

    async def _call_tool(
        self, name: str, arguments: dict[str, JsonValue]
    ) -> tuple[bool, dict[str, JsonValue]]:
        Client, create_mcp_http_client, streamable_http_client = self._sdk()
        async with create_mcp_http_client(headers=self._request_headers(), auth=self.auth) as http_client:
            transport = streamable_http_client(self.component.url, http_client=http_client)
            async with Client(
                transport,
                mode="auto",
                raise_exceptions=False,
                read_timeout_seconds=self.timeout_seconds,
            ) as client:
                result = await client.call_tool(name, arguments)
        content = result.structured_content
        if not isinstance(content, dict):
            raise ToolBridgeError(
                f"MCP Tool {name} omitted structured object content",
                kind=ToolBridgeErrorKind.PROTOCOL_INVALID,
            )
        validate_json_value(content)
        return bool(result.is_error), dict(content)

    def call_tool(
        self, name: str, arguments: dict[str, JsonValue]
    ) -> tuple[bool, dict[str, JsonValue]]:
        validate_json_value(arguments)
        return self._run(self._call_tool(name, arguments))


__all__ = [
    "HarnessMcpClient",
    "LoopbackMcpEndpoint",
    "McpHttpEndpoint",
    "OfficialMcpClient",
]
