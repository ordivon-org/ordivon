"""Native consumer contract: Work and Attention reads are one PG read-only cut.

No private query helper, source filename, SQL literal inventory, or mock DB is
the oracle. Inspect actual server transaction settings and public results.
"""

from __future__ import annotations

import os
from contextlib import nullcontext
from uuid import uuid4

import psycopg
import pytest
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool

from ordivon_host_v2.attention_store import AttentionStore
from ordivon_host_v2.collaboration_inputs import MessageInput, SpaceInput, TopicInput
from ordivon_host_v2.errors import ActorRefNotFound, WorkNotFound
from ordivon_host_v2.references.actor_store import ActorReferenceStore
from ordivon_host_v2.social_store import SocialStore
from ordivon_host_v2.work_inputs import ActorKind, ActorRefInput, WorkCreateInput, WorkSnapshotInput
from ordivon_host_v2.work_store import WorkStore

DSN = os.environ.get("ORDIVON_HOST_V2_TEST_DSN")
pytestmark = [
    pytest.mark.skipif(not DSN, reason="requires native Host test PostgreSQL"),
    pytest.mark.usefixtures("host_test_db_ready"),
]


@pytest.fixture
def seed():
    assert DSN
    uid = uuid4().hex
    reader, author = f"actor:agent:read-contract:{uid}", f"actor:agent:writer-contract:{uid}"
    space, topic, work = (f"{kind}:read-contract:{uid}" for kind in ("space", "topic", "work"))
    actors = ActorReferenceStore(DSN)
    for ref in (reader, author):
        actors.declare_actor(
            ActorRefInput(actor_ref=ref, actor_kind=ActorKind.AGENT),
            client_request_id=f"actor:{ref}",
        )
    social = SocialStore(DSN)
    social.create_space(
        SpaceInput(space_ref=space, purpose="read contract", actor_ref=author),
        client_request_id=f"space:{uid}",
    )
    social.create_topic(
        TopicInput(topic_ref=topic, space_ref=space, title="contract", actor_ref=author),
        client_request_id=f"topic:{uid}",
    )
    AttentionStore(DSN).follow(
        actor_ref=reader, target_kind="topic", target_ref=topic, client_request_id=f"follow:{uid}"
    )
    social.post_message(
        MessageInput(
            message_ref=f"message:read-contract:{uid}",
            client_request_id=f"post:{uid}",
            space_ref=space,
            topic_ref=topic,
            author_actor_ref=author,
            body="read contract evidence",
            recorded_at_ms=1,
        )
    )
    created = WorkStore(DSN).create_work(
        WorkCreateInput(
            work_ref=work,
            kind="investigation",
            actor_ref=author,
            initial_snapshot=WorkSnapshotInput(objective="read contract", frontier="seed"),
        ),
        client_request_id=f"work:{uid}",
    )
    return reader, topic, work, created


def observe_native_reads(monkeypatch, *, omit_fence=False):
    """Observe the real database before any subsequent public read statement."""
    execute = psycopg.Connection.execute
    observations = []

    def observed(conn, query, *args, **kwargs):
        # Negative control only: remove the real transaction fence without
        # modifying production source or mocking the database response.
        if omit_fence and isinstance(query, str) and query.startswith("SET TRANSACTION"):
            result = execute(conn, "SELECT 1")
        else:
            result = execute(conn, query, *args, **kwargs)
        isolation = execute(conn, "SHOW transaction_isolation").fetchone()["transaction_isolation"]
        readonly = execute(conn, "SHOW transaction_read_only").fetchone()["transaction_read_only"]
        observations.append((id(conn), isolation, readonly))
        assert (isolation, readonly) == ("repeatable read", "on"), "native read fence absent"
        return result

    monkeypatch.setattr(psycopg.Connection, "execute", observed)
    return observations


