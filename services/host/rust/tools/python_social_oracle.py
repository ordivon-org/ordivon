"""Original Python Host Social oracle for Rust MCP Topic/Message transaction parity.

Run only against the temporary PostgreSQL18 created by verify_r2_integrated_pg18.sh.
"""
from __future__ import annotations

import os
import sys
from urllib.parse import urlsplit

import psycopg

from ordivon_host_v2.collaboration_inputs import (
    MessageInput,
    MessageKind,
    SpaceInput,
    TopicInput,
)
from ordivon_host_v2.mcp_tool_registration import _request_id
from ordivon_host_v2.social_store import SocialStore

ACTOR = "actor:test:rust-mcp"
SPACE = "space:test:rust-mcp-social"
TOPIC = "topic:test:rust-mcp-social"
PY_MSG = "message:test:rust-mcp-python-seed"
RUST_MSG = "message:test:rust-mcp-social-rust"
RUST_BODY = "Rust 续读后提交，原始 Python Host 可恢复 🌍"
RUST_MS = 1700000000111


def disposable_dsn() -> str:
    dsn = os.environ.get("HOST_RUST_TEST_DSN", "")
    parsed = urlsplit(dsn)
    if (
        os.environ.get("ORDIVON_HOST_V2_DSN") != dsn
        or parsed.scheme != "postgresql"
        or parsed.hostname not in {"127.0.0.1", "localhost"}
        or not parsed.port
        or parsed.path != "/host_rust_r2"
    ):
        raise RuntimeError("REFUSE_NON_DISPOSABLE_PG18")
    with psycopg.connect(dsn) as con:
        major = int(con.execute("SHOW server_version_num").fetchone()[0]) // 10000
        schema = con.execute("SELECT schema_version FROM host_v2_schema WHERE singleton").fetchone()
        if major != 18 or schema != (13,):
            raise RuntimeError("REFUSE_UNEXPECTED_DATABASE_VERSION")
    return dsn


def seed(store: SocialStore) -> None:
    # The Work oracle first declares ACTOR against the same disposable PG.
    space = SpaceInput(space_ref=SPACE, purpose="Python to Rust MCP Social recovery",
                       actor_ref=ACTOR)
    created = store.create_space(
        space, client_request_id=_request_id("space-create", space.model_dump(mode="json"))
    )
    assert created["admission"] == "committed", created
    topic = TopicInput(topic_ref=TOPIC, space_ref=SPACE, title="Cross-language MCP recovery",
                       actor_ref=ACTOR)
    created = store.create_topic(
        topic, client_request_id=_request_id("topic-create", topic.model_dump(mode="json"))
    )
    assert created["admission"] == "committed", created
    wire = {
        "messageRef": PY_MSG, "spaceRef": SPACE, "topicRef": TOPIC,
        "authorActorRef": ACTOR, "body": "Original Python seed 🧩",
        "recordedAtMs": 1700000000000, "messageKind": "note",
    }
    msg = MessageInput(
        message_ref=PY_MSG,
        client_request_id=_request_id("message-post", wire),
        space_ref=SPACE,
        topic_ref=TOPIC,
        author_actor_ref=ACTOR,
        body=wire["body"],
        recorded_at_ms=wire["recordedAtMs"],
        message_kind=MessageKind.NOTE,
    )
    created = store.post_message(msg)
    assert created["admission"] == "committed", created
    print("PYTHON_SOCIAL_ORACLE_SEED_PASS", created["sequence"])


def verify(store: SocialStore, dsn: str) -> None:
    messages = store.resume_topic(TOPIC, after_sequence=0, limit=50, max_bytes=524288)["messages"]
    assert [m["messageRef"] for m in messages] == [PY_MSG, RUST_MSG], messages
    persisted = store.get_message(RUST_MSG)
    assert persisted["body"] == RUST_BODY and persisted["messageKind"] == "finding", persisted
    cursor = store.get_topic_cursor(actor_ref=ACTOR, topic_ref=TOPIC)
    assert cursor["cursor"] == messages[-1]["sequence"], cursor
    relations = store.list_message_relations(RUST_MSG)
    assert any(rel["relation"] == "reply_to" and rel["targetRef"] == PY_MSG
               for rel in relations["relations"]), relations

    # Reconstruct the exact Python original MCP wrapper input request identities.
    identities = {
        "message.post": _request_id("message-post", {
            "messageRef": RUST_MSG, "spaceRef": SPACE, "topicRef": TOPIC,
            "authorActorRef": ACTOR, "body": RUST_BODY,
            "recordedAtMs": RUST_MS, "messageKind": "finding",
        }),
        "message.relation.add": _request_id("message-relation-add", {
            "source_message_ref": RUST_MSG, "relation": "reply_to",
            "target_ref": PY_MSG, "actor_ref": ACTOR,
        }),
        "topic.cursor.ack": _request_id("topic-cursor-ack", {
            "actorRef": ACTOR, "topicRef": TOPIC, "cursor": messages[-1]["sequence"],
        }),
        "topic.state.set": _request_id("topic-state-set", {
            "topicRef": TOPIC, "actorRef": ACTOR, "state": "closed",
            "expectedState": "open", "expectedHighSequence": messages[-1]["sequence"],
        }),
    }
    with psycopg.connect(dsn) as con:
        for operation, identity in identities.items():
            row = con.execute(
                "SELECT operation, response FROM command_receipts WHERE client_request_id=%s",
                (identity,),
            ).fetchone()
            assert row is not None and row[0] == operation, (operation, identity, row)
        status = con.execute("SELECT state FROM topics WHERE topic_ref=%s", (TOPIC,)).fetchone()
        assert status == ("closed",), status
        count = con.execute("SELECT COUNT(*) FROM messages WHERE topic_ref=%s", (TOPIC,)).fetchone()
        assert count == (2,), count
    print("PYTHON_SOCIAL_ORACLE_VERIFY_PASS messages=2 receipts=4 closed=1 cursor=exact")


def main() -> None:
    if len(sys.argv) != 2 or sys.argv[1] not in {"seed", "verify"}:
        raise SystemExit("usage: python_social_oracle.py seed|verify")
    dsn = disposable_dsn()
    store = SocialStore(dsn)
    if sys.argv[1] == "seed":
        seed(store)
    else:
        verify(store, dsn)


if __name__ == "__main__":
    main()
