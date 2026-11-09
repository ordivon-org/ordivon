"""Read-only Psycopg native pool diagnostics; no new telemetry ownership."""

from __future__ import annotations

from time import time_ns

from psycopg_pool import ConnectionPool

from .contracts import HostNativePoolStatsWire, HostPoolStatsResponse

# Psycopg get_stats() may omit zeroes or add new keys in future versions.
# Export only documented counters; never expose conninfo, DSN or pool internals.

def pool_stats_response(pool: ConnectionPool | None) -> HostPoolStatsResponse:
    if pool is None:
        return {
            "schemaVersion": 1,
            "kind": "ordivon.host-pool-stats",
            "observedAtMs": time_ns() // 1_000_000,
            "connectionMode": "direct",
            "stats": None,
            "truthBoundary": "Local Host process only; no PostgreSQL cluster, cross-process history or domain truth",
        }
    native = pool.get_stats()
    stats: HostNativePoolStatsWire = {
        "pool_min": native.get("pool_min", 0),
        "pool_max": native.get("pool_max", 0),
        "pool_size": native.get("pool_size", 0),
        "pool_available": native.get("pool_available", 0),
        "requests_waiting": native.get("requests_waiting", 0),
        "usage_ms": native.get("usage_ms", 0),
        "requests_num": native.get("requests_num", 0),
        "requests_queued": native.get("requests_queued", 0),
        "requests_wait_ms": native.get("requests_wait_ms", 0),
        "requests_errors": native.get("requests_errors", 0),
        "returns_bad": native.get("returns_bad", 0),
        "connections_num": native.get("connections_num", 0),
        "connections_ms": native.get("connections_ms", 0),
        "connections_errors": native.get("connections_errors", 0),
        "connections_lost": native.get("connections_lost", 0),
    }
    return {
        "schemaVersion": 1,
        "kind": "ordivon.host-pool-stats",
        "observedAtMs": time_ns() // 1_000_000,
        "connectionMode": "pooled",
        "stats": stats,
        "truthBoundary": "Local Host process only; native cumulative counters reset on process restart; no domain truth",
    }
