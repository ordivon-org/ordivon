"""Actual PostgreSQL message evidence consumers reject altered durable content."""

from __future__ import annotations

import os
from uuid import uuid4

import psycopg
import pytest

from ordivon_host_v2.social_graph import MessageInput, MessageKind, SpaceInput, TopicInput
from ordivon_host_v2.social_store import SocialStore
from ordivon_host_v2.social_work import ActorKind, ActorRefInput
from ordivon_host_v2.work_store import WorkStore

DSN = os.getenv("ORDIVON_HOST_V2_TEST_DSN")
pytestmark = [
    pytest.mark.skipif(not DSN, reason="ORDIVON_HOST_V2_TEST_DSN not set"),
    pytest.mark.usefixtures("host_test_db_ready"),
]


def _new_message() -> tuple[SocialStore, MessageInput]:
    assert DSN
    token = uuid4().hex
    actor, space, topic, message = (
        f"actor:agent:integrity:{token}",
        f"space:integrity:{token}",
        f"topic:integrity:{token}",
        f"message:integrity:{token}",
    )
    WorkStore(DSN).declare_actor(
        ActorRefInput(actor_ref=actor, actor_kind=ActorKind.AGENT),
        client_request_id=f"actor:{actor}",
    )
    social = SocialStore(DSN)
    social.create_space(
        SpaceInput(space_ref=space, purpose="message integrity", actor_ref=actor),
        client_request_id=f"space:{space}",
    )
    social.create_topic(
        TopicInput(topic_ref=topic, space_ref=space, title="Integrity", actor_ref=actor),
        client_request_id=f"topic:{topic}",
    )
    payload = MessageInput(
        message_ref=message,
        client_request_id=f"post:{message}",
        space_ref=space,
        topic_ref=topic,
        author_actor_ref=actor,
        message_kind=MessageKind.FINDING,
        body="original attested evidence",
        recorded_at_ms=123,
    )
    assert social.post_message(payload)["admission"] == "committed"
    return social, payload


def test_postgresql_corrupt_message_body_fails_closed_in_all_content_consumers() -> None:
    assert DSN is not None
    social, original = _new_message()
    receipt = social.get_message(original.message_ref)
    with psycopg.connect(DSN) as conn:
        conn.execute(
            "UPDATE messages SET body=%s WHERE message_ref=%s",
            ("counterfeit evidence signal", original.message_ref),
        )
    with pytest.raises(RuntimeError, match="message content digest"):
        social.get_message(original.message_ref, expected_digest=receipt["messageDigest"])
    with pytest.raises(RuntimeError, match="message content digest"):
        social.resume_topic(original.topic_ref)
    with pytest.raises(RuntimeError, match="message content digest"):
        social.search_messages("counterfeit", topic_ref=original.topic_ref)
    with pytest.raises(RuntimeError, match="message content digest"):
        social.post_message(original.model_copy(update={
            "client_request_id": f"post-recovery:{original.message_ref}"
        }))


def test_postgresql_corrupt_message_timestamp_fails_closed_in_topic_and_get() -> None:
    assert DSN is not None
    social, original = _new_message()
    with psycopg.connect(DSN) as conn:
        conn.execute(
            "UPDATE messages SET recorded_at_ms=%s WHERE message_ref=%s",
            (987, original.message_ref),
        )
    with pytest.raises(RuntimeError, match="message content digest"):
        social.get_message(original.message_ref)
    with pytest.raises(RuntimeError, match="message content digest"):
        social.resume_topic(original.topic_ref)


def test_postgresql_search_cjk_substring_reaches_original_message() -> None:
    """An actual Agent's Chinese search finds an embedded phrase, not only a whole lexeme."""
    social, original = _new_message()
    inserted = original.model_copy(update={
        "message_ref": f"{original.message_ref}:cjk",
        "client_request_id": f"post:{original.message_ref}:cjk",
        "body": "已有真实终端消费链及独立验收证据",
    })
    assert social.post_message(inserted)["admission"] == "committed"
    found = social.search_messages("终端消费", topic_ref=original.topic_ref)
    assert [row["messageRef"] for row in found["messages"]] == [inserted.message_ref]
    assert social.search_messages("完全无关词", topic_ref=original.topic_ref)["messages"] == []
