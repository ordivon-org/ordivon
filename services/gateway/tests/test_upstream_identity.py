from __future__ import annotations

import os
from pathlib import Path

import pytest

from ordivon_gateway.upstream import (
    McpOwnerCaller,
    OwnerCallError,
    OwnerEndpoint,
    _headers_for_endpoint,
)


def _secret(path: Path, value: str) -> str:
    path.write_text(value + "\n", encoding="utf-8")
    os.chmod(path, 0o600)
    return str(path)


def test_cloudflare_service_identity_headers_are_loaded_from_private_files(tmp_path: Path) -> None:
    client_id = _secret(tmp_path / "client-id", "0123456789abcdef.access")
    client_secret = _secret(
        tmp_path / "client-secret", "cfast_ABCDEFGHIJKLMNOPQRSTUVWXYZ12345678901234abcd"
    )

    headers = _headers_for_endpoint(
        OwnerEndpoint(
            "https://windows-runtime.example/mcp",
            access_client_id_file=client_id,
            access_client_secret_file=client_secret,
            validate_tool_results=False,
        )
    )

    assert headers == {
        "CF-Access-Client-Id": "0123456789abcdef.access",
        "CF-Access-Client-Secret": "cfast_ABCDEFGHIJKLMNOPQRSTUVWXYZ12345678901234abcd",
    }


def test_owner_endpoint_rejects_ambiguous_or_partial_identity(tmp_path: Path) -> None:
    bearer = _secret(tmp_path / "bearer", "x" * 40)
    client_id = _secret(tmp_path / "client-id", "client.access")
    client_secret = _secret(tmp_path / "client-secret", "y" * 64)

    with pytest.raises(OwnerCallError, match="both"):
        McpOwnerCaller(
            {
                "runtime.windows": OwnerEndpoint(
                    "https://windows-runtime.example/mcp",
                    access_client_id_file=client_id,
                )
            }
        )

    with pytest.raises(OwnerCallError, match="mutually exclusive"):
        McpOwnerCaller(
            {
                "runtime.windows": OwnerEndpoint(
                    "https://windows-runtime.example/mcp",
                    bearer_token_file=bearer,
                    access_client_id_file=client_id,
                    access_client_secret_file=client_secret,
                )
            }
        )


def test_windows_service_identity_env_is_file_reference_only(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    client_id = _secret(tmp_path / "client-id", "client.access")
    client_secret = _secret(tmp_path / "client-secret", "z" * 64)
    monkeypatch.setenv(
        "ORDIVON_GATEWAY_WINDOWS_RUNTIME_URL",
        "https://windows-runtime.example/mcp",
    )
    monkeypatch.setenv("ORDIVON_GATEWAY_WINDOWS_ACCESS_CLIENT_ID_FILE", client_id)
    monkeypatch.setenv("ORDIVON_GATEWAY_WINDOWS_ACCESS_CLIENT_SECRET_FILE", client_secret)

    caller = McpOwnerCaller.from_env()
    endpoint = caller._owners["runtime.windows"]

    assert endpoint.bearer_token_file is None
    assert endpoint.access_client_id_file == client_id
    assert endpoint.access_client_secret_file == client_secret
