"""Native Psycopg pool: lifecycle, bound, rollback and full MCP consumers.

The PG checks run only under the already-existing disposable PG 18 queue
launcher; no production DSN is admitted by that test harness.
"""
from __future__ import annotations

import asyncio
import os
from uuid import uuid4

import pytest
from mcp import Client
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool, PoolTimeout

from ordivon_host_v2.attention_store import AttentionStore
from ordivon_host_v2.mcp_server import build_server
from ordivon_host_v2.service import HostV2
from ordivon_host_v2.social_store import SocialStore
from ordivon_host_v2.work_store import WorkStore

DSN = os.environ.get("ORDIVON_HOST_V2_TEST_DSN")


def test_pool_is_injected_into_each_native_owner_without_opening_database() -> None:
    class FakePool:
        def connection(self) -> object:
            return self

    fake_pool = FakePool()
    for store in (HostV2, WorkStore, SocialStore, AttentionStore):
        assert store("postgresql://invalid.invalid/never", pool=fake_pool)._connect() is fake_pool


@pytest.mark.skipif(not DSN, reason="ORDIVON_HOST_V2_TEST_DSN not set")
@pytest.mark.usefixtures("host_test_db_ready")
def test_pool_single_backend_rollback_and_bounded_wait() -> None:
    assert DSN
    with ConnectionPool(
        DSN, min_size=1, max_size=1, kwargs={"row_factory": dict_row},
        timeout=1.0, max_waiting=1, open=False,
    ) as pool:
        # An exhausted pool fails in bounded time; it must not silently open
        # another PostgreSQL connection beyond its configured limit.
        with pool.connection() as conn:
            first_pid = conn.execute("SELECT pg_backend_pid() AS pid").fetchone()["pid"]
            with pytest.raises(PoolTimeout):
                with pool.connection(timeout=0.1):
                    pytest.fail("pool admitted a second connection")
        # The same backend is returned, not closed on every command.
        with pool.connection() as conn:
            assert conn.execute("SELECT pg_backend_pid() AS pid").fetchone()["pid"] == first_pid
        # A failed command is rolled back before the borrowed session is reused.
        with pytest.raises(RuntimeError, match="intentional rollback"):
            with pool.connection() as conn, conn.transaction():
                conn.execute("CREATE TEMP TABLE host_pool_rollback_guard(v int) ON COMMIT DROP")
                raise RuntimeError("intentional rollback")
        with pool.connection() as conn:
            assert conn.execute(
                "SELECT to_regclass('pg_temp.host_pool_rollback_guard') AS marker"
            ).fetchone()["marker"] is None
        assert pool.get_stats()["connections_num"] == 1


