from __future__ import annotations

import os
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from uuid import uuid4

import pytest

from ordivon_host_v2.collaboration_inputs import MessageInput, SpaceInput, TopicInput
from ordivon_host_v2.errors import ConflictError
from ordivon_host_v2.social_store import SocialStore
from ordivon_host_v2.work_inputs import ActorKind, ActorRefInput
from ordivon_host_v2.work_store import WorkStore

DSN = os.environ.get("ORDIVON_HOST_V2_TEST_DSN")
pytestmark = [
    pytest.mark.skipif(not DSN, reason="ORDIVON_HOST_V2_TEST_DSN not set"),
    pytest.mark.usefixtures("host_test_db_ready"),
]


def setup_topic() -> tuple[SocialStore, str, str, str]:
    assert DSN is not None
    token = uuid4().hex
    actor = f"actor:agent:topic-state:{token}"
    space = f"space:topic-state:{token}"
    topic = f"topic:state:{token}"
    WorkStore(DSN).declare_actor(
        ActorRefInput(actor_ref=actor, actor_kind=ActorKind.AGENT),
        client_request_id=f"actor:topic-state:{token}",
    )
    social = SocialStore(DSN)
    social.create_space(
        SpaceInput(space_ref=space, purpose="topic lifecycle contract test", actor_ref=actor),
        client_request_id=f"space:topic-state:{token}",
    )
    social.create_topic(
        TopicInput(topic_ref=topic, space_ref=space, title="Lifecycle test", actor_ref=actor),
        client_request_id=f"topic:topic-state:{token}",
    )
    return social, actor, space, topic


def test_close_reopen_preserves_messages_and_idempotency() -> None:
    social, actor, space, topic = setup_topic()
    message = MessageInput(
        message_ref=f"message:topic-state:{uuid4().hex}",
        client_request_id=f"post:topic-state:{uuid4().hex}",
        space_ref=space,
        topic_ref=topic,
        author_actor_ref=actor,
        body="immutable historical evidence",
        recorded_at_ms=1,
    )
    posted = social.post_message(message)
    seq = posted["sequence"]
    request = f"topic-close:{uuid4().hex}"
    result = social.set_topic_state(
        topic_ref=topic,
        actor_ref=actor,
        state="closed",
        expected_state="open",
        expected_high_sequence=seq,
        client_request_id=request,
    )
    assert (result["admission"], result["state"]) == ("committed", "closed")
    replay = social.set_topic_state(
        topic_ref=topic,
        actor_ref=actor,
        state="closed",
        expected_state="open",
        expected_high_sequence=seq,
        client_request_id=request,
    )
    assert (replay["admission"], replay["state"]) == ("existing", "closed")
    with pytest.raises(ConflictError, match="closed topic"):
        social.post_message(
            MessageInput(
                message_ref=f"message:topic-state:{uuid4().hex}",
                client_request_id=f"post:topic-state:{uuid4().hex}",
                space_ref=space,
                topic_ref=topic,
                author_actor_ref=actor,
                body="must be rejected while closed",
                recorded_at_ms=2,
            )
        )
    restored = social.resume_topic(topic, after_sequence=0)
    assert any(row["messageRef"] == message.message_ref for row in restored["messages"])
    reopened = social.set_topic_state(
        topic_ref=topic,
        actor_ref=actor,
        state="open",
        expected_state="closed",
        expected_high_sequence=seq,
        client_request_id=f"topic-reopen:{uuid4().hex}",
    )
    assert reopened["state"] == "open"
    new_msg = social.post_message(
        MessageInput(
            message_ref=f"message:topic-state:{uuid4().hex}",
            client_request_id=f"post:topic-state:{uuid4().hex}",
            space_ref=space,
            topic_ref=topic,
            author_actor_ref=actor,
            body="reopen permits new content",
            recorded_at_ms=3,
        )
    )
    assert new_msg["sequence"] > seq
    with pytest.raises(ConflictError, match="messages changed"):
        social.set_topic_state(
            topic_ref=topic,
            actor_ref=actor,
            state="closed",
            expected_state="open",
            expected_high_sequence=seq,
            client_request_id=f"stale-close:{uuid4().hex}",
        )


def test_topic_state_compare_and_set_is_strict_and_reversible() -> None:
    social, actor, _, topic = setup_topic()
    with pytest.raises(ValueError):
        social.set_topic_state(
            topic_ref=topic,
            actor_ref=actor,
            state="closed",
            expected_state="open",
            expected_high_sequence=True,
            client_request_id=f"bool:{uuid4().hex}",
        )
    with pytest.raises(ConflictError, match="state changed"):
        social.set_topic_state(
            topic_ref=topic,
            actor_ref=actor,
            state="open",
            expected_state="closed",
            expected_high_sequence=0,
            client_request_id=f"stale:{uuid4().hex}",
        )
    unchanged = social.set_topic_state(
        topic_ref=topic,
        actor_ref=actor,
        state="open",
        expected_state="open",
        expected_high_sequence=0,
        client_request_id=f"no-op:{uuid4().hex}",
    )
    assert unchanged["admission"] == "existing"


def test_concurrent_message_and_close_have_one_serialized_winner() -> None:
    social, actor, space, topic = setup_topic()
    barrier = Barrier(2)

    def close() -> str:
        barrier.wait(timeout=15)
        try:
            social.set_topic_state(
                topic_ref=topic,
                actor_ref=actor,
                state="closed",
                expected_state="open",
                expected_high_sequence=0,
                client_request_id=f"close-race:{uuid4().hex}",
            )
            return "close"
        except ConflictError:
            return "conflict"

    def post() -> str:
        barrier.wait(timeout=15)
        try:
            social.post_message(
                MessageInput(
                    message_ref=f"message:race:{uuid4().hex}",
                    client_request_id=f"post-race:{uuid4().hex}",
                    space_ref=space,
                    topic_ref=topic,
                    author_actor_ref=actor,
                    body="concurrent contender",
                    recorded_at_ms=4,
                )
            )
            return "post"
        except ConflictError:
            return "conflict"

    with ThreadPoolExecutor(max_workers=2) as executor:
        first = executor.submit(close)
        second = executor.submit(post)
        outcomes = sorted([first.result(timeout=30), second.result(timeout=30)])
    assert outcomes in (["close", "conflict"], ["conflict", "post"])
    state = social.list_topics(space)["topics"][0]["state"]
    assert state == ("closed" if "close" in outcomes else "open")
