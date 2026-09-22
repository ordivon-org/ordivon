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
    CollaborationPage,
    CollaborationPostReceipt,
    CollaborationSearch,
    ContinuityAttention,
    ContinuityMutationReceipt,
    ContinuityObservation,
    ContinuityObserved,
    ContinuityPage,
    ExecutionObservation,
    ExecutionReceipt,
    ExecutionResolution,
    SystemDescription,
)
from .service import GatewayService
from .upstream import McpOwnerCaller


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
        context: str | None = None,
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

    @server.tool(name="continuity.get")
    async def continuity_get(taskId: str) -> ContinuityObservation:
        return await gateway.continuity_get(taskId)

    @server.tool(name="continuity.list")
    async def continuity_list(
        goalId: str | None = None,
        limit: int = 50,
        cursor: str | None = None,
        includeTerminal: bool = False,
    ) -> ContinuityPage:
        return await gateway.continuity_list(
            goal_id=goalId,
            limit=limit,
            cursor=cursor,
            include_terminal=includeTerminal,
        )

    @server.tool(name="continuity.observe")
    async def continuity_observe(
        taskId: str, expectedRevision: int | None = None, eventLimit: int = 5
    ) -> ContinuityObserved:
        return await gateway.continuity_observe(
            taskId, expected_revision=expectedRevision, event_limit=eventLimit
        )

    @server.tool(name="continuity.adopt")
    async def continuity_adopt(
        taskId: str, goalId: str, checkpoint: dict[str, Any], writerLabel: str | None = None
    ) -> ContinuityMutationReceipt:
        return await gateway.continuity_adopt(
            task_id=taskId, goal_id=goalId, checkpoint=checkpoint, writer_label=writerLabel
        )

    @server.tool(name="continuity.checkpoint")
    async def continuity_checkpoint(
        taskId: str,
        expectedRevision: int,
        checkpoint: dict[str, Any],
        disposition: Literal["continue", "complete", "abandon"] = "continue",
        writerLabel: str | None = None,
    ) -> ContinuityMutationReceipt:
        return await gateway.continuity_checkpoint(
            task_id=taskId,
            expected_revision=expectedRevision,
            checkpoint=checkpoint,
            disposition=disposition,
            writer_label=writerLabel,
        )

    @server.tool(name="continuity.attention")
    async def continuity_attention(afterSequence: int, limit: int = 100) -> ContinuityAttention:
        return await gateway.continuity_attention(after_sequence=afterSequence, limit=limit)

    @server.tool(name="collaboration.post")
    async def collaboration_post(
        clientMessageId: str,
        authorLabel: str,
        message: str,
        messageKind: Literal["note", "question", "proposal", "warning", "reply"] = "note",
        topic: str | None = None,
        replyToClientMessageId: str | None = None,
        taskId: str | None = None,
    ) -> CollaborationPostReceipt:
        return await gateway.collaboration_post(
            client_message_id=clientMessageId,
            author_label=authorLabel,
            message=message,
            message_kind=messageKind,
            topic=topic,
            reply_to_client_message_id=replyToClientMessageId,
            task_id=taskId,
        )

    @server.tool(name="collaboration.list")
    async def collaboration_list(
        afterSequence: int | None = None,
        limit: int = 50,
        topic: str | None = None,
        clientMessageId: str | None = None,
        replyToClientMessageId: str | None = None,
        replyToAuthorLabel: str | None = None,
    ) -> CollaborationPage:
        return await gateway.collaboration_list(
            after_sequence=afterSequence,
            limit=limit,
            topic=topic,
            client_message_id=clientMessageId,
            reply_to_client_message_id=replyToClientMessageId,
            reply_to_author_label=replyToAuthorLabel,
        )

    @server.tool(name="collaboration.search")
    async def collaboration_search(query: str, limit: int = 20) -> CollaborationSearch:
        return await gateway.collaboration_search(query, limit=limit)

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
    if access_verifier is not None or local_bearer_token_file is not None:
        return CloudflareAccessMiddleware(
            app,
            access_verifier,
            protected_path_prefix=path,
            local_bearer_token_file=local_bearer_token_file,
        )
    return app


def main() -> None:
    server = build_server()
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
    )
    uvicorn.run(app, host=host, port=port, log_level="info")


if __name__ == "__main__":
    main()
