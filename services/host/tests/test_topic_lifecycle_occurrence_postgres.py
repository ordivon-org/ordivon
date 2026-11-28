"""Public MCP lifecycle occurrence and native PostgreSQL state must agree."""
from __future__ import annotations

import asyncio
from uuid import uuid4

import pytest
from mcp import Client
from test_topic_state_lifecycle_postgres import DSN, pytestmark, setup_topic  # noqa: F401

from ordivon_host_v2.collaboration_inputs import MessageInput
from ordivon_host_v2.errors import ConflictError
from ordivon_host_v2.mcp_server import build_server


@pytest.mark.parametrize("nonempty", [False, True])
def test_repeated_close_without_new_messages_is_a_new_lifecycle_occurrence(nonempty) -> None:
    social, actor, space, topic = setup_topic()
    assert DSN is not None
    if nonempty:
        social.post_message(MessageInput(
            message_ref=f"message:lifecycle:{uuid4().hex}",
            client_request_id=f"post:lifecycle:{uuid4().hex}",
            space_ref=space, topic_ref=topic, author_actor_ref=actor,
            body="immutable original history", recorded_at_ms=1,
        ))

    async def scenario() -> None:
        async with Client(build_server(DSN), raise_exceptions=False) as client:
            async def current():
                result = await client.call_tool("topic.resume", {"topicRef": topic})
                assert not result.is_error
                return result.structured_content["topic"]

            before = await current()
            assert before["state"] == "open"
            args = {
                "topicRef": topic,
                "actorRef": actor,
                "state": "closed",
                "expectedState": "open",
                "expectedHighSequence": before["topicHighSequence"],
                "expectedChangeSequence": before["changeSequence"],
            }
            legacy = await client.call_tool(
                "topic.state.set", {k: v for k, v in args.items() if k != "expectedChangeSequence"}
            )
            assert legacy.is_error
            assert await current() == before

            first = await client.call_tool("topic.state.set", args)
            assert not first.is_error
            first_value = first.structured_content
            assert first_value["admission"] == "committed"
            closed = await current()
            assert closed["state"] == "closed"
            assert closed["changeSequence"] == first_value["changeSequence"] > before["changeSequence"]
            reopened = await client.call_tool(
                "topic.state.set",
                {**args, "state": "open", "expectedState": "closed",
                 "expectedChangeSequence": closed["changeSequence"]},
            )
            assert not reopened.is_error
            assert reopened.structured_content["state"] == "open"
            now = await current()
            assert now["state"] == before["state"] and now["topicHighSequence"] == before["topicHighSequence"]
            assert now["changeSequence"] > closed["changeSequence"]

            # Identical original occurrence is historical replay only, never a new effect.
            old_replay = await client.call_tool("topic.state.set", args)
            assert not old_replay.is_error
            assert old_replay.structured_content == {**first_value, "admission": "existing"}
            assert await current() == now

            # A distinct, unadmitted stale occurrence cannot pass an ABA state/high check.
            with pytest.raises(ConflictError, match="lifecycle changed"):
                social.set_topic_state(
                    topic_ref=topic, actor_ref=actor, state="closed", expected_state="open",
                    expected_high_sequence=before["topicHighSequence"],
                    expected_change_sequence=before["changeSequence"],
                    client_request_id=f"distinct-stale:{uuid4().hex}",
                )
            assert await current() == now

            fresh_args = {**args, "expectedChangeSequence": now["changeSequence"]}
            second = await client.call_tool("topic.state.set", fresh_args)
            assert not second.is_error
            second_value = second.structured_content
            actual = social.resume_topic(topic)["topic"]
            assert second_value["admission"] == "committed"
            assert second_value["state"] == actual["state"] == "closed"
            assert second_value["changeSequence"] == actual["changeSequence"] > now["changeSequence"]
            assert actual["topicHighSequence"] == before["topicHighSequence"]
            replay = await client.call_tool("topic.state.set", fresh_args)
            assert replay.structured_content == {**second_value, "admission": "existing"}
            assert await current() == actual

    asyncio.run(scenario())


def test_archive_restore_rearchive_keeps_exact_history_and_occurrence() -> None:
    social, actor, space, topic = setup_topic()
    assert DSN is not None
    msg = social.post_message(MessageInput(
        message_ref=f"message:archive-occurrence:{uuid4().hex}",
        client_request_id=f"post:archive-occurrence:{uuid4().hex}",
        space_ref=space, topic_ref=topic, author_actor_ref=actor,
        body="retained exact history", recorded_at_ms=1,
    ))

    async def scenario() -> None:
        async with Client(build_server(DSN), raise_exceptions=True) as client:
            async def read():
                return (await client.call_tool("topic.resume", {"topicRef": topic})).structured_content

            async def transition(target):
                before = (await read())["topic"]
                args = {
                    "topicRef": topic, "actorRef": actor, "state": target,
                    "expectedState": before["state"],
                    "expectedChangeSequence": before["changeSequence"],
                    "expectedHighSequence": before["topicHighSequence"],
                }
                result = (await client.call_tool("topic.state.set", args)).structured_content
                assert result["state"] == target
                assert result["changeSequence"] > before["changeSequence"]
                return args, result

            await transition("closed")
            old_args, archived = await transition("archived")
            await transition("closed")
            new_args, rearchived = await transition("archived")
            assert new_args["expectedChangeSequence"] > old_args["expectedChangeSequence"]
            assert rearchived["admission"] == "committed"
            old = (await client.call_tool("topic.state.set", old_args)).structured_content
            assert old == {**archived, "admission": "existing"}
            current = await read()
            assert current["topic"]["changeSequence"] == rearchived["changeSequence"]
            assert current["topic"]["state"] == "archived"
            assert current["topic"]["topicHighSequence"] == msg["sequence"]
            assert current["messages"][0]["messageDigest"] == msg["messageDigest"]

    asyncio.run(scenario())


def test_pre_epoch9_create_receipt_remains_exact_historical_response() -> None:
    """Only modify this fresh synthetic receipt to model the pre-upgrade shape."""
    import psycopg

    social, actor, space, _ = setup_topic()
    assert DSN is not None
    topic = f"topic:legacy-create:{uuid4().hex}"

    async def scenario() -> None:
        async with Client(build_server(DSN), raise_exceptions=True) as client:
            args = {"topicRef": topic, "spaceRef": space, "title": "legacy", "actorRef": actor}
            first = (await client.call_tool("topic.create", args)).structured_content
            assert first["changeSequence"] > 0
            legacy = {k: v for k, v in first.items() if k != "changeSequence"}
            with psycopg.connect(DSN) as conn:
                updated = conn.execute(
                    "UPDATE command_receipts SET response=response - 'changeSequence' "
                    "WHERE operation='topic.create' AND response->>'topicRef'=%s",
                    (topic,),
                )
                assert updated.rowcount == 1
            replay = (await client.call_tool("topic.create", args)).structured_content
            assert replay == {**legacy, "admission": "existing"}
            assert social.resume_topic(topic)["topic"]["changeSequence"] == first["changeSequence"]

    asyncio.run(scenario())
