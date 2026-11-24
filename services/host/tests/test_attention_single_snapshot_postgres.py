"""Host Attention readbacks must derive from one PostgreSQL MVCC snapshot.

Pausing after delta materialization gives a real concurrent writer a chance
to advance Topic cursor. Re-entry must still present the prior cursor from
the *same* REPEATABLE READ snapshot as the event horizon.
"""
from __future__ import annotations

import os
from concurrent.futures import ThreadPoolExecutor
from contextlib import nullcontext
from threading import Event
from uuid import uuid4

import psycopg
import pytest
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool

from ordivon_host_v2.attention_delta_queries import AttentionDeltaQueries
from ordivon_host_v2.attention_store import AttentionStore
from ordivon_host_v2.canonical_json import canonical_bytes
from ordivon_host_v2.collaboration_inputs import MessageInput, MessageKind, SpaceInput, TopicInput
from ordivon_host_v2.references.actor_store import ActorReferenceStore
from ordivon_host_v2.social_store import SocialStore
from ordivon_host_v2.work_inputs import ActorKind, ActorRefInput

DSN = os.environ.get("ORDIVON_HOST_V2_TEST_DSN")
pytestmark = [
    pytest.mark.skipif(not DSN, reason="ORDIVON_HOST_V2_TEST_DSN not set"),
    pytest.mark.usefixtures("host_test_db_ready"),
]


def _fixture() -> tuple[str, str, str, SocialStore]:
    assert DSN is not None
    token = uuid4().hex
    actor, author = (f"actor:agent:mvcc:{part}:{token}" for part in ("reader", "writer"))
    space, topic = f"space:mvcc:{token}", f"topic:mvcc:{token}"
    social = SocialStore(DSN)
    for ref in (actor, author):
        ActorReferenceStore(DSN).declare_actor(
            ActorRefInput(actor_ref=ref, actor_kind=ActorKind.AGENT),
            client_request_id=f"declare:{ref}",
        )
    social.create_space(
        SpaceInput(space_ref=space, purpose="snapshot refinement", actor_ref=actor),
        client_request_id=f"space:{space}",
    )
    social.create_topic(
        TopicInput(topic_ref=topic, space_ref=space, title="mvcc", actor_ref=actor),
        client_request_id=f"topic:{topic}",
    )
    AttentionStore(DSN).follow(
        actor_ref=actor, target_kind="topic", target_ref=topic,
        client_request_id=f"follow:{token}",
    )
    posted = social.post_message(
        MessageInput(
            message_ref=f"message:mvcc:{token}", client_request_id=f"post:{token}",
            space_ref=space, topic_ref=topic, author_actor_ref=author,
            message_kind=MessageKind.FINDING, body="MVCC fence",
            recorded_at_ms=1,
        )
    )
    return actor, topic, int(posted["sequence"]), social


@pytest.mark.parametrize("pooled", [False, True])
def test_reentry_keeps_delta_and_topic_cursor_in_one_repeatable_read_snapshot(pooled: bool, monkeypatch) -> None:
    assert DSN
    actor, topic, sequence, social = _fixture()
    after_delta = Event()
    ack_committed = Event()

    original_delta = AttentionDeltaQueries._delta_in_tx

    def pause_before_topic_cursor(self, conn, actor_ref, *, after_sequence, limit, max_bytes):
        result = original_delta(self,
            conn, actor_ref, after_sequence=after_sequence,
            limit=limit, max_bytes=max_bytes,
        )
        if not after_delta.is_set():
            assert any(event["navigationRef"] == topic for event in result["events"])
            after_delta.set()
            assert ack_committed.wait(12), "concurrent Topic cursor ack never committed"
        return result

    monkeypatch.setattr(AttentionDeltaQueries, "_delta_in_tx", pause_before_topic_cursor)

    pool_context = (
        ConnectionPool(
            DSN, min_size=1, max_size=1, timeout=5,
            kwargs={"row_factory": dict_row}, open=False,
        )
        if pooled else nullcontext(None)
    )
    with pool_context as native_pool:
        reader = AttentionStore(DSN, pool=native_pool)
        with ThreadPoolExecutor(max_workers=1) as worker:
            pending = worker.submit(reader.reentry, actor, after_sequence=0, limit=100)
            assert after_delta.wait(12), "re-entry did not reach delta projection"
            try:
                social.ack_topic_cursor(
                    actor_ref=actor, topic_ref=topic, cursor=sequence,
                    client_request_id=f"topic-ack-mvcc:{uuid4().hex}",
                )
            finally:
                ack_committed.set()
            earlier = pending.result(timeout=15)

    topic_item = next(
        item for item in earlier["items"]
        if item["navigationKind"] == "topic" and item["navigationRef"] == topic
    )
    # This cursor may have advanced in another transaction, but the
    # re-entry projection must not mix that later state into its earlier snapshot.
    assert topic_item["resumeAfterSequence"] == 0
    assert earlier["snapshotHighSequence"] >= topic_item["latestChangeSequence"]

    later = AttentionStore(DSN).reentry(actor, after_sequence=0, limit=100)
    later_topic = next(item for item in later["items"] if item["navigationRef"] == topic)
    assert later_topic["resumeAfterSequence"] == sequence


