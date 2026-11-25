"""Real public MCP Tool name and Owner dispatch must share a request boundary.

The actual Gateway Security PEP is the existing owner for this assertion. These
tests use its verified request and an inert fake Owner, never a live Host effect.
"""

from __future__ import annotations

import asyncio
from types import SimpleNamespace
from typing import Any

import pytest

from ordivon_gateway.capabilities.host.dispatch import HostContinuityAdapter
from ordivon_gateway.logic.execution_refs import GatewayError
from ordivon_gateway.security.capability_authz import GatewayCapabilityAuthorizationMiddleware


class _Authorizer:
    def __init__(self, outcome: str = "ALLOW") -> None:
        self.outcome = outcome

    async def authorize(self, **request: Any) -> dict[str, Any]:
        return {
            "schemaVersion": 3,
            "kind": "ordivon.security.gateway-capability-authz",
            "principalId": request["principal_id"],
            "issuer": request["issuer"],
            "requestedCapability": request["requested_capability"],
            "requestedResource": request["requested_resource"],
            "qualificationTarget": True,
            "authorizationProfile": "interactive-principal-authzen",
            "outcome": self.outcome,
            "authorizationEvidence": {
                "standard": "openid-authzen-authorization-api-1.0",
                "requestId": "action-effect-test",
                "responseRequestId": "action-effect-test",
                "decision": self.outcome == "ALLOW",
            },
            "authorityProjection": None,
            "effectAdmission": None,
        }


class _Owner:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str, dict[str, Any]]] = []

    def has_route(self, name: str) -> bool:
        return False

    async def call_tool(
        self, owner_route: str, name: str, arguments: dict[str, Any]
    ) -> dict[str, Any]:
        self.calls.append((owner_route, name, arguments))
        return {"kind": "fake-test-only-host", "name": name}


def _ctx(name: str, args: dict[str, Any]) -> Any:
    return SimpleNamespace(
        method="tools/call",
        params={"name": name, "arguments": args},
        request=SimpleNamespace(
            scope={
                "state": {
                    "ordivon_access_principal": "principal:agent:test",
                    "ordivon_access_issuer": "test-verifier",
                }
            }
        ),
    )


def test_public_host_read_cannot_delegate_host_write_after_pep_allow() -> None:
    async def scenario() -> None:
        owner = _Owner()
        adapter = HostContinuityAdapter(owner)  # type: ignore[arg-type]
        middleware = GatewayCapabilityAuthorizationMiddleware(_Authorizer())

        async def subverted(_ctx: Any) -> Any:
            return await adapter.call("work.snapshot.commit", {"workRef": "work:demo:one"})

        with pytest.raises(GatewayError, match="public.*owner|public.*action|delegat"):
            await middleware(_ctx("work.get", {"workRef": "work:demo:one"}), subverted)
        assert owner.calls == []

        async def correct(_ctx: Any) -> Any:
            return await adapter.call("work.get", {"workRef": "work:demo:one"})

        result = await middleware(_ctx("work.get", {"workRef": "work:demo:one"}), correct)
        assert result["name"] == "work.get"
        assert [row[1] for row in owner.calls] == ["work.get"]

    asyncio.run(scenario())


def test_public_host_selector_cannot_be_replaced_after_pep_allow() -> None:
    async def scenario() -> None:
        owner = _Owner()
        adapter = HostContinuityAdapter(owner)  # type: ignore[arg-type]
        middleware = GatewayCapabilityAuthorizationMiddleware(_Authorizer())

        async def retarget(_ctx: Any) -> Any:
            return await adapter.call("topic.resume", {"topicRef": "topic:other"})

        with pytest.raises(GatewayError, match="selector|target|resource"):
            await middleware(_ctx("topic.resume", {"topicRef": "topic:demo"}), retarget)
        assert owner.calls == []

    asyncio.run(scenario())


def test_unprotected_public_tool_cannot_launder_host_call() -> None:
    async def scenario() -> None:
        owner = _Owner()
        adapter = HostContinuityAdapter(owner)  # type: ignore[arg-type]
        middleware = GatewayCapabilityAuthorizationMiddleware(None)

        async def wrong(_ctx: Any) -> Any:
            return await adapter.call("work.get", {"workRef": "work:demo:one"})

        with pytest.raises(GatewayError, match="public.*owner|public.*action|delegat"):
            await middleware(_ctx("capability.describe", {"capability": "execution.linux"}), wrong)
        assert owner.calls == []

    asyncio.run(scenario())


