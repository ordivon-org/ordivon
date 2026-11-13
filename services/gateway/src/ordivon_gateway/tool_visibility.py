"""Static public MCP projection over existing natural-owner tool implementations.

Only tool discovery/registration changes. This is not a policy decision,
second capability catalog, Tool invocation router, or private MCP protocol.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from mcp.server import MCPServer

CORE_PUBLIC_TOOLS = frozenset(
    {
        "capability.search",
        "work.create",
        "work.get",
        "work.list",
        "work.snapshot.commit",
        "space.list",
        "topic.list",
        "topic.resume",
        "message.search",
        "message.post",
        "attention.delta",
        "attention.ack",
        "execution.submit",
        "execution.resolve",
        "execution.get",
        "execution.cancel",
        "artifact.read",
    }
)


def expose_tool(
    server: MCPServer, name: str, visible_tools: frozenset[str] | None
) -> Callable[[Any], Any]:
    """Register only explicitly selected public tools; never register hidden names."""
    if visible_tools is None or name in visible_tools:
        return server.tool(name=name)
    return lambda function: function
