"""Compose non-authoritative Host MCP adapters through one Gateway boundary."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import TYPE_CHECKING, Any

from mcp.server import MCPServer
from mcp_types import CallToolResult

from ...logic.host_tool_contracts import HostCollectionBytes as HostCollectionBytes
from ...logic.host_tool_contracts import HostMessageBytes as HostMessageBytes
from ...logic.owner_protocol import OwnerCallError
from .attention import register_host_attention_tools
from .social import register_host_social_tools
from .work import register_host_work_tools

if TYPE_CHECKING:
    from ...service import GatewayService


def register_host_tools(
    server: MCPServer,
    gateway: GatewayService,
    owner_boundary: Callable[[Awaitable[Any]], Awaitable[Any]],
    project_error: Callable[[OwnerCallError], CallToolResult],
) -> None:
    async def _host(tool_name: str, arguments: dict[str, Any]) -> Any:
        return await owner_boundary(gateway.social_work_call(tool_name, arguments))

    register_host_work_tools(server, _host, project_error)
    register_host_social_tools(server, _host)
    register_host_attention_tools(server, _host)
