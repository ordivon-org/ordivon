from __future__ import annotations

import os
from contextlib import asynccontextmanager
from importlib.metadata import version as package_version
from typing import Any

import uvicorn
from mcp.server import MCPServer
from mcp.server.mcpserver import Context

from .capabilities.host.tools import register_host_tools
from .contracts import (
    ArtifactChunk,
    CapabilityInquiryProjection,
    CapabilityProjection,
    CapabilityResolution,
    CapabilitySearchProjection,
    ExecutionObservation,
    ExecutionReceipt,
    ExecutionResolution,
    RuntimeReleaseAdmission,
    RuntimeReleaseProjection,
    SystemDescription,
)
from .security import (
    CapabilityAuthorizer,
    GatewayAuditMiddleware,
    TrustedCloudflareOperator,
    install_tool_security,
    require_release_access,
)
from .security import (
    access_verifier_from_env as _access_verifier_from_env,
)
from .security import (
    capability_authorizer_from_env as _capability_authorizer_from_env,
)
from .security import (
    owner_error_result as _owner_error_result,
)
from .security import (
    qualify_gateway_operation_ref as _qualify_gateway_operation_ref,
)
from .security import (
    require_http_execution_identity as _require_http_execution_identity,
)
from .security import (
    trusted_operator_from_env as _trusted_operator_from_env,
)
from .security import (
    verified_execution_request_id as _verified_execution_request_id,
)
from .service import GatewayService
from .transport.http import build_http_app
from .transport.upstream import McpOwnerCaller, OwnerCallError


async def _owner_boundary(call) -> Any:
    try:
        return await call
    except OwnerCallError as exc:
        return _owner_error_result(exc)


def build_server(
    service: GatewayService | None = None,
    *,
    capability_authorizer: CapabilityAuthorizer | None = None,
    protect_artifact_reads: bool = False,
    require_http_execution_identity: bool = False,
    trusted_operator: TrustedCloudflareOperator | None = None,
) -> MCPServer:
    gateway = service or GatewayService(McpOwnerCaller.from_env())

    @asynccontextmanager
    async def gateway_lifespan(_server):
        try:
            yield {}
        finally:
            close = getattr(gateway, "aclose", None)
            if callable(close):
                await close()

    server = MCPServer(
        "ordivon-gateway",
        version=package_version("ordivon-gateway"),
        lifespan=gateway_lifespan,
    )
    server.middleware.append(GatewayAuditMiddleware())
    install_tool_security(
        server,
        capability_authorizer=capability_authorizer,
        protect_artifact_reads=protect_artifact_reads,
        require_http_execution_identity=require_http_execution_identity,
        trusted_operator=trusted_operator,
    )

    @server.tool(name="system.describe")
    def system_describe() -> SystemDescription:
        return gateway.system_describe()

    @server.tool(name="capability.describe")
    async def capability_describe(capability: str | None = None) -> CapabilityProjection:
        return await gateway.capability_describe(capability)

    @server.tool(name="capability.inquire")
    async def capability_inquire(
        capability: str, verifyReadOnly: bool = False
    ) -> CapabilityInquiryProjection:
        """Optionally re-observe read-only Owner state, never issue a business effect."""
        return await gateway.capability_inquire(
            capability=capability, verify_read_only=verifyReadOnly
        )

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

    @server.tool(name="runtime.release.apply")
    async def runtime_release_apply(
        requestId: str,
        workspaceId: str,
        commit: str,
        candidateManifestDigest: str,
        expectedToolCount: int,
        ctx: Context = None,
    ) -> RuntimeReleaseAdmission:
        # Release admission policy belongs to Security; Runtime still owns the effect.
        require_release_access(
            ctx, require_http_execution_identity, capability_authorizer, trusted_operator
        )
        scoped = _verified_execution_request_id(requestId, "runtime.release.linux", ctx)
        return await _owner_boundary(
            gateway.runtime_release_apply(
                request_id=scoped,
                workspace_id=workspaceId,
                commit=commit,
                candidate_manifest_digest=candidateManifestDigest,
                expected_tool_count=expectedToolCount,
            )
        )

    @server.tool(name="runtime.release.get")
    async def runtime_release_get(requestId: str, ctx: Context = None) -> RuntimeReleaseProjection:
        # The same original principal-scoped key must be used after response
        # loss; no new release request, retry or operational preflight here.
        _require_http_execution_identity(ctx)
        scoped = _verified_execution_request_id(requestId, "runtime.release.linux", ctx)
        return await _owner_boundary(gateway.runtime_release_get(request_id=scoped))

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
        stdoutLimitBytes: int | None = None,
        stderrLimitBytes: int | None = None,
        authorityReferences: list[dict[str, Any]] | None = None,
        ctx: Context = None,
    ) -> ExecutionReceipt:
        if require_http_execution_identity:
            _require_http_execution_identity(ctx)
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
                stdout_limit_bytes=stdoutLimitBytes,
                stderr_limit_bytes=stderrLimitBytes,
                authority_references=authorityReferences,
            )
        )

    @server.tool(name="execution.resolve")
    async def execution_resolve(
        capability: str, requestId: str, ctx: Context = None
    ) -> ExecutionResolution:
        if require_http_execution_identity:
            _require_http_execution_identity(ctx)
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
        if require_http_execution_identity:
            _require_http_execution_identity(ctx)
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
        if require_http_execution_identity:
            _require_http_execution_identity(ctx)
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
        if require_http_execution_identity:
            _require_http_execution_identity(ctx)
        await _qualify_gateway_operation_ref(gateway, operationRef, capability, requestId, ctx)
        return await _owner_boundary(
            gateway.artifact_read(operationRef, artifactId, offset=offset, max_bytes=maxBytes)
        )

    register_host_tools(server, gateway, _owner_boundary)

    return server


def _reject_retired_worker_database_config() -> None:
    """Reject the deleted SQLite worker config; Gateway delegates effects to owners."""
    if os.environ.get("ORDIVON_GATEWAY_EXTERNAL_WORKER_DB", "").strip():
        raise RuntimeError(
            "Gateway SQLite External Worker was retired; use PostgreSQL Owner Runtime."
        )


def main() -> None:
    _reject_retired_worker_database_config()
    transport = os.environ.get("ORDIVON_GATEWAY_TRANSPORT", "stdio")
    gateway = GatewayService(McpOwnerCaller.from_env())
    server = build_server(
        gateway,
        capability_authorizer=_capability_authorizer_from_env(),
        protect_artifact_reads=(transport == "streamable-http"),
        require_http_execution_identity=(transport == "streamable-http"),
        trusted_operator=_trusted_operator_from_env(),
    )
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
