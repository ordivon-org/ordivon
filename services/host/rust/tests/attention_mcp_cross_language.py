"""Temporary migration oracle: compare real Rust MCP with Python Host over same disposable PG18.

Only invoked from a script that seeds brand-new PostgreSQL 18 and applies Host
schema 13. Never invokes the production Host or external service endpoints.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import uuid
from typing import Any

import psycopg

from ordivon_host_v2.attention_store import AttentionStore
from ordivon_host_v2.errors import ConflictError
from ordivon_host_v2.mcp_domain_errors import _domain_error_payload
from ordivon_host_v2.collaboration_inputs import MessageInput, MessageRelationInput
from ordivon_host_v2.mcp_tool_registration import _request_id
from ordivon_host_v2.social_store import SocialStore

assert len(sys.argv) == 2, "expected Rust Host binary"
dsn = os.environ["HOST_RUST_TEST_DSN"]
assert dsn == os.environ["ORDIVON_HOST_V2_DSN"], "refusing mismatched production credentials"
assert "127.0.0.1:" in dsn or "localhost:" in dsn, "disposable loopback PG only"

suffix = uuid.uuid4().hex[:12]
actor, space, topic = (f"{kind}:test:host-rust-attention-b:{suffix}" for kind in ("actor", "space", "topic"))
with psycopg.connect(dsn) as conn:
    conn.execute(
        "INSERT INTO actor_refs(actor_ref,actor_kind) VALUES (%s,'agent')",
        (actor,),
    )
    conn.execute(
        "INSERT INTO spaces(space_ref,purpose,created_by_actor_ref) "
        "VALUES (%s,'cross-language attention oracle',%s)",
        (space, actor),
    )
    conn.execute(
        "INSERT INTO topics(topic_ref,space_ref,title,state,created_by_actor_ref) "
        "VALUES (%s,%s,'attention-oracle','open',%s)",
        (topic, space, actor),
    )
social = SocialStore(dsn)
attention = AttentionStore(dsn)

process = subprocess.Popen(
    [sys.argv[1]],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True,
    encoding="utf-8",
    bufsize=1,
    env=os.environ.copy(),
)
sequence = 0


def send(method: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    global sequence
    sequence += 1
    packet: dict[str, Any] = {"jsonrpc": "2.0", "method": method, "id": sequence}
    if params is not None:
        packet["params"] = params
    assert process.stdin is not None
    assert process.stdout is not None
    process.stdin.write(json.dumps(packet, ensure_ascii=False) + "\n")
    process.stdin.flush()
    line = process.stdout.readline()
    if not line:
        assert process.stderr is not None
        raise AssertionError(f"Rust MCP ended: {process.stderr.read()[:2000]}")
    answer = json.loads(line)
    assert answer["id"] == sequence, answer
    assert "error" not in answer, answer
    return answer["result"]


def call(name: str, arguments: dict[str, Any], *, error: bool = False) -> dict[str, Any]:
    result = send("tools/call", {"name": name, "arguments": arguments})
    assert result.get("isError", False) is error, (name, arguments, result)
    if error:
        return result
    assert isinstance(result.get("structuredContent"), dict), (name, result)
    return result["structuredContent"]


try:
    assert send(
        "initialize",
        {
            "protocolVersion": "2025-06-18",
            "capabilities": {},
            "clientInfo": {"name": "host-rust-b-parity", "version": "1.0"},
        },
    )["serverInfo"]["name"]

    follow_args = {"actorRef": actor, "targetKind": "topic", "targetRef": topic}
    follow = call("subscription.follow", follow_args)
    assert follow["admission"] == "committed", follow
    python_sub = attention.list_subscriptions(actor)
    rust_sub = call("subscription.list", {"actorRef": actor})
    assert rust_sub == python_sub, (rust_sub, python_sub)
    assert follow == attention.follow(
        actor_ref=actor,
        target_kind="topic",
        target_ref=topic,
        client_request_id="python-oracle-repeat-follow",
    ) | {"admission": "committed"}, "follow readback vs Python after desired-state existing"

    first = social.post_message(
        MessageInput(
            message_ref=f"message:test:host-rust-attention-b:{suffix}:1",
            client_request_id=f"message-python-host-b:{suffix}:1",
            space_ref=space,
            topic_ref=topic,
            author_actor_ref=actor,
            message_kind="finding",
            body="原始 Python 消息 🧩",
            recorded_at_ms=1794310000001,
        )
    )
    second = social.post_message(
        MessageInput(
            message_ref=f"message:test:host-rust-attention-b:{suffix}:2",
            client_request_id=f"message-python-host-b:{suffix}:2",
            space_ref=space,
            topic_ref=topic,
            author_actor_ref=actor,
            message_kind="note",
            body="Unicode 大小字节预算 🎯",
            recorded_at_ms=1794310000002,
        )
    )
    assert int(second["sequence"]) > int(first["sequence"])
    args = {"actorRef": actor, "afterSequence": 0, "limit": 1}
    rust_page_one = call("attention.delta", args)
    python_page_one = attention.delta(actor, after_sequence=0, limit=1)
    assert rust_page_one == python_page_one, (rust_page_one, python_page_one)
    after = rust_page_one["nextAfterSequence"]
    args["afterSequence"] = after
    args["limit"] = 100
    rust_page_two = call("attention.delta", args)
    python_page_two = attention.delta(actor, after_sequence=after)
    assert rust_page_two == python_page_two, (rust_page_two, python_page_two)
    high = rust_page_two["snapshotHighSequence"]
    assert int(high) >= int(after)
    assert call("attention.get", {"actorRef": actor}) == attention.get(actor)
    assert call("attention.reentry", {"actorRef": actor, "afterSequence": 0}) == attention.reentry(
        actor, after_sequence=0
    )

    ack_args = {"actorRef": actor, "cursor": high}
    original_ack = call("attention.ack", ack_args)
    assert original_ack["previousCursor"] == 0, original_ack
    expected_ack = attention.ack(
        actor,
        cursor=high,
        client_request_id=_request_id("attention-ack", ack_args),
    )
    assert expected_ack == original_ack | {"admission": "existing"}, (expected_ack, original_ack)
    assert call("attention.get", {"actorRef": actor}) == attention.get(actor)
    assert call("attention.get", {"actorRef": actor})["events"] == []

    relation = social.add_message_relation(
        MessageRelationInput(
            source_message_ref=first["messageRef"],
            relation="mentions",
            target_ref=actor,
            actor_ref=actor,
        ),
        client_request_id=f"message-python-host-b:{suffix}:late-mention",
    )
    assert relation["admission"] == "committed"
    rust_late = call("attention.delta", {"actorRef": actor, "afterSequence": high})
    python_late = attention.delta(actor, after_sequence=high)
    assert rust_late == python_late, (rust_late, python_late)
    assert len(rust_late["events"]) == 1 and rust_late["events"][0]["eventKind"] == "message_relation"

    # Missing record, out-of-horizon cursor, and invalid budget must never
    # become false successful MCP results; do not overclaim Python error text parity.
    invalid_high = call(
        "attention.delta", {"actorRef": actor, "afterSequence": high + 1_000_000}, error=True
    )
    expected_failure = _domain_error_payload(
        ConflictError("after_sequence cannot exceed current change horizon")
    )
    rust_error_text = invalid_high["content"][0]["text"]
    try:
        rust_error_payload = json.loads(rust_error_text)
    except json.JSONDecodeError:
        rust_error_payload = None
    envelope_parity = rust_error_payload == expected_failure
    print(
        "B_ATTENTION_ERROR_ENVELOPE_"
        + ("MATCH" if envelope_parity else "GAP")
        + f" python_code={expected_failure['code']}"
        + f" rust_is_json={rust_error_payload is not None}"
    )
    call("attention.delta", {"actorRef": actor, "afterSequence": 0, "maxBytes": 100}, error=True)
    call("attention.delta", {"actorRef": actor, "afterSequence": -1}, error=True)

    assert call("subscription.unfollow", follow_args)["admission"] == "committed"
    assert call("subscription.follow", follow_args)["admission"] == "committed"
    assert attention.list_subscriptions(actor)["subscriptions"]
    print(
        "B_CROSSLANGUAGE_ATTENTION_MCP_PASS "
        "follow/list=EXACT delta2pages=EXACT reentry=EXACT "
        "ack=PYTHON_RECEIPT_REPLAY late_relation=EXACT invalid_inputs=DENIED "
        "desired_follow_reactivation=PASS"
    )
finally:
    process.terminate()
    try:
        process.communicate(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()
        process.communicate()
