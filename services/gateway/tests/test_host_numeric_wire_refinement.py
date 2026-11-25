"""Native Gateway SDK must preserve exact Host V1 numeric coordinates."""

from __future__ import annotations

import asyncio

import pytest
from mcp import Client

from ordivon_gateway.mcp_server import build_server
from ordivon_gateway.service import GatewayService

SAFE = (1 << 53) - 1


class WitnessOwner:
    def __init__(self):
        self.calls = []

    def is_configured(self, owner_id):
        return True

    async def call_tool(self, owner_id, tool_name, arguments):
        self.calls.append((owner_id, tool_name, arguments))
        return {"forwarded": tool_name}


@pytest.mark.parametrize(
    "name,field,base",
    [
        ("attention.ack", "cursor", {"actorRef": "actor:fixture"}),
        ("attention.delta", "afterSequence", {"actorRef": "actor:fixture"}),
        ("attention.reentry", "afterSequence", {"actorRef": "actor:fixture"}),
        ("topic.cursor.ack", "cursor", {"actorRef": "actor:fixture", "topicRef": "topic:fixture"}),
        ("topic.resume", "afterSequence", {"topicRef": "topic:fixture"}),
        (
            "topic.state.set",
            "expectedHighSequence",
            {
                "actorRef": "actor:fixture",
                "topicRef": "topic:fixture",
                "state": "closed",
                "expectedState": "open",
                "expectedChangeSequence": 1,
            },
        ),
        (
            "topic.state.set",
            "expectedChangeSequence",
            {
                "actorRef": "actor:fixture",
                "topicRef": "topic:fixture",
                "state": "closed",
                "expectedState": "open",
                "expectedHighSequence": 0,
            },
        ),
        (
            "message.post",
            "recordedAtMs",
            {
                "messageRef": "message:fixture",
                "spaceRef": "space:fixture",
                "topicRef": "topic:fixture",
                "authorActorRef": "actor:fixture",
                "body": "test",
            },
        ),
        ("message.search", "beforeSequence", {"query": "test"}),
        ("message.relation.list", "afterChangeSequence", {"messageRef": "message:fixture"}),
        ("work.get", "revision", {"workRef": "work:fixture"}),
        (
            "work.snapshot.commit",
            "expectedRevision",
            {
                "workRef": "work:fixture",
                "actorRef": "actor:fixture",
                "snapshot": {"objective": "test", "frontier": "test"},
            },
        ),
    ],
)
def test_native_sdk_host_numeric_boundary(name, field, base):
    async def scenario():
        owner = WitnessOwner()
        async with Client(build_server(GatewayService(owner)), raise_exceptions=False) as client:
            tools = {tool.name: tool for tool in (await client.list_tools()).tools}
            spec = tools[name].input_schema["properties"][field]
            if "anyOf" in spec:
                spec = next(x for x in spec["anyOf"] if x.get("type") == "integer")
            maximum = SAFE - 1 if name == "work.snapshot.commit" else SAFE
            minimum = (
                1
                if name.startswith("work.")
                or name == "message.search"
                or field == "expectedChangeSequence"
                else 0
            )
            for value in (True, 1.0, "1", minimum - 1, maximum + 1):
                result = await client.call_tool(name, {**base, field: value})
                assert result.is_error, (name, value, result)
                assert not owner.calls, (name, value, owner.calls)
            assert spec.get("minimum") == minimum
            assert spec.get("maximum") == maximum
            for value in (minimum, maximum):
                result = await client.call_tool(name, {**base, field: value})
                assert not result.is_error, (name, value, result)
                owner_id, forwarded_name, args = owner.calls.pop()
                assert owner_id == "host" and forwarded_name == name
                assert type(args[field]) is int and args[field] == value
            assert not owner.calls

    asyncio.run(scenario())


def test_topic_lifecycle_requires_observed_occurrence_and_forwards_metadata():
    class TopicOwner(WitnessOwner):
        async def call_tool(self, owner_id, tool_name, arguments):
            self.calls.append((owner_id, tool_name, arguments))
            if tool_name == "topic.resume":
                return {
                    "topic": {
                        "topicRef": "topic:fixture",
                        "state": "open",
                        "changeSequence": 12,
                        "topicHighSequence": 5,
                    }
                }
            return {"forwarded": tool_name}

    async def scenario():
        owner = TopicOwner()
        async with Client(build_server(GatewayService(owner)), raise_exceptions=False) as client:
            read = await client.call_tool("topic.resume", {"topicRef": "topic:fixture"})
            assert not read.is_error
            observed = read.structured_content["topic"]
            assert observed == {
                "topicRef": "topic:fixture",
                "state": "open",
                "changeSequence": 12,
                "topicHighSequence": 5,
            }
            owner.calls.clear()
            args = {
                "topicRef": observed["topicRef"],
                "actorRef": "actor:fixture",
                "state": "closed",
                "expectedState": observed["state"],
                "expectedHighSequence": observed["topicHighSequence"],
            }
            missing = await client.call_tool("topic.state.set", args)
            assert missing.is_error
            assert not owner.calls
            args["expectedChangeSequence"] = observed["changeSequence"]
            result = await client.call_tool("topic.state.set", args)
            assert not result.is_error
            assert owner.calls == [("host", "topic.state.set", args)]

    asyncio.run(scenario())
