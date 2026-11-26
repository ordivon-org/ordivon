"""Native consumer oracle for relation-scoped Attention, not SQL spelling."""
from __future__ import annotations

import os
from uuid import uuid4

import pytest

from ordivon_host_v2.attention_store import AttentionStore
from ordivon_host_v2.collaboration_inputs import (
    MessageInput,
    MessageRelationInput,
    MessageRelationKind,
    SpaceInput,
    TopicInput,
)
from ordivon_host_v2.references.actor_store import ActorReferenceStore
from ordivon_host_v2.social_store import SocialStore
from ordivon_host_v2.work_inputs import ActorKind, ActorRefInput

DSN = os.environ.get("ORDIVON_HOST_V2_TEST_DSN")
pytestmark = [
    pytest.mark.skipif(not DSN, reason="requires disposable PostgreSQL test DSN"),
    pytest.mark.usefixtures("host_test_db_ready"),
]


def test_relation_scope_horizon_reason_union_and_pagination() -> None:
    assert DSN
    uid = uuid4().hex
    reader, author, outsider = (
        f"actor:agent:relation:{role}:{uid}" for role in ("reader", "author", "outsider")
    )
    social = SocialStore(DSN)
    attention = AttentionStore(DSN)
    for ref in (reader, author, outsider):
        ActorReferenceStore(DSN).declare_actor(
            ActorRefInput(actor_ref=ref, actor_kind=ActorKind.AGENT),
            client_request_id=f"declare:{ref}",
        )
    space, foreign = f"space:relation:{uid}", f"space:relation-foreign:{uid}"
    topic, sibling, outside = (
        f"topic:relation:{role}:{uid}" for role in ("target", "sibling", "outside")
    )
    for ref in (space, foreign):
        social.create_space(
            SpaceInput(space_ref=ref, purpose="relation scope", actor_ref=author),
            client_request_id=f"create:{ref}",
        )
    for ref, container in ((topic, space), (sibling, space), (outside, foreign)):
        social.create_topic(
            TopicInput(topic_ref=ref, space_ref=container, title="relation", actor_ref=author),
            client_request_id=f"create:{ref}",
        )

    def post(name, actor, container, channel):
        ref = f"message:relation:{name}:{uid}"
        social.post_message(MessageInput(
            message_ref=ref, client_request_id=f"post:{ref}", space_ref=container,
            topic_ref=channel, author_actor_ref=actor, body=name, recorded_at_ms=1,
        ))
        return ref

    def relate(source, kind, target):
        social.add_message_relation(MessageRelationInput(
            source_message_ref=source, relation=kind, target_ref=target, actor_ref=author,
        ), client_request_id=f"rel:{source}:{kind.value}:{target}")
        return source + ":" + kind.value + ":" + target

    def follow(actor, kind, target):
        attention.follow(actor_ref=actor, target_kind=kind, target_ref=target,
                         client_request_id=f"follow:{actor}:{target}")

    parent = post("parent", reader, space, topic)
    pre = post("pre", author, space, topic)
    other = post("other", author, foreign, outside)
    before = relate(pre, MessageRelationKind.REFERENCES, parent)
    follow(reader, "space", space)
    follow(outsider, "space", foreign)
    # A late relation on an older message uses relation time, not message time.
    space_only = relate(pre, MessageRelationKind.MENTIONS, reader)
    follow(reader, "topic", topic)
    reply = post("reply", author, space, topic)
    both = relate(reply, MessageRelationKind.REPLY_TO, parent)
    both_mention = relate(reply, MessageRelationKind.MENTIONS, reader)
    sibling_msg = post("sibling", author, space, sibling)
    sibling_ref = relate(sibling_msg, MessageRelationKind.REFERENCES, parent)
    foreign_ref = relate(other, MessageRelationKind.REFERENCES, parent)
    outside_msg = post("outside-late", author, foreign, outside)
    outside_mention = relate(outside_msg, MessageRelationKind.MENTIONS, reader)

    expected = {
        space_only: ["followed_space", "mentioned"],
        both: ["followed_space", "followed_topic", "replied_to_me"],
        both_mention: ["followed_space", "followed_topic", "mentioned"],
        sibling_ref: ["followed_space"],
        outside_mention: ["mentioned"],
    }
    whole = attention.delta(reader, after_sequence=0, limit=500)
    relations = {x["sourceRef"]: x["reasons"] for x in whole["events"]
                 if x["eventKind"] == "message_relation"}
    assert relations == expected
    assert before not in relations and foreign_ref not in relations

    # Actual public consumer pagination must produce the same ordered sequence
    # and never acknowledge or silently change the topic cursor.
    cursor = 0
    rows = []
    while True:
        page = attention.delta(reader, after_sequence=cursor, limit=2)
        rows.extend(page["events"])
        if not page["hasMore"]:
            break
        assert page["nextAfterSequence"] > cursor
        cursor = page["nextAfterSequence"]
    assert rows == whole["events"]
    assert attention.get(reader)["afterSequence"] == 0
    assert social.get_topic_cursor(actor_ref=reader, topic_ref=topic)["cursor"] == 0

    # Removing a follow must remove only that reason. Mentions/replies still
    # route independently and another actor's subscriptions cannot leak.
    attention.unfollow(actor_ref=reader, target_kind="space", target_ref=space,
                       client_request_id=f"unfollow:{uid}")
    after = attention.delta(reader, after_sequence=0, limit=500)
    assert {x["sourceRef"]: x["reasons"] for x in after["events"]
            if x["eventKind"] == "message_relation"} == {
        space_only: ["mentioned"],
        both: ["followed_topic", "replied_to_me"],
        both_mention: ["followed_topic", "mentioned"],
        outside_mention: ["mentioned"],
    }