def test_public_action_binding_is_request_scoped_and_denied_requests_never_dispatch() -> None:
    async def scenario() -> None:
        owner = _Owner()
        adapter = HostContinuityAdapter(owner)  # type: ignore[arg-type]
        denied = GatewayCapabilityAuthorizationMiddleware(_Authorizer("DENY"))
        allowed = GatewayCapabilityAuthorizationMiddleware(_Authorizer())

        async def should_not_run(_ctx: Any) -> Any:
            raise AssertionError("denied request entered Owner")

        result = await denied(_ctx("work.get", {"workRef": "work:demo:deny"}), should_not_run)
        assert result.is_error is True
        assert owner.calls == []

        async def one(target: str) -> dict[str, Any]:
            async def _forward(_ctx: Any) -> dict[str, Any]:
                await asyncio.sleep(0)  # prove concurrent contexts do not leak
                return await adapter.call("work.get", {"workRef": target})

            return await allowed(_ctx("work.get", {"workRef": target}), _forward)

        results = await asyncio.gather(one("work:demo:one"), one("work:demo:two"))
        assert [item["name"] for item in results] == ["work.get", "work.get"]
        assert [entry[2]["workRef"] for entry in owner.calls] == [
            "work:demo:one",
            "work:demo:two",
        ]

        # No request context is left behind after middleware call.
        # Existing direct local test/SDK use remains possible without a remote
        # Principal; this does NOT grant HTTP authorizations or effects.
        direct = await adapter.call("work.get", {"workRef": "work:local"})
        assert direct["name"] == "work.get"

    asyncio.run(scenario())


def test_native_mcp_sdk_preserves_public_action_into_owner_boundary() -> None:
    """Not just a synthetic ctx: use the actual SDK call_tool middleware path."""
    from mcp import Client
    from mcp.server import MCPServer

    async def scenario() -> None:
        owner = _Owner()
        adapter = HostContinuityAdapter(owner)  # type: ignore[arg-type]
        server = MCPServer("test-existing-gateway-public-action-bridge")
        server.middleware.append(GatewayCapabilityAuthorizationMiddleware(None))

        @server.tool(name="capability.describe")
        async def unrelated_public_tool() -> dict[str, Any]:
            # The public action is unprotected and must not be able to
            # impersonate an authorized Host read through its code body.
            return await adapter.call("work.get", {"workRef": "work:demo:one"})

        async with Client(server, raise_exceptions=False) as sdk:
            result = await sdk.call_tool("capability.describe", {})
        assert result.is_error is True
        assert owner.calls == []

    asyncio.run(scenario())


def test_native_sdk_authorized_host_read_uses_bound_public_identity() -> None:
    """Real SDK registration and middleware, with a test-only verified Principal."""
    from mcp import Client
    from mcp.server import MCPServer

    from ordivon_gateway.capabilities.host.work import register_host_work_tools
    from ordivon_gateway.transport.owner_error_projection import owner_error_result

    class TestIngress:
        async def __call__(self, ctx: Any, call_next: Any) -> Any:
            if ctx.method == "tools/call":
                ctx.request = SimpleNamespace(
                    scope={
                        "state": {
                            "ordivon_access_principal": "principal:agent:test",
                            "ordivon_access_issuer": "test-verifier",
                        }
                    }
                )
            return await call_next(ctx)

    async def scenario() -> None:
        owner = _Owner()
        adapter = HostContinuityAdapter(owner)  # type: ignore[arg-type]
        server = MCPServer("test-qualified-host-bound-action")
        server.middleware.append(TestIngress())
        server.middleware.append(GatewayCapabilityAuthorizationMiddleware(_Authorizer()))
        register_host_work_tools(server, adapter.call, owner_error_result)

        async with Client(server, raise_exceptions=False) as sdk:
            result = await sdk.call_tool("work.get", {"workRef": "work:demo:one"})
        assert result.is_error is False, result
        assert owner.calls == [("host", "work.get", {"workRef": "work:demo:one", "revision": None})]

    asyncio.run(scenario())


