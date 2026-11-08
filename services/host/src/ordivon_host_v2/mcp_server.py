from __future__ import annotations

import os
from importlib.metadata import version as package_version
from typing import Literal

import uvicorn
from mcp.server import MCPServer
from mcp.server.transport_security import TransportSecuritySettings

from .contracts import HostStatusResponse
from .http_identity import protect_host_http_app
from .mcp_tool_registration import register_social_work_tools
from .service import HostV2


def build_server(dsn: str | None = None) -> MCPServer:
    effective_dsn = dsn or os.environ["ORDIVON_HOST_V2_DSN"]
    service = HostV2(effective_dsn)
    mcp = MCPServer("ordivon-host-v2", version=package_version("ordivon-host-v2"))

    @mcp.tool(name="host.status")
    def host_status(
        detail: Literal["summary", "integrity", "history"] = "summary",
    ) -> HostStatusResponse:
        """Report PostgreSQL-native Social Work Fabric authority and bounded integrity."""
        return service.status(detail=detail)

    register_social_work_tools(mcp, effective_dsn)
    return mcp


def main() -> None:
    transport = os.environ.get("ORDIVON_HOST_V2_TRANSPORT", "stdio")
    server = build_server()
    if transport == "stdio":
        server.run()
        return
    if transport != "streamable-http":
        raise RuntimeError("ORDIVON_HOST_V2_TRANSPORT must be stdio or streamable-http")
    host = os.environ.get("ORDIVON_HOST_V2_HOST", "127.0.0.1")
    if host not in {"127.0.0.1", "::1", "localhost"}:
        raise RuntimeError("Host v2 HTTP transport must remain loopback-bound")
    port = int(os.environ.get("ORDIVON_HOST_V2_PORT", "8898"))
    path = os.environ.get("ORDIVON_HOST_V2_PATH", "/mcp")
    if not path.startswith("/"):
        raise RuntimeError("ORDIVON_HOST_V2_PATH must start with /")

    allowed_hosts = ["127.0.0.1:*", "localhost:*", "[::1]:*"]
    allowed_origins = ["http://127.0.0.1:*", "http://localhost:*", "http://[::1]:*"]
    public_origin = os.environ.get("ORDIVON_HOST_V2_PUBLIC_ORIGIN")
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
            raise RuntimeError(
                "ORDIVON_HOST_V2_PUBLIC_ORIGIN must be one canonical HTTPS origin without path/query/fragment"
            )
        canonical_public_origin = f"https://{parsed.netloc}"
        allowed_hosts.append(parsed.netloc)
        allowed_origins.append(canonical_public_origin)

    app = server.streamable_http_app(
        host=host,
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

    # Host is the enforcement boundary for its own HTTP network ingress:
    # Gateway authorization does not protect a directly reachable Host port.
    # STDIO remains a separate operator-local transport contract.
    credential_file = os.environ.get("ORDIVON_HOST_V2_BEARER_TOKEN_FILE", "").strip()
    if not credential_file:
        raise RuntimeError(
            "Host HTTP requires ORDIVON_HOST_V2_BEARER_TOKEN_FILE: "
            "an operator-managed credential shared with Gateway's Host client"
        )
    resource_host = "127.0.0.1" if host == "localhost" else host
    host_literal = f"[{resource_host}]" if ":" in resource_host else resource_host
    resource_url = f"http://{host_literal}:{port}{path}"
    protected = protect_host_http_app(
        app,
        credential_file=credential_file,
        resource_url=resource_url,
    )
    uvicorn.run(protected, host=host, port=port, log_level="info")
