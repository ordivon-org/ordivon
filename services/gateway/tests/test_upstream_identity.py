from __future__ import annotations

import asyncio
import os
from pathlib import Path
from types import SimpleNamespace

import pytest

from ordivon_gateway.upstream import (
    McpOwnerCaller,
    OwnerCallError,
    OwnerEndpoint,
    _headers_for_endpoint,
    _read_private_secret_file,
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


def test_conforming_owner_uses_first_class_mcp_client(monkeypatch: pytest.MonkeyPatch) -> None:
    import ordivon_gateway.upstream as upstream

    observed: dict[str, object] = {}

    class FakeHttpContext:
        async def __aenter__(self):
            return object()

        async def __aexit__(self, exc_type, exc, tb):
            return False

    class FakeClient:
        def __init__(self, transport, **kwargs):
            observed["transport"] = transport
            observed["client_kwargs"] = kwargs

        async def __aenter__(self):
            observed["entered"] = True
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        async def call_tool(self, name, arguments, *, meta=None):
            observed["call"] = (name, arguments, meta)
            return SimpleNamespace(
                is_error=False,
                structured_content={"task": {"task_id": "task:1"}},
                content=[],
            )

    fake_transport = object()
    monkeypatch.setattr(upstream, "create_mcp_http_client", lambda headers=None: FakeHttpContext())
    monkeypatch.setattr(
        upstream,
        "streamable_http_client",
        lambda url, http_client=None: (
            observed.update({"url": url, "http_client": http_client}) or fake_transport
        ),
    )
    monkeypatch.setattr(upstream, "Client", FakeClient)
    monkeypatch.setattr(
        upstream,
        "inject_trace_context",
        lambda meta: meta.update(
            {
                "traceparent": "00-11111111111111111111111111111111-2222222222222222-01",
                "tracestate": "vendor=value",
            }
        ),
    )

    caller = McpOwnerCaller(
        {
            "host": OwnerEndpoint(
                "https://host.example/mcp",
            )
        }
    )
    result = asyncio.run(caller.call_tool("host", "task.list", {"limit": 1}))

    assert result == {"task": {"task_id": "task:1"}}
    assert observed["url"] == "https://host.example/mcp"
    assert observed["transport"] is fake_transport
    assert observed["client_kwargs"] == {"mode": "auto", "raise_exceptions": False}
    assert observed["call"] == (
        "task.list",
        {"limit": 1},
        {
            "traceparent": "00-11111111111111111111111111111111-2222222222222222-01",
            "tracestate": "vendor=value",
        },
    )


def test_systemd_credential_projection_accepts_provider_native_group_read(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    credential_directory = tmp_path / "credentials"
    credential_directory.mkdir(mode=0o750)
    credential = credential_directory / "runtime-token"
    credential.write_text("systemd-token\n", encoding="utf-8")
    os.chmod(credential, 0o440)
    monkeypatch.setenv("CREDENTIALS_DIRECTORY", str(credential_directory))

    assert _read_private_secret_file(str(credential), "owner bearer token") == "systemd-token"


def test_group_read_outside_systemd_credential_directory_is_rejected(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    credential = tmp_path / "runtime-token"
    credential.write_text("ordinary-token\n", encoding="utf-8")
    os.chmod(credential, 0o440)
    monkeypatch.delenv("CREDENTIALS_DIRECTORY", raising=False)

    with pytest.raises(OwnerCallError, match="group/world accessible"):
        _read_private_secret_file(str(credential), "owner bearer token")
