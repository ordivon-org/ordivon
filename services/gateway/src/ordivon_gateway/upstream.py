from __future__ import annotations

import asyncio
import json
import logging
import os
import time
from collections.abc import Generator, Mapping
from typing import Any, Protocol

import httpx2
from mcp import Client, types
from mcp.client.streamable_http import create_mcp_http_client, streamable_http_client
from mcp.shared._otel import inject_trace_context

from .upstream_identity import (
    OwnerCallError as OwnerCallError,
)
from .upstream_identity import (
    OwnerEndpoint as OwnerEndpoint,
)
from .upstream_identity import (
    _headers_for_endpoint as _headers_for_endpoint,
)
from .upstream_identity import (
    _read_private_secret_file as _read_private_secret_file,
)
from .upstream_identity import (
    _read_private_token_file as _read_private_token_file,
)
from .upstream_identity import (
    _runtime_identity_configured as _runtime_identity_configured,
)
from .upstream_identity import (
    _validate_windows_private_secret_file as _validate_windows_private_secret_file,
)

_LOG = logging.getLogger("ordivon_gateway.upstream")

# SDK-supported choices; this is not a new Gateway protocol or a cache.
_SUPPORTED_OWNER_MCP_MODES = frozenset({"auto", "legacy", "2026-07-28"})


def _exception_summary(exc: BaseException, *, limit: int = 4) -> str:
    leaves: list[BaseException] = []

    def visit(value: BaseException) -> None:
        if isinstance(value, BaseExceptionGroup):
            for child in value.exceptions:
                visit(child)
            return
        leaves.append(value)

    visit(exc)
    rendered = [f"{type(value).__name__}: {str(value)[:180]}" for value in leaves[:limit]]
    if len(leaves) > limit:
        rendered.append(f"+{len(leaves) - limit} more")
    return "; ".join(rendered) or f"{type(exc).__name__}: {str(exc)[:180]}"


def _extract_owner_tool_error(
    result: Any, *, owner_id: str, tool_name: str
) -> dict[str, Any] | None:
    """Preserve owner-typed errors without granting arbitrary text structured authority."""
    if isinstance(result.structured_content, dict):
        candidate = result.structured_content.get("error")
        if isinstance(candidate, dict):
            return dict(candidate)

    # Host domain errors are raised by MCP tools and MCP v2 currently serializes that
    # exception as text rather than structuredContent. Recover only the exact canonical
    # Host envelope; arbitrary owner prose must remain an opaque OWNER_CALL_FAILED.
    if owner_id != "host":
        return None
    prefix = f"Error executing tool {tool_name}: "
    for item in result.content:
        text = getattr(item, "text", None)
        if not isinstance(text, str) or not text.startswith(prefix):
            continue
        try:
            candidate = json.loads(text[len(prefix) :])
        except json.JSONDecodeError:
            continue
        if not isinstance(candidate, dict):
            continue
        if candidate.get("kind") != "ordivon.host-domain-error":
            continue
        if candidate.get("schemaVersion") != 1:
            continue
        code = candidate.get("code")
        if not isinstance(code, str) or not code:
            continue
        retryable = candidate.get("retryable")
        if retryable is not None and not isinstance(retryable, bool):
            continue
        return dict(candidate)
    return None


class OwnerToolCaller(Protocol):
    async def call_tool(
        self, owner_id: str, tool_name: str, arguments: dict[str, Any]
    ) -> dict[str, Any]: ...

    def is_configured(self, owner_id: str) -> bool: ...


class OwnerEndpointAuth(httpx2.Auth):
    """Resolve Owner credentials for each HTTP request, not at pool creation.

    A long-lived HTTP pool must not freeze rotated bearer or Access credentials.
    Existing endpoint file permissions and secrets policy remain authoritative.
    """

    def __init__(self, endpoint: OwnerEndpoint) -> None:
        self._endpoint = endpoint

    def auth_flow(self, request: httpx2.Request) -> Generator[httpx2.Request, httpx2.Response]:
        headers = _headers_for_endpoint(self._endpoint)
        if headers:
            request.headers.update(headers)
        yield request


