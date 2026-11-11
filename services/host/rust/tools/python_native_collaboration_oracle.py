"""R5: Rust MCP first-owned collaboration read back by the original Python Host.

Only run after the stdio MCP consumer in an isolated, disposable PG18 schema13.
This is a recovery/parity oracle, not a second production owner.
"""
from __future__ import annotations

import os
from urllib.parse import urlsplit

import psycopg

from ordivon_host_v2.canonical_json import canonical_digest
from ordivon_host_v2.collaboration_inputs import (
    MessageInput,
    MessageKind,
    ParticipationStanding,
    SpaceInput,
    TopicInput,
)
from ordivon_host_v2.mcp_tool_registration import _request_id
from ordivon_host_v2.social_store import SocialStore
from ordivon_host_v2.work_inputs import ActorKind, ActorRefInput
from ordivon_host_v2.work_store import WorkStore

ACTOR = "actor:test:rust-mcp-r5-first"
SPACE = "space:test:rust-mcp-r5-first"
TOPIC = "topic:test:rust-mcp-r5-first"
MESSAGE = "message:test:rust-mcp-r5-first"
PURPOSE = "新 Agent 的 Rust MCP 原生协作 🧩"
TITLE = "由 Rust MCP 原生创建的会话 🧩"
BODY = "新 Agent 从零创建协作世界，真实 Rust MCP↔Python Host 🌍"
MILLISECONDS = 1700000000222


def dsn() -> str:
    value = os.environ.get("HOST_RUST_TEST_DSN", "")
    parsed = urlsplit(value)
    if (
        not value
        or value != os.environ.get("ORDIVON_HOST_V2_DSN")
        or parsed.scheme != "postgresql"
        or parsed.hostname not in {"localhost", "127.0.0.1"}
        or not parsed.port
        or parsed.path != "/host_rust_r2"
    ):
        raise RuntimeError("REFUSE_NON_DISPOSABLE_R5_PG18")
    with psycopg.connect(value) as conn:
        schema = conn.execute(
            "SELECT schema_version FROM host_v2_schema WHERE singleton"
        ).fetchone()
        major = int(conn.execute("SHOW server_version_num").fetchone()[0]) // 10000
        if schema != (13,) or major != 18:
            raise RuntimeError("R5_ORACLE_REQUIRES_SCHEMA13_PG18")
    return value


