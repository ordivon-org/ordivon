from __future__ import annotations

import json
import os
from collections.abc import Mapping
from typing import Any, Protocol

from mcp import Client
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
            normalized[owner_id] = OwnerEndpoint(
                url=url,
                bearer_token_file=endpoint.bearer_token_file,
                access_client_id_file=endpoint.access_client_id_file,
                access_client_secret_file=endpoint.access_client_secret_file,
            )
        self._owners = normalized

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
            owners[owner_id] = OwnerEndpoint(
                url=url,
                bearer_token_file=token_file.strip() if token_file else None,
                access_client_id_file=access_id.strip() if access_id else None,
                access_client_secret_file=access_secret.strip() if access_secret else None,
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

        try:
            headers = _headers_for_endpoint(endpoint)
            async with create_mcp_http_client(headers=headers) as http_client:
                transport = streamable_http_client(endpoint.url, http_client=http_client)
                # MCP v2 Client owns modern discovery, output-schema validation, and
                # legacy fallback. Gateway does not hand-code protocol negotiation.
                async with Client(transport, mode="auto", raise_exceptions=False) as client:
                    meta: dict[str, Any] = {}
                    inject_trace_context(meta)
                    result = await client.call_tool(
                        tool_name,
                        arguments,
                        meta=meta or None,
                    )
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
        if isinstance(result.structured_content, dict):
            return dict(result.structured_content)

        for item in result.content:
            text = getattr(item, "text", None)
            if not isinstance(text, str):
                continue
            try:
                value = json.loads(text)
            except json.JSONDecodeError:
                continue
            if isinstance(value, dict):
                return value

        raise OwnerCallError(f"owner tool returned no structured object: {owner_id}/{tool_name}")
