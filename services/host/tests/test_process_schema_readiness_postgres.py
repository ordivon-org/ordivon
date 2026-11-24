"""Actual serving entrypoint must not expose a Host with mismatched PG schema."""
from __future__ import annotations

import asyncio
import os
import socket
import subprocess
import sys
import time
from pathlib import Path

import httpx2
import psycopg
import pytest
from mcp import Client, StdioServerParameters

from ordivon_host_v2.service import REQUIRED_SCHEMA_VERSION

DSN = os.environ.get("ORDIVON_HOST_V2_TEST_DSN")
OLD_DSN = os.environ.get("ORDIVON_HOST_V2_MIGRATION_STARTUP_DSN")
COMMAND = [sys.executable, "-c", "from ordivon_host_v2.mcp_server import main; main()"]


def environment(dsn: str, transport: str, tmp_path: Path) -> dict[str, str]:
    env = {k: v for k, v in os.environ.items() if not k.startswith("ORDIVON_HOST_V2_")}
    env.update(
        ORDIVON_HOST_V2_DSN=dsn,
        ORDIVON_HOST_V2_TRANSPORT=transport,
        ORDIVON_HOST_V2_PG_POOL_MAX_SIZE="2",
    )
    if transport == "streamable-http":
        credential = tmp_path / "host-test-token"
        credential.write_text("r" * 48, encoding="utf-8")
        credential.chmod(0o600)
        # Never bind an existing service port or use a production credential.
        with socket.socket() as sock:
            sock.bind(("127.0.0.1", 0))
            port = sock.getsockname()[1]
        env.update(
            ORDIVON_HOST_V2_HOST="127.0.0.1",
            ORDIVON_HOST_V2_PORT=str(port),
            ORDIVON_HOST_V2_OWNER_BEARER_TOKEN_FILE=str(credential),
        )
    return env


@pytest.mark.parametrize("transport", ["stdio", "streamable-http"])
def test_native_process_rejects_previous_schema_before_serving(transport, tmp_path) -> None:
    if not OLD_DSN:
        pytest.skip("requires explicitly dedicated previous-schema startup database")
    assert OLD_DSN != DSN
    with psycopg.connect(OLD_DSN) as conn:
        observed = conn.execute("SELECT schema_version FROM host_v2_schema").fetchone()
        assert observed == (REQUIRED_SCHEMA_VERSION - 1,)
    env = environment(OLD_DSN, transport, tmp_path)
    # A real wrong-schema server must exit without exposing either transport.
    # In the old implementation stdio exits normally at EOF, while HTTP stays up.
    try:
        result = subprocess.run(
            COMMAND, stdin=subprocess.DEVNULL, capture_output=True,
            text=True, env=env, timeout=8, check=False,
        )
    except subprocess.TimeoutExpired as exc:
        pytest.fail(f"wrong-schema Host {transport} remained alive: {exc.stderr!r}")
    assert result.returncode != 0
    assert f"required version {REQUIRED_SCHEMA_VERSION} (observed={REQUIRED_SCHEMA_VERSION - 1})" in result.stderr
    assert not result.stdout
    assert "Uvicorn running" not in result.stderr


def test_native_stdio_process_serves_current_schema(tmp_path) -> None:
    if not DSN:
        pytest.skip("requires native Host PostgreSQL test database")
    env = environment(DSN, "stdio", tmp_path)

    async def scenario() -> None:
        async with Client(
            StdioServerParameters(command=COMMAND[0], args=COMMAND[1:], env=env),
            raise_exceptions=True, read_timeout_seconds=8,
        ) as client:
            tools = await client.list_tools()
            assert len(tools.tools) == 31
            result = await client.call_tool("host.status", {"detail": "summary"})
            assert result.structured_content["authority"]["journalSchema"] == REQUIRED_SCHEMA_VERSION

    asyncio.run(scenario())


def test_native_protected_http_process_serves_current_schema(tmp_path) -> None:
    if not DSN:
        pytest.skip("requires native Host PostgreSQL test database")
    env = environment(DSN, "streamable-http", tmp_path)
    url = f"http://127.0.0.1:{env['ORDIVON_HOST_V2_PORT']}/mcp"
    with subprocess.Popen(
        COMMAND, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE, env=env, text=True,
    ) as process:
        try:
            with httpx2.Client(timeout=2, trust_env=False) as client:
                deadline = time.monotonic() + 10
                while True:
                    assert process.poll() is None, process.stderr.read()
                    try:
                        anonymous = client.post(url, json={"method": "tools/list"})
                        break
                    except httpx2.ConnectError:
                        if time.monotonic() >= deadline:
                            pytest.fail("native HTTP process did not start")
                        time.sleep(0.05)
                assert anonymous.status_code == 401
                headers = {
                    "Authorization": "Bearer " + "r" * 48,
                    "Accept": "application/json, text/event-stream",
                }
                initialized = client.post(
                    url, headers=headers, json={
                        "jsonrpc": "2.0", "id": 1, "method": "initialize",
                        "params": {
                            "protocolVersion": "2025-11-25", "capabilities": {},
                            "clientInfo": {"name": "native-readiness-test", "version": "1"},
                        },
                    },
                )
                assert initialized.status_code == 200, initialized.text
                headers["MCP-Protocol-Version"] = initialized.json()["result"]["protocolVersion"]
                if session_id := initialized.headers.get("Mcp-Session-Id"):
                    headers["Mcp-Session-Id"] = session_id
                client.post(url, headers=headers, json={
                    "jsonrpc": "2.0", "method": "notifications/initialized",
                })
                response = client.post(url, headers=headers, json={
                    "jsonrpc": "2.0", "id": 2, "method": "tools/call",
                    "params": {"name": "host.status", "arguments": {"detail": "summary"}},
                })
                assert response.status_code == 200, response.text
                assert response.json()["result"]["structuredContent"]["authority"]["journalSchema"] == REQUIRED_SCHEMA_VERSION
        finally:
            process.terminate()
            try:
                process.communicate(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.communicate()
