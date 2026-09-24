from __future__ import annotations

import os
from importlib.metadata import version as package_version
from typing import Any, Literal
from urllib.parse import urlsplit

import uvicorn
from mcp.server import MCPServer
from mcp.server.transport_security import TransportSecuritySettings
from starlette.responses import JSONResponse

from .access_auth import (
    CloudflareAccessConfig,
    CloudflareAccessMiddleware,
    CloudflareAccessVerifier,
)
from .audit import GatewayAuditMiddleware
from .contracts import (
    ArtifactChunk,
    CapabilityProjection,
    ExecutionObservation,
    ExecutionReceipt,
    ExecutionResolution,
    SystemDescription,
)
from .external_worker import ExternalPullWorkerTransport
from .service import GatewayService
from .upstream import McpOwnerCaller
from .worker_http import attach_worker_routes


def build_server(service: GatewayService | None = None) -> MCPServer:
    gateway = service or GatewayService(McpOwnerCaller.from_env())
    server = MCPServer("ordivon-gateway", version=package_version("ordivon-gateway"))
    server.middleware.append(GatewayAuditMiddleware())

    @server.tool(name="system.describe")
    def system_describe() -> SystemDescription:
        return gateway.system_describe()

    @server.tool(name="capability.describe")
    async def capability_describe(capability: str | None = None) -> CapabilityProjection:
        return await gateway.capability_describe(capability)

    @server.tool(name="execution.submit")
    async def execution_submit(
        capability: str,
        requestId: str,
        workspaceId: str,
        executable: str,
        args: list[str],
        cwdRelative: str = ".",
        context: str | dict[str, Any] | None = None,
        env: dict[str, str] | None = None,
        timeoutMs: int | None = None,
        authorityReferences: list[dict[str, Any]] | None = None,
    ) -> ExecutionReceipt:
        return await gateway.execution_submit(
            capability=capability,
            request_id=requestId,
            workspace_id=workspaceId,
            executable=executable,
            args=args,
            cwd_relative=cwdRelative,
            context=context,
            env=env,
            timeout_ms=timeoutMs,
            authority_references=authorityReferences,
        )

    @server.tool(name="execution.resolve")
    async def execution_resolve(capability: str, requestId: str) -> ExecutionResolution:
        return await gateway.execution_resolve(capability=capability, request_id=requestId)

    @server.tool(name="execution.get")
    async def execution_get(
        operationRef: str, eventLimit: int = 10, waitMs: int = 0
    ) -> ExecutionObservation:
        return await gateway.execution_get(operationRef, event_limit=eventLimit, wait_ms=waitMs)

    @server.tool(name="execution.cancel")
    async def execution_cancel(operationRef: str) -> ExecutionReceipt:
        return await gateway.execution_cancel(operationRef)

    @server.tool(name="artifact.read")
    async def artifact_read(
        operationRef: str,
        artifactId: str,
        offset: int = 0,
        maxBytes: int = 1_048_576,
    ) -> ArtifactChunk:
        return await gateway.artifact_read(
            operationRef, artifactId, offset=offset, max_bytes=maxBytes
        )

    async def _host(tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        return await gateway.social_work_call(tool_name, arguments)

    @server.tool(name="host.status")
    async def host_status(
        detail: Literal["summary", "integrity", "history"] = "summary",
    ) -> dict[str, Any]:
        return await _host("host.status", {"detail": detail})

    @server.tool(name="actor.declare")
    async def actor_declare(
        actorRef: str,
        actorKind: Literal["unknown", "human", "agent", "service", "organization"],
    ) -> dict[str, Any]:
        return await _host("actor.declare", {"actorRef": actorRef, "actorKind": actorKind})

    @server.tool(name="work.create")
    async def work_create(
        workRef: str, workKind: str, actorRef: str, initialSnapshot: dict[str, Any]
    ) -> dict[str, Any]:
        return await _host(
            "work.create",
            {
                "workRef": workRef,
                "workKind": workKind,
                "actorRef": actorRef,
                "initialSnapshot": initialSnapshot,
            },
        )

    @server.tool(name="work.get")
    async def work_get(workRef: str, revision: int | None = None) -> dict[str, Any]:
        return await _host("work.get", {"workRef": workRef, "revision": revision})

    @server.tool(name="work.list")
    async def work_list(
        state: Literal["open", "completed", "abandoned"] | None = None,
        limit: int = 50,
        beforeUpdatedAt: str | None = None,
        beforeWorkRef: str | None = None,
    ) -> dict[str, Any]:
        return await _host(
            "work.list",
            {
                "state": state,
                "limit": limit,
                "beforeUpdatedAt": beforeUpdatedAt,
                "beforeWorkRef": beforeWorkRef,
            },
        )

    @server.tool(name="work.snapshot.commit")
    async def work_snapshot_commit(
        workRef: str,
        expectedRevision: int,
        snapshot: dict[str, Any],
        actorRef: str,
        continuityDisposition: Literal["continue", "complete", "abandon"] = "continue",
    ) -> dict[str, Any]:
        return await _host(
            "work.snapshot.commit",
            {
                "workRef": workRef,
                "expectedRevision": expectedRevision,
                "snapshot": snapshot,
                "actorRef": actorRef,
                "continuityDisposition": continuityDisposition,
            },
        )

    @server.tool(name="space.create")
    async def space_create(
        spaceRef: str, purpose: str, actorRef: str, subjectRefs: list[str] | None = None
    ) -> dict[str, Any]:
        return await _host(
            "space.create",
            {
                "spaceRef": spaceRef,
                "purpose": purpose,
                "actorRef": actorRef,
                "subjectRefs": subjectRefs,
            },
        )

    @server.tool(name="space.get")
    async def space_get(spaceRef: str) -> dict[str, Any]:
        return await _host("space.get", {"spaceRef": spaceRef})

    @server.tool(name="space.list")
    async def space_list(
        actorRef: str | None = None,
        subjectRef: str | None = None,
        limit: int = 50,
        beforeCreatedAt: str | None = None,
        beforeSpaceRef: str | None = None,
    ) -> dict[str, Any]:
        return await _host(
            "space.list",
            {
                "actorRef": actorRef,
                "subjectRef": subjectRef,
                "limit": limit,
                "beforeCreatedAt": beforeCreatedAt,
                "beforeSpaceRef": beforeSpaceRef,
            },
        )

    @server.tool(name="space.participation.set")
    async def space_participation_set(
        spaceRef: str, actorRef: str, standing: Literal["joined", "left", "observer"]
    ) -> dict[str, Any]:
        return await _host(
            "space.participation.set",
            {"spaceRef": spaceRef, "actorRef": actorRef, "standing": standing},
        )

    @server.tool(name="topic.create")
    async def topic_create(
        topicRef: str, spaceRef: str, title: str, actorRef: str
    ) -> dict[str, Any]:
        return await _host(
            "topic.create",
            {"topicRef": topicRef, "spaceRef": spaceRef, "title": title, "actorRef": actorRef},
        )

    @server.tool(name="topic.resume")
    async def topic_resume(
        topicRef: str, afterSequence: int = 0, limit: int = 50
    ) -> dict[str, Any]:
        return await _host(
            "topic.resume", {"topicRef": topicRef, "afterSequence": afterSequence, "limit": limit}
        )

    @server.tool(name="message.post")
    async def message_post(
        messageRef: str,
        spaceRef: str,
        topicRef: str,
        authorActorRef: str,
        body: str,
        recordedAtMs: int,
        messageKind: Literal[
            "note", "question", "proposal", "warning", "finding", "handoff"
        ] = "note",
    ) -> dict[str, Any]:
        return await _host(
            "message.post",
            {
                "messageRef": messageRef,
                "spaceRef": spaceRef,
                "topicRef": topicRef,
                "authorActorRef": authorActorRef,
                "body": body,
                "recordedAtMs": recordedAtMs,
                "messageKind": messageKind,
            },
        )

    @server.tool(name="message.search")
    async def message_search(
        query: str,
        spaceRef: str | None = None,
        topicRef: str | None = None,
        beforeSequence: int | None = None,
        limit: int = 50,
    ) -> dict[str, Any]:
        return await _host(
            "message.search",
            {
                "query": query,
                "spaceRef": spaceRef,
                "topicRef": topicRef,
                "beforeSequence": beforeSequence,
                "limit": limit,
            },
        )

    @server.tool(name="message.relation.add")
    async def message_relation_add(
        sourceMessageRef: str,
        relation: Literal[
            "reply_to", "mentions", "references", "acknowledges", "supersedes", "about"
        ],
        targetRef: str,
        actorRef: str,
    ) -> dict[str, Any]:
        return await _host(
            "message.relation.add",
            {
                "sourceMessageRef": sourceMessageRef,
                "relation": relation,
                "targetRef": targetRef,
                "actorRef": actorRef,
            },
        )

    @server.tool(name="subscription.follow")
    async def subscription_follow(
        actorRef: str, targetKind: Literal["work", "space", "topic"], targetRef: str
    ) -> dict[str, Any]:
        return await _host(
            "subscription.follow",
            {"actorRef": actorRef, "targetKind": targetKind, "targetRef": targetRef},
        )

    @server.tool(name="subscription.list")
    async def subscription_list(
        actorRef: str, targetKind: Literal["work", "space", "topic"] | None = None, limit: int = 200
    ) -> dict[str, Any]:
        return await _host(
            "subscription.list", {"actorRef": actorRef, "targetKind": targetKind, "limit": limit}
        )

    @server.tool(name="subscription.unfollow")
    async def subscription_unfollow(
        actorRef: str, targetKind: Literal["work", "space", "topic"], targetRef: str
    ) -> dict[str, Any]:
        return await _host(
            "subscription.unfollow",
            {"actorRef": actorRef, "targetKind": targetKind, "targetRef": targetRef},
        )

    @server.tool(name="attention.get")
    async def attention_get(actorRef: str, limit: int = 100) -> dict[str, Any]:
        return await _host("attention.get", {"actorRef": actorRef, "limit": limit})

    @server.tool(name="attention.delta")
    async def attention_delta(
        actorRef: str, afterSequence: int, limit: int = 100
    ) -> dict[str, Any]:
        return await _host(
            "attention.delta",
            {"actorRef": actorRef, "afterSequence": afterSequence, "limit": limit},
        )

    @server.tool(name="attention.ack")
    async def attention_ack(actorRef: str, cursor: int) -> dict[str, Any]:
        return await _host("attention.ack", {"actorRef": actorRef, "cursor": cursor})

    return server


def _bool_env(name: str, default: bool = False) -> bool:
    value = os.environ.get(name)
    if value is None:
        return default
    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes"}:
        return True
    if normalized in {"0", "false", "no"}:
        return False
    raise RuntimeError(f"{name} must be true or false")


def _access_verifier_from_env() -> CloudflareAccessVerifier | None:
    if not _bool_env("ORDIVON_GATEWAY_TRUST_CF_ACCESS"):
        return None
    issuer = os.environ.get("ORDIVON_GATEWAY_CF_ACCESS_ISSUER", "").strip().rstrip("/")
    audience = os.environ.get("ORDIVON_GATEWAY_CF_ACCESS_AUDIENCE", "").strip()
    if not issuer or not audience:
        raise RuntimeError("Gateway Cloudflare Access trust requires issuer and audience")
    jwks_url = os.environ.get(
        "ORDIVON_GATEWAY_CF_ACCESS_JWKS_URL",
        f"{issuer}/cdn-cgi/access/certs",
    ).strip()
    return CloudflareAccessVerifier(
        CloudflareAccessConfig(
            issuer=issuer,
            audience=audience,
            jwks_url=jwks_url,
        )
    )


def build_http_app(
    server: MCPServer,
    *,
    host: str,
    path: str,
    public_origin: str | None,
    access_verifier: CloudflareAccessVerifier | None,
    local_bearer_token_file: str | None = None,
    external_workers: ExternalPullWorkerTransport | None = None,
    worker_enrollment_token_file: str | None = None,
):
    allowed_hosts = ["127.0.0.1:*", "localhost:*", "[::1]:*"]
    allowed_origins = [
        "http://127.0.0.1:*",
        "http://localhost:*",
        "http://[::1]:*",
    ]
    if public_origin:
        parsed = urlsplit(public_origin)
        if (
            parsed.scheme != "https"
            or not parsed.hostname
            or parsed.username is not None
            or parsed.password is not None
            or parsed.path not in ("", "/")
            or parsed.query
            or parsed.fragment
        ):
            raise RuntimeError("ORDIVON_GATEWAY_PUBLIC_ORIGIN must be one canonical HTTPS origin")
        if access_verifier is None:
            raise RuntimeError(
                "public Gateway origin requires Cloudflare Access assertion verification"
            )
        allowed_hosts.append(parsed.netloc)
        allowed_origins.append(f"https://{parsed.netloc}")

    app = server.streamable_http_app(
        streamable_http_path=path,
        stateless_http=True,
        json_response=True,
        max_sessions=256,
        host=host,
        transport_security=TransportSecuritySettings(
            enable_dns_rebinding_protection=True,
            allowed_hosts=allowed_hosts,
            allowed_origins=allowed_origins,
        ),
    )

    async def health(_request):
        return JSONResponse(
            {"status": "ok", "service": "ordivon-gateway"},
            headers={"Cache-Control": "no-store"},
        )

    app.add_route("/health", health, methods=["GET"])
    if external_workers is not None:
        attach_worker_routes(
            app,
            external_workers,
            enrollment_token_file=worker_enrollment_token_file,
        )
    if access_verifier is not None or local_bearer_token_file is not None:
        return CloudflareAccessMiddleware(
            app,
            access_verifier,
            protected_path_prefix=path,
            local_bearer_token_file=local_bearer_token_file,
        )
    return app


def main() -> None:
    external_worker_db = os.environ.get("ORDIVON_GATEWAY_EXTERNAL_WORKER_DB")
    external_workers = (
        ExternalPullWorkerTransport(external_worker_db.strip())
        if external_worker_db and external_worker_db.strip()
        else None
    )
    gateway = GatewayService(McpOwnerCaller.from_env(), external_workers=external_workers)
    server = build_server(gateway)
    transport = os.environ.get("ORDIVON_GATEWAY_TRANSPORT", "stdio")
    if transport == "stdio":
        server.run()
        return
    if transport != "streamable-http":
        raise RuntimeError("ORDIVON_GATEWAY_TRANSPORT must be stdio or streamable-http")

    host = os.environ.get("ORDIVON_GATEWAY_HOST", "127.0.0.1")
    if host not in {"127.0.0.1", "::1", "localhost"}:
        raise RuntimeError("Gateway HTTP transport must remain loopback-bound")
    port = int(os.environ.get("ORDIVON_GATEWAY_PORT", "8899"))
    path = os.environ.get("ORDIVON_GATEWAY_PATH", "/mcp")
    if not path.startswith("/"):
        raise RuntimeError("ORDIVON_GATEWAY_PATH must start with /")

    public_origin = os.environ.get("ORDIVON_GATEWAY_PUBLIC_ORIGIN")
    access_verifier = _access_verifier_from_env()
    local_bearer_token_file = os.environ.get("ORDIVON_GATEWAY_LOCAL_BEARER_TOKEN_FILE")
    if local_bearer_token_file is not None:
        local_bearer_token_file = local_bearer_token_file.strip() or None
    app = build_http_app(
        server,
        host=host,
        path=path,
        public_origin=public_origin,
        access_verifier=access_verifier,
        local_bearer_token_file=local_bearer_token_file,
        external_workers=external_workers,
        worker_enrollment_token_file=(
            os.environ.get("ORDIVON_GATEWAY_WORKER_ENROLLMENT_TOKEN_FILE") or None
        ),
    )
    uvicorn.run(app, host=host, port=port, log_level="info")


if __name__ == "__main__":
    main()
