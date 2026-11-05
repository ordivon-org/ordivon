"""Compose non-authoritative Host MCP adapters through one Gateway boundary."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

from mcp.server import MCPServer

from .host_attention_tools import register_host_attention_tools
from .host_social_tools import register_host_social_tools
from .host_tool_contracts import HostCollectionBytes as HostCollectionBytes
from .host_tool_contracts import HostMessageBytes as HostMessageBytes
from .host_work_tools import register_host_work_tools
from .service import GatewayService


def register_host_tools(
    server: MCPServer,
    gateway: GatewayService,
    owner_boundary: Callable[[Awaitable[Any]], Awaitable[Any]],
) -> None:
    async def _host(tool_name: str, arguments: dict[str, Any]) -> Any:
        return await owner_boundary(gateway.social_work_call(tool_name, arguments))

    register_host_work_tools(server, _host)
    register_host_social_tools(server, _host)
    register_host_attention_tools(server, _host)
