from __future__ import annotations

import asyncio
import json
import os
from pathlib import Path
from types import SimpleNamespace

import pytest

from ordivon_gateway.upstream import (
    McpOwnerCaller,
    OwnerCallError,
    OwnerEndpoint,
    _exception_summary,
    _extract_owner_tool_error,
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


def test_conforming_owner_uses_first_class_mcp_client(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    import ordivon_gateway.upstream as upstream

    observed: dict[str, object] = {}

    class FakeHttpContext:
        async def aclose(self) -> None:
            pass

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
    monkeypatch.setattr(upstream, "create_mcp_http_client", lambda **kwargs: FakeHttpContext())
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
                bearer_token_file=_secret(tmp_path / "host-bearer", "x" * 48),
            )
        }
    )
    result = asyncio.run(caller.call_tool("host", "host.status", {"detail": "summary"}))

    assert result == {"task": {"task_id": "task:1"}}
    assert observed["url"] == "https://host.example/mcp"
    assert observed["transport"] is fake_transport
    assert observed["client_kwargs"] == {"mode": "auto", "raise_exceptions": False}
    assert observed["call"] == (
        "host.status",
        {"detail": "summary"},
        {
            "traceparent": "00-11111111111111111111111111111111-2222222222222222-01",
            "tracestate": "vendor=value",
        },
    )


@pytest.mark.parametrize("error_carrier", ["structured", "host_text"])
def test_host_failure_survives_real_gateway_owner_call_boundary(
    monkeypatch: pytest.MonkeyPatch, error_carrier: str, tmp_path: Path
) -> None:
    """The MCP client's owner error must not turn into a Gateway success."""

    import ordivon_gateway.upstream as upstream

    host_error = {
        "code": "NOT_FOUND",
        "kind": "ordivon.host-domain-error",
        "resourceKind": "work",
        "resourceRef": "work:absent",
        "retryable": False,
        "schemaVersion": 1,
    }
    observed: list[tuple[str, dict[str, object]]] = []

    class FakeHttpContext:
        async def aclose(self) -> None:
            pass

    class FakeClient:
        def __init__(self, transport, **kwargs):
            assert kwargs == {"mode": "auto", "raise_exceptions": False}

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        async def call_tool(self, name, arguments, *, meta=None):
            observed.append((name, arguments))
            return SimpleNamespace(
                is_error=True,
                structured_content={"error": host_error} if error_carrier == "structured" else None,
                content=(
                    []
                    if error_carrier == "structured"
                    else [
                        SimpleNamespace(
                            text="Error executing tool work.get: "
                            + json.dumps(host_error, separators=(",", ":"))
                        )
                    ]
                ),
            )

    monkeypatch.setattr(upstream, "create_mcp_http_client", lambda **kwargs: FakeHttpContext())
    monkeypatch.setattr(upstream, "streamable_http_client", lambda url, http_client=None: object())
    monkeypatch.setattr(upstream, "Client", FakeClient)
    caller = McpOwnerCaller(
        {
            "host": OwnerEndpoint(
                "http://127.0.0.1:8898/mcp",
                bearer_token_file=_secret(tmp_path / "host-bearer", "z" * 48),
            )
        }
    )

    with pytest.raises(OwnerCallError) as raised:
        asyncio.run(caller.call_tool("host", "work.get", {"workRef": "work:absent"}))

    assert observed == [("work.get", {"workRef": "work:absent"})]
    assert raised.value.owner_id == "host"
    assert raised.value.tool_name == "work.get"
    assert raised.value.error == host_error


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


def test_runtime_endpoint_requires_explicit_owner_identity_before_configured() -> None:
    caller = McpOwnerCaller({"runtime.windows": OwnerEndpoint("http://127.0.0.1:18997/mcp")})

    assert caller.is_configured("runtime.windows") is False
    assert caller.configuration_error("runtime.windows") == "owner authentication is not configured"
    with pytest.raises(OwnerCallError) as captured:
        asyncio.run(caller.call_tool("runtime.windows", "runtime.describe", {"schemaVersion": 1}))
    assert captured.value.error == {
        "code": "OWNER_AUTH_NOT_CONFIGURED",
        "message": "owner authentication is not configured",
        "origin": "gateway_adapter",
    }


def test_host_endpoint_requires_explicit_service_identity(tmp_path: Path) -> None:
    caller = McpOwnerCaller({"host": OwnerEndpoint("http://127.0.0.1:8898/mcp")})
    assert caller.is_configured("host") is False
    assert caller.configuration_error("host") == "owner authentication is not configured"
    with pytest.raises(OwnerCallError) as captured:
        asyncio.run(caller.call_tool("host", "work.get", {"workRef": "work:test"}))
    assert captured.value.error["code"] == "OWNER_AUTH_NOT_CONFIGURED"

    qualified = McpOwnerCaller(
        {
            "host": OwnerEndpoint(
                "http://127.0.0.1:8898/mcp",
                bearer_token_file=_secret(tmp_path / "host-bearer", "a" * 48),
            )
        }
    )
    assert qualified.is_configured("host") is True


def test_exception_summary_exposes_nested_task_group_leaf() -> None:
    error = ExceptionGroup(
        "unhandled errors in a TaskGroup",
        [RuntimeError("HTTP 401 owner authentication required")],
    )
    assert _exception_summary(error) == "RuntimeError: HTTP 401 owner authentication required"


