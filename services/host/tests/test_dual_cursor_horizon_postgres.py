"""Dual cursor recovery against a real disposable PostgreSQL 18 Host.

The global Attention change clock is NOT the Topic message identity sequence.
An invalid Topic cursor must not masquerade as an empty successfully read page.
"""

from __future__ import annotations

import os
from uuid import uuid4

import pytest

from ordivon_host_v2.attention_store import AttentionStore
from ordivon_host_v2.collaboration_inputs import MessageInput, SpaceInput, TopicInput
from ordivon_host_v2.errors import ConflictError
from ordivon_host_v2.references.actor_store import ActorReferenceStore
from ordivon_host_v2.social_errors import TopicResumeCursorAhead
from ordivon_host_v2.social_store import SocialStore
from ordivon_host_v2.work_inputs import ActorKind, ActorRefInput

DSN = os.environ.get("ORDIVON_HOST_V2_TEST_DSN")
pytestmark = [
    pytest.mark.skipif(not DSN, reason="requires disposable PostgreSQL test DSN"),
    pytest.mark.usefixtures("host_test_db_ready"),
]


def _create_topic_pair() -> tuple[str, str, str, str, SocialStore, AttentionStore]:
    assert DSN is not None
    uid = uuid4().hex
    actor = f"actor:agent:dual-cursor:{uid}"
    space = f"space:dual-cursor:{uid}"
    topic = f"topic:dual-cursor:{uid}"
    other = f"topic:dual-cursor-other:{uid}"
    social = SocialStore(DSN)
    attention = AttentionStore(DSN)
    ActorReferenceStore(DSN).declare_actor(
        ActorRefInput(actor_ref=actor, actor_kind=ActorKind.AGENT),
        client_request_id=f"actor:{uid}",
    )
    social.create_space(
        SpaceInput(space_ref=space, purpose="dual cursor negative evidence", actor_ref=actor),
        client_request_id=f"space:{uid}",
    )
    for name in (topic, other):
        social.create_topic(
            TopicInput(topic_ref=name, space_ref=space, title="cursor", actor_ref=actor),
            client_request_id=f"topic:{name}",
        )
    attention.follow(
        actor_ref=actor,
        target_kind="topic",
        target_ref=topic,
        client_request_id=f"follow:{uid}",
    )
    return actor, space, topic, other, social, attention


def _post(
    social: SocialStore, actor: str, space: str, topic: str, *, number: int
) -> dict[str, object]:
    uid = uuid4().hex
    return social.post_message(
        MessageInput(
            message_ref=f"message:dual-cursor:{uid}",
            client_request_id=f"post:{uid}",
            space_ref=space,
            topic_ref=topic,
            author_actor_ref=actor,
            body=f"cursor page {number}",
            recorded_at_ms=number,
        )
    )


def test_forward_empty_page_not_confused_with_wrong_cursor_domain() -> None:
    actor, space, topic, _, social, attention = _create_topic_pair()
    posted = _post(social, actor, space, topic, number=1)
    message_sequence = int(posted["sequence"])
    observed = attention.delta(actor, after_sequence=0, limit=100)
    global_high = int(observed["snapshotHighSequence"])
    assert global_high > message_sequence  # Different durable cursor domains.

    # Positive: the canonical Topic message sequence resumes the actual message.
    page = social.resume_topic(topic, after_sequence=0)
    assert [x["messageRef"] for x in page["messages"]] == [posted["messageRef"]]
    assert page["hasMore"] is False
    assert page["nextAfterSequence"] == message_sequence

    # Negative: the global Attention sequence is NOT a Topic position.
    # Previous Host source returned an empty successful page, falsely suggesting
    # the Topic was exhausted. Now return the exact bounded counterevidence.
    with pytest.raises(TopicResumeCursorAhead) as mismatch:
        social.resume_topic(topic, after_sequence=global_high)
    assert mismatch.value.topic_ref == topic
    assert mismatch.value.after_sequence == global_high
    assert mismatch.value.topic_high == message_sequence
    assert isinstance(mismatch.value, ConflictError)

    # Correct cursor == committed high legitimately yields an empty page.
    at_high = social.resume_topic(topic, after_sequence=message_sequence)
    assert at_high["messages"] == []
    assert at_high["hasMore"] is False
    assert at_high["nextAfterSequence"] == message_sequence

    # Two independent acknowledgements: one cannot substitute for the other.
    attention.ack(actor, cursor=global_high, client_request_id=f"ack-attn:{uuid4().hex}")
    assert social.get_topic_cursor(actor_ref=actor, topic_ref=topic)["cursor"] == 0
    reentry = attention.reentry(actor, after_sequence=0)
    navigation = next(x for x in reentry["items"] if x["navigationRef"] == topic)
    assert navigation["resumeAfterSequence"] == 0
    social.ack_topic_cursor(
        actor_ref=actor,
        topic_ref=topic,
        cursor=message_sequence,
        client_request_id=f"ack-topic:{uuid4().hex}",
    )
    assert social.get_topic_cursor(actor_ref=actor, topic_ref=topic)["cursor"] == message_sequence
    assert attention.get(actor)["events"] == []


def test_other_topic_cursor_cannot_silently_hide_first_topic() -> None:
    actor, space, topic, other, social, _ = _create_topic_pair()
    first = _post(social, actor, space, topic, number=1)
    second = _post(social, actor, space, other, number=2)
    assert second["sequence"] > first["sequence"]
    with pytest.raises(TopicResumeCursorAhead) as wrong:
        social.resume_topic(topic, after_sequence=int(second["sequence"]))
    assert wrong.value.topic_high == first["sequence"]
    assert (
        social.resume_topic(other, after_sequence=int(first["sequence"]))["messages"][0][
            "messageRef"
        ]
        == second["messageRef"]
    )
    with pytest.raises(ConflictError, match="beyond current topic horizon"):
        social.ack_topic_cursor(
            actor_ref=actor,
            topic_ref=topic,
            cursor=int(second["sequence"]),
            client_request_id=f"wrong-topic-ack:{uuid4().hex}",
        )


def test_empty_topic_has_zero_horizon_not_an_arbitrary_future_empty_page() -> None:
    _, _, _, empty, social, _ = _create_topic_pair()
    zero = social.resume_topic(empty, after_sequence=0)
    assert zero["messages"] == []
    assert zero["hasMore"] is False
    assert zero["nextAfterSequence"] == 0
    with pytest.raises(TopicResumeCursorAhead) as incorrect:
        social.resume_topic(empty, after_sequence=1)
    assert incorrect.value.topic_high == 0


def test_has_more_false_is_only_one_time_cut_not_forever_no_messages() -> None:
    actor, space, topic, _, social, _ = _create_topic_pair()
    first = _post(social, actor, space, topic, number=1)
    empty_after_first = social.resume_topic(topic, after_sequence=int(first["sequence"]))
    assert empty_after_first["hasMore"] is False
    assert empty_after_first["messages"] == []

    second = _post(social, actor, space, topic, number=2)
    later = social.resume_topic(topic, after_sequence=empty_after_first["nextAfterSequence"])
    assert [row["messageRef"] for row in later["messages"]] == [second["messageRef"]]
