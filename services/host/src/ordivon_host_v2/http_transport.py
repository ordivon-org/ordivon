"""Host HTTP ingress configuration and workload credential boundary.

Only transport selection and authentication happen here; the Host business
MCP Server remains an unaware consumer. Reuse the existing native MCP TokenVerifier,
never infer authorization from Host Social ActorRef or MCP Tool arguments.
"""

from __future__ import annotations

import os

import uvicorn
from mcp.server import MCPServer
from mcp.server.transport_security import TransportSecuritySettings

from .http_identity import protect_host_http_app


def serve_host_http(server: MCPServer) -> None:
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
    credential_file = os.environ.get("ORDIVON_HOST_V2_OWNER_BEARER_TOKEN_FILE", "").strip()
    # Compatibility is explicit and only preserves the already-installed
    # loopback Host ingress during its consumers' Gateway/Cloudflare migration.
    # It never supersedes an installed Owner bearer or binds a public socket.
    legacy_direct_http = os.environ.get("ORDIVON_HOST_V2_LEGACY_DIRECT_HTTP", "").strip()
    if legacy_direct_http not in ("", "true"):
        raise RuntimeError("ORDIVON_HOST_V2_LEGACY_DIRECT_HTTP must be true or unset")
    if legacy_direct_http and credential_file:
        raise RuntimeError("legacy direct HTTP cannot coexist with Owner bearer")
    if legacy_direct_http:
        if not public_origin:
            raise RuntimeError("legacy direct HTTP requires the existing HTTPS public origin")
        uvicorn.run(app, host=host, port=port, log_level="info")
        return
    if not credential_file:
        raise RuntimeError("Host HTTP requires ORDIVON_HOST_V2_OWNER_BEARER_TOKEN_FILE")
    resource_host = "127.0.0.1" if host == "localhost" else host
    host_literal = f"[{resource_host}]" if ":" in resource_host else resource_host
    resource_url = f"http://{host_literal}:{port}{path}"
    protected = protect_host_http_app(
        app,
        credential_file=credential_file,
        resource_url=resource_url,
    )
    uvicorn.run(protected, host=host, port=port, log_level="info")
