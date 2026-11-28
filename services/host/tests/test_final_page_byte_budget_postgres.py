"""Actual PostgreSQL consumer oracle for complete-page canonical byte budgets."""

from __future__ import annotations

import os
from uuid import uuid4

import pytest

from ordivon_host_v2.attention_store import AttentionStore
from ordivon_host_v2.canonical_json import canonical_bytes
from ordivon_host_v2.collaboration_inputs import MessageInput, SpaceInput, TopicInput
from ordivon_host_v2.references.actor_store import ActorReferenceStore
from ordivon_host_v2.social_store import SocialStore
from ordivon_host_v2.work_inputs import ActorKind, ActorRefInput

DSN = os.environ.get("ORDIVON_HOST_V2_TEST_DSN")
pytestmark = [
    pytest.mark.skipif(not DSN, reason="requires disposable PostgreSQL test DSN"),
    pytest.mark.usefixtures("host_test_db_ready"),
]


@pytest.fixture
def populated_topic():
    assert DSN
    uid = uuid4().hex
    reader = f"actor:agent:page-reader:{uid}"
    author = f"actor:agent:page-author:{uid}"
    space = f"space:page:{uid}"
    topic = f"topic:page:{uid}"
    actors = ActorReferenceStore(DSN)
    social = SocialStore(DSN)
    attention = AttentionStore(DSN)
    for actor in (reader, author):
        actors.declare_actor(
            ActorRefInput(actor_ref=actor, actor_kind=ActorKind.AGENT),
            client_request_id=f"declare:{actor}",
        )
    social.create_space(
        SpaceInput(space_ref=space, purpose="byte budget", actor_ref=author),
        client_request_id=f"create:{space}",
    )
    social.create_topic(
        TopicInput(topic_ref=topic, space_ref=space, title="budget", actor_ref=author),
        client_request_id=f"create:{topic}",
    )
    attention.follow(
        actor_ref=reader,
        target_kind="topic",
        target_ref=topic,
        client_request_id=f"follow:{uid}",
    )
    for i in range(80):
        ref = f"message:page:{uid}:{i}:" + "x" * 70
        social.post_message(
            MessageInput(
                message_ref=ref,
                client_request_id=f"post:{ref}",
                space_ref=space,
                topic_ref=topic,
                author_actor_ref=author,
                body="z" * 3000,
                recorded_at_ms=1,
            )
        )
    return social, attention, topic, reader


@pytest.mark.parametrize("surface", ["topic", "attention"])
def test_terminal_page_uses_actual_envelope_budget(populated_topic, surface):
    social, attention, topic, reader = populated_topic
    if surface == "topic":
        read = lambda cursor, budget: social.resume_topic(
            topic, after_sequence=cursor, limit=500, max_bytes=budget
        )
        key = "messages"
        minimum = 131072
    else:
        read = lambda cursor, budget: attention.delta(
            reader, after_sequence=cursor, limit=500, max_bytes=budget
        )
        key = "events"
        minimum = 16384
    full = read(0, 4194304)
    assert not full["hasMore"]
    assert len(full[key]) >= 80
    budget = len(canonical_bytes(full)) - 1
    assert budget >= minimum
    exact = read(0, budget + 1)
    assert exact == full
    first = read(0, budget)
    assert len(canonical_bytes(first)) <= budget
    assert first["hasMore"]
    assert first[key] == full[key][:-1]
    rest = read(first["nextAfterSequence"], budget)
    assert not rest["hasMore"]
    assert first[key] + rest[key] == full[key]
