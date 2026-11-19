"""Host continuity transport adapter, independent of the MCP registration layer.

Host is the only authority for Work, Topic and Message state. This adapter
does not create Actor identity, authorize tools or synthesize Host success.
"""

from __future__ import annotations

from typing import Any

from ...logic.execution_refs import GatewayError
from ...logic.host_tool_contracts import (
    HOST_READ_TOOLS,
    SOCIAL_WORK_HOST_TOOLS,
    host_read_transport_route,
)
from ...logic.owner_protocol import OwnerToolCaller


class HostContinuityAdapter:
    def __init__(self, caller: OwnerToolCaller) -> None:
        self._caller = caller

    async def call(self, tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        if tool_name not in SOCIAL_WORK_HOST_TOOLS:
            raise GatewayError(f"unsupported Host Social Work tool: {tool_name}")
        # A declared protected read URL is sticky: if its credentials or
        # connection fail, DO NOT retry against the legacy writable Host.
        owner_route = (
            host_read_transport_route(self._caller) if tool_name in HOST_READ_TOOLS else "host"
        )
        result = await self._caller.call_tool(owner_route, tool_name, arguments)
        if not isinstance(result, dict):
            raise GatewayError("Host Social Work owner returned non-object response")
        return result
