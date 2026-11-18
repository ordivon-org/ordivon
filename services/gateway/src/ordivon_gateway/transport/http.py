"""HTTP MCP transport and origin validation; no business Owner dispatch."""

from __future__ import annotations

from urllib.parse import urlsplit

from mcp.server import MCPServer
from mcp.server.transport_security import TransportSecuritySettings
from starlette.responses import JSONResponse

from ..security import CloudflareAccessVerifier, protect_http_app


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
    return protect_http_app(
        app,
        access_verifier=access_verifier,
        path=path,
        local_bearer_token_file=local_bearer_token_file,
    )
