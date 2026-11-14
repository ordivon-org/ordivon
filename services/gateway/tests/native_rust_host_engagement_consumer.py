"""Real Agent Work/Social/Attention consumer qualification.

One substantive test fixture with production Owner/PEP/OPA/JWT/PG18 code,
but disposable policy data, keys and database; no installed Grant claims.
The upstream read-only Gateway parity smoke lives in its original script.
"""

from __future__ import annotations

import asyncio
import os
import socket
import subprocess
import sys

from ordivon_gateway.mcp_server import build_server
from ordivon_gateway.service import GatewayService
from ordivon_gateway.upstream import McpOwnerCaller, OwnerEndpoint


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

    # Real Security owner policy, not a test Python allowlist:
    # Security's AuthZEN HTTP -> upstream OPA/Rego interpreter. The policy-data
    # file is disposable and exact-scoped. Production policy remains untouched.
    import json
    import secrets
    import shutil
    import threading
    import time

    import jwt
    import uvicorn
    from cryptography.hazmat.primitives.asymmetric import rsa

    from ordivon_gateway.access_auth import CloudflareAccessConfig, CloudflareAccessVerifier
    from ordivon_gateway.authzen_authorizer import AuthZenPrincipalAuthorizer

    repository = Path(__file__).resolve().parents[3]
    security_root = repository / "platform/security/services/gateway-authzen"
    security_source = security_root / "src"
    if str(security_source) not in sys.path:
        sys.path.insert(0, str(security_source))
    from ordivon_security_gateway_authzen.server import make_app

    opa = os.environ.get("ORDIVON_HOST_RUST_TEST_OPA") or shutil.which("opa")
    if not opa or not Path(opa).is_absolute() or not Path(opa).is_file():
        raise RuntimeError("Real OPA executable is required by Host Agent consumer fixture")
    rego = security_root / "policies/gateway_artifact.rego"
    principal = "principal:local-service:harness"
    issuer = "ordivon-local-service"
    cf_issuer = "https://test-agents.cloudflareaccess.com"
    cf_audience = "ordivon-r12-agent-mcp-test"

    # The real native verifier validates signed RS256 JWT claims, not a
    # simulated Principal string injected into MCP Tool arguments. This key
    # exists only inside the disposable Python test process.
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    verifier = CloudflareAccessVerifier(
        CloudflareAccessConfig(
            issuer=cf_issuer,
            audience=cf_audience,
            jwks_url=cf_issuer + "/cdn-cgi/access/certs",
        ),
        key_resolver=lambda _jwt: private_key.public_key(),
    )

    def signed_agent_identity(name: str) -> tuple[str, str]:
        now = int(time.time())
        assertion = jwt.encode(
            {
                "iss": cf_issuer,
                "aud": [cf_audience],
                "sub": "r12-" + name,
                "iat": now - 1,
                "exp": now + 300,
            },
            private_key,
            algorithm="RS256",
            headers={"kid": "r12-test-only-agent-signing-key"},
        )
        return assertion, verifier.verify_identity(assertion).principal

    signed_agents = {
        role: signed_agent_identity(role) for role in ("requester", "worker", "reviewer")
    }
    assert len({value[1] for value in signed_agents.values()}) == 3

    def scoped_grant(
        actor: str,
        tools: list[str],
        actions: list[str],
        *,
        principal_id: str = principal,
        grant_issuer: str = issuer,
        allowed_refs: list[str] | None = None,
    ) -> dict:
        now = int(time.time())
        return {
            "active": True,
            "principalId": principal_id,
            "issuer": grant_issuer,
            "actorRef": actor,
            "notBeforeEpochSeconds": now - 30,
            "expiresAtEpochSeconds": now + 3600,
            "allowedTools": tools,
            "allowedActions": actions,
            # Actor and object scopes are separate obligations. There are
            # no operator wildcard prefixes or unscoped Host inventory reads.
            "exactRefs": allowed_refs if allowed_refs is not None else [work, space, topic, actor],
            "namespacePrefixes": [],
            "allowUnscopedReads": False,
        }

    grants = [
        scoped_grant(requester, ["work.engagement.advance"], ["offer"]),
        scoped_grant(worker, ["work.engagement.advance", "message.post"], ["claim", "submit"]),
        scoped_grant(
            reviewer,
            [
                "work.engagement.advance",
                "work.engagement.list",
                "work.get",
                "attention.reentry",
                "topic.resume",
                "topic.cursor.ack",
                "attention.ack",
            ],
            ["review"],
        ),
    ]

    def policy_data(records: list[dict]) -> dict:
        return {
            "ordivon": {
                "security": {
                    "gateway_artifact_config": {"cf_issuer": cf_issuer},
                    "gateway_host_actor_grants": records,
                }
            }
        }

    class ObservedNativeAuthZen(AuthZenPrincipalAuthorizer):
        def __init__(self, url: str, token: str) -> None:
            super().__init__(
                url,
                bearer_token_provider=lambda: token,
                timeout_seconds=9,
                allow_insecure_loopback=True,  # disposable loopback, not production TLS
            )
            self.decisions: list[bool] = []

        async def authorize(self, **kwargs: Any) -> dict:
            response = dict(await super().authorize(**kwargs))
            self.decisions.append(response["outcome"] == "ALLOW")
            return response

    with tempfile.TemporaryDirectory(prefix="ordivon-agent-consumer-") as tmp:
        bearer = "g" * 64
        path = Path(tmp) / "gateway-token"
        path.write_text(bearer, encoding="utf-8")
        path.chmod(0o600)
        security_token = secrets.token_hex(32)
        pdp_token = Path(tmp) / "security-pdp-bearer"
        pdp_token.write_text(security_token, encoding="utf-8")
        pdp_token.chmod(0o600)
        data_path = Path(tmp) / "security-opa-policy-data.json"
        data_path.write_text(json.dumps(policy_data([])), encoding="utf-8")
        data_path.chmod(0o600)
        with socket.socket() as listener:
            listener.bind(("127.0.0.1", 0))
            pdp_port = listener.getsockname()[1]
        security_app = make_app(
            token_path=str(pdp_token),
            policy=str(rego),
            policy_data=str(data_path),
            opa=str(opa),
        )
        security_server = uvicorn.Server(
            uvicorn.Config(
                security_app,
                host="127.0.0.1",
                port=pdp_port,
                log_level="error",
                access_log=False,
            )
        )
        security_thread = threading.Thread(
            target=security_server.run,
            name="test-native-opa-authzen-loopback",
            daemon=True,
        )
        security_thread.start()
        for _ in range(100):
            if security_server.started:
                break
            if not security_thread.is_alive():
                raise RuntimeError("Isolated real AuthZEN/OPA HTTP process exited")
            await asyncio.sleep(0.05)
        else:
            raise RuntimeError("Isolated real AuthZEN/OPA HTTP did not start")

        policy = ObservedNativeAuthZen(
            f"http://127.0.0.1:{pdp_port}/access/v1/evaluation", security_token
        )
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
            access_verifier=verifier,
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
                            # No trusted policy-data grants means a verified
                            # machine Principal cannot make any Agent claim.
                            no_grant = await agent.call_tool(
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
                                    "missing-grant",
                                ),
                            )
                            assert no_grant.is_error
                            assert no_grant.structured_content["error"]["code"] == (
                                "CAPABILITY_AUTHZ_DENIED"
                            )
                            assert (await owner.call_tool("host", "work.get", {"workRef": work}))[
                                "revision"
                            ] == 1
                            # Native OPA reloads the test-owned policy-data on
                            # evaluation; this never writes installed credentials.
                            data_path.write_text(json.dumps(policy_data(grants)), encoding="utf-8")
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
                            # Revocation is applied by the *real* OPA policy
                            # engine. No new Host write may result.
                            data_path.write_text(json.dumps(policy_data([])), encoding="utf-8")
                            revoked_read = await returning.call_tool("work.get", {"workRef": work})
                            assert revoked_read.is_error
                            assert revoked_read.structured_content["error"]["code"] == (
                                "CAPABILITY_AUTHZ_DENIED"
                            )
                            assert (await owner.call_tool("host", "work.get", {"workRef": work}))[
                                "revision"
                            ] == 5
                    assert child.poll() is None
                    # Three distinct signed identities, three independent
                    # HTTP MCP sessions and three native OPA/Rego grants.
                    # No Tool parameter can impersonate another principal.
                    second_work = "work:test:verified-gateway:cf-three-principals"
                    native_created = await owner.call_tool(
                        "host",
                        "work.create",
                        {
                            "workRef": second_work,
                            "workKind": "agent-accountability",
                            "actorRef": requester,
                            "initialSnapshot": {
                                "objective": "Verify three signed Agent principals",
                                "frontier": "Separate requester/worker/reviewer grants",
                            },
                        },
                    )
                    assert native_created["revision"] == 1
                    cf_grants = [
                        scoped_grant(
                            requester,
                            ["work.engagement.advance"],
                            ["offer"],
                            principal_id=signed_agents["requester"][1],
                            grant_issuer=cf_issuer,
                            allowed_refs=[second_work, requester],
                        ),
                        scoped_grant(
                            worker,
                            ["work.engagement.advance"],
                            ["claim", "submit"],
                            principal_id=signed_agents["worker"][1],
                            grant_issuer=cf_issuer,
                            allowed_refs=[second_work, worker],
                        ),
                        scoped_grant(
                            reviewer,
                            [
                                "work.engagement.advance",
                                "work.engagement.list",
                                "work.get",
                            ],
                            ["review"],
                            principal_id=signed_agents["reviewer"][1],
                            grant_issuer=cf_issuer,
                            allowed_refs=[second_work, reviewer],
                        ),
                    ]
                    data_path.write_text(json.dumps(policy_data(cf_grants)), encoding="utf-8")

                    def signed_client(role: str):
                        return httpx2.AsyncClient(
                            transport=httpx2.ASGITransport(app=app, client=("192.0.2.10", 50912)),
                            base_url="http://127.0.0.1:18991",
                            headers={"CF-Access-Jwt-Assertion": signed_agents[role][0]},
                            timeout=httpx2.Timeout(15, read=45),
                            trust_env=False,
                        )

                    # Requester: only its signed Principal can Offer.
                    async with signed_client("requester") as req_http:
                        async with streamable_http_client(
                            endpoint, http_client=req_http
                        ) as streams:
                            async with ClientSession(streams[0], streams[1]) as req_agent:
                                await req_agent.initialize()
                                new_offer = await call(
                                    req_agent,
                                    "work.engagement.advance",
                                    {
                                        "workRef": second_work,
                                        "expectedRevision": 1,
                                        "actorRef": requester,
                                        "clientRequestId": "request:test:cf:offer",
                                        "action": {
                                            "type": "offer",
                                            "consumerActorRef": reviewer,
                                            "acceptanceCriteria": [
                                                "Three signed Principals with real OPA grants"
                                            ],
                                        },
                                    },
                                )
                                assert new_offer["revision"] == 2
                                forged_req = await req_agent.call_tool(
                                    "work.engagement.advance",
                                    {
                                        "workRef": second_work,
                                        "expectedRevision": 2,
                                        "actorRef": worker,
                                        "clientRequestId": "request:test:cf:forged-claim",
                                        "action": {"type": "claim"},
                                    },
                                )
                                assert forged_req.is_error
                                assert forged_req.structured_content["error"]["code"] == (
                                    "CAPABILITY_AUTHZ_DENIED"
                                )
                    # Worker: signed identity matches ActorRef and allowed actions.
                    async with signed_client("worker") as worker_http:
                        async with streamable_http_client(
                            endpoint, http_client=worker_http
                        ) as streams:
                            async with ClientSession(streams[0], streams[1]) as worker_agent:
                                await worker_agent.initialize()
                                signed_claim = await call(
                                    worker_agent,
                                    "work.engagement.advance",
                                    {
                                        "workRef": second_work,
                                        "expectedRevision": 2,
                                        "actorRef": worker,
                                        "clientRequestId": "request:test:cf:claim",
                                        "action": {"type": "claim"},
                                    },
                                )
                                assert signed_claim["revision"] == 3
                                signed_delivery = await call(
                                    worker_agent,
                                    "work.engagement.advance",
                                    {
                                        "workRef": second_work,
                                        "expectedRevision": 3,
                                        "actorRef": worker,
                                        "clientRequestId": "request:test:cf:submit",
                                        "action": {
                                            "type": "submit",
                                            "claimEpoch": 1,
                                            "deliveryRef": "delivery:test:cf:1",
                                            "summary": "Only signed worker could submit",
                                            "outputRefs": ["artifact:test:cf:output"],
                                            "evidenceRefs": ["receipt:test:cf:receipt"],
                                        },
                                    },
                                )
                                assert signed_delivery["revision"] == 4
                                forged_review = await worker_agent.call_tool(
                                    "work.engagement.advance",
                                    {
                                        "workRef": second_work,
                                        "expectedRevision": 4,
                                        "actorRef": reviewer,
                                        "clientRequestId": "request:test:cf:forged-review",
                                        "action": {
                                            "type": "review",
                                            "claimEpoch": 1,
                                            "decision": "accepted",
                                            "rationale": "Worker impersonated reviewer",
                                            "verificationRefs": ["evidence:test:cf:forged"],
                                        },
                                    },
                                )
                                assert forged_review.is_error
                                assert forged_review.structured_content["error"]["code"] == (
                                    "CAPABILITY_AUTHZ_DENIED"
                                )
                    # Reviewer: separate signed Principal detects submitted Work
                    # and commits only its own authorized acceptance.
                    async with signed_client("reviewer") as reviewer_http:
                        async with streamable_http_client(
                            endpoint, http_client=reviewer_http
                        ) as streams:
                            async with ClientSession(streams[0], streams[1]) as reviewer_agent:
                                await reviewer_agent.initialize()
                                new_queue = await call(
                                    reviewer_agent,
                                    "work.engagement.list",
                                    {
                                        "consumerActorRef": reviewer,
                                        "phase": "submitted",
                                    },
                                )
                                assert second_work in [
                                    x["workRef"] for x in new_queue["engagements"]
                                ]
                                signed_accepted = await call(
                                    reviewer_agent,
                                    "work.engagement.advance",
                                    {
                                        "workRef": second_work,
                                        "expectedRevision": 4,
                                        "actorRef": reviewer,
                                        "clientRequestId": "request:test:cf:accepted",
                                        "action": {
                                            "type": "review",
                                            "claimEpoch": 1,
                                            "decision": "accepted",
                                            "rationale": "Verified independent Agent claim",
                                            "verificationRefs": ["evidence:test:cf:accepted"],
                                        },
                                    },
                                )
                                assert signed_accepted["revision"] == 5
                                assert signed_accepted["state"] == "completed"
                                assert (
                                    await call(
                                        reviewer_agent,
                                        "work.get",
                                        {"workRef": second_work},
                                    )
                                )["revision"] == 5
                    # An unsigned foreign client cannot use the local bearer
                    # path because it is not loopback, nor can it invent a
                    # cryptographically verified CF identity.
                    async with httpx2.AsyncClient(
                        transport=httpx2.ASGITransport(app=app, client=("192.0.2.10", 50913)),
                        base_url="http://127.0.0.1:18991",
                        trust_env=False,
                    ) as anonymous_cf:
                        denied = await anonymous_cf.post(
                            "/mcp",
                            headers={
                                "Authorization": f"Bearer {bearer}",
                                "Content-Type": "application/json",
                            },
                            json={"jsonrpc": "2.0", "id": 1, "method": "tools/list"},
                        )
                        assert denied.status_code == 403
                    assert (await owner.call_tool("host", "work.get", {"workRef": second_work}))[
                        "revision"
                    ] == 5
                    assert len({v[1] for v in signed_agents.values()}) == 3
                    assert sum(not x for x in policy.decisions) == 6
                    print(
                        "R12_SIGNED_CF_ACCESS_THREE_PRINCIPAL_REAL_OPA_RUST_PG18_PASS"
                        " signed_identity=RS256_verified"
                        " distinct_principals=3 exact_test_grants=3"
                        " owner_issuer_bound=true forged_roles_denied=2"
                        " remote_local_bearer_denied=true final_revision=5"
                        " production_certs_or_grants=NOT_CLAIMED",
                        flush=True,
                    )

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
                        " security_pdp=REAL_OPA_AUTHZEN(test_scoped_grants)"
                        " no_grant_denied=true revocation_denied=true"
                        " no_production_grants=true",
                        flush=True,
                    )
        finally:
            security_server.should_exit = True
            await asyncio.to_thread(security_thread.join, 8)
            if security_thread.is_alive():
                raise RuntimeError("Disposable AuthZEN server did not stop")
            await gateway.aclose()
