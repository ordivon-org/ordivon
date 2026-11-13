"""Process-start public MCP projection using the official MCP SDK.

Natural Owner Tools are registered unmodified. At server lifespan admission,
the official MCPServer.list_tools/remove_tool pair projects one static
consumer profile. New registrations are hidden by default, not left visible.
"""

from __future__ import annotations

from mcp.server import MCPServer

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

# Actual task-space-reentry Skill consumers need space.get/attention.reentry.
# First-time collaboration consumers need Actor/Space/Topic bootstrap.
# Neither group is silently loaded into the 17-tool default Core.
COLLABORATION_PUBLIC_TOOLS = CORE_PUBLIC_TOOLS | frozenset(
    {"actor.declare", "space.create", "space.get", "topic.create", "attention.reentry"}
)

PUBLIC_TOOL_PROFILES: dict[str, frozenset[str]] = {
    "core": CORE_PUBLIC_TOOLS,
    "collaboration": COLLABORATION_PUBLIC_TOOLS,
}


async def project_registered_tools(server: MCPServer, visible_tools: frozenset[str]) -> None:
    """One SDK-native fail-closed projection before the service accepts calls.

    New registered tools not explicitly in the selected public projection
    are removed as well. A missing required public tool refuses startup.
    This must run exactly once during MCPServer lifespan startup, before
    HTTP/session requests; profiles must not vary per request.
    """
    registered_tools = {tool.name for tool in await server.list_tools()}
    missing = visible_tools - registered_tools
    if missing:
        raise RuntimeError(
            "Gateway public profile lacks registered tools: " + ", ".join(sorted(missing))
        )
    for tool_name in sorted(registered_tools - visible_tools):
        server.remove_tool(tool_name)
