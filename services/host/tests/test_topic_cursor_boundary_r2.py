"""Independent Topic cursor model against native PG, not an SQL-string simulator."""

from __future__ import annotations

import os
from uuid import uuid4

import psycopg
import pytest
from hypothesis import example, given, settings
from hypothesis import strategies as st
from psycopg.rows import dict_row

from ordivon_host_v2.attention_store import AttentionStore
from ordivon_host_v2.collaboration_inputs import MessageInput, SpaceInput, TopicInput
from ordivon_host_v2.errors import ConflictError
from ordivon_host_v2.references.actor_store import ActorReferenceStore
from ordivon_host_v2.social_store import SocialStore
from ordivon_host_v2.topic_cursor_records import list_topic_cursors_in_tx
from ordivon_host_v2.work_inputs import ActorKind, ActorRefInput

DSN = os.environ.get("ORDIVON_HOST_V2_TEST_DSN")
native_db = pytest.mark.skipif(not DSN, reason="requires native disposable PostgreSQL")


def seed():
    assert DSN
    uid = uuid4().hex
    actors = [f"actor:agent:cursor-model:{uid}:{i}" for i in range(2)]
    topics = [f"topic:cursor-model:{uid}:{i}" for i in range(2)]
    space = f"space:cursor-model:{uid}"
    social, attention = SocialStore(DSN), AttentionStore(DSN)
    for actor in actors:
        ActorReferenceStore(DSN).declare_actor(
            ActorRefInput(actor_ref=actor, actor_kind=ActorKind.AGENT),
            client_request_id=f"declare:{actor}",
        )
    social.create_space(
        SpaceInput(space_ref=space, purpose="cursor model", actor_ref=actors[0]),
        client_request_id=f"space:{uid}",
    )
    highs = []
    for i, topic in enumerate(topics):
        social.create_topic(
            TopicInput(topic_ref=topic, space_ref=space, title="cursor model", actor_ref=actors[0]),
            client_request_id=f"topic:{topic}",
        )
        for actor in actors:
            attention.follow(
                actor_ref=actor,
                target_kind="topic",
                target_ref=topic,
                client_request_id=f"follow:{actor}:{topic}",
            )
        posted = social.post_message(
            MessageInput(
                message_ref=f"message:cursor-model:{uid}:{i}",
                client_request_id=f"post:{uid}:{i}",
                space_ref=space,
                topic_ref=topic,
                author_actor_ref=actors[0],
                body="cursor model evidence",
                recorded_at_ms=i,
            )
        )
        highs.append(posted["sequence"])
    return actors, topics, highs, social, attention


@pytest.mark.parametrize("value", [True, 3.0, -1, 2**53])
def test_invalid_type_or_coordinate_rejected_before_connection(value, monkeypatch):
    def forbidden(*args, **kwargs):
        pytest.fail("invalid cursor reached database checkout")

    monkeypatch.setattr(psycopg, "connect", forbidden)
    with pytest.raises(ValueError):
        SocialStore("postgresql://unreachable").ack_topic_cursor(
            actor_ref="actor:a", topic_ref="topic:a", cursor=value, client_request_id="bad:cursor"
        )


def test_empty_bulk_cursor_lookup_needs_no_database():
    class Forbidden:
        def execute(self, *args, **kwargs):
            pytest.fail("empty bulk cursor lookup must not issue SQL")

    assert list_topic_cursors_in_tx(Forbidden(), actor_ref="actor:a", topic_refs=[]) == {}


@native_db
@pytest.mark.usefixtures("host_test_db_ready")
def test_cursor_and_horizon_are_one_native_projection(monkeypatch):
    actors, topics, highs, social, _ = seed()
    original = psycopg.Connection.execute
    reads = []

    def observe(conn, query, *args, **kwargs):
        result = original(conn, query, *args, **kwargs)
        if isinstance(query, str) and (
            "FROM topic_consumption_cursors" in query or "FROM messages" in query
        ):
            reads.append(query)
        return result

    monkeypatch.setattr(psycopg.Connection, "execute", observe)
    result = social.get_topic_cursor(actor_ref=actors[0], topic_ref=topics[0])
    assert result["cursor"] == 0
    assert result["topicHighSequence"] == highs[0]
    assert len(reads) == 1, "cursor and horizon must be one native query"


@native_db
@pytest.mark.usefixtures("host_test_db_ready")
@settings(max_examples=12, deadline=None, derandomize=True)
@example(
    ops=[
        (0, 0, "high"),
        (0, 0, "replay"),
        (0, 0, "zero"),
        (0, 1, "future"),
        (1, 0, "mid"),
        (1, 1, "high"),
        (0, 0, "replay"),
        (1, 1, "future"),
        (0, 1, "high"),
    ]
)
@given(
    ops=st.lists(
        st.tuples(
            st.integers(0, 1),
            st.integers(0, 1),
            st.sampled_from(("zero", "mid", "high", "future", "replay")),
        ),
        min_size=4,
        max_size=12,
    )
)
def test_native_cursor_model_matches_public_read_ack_and_reentry(ops):
    actors, topics, highs, social, attention = seed()
    model = {(i, j): 0 for i in range(2) for j in range(2)}
    receipts = {}
    for i, j, op in ops:
        pair = (i, j)
        cursor = {"zero": 0, "mid": highs[j] // 2, "high": highs[j], "future": highs[j] + 1}.get(op)

        def ack(value, request):
            return social.ack_topic_cursor(
                actor_ref=actors[i], topic_ref=topics[j], cursor=value, client_request_id=request
            )

        if op == "replay" and pair in receipts:
            request, value, original = receipts[pair]
            replay = ack(value, request)
            assert replay == {**original, "admission": "existing"}
        else:
            if cursor is None:
                cursor = highs[j]
            request = f"model:{uuid4().hex}"
            prior = model[pair]
            if cursor < prior or cursor > highs[j]:
                with pytest.raises(ConflictError):
                    ack(cursor, request)
                # Failed admission must not consume its receipt identity.
                accepted = ack(prior, request)
                assert accepted["previousCursor"] == prior
                assert accepted["cursor"] == prior
                receipts[pair] = (request, prior, accepted)
            else:
                accepted = ack(cursor, request)
                assert accepted["previousCursor"] == prior
                assert accepted["cursor"] == cursor
                assert accepted["topicHighSequence"] == highs[j]
                model[pair] = cursor
                receipts[pair] = (request, cursor, accepted)
        for (ai, tj), expected in model.items():
            observed = social.get_topic_cursor(actor_ref=actors[ai], topic_ref=topics[tj])
            assert (observed["cursor"], observed["topicHighSequence"]) == (expected, highs[tj])
    for i, actor in enumerate(actors):
        reentry = attention.reentry(actor, after_sequence=0, limit=500)
        actual = {
            item["navigationRef"]: item["resumeAfterSequence"]
            for item in reentry["items"]
            if item["navigationKind"] == "topic"
        }
        assert {topic: actual[topic] for topic in topics} == {
            topic: model[i, j] for j, topic in enumerate(topics)
        }
    with psycopg.connect(DSN, row_factory=dict_row) as conn:
        stored = conn.execute(
            "SELECT actor_ref,topic_ref,cursor FROM topic_consumption_cursors "
            "WHERE actor_ref=ANY(%s)",
            (actors,),
        ).fetchall()
    stored_map = {(row["actor_ref"], row["topic_ref"]): row["cursor"] for row in stored}
    assert all(
        stored_map.get((actors[i], topics[j]), 0) == value for (i, j), value in model.items()
    )
