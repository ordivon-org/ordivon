"""Native message wire and relation round-trip contract."""

from __future__ import annotations

import os
from contextlib import contextmanager
from uuid import uuid4

import psycopg
import pytest
from psycopg.rows import dict_row

from ordivon_host_v2.canonical_json import canonical_digest
from ordivon_host_v2.collaboration_inputs import (
    MessageInput,
    MessageRelationInput,
    MessageRelationKind,
    SpaceInput,
    TopicInput,
)
from ordivon_host_v2.references.actor_store import ActorReferenceStore
from ordivon_host_v2.social_message_commands import SocialMessageCommands
from ordivon_host_v2.social_store import SocialStore
from ordivon_host_v2.work_inputs import ActorKind, ActorRefInput

DSN = os.environ.get("ORDIVON_HOST_V2_TEST_DSN")
pytestmark = [
    pytest.mark.skipif(not DSN, reason="requires disposable PG"),
    pytest.mark.usefixtures("host_test_db_ready"),
]


@pytest.fixture
def sample():
    assert DSN
    uid = uuid4().hex
    actor, space, topic = f"actor:agent:codec:{uid}", f"space:codec:{uid}", f"topic:codec:{uid}"
    ActorReferenceStore(DSN).declare_actor(
        ActorRefInput(actor_ref=actor, actor_kind=ActorKind.AGENT), client_request_id=f"actor:{uid}"
    )
    social = SocialStore(DSN)
    social.create_space(
        SpaceInput(space_ref=space, purpose="codec", actor_ref=actor),
        client_request_id=f"space:{uid}",
    )
    social.create_topic(
        TopicInput(topic_ref=topic, space_ref=space, title="codec", actor_ref=actor),
        client_request_id=f"topic:{uid}",
    )
    payload = MessageInput(
        message_ref=f"message:codec:{uid}",
        client_request_id=f"post:{uid}",
        space_ref=space,
        topic_ref=topic,
        author_actor_ref=actor,
        body='codec witness 中文𐀀\n"\\',
        recorded_at_ms=2**53 - 1,
    )
    return social, payload


def test_wire_projections_and_digest_match_native_independent_oracle(sample):
    social, payload = sample
    post = social.post_message(payload)
    read = social.get_message(payload.message_ref)
    search = social.search_messages("witness", topic_ref=payload.topic_ref)["messages"][0]
    resume = social.resume_topic(payload.topic_ref)["messages"][0]
    content = {
        "messageRef": payload.message_ref,
        "spaceRef": payload.space_ref,
        "topicRef": payload.topic_ref,
        "authorActorRef": payload.author_actor_ref,
        "messageKind": payload.message_kind.value,
        "body": payload.body,
        "recordedAtMs": payload.recorded_at_ms,
    }
    with psycopg.connect(DSN, row_factory=dict_row) as conn:
        row = conn.execute(
            "SELECT sequence, created_at,message_digest FROM messages WHERE message_ref=%s",
            (payload.message_ref,),
        ).fetchone()
    wire = {
        **content,
        "sequence": row["sequence"],
        "createdAt": row["created_at"].isoformat(),
        "messageDigest": canonical_digest(content),
    }
    assert row["message_digest"] == wire["messageDigest"]
    assert search == wire
    assert resume == {k: v for k, v in wire.items() if k not in {"spaceRef", "topicRef"}}
    assert read == {
        "schemaVersion": 1,
        "kind": "ordivon.host-message-read",
        **wire,
        "truthBoundary": "exact durable Host message projection only; message content remains collaboration evidence until interpreted by the owning domain",
    }
    assert post == {
        "schemaVersion": 1,
        "kind": "ordivon.host-message",
        "admission": "committed",
        **wire,
        "truthBoundary": "durable collaboration message only; participation is not authorization and message content is not Work/domain truth",
    }
    assert social.post_message(payload) == {**post, "admission": "existing"}


def test_relation_fresh_returning_avoids_second_query_and_preserves_replay(sample):
    social, payload = sample
    social.post_message(payload)
    value = MessageRelationInput(
        source_message_ref=payload.message_ref,
        relation=MessageRelationKind.REFERENCES,
        target_ref="external:codec:witness",
        actor_ref=payload.author_actor_ref,
    )
    statements = []

    class ObservedConnection:
        def __init__(self, conn):
            self.conn = conn

        def execute(self, statement, *args, **kwargs):
            statements.append(statement)
            return self.conn.execute(statement, *args, **kwargs)

        def transaction(self):
            return self.conn.transaction()

    @contextmanager
    def connect():
        with psycopg.connect(DSN, row_factory=dict_row) as conn:
            yield ObservedConnection(conn)

    commands = SocialMessageCommands(connect)

    def relation_select_count():
        return sum("FROM message_relations WHERE" in s for s in statements)

    initial = commands.add_message_relation(
        value, client_request_id=f"relation:first:{payload.message_ref}"
    )
    assert initial["admission"] == "committed"
    assert relation_select_count() == 0
    statements.clear()
    replay = commands.add_message_relation(
        value, client_request_id=f"relation:first:{payload.message_ref}"
    )
    assert replay == {**initial, "admission": "existing"}
    assert relation_select_count() == 0
    statements.clear()
    duplicate = commands.add_message_relation(
        value, client_request_id=f"relation:other:{payload.message_ref}"
    )
    assert duplicate == {**initial, "admission": "existing"}
    assert relation_select_count() == 1
    with psycopg.connect(DSN, row_factory=dict_row) as conn:
        rows = conn.execute(
            "SELECT source_message_ref,relation,target_ref,created_by_actor_ref,created_at FROM message_relations WHERE source_message_ref=%s",
            (payload.message_ref,),
        ).fetchall()
    assert len(rows) == 1
    assert {
        k: initial[k]
        for k in ("sourceMessageRef", "relation", "targetRef", "createdByActorRef", "createdAt")
    } == {
        "sourceMessageRef": rows[0]["source_message_ref"],
        "relation": rows[0]["relation"],
        "targetRef": rows[0]["target_ref"],
        "createdByActorRef": rows[0]["created_by_actor_ref"],
        "createdAt": rows[0]["created_at"].isoformat(),
    }
