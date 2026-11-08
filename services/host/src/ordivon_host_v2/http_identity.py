"""Host HTTP service identity using the MCP SDK's native bearer auth middleware.

This is a transport-level M2M identity fence, *not* OAuth token issuance,
Human/Agent identity delegation or Host object authorization. It does not
introduce a second policy source or mirror Security/Runtime state.
"""

from __future__ import annotations

import hmac
import os
import stat
from pathlib import Path
from typing import Any

from mcp.server.auth.middleware.auth_context import AuthContextMiddleware
from mcp.server.auth.middleware.bearer_auth import BearerAuthBackend, RequireAuthMiddleware
from mcp.server.auth.provider import AccessToken
from pydantic import AnyHttpUrl
from starlette.middleware.authentication import AuthenticationMiddleware

HOST_MCP_SCOPE = "ordivon.host:mcp"
MAX_SECRET_BYTES = 16384


class HostServiceTokenVerifier:
    """Adapt the operator's rotating private credential to native MCP TokenVerifier.

    No token is logged, stored, forwarded to Tool arguments, or accepted from
    MCP _meta. The same FD is used for fstat and bounded read (no stat/read race).
    """

    def __init__(self, path: str, resource_url: str) -> None:
        if os.name != "posix" or not hasattr(os, "O_NOFOLLOW"):
            raise RuntimeError(
                "Host HTTP credential verification requires native POSIX no-follow file access"
            )
        if not isinstance(path, str) or not Path(path).is_absolute():
            raise ValueError("Host bearer credential file must be absolute")
        self._path = path
        self._resource_url = str(AnyHttpUrl(resource_url)).removesuffix("/")
        self._read_expected()  # Reject broken deployment before binding port.

    def _read_expected(self) -> str:
        # O_NONBLOCK avoids stalling on a substituted FIFO before fstat.
        flags = (
            os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | os.O_NOFOLLOW | getattr(os, "O_NONBLOCK", 0)
        )
        fd = os.open(self._path, flags)
        try:
            info = os.fstat(fd)
            if not stat.S_ISREG(info.st_mode) or info.st_size > MAX_SECRET_BYTES:
                raise ValueError("Host bearer credential file must be a bounded regular file")
            mode = stat.S_IMODE(info.st_mode)
            directory = os.environ.get("CREDENTIALS_DIRECTORY", "").strip()
            is_systemd_credential = (
                bool(directory)
                and Path(directory).is_absolute()
                and Path(self._path).parent == Path(directory)
                and not Path(directory).is_symlink()
            )
            # Same accepted systemd file-mode envelope as Gateway's private
            # credential reader: group read is allowed only in that directory.
            if mode & (0o037 if is_systemd_credential else 0o077):
                raise ValueError("Host bearer credential file mode is too permissive")
            chunks: list[bytes] = []
            remaining = MAX_SECRET_BYTES + 1
            while remaining > 0:
                chunk = os.read(fd, remaining)
                if not chunk:
                    break
                chunks.append(chunk)
                remaining -= len(chunk)
            data = b"".join(chunks)
            if len(data) > MAX_SECRET_BYTES:
                raise ValueError("Host bearer credential file is oversized")
            after = os.fstat(fd)
            if (
                info.st_dev,
                info.st_ino,
                info.st_size,
                info.st_mtime_ns,
                info.st_ctime_ns,
            ) != (
                after.st_dev,
                after.st_ino,
                after.st_size,
                after.st_mtime_ns,
                after.st_ctime_ns,
            ):
                raise ValueError("Host bearer credential changed during read")
        finally:
            os.close(fd)
        try:
            expected = data.decode("utf-8").strip()
        except UnicodeDecodeError as exc:
            raise ValueError("Host bearer credential must be valid UTF-8") from exc
        if len(expected) < 32 or any(ch.isspace() for ch in expected):
            raise ValueError("Host bearer credential is invalid")
        return expected

    async def verify_token(self, token: str) -> AccessToken | None:
        if not isinstance(token, str) or not token:
            return None
        # Read on every verification for operational rotation. A missing or
        # corrupted operator credential never turns into anonymous access.
        try:
            expected = self._read_expected()
        except OSError, ValueError:
            return None
        if not hmac.compare_digest(token, expected):
            return None
        return AccessToken(
            token=token,
            client_id="ordivon-gateway-local-service",
            scopes=[HOST_MCP_SCOPE],
            resource=self._resource_url,
            subject="service:ordivon-gateway",
        )


class AuthenticatedHostApp:
    """Apply native HTTP auth while preserving MCP's ASGI lifespan protocol."""

    def __init__(self, app: Any, authenticated_http: AuthenticationMiddleware) -> None:
        self.app = app
        self.authenticated_http = authenticated_http

    async def __call__(self, scope: Any, receive: Any, send: Any) -> None:
        # RequireAuthMiddleware handles HTTP requests, not ASGI lifespan.
        if scope.get("type") == "lifespan":
            await self.app(scope, receive, send)
        else:
            await self.authenticated_http(scope, receive, send)


def protect_host_http_app(
    app: Any, *, credential_file: str, resource_url: str
) -> AuthenticatedHostApp:
    """Stack official Starlette/MCP authentication around the Owner HTTP app.

    This deliberately does not advertise a fictional OAuth authorization
    server or RFC 9728 discovery: the installed local service credential is
    not an OAuth token. For federated OAuth, use the SDK's AuthSettings and
    real IdP verifier, not this operator-local adapter.
    """
    verifier = HostServiceTokenVerifier(credential_file, resource_url)
    required = RequireAuthMiddleware(app, required_scopes=[HOST_MCP_SCOPE])
    context = AuthContextMiddleware(required)
    authenticated_http = AuthenticationMiddleware(
        context,
        backend=BearerAuthBackend(verifier, resource_server_url=AnyHttpUrl(resource_url)),
    )
    return AuthenticatedHostApp(app, authenticated_http)
