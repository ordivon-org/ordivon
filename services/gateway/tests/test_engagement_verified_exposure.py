"""Versioned Work accountability only crosses Gateway's verified HTTP + PDP fence.

Official in-process MCP Client probes the registered *real* Gateway tool
surface. A recording upstream is intentionally not a real Security PDP:
positive cases here prove tool-contract routing only, not end-Agent authority.
Actual deployment/PG18 positive+negative authorization remains release gated.
"""

from __future__ import annotations

import asyncio
from collections.abc import Mapping
from typing import Any

import pytest
from mcp import Client

from ordivon_gateway.mcp_server import build_server
from ordivon_gateway.service import GatewayService


class RecordingOwner:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str, dict[str, Any]]] = []

    async def call_tool(self, owner_id: str, name: str, arguments: dict[str, Any]) -> dict:
        self.calls.append((owner_id, name, arguments))
        return {"kind": "test-only-owner-response", "called": name}

    async def aclose(self) -> None:
        pass


class MockSecurityPDP:
    """Config presence only; never treat this test policy as a real actor grant."""

    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []

    async def authorize(self, **kwargs: Any) -> Mapping[str, Any]:
        self.calls.append(kwargs)
        raise RuntimeError("test policy is not an authorized actor-binding service")


ENGAGEMENT = {"work.engagement.advance", "work.engagement.list"}
REVIEW = {
    "workRef": "work:test:r13:submission",
    "expectedRevision": 4,
    "actorRef": "actor:test:r13:consumer",
    "action": {
        "type": "review",
        "claimEpoch": 1,
        "decision": "accepted",
        "rationale": "only the verified consumer may accept",
        "verificationRefs": ["evidence:test:r13:accepted"],
    },
    "clientRequestId": "request:test:r13:review",
}


@pytest.mark.parametrize(
    ("http_verified", "has_pdp", "expected_visible"),
    [
        (False, False, False),
        (False, True, False),
        (True, False, False),
        (True, True, True),
    ],
)
def test_gateway_engagement_tools_only_discoverable_with_both_trust_owners(
    http_verified: bool, has_pdp: bool, expected_visible: bool
) -> None:
    """No policy bypass by stdio or by merely setting an HTTP transport flag."""

    async def check() -> None:
        owner = RecordingOwner()
        policy = MockSecurityPDP() if has_pdp else None
        gateway = GatewayService(owner)
        async with Client(
            build_server(
                gateway,
                capability_authorizer=policy,
                require_http_execution_identity=http_verified,
                protect_artifact_reads=http_verified,
            ),
            raise_exceptions=False,
        ) as client:
            tools = {t.name: t for t in (await client.list_tools()).tools}
            assert {"work.get", "host.status", "topic.resume"} <= tools.keys()
            assert (ENGAGEMENT <= tools.keys()) is expected_visible
            if expected_visible:
                advance = tools["work.engagement.advance"]
                required = set(advance.input_schema.get("required", []))
                assert {
                    "workRef",
                    "expectedRevision",
                    "actorRef",
                    "action",
                    "clientRequestId",
                } <= required
                listing = tools["work.engagement.list"]
                assert "consumerActorRef" in listing.input_schema["properties"]
                assert "beforeWorkRef" in listing.input_schema["properties"]
                assert "maxBytes" in listing.input_schema["properties"]
        assert owner.calls == []
        if policy:
            assert policy.calls == []

    asyncio.run(check())


def test_gateway_http_engagement_denies_unverified_inprocess_client_before_owner() -> None:
    """A true principal cannot come from caller-supplied Tool arguments."""

    async def check() -> None:
        owner = RecordingOwner()
        policy = MockSecurityPDP()
        gateway = GatewayService(owner)
        async with Client(
            build_server(
                gateway,
                capability_authorizer=policy,
                require_http_execution_identity=True,
                protect_artifact_reads=True,
            ),
            raise_exceptions=False,
        ) as client:
            registered = {t.name for t in (await client.list_tools()).tools}
            assert ENGAGEMENT <= registered
            for name, arguments in (
                (
                    "work.engagement.advance",
                    {
                        **REVIEW,
                        "ordivon_access_principal": "principal:forged-by-caller",
                    },
                ),
                (
                    "work.engagement.list",
                    {
                        "consumerActorRef": "actor:test:r13:consumer",
                        "ordivon_access_principal": "principal:forged-by-caller",
                    },
                ),
            ):
                result = await client.call_tool(name, arguments)
                assert result.is_error, (name, result)
                assert not result.structured_content or (
                    result.structured_content.get("error", {}).get("code")
                    in {
                        "HTTP_INGRESS_IDENTITY_MISSING",
                        "CAPABILITY_AUTHZ_INGRESS_IDENTITY_MISSING",
                        "CAPABILITY_AUTHZ_UNAVAILABLE",
                    }
                )
        assert owner.calls == [], "no Work side effect or read even when caller forges Principal"
        assert policy.calls == [], "unverified identity must not reach external PDP"

    asyncio.run(check())