def verify() -> None:
    database = dsn()
    social = SocialStore(database)
    work = WorkStore(database)

    actor = ActorRefInput(actor_ref=ACTOR, actor_kind=ActorKind.AGENT)
    actor_id = _request_id("actor-declare", actor.model_dump(mode="json"))
    stored_actor = work.declare_actor(actor, client_request_id=actor_id)
    assert stored_actor["admission"] == "existing", stored_actor

    space = SpaceInput(
        space_ref=SPACE,
        purpose=PURPOSE,
        actor_ref=ACTOR,
        # Preserve the exact supplied order in the receipt hash; the native
        # stored subject projection is lexically sorted.
        subject_refs=["subject:zeta", "subject:alpha"],
    )
    space_id = _request_id("space-create", space.model_dump(mode="json"))
    repeated_space = social.create_space(space, client_request_id=space_id)
    assert repeated_space["admission"] == "existing", repeated_space
    assert repeated_space["subjectRefs"] == ["subject:alpha", "subject:zeta"]
    original_space = social.get_space(SPACE)
    assert original_space["subjectRefs"] == repeated_space["subjectRefs"]
    assert original_space["subjectCount"] == 2, original_space
    assert original_space["participantCount"] == 1, original_space
    assert original_space["participants"][0]["standing"] == "joined", original_space
    assert original_space["topicCount"] == 1, original_space
    assert original_space["topics"][0]["topicRef"] == TOPIC, original_space

    topic = TopicInput(topic_ref=TOPIC, space_ref=SPACE, title=TITLE, actor_ref=ACTOR)
    topic_id = _request_id("topic-create", topic.model_dump(mode="json"))
    repeated_topic = social.create_topic(topic, client_request_id=topic_id)
    assert repeated_topic["admission"] == "existing" and repeated_topic["state"] == "open", repeated_topic
    assert repeated_topic["topicRef"] == TOPIC

    # Membership is desired-state, never an immutable Command Receipt.
    membership = social.set_participation(
        space_ref=SPACE,
        actor_ref=ACTOR,
        standing=ParticipationStanding.JOINED,
        client_request_id="python-r5-desired-state-non-receipt",
    )
    assert membership["standing"] == "joined", membership
    assert social.get_space(SPACE)["participantCount"] == 1

    message_payload = {
        "messageRef": MESSAGE,
        "spaceRef": SPACE,
        "topicRef": TOPIC,
        "authorActorRef": ACTOR,
        "body": BODY,
        "recordedAtMs": MILLISECONDS,
        "messageKind": "finding",
    }
    message_id = _request_id("message-post", message_payload)
    message = MessageInput(
        message_ref=MESSAGE,
        client_request_id=message_id,
        space_ref=SPACE,
        topic_ref=TOPIC,
        author_actor_ref=ACTOR,
        message_kind=MessageKind.FINDING,
        body=BODY,
        recorded_at_ms=MILLISECONDS,
    )
    repeated_message = social.post_message(message)
    assert repeated_message["admission"] == "existing", repeated_message
    assert repeated_message["messageRef"] == MESSAGE
    assert social.get_message(MESSAGE)["body"] == BODY

    page = social.resume_topic(TOPIC, after_sequence=0, limit=100, max_bytes=524288)
    assert [entry["messageRef"] for entry in page["messages"]] == [MESSAGE], page

    identities = [
        ("actor.declare", actor_id, {"operation": "actor.declare", **actor.model_dump(mode="json")}),
        ("space.create", space_id, {"operation": "space.create", **space.model_dump(mode="json")}),
        ("topic.create", topic_id, {"operation": "topic.create", **topic.model_dump(mode="json")}),
        ("message.post", message_id, {
            "operation": "message.post",
            "message_ref": MESSAGE,
            "client_request_id": message_id,
            "space_ref": SPACE,
            "topic_ref": TOPIC,
            "author_actor_ref": ACTOR,
            "message_kind": "finding",
            "body": BODY,
            "recorded_at_ms": MILLISECONDS,
        }),
    ]
    with psycopg.connect(database) as conn:
        for operation, identity, payload in identities:
            row = conn.execute(
                "SELECT operation,request_digest,response FROM command_receipts "
                "WHERE client_request_id=%s", (identity,)
            ).fetchone()
            assert row is not None, (operation, identity)
            assert row[0] == operation, (operation, row)
            assert row[1] == canonical_digest(payload), (operation, identity, row[1])
            # Message.post intentionally records a compact immutable reference,
            # not the full output body. Python/Rust both reconstruct it from
            # the digest-checked Message row after a lost response.
            if operation == "message.post":
                assert row[2]["kind"] == "ordivon.host-message-post-receipt-ref", row[2]
                assert row[2]["messageRef"] == MESSAGE, row[2]
                assert row[2]["messageDigest"] == social.get_message(MESSAGE)["messageDigest"]
            else:
                assert row[2]["admission"] == "committed", (operation, row[2])

        # A prior joined request cannot pin desired state after left->joined.
        membership_receipt = _request_id("space-participation-set", {
            "spaceRef": SPACE,
            "actorRef": ACTOR,
            "standing": "joined",
        })
        assert conn.execute(
            "SELECT 1 FROM command_receipts WHERE client_request_id=%s",
            (membership_receipt,),
        ).fetchone() is None, "membership erroneously pinned as immutable receipt"
        assert conn.execute(
            "SELECT count(*) FROM spaces WHERE space_ref=%s", (SPACE,)
        ).fetchone() == (1,)
        assert conn.execute(
            "SELECT count(*) FROM topics WHERE topic_ref=%s", (TOPIC,)
        ).fetchone() == (1,)
        assert conn.execute(
            "SELECT count(*) FROM messages WHERE message_ref=%s", (MESSAGE,)
        ).fetchone() == (1,)
        assert conn.execute(
            "SELECT count(*) FROM participations WHERE space_ref=%s AND actor_ref=%s",
            (SPACE, ACTOR),
        ).fetchone() == (1,)
    print("PYTHON_READ_RUST_R5_NATIVE_COLLAB_PASS actor=1 space=1 topic=1 message=1 "
          "membership=desired-state receipts=4 exact-jcs=YES output=original-python")


if __name__ == "__main__":
    verify()