@pytest.mark.parametrize("pooled", [False, True])
def test_public_work_attention_reads_have_native_readonly_cut(seed, pooled, monkeypatch):
    reader, topic, work, created = seed
    pool = (
        ConnectionPool(
            DSN, min_size=1, max_size=1, timeout=5, kwargs={"row_factory": dict_row}, open=False
        )
        if pooled
        else nullcontext(None)
    )
    with pool as native_pool:
        work_store = WorkStore(DSN, pool=native_pool)
        attention = AttentionStore(DSN, pool=native_pool)
        observations = observe_native_reads(monkeypatch)
        checkouts = []
        if native_pool is None:
            original = psycopg.connect

            def counted_connect(*args, **kwargs):
                checkouts.append("direct")
                return original(*args, **kwargs)

            monkeypatch.setattr(psycopg, "connect", counted_connect)
        else:
            original = native_pool.connection

            def counted_connection(*args, **kwargs):
                checkouts.append("pooled")
                return original(*args, **kwargs)

            monkeypatch.setattr(native_pool, "connection", counted_connection)

        def check(call, predicate):
            observations.clear()
            checkouts.clear()
            result = call()
            assert predicate(result)
            assert observations
            assert len(checkouts) == 1
            assert len({row[0] for row in observations}) == 1

        check(
            lambda: work_store.get_work(work),
            lambda r: r["snapshotDigest"] == created["snapshotDigest"],
        )
        check(lambda: work_store.get_work(work, revision=1), lambda r: r["revision"] == 1)
        check(
            lambda: work_store.list_works(limit=200),
            lambda r: any(w["workRef"] == work for w in r["works"]),
        )
        check(
            lambda: attention.list_subscriptions(reader),
            lambda r: any(s["targetRef"] == topic for s in r["subscriptions"]),
        )
        check(
            lambda: attention.get(reader),
            lambda r: any(e["navigationRef"] == topic for e in r["events"]),
        )
        check(
            lambda: attention.delta(reader, after_sequence=0),
            lambda r: any(e["navigationRef"] == topic for e in r["events"]),
        )
        check(
            lambda: attention.reentry(reader),
            lambda r: any(i["navigationRef"] == topic for i in r["items"]),
        )
        for call, error in (
            (lambda: work_store.get_work(work + ":missing"), WorkNotFound),
            (lambda: attention.get(reader + ":missing"), ActorRefNotFound),
            (lambda: attention.list_subscriptions(reader + ":missing"), ActorRefNotFound),
        ):
            observations.clear()
            checkouts.clear()
            with pytest.raises(error):
                call()
            assert observations
            assert len(checkouts) == 1
            assert len({row[0] for row in observations}) == 1
        # A rejected read must return its connection to a usable state.
        check(
            lambda: work_store.get_work(work),
            lambda r: r["snapshotDigest"] == created["snapshotDigest"],
        )


def test_native_probe_detects_missing_transaction_fence(seed, monkeypatch):
    _, _, work, _ = seed
    observe_native_reads(monkeypatch, omit_fence=True)
    with pytest.raises(AssertionError, match="native read fence absent"):
        WorkStore(DSN).get_work(work)


def test_postgres_rejects_indirect_write_on_public_read_path(seed, monkeypatch):
    _, _, work, created = seed
    execute = psycopg.Connection.execute
    injected = False

    def observed(conn, query, *args, **kwargs):
        nonlocal injected
        result = execute(conn, query, *args, **kwargs)
        if not injected:
            injected = True
            # The no-op statement is hidden from the source-literal test's
            # read modules. PostgreSQL must reject the operation itself.
            execute(conn, "UPDATE works SET current_revision=current_revision WHERE false")
        return result

    with monkeypatch.context() as patch:
        patch.setattr(psycopg.Connection, "execute", observed)
        with pytest.raises(psycopg.errors.ReadOnlySqlTransaction):
            WorkStore(DSN).get_work(work)
    assert injected
    assert WorkStore(DSN).get_work(work)["snapshotDigest"] == created["snapshotDigest"]
