"""Real Gateway SDK -> real Rust Host HTTP -> disposable PG18 consumer proof.

This uses the production Gateway MCP client transport and Gateway server SDK.
Only the Rust Host endpoint is redirected to a loopback, disposable test owner.
No production Gateway config, broker, extra protocol, or database is created.
"""

from __future__ import annotations

import asyncio
import os
import socket
import subprocess
import sys

from mcp import Client

from ordivon_gateway.mcp_server import build_server
from ordivon_gateway.service import GatewayService
from ordivon_gateway.upstream import McpOwnerCaller, OwnerCallError, OwnerEndpoint


def require_disposable_pg18() -> None:
    dsn = os.environ.get("HOST_RUST_TEST_DSN")
    if not dsn or "127.0.0.1" not in dsn or dsn != os.environ.get("ORDIVON_HOST_V2_DSN"):
        raise RuntimeError("Gateway→Rust owner consumer requires the same disposable loopback PG18")
    if os.environ.get("ORDIVON_GATEWAY_HOST_URL"):
        # Prevent an installed production Host config from being mistaken for a
        # disposable owner in the test process, even though we inject an explicit endpoint.
        raise RuntimeError("Gateway→Rust smoke refuses inherited production Host URL")


async def consume_owner(url: str, child: subprocess.Popen) -> None:
    # This is exactly the existing Gateway's production upstream implementation,
    # not an ad hoc requests/httpx proxy and not a stub Owner caller.
    # An authenticated Host service caller is required by Rust HTTP.
    # This is NOT end-user Principal to ActorRef delegation.
    owner = McpOwnerCaller(
        {
            "host": OwnerEndpoint(
                url=url,
                bearer_token_file=os.environ["ORDIVON_HOST_V2_OWNER_BEARER_TOKEN_FILE"],
            )
        }
    )
    gateway = GatewayService(owner)
    try:
        for attempt in range(90):
            if child.poll() is not None:
                raise RuntimeError("Rust Host process exited before real Gateway owner connect")
            try:
                await owner.call_tool("host", "host.status", {"detail": "summary"})
                break
            except OwnerCallError:
                if attempt == 89:
                    raise
                await asyncio.sleep(0.15)
        async with Client(build_server(gateway), raise_exceptions=False) as agent:
            registered = {tool.name for tool in (await agent.list_tools()).tools}
            # Gateway is intentionally a thinner 29-tool Host projection; the
            # versioned Work engagement extension has not been installed here.
            assert {"work.get", "host.status", "space.list", "topic.resume"} <= registered
            assert "work.engagement.advance" not in registered
            assert "work.engagement.list" not in registered
            assert "host.pool.stats" not in registered
            assert "message.get" not in registered

            async def roundtrip(name: str, args: dict) -> dict:
                expected = await owner.call_tool("host", name, args)
                result = await agent.call_tool(name, args)
                assert not result.is_error, (name, result)
                actual = result.structured_content
                assert isinstance(actual, dict), (name, "Gateway lost structured output")
                if name == "host.status":
                    # Independent Host reads are two distinct observations, so
                    # their volatile observedAtMs can legitimately differ.
                    # Compare every stable field; never hide Doctor or authority drift.
                    assert type(actual.get("observedAtMs")) is int
                    assert type(expected.get("observedAtMs")) is int
                    actual = {key: val for key, val in actual.items() if key != "observedAtMs"}
                    expected_stable = {
                        key: val for key, val in expected.items() if key != "observedAtMs"
                    }
                    assert actual == expected_stable, (
                        name,
                        "Gateway changed stable Host status/Doctor semantics",
                    )
                else:
                    assert actual == expected, (name, "Gateway changed Host payload")
                return expected

            current = await roundtrip(
                "work.get",
                {"workRef": "work:test:rust-mcp-stdio", "revision": 2},
            )
            assert current["revision"] == 2
            listing = await roundtrip(
                "space.list",
                {"limit": 2, "maxBytes": 262144},
            )
            assert isinstance(listing["spaces"], list)
            status = await roundtrip("host.status", {"detail": "integrity"})
            assert status["detail"] == "integrity"
            assert status["authority"]["journalSchema"] == 13
            topic = await roundtrip(
                "topic.resume",
                {"topicRef": "topic:test:rust-mcp-social", "afterSequence": 0},
            )
            assert len(topic["messages"]) >= 2

            missing = await agent.call_tool(
                "work.get",
                {"workRef": "work:r9:missing:never-created"},
            )
            assert missing.is_error, missing
            envelope = missing.structured_content
            assert isinstance(envelope, dict), missing
            assert envelope.get("error", {}).get("code") == "NOT_FOUND", envelope
            assert envelope.get("error", {}).get("resourceKind") == "work", envelope
            assert envelope.get("error", {}).get("resourceRef") == (
                "work:r9:missing:never-created"
            ), envelope
            assert envelope["gatewayOwnerId"] == "host"
            assert envelope["gatewayOwnerTool"] == "work.get"

            print(
                "GATEWAY_REAL_RUST_OWNER_CONSUMER_PASS"
                " sdk_gateway=true sdk_upstream=true rust_http=true"
                " actual_payloads=4 typed_missing=1"
                " installed_gateway=false production_effect=false",
                flush=True,
            )
    finally:
        await gateway.aclose()


