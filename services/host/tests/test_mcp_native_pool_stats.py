"""Read-only Psycopg pool diagnostics: official SDK, native stats, no DB I/O."""

from __future__ import annotations

import asyncio
import os

import pytest
from mcp import Client
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool

from ordivon_host_v2.mcp_server import build_server

DSN = os.environ.get("ORDIVON_HOST_V2_TEST_DSN")


def test_direct_mode_does_not_need_database_connection_or_artificial_zero_pool(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def forbid(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("a pool diagnostic must never open a database")

    monkeypatch.setattr("psycopg.connect", forbid)

    async def scenario() -> None:
        async with Client(build_server("postgresql://invalid.invalid/never")) as client:
            listed = await client.list_tools()
            assert "host.pool.stats" in {tool.name for tool in listed.tools}
            result = await client.call_tool("host.pool.stats", {})
            assert result.is_error is False
            payload = result.structured_content
            assert payload is not None
            assert payload["connectionMode"] == "direct"
            assert payload["stats"] is None
            assert payload["kind"] == "ordivon.host-pool-stats"
            assert payload["observedAtMs"] > 0

    asyncio.run(scenario())


def test_native_stats_are_bounded_and_zero_filled_without_leaking_connection_info() -> None:
    class FakePool:
        calls = 0

        def get_stats(self) -> dict[str, int]:
            self.calls += 1
            return {
                "pool_min": 1, "pool_max": 8, "pool_size": 3,
                "pool_available": 2, "requests_num": 17,
                "requests_queued": 4, "requests_wait_ms": 51,
                "requests_waiting": 1, "requests_errors": 2,
                "connections_errors": 1,
                "conninfo": "not-an-int-but-never-emitted",
                "future_counter": 999,
            }

    pool = FakePool()

    async def scenario() -> None:
        async with Client(
            build_server("postgresql://secret-user:secret-password@private/host",pool=pool)
        ) as client:
            result = await client.call_tool("host.pool.stats", {})
            assert result.is_error is False
            payload = result.structured_content
            assert payload is not None
            assert payload["connectionMode"] == "pooled"
            stats = payload["stats"]
            assert stats["pool_size"] == 3
            assert stats["pool_available"] == 2
            assert stats["requests_errors"] == 2
            assert stats["usage_ms"] == 0
            assert stats["connections_lost"] == 0
            assert len(stats) == 15
            assert all(type(value) is int for value in stats.values())
            assert "secret-password" not in str(payload)
            assert "conninfo" not in str(payload)
            assert "future_counter" not in str(payload)

    asyncio.run(scenario())
    assert pool.calls == 1


@pytest.mark.skipif(not DSN, reason="ORDIVON_HOST_V2_TEST_DSN not set")
@pytest.mark.usefixtures("host_test_db_ready")
def test_real_pg18_pool_stats_track_checkout_and_return_without_reset() -> None:
    assert DSN is not None
    with ConnectionPool(
        DSN, min_size=1, max_size=1, kwargs={"row_factory":dict_row},
        timeout=5, max_waiting=4, open=False,
    ) as pool:
        pool.wait(timeout=8)

        async def scenario() -> None:
            async with Client(build_server(DSN,pool=pool)) as client:
                first=(await client.call_tool("host.pool.stats",{})).structured_content
                assert first is not None
                assert first["stats"]["pool_max"]==1
                assert first["stats"]["requests_waiting"]==0
                with pool.connection() as conn:
                    assert conn.execute("SELECT 1 AS value").fetchone()["value"]==1
                second=(await client.call_tool("host.pool.stats",{})).structured_content
                assert second is not None
                assert second["stats"]["requests_num"] >= first["stats"]["requests_num"]+1
                assert second["stats"]["pool_available"]==1
                assert second["stats"]["connections_num"]==1

        asyncio.run(scenario())
