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
    validate_tool_results: bool = True


class OwnerToolCaller(Protocol):
    async def call_tool(
        self, owner_id: str, tool_name: str, arguments: dict[str, Any]
    ) -> dict[str, Any]: ...

    def is_configured(self, owner_id: str) -> bool: ...


def _read_private_token_file(path_text: str) -> str:
    path = Path(path_text)
    if not path.is_absolute():
        raise OwnerCallError("owner bearer token file must be absolute")
    metadata = path.lstat()
    if path.is_symlink() or not stat.S_ISREG(metadata.st_mode):
        raise OwnerCallError("owner bearer token path must be a regular file")
    if stat.S_IMODE(metadata.st_mode) & 0o077:
        raise OwnerCallError("owner bearer token file must not be group/world accessible")
    if metadata.st_size > 16_384:
        raise OwnerCallError("owner bearer token file exceeds size bound")
    token = path.read_text(encoding="utf-8").strip()
    if not token or any(character.isspace() for character in token):
        raise OwnerCallError("owner bearer token file must contain one non-whitespace token")
    return token


class McpOwnerCaller:
    def __init__(self, owners: Mapping[str, str | OwnerEndpoint]) -> None:
        normalized: dict[str, OwnerEndpoint] = {}
        for owner_id, value in owners.items():
            endpoint = OwnerEndpoint(value) if isinstance(value, str) else value
            url = endpoint.url.strip()
            if not url:
                continue
            normalized[owner_id] = OwnerEndpoint(
                url=url,
                bearer_token_file=endpoint.bearer_token_file,
                validate_tool_results=endpoint.validate_tool_results,
            )
        self._owners = normalized

    @classmethod
    def from_env(cls) -> McpOwnerCaller:
        owners: dict[str, OwnerEndpoint] = {}
        mapping = {
            "runtime.linux": (
                "ORDIVON_GATEWAY_LINUX_RUNTIME_URL",
                "ORDIVON_GATEWAY_LINUX_RUNTIME_BEARER_TOKEN_FILE",
                False,
            ),
            "runtime.windows": (
                "ORDIVON_GATEWAY_WINDOWS_RUNTIME_URL",
                "ORDIVON_GATEWAY_WINDOWS_RUNTIME_BEARER_TOKEN_FILE",
                False,
            ),
            "host": (
                "ORDIVON_GATEWAY_HOST_URL",
                "ORDIVON_GATEWAY_HOST_BEARER_TOKEN_FILE",
                True,
            ),
        }
        for owner_id, (url_key, token_file_key, validate_results) in mapping.items():
            url = os.environ.get(url_key, "").strip()
            if not url:
                continue
            token_file = os.environ.get(token_file_key)
            owners[owner_id] = OwnerEndpoint(
                url=url,
                bearer_token_file=token_file.strip() if token_file else None,
                validate_tool_results=validate_results,
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

        headers: dict[str, str] | None = None
        if endpoint.bearer_token_file is not None:
            token = _read_private_token_file(endpoint.bearer_token_file)
            headers = {"Authorization": f"Bearer {token}"}

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
