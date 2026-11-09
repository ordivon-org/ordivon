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

import pytest
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool

from ordivon_host_v2.attention_store import AttentionStore
from ordivon_host_v2.collaboration_inputs import MessageInput, MessageKind, SpaceInput, TopicInput
from ordivon_host_v2.social_store import SocialStore
from ordivon_host_v2.work_inputs import ActorKind, ActorRefInput
from ordivon_host_v2.work_store import WorkStore

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
    work = WorkStore(DSN)
    social = SocialStore(DSN)
    for ref in (actor, author):
        work.declare_actor(
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
def test_reentry_keeps_delta_and_topic_cursor_in_one_repeatable_read_snapshot(pooled: bool) -> None:
    assert DSN
    actor, topic, sequence, social = _fixture()
    after_delta = Event()
    ack_committed = Event()

    class PauseBeforeTopicCursor(AttentionStore):
        def _delta_in_tx(self, conn, actor_ref, *, after_sequence, limit, max_bytes):
            result = super()._delta_in_tx(
                conn, actor_ref, after_sequence=after_sequence,
                limit=limit, max_bytes=max_bytes,
            )
            if not after_delta.is_set():
                assert any(event["navigationRef"] == topic for event in result["events"])
                after_delta.set()
                assert ack_committed.wait(12), "concurrent Topic cursor ack never committed"
            return result

    pool_context = (
        ConnectionPool(
            DSN, min_size=1, max_size=1, timeout=5,
            kwargs={"row_factory": dict_row}, open=False,
        )
        if pooled else nullcontext(None)
    )
    with pool_context as native_pool:
        reader = PauseBeforeTopicCursor(DSN, pool=native_pool)
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