class McpOwnerCaller:
    def __init__(self, owners: Mapping[str, str | OwnerEndpoint]) -> None:
        normalized: dict[str, OwnerEndpoint] = {}
        for owner_id, value in owners.items():
            endpoint = OwnerEndpoint(value) if isinstance(value, str) else value
            url = endpoint.url.strip()
            if not url:
                continue
            has_id = endpoint.access_client_id_file is not None
            has_secret = endpoint.access_client_secret_file is not None
            if has_id != has_secret:
                raise OwnerCallError(
                    "Cloudflare Access service identity requires both client ID and client secret files"
                )
            if endpoint.bearer_token_file is not None and has_id:
                raise OwnerCallError(
                    "owner bearer and Cloudflare Access service identity are mutually exclusive"
                )
            if endpoint.mcp_mode not in _SUPPORTED_OWNER_MCP_MODES:
                raise OwnerCallError(
                    "unsupported MCP SDK protocol mode for configured Owner",
                    owner_id=owner_id,
                )
            normalized[owner_id] = OwnerEndpoint(
                url=url,
                bearer_token_file=endpoint.bearer_token_file,
                access_client_id_file=endpoint.access_client_id_file,
                access_client_secret_file=endpoint.access_client_secret_file,
                mcp_mode=endpoint.mcp_mode,
            )
        self._owners = normalized
        # One HTTP connection pool per natural Owner. MCP Client protocol
        # sessions remain request-local to avoid cross-call state ownership.
        self._http_clients: dict[str, httpx2.AsyncClient] = {}
        self._closed = False

    def _http_client(self, owner_id: str, endpoint: OwnerEndpoint) -> httpx2.AsyncClient:
        if self._closed:
            raise OwnerCallError("Owner transport is closed", owner_id=owner_id)
        client = self._http_clients.get(owner_id)
        if client is None:
            client = create_mcp_http_client(auth=OwnerEndpointAuth(endpoint))
            self._http_clients[owner_id] = client
        return client

    async def aclose(self) -> None:
        """Drain process-owned HTTP pools when the MCP server stops."""
        self._closed = True
        clients = tuple(self._http_clients.values())
        self._http_clients.clear()
        for client in clients:
            await client.aclose()

    @classmethod
    def from_env(cls) -> McpOwnerCaller:
        owners: dict[str, OwnerEndpoint] = {}
        mapping = {
            "runtime.linux": {
                "url": "ORDIVON_GATEWAY_LINUX_RUNTIME_URL",
                "bearer": "ORDIVON_GATEWAY_LINUX_RUNTIME_BEARER_TOKEN_FILE",
            },
            "runtime.windows": {
                "url": "ORDIVON_GATEWAY_WINDOWS_RUNTIME_URL",
                "bearer": "ORDIVON_GATEWAY_WINDOWS_RUNTIME_BEARER_TOKEN_FILE",
                "access_id": "ORDIVON_GATEWAY_WINDOWS_ACCESS_CLIENT_ID_FILE",
                "access_secret": "ORDIVON_GATEWAY_WINDOWS_ACCESS_CLIENT_SECRET_FILE",
                "mcp_mode": "ORDIVON_GATEWAY_WINDOWS_RUNTIME_MCP_MODE",
            },
            "host": {
                "url": "ORDIVON_GATEWAY_HOST_URL",
                "bearer": "ORDIVON_GATEWAY_HOST_BEARER_TOKEN_FILE",
            },
            "skills": {
                "url": "ORDIVON_GATEWAY_SKILLS_URL",
                "bearer": "ORDIVON_GATEWAY_SKILLS_BEARER_TOKEN_FILE",
            },
        }
        for owner_id, keys in mapping.items():
            url = os.environ.get(str(keys["url"]), "").strip()
            if not url:
                continue
            token_file = os.environ.get(str(keys["bearer"]))
            access_id_key = keys.get("access_id")
            access_secret_key = keys.get("access_secret")
            access_id = os.environ.get(str(access_id_key)) if access_id_key else None
            access_secret = os.environ.get(str(access_secret_key)) if access_secret_key else None
            mode_key = keys.get("mcp_mode")
            mcp_mode = os.environ.get(str(mode_key), "auto").strip() if mode_key else "auto"
            owners[owner_id] = OwnerEndpoint(
                url=url,
                bearer_token_file=token_file.strip() if token_file else None,
                access_client_id_file=access_id.strip() if access_id else None,
                access_client_secret_file=access_secret.strip() if access_secret else None,
                mcp_mode=mcp_mode,
            )
        return cls(owners)

    def configuration_error(self, owner_id: str) -> str | None:
        endpoint = self._owners.get(owner_id)
        if endpoint is None:
            return "owner endpoint is not configured"
        if (
            owner_id.startswith("runtime.") or owner_id == "skills"
        ) and not _runtime_identity_configured(endpoint):
            return "owner authentication is not configured"
        return None

    def is_configured(self, owner_id: str) -> bool:
        return self.configuration_error(owner_id) is None

    async def call_tool(
        self, owner_id: str, tool_name: str, arguments: dict[str, Any]
    ) -> dict[str, Any]:
        endpoint = self._owners.get(owner_id)
        configuration_error = self.configuration_error(owner_id)
        if configuration_error is not None:
            code = "OWNER_NOT_CONFIGURED" if endpoint is None else "OWNER_AUTH_NOT_CONFIGURED"
            raise OwnerCallError(
                f"{configuration_error}: {owner_id}",
                owner_id=owner_id,
                tool_name=tool_name,
                error={
                    "code": code,
                    "message": configuration_error,
                    "origin": "gateway_adapter",
                },
            )
        assert endpoint is not None

        started = time.perf_counter()
        phase = "transport_open"
        tool_elapsed_ms: int | None = None
        try:
            transport = streamable_http_client(
                endpoint.url, http_client=self._http_client(owner_id, endpoint)
            )
            # The SDK owns negotiation; the only shared object is the HTTP pool.
            phase = "session_open"
            async with Client(transport, mode=endpoint.mcp_mode, raise_exceptions=False) as client:
                # The pinned modern Windows Runtime status read is a bounded,
                # read-only, non-interactive contract. The SDK's high-level
                # Client.call_tool() follows its tools/call with tools/list to
                # validate output schemas on *each* fresh ClientSession, even
                # after the Owner has completed the status read. Use the SDK's
                # public typed send_request only for this one operation;
                # Gateway then validates Runtime status with strict B03 rules.
                # All effectful and other calls retain the full SDK driver,
                # including MRTR, schema checks, and error handling.
                typed_runtime_read = (
                    owner_id == "runtime.windows"
                    and endpoint.mcp_mode == "2026-07-28"
                    and tool_name == "runtime.describe"
                    and arguments == {"schemaVersion": 1}
                )
                phase = "typed_readonly_call" if typed_runtime_read else "sdk_client_call"
                meta: dict[str, Any] = {}
                inject_trace_context(meta)
                try:
                    if typed_runtime_read:
                        result = await client.session.send_request(
                            types.CallToolRequest(
                                params=types.CallToolRequestParams(
                                    name=tool_name,
                                    arguments=arguments,
                                    _meta=meta or None,
                                )
                            ),
                            types.CallToolResult,
                        )
                    else:
                        result = await client.call_tool(
                            tool_name,
                            arguments,
                            meta=meta or None,
                        )
                except asyncio.CancelledError:
                    # An SDK Client.call_tool can issue tools/list AFTER an
                    # already-completed wire tools/call. Cancellation here
                    # does not prove Owner failure, only the SDK boundary.
                    # The direct typed read has no SDK post-call list phase.
                    tool_elapsed_ms = int((time.perf_counter() - started) * 1000)
                    phase = (
                        "typed_readonly_call_cancelled"
                        if typed_runtime_read
                        else "sdk_client_call_cancelled"
                    )
                    raise
                else:
                    # Only a completed call reaches session teardown normally.
                    tool_elapsed_ms = int((time.perf_counter() - started) * 1000)
                    phase = "session_close"
        except asyncio.CancelledError:
            # Observation deadlines cancel the SDK task; its session cleanup
            # can then add latency. Log the exact phase without payloads,
            # credentials, response bodies, or a new Gateway state store.
            _LOG.warning(
                "gateway_owner_rpc_cancelled owner=%s tool=%s phase=%s "
                "total_ms=%d phase_before_cleanup_ms=%s",
                owner_id,
                tool_name,
                phase,
                int((time.perf_counter() - started) * 1000),
                tool_elapsed_ms,
            )
            raise
        except OwnerCallError:
            raise
        except Exception as exc:
            detail = _exception_summary(exc)
            raise OwnerCallError(
                f"owner transport/protocol call failed: {owner_id}/{tool_name}: {detail}",
                owner_id=owner_id,
                tool_name=tool_name,
                error={
                    "code": "OWNER_TRANSPORT_OR_PROTOCOL_ERROR",
                    "message": detail,
                    "origin": "gateway_adapter",
                },
            ) from exc

        if result.is_error:
            raise OwnerCallError(
                f"owner tool returned error: {owner_id}/{tool_name}",
                owner_id=owner_id,
                tool_name=tool_name,
                error=_extract_owner_tool_error(result, owner_id=owner_id, tool_name=tool_name),
            )
        payload: dict[str, Any] | None = (
            dict(result.structured_content) if isinstance(result.structured_content, dict) else None
        )
        if payload is None:
            for item in result.content:
                text = getattr(item, "text", None)
                if not isinstance(text, str):
                    continue
                try:
                    value = json.loads(text)
                except json.JSONDecodeError:
                    continue
                if isinstance(value, dict):
                    payload = value
                    break

        if payload is None:
            raise OwnerCallError(
                f"owner tool returned no structured object: {owner_id}/{tool_name}"
            )

        if typed_runtime_read:
            # The narrow typed SDK path does not perform the high-level
            # tool-output-schema lookup. Guard the versioned envelope here,
            # then defer readiness truth (including malformed booleans) to
            # the existing B03 strict owner projection.
            node = payload.get("node")
            targets = payload.get("targets")
            if (
                type(payload.get("schemaVersion")) is not int
                or payload["schemaVersion"] != 1
                or not isinstance(node, dict)
                or not isinstance(node.get("nodeId"), str)
                or not node["nodeId"]
                or not isinstance(targets, list)
                or not all(isinstance(target, dict) for target in targets)
            ):
                raise OwnerCallError(
                    "Owner returned invalid runtime.describe status envelope",
                    owner_id=owner_id,
                    tool_name=tool_name,
                    error={
                        "code": "OWNER_INVALID_STATUS_ENVELOPE",
                        "message": "runtime.describe status envelope is malformed",
                        "origin": "gateway_adapter",
                    },
                )
        return payload
