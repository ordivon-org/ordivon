from __future__ import annotations

import os
from importlib.metadata import version as package_version
from typing import Literal

from mcp.server import MCPServer
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool

from .contracts import HostPoolStatsResponse, HostStatusResponse
from .http_transport import serve_host_http
from .mcp_tool_registration import register_social_work_tools
from .native_pool_observability import pool_stats_response
from .service import HostV2


def build_server(dsn: str | None = None, *, pool: ConnectionPool | None = None) -> MCPServer:
    effective_dsn = dsn or os.environ["ORDIVON_HOST_V2_DSN"]
    service = HostV2(effective_dsn, pool=pool)
    mcp = MCPServer("ordivon-host-v2", version=package_version("ordivon-host-v2"))

    @mcp.tool(name="host.status")
    def host_status(
        detail: Literal["summary", "integrity", "history"] = "summary",
    ) -> HostStatusResponse:
        """Report PostgreSQL-native Social Work Fabric authority and bounded integrity."""
        return service.status(detail=detail)

    @mcp.tool(name="host.pool.stats")
    def host_pool_stats() -> HostPoolStatsResponse:
        """Inspect native Psycopg pool gauges and process-scoped cumulative counters."""
        return pool_stats_response(pool)

    register_social_work_tools(mcp, effective_dsn, pool=pool)
    return mcp


def main() -> None:
    transport = os.environ.get("ORDIVON_HOST_V2_TRANSPORT", "stdio")
    pool_size = int(os.environ.get("ORDIVON_HOST_V2_PG_POOL_MAX_SIZE", "8"))
    if not 1 <= pool_size <= 64:
        raise ValueError("ORDIVON_HOST_V2_PG_POOL_MAX_SIZE must be in [1,64]")
    dsn = os.environ["ORDIVON_HOST_V2_DSN"]
    with ConnectionPool(
        conninfo=dsn,
        min_size=1,
        max_size=pool_size,
        kwargs={"row_factory": dict_row},
        timeout=5.0,
        max_waiting=64,
        open=False,
    ) as pool:
        # Both serving transports must require the actual migrated authority
        # before serving any tool. Keep build_server() usable for offline SDK
        # contract discovery; it is not the process entrypoint.
        HostV2(dsn, pool=pool).initialize()
        server = build_server(dsn, pool=pool)
        if transport == "stdio":
            server.run()
            return
        if transport != "streamable-http":
            raise RuntimeError("ORDIVON_HOST_V2_TRANSPORT must be stdio or streamable-http")
        serve_host_http(server)