async def consume_verified_engagement(url: str, child: subprocess.Popen) -> None:
    """Test-only Principal delegation -> real Gateway HTTP -> Rust Host/PG18.

    A single local service Principal is explicitly delegated multiple test
    ActorRefs; this is NOT a real multi-Principal or installed Security proof.
    """
    import tempfile
    from pathlib import Path
    from typing import Any

    import httpx2
    from mcp.client.session import ClientSession
    from mcp.client.streamable_http import streamable_http_client

    from ordivon_gateway.mcp_server import build_http_app

    requester = "actor:test:verified-gateway:requester"
    worker = "actor:test:verified-gateway:worker"
    reviewer = "actor:test:verified-gateway:reviewer"
    work = "work:test:verified-gateway:work"
    space = "space:test:verified-gateway:space"
    topic = "topic:test:verified-gateway:topic"
    message = "message:test:verified-gateway:submission"

    owner = McpOwnerCaller(
        {
            "host": OwnerEndpoint(
                url=url,
                bearer_token_file=os.environ["ORDIVON_HOST_V2_OWNER_BEARER_TOKEN_FILE"],
            )
        }
    )
    gateway = GatewayService(owner)
    for actor in (requester, worker, reviewer):
        await owner.call_tool("host", "actor.declare", {"actorRef": actor, "actorKind": "agent"})
    created = await owner.call_tool(
        "host",
        "work.create",
        {
            "workRef": work,
            "workKind": "agent-accountability",
            "actorRef": requester,
            "initialSnapshot": {
                "objective": "Agent information-terminal handoff",
                "frontier": "Pending independent consumer review",
            },
        },
    )
    assert created["revision"] == 1
    await owner.call_tool(
        "host",
        "space.create",
        {
            "spaceRef": space,
            "purpose": "Agent handoff conversation",
            "actorRef": requester,
            "subjectRefs": [work],
        },
    )
    await owner.call_tool(
        "host",
        "topic.create",
        {
            "topicRef": topic,
            "spaceRef": space,
            "title": "Work engagement review",
            "actorRef": requester,
        },
    )
    await owner.call_tool(
        "host",
        "subscription.follow",
        {"actorRef": reviewer, "targetKind": "topic", "targetRef": topic},
    )
    assert (
        await owner.call_tool(
            "host",
            "subscription.list",
            {"actorRef": reviewer, "targetKind": "work"},
        )
    )["subscriptions"] == []

    class TestOnlyScopedPolicy:
        def __init__(self) -> None:
            self.decisions: list[bool] = []

        async def authorize(self, **kwargs: Any) -> dict[str, Any]:
            resource = kwargs["requested_resource"]
            attrs = resource["properties"]
            capability = kwargs["requested_capability"]
            action = attrs.get("actionType")
            actor = attrs.get("claimedActorRef")
            actor_for_action = {
                "offer": requester,
                "claim": worker,
                "submit": worker,
                "review": reviewer,
            }
            permitted = (
                kwargs["principal_id"] == "principal:local-service:harness"
                and kwargs["issuer"] == "ordivon-local-service"
                and (
                    (
                        capability == "host.work.engagement.advance"
                        and attrs.get("workRef") == work
                        and actor_for_action.get(action) == actor
                        and action in actor_for_action
                    )
                    or (
                        capability == "host.work.engagement.list"
                        and attrs.get("requestedConsumerActorRef") == reviewer
                        and attrs.get("requestedAssigneeActorRef") is None
                    )
                    or (
                        capability == "host.legacy-read"
                        and attrs.get("toolName") == "work.get"
                        and attrs.get("requestedSelectors") == {"workRef": work}
                    )
                    or (
                        capability == "host.legacy-read"
                        and attrs.get("toolName") == "attention.reentry"
                        and attrs.get("requestedSelectors") == {"actorRef": reviewer}
                    )
                    or (
                        capability == "host.legacy-read"
                        and attrs.get("toolName") == "topic.resume"
                        and attrs.get("requestedSelectors") == {"topicRef": topic}
                    )
                    or (
                        capability == "host.legacy-write"
                        and attrs.get("toolName") == "message.post"
                        and attrs.get("claimedActorRef") == worker
                        and attrs.get("spaceRef") == space
                        and attrs.get("topicRef") == topic
                    )
                    or (
                        capability == "host.legacy-write"
                        and attrs.get("toolName") == "topic.cursor.ack"
                        and attrs.get("claimedActorRef") == reviewer
                        and attrs.get("topicRef") == topic
                    )
                    or (
                        capability == "host.legacy-write"
                        and attrs.get("toolName") == "attention.ack"
                        and attrs.get("claimedActorRef") == reviewer
                    )
                )
            )
            self.decisions.append(permitted)
            return {
                "schemaVersion": 3,
                "kind": "ordivon.security.gateway-capability-authz",
                "principalId": kwargs["principal_id"],
                "issuer": kwargs["issuer"],
                "requestedCapability": capability,
                "requestedResource": resource,
                "qualificationTarget": True,
                "authorizationProfile": "interactive-principal-authzen",
                "outcome": "ALLOW" if permitted else "DENY",
                "reason": "isolated-test-only-delegation",
                "authorizationEvidence": {
                    "standard": "openid-authzen-authorization-api-1.0",
                    "requestId": "test:host-agent-consumer",
                    "responseRequestId": "test:host-agent-consumer",
                    "decision": permitted,
                },
                "authorityProjection": None,
                "effectAdmission": None,
            }

    policy = TestOnlyScopedPolicy()
    with tempfile.TemporaryDirectory(prefix="ordivon-agent-consumer-") as tmp:
        bearer = "g" * 64
        path = Path(tmp) / "gateway-token"
        path.write_text(bearer, encoding="utf-8")
        path.chmod(0o600)
        server = build_server(
            gateway,
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
            local_bearer_token_file=str(path),
        )

        async def call(session: ClientSession, name: str, args: dict) -> dict:
            result = await session.call_tool(name, args)
            assert not result.is_error, (name, result)
            assert isinstance(result.structured_content, dict)
            return result.structured_content

        def advance(rev: int, actor: str, action: dict, key: str) -> dict:
            return {
                "workRef": work,
                "expectedRevision": rev,
                "actorRef": actor,
                "action": action,
                "clientRequestId": f"request:test:agent-consumer:{key}",
            }

        try:
            inner = app._app
            async with inner.router.lifespan_context(inner):
                async with httpx2.AsyncClient(
                    transport=httpx2.ASGITransport(app=app, client=("127.0.0.1", 50911)),
                    base_url="http://127.0.0.1:18991",
                    headers={"Authorization": f"Bearer {bearer}"},
                    trust_env=False,
                    timeout=httpx2.Timeout(15, read=45),
                ) as http:
                    endpoint = "http://127.0.0.1:18991/mcp"
                    async with streamable_http_client(endpoint, http_client=http) as streams:
                        async with ClientSession(streams[0], streams[1]) as agent:
                            await agent.initialize()
                            names = {t.name for t in (await agent.list_tools()).tools}
                            assert {
                                "work.engagement.advance",
                                "work.engagement.list",
                                "work.get",
                                "attention.reentry",
                                "topic.resume",
                                "topic.cursor.ack",
                                "attention.ack",
                            } <= names
                            offered = await call(
                                agent,
                                "work.engagement.advance",
                                advance(
                                    1,
                                    requester,
                                    {
                                        "type": "offer",
                                        "consumerActorRef": reviewer,
                                        "acceptanceCriteria": [
                                            "Consumer verifies delivery references"
                                        ],
                                    },
                                    "offer",
                                ),
                            )
                            assert offered["revision"] == 2
                            inbox = await call(
                                agent,
                                "work.engagement.list",
                                {"phase": "offered", "consumerActorRef": reviewer},
                            )
                            assert work in [x["workRef"] for x in inbox["engagements"]]
                            forbidden = await agent.call_tool(
                                "work.engagement.advance",
                                advance(2, reviewer, {"type": "claim"}, "forged-claim"),
                            )
                            assert forbidden.is_error
                            assert forbidden.structured_content["error"]["code"] == (
                                "CAPABILITY_AUTHZ_DENIED"
                            )
                            current = await call(agent, "work.get", {"workRef": work})
                            assert current["revision"] == 2
                            claimed = await call(
                                agent,
                                "work.engagement.advance",
                                advance(2, worker, {"type": "claim"}, "claim"),
                            )
                            assert claimed["revision"] == 3
                            assert claimed["snapshot"]["engagement"]["claimEpoch"] == 1
                            submitted = await call(
                                agent,
                                "work.engagement.advance",
                                advance(
                                    3,
                                    worker,
                                    {
                                        "type": "submit",
                                        "claimEpoch": 1,
                                        "deliveryRef": "delivery:test:agent-consumer:1",
                                        "summary": "Agent submitted a result",
                                        "outputRefs": ["artifact:test:agent-consumer:1"],
                                        "evidenceRefs": ["receipt:test:agent-consumer:1"],
                                    },
                                    "submit",
                                ),
                            )
                            assert submitted["revision"] == 4
                            posted = await call(
                                agent,
                                "message.post",
                                {
                                    "messageRef": message,
                                    "spaceRef": space,
                                    "topicRef": topic,
                                    "authorActorRef": worker,
                                    "body": f"Submission for {work}: review delivery revision 4",
                                    "recordedAtMs": 1700000000111,
                                    "messageKind": "handoff",
                                },
                            )
                            assert posted["admission"] == "committed"

                    # Reopen an independent MCP session after the earlier
                    # consumer disconnected, then recover and review.
                    async with streamable_http_client(endpoint, http_client=http) as streams:
                        async with ClientSession(streams[0], streams[1]) as returning:
                            await returning.initialize()
                            old = await call(returning, "work.get", {"workRef": work})
                            assert old["revision"] == 4
                            changed = await call(
                                returning,
                                "attention.reentry",
                                {"actorRef": reviewer},
                            )
                            navigations = {x["navigationRef"]: x for x in changed["items"]}
                            assert topic in navigations
                            assert "followed_topic" in navigations[topic]["reasons"]
                            discussion = await call(
                                returning,
                                "topic.resume",
                                {"topicRef": topic, "afterSequence": 0},
                            )
                            assert [m["messageRef"] for m in discussion["messages"]] == [message]
                            acked_topic = await call(
                                returning,
                                "topic.cursor.ack",
                                {
                                    "actorRef": reviewer,
                                    "topicRef": topic,
                                    "cursor": discussion["messages"][-1]["sequence"],
                                },
                            )
                            assert acked_topic["cursor"] == discussion["messages"][-1]["sequence"]
                            acked_attention = await call(
                                returning,
                                "attention.ack",
                                {"actorRef": reviewer, "cursor": changed["nextAfterSequence"]},
                            )
                            assert acked_attention["cursor"] == changed["nextAfterSequence"]
                            quiet = await call(
                                returning,
                                "attention.reentry",
                                {"actorRef": reviewer},
                            )
                            assert quiet["items"] == []
                            queue = await call(
                                returning,
                                "work.engagement.list",
                                {"phase": "submitted", "consumerActorRef": reviewer},
                            )
                            assert work in [x["workRef"] for x in queue["engagements"]]
                            forged_review = await returning.call_tool(
                                "work.engagement.advance",
                                advance(
                                    4,
                                    worker,
                                    {
                                        "type": "review",
                                        "claimEpoch": 1,
                                        "decision": "accepted",
                                        "rationale": "wrong reviewer",
                                        "verificationRefs": ["evidence:test:forged"],
                                    },
                                    "forged-review",
                                ),
                            )
                            assert forged_review.is_error
                            assert forged_review.structured_content["error"]["code"] == (
                                "CAPABILITY_AUTHZ_DENIED"
                            )
                            accepted = await call(
                                returning,
                                "work.engagement.advance",
                                advance(
                                    4,
                                    reviewer,
                                    {
                                        "type": "review",
                                        "claimEpoch": 1,
                                        "decision": "accepted",
                                        "rationale": "Consumer confirmed native Host delivery",
                                        "verificationRefs": ["evidence:test:accepted"],
                                    },
                                    "accept",
                                ),
                            )
                            assert accepted["revision"] == 5
                            assert accepted["state"] == "completed"
                            assert (await call(returning, "work.get", {"workRef": work}))[
                                "revision"
                            ] == 5
                    assert child.poll() is None
                    assert sum(not x for x in policy.decisions) == 2
                    assert sum(policy.decisions) >= 8
                    subscriptions = await owner.call_tool(
                        "host",
                        "subscription.list",
                        {"actorRef": reviewer, "targetKind": "work"},
                    )
                    assert subscriptions["subscriptions"] == []
                    print(
                        "AGENT_GATEWAY_RUST_PG18_VERIFIED_CONSUMER_PASS"
                        " offer_claim_submit_review=true forged_actor_denied=2"
                        " unsubscribed_work_discovery=true cold_reentry=2_mcp_sessions"
                        " social_topic_attention_ack=true double_cursor_verified=true"
                        " security_pdp=test_only no_production_grants=true",
                        flush=True,
                    )
        finally:
            await gateway.aclose()


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("expected Rust Host executable")
    require_disposable_pg18()
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        port = listener.getsockname()[1]
    env = dict(os.environ)
    env.update(
        ORDIVON_HOST_V2_TRANSPORT="streamable-http",
        ORDIVON_HOST_V2_HOST="127.0.0.1",
        ORDIVON_HOST_V2_PORT=str(port),
        ORDIVON_HOST_V2_PATH="/mcp",
    )
    child = subprocess.Popen(
        [sys.argv[1]],
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        asyncio.run(consume_owner(f"http://127.0.0.1:{port}/mcp", child))
        asyncio.run(consume_verified_engagement(f"http://127.0.0.1:{port}/mcp", child))
    finally:
        child.terminate()
        try:
            child.wait(timeout=6)
        except subprocess.TimeoutExpired:
            child.kill()
            child.wait(timeout=6)


if __name__ == "__main__":
    main()
