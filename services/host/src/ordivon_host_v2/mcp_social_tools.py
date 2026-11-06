from __future__ import annotations

from collections.abc import Callable

from mcp.server import MCPServer

from .mcp_message_tools import register_message_tools
from .mcp_space_tools import register_space_tools
from .mcp_topic_tools import register_topic_tools
from .social_store import SocialStore


def register_social_tools(
    mcp: MCPServer,
    social: SocialStore,
    request_id: Callable[[str, object], str],
) -> None:
    """Compose native Space, Topic, and Message tools without a second state owner."""
    register_space_tools(mcp, social, request_id)
    register_topic_tools(mcp, social, request_id)
    register_message_tools(mcp, social, request_id)
