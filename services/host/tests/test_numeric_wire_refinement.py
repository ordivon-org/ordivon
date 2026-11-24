"""Refine the public numeric domain to exact JSON/JCS and native store input."""
import asyncio

import pytest
from mcp import Client

from ordivon_host_v2.attention_store import AttentionStore
from ordivon_host_v2.errors import ConflictError
from ordivon_host_v2.mcp_server import build_server
from ordivon_host_v2.social_store import SocialStore
from ordivon_host_v2.work_inputs import WorkSnapshotInput
from ordivon_host_v2.work_store import WorkStore

SAFE = (1 << 53) - 1


@pytest.mark.parametrize("operation,field,arguments", [
    ("message.post", "recordedAtMs", {
        "messageRef": "message:boundary", "spaceRef": "space:boundary",
        "topicRef": "topic:boundary", "authorActorRef": "actor:boundary", "body": "test",
    }),
    ("topic.state.set", "expectedHighSequence", {
        "topicRef": "topic:boundary", "actorRef": "actor:boundary",
        "state": "closed", "expectedState": "open",
    }),
    ("attention.ack", "cursor", {"actorRef": "actor:boundary"}),
    ("topic.cursor.ack", "cursor", {"actorRef": "actor:boundary", "topicRef": "topic:boundary"}),
    ("attention.delta", "afterSequence", {"actorRef": "actor:boundary"}),
    ("attention.reentry", "afterSequence", {"actorRef": "actor:boundary"}),
    ("topic.resume", "afterSequence", {"topicRef": "topic:boundary"}),
    ("message.search", "beforeSequence", {"query": "test"}),
    ("message.relation.list", "afterChangeSequence", {"messageRef": "message:boundary"}),
    ("work.get", "revision", {"workRef": "work:boundary"}),
    ("work.snapshot.commit", "expectedRevision", {
        "workRef": "work:boundary", "actorRef": "actor:boundary",
        "snapshot": {"objective": "test", "frontier": "test"},
    }),
])
def test_native_mcp_numeric_schema_and_invalid_inputs(monkeypatch, operation, field, arguments):
    calls = []

    def witness(*args, **kwargs):
        calls.append((args, kwargs))
        raise ConflictError("boundary witness")

    for owner, methods in [
        (WorkStore, ("get_work", "commit_snapshot")),
        (SocialStore, ("post_message", "set_topic_state", "ack_topic_cursor", "resume_topic", "search_messages", "list_message_relations")),
        (AttentionStore, ("ack", "delta", "reentry")),
    ]:
        for method in methods:
            monkeypatch.setattr(owner, method, witness)

    async def run():
        async with Client(build_server("postgresql://unused.invalid"), raise_exceptions=False) as client:
            tools = {tool.name: tool for tool in (await client.list_tools()).tools}
            spec = tools[operation].input_schema["properties"][field]
            if "anyOf" in spec:
                spec = next(item for item in spec["anyOf"] if item.get("type") == "integer")
            expected_max = SAFE - 1 if operation == "work.snapshot.commit" else SAFE
            # Test the real SDK, not the annotation's appearance in a source file.
            assert spec.get("maximum") == expected_max
            assert spec.get("minimum") == (1 if operation.startswith("work.") or operation == "message.search" else 0)
            for invalid in (True, 1.0, "1", spec.get("minimum") - 1, expected_max + 1):
                result = await client.call_tool(operation, {**arguments, field: invalid})
                assert result.is_error
            assert not calls
            # Legal upper endpoint must actually cross the SDK into the store;
            # otherwise an always-rejecting endpoint could satisfy negatives.
            await client.call_tool(operation, {**arguments, field: expected_max})
            assert len(calls) == 1
            args, kwargs = calls.pop()
            if operation == "message.post":
                value = args[1].recorded_at_ms
            elif operation == "work.get":
                value = args[2]
            else:
                name = {
                    "expectedHighSequence": "expected_high_sequence",
                    "expectedRevision": "expected_revision",
                    "afterSequence": "after_sequence",
                    "cursor": "cursor",
                    "beforeSequence": "before_sequence",
                    "afterChangeSequence": "after_change_sequence",
                }[field]
                value = kwargs[name]
            assert type(value) is int and value == expected_max

    asyncio.run(run())


def test_direct_ack_and_cas_reject_before_digest_or_database(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("invalid coordinate reached digest or DB")

    from ordivon_host_v2 import attention_store, social_topic_commands, work_store

    for module in (attention_store, social_topic_commands, work_store):
        monkeypatch.setattr(module, "canonical_digest", forbidden)
    for owner in (AttentionStore, SocialStore, WorkStore):
        monkeypatch.setattr(owner, "_connect", forbidden)
    attention = AttentionStore("postgresql://unused.invalid")
    social = SocialStore("postgresql://unused.invalid")
    work = WorkStore("postgresql://unused.invalid")
    with pytest.raises(ValueError, match="safe integer"):
        attention.ack("actor:boundary", cursor=SAFE + 1, client_request_id="test")
    with pytest.raises(ValueError, match="safe integer"):
        social.ack_topic_cursor(
            actor_ref="actor:boundary", topic_ref="topic:boundary",
            cursor=SAFE + 1, client_request_id="test",
        )
    with pytest.raises(ValueError, match="safe integer"):
        work.commit_snapshot(
            "work:boundary", expected_revision=SAFE, snapshot=WorkSnapshotInput(objective="test", frontier="test"),
            actor_ref="actor:boundary", client_request_id="test",
        )
