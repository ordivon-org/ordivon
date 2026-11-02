from __future__ import annotations

import hashlib
import json
import os
from importlib.metadata import version as package_version
from typing import Any
from urllib.parse import urlsplit

import uvicorn
from mcp.server import MCPServer
from mcp.server.mcpserver import Context
from mcp.server.mcpserver.exceptions import ToolError
from mcp.server.transport_security import TransportSecuritySettings
from mcp_types import CallToolResult, TextContent
from starlette.responses import JSONResponse

from .access_auth import (
    CloudflareAccessConfig,
    CloudflareAccessMiddleware,
    CloudflareAccessVerifier,
)
from .audit import GatewayAuditMiddleware
from .capability_authz import CapabilityAuthorizer, GatewayCapabilityAuthorizationMiddleware
from .contracts import (
    ArtifactChunk,
    CapabilityProjection,
    CapabilityResolution,
    CapabilitySearchProjection,
    ExecutionObservation,
    ExecutionReceipt,
    ExecutionResolution,
    SystemDescription,
)
from .external_worker import ExternalPullWorkerTransport, require_qualified_legacy_sqlite
from .host_tools import register_host_tools
from .service import GatewayError, GatewayService
from .upstream import McpOwnerCaller, OwnerCallError
from .worker_http import attach_worker_routes


def _owner_error_result(exc: OwnerCallError) -> CallToolResult:
    error = (
        dict(exc.error)
        if exc.error is not None
        else {
            "code": "OWNER_CALL_FAILED",
            "message": str(exc),
            "origin": "gateway_adapter",
        }
    )
    structured: dict[str, Any] = {"error": error}
    if exc.owner_id is not None:
        structured["gatewayOwnerId"] = exc.owner_id
    if exc.tool_name is not None:
        structured["gatewayOwnerTool"] = exc.tool_name
    return CallToolResult(
        content=[TextContent(type="text", text=str(exc))],
        structuredContent=structured,
        isError=True,
    )


async def _owner_boundary(call) -> Any:
    try:
        return await call
    except OwnerCallError as exc:
        return _owner_error_result(exc)


def _verified_execution_scope(context: Context | None) -> tuple[str, str] | None:
    """Request-local authority from the existing verified HTTP ingress, if present."""
    try:
        request = context.request_context.request
    except ValueError, AttributeError:
        return None
    scope = getattr(request, "scope", None)
    state = scope.get("state") if isinstance(scope, dict) else None
    if not isinstance(state, dict):
        return None
    principal = state.get("ordivon_access_principal")
    issuer = state.get("ordivon_access_issuer")
    if not (isinstance(principal, str) and principal and isinstance(issuer, str) and issuer):
        return None
    return issuer, principal


