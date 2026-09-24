from __future__ import annotations

import asyncio

from mcp import Client

from ordivon_host_v2.mcp_server import build_server

EXPECTED = {
    "host.status",
    "actor.declare",
    "work.create",
    "work.get",
    "work.list",
    "work.snapshot.commit",
    "space.create",
    "space.get",
    "space.list",
    "space.participation.set",
    "topic.create",
    "topic.resume",
    "message.post",
    "message.search",
    "message.relation.add",
    "subscription.follow",
    "subscription.list",
    "subscription.unfollow",
    "attention.get",
    "attention.delta",
    "attention.ack",
}


def test_host_server_identity_and_exact_social_work_surface() -> None:
    async def scenario() -> None:
        async with Client(
            build_server("postgresql://unused.invalid/unused"), raise_exceptions=True
        ) as client:
            listed = await client.list_tools()
            assert client.server_info is not None
            assert client.server_info.name == "ordivon-host-v2"
            assert client.server_info.version == "0.3.0"
            assert listed.ttl_ms == 0
            assert listed.cache_scope == "private"
            by_name = {tool.name: tool for tool in listed.tools}
            assert set(by_name) == EXPECTED
            assert not any(name.startswith("task.") for name in by_name)
            assert not any(name.startswith("board.") for name in by_name)
            attention = by_name["attention.delta"].input_schema
            assert set(attention["required"]) == {"actorRef", "afterSequence"}
            assert "actorRef" in attention["properties"]
            for tool in listed.tools:
                assert tool.output_schema is not None
                assert tool.output_schema.get("additionalProperties") is not True

    asyncio.run(scenario())
