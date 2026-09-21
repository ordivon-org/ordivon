from __future__ import annotations

import os

from mcp.server import MCPServer
from mcp.server.transport_security import TransportSecuritySettings

from .contracts import (
    ArtifactChunk,
    CapabilityProjection,
    ContinuityObservation,
    ContinuityPage,
    ExecutionObservation,
    ExecutionReceipt,
    SystemDescription,
)
from .service import GatewayService
from .upstream import McpOwnerCaller


def build_server(service: GatewayService | None = None) -> MCPServer:
    gateway = service or GatewayService(McpOwnerCaller.from_env())
    server = MCPServer("ordivon-gateway")

    @server.tool(name="system.describe")
    def system_describe() -> SystemDescription:
        return gateway.system_describe()

    @server.tool(name="capability.describe")
    def capability_describe(capability: str | None = None) -> CapabilityProjection:
        return gateway.capability_describe(capability)

    @server.tool(name="execution.submit")
    async def execution_submit(
        capability: str,
        requestId: str,
        workspaceId: str,
        executable: str,
        args: list[str],
        cwdRelative: str = ".",
        context: str | None = None,
        timeoutMs: int | None = None,
    ) -> ExecutionReceipt:
        return await gateway.execution_submit(
            capability=capability,
            request_id=requestId,
            workspace_id=workspaceId,
            executable=executable,
            args=args,
            cwd_relative=cwdRelative,
            context=context,
            timeout_ms=timeoutMs,
        )

    @server.tool(name="execution.get")
    async def execution_get(operationRef: str, eventLimit: int = 10) -> ExecutionObservation:
        return await gateway.execution_get(operationRef, event_limit=eventLimit)

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

    return server


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

    allowed_hosts = ["127.0.0.1:*", "localhost:*", "[::1]:*"]
    allowed_origins = [
        "http://127.0.0.1:*",
        "http://localhost:*",
        "http://[::1]:*",
    ]
    public_origin = os.environ.get("ORDIVON_GATEWAY_PUBLIC_ORIGIN")
    if public_origin:
        from urllib.parse import urlsplit

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
        allowed_hosts.append(parsed.netloc)
        allowed_origins.append(f"https://{parsed.netloc}")

    server.run(
        transport="streamable-http",
        host=host,
        port=port,
        streamable_http_path=path,
        stateless_http=True,
        json_response=True,
        max_sessions=256,
        transport_security=TransportSecuritySettings(
            enable_dns_rebinding_protection=True,
            allowed_hosts=allowed_hosts,
            allowed_origins=allowed_origins,
        ),
    )


if __name__ == "__main__":
    main()
