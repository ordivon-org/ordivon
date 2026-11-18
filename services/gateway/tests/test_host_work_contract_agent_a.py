"""Agent A: source-only Host Work MCP contract falsifiers.

The Gateway must reject malformed Host Work input before forwarding it.
No Host database, Security grant, installed Gateway, or effect is exercised.
"""

from __future__ import annotations

import asyncio

from mcp import Client
from mcp.server import MCPServer

from ordivon_gateway.host_work_tools import register_host_work_tools


def test_native_sdk_rejects_invalid_host_work_arguments_before_forward() -> None:
    async def scenario() -> None:
        forwarded: list[tuple[str, dict]] = []

        async def fake_host(name: str, args: dict) -> dict:
            forwarded.append((name, args))
            return {"forwarded": name}

        server = MCPServer("gateway-agent-a-host-work-contract")
        register_host_work_tools(server, fake_host)

        invalid = (
            (
                "work.create",
                {
                    "workRef": "work:fixture",
                    "workKind": "task",
                    "actorRef": "actor:fixture",
                    "initialSnapshot": {"frontier": "open"},
                },
            ),
            (
                "work.create",
                {
                    "workRef": "work:fixture",
                    "workKind": "task",
                    "actorRef": "actor:fixture",
                    "initialSnapshot": {
                        "objective": "x",
                        "frontier": "open",
                        "unexpected": "must-not-pass",
                    },
                },
            ),
            (
                "work.create",
                {
                    "workRef": "work:fixture",
                    "workKind": "task",
                    "actorRef": "actor:fixture",
                    "initialSnapshot": {
                        "objective": "x",
                        "frontier": "open",
                        "established": ["x"] * 129,
                    },
                },
            ),
            (
                "work.snapshot.commit",
                {
                    "workRef": "work:fixture",
                    "expectedRevision": 1,
                    "actorRef": "actor:fixture",
                    "snapshot": {"objective": "x", "frontier": "open", "established": ["  "]},
                },
            ),
            ("work.get", {"workRef": "work:fixture", "revision": 0}),
            ("work.get", {"workRef": "work:fixture", "revision": False}),
            ("work.get", {"workRef": "work:fixture", "revision": 2**63}),
            ("work.list", {"limit": 0}),
            ("work.list", {"limit": 201}),
            ("work.list", {"limit": True}),
            (
                "work.snapshot.commit",
                {
                    "workRef": "work:fixture",
                    "expectedRevision": 0,
                    "actorRef": "actor:fixture",
                    "snapshot": {"objective": "x", "frontier": "open"},
                },
            ),
            (
                "work.snapshot.commit",
                {
                    "workRef": "work:fixture",
                    "expectedRevision": 2**63 - 1,
                    "actorRef": "actor:fixture",
                    "snapshot": {"objective": "x", "frontier": "open"},
                },
            ),
            (
                "work.snapshot.commit",
                {
                    "workRef": "work:fixture",
                    "expectedRevision": 1,
                    "actorRef": "actor:fixture",
                    "snapshot": {"frontier": "open"},
                },
            ),
        )
        async with Client(server, raise_exceptions=True) as client:
            tools = {tool.name: tool for tool in (await client.list_tools()).tools}
            assert len(tools) == 6
            work_create = tools["work.create"].input_schema
            work_commit = tools["work.snapshot.commit"].input_schema
            # Preserve the original ChatGPT/public 0.10.12 MCP schema, while
            # validating the same strict Host wire contracts internally.
            initial = work_create["properties"]["initialSnapshot"]
            committed = work_commit["properties"]["snapshot"]
            assert initial["type"] == "object" and initial["additionalProperties"] is True
            assert committed["type"] == "object" and committed["additionalProperties"] is True
            assert "$ref" not in initial and "$ref" not in committed
            assert tools["work.get"].input_schema["properties"]["revision"]["anyOf"][0] == {
                "type": "integer",
            }
            assert tools["work.list"].input_schema["properties"]["limit"] == {
                "default": 50,
                "title": "Limit",
                "type": "integer",
            }
            assert work_commit["properties"]["expectedRevision"]["type"] == "integer"
            for name, args in invalid:
                result = await client.call_tool(name, args)
                assert result.is_error is True, (name, args, result)
                # A rejected legacy input has the old public Gateway error
                # envelope, not a traceback-only MCP SDK validation failure.
                structured = result.structured_content
                # A JSON boolean violates the ORIGINAL integer inputSchema.
                # The native SDK can reject it before our Tool body runs,
                # so no Server-side owner envelope can be promised there.
                sdk_rejects_boolean = (name == "work.get" and args.get("revision") is False) or (
                    name == "work.list" and args.get("limit") is True
                )
                if sdk_rejects_boolean:
                    assert structured is None
                    continue
                assert isinstance(structured, dict), (name, args, result)
                assert structured["error"]["code"] == "OWNER_CALL_FAILED"
                assert structured["error"]["origin"] == "gateway_adapter"
                assert structured["gatewayOwnerId"] == "host"
                assert structured["gatewayOwnerTool"] == name
                assert result.content[0].text == f"owner tool returned error: host/{name}"
            assert forwarded == []

            valid_snapshot = {
                "objective": "Build exact source witness",
                "frontier": "qualify input",
                "nextActions": ["check Host source"],
            }
            valid = (
                (
                    "work.create",
                    {
                        "workRef": "work:fixture",
                        "workKind": "task",
                        "actorRef": "actor:fixture",
                        "initialSnapshot": valid_snapshot,
                    },
                ),
                ("work.get", {"workRef": "work:fixture", "revision": 1}),
                ("work.list", {"limit": 200}),
                (
                    "work.snapshot.commit",
                    {
                        "workRef": "work:fixture",
                        "expectedRevision": 1,
                        "snapshot": valid_snapshot,
                        "actorRef": "actor:fixture",
                    },
                ),
            )
            for name, args in valid:
                result = await client.call_tool(name, args)
                assert result.is_error is False, (name, result)
            assert [item[0] for item in forwarded] == [name for name, _ in valid]
            assert forwarded[0][1]["initialSnapshot"] == valid_snapshot
            assert forwarded[-1][1]["snapshot"] == valid_snapshot

    asyncio.run(scenario())