@pytest.mark.skipif(not DSN, reason="ORDIVON_HOST_V2_TEST_DSN not set")
@pytest.mark.usefixtures("host_test_db_ready")
def test_one_pool_serves_mcp_work_social_attention_and_status() -> None:
    assert DSN
    token = uuid4().hex
    actor = "actor:agent:pool:" + token
    work = "work:pool:" + token
    space = "space:pool:" + token
    topic = "topic:pool:" + token

    async def call(client: Client, name: str, args: dict[str, object]) -> dict[str, object]:
        result = await client.call_tool(name, args)
        assert not result.is_error, (name, result)
        assert result.structured_content is not None
        return result.structured_content

    async def exercise(pool: ConnectionPool) -> None:
        async with Client(build_server(DSN, pool=pool), raise_exceptions=True) as client:
            await call(client, "actor.declare", {"actorRef": actor, "actorKind": "agent"})
            created = await call(
                client, "work.create",
                {
                    "workRef": work,
                    "workKind": "qualification",
                    "actorRef": actor,
                    "initialSnapshot": {
                        "objective": "native pool PG consumer",
                        "frontier": "begin",
                        "established": [],
                        "unresolved": [],
                        "rejected": [],
                        "constraints": [],
                        "nextActions": [],
                        "referenceRefs": [],
                    },
                },
            )
            assert created["revision"] == 1
            await call(
                client, "space.create",
                {"spaceRef": space, "purpose": "pool verification",
                 "actorRef": actor, "subjectRefs": [work]},
            )
            await call(
                client, "topic.create",
                {"topicRef": topic, "spaceRef": space, "title": "verification", "actorRef": actor},
            )
            await call(
                client, "subscription.follow",
                {"actorRef": actor, "targetKind": "topic", "targetRef": topic},
            )
            posted = await call(
                client, "message.post",
                {"messageRef": "message:pool:" + token, "spaceRef": space,
                 "topicRef": topic, "authorActorRef": actor, "recordedAtMs": 1,
                 "messageKind": "finding", "body": "pool tested"},
            )
            assert posted["body"] == "pool tested"
            changes = await call(
                client, "attention.delta",
                {"actorRef": actor, "afterSequence": 0, "limit": 100},
            )
            assert any(row["sourceRef"] == posted["messageRef"] for row in changes["events"])
            result = await call(client, "host.status", {"detail": "integrity"})
            assert result["doctor"]["healthy"] is True
            assert result["authority"]["journalSchema"] == 13

    with ConnectionPool(
        DSN, min_size=1, max_size=1, kwargs={"row_factory": dict_row},
        timeout=5.0, max_waiting=8, open=False,
    ) as pool:
        asyncio.run(exercise(pool))
        stats = pool.get_stats()
        assert stats["connections_num"] == 1
        assert stats["requests_num"] >= 7


@pytest.mark.parametrize("transport", ["stdio", "streamable-http"])
def test_mcp_process_owns_and_closes_pool(monkeypatch: pytest.MonkeyPatch, transport: str) -> None:
    """Native pool lifecycle is fenced by server.run for either transport."""
    from ordivon_host_v2 import mcp_server

    events: list[object] = []

    class FakePool:
        def __init__(self, **kwargs: object) -> None:
            events.append(("configured", kwargs))

        def __enter__(self) -> FakePool:
            events.append("open")
            return self

        def __exit__(self, *_args: object) -> None:
            events.append("close")

    class FakeServer:
        def run(self, **kwargs: object) -> None:
            events.append(("run", kwargs))

    def fake_build_server(dsn: str, *, pool: FakePool) -> FakeServer:
        assert dsn == "postgresql://invalid.invalid/unused"
        events.append(("bound", pool))
        return FakeServer()

    monkeypatch.setenv("ORDIVON_HOST_V2_DSN", "postgresql://invalid.invalid/unused")
    monkeypatch.setenv("ORDIVON_HOST_V2_TRANSPORT", transport)
    monkeypatch.setenv("ORDIVON_HOST_V2_PG_POOL_MAX_SIZE", "2")
    monkeypatch.setattr(mcp_server, "ConnectionPool", FakePool)
    monkeypatch.setattr(mcp_server, "build_server", fake_build_server)
    mcp_server.main()

    assert events[1] == "open"
    assert events[2][0] == "bound"
    assert events[3][0] == "run"
    assert events[4] == "close"
    assert events[0][1]["max_size"] == 2
    assert events[0][1]["open"] is False
    if transport == "streamable-http":
        assert events[3][1]["transport"] == "streamable-http"


@pytest.mark.parametrize("invalid", ["0", "-1", "65"])
def test_pool_size_outside_bound_rejected_before_any_connection(
    monkeypatch: pytest.MonkeyPatch, invalid: str,
) -> None:
    from ordivon_host_v2 import mcp_server

    monkeypatch.setenv("ORDIVON_HOST_V2_DSN", "postgresql://invalid.invalid/unused")
    monkeypatch.setenv("ORDIVON_HOST_V2_PG_POOL_MAX_SIZE", invalid)
    with pytest.raises(ValueError, match="POOL_MAX_SIZE"):
        mcp_server.main()