def _verified_execution_request_id(
    public_request_id: str,
    capability: str,
    context: Context | None,
) -> str:
    """Scope owner idempotency to verified ingress, not caller-claimed identity.

    Unqualified direct/stdio callers retain their old requestId, with no
    claim that they have a verified HTTP principal or reattach protection.
    """
    verified = _verified_execution_scope(context)
    if verified is None:
        return public_request_id
    issuer, principal = verified
    canonical = json.dumps(
        [
            "ordivon.gateway-principal-scoped-execution-request.v1",
            issuer,
            principal,
            capability,
            public_request_id,
        ],
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return "request:gw-principal:" + hashlib.sha256(canonical).hexdigest()


async def _qualify_gateway_operation_ref(
    gateway: GatewayService,
    operation_ref: str,
    capability: str | None,
    public_request_id: str | None,
    context: Context | None,
) -> None:
    """Use the same actual owner lookup before any observe or cancel effect.

    This composes existing execution.resolve with existing owner job identity
    instead of treating a caller-supplied operationRef as principal proof.
    """
    if _verified_execution_scope(context) is None:
        return  # Legacy non-HTTP path; no identity qualification asserted.
    if not isinstance(public_request_id, str) or not public_request_id:
        raise ToolError("verified operation requires original requestId")
    if not isinstance(capability, str) or not capability:
        raise ToolError("verified operation requires original capability")
    owner_request_id = _verified_execution_request_id(public_request_id, capability, context)
    try:
        recovered = await gateway.execution_resolve(
            capability=capability, request_id=owner_request_id
        )
    except GatewayError as exc:
        raise ToolError("operationRef cannot be qualified for this principal") from exc
    if recovered.resolution != "found" or recovered.operation_ref != operation_ref:
        raise ToolError("operationRef cannot be qualified for this principal")


def build_server(
    service: GatewayService | None = None,
    *,
    capability_authorizer: CapabilityAuthorizer | None = None,
) -> MCPServer:
    gateway = service or GatewayService(McpOwnerCaller.from_env())
    server = MCPServer("ordivon-gateway", version=package_version("ordivon-gateway"))
    server.middleware.append(GatewayAuditMiddleware())
    if capability_authorizer is not None:
        server.middleware.append(GatewayCapabilityAuthorizationMiddleware(capability_authorizer))

    @server.tool(name="system.describe")
    def system_describe() -> SystemDescription:
        return gateway.system_describe()

    @server.tool(name="capability.describe")
    async def capability_describe(capability: str | None = None) -> CapabilityProjection:
        return await gateway.capability_describe(capability)

    @server.tool(name="capability.search")
    async def capability_search(
        query: str,
        category: str | None = None,
        ownerId: str | None = None,
        limit: int = 10,
        includeUnavailable: bool = True,
    ) -> CapabilitySearchProjection:
        return await gateway.capability_search(
            query=query,
            category=category,
            owner_id=ownerId,
            limit=limit,
            include_unavailable=includeUnavailable,
        )

    @server.tool(name="capability.resolve")
    async def capability_resolve(
        capability: str,
        workspaceId: str | None = None,
        agentId: str | None = None,
    ) -> CapabilityResolution:
        return await gateway.capability_resolve(
            capability=capability,
            workspace_id=workspaceId,
            agent_id=agentId,
        )

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
        ctx: Context = None,
    ) -> ExecutionReceipt:
        owner_request_id = _verified_execution_request_id(requestId, capability, ctx)
        return await _owner_boundary(
            gateway.execution_submit(
                capability=capability,
                request_id=owner_request_id,
                workspace_id=workspaceId,
                executable=executable,
                args=args,
                cwd_relative=cwdRelative,
                context=context,
                env=env,
                timeout_ms=timeoutMs,
                authority_references=authorityReferences,
            )
        )

    @server.tool(name="execution.resolve")
    async def execution_resolve(
        capability: str, requestId: str, ctx: Context = None
    ) -> ExecutionResolution:
        owner_request_id = _verified_execution_request_id(requestId, capability, ctx)
        result = await _owner_boundary(
            gateway.execution_resolve(capability=capability, request_id=owner_request_id)
        )
        # The client never sees the downstream owner namespace. Reproject the
        # original public requestId only on the exact owner response type.
        if isinstance(result, ExecutionResolution) and owner_request_id != requestId:
            return result.model_copy(update={"request_id": requestId})
        return result

    @server.tool(name="execution.get")
    async def execution_get(
        operationRef: str,
        eventLimit: int = 10,
        waitMs: int = 0,
        requestId: str | None = None,
        capability: str | None = None,
        ctx: Context = None,
    ) -> ExecutionObservation:
        await _qualify_gateway_operation_ref(gateway, operationRef, capability, requestId, ctx)
        return await _owner_boundary(
            gateway.execution_get(operationRef, event_limit=eventLimit, wait_ms=waitMs)
        )

    @server.tool(name="execution.cancel")
    async def execution_cancel(
        operationRef: str,
        requestId: str | None = None,
        capability: str | None = None,
        ctx: Context = None,
    ) -> ExecutionReceipt:
        await _qualify_gateway_operation_ref(gateway, operationRef, capability, requestId, ctx)
        return await _owner_boundary(gateway.execution_cancel(operationRef))

    @server.tool(name="artifact.read")
    async def artifact_read(
        operationRef: str,
        artifactId: str,
        offset: int = 0,
        maxBytes: int = 1_048_576,
        requestId: str | None = None,
        capability: str | None = None,
        ctx: Context = None,
    ) -> ArtifactChunk:
        # Artifact bytes have the same original execution owner as observe/cancel.
        # Reuse the trusted HTTP ingress identity fence before any owner read.
        await _qualify_gateway_operation_ref(gateway, operationRef, capability, requestId, ctx)
        return await _owner_boundary(
            gateway.artifact_read(operationRef, artifactId, offset=offset, max_bytes=maxBytes)
        )

    register_host_tools(server, gateway, _owner_boundary)

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


def _external_workers_from_env() -> ExternalPullWorkerTransport | None:
    """Gate the optional legacy SQLite transport at its actual consumer boundary."""
    external_worker_db = os.environ.get("ORDIVON_GATEWAY_EXTERNAL_WORKER_DB", "").strip()
    if not external_worker_db:
        return None
    if "://" in external_worker_db:
        raise RuntimeError(
            "ORDIVON_GATEWAY_EXTERNAL_WORKER_DB is not a PostgreSQL backend; "
            "do not treat a database DSN as a SQLite filesystem path"
        )
    require_qualified_legacy_sqlite()
    return ExternalPullWorkerTransport(external_worker_db)


def main() -> None:
    external_workers = _external_workers_from_env()
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