def test_host_mutation_cannot_change_bound_actor_or_body_after_pep_allow() -> None:
    """Write authorization binds the requested Actor and complete public inputs."""

    async def scenario() -> None:
        owner = _Owner()
        adapter = HostContinuityAdapter(owner)  # type: ignore[arg-type]
        middleware = GatewayCapabilityAuthorizationMiddleware(_Authorizer())
        request = {
            "messageRef": "message:demo:one",
            "spaceRef": "space:demo:one",
            "topicRef": "topic:demo:one",
            "authorActorRef": "actor:demo:author",
            "body": "exact public message",
            "recordedAtMs": 1795100000000,
            "messageKind": "note",
        }

        async def forged(_ctx: Any) -> Any:
            return await adapter.call(
                "message.post", {**request, "authorActorRef": "actor:demo:other"}
            )

        with pytest.raises(GatewayError, match="public.*argument"):
            await middleware(_ctx("message.post", request), forged)
        assert owner.calls == []

        async def correct(_ctx: Any) -> Any:
            return await adapter.call("message.post", dict(request))

        result = await middleware(_ctx("message.post", request), correct)
        assert result["name"] == "message.post"
        assert owner.calls == [("host", "message.post", request)]

    asyncio.run(scenario())


def test_public_nested_json_work_snapshot_is_original_not_mutated_after_pep_allow() -> None:
    """The original public JSON is a value, not an alias into the downstream Tool."""

    async def scenario() -> None:
        owner = _Owner()
        adapter = HostContinuityAdapter(owner)  # type: ignore[arg-type]
        middleware = GatewayCapabilityAuthorizationMiddleware(_Authorizer())
        original = {
            "workRef": "work:demo:nested",
            "workKind": "task",
            "actorRef": "actor:demo:author",
            "initialSnapshot": {
                "objective": "ORIGINAL_APPROVED_OBJECTIVE",
                "frontier": "pending",
                "nextActions": ["ORIGINAL_APPROVED_ACTION"],
            },
        }

        async def retarget_in_place(ctx: Any) -> Any:
            # The downstream handler sees the original decoded MCP JSON object.
            # Mutating a nested dict/list must NOT change the prior PEP snapshot.
            decoded = ctx.params["arguments"]
            decoded["initialSnapshot"]["objective"] = "CHANGED_AFTER_AUTHZ"
            decoded["initialSnapshot"]["nextActions"][0] = "CHANGED_AFTER_AUTHZ"
            return await adapter.call("work.create", dict(decoded))

        with pytest.raises(GatewayError, match="public Host arguments changed"):
            await middleware(_ctx("work.create", original), retarget_in_place)
        assert owner.calls == []

        accepted = {
            "workRef": "work:demo:accepted",
            "workKind": "task",
            "actorRef": "actor:demo:author",
            "initialSnapshot": {
                "objective": "UNCHANGED_ORIGINAL_OBJECTIVE",
                "frontier": "pending",
                "nextActions": ["UNCHANGED_ORIGINAL_ACTION"],
            },
        }

        async def exact(_ctx: Any) -> Any:
            return await adapter.call("work.create", dict(accepted))

        result = await middleware(_ctx("work.create", accepted), exact)
        assert result["name"] == "work.create"
        assert owner.calls == [("host", "work.create", accepted)]

    asyncio.run(scenario())


@pytest.mark.parametrize(("original", "changed"), [(1, True), (True, 1), (1, 1.0), (0.0, -0.0)])
def test_public_json_number_kind_and_boolean_do_not_alias(original, changed):
    async def scenario():
        owner = _Owner()
        adapter = HostContinuityAdapter(owner)
        middleware = GatewayCapabilityAuthorizationMiddleware(_Authorizer())
        request = {"topicRef": "topic:demo", "limit": original}

        async def changed_call(_ctx):
            return await adapter.call("topic.resume", {"topicRef": "topic:demo", "limit": changed})

        with pytest.raises(GatewayError, match="public Host arguments changed"):
            await middleware(_ctx("topic.resume", request), changed_call)
        assert owner.calls == []

    asyncio.run(scenario())


def test_omitted_selector_cannot_be_filled_with_unbound_reference():
    async def scenario():
        owner = _Owner()
        adapter = HostContinuityAdapter(owner)
        middleware = GatewayCapabilityAuthorizationMiddleware(_Authorizer())

        async def changed_call(_ctx):
            return await adapter.call("message.search", {"query": "x", "topicRef": "topic:other"})

        with pytest.raises(GatewayError, match="selector"):
            await middleware(_ctx("message.search", {"query": "x"}), changed_call)
        assert owner.calls == []

    asyncio.run(scenario())


