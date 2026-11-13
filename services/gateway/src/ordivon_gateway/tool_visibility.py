"""Project one existing MCP SDK tool set into the consumer Core surface.

Use SDK-native MCPServer.remove_tool before publishing the server, rather
than wrapping every Host decorator or maintaining an alternate tool router.
"""

from __future__ import annotations

from mcp.server import MCPServer

from .service import _SOCIAL_WORK_HOST_TOOLS

CORE_PUBLIC_TOOLS = frozenset(
    {
        "artifact.read",
        "attention.ack",
        "attention.delta",
        "capability.search",
        "execution.cancel",
        "execution.get",
        "execution.resolve",
        "execution.submit",
        "message.post",
        "message.search",
        "space.list",
        "topic.list",
        "topic.resume",
        "work.create",
        "work.get",
        "work.list",
        "work.snapshot.commit",
    }
)

# Only the original Gateway metadata Tools are hidden beyond the actual
# canonical Host tool set. The Runtime execution/Artifact recovery tools
# all remain public. No duplicate Host registry or custom MCP protocol.
_NON_CORE_METADATA = frozenset({"system.describe", "capability.describe", "capability.resolve"})


def retain_core_tools(server: MCPServer) -> None:
    """Remove hidden tool dispatch AND discovery using official MCP SDK.

    This runs before the server is returned/published. Tool removals
    do not change any natural Owner function or its authorization target.
    Future tool additions are still protected by the source/SDK surface
    release contract, which fails if the effective public tool set drifts.
    """
    for tool_name in sorted((_SOCIAL_WORK_HOST_TOOLS | _NON_CORE_METADATA) - CORE_PUBLIC_TOOLS):
        server.remove_tool(tool_name)
