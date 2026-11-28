"""Destructive-to-capacity boundary test: only dedicated, empty scratch databases."""

from __future__ import annotations

import asyncio
import json
import os

import psycopg
import pytest
from mcp import Client

from ordivon_host_v2.mcp_server import build_server

MAX_EXACT = 9007199254740991


@pytest.mark.parametrize("domain", ["MESSAGE", "CHANGE"])
def test_final_coordinate_is_readable_and_next_write_rolls_back(domain: str) -> None:
    dsn = os.environ.get(f"ORDIVON_HOST_V2_BOUNDARY_{domain}_DSN")
    if not dsn:
        pytest.skip("requires an explicitly dedicated empty boundary database")

    with psycopg.connect(dsn) as conn:
        from ordivon_host_v2.service import REQUIRED_SCHEMA_VERSION
        assert conn.execute("SELECT schema_version FROM host_v2_schema").fetchone() == (REQUIRED_SCHEMA_VERSION,)
        assert conn.execute("SELECT count(*) FROM actor_refs").fetchone() == (0,)
        assert conn.execute("SELECT count(*) FROM messages").fetchone() == (0,)
        assert conn.execute("SELECT count(*) FROM command_receipts").fetchone() == (0,)
        assert conn.execute("SELECT value FROM swf_change_clock").fetchone() == (0,)

    async def scenario() -> None:
        async with Client(build_server(dsn), raise_exceptions=False) as client:

            async def call(name, args):
                result = await client.call_tool(name, args)
                assert result.is_error is False, (name, result)
                assert result.structured_content is not None
                return result.structured_content

            actor = "actor:agent:generated-coordinate-boundary"
            space = "space:generated-coordinate-boundary"
            topic = "topic:generated-coordinate-boundary"
            await call("actor.declare", {"actorRef": actor, "actorKind": "agent"})
            await call(
                "space.create", {"spaceRef": space, "purpose": "capacity", "actorRef": actor}
            )
            await call(
                "topic.create",
                {"topicRef": topic, "spaceRef": space, "title": "capacity", "actorRef": actor},
            )
            await call(
                "subscription.follow",
                {"actorRef": actor, "targetKind": "topic", "targetRef": topic},
            )
            with psycopg.connect(dsn) as conn:
                if domain == "MESSAGE":
                    conn.execute(
                        "SELECT setval(pg_get_serial_sequence('messages','sequence'), %s, true)",
                        (MAX_EXACT - 1,),
                    )
                else:
                    conn.execute(
                        "UPDATE swf_change_clock SET value=%s WHERE singleton", (MAX_EXACT - 1,)
                    )
            args = {
                "messageRef": "message:generated-coordinate-final",
                "spaceRef": space,
                "topicRef": topic,
                "authorActorRef": actor,
                "body": "last exact coordinate",
                "recordedAtMs": 1,
            }
            posted = await call("message.post", args)
            page = await call("topic.resume", {"topicRef": topic, "afterSequence": 0})
            delta = await call("attention.delta", {"actorRef": actor, "afterSequence": 0})
            reentry = await call("attention.reentry", {"actorRef": actor, "afterSequence": 0})
            assert page["messages"][0]["messageRef"] == args["messageRef"]
            if domain == "MESSAGE":
                assert posted["sequence"] == page["nextAfterSequence"] == MAX_EXACT
            else:
                assert delta["snapshotHighSequence"] == reentry["snapshotHighSequence"] == MAX_EXACT
            with psycopg.connect(dsn) as conn:
                before = conn.execute("SELECT count(*) FROM command_receipts").fetchone()
                clock_before = conn.execute("SELECT value FROM swf_change_clock").fetchone()

            rejected = await client.call_tool(
                "message.post", {**args, "messageRef": "message:generated-coordinate-overflow"}
            )
            assert rejected.is_error is True
            error = "".join(getattr(item, "text", "") for item in rejected.content)
            payload = json.loads(error.split(": ", 1)[1])
            assert payload["code"] == "RESOURCE_EXHAUSTED"
            assert payload["reason"] == "generated_coordinate_exhausted"
            assert payload["retryable"] is False
            with psycopg.connect(dsn) as conn:
                assert conn.execute("SELECT count(*) FROM messages").fetchone() == (1,)
                assert conn.execute("SELECT count(*) FROM command_receipts").fetchone() == before
                assert conn.execute("SELECT value FROM swf_change_clock").fetchone() == clock_before
            replay = await call("message.post", args)
            assert replay["admission"] == "existing"
            assert replay["messageDigest"] == posted["messageDigest"]
            assert replay["sequence"] == posted["sequence"]
            assert await call("topic.resume", {"topicRef": topic, "afterSequence": 0}) == page
            assert (
                await call("attention.reentry", {"actorRef": actor, "afterSequence": 0}) == reentry
            )

    asyncio.run(scenario())