def test_authorizer_arguments_and_resource_are_not_aliases_to_binding():
    class MutatingAuthorizer(_Authorizer):
        async def authorize(self, **request):
            request["arguments"]["initialSnapshot"]["objective"] = "changed"
            request["requested_resource"]["properties"]["requestSha256"] = "changed"
            return await super().authorize(**request)

    async def scenario():
        owner = _Owner()
        adapter = HostContinuityAdapter(owner)
        middleware = GatewayCapabilityAuthorizationMiddleware(MutatingAuthorizer())
        request = {
            "workRef": "work:demo",
            "actorRef": "actor:demo",
            "workKind": "task",
            "initialSnapshot": {"objective": "original", "frontier": "pending"},
        }

        async def changed_call(_ctx):
            return await adapter.call(
                "work.create",
                request | {"initialSnapshot": {"objective": "changed", "frontier": "pending"}},
            )

        result = await middleware(_ctx("work.create", request), changed_call)
        assert result.is_error is True
        assert result.structured_content["error"]["code"] == "CAPABILITY_AUTHZ_BINDING_MISMATCH"
        assert owner.calls == []

    asyncio.run(scenario())


def test_native_mcp_sdk_rejects_changed_scalar_and_omitted_selector():
    from mcp import Client
    from mcp.server import MCPServer

    class TestIngress:
        async def __call__(self, ctx, call_next):
            if ctx.method == "tools/call":
                ctx.request = _ctx("unused", {}).request
            return await call_next(ctx)

    async def scenario():
        owner = _Owner()
        adapter = HostContinuityAdapter(owner)
        server = MCPServer("test-host-request-representation")
        server.middleware.append(TestIngress())
        server.middleware.append(GatewayCapabilityAuthorizationMiddleware(_Authorizer()))

        @server.tool(name="topic.resume")
        async def retarget_number(topicRef: str, limit: int) -> dict[str, Any]:
            return await adapter.call("topic.resume", {"topicRef": topicRef, "limit": bool(limit)})

        @server.tool(name="message.search")
        async def retarget_omitted(query: str, topicRef: str | None = None) -> dict[str, Any]:
            return await adapter.call(
                "message.search", {"query": query, "topicRef": topicRef or "topic:other"}
            )

        async with Client(server, raise_exceptions=False) as client:
            assert (
                await client.call_tool("topic.resume", {"topicRef": "topic:demo", "limit": 1})
            ).is_error
            assert (await client.call_tool("message.search", {"query": "x"})).is_error
            assert not (
                await client.call_tool("message.search", {"query": "x", "topicRef": "topic:exact"})
            ).is_error
        assert owner.calls == [
            ("host", "message.search", {"query": "x", "topicRef": "topic:exact"})
        ]

    asyncio.run(scenario())


def test_actual_native_host_optional_selectors_default_to_null():
    from mcp import Client

    from ordivon_gateway.logic.host_tool_contracts import HOST_READ_SELECTORS
    from ordivon_gateway.mcp_server import build_server
    from ordivon_gateway.service import GatewayService

    async def scenario():
        async with Client(build_server(GatewayService(_Owner())), raise_exceptions=True) as client:
            schemas = {item.name: item.input_schema for item in (await client.list_tools()).tools}
        for name, selectors in HOST_READ_SELECTORS.items():
            schema = schemas[name]
            for selector in selectors:
                if selector not in schema.get("required", []):
                    assert "default" in schema["properties"][selector]
                    assert schema["properties"][selector]["default"] is None

    asyncio.run(scenario())


def test_public_request_witness_is_not_mutable_through_accessor():
    from ordivon_gateway.logic.host_tool_contracts import (
        bind_public_tool_call,
        current_public_tool_call,
    )

    original = {"snapshot": {"objective": "original"}}
    with bind_public_tool_call("work.create", original):
        original["snapshot"]["objective"] = "changed"
        witness = current_public_tool_call()
        assert witness is not None
        witness[1]["snapshot"]["objective"] = "changed-again"
        assert current_public_tool_call() == (
            "work.create",
            {"snapshot": {"objective": "original"}},
        )
    assert current_public_tool_call() is None
