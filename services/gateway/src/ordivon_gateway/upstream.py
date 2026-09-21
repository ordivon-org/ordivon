from __future__ import annotations

import json
import os
import stat
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

from mcp import Client
from mcp.client.streamable_http import create_mcp_http_client, streamable_http_client


class OwnerCallError(RuntimeError):
    pass


@dataclass(frozen=True)
class OwnerEndpoint:
    url: str
    bearer_token_file: str | None = None
    access_client_id_file: str | None = None
    access_client_secret_file: str | None = None


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
    mode = stat.S_IMODE(metadata.st_mode)
    credential_directory = os.environ.get("CREDENTIALS_DIRECTORY", "").strip()
    is_systemd_credential = bool(
        credential_directory
        and Path(credential_directory).is_absolute()
        and path.parent == Path(credential_directory)
        and not Path(credential_directory).is_symlink()
    )
    if is_systemd_credential:
        if mode & 0o037:
            raise OwnerCallError(
                f"{label} systemd credential must not be world accessible or group writable/executable"
            )
    elif mode & 0o077:
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

    def is_configured(self, owner_id: str) -> bool:
        return owner_id in self._owners

    async def call_tool(
        self, owner_id: str, tool_name: str, arguments: dict[str, Any]
    ) -> dict[str, Any]:
        endpoint = self._owners.get(owner_id)
        if endpoint is None:
            raise OwnerCallError(f"owner is not configured: {owner_id}")

        headers = _headers_for_endpoint(endpoint)

        async with create_mcp_http_client(headers=headers) as http_client:
            transport = streamable_http_client(endpoint.url, http_client=http_client)
            # MCP v2 Client owns modern discovery, output-schema validation, and
            # legacy fallback. Gateway does not hand-code protocol negotiation.
            async with Client(transport, mode="auto", raise_exceptions=False) as client:
                result = await client.call_tool(tool_name, arguments)

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
