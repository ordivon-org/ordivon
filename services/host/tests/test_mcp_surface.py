from __future__ import annotations

import asyncio
import os
from uuid import uuid4

import pytest
from mcp import Client

from ordivon_host_v2 import HostV2
from ordivon_host_v2.mcp_server import build_server

DSN = os.environ.get("ORDIVON_HOST_V2_TEST_DSN")
pytestmark = pytest.mark.skipif(not DSN, reason="ORDIVON_HOST_V2_TEST_DSN not set")


def snapshot(frontier: str) -> dict[str, object]:
    return {
        "objective": "prove Social Work Fabric northbound vertical",
        "frontier": frontier,
        "established": [],
        "unresolved": [],
        "rejected": [],
        "constraints": ["owner boundaries preserved"],
        "next_actions": [],
        "reference_refs": [],
    }


def test_official_mcp_exposes_social_work_surface_and_runs_vertical_slice() -> None:
    assert DSN is not None
    HostV2(DSN).initialize()
    token = uuid4().hex
    actor_a = f"actor:agent:mcp-a:{token}"
    actor_b = f"actor:agent:mcp-b:{token}"
    work_ref = f"work:mcp:{token}"
    space_ref = f"space:mcp:{token}"
    topic_ref = f"topic:mcp:{token}"
    message_ref = f"message:mcp:{token}"

    async def call(client: Client, name: str, arguments: dict[str, object]) -> dict[str, object]:
        result = await client.call_tool(name, arguments)
        assert result.is_error is False, (name, result)
        assert result.structured_content is not None
        return result.structured_content

    async def scenario() -> None:
        async with Client(build_server(DSN), raise_exceptions=True) as client:
            listed = await client.list_tools()
            names = {tool.name for tool in listed.tools}
            assert "task.resume" not in names
            assert "board.post" not in names

            for actor in (actor_a, actor_b):
                created = await call(
                    client, "actor.declare", {"actorRef": actor, "actorKind": "agent"}
                )
                assert created["actorRef"] == actor

            created_work = await call(
                client,
                "work.create",
                {
                    "workRef": work_ref,
                    "workKind": "investigation",
                    "actorRef": actor_a,
                    "initialSnapshot": snapshot("r1"),
                },
            )
            assert created_work["revision"] == 1
            work_inventory = await call(client, "work.list", {"state": "open", "limit": 20})
            assert any(row["workRef"] == work_ref for row in work_inventory["works"])
            assert work_inventory["rankingApplied"] is False

            await call(
                client,
                "space.create",
                {
                    "spaceRef": space_ref,
                    "purpose": "cross-agent collaboration",
                    "actorRef": actor_a,
                    "subjectRefs": [work_ref],
                },
            )
            for actor in (actor_a, actor_b):
                joined = await call(
                    client,
                    "space.participation.set",
                    {"spaceRef": space_ref, "actorRef": actor, "standing": "joined"},
                )
                assert joined["standing"] == "joined"

            spaces = await call(
                client, "space.list", {"actorRef": actor_a, "subjectRef": work_ref, "limit": 20}
            )
            assert [row["spaceRef"] for row in spaces["spaces"]] == [space_ref]
            assert spaces["rankingApplied"] is False

            await call(
                client,
                "topic.create",
                {
                    "topicRef": topic_ref,
                    "spaceRef": space_ref,
                    "title": "matching",
                    "actorRef": actor_a,
                },
            )
            await call(
                client,
                "subscription.follow",
                {"actorRef": actor_a, "targetKind": "topic", "targetRef": topic_ref},
            )
            subscriptions = await call(
                client, "subscription.list", {"actorRef": actor_a, "targetKind": "topic"}
            )
            assert [row["targetRef"] for row in subscriptions["subscriptions"]] == [topic_ref]
            assert subscriptions["rankingApplied"] is False
            baseline = await call(
                client, "attention.delta", {"actorRef": actor_a, "afterSequence": 0, "limit": 500}
            )
            high = int(baseline["snapshotHighSequence"])

            posted = await call(
                client,
                "message.post",
                {
                    "messageRef": message_ref,
                    "spaceRef": space_ref,
                    "topicRef": topic_ref,
                    "authorActorRef": actor_b,
                    "body": "please inspect",
                    "recordedAtMs": 1,
                    "messageKind": "finding",
                },
            )
            assert posted["messageRef"] == message_ref
            search = await call(
                client,
                "message.search",
                {"query": "inspect", "spaceRef": space_ref, "topicRef": topic_ref, "limit": 20},
            )
            assert [row["messageRef"] for row in search["messages"]] == [message_ref]
            assert search["rankingApplied"] is False
            assert search["ordering"] == "sequence_desc"
            await call(
                client,
                "message.relation.add",
                {
                    "sourceMessageRef": message_ref,
                    "relation": "mentions",
                    "targetRef": actor_a,
                    "actorRef": actor_b,
                },
            )
            delta = await call(
                client,
                "attention.delta",
                {"actorRef": actor_a, "afterSequence": high, "limit": 100},
            )
            kinds = {row["eventKind"] for row in delta["events"]}
            assert {"message", "message_relation"} <= kinds
            assert delta["rankingApplied"] is False

            updated = await call(
                client,
                "work.snapshot.commit",
                {
                    "workRef": work_ref,
                    "expectedRevision": 1,
                    "snapshot": snapshot("r2"),
                    "actorRef": actor_a,
                },
            )
            assert updated["revision"] == 2
            current = await call(client, "work.get", {"workRef": work_ref})
            assert current["snapshot"]["frontier"] == "r2"

            status = await call(client, "host.status", {"detail": "integrity"})
            assert status["schemaVersion"] == 3
            assert status["authority"]["journalSchema"] == 8
            assert status["doctor"]["healthy"] is True
            assert "board" not in status

    asyncio.run(scenario())