def test_gateway_authorized_owner_route_preserves_typed_work_action_without_rewriting() -> None:
    """This is a *routing* check, NOT an independent authorization grant."""

    async def check() -> None:
        owner = RecordingOwner()
        gateway = GatewayService(owner)
        result = await gateway.social_work_call("work.engagement.advance", REVIEW)
        assert result["called"] == "work.engagement.advance"
        assert owner.calls == [("host", "work.engagement.advance", REVIEW)]
        params = {
            "phase": "submitted",
            "consumerActorRef": "actor:test:r13:consumer",
            "assigneeActorRef": None,
            "limit": 5,
            "maxBytes": 262_144,
            "beforeUpdatedAt": None,
            "beforeWorkRef": None,
        }
        listed = await gateway.social_work_call("work.engagement.list", params)
        assert listed["called"] == "work.engagement.list"
        assert owner.calls[-1] == ("host", "work.engagement.list", params)

    asyncio.run(check())


def test_actual_gateway_http_ingress_authzen_pep_and_owner_route_are_composed(
    tmp_path,
) -> None:
    """Real ASGI HTTP + official MCP session, test PDP only, no real Host/PG.

    This proves a trusted ingress Principal goes through the same PEP target
    and owner adapter, while the claimed ActorRef remains an untrusted policy
    coordinate. The test deliberately does NOT claim an installed Security
    policy or actual Actor delegation, a separate production release gate.
    """
    import httpx2
    from mcp.client.session import ClientSession
    from mcp.client.streamable_http import streamable_http_client

    from ordivon_gateway.mcp_server import build_http_app

    token = "a" * 64
    token_file = tmp_path / "gateway-local-test-bearer"
    token_file.write_text(token, encoding="utf-8")
    token_file.chmod(0o600)

    class ScopedTestPDP:
        def __init__(self) -> None:
            self.requests: list[dict[str, Any]] = []

        async def authorize(self, **kwargs: Any) -> Mapping[str, Any]:
            self.requests.append(dict(kwargs))
            resource = kwargs["requested_resource"]
            properties = resource["properties"]
            permitted = (
                kwargs["principal_id"] == "principal:local-service:harness"
                and kwargs["issuer"] == "ordivon-local-service"
                and kwargs["requested_capability"] == "host.work.engagement.advance"
                and properties["claimedActorRef"] == REVIEW["actorRef"]
                and properties["workRef"] == REVIEW["workRef"]
                and properties["actionType"] == "review"
                and properties["reviewDecision"] == "accepted"
            )
            return {
                "schemaVersion": 3,
                "kind": "ordivon.security.gateway-capability-authz",
                "principalId": kwargs["principal_id"],
                "issuer": kwargs["issuer"],
                "requestedCapability": kwargs["requested_capability"],
                "requestedResource": resource,
                "qualificationTarget": True,
                "authorizationProfile": "interactive-principal-authzen",
                "outcome": "ALLOW" if permitted else "DENY",
                "reason": "test-only-exact-binding",
                "authorizationEvidence": {
                    "standard": "openid-authzen-authorization-api-1.0",
                    "requestId": "test-r13-http-bound",
                    "responseRequestId": "test-r13-http-bound",
                    "decision": permitted,
                },
                "authorityProjection": None,
                "effectAdmission": None,
            }

    async def exercise() -> None:
        owner = RecordingOwner()
        policy = ScopedTestPDP()
        server = build_server(
            GatewayService(owner),
            capability_authorizer=policy,
            require_http_execution_identity=True,
            protect_artifact_reads=True,
        )
        app = build_http_app(
            server,
            host="127.0.0.1",
            path="/mcp",
            public_origin=None,
            access_verifier=None,
            local_bearer_token_file=str(token_file),
        )

        # CloudflareAccessMiddleware wraps native Starlette/MCP ASGI app.
        inner = app._app
        async with inner.router.lifespan_context(inner):
            async with httpx2.AsyncClient(
                transport=httpx2.ASGITransport(
                    app=app,
                    client=("127.0.0.1", 50231),
                ),
                base_url="http://127.0.0.1:18899",
                headers={"Authorization": f"Bearer {token}"},
                trust_env=False,
                timeout=httpx2.Timeout(15, read=45),
            ) as http:
                async with streamable_http_client(
                    "http://127.0.0.1:18899/mcp", http_client=http
                ) as streams:
                    async with ClientSession(streams[0], streams[1]) as agent:
                        await agent.initialize()
                        names = {t.name for t in (await agent.list_tools()).tools}
                        assert ENGAGEMENT <= names
                        forged = {
                            **REVIEW,
                            "actorRef": "actor:test:r13:not-the-consumer",
                            "clientRequestId": "request:test:r13:forged",
                        }
                        rejected = await agent.call_tool(
                            "work.engagement.advance",
                            forged,
                        )
                        assert rejected.is_error
                        assert rejected.structured_content["error"]["code"] == (
                            "CAPABILITY_AUTHZ_DENIED"
                        )
                        assert owner.calls == []
                        assert (
                            policy.requests[-1]["requested_resource"]["properties"][
                                "claimedActorRef"
                            ]
                            == "actor:test:r13:not-the-consumer"
                        )

                        allowed = await agent.call_tool(
                            "work.engagement.advance",
                            REVIEW,
                        )
                        assert not allowed.is_error
                        assert allowed.structured_content["called"] == ("work.engagement.advance")
                        assert owner.calls == [("host", "work.engagement.advance", REVIEW)]
                        assert (
                            policy.requests[-1]["requested_resource"]["properties"][
                                "claimedActorRef"
                            ]
                            == REVIEW["actorRef"]
                        )
                        assert policy.requests[-1]["principal_id"] == (
                            "principal:local-service:harness"
                        )

        # An HTTP packet without trusted ingress does not even reach PDP.
        owner_calls = list(owner.calls)
        policy_calls = list(policy.requests)
        async with httpx2.AsyncClient(
            transport=httpx2.ASGITransport(
                app=app,
                client=("127.0.0.1", 50232),
            ),
            base_url="http://127.0.0.1:18899",
            trust_env=False,
        ) as anonymous:
            response = await anonymous.post(
                "/mcp",
                json={
                    "jsonrpc": "2.0",
                    "id": "anonymous",
                    "method": "tools/call",
                    "params": {
                        "name": "work.engagement.advance",
                        "arguments": REVIEW,
                    },
                },
                headers={
                    "Accept": "application/json, text/event-stream",
                    "Content-Type": "application/json",
                },
            )
            assert response.status_code == 403, response.text
        assert owner.calls == owner_calls
        assert policy.requests == policy_calls

    asyncio.run(exercise())


