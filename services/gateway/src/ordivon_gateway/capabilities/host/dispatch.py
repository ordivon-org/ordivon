"""Host continuity transport adapter, independent of the MCP registration layer.

Host is the only authority for Work, Topic and Message state. This adapter
does not create Actor identity, authorize tools or synthesize Host success.
"""

from __future__ import annotations

from typing import Any

from ...logic.execution_refs import GatewayError
from ...logic.host_tool_contracts import (
    HOST_READ_SELECTORS,
    HOST_READ_TOOLS,
    SOCIAL_WORK_HOST_TOOLS,
    host_read_transport_route,
)
from ...logic.owner_protocol import OwnerToolCaller
from ...logic.public_tool_binding import current_public_tool_call


class HostContinuityAdapter:
    def __init__(self, caller: OwnerToolCaller) -> None:
        self._caller = caller

    async def call(self, tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        if tool_name not in SOCIAL_WORK_HOST_TOOLS:
            raise GatewayError(f"unsupported Host Social Work tool: {tool_name}")
        # The existing Security middleware binds the actual public MCP action
        # around call_next. Refuse a different delegated effect or resource
        # before contacting the natural Host. This is *not* a second PDP:
        # Principal/issuer/ALLOW belong solely to the existing PEP.
        public_request = current_public_tool_call()
        if public_request is not None:
            public_action, public_arguments = public_request
            if public_action != tool_name:
                raise GatewayError("Gateway public action does not match delegated Owner tool")
            for selector in HOST_READ_SELECTORS.get(tool_name, ()):
                if (
                    selector in public_arguments
                    and arguments.get(selector) != public_arguments[selector]
                ):
                    raise GatewayError(
                        "Gateway authorized Host selector changed before Owner dispatch"
                    )
            for key, value in public_arguments.items():
                if key not in arguments or arguments[key] != value:
                    raise GatewayError(
                        "Gateway public Host arguments changed before Owner dispatch"
                    )
        # A declared protected read URL is sticky: if its credentials or
        # connection fail, DO NOT retry against the legacy writable Host.
        owner_route = (
            host_read_transport_route(self._caller) if tool_name in HOST_READ_TOOLS else "host"
        )
        result = await self._caller.call_tool(owner_route, tool_name, arguments)
        if not isinstance(result, dict):
            raise GatewayError("Host Social Work owner returned non-object response")
        return result
