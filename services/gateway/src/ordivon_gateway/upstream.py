from __future__ import annotations

import json
import os
import stat
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

from mcp import ClientSession
from mcp.client.streamable_http import create_mcp_http_client, streamable_http_client
from mcp.types import CallToolResult


class OwnerCallError(RuntimeError):
    pass


class _RuntimeCompatibilitySession(ClientSession):
    """Use MCP transport/session semantics while skipping incompatible tools/list validation."""

    async def validate_tool_result(self, name: str, result: CallToolResult) -> None:
        return None


@dataclass(frozen=True)
class OwnerEndpoint:
    url: str
    bearer_token_file: str | None = None
    access_client_id_file: str | None = None
    access_client_secret_file: str | None = None
    validate_tool_results: bool = True


class OwnerToolCaller(Protocol):
    async def call_tool(
        self, owner_id: str, tool_name: str, arguments: dict[str, Any]
    ) -> dict[str, Any]: ...

    def is_configured(self, owner_id: str) -> bool: ...


def _read_private_secret_file(path_text: str, label: str) -> str:
    path = Path(path_text)
    if not path.is_absolute():
        raise OwnerCallError(f"{label} file must be absolute")
    metadata = path.lstat()
    if path.is_symlink() or not stat.S_ISREG(metadata.st_mode):
        raise OwnerCallError(f"{label} path must be a regular file")
    if stat.S_IMODE(metadata.st_mode) & 0o077:
        raise OwnerCallError(f"{label} file must not be group/world accessible")
    if metadata.st_size > 16_384:
        raise OwnerCallError(f"{label} file exceeds size bound")
    value = path.read_text(encoding="utf-8").strip()
    if not value or any(character.isspace() for character in value):
        raise OwnerCallError(f"{label} file must contain one non-whitespace value")
    return value


def _read_private_token_file(path_text: str) -> str:
    return _read_private_secret_file(path_text, "owner bearer token")


def _headers_for_endpoint(endpoint: OwnerEndpoint) -> dict[str, str] | None:
    if endpoint.bearer_token_file is not None:
        token = _read_private_token_file(endpoint.bearer_token_file)
        return {"Authorization": f"Bearer {token}"}
    if endpoint.access_client_id_file is not None:
        client_id = _read_private_secret_file(
            endpoint.access_client_id_file, "Cloudflare Access client ID"
        )
        client_secret = _read_private_secret_file(
            endpoint.access_client_secret_file or "",
            "Cloudflare Access client secret",
        )
        return {
            "CF-Access-Client-Id": client_id,
            "CF-Access-Client-Secret": client_secret,
        }
    return None


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
                validate_tool_results=endpoint.validate_tool_results,
            )
        self._owners = normalized

    @classmethod
    def from_env(cls) -> McpOwnerCaller:
        owners: dict[str, OwnerEndpoint] = {}
        mapping = {
            "runtime.linux": {
                "url": "ORDIVON_GATEWAY_LINUX_RUNTIME_URL",
                "bearer": "ORDIVON_GATEWAY_LINUX_RUNTIME_BEARER_TOKEN_FILE",
                "validate": False,
            },
            "runtime.windows": {
                "url": "ORDIVON_GATEWAY_WINDOWS_RUNTIME_URL",
                "bearer": "ORDIVON_GATEWAY_WINDOWS_RUNTIME_BEARER_TOKEN_FILE",
                "access_id": "ORDIVON_GATEWAY_WINDOWS_ACCESS_CLIENT_ID_FILE",
                "access_secret": "ORDIVON_GATEWAY_WINDOWS_ACCESS_CLIENT_SECRET_FILE",
                "validate": False,
            },
            "host": {
                "url": "ORDIVON_GATEWAY_HOST_URL",
                "bearer": "ORDIVON_GATEWAY_HOST_BEARER_TOKEN_FILE",
                "validate": True,
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
                validate_tool_results=bool(keys["validate"]),
            )
        return cls(owners)

    def is_configured(self, owner_id: str) -> bool:
        return owner_id in self._owners

    async def call_tool(
        self, owner_id: str, tool_name: str, arguments: dict[str, Any]
    ) -> dict[str, Any]:
        endpoint = self._owners.get(owner_id)
        if endpoint is None:
            raise OwnerCallError(f"owner is not configured: {owner_id}")

        headers = _headers_for_endpoint(endpoint)

        session_type = (
            ClientSession if endpoint.validate_tool_results else _RuntimeCompatibilitySession
        )
        async with create_mcp_http_client(headers=headers) as http_client:
            async with streamable_http_client(endpoint.url, http_client=http_client) as streams:
                read_stream, write_stream = streams
                async with session_type(read_stream, write_stream) as session:
                    await session.initialize()
                    result = await session.call_tool(tool_name, arguments)

        if result.is_error:
            detail = None
            if isinstance(result.structured_content, dict):
                detail = result.structured_content.get("error")
            raise OwnerCallError(
                f"owner tool returned error: {owner_id}/{tool_name}"
                + (f": {detail}" if detail is not None else "")
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
