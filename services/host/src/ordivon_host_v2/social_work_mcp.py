from __future__ import annotations

from mcp.server import MCPServer

from .attention_store import AttentionStore
from .canonical_json import canonical_digest
from .mcp_attention_tools import register_attention_tools
from .mcp_social_tools import register_social_tools
from .mcp_work_tools import register_work_tools
from .social_store import SocialStore
from .work_store import WorkStore


def _request_id(prefix: str, payload: object) -> str:
    return f"{prefix}:{canonical_digest(payload).removeprefix('sha256:')}"


def register_social_work_tools(mcp: MCPServer, dsn: str) -> None:
    """Register the Social Work Fabric northbound surface.

    Work, Social and Attention each retain their native state ownership. This
    registrar only composes the three owners into the public MCP entry point.
    """

    work = WorkStore(dsn)
    social = SocialStore(dsn)
    attention = AttentionStore(dsn)

    register_work_tools(mcp, work, _request_id)
    register_social_tools(mcp, social, _request_id)
    register_attention_tools(mcp, attention, _request_id)