def test_host_domain_error_text_is_preserved_as_typed_owner_error() -> None:
    domain_error = {
        "code": "NOT_FOUND",
        "kind": "ordivon.host-domain-error",
        "resourceKind": "work",
        "resourceRef": "work:missing",
        "retryable": False,
        "schemaVersion": 1,
        "suggestedAction": "discover-before-create",
    }
    result = SimpleNamespace(
        structured_content=None,
        content=[
            SimpleNamespace(
                text="Error executing tool work.get: "
                + __import__("json").dumps(domain_error, separators=(",", ":"))
            )
        ],
    )

    assert _extract_owner_tool_error(result, owner_id="host", tool_name="work.get") == domain_error


def test_arbitrary_owner_error_text_is_not_promoted_to_structured_authority() -> None:
    result = SimpleNamespace(
        structured_content=None,
        content=[SimpleNamespace(text='Error executing tool work.get: {"code":"NOT_FOUND"}')],
    )

    assert _extract_owner_tool_error(result, owner_id="host", tool_name="work.get") is None
    assert _extract_owner_tool_error(result, owner_id="runtime.linux", tool_name="work.get") is None


def test_structured_owner_error_precedes_text_fallback() -> None:
    structured = {
        "code": "REGISTRY_COMMIT_UNKNOWN",
        "origin": "runtime_core",
        "retryable": True,
    }
    result = SimpleNamespace(
        structured_content={"error": structured},
        content=[
            SimpleNamespace(
                text='Error executing tool work.get: {"code":"NOT_FOUND","kind":"ordivon.host-domain-error","schemaVersion":1}'
            )
        ],
    )

    assert _extract_owner_tool_error(result, owner_id="host", tool_name="work.get") == structured


@pytest.mark.skipif(os.name != "posix", reason="native POSIX O_NOFOLLOW contract")
def test_posix_owner_credential_preserves_open_inode_during_path_replacement(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """An adversary changing pathname after open cannot redirect opened FD."""
    checked = tmp_path / "trusted"
    alternate = tmp_path / "untrusted"
    _secret(checked, "trusted-service-token")
    _secret(alternate, "attacker-token")
    original_fstat = os.fstat
    changed = False

    def replace_after_open(fd: int) -> os.stat_result:
        nonlocal changed
        if not changed:
            checked.unlink()
            checked.symlink_to(alternate)
            changed = True
        return original_fstat(fd)

    monkeypatch.setattr(os, "fstat", replace_after_open)
    # The original code reread checked by pathname and accepted alternate.
    # A same-FD reader always returns the bytes actually opened.
    assert _read_private_secret_file(str(checked), "owner bearer token") == "trusted-service-token"
    assert changed


@pytest.mark.skipif(os.name != "posix", reason="native POSIX O_NOFOLLOW contract")
def test_posix_owner_credential_rejects_symlink_substitution_before_open(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    checked = tmp_path / "trusted"
    alternate = tmp_path / "untrusted"
    _secret(checked, "trusted-service-token")
    _secret(alternate, "attacker-token")
    original_open = os.open
    changed = False

    def replace_before_open(path, flags, *args, **kwargs):
        nonlocal changed
        if os.fspath(path) == str(checked) and not changed:
            checked.unlink()
            checked.symlink_to(alternate)
            changed = True
        return original_open(path, flags, *args, **kwargs)

    monkeypatch.setattr(os, "open", replace_before_open)
    with pytest.raises(OwnerCallError, match="could not be opened securely"):
        _read_private_secret_file(str(checked), "owner bearer token")
    assert changed


@pytest.mark.skipif(os.name != "posix", reason="native POSIX same-descriptor stability contract")
def test_posix_owner_credential_fails_closed_on_mutation_during_read(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    checked = tmp_path / "mutable-secret"
    _secret(checked, "verified-original-secret")
    original_read = os.read
    changed = False

    def mutate_between_read_and_final_fstat(fd: int, length: int) -> bytes:
        nonlocal changed
        data = original_read(fd, length)
        if not changed:
            # This remains the SAME inode, unlike symlink/path replacement.
            checked.write_text("changed-secret-during-read", encoding="utf-8")
            changed = True
        return data

    monkeypatch.setattr(os, "read", mutate_between_read_and_final_fstat)
    with pytest.raises(OwnerCallError, match="changed during read"):
        _read_private_secret_file(str(checked), "owner bearer token")
    assert changed


@pytest.mark.skipif(os.name != "posix", reason="native POSIX O_NOFOLLOW contract")
def test_posix_owner_credential_rejects_fifo_without_blocking(tmp_path: Path) -> None:
    fifo = tmp_path / "unexpected-fifo"
    os.mkfifo(fifo, mode=0o600)
    with pytest.raises(OwnerCallError, match="regular file"):
        _read_private_secret_file(str(fifo), "owner bearer token")


@pytest.mark.skipif(os.name != "posix", reason="native POSIX credential-mode contract")
def test_owner_credential_rejects_world_readable_replacement(tmp_path: Path) -> None:
    vulnerable = tmp_path / "world-readable"
    vulnerable.write_text("unexpected-secret\n")
    vulnerable.chmod(0o644)
    with pytest.raises(OwnerCallError, match="group/world accessible"):
        _read_private_secret_file(str(vulnerable), "owner bearer token")


def test_owner_credential_rejects_oversized_secret(tmp_path: Path) -> None:
    oversized = tmp_path / "oversized"
    _secret(oversized, "x" * 16_385)
    with pytest.raises(OwnerCallError, match="size bound"):
        _read_private_secret_file(str(oversized), "owner bearer token")
