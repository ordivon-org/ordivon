"""Both first ACKs must report the predecessor at their actual PG linearization point."""
from concurrent.futures import ThreadPoolExecutor
from contextlib import nullcontext
from threading import Event
from uuid import uuid4

import psycopg
import pytest
from psycopg.rows import dict_row
from test_attention_single_snapshot_postgres import DSN, _fixture

from ordivon_host_v2.attention_store import AttentionStore
from ordivon_host_v2.collaboration_inputs import MessageInput, MessageKind
from ordivon_host_v2.errors import ConflictError
from ordivon_host_v2.social_store import SocialStore

pytestmark = [
    pytest.mark.skipif(not DSN, reason="ORDIVON_HOST_V2_TEST_DSN not set"),
    pytest.mark.usefixtures("host_test_db_ready"),
]


@pytest.mark.parametrize("domain", ["attention", "topic"])
def test_concurrent_first_ack_returns_actual_predecessor_and_replays_it(domain, monkeypatch):
    assert DSN
    actor, topic, sequence, social = _fixture()
    topic_data = social.resume_topic(topic)["topic"]
    token = uuid4().hex
    posted = social.post_message(
        MessageInput(
            message_ref=f"message:ack:{token}", client_request_id=f"post:ack:{token}",
            space_ref=topic_data["spaceRef"], topic_ref=topic, author_actor_ref=actor,
            message_kind=MessageKind.FINDING, body="second ACK horizon", recorded_at_ms=2,
        )
    )
    lower = 1
    upper = int(posted["sequence"]) if domain == "topic" else 2
    assert int(posted["sequence"]) > sequence >= 1
    assert upper > lower
    table = "attention_cursors" if domain == "attention" else "topic_consumption_cursors"
    store_class = AttentionStore if domain == "attention" else SocialStore
    reached_upsert = Event()
    request1, request2 = f"ack1:{uuid4().hex}", f"ack2:{uuid4().hex}"

    def ack(store, cursor, request):
        if domain == "attention":
            return store.ack(actor, cursor=cursor, client_request_id=request)
        return store.ack_topic_cursor(
            actor_ref=actor, topic_ref=topic, cursor=cursor, client_request_id=request
        )

    with psycopg.connect(DSN, row_factory=dict_row) as first_conn:
        first_conn.execute("SELECT 1")  # outer transaction; inner command uses savepoint
        class FirstWriter(store_class):
            def _connect(self):
                return nullcontext(first_conn)

        first = ack(FirstWriter(DSN), lower, request1)
        assert first["previousCursor"] == 0
        assert first["cursor"] == lower
        # First command/receipt are real, but the outer transaction is still uncommitted.
        original_execute = psycopg.Connection.execute

        def witness_execute(self, query, *args, **kwargs):
            if self is not first_conn and isinstance(query, str) and query.startswith(
                f"INSERT INTO {table}("
            ):
                reached_upsert.set()
            return original_execute(self, query, *args, **kwargs)

        monkeypatch.setattr(psycopg.Connection, "execute", witness_execute)
        with ThreadPoolExecutor(max_workers=1) as worker:
            pending = worker.submit(ack, store_class(DSN), upper, request2)
            try:
                assert reached_upsert.wait(10), "second ACK did not reach native upsert"
            finally:
                first_conn.commit()
            second = pending.result(timeout=15)

    assert second["previousCursor"] == lower
    assert second["cursor"] == upper
    replay = ack(store_class(DSN), upper, request2)
    assert replay["previousCursor"] == lower
    assert replay["cursor"] == upper
    with pytest.raises(ConflictError, match="backwards"):
        ack(store_class(DSN), 0, f"regress:{uuid4().hex}")
    with pytest.raises(ConflictError, match="beyond current"):
        ack(store_class(DSN), 1000000000, f"future:{uuid4().hex}")
    with psycopg.connect(DSN, row_factory=dict_row) as conn:
        if domain == "attention":
            stored = conn.execute(
                "SELECT cursor FROM attention_cursors WHERE actor_ref=%s", (actor,)
            ).fetchone()
        else:
            stored = conn.execute(
                "SELECT cursor FROM topic_consumption_cursors WHERE actor_ref=%s AND topic_ref=%s",
                (actor, topic),
            ).fetchone()
        assert stored["cursor"] == upper
    # Exact historical replay still returns its own original transition.
    first_replay = ack(store_class(DSN), lower, request1)
    assert first_replay["previousCursor"] == 0
    assert first_replay["cursor"] == lower
