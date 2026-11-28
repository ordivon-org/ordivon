from __future__ import annotations

from mcp.server import MCPServer
from psycopg_pool import ConnectionPool

from .attention_store import AttentionStore
from .canonical_json import canonical_digest
from .mcp_actor_tools import register_actor_tools
from .mcp_attention_tools import register_attention_tools
from .mcp_social_tools import register_social_tools
from .mcp_work_tools import register_work_tools
from .references.actor_store import ActorReferenceStore
from .social_store import SocialStore
from .work_store import WorkStore


def _request_id(prefix: str, payload: object) -> str:
    return f"{prefix}:{canonical_digest(payload).removeprefix('sha256:')}"


def register_social_work_tools(
    mcp: MCPServer,
    dsn: str,
    *,
    pool: ConnectionPool | None = None,
    compact_work_receipts: bool = False,
) -> None:
    """Register the Social Work Fabric northbound surface.

    Work, Social and Attention each retain their native state ownership. This
    registrar only composes the three owners into the public MCP entry point.
    """

    actors = ActorReferenceStore(dsn, pool=pool)
    work = WorkStore(dsn, pool=pool, compact_work_receipts=compact_work_receipts)
    social = SocialStore(dsn, pool=pool)
    attention = AttentionStore(dsn, pool=pool)

    register_actor_tools(mcp, actors, _request_id)
    register_work_tools(mcp, work, _request_id)
    register_social_tools(mcp, social, _request_id)
    register_attention_tools(mcp, attention, _request_id)