def test_get_delta_and_reentry_each_use_one_database_checkout() -> None:
    assert DSN
    actor, topic, _, _ = _fixture()

    class CountingCheckout(AttentionStore):
        count = 0

        def _connect(self):
            self.count += 1
            return super()._connect()

    reader = CountingCheckout(DSN)
    assert reader.get(actor)["kind"] == "ordivon.host-attention-delta-r1"
    assert reader.count == 1
    assert reader.delta(actor, after_sequence=0)["events"]
    assert reader.count == 2
    assert any(item["navigationRef"] == topic for item in reader.reentry(actor)["items"])
    assert reader.count == 3


def test_reentry_byte_fit_does_not_rerun_delta_sql(monkeypatch) -> None:
    """100 legal delta-shaped rows fit 16 KiB, but their grouped re-entry page does not."""
    assert DSN
    actor, _, _, _ = _fixture()
    events = [
        {
            "changeSequence": i + 1,
            "eventKind": "message",
            "sourceRef": "m",
            "contextRef": "t",
            "reasons": ["mentioned"],
            "navigationKind": "topic",
            "navigationRef": f"t{i:03d}",
        }
        for i in range(100)
    ]

    calls = 0

    def instrumented_delta(self, conn, actor_ref, *, after_sequence, limit, max_bytes):
        nonlocal calls
        calls += 1
        return {
            "schemaVersion": 1,
            "kind": "ordivon.host-attention-delta-r1",
            "actorRef": actor_ref,
            "afterSequence": after_sequence,
            "snapshotHighSequence": 100,
            "events": events,
            "hasMore": False,
            "nextAfterSequence": 100,
            "rankingApplied": False,
            "truthBoundary": "rebuildable navigation",
        }

    monkeypatch.setattr(AttentionDeltaQueries, "_delta_in_tx", instrumented_delta)
    reader = AttentionStore(DSN)
    result = reader.reentry(actor, after_sequence=0, limit=100, max_bytes=16_384)
    assert calls == 1
    assert 0 < result["rawEventCount"] < len(events)
    assert result["hasMore"] is True
    assert result["nextAfterSequence"] == result["rawEventCount"]
    assert len(canonical_bytes(result)) <= 16_384


def test_benchmark_sql_override_reaches_actual_store_queries(monkeypatch) -> None:
    """Falsify a detached benchmark injection using real native SQL execution."""
    assert DSN
    actor, _, _, _ = _fixture()
    from pathlib import Path

    from ordivon_host_v2 import attention_delta_queries

    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[1] / "tools"))
    from bench_attention_compare_r44 import extract

    store = AttentionStore(DSN)
    original = attention_delta_queries.ATTENTION_DELTA_SQL
    # extract() must actually change the query that runs; a dead module
    # attribute would silently yield a valid baseline page instead.
    monkeypatch.setattr(attention_delta_queries, "ATTENTION_DELTA_SQL", original)
    invalid = "SELECT * FROM host_benchmark_nonexistent_relation"
    with pytest.raises(psycopg.errors.UndefinedTable):
        extract(invalid, store, actor, after=0, limit=10)
    with pytest.raises(psycopg.errors.UndefinedTable):
        store.reentry(actor, after_sequence=0, limit=10)
    assert extract(original, store, actor, after=0, limit=10)["events"]
    assert store.reentry(actor, after_sequence=0, limit=10)["items"]