def test_real_gateway_http_authenticated_legacy_writer_denied_without_security(
    tmp_path,
) -> None:
    """Production ingress + real MCP sessions, but no PDP: old Writer cannot escape."""
    import httpx2
    from mcp.client.session import ClientSession
    from mcp.client.streamable_http import streamable_http_client

    from ordivon_gateway.mcp_server import build_http_app

    bearer = "c" * 64
    token_path = tmp_path / "legacy-writer-private-bearer"
    token_path.write_text(bearer, encoding="utf-8")
    token_path.chmod(0o600)

    async def scenario() -> None:
        owner = RecordingOwner()
        gateway = GatewayService(owner)
        server = build_server(
            gateway,
            capability_authorizer=None,
            require_http_execution_identity=True,
            # A caller of build_server must not need this unrelated switch
            # to protect legacy Host state-changing tools.
            protect_artifact_reads=False,
        )
        assert any(
            type(m).__name__ == "GatewayCapabilityAuthorizationMiddleware"
            for m in server.middleware
        )
        app = build_http_app(
            server,
            host="127.0.0.1",
            path="/mcp",
            public_origin=None,
            access_verifier=None,
            local_bearer_token_file=str(token_path),
        )
        inner = app._app
        async with inner.router.lifespan_context(inner):
            async with httpx2.AsyncClient(
                transport=httpx2.ASGITransport(
                    app=app,
                    client=("127.0.0.1", 50275),
                ),
                base_url="http://127.0.0.1:19077",
                headers={"Authorization": f"Bearer {bearer}"},
                trust_env=False,
                timeout=httpx2.Timeout(15, read=45),
            ) as http:
                async with streamable_http_client(
                    "http://127.0.0.1:19077/mcp", http_client=http
                ) as streams:
                    async with ClientSession(streams[0], streams[1]) as session:
                        await session.initialize()
                        names = {t.name for t in (await session.list_tools()).tools}
                        assert "work.snapshot.commit" in names
                        result = await session.call_tool(
                            "work.snapshot.commit",
                            {
                                "workRef": "work:test:old",
                                "expectedRevision": 2,
                                "snapshot": {
                                    "objective": "no unauthorized CAS",
                                    "frontier": "Owner must not be invoked",
                                },
                                "actorRef": "actor:impersonated",
                            },
                        )
                        assert result.is_error is True
                        assert result.structured_content["error"]["code"] == (
                            "CAPABILITY_AUTHZ_UNAVAILABLE"
                        )
        assert owner.calls == [], "valid machine bearer != authorization to write Work"

    asyncio.run(scenario())
