from __future__ import annotations

import asyncio

from mcp import Client

from ordivon_gateway.mcp_server import build_server

# Consumer-driven contract: reflect the Host owner's byte envelope in
# MCP tools/list, so agents can choose a legal response budget first try.
_HOST_COLLECTION_TOOLS = (
    "work.list",
    "space.list",
    "space.subject.list",
    "space.participation.list",
    "topic.list",
    "message.relation.list",
    "subscription.list",
    "attention.get",
    "attention.delta",
    "attention.reentry",
)
_HOST_MESSAGE_TOOLS = ("topic.resume", "message.search")


def test_host_forwarded_byte_budgets_are_advertised_by_the_real_sdk() -> None:
    async def scenario() -> None:
        async with Client(build_server(), raise_exceptions=True) as client:
            tools = {tool.name: tool for tool in (await client.list_tools()).tools}
            expected = {
                **dict.fromkeys(_HOST_COLLECTION_TOOLS, 16_384),
                **dict.fromkeys(_HOST_MESSAGE_TOOLS, 131_072),
                "space.get": 1_048_576,
            }
            for name, minimum in expected.items():
                assert name in tools
                field = tools[name].input_schema["properties"]["maxBytes"]
                assert field["minimum"] == minimum, name
                assert field["maximum"] == 4_194_304, name

    asyncio.run(scenario())


def test_sdk_rejects_illegal_owner_budgets_before_any_host_call() -> None:
    from ordivon_gateway.service import GatewayService

    class OwnerSpy:
        def __init__(self) -> None:
            self.calls: list[tuple[str, str]] = []

        def is_configured(self, owner_id: str) -> bool:
            return True

        async def call_tool(self, owner_id: str, tool_name: str, arguments: dict):
            self.calls.append((owner_id, tool_name))
            raise AssertionError("invalid input must never reach an owner")

    async def scenario() -> None:
        caller = OwnerSpy()
        async with Client(build_server(GatewayService(caller)), raise_exceptions=True) as client:
            for name, payload in (
                ("topic.resume", {"topicRef": "topic:fixture", "maxBytes": 16_384}),
                ("message.search", {"query": "fixture", "maxBytes": 4_194_305}),
                ("space.get", {"spaceRef": "space:fixture", "maxBytes": 262_144}),
                ("work.list", {"maxBytes": 1}),
            ):
                result = await client.call_tool(name, payload)
                assert result.is_error is True, (name, result)
            assert caller.calls == []

    asyncio.run(scenario())


def test_gateway_topic_archive_forwarding_uses_existing_owner_tool() -> None:
    from mcp.server import MCPServer

    from ordivon_gateway.capabilities.host.social import register_host_social_tools

    async def scenario() -> None:
        calls: list[tuple[str, dict]] = []

        async def owner(tool: str, args: dict) -> dict:
            calls.append((tool, args))
            return {"acceptedByFixture": True}

        server = MCPServer("host-topic-archive-source-fixture", version="1.0")
        register_host_social_tools(server, owner)
        async with Client(server, raise_exceptions=True) as client:
            tools = {tool.name: tool for tool in (await client.list_tools()).tools}
            state = tools["topic.state.set"].input_schema["properties"]
            assert "archived" in state["state"]["enum"]
            assert "archived" in state["expectedState"]["enum"]
            topic_list = tools["topic.list"].input_schema["properties"]
            assert topic_list["includeArchived"]["default"] is False
            await client.call_tool(
                "topic.state.set",
                {
                    "topicRef": "topic:fixture",
                    "actorRef": "actor:fixture",
                    "state": "archived",
                    "expectedState": "closed",
                    "expectedHighSequence": 5,
                },
            )
            assert calls[-1] == (
                "topic.state.set",
                {
                    "topicRef": "topic:fixture",
                    "actorRef": "actor:fixture",
                    "state": "archived",
                    "expectedState": "closed",
                    "expectedHighSequence": 5,
                },
            )
            await client.call_tool(
                "topic.list",
                {"spaceRef": "space:fixture", "includeArchived": True},
            )
            assert calls[-1][0] == "topic.list"
            assert calls[-1][1]["includeArchived"] is True

    asyncio.run(scenario())
