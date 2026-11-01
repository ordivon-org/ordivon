"""Opt-in physical Gateway -> PostgreSQL Runtime consumer acceptance.

The provider is a disposable native PostgreSQL cluster and real PG Runtime MCP
binary. This test does not touch any installed Gateway, SQL role, HBA, or secrets.
Invoke with ORDIVON_GATEWAY_PG_E2E_BINARY=/path/to/verified/ordivon-runtime-pg.
"""

from __future__ import annotations

import asyncio
import os
import secrets
import shutil
import socket
import stat
import subprocess
import tempfile
import time
from pathlib import Path

import pytest
from mcp import Client

from ordivon_gateway.mcp_server import build_server
from ordivon_gateway.service import GatewayService
from ordivon_gateway.upstream import McpOwnerCaller, OwnerEndpoint


@pytest.mark.skipif(
    not os.getenv("ORDIVON_GATEWAY_PG_E2E_BINARY"),
    reason="requires explicit disposable native PostgreSQL/PG Runtime integration opt-in",
)
def test_actual_gateway_to_native_pg_mcp_job_and_artifact() -> None:
    binary = Path(os.environ["ORDIVON_GATEWAY_PG_E2E_BINARY"]).resolve(strict=True)
    assert binary.is_file()
    source_root = Path(__file__).resolve().parents[2]
    schema = source_root / "runtime/crates/ordivon-runtime-core/sql/pg_fresh_epoch.sql"
    assert schema.is_file()
    runner = Path(
        os.getenv(
            "ORDIVON_GATEWAY_PG_E2E_RUNNER", "/usr/local/libexec/ordivon/ordivon-runtime-runner"
        )
    ).resolve(strict=True)
    assert runner.is_file()

    root = Path(tempfile.mkdtemp(prefix="ordivon-gateway-pg-e2e-", dir="/var/tmp"))
    root.chmod(0o777)
    pg_started = False
    server = None

    def run(
        cmd: list[str], *, unprivileged: bool = False, env: dict[str, str] | None = None
    ) -> subprocess.CompletedProcess[str]:
        def to_nobody() -> None:
            os.setgroups([])
            os.setgid(65534)
            os.setuid(65534)

        process = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=35,
            env=env,
            preexec_fn=to_nobody if unprivileged and os.geteuid() == 0 else None,
        )
        assert process.returncode == 0, (
            f"physical fixture command {cmd[0]} failed {process.returncode}: "
            f"{process.stderr[-750:]}"
        )
        return process

    def psql(statement: str | None = None, *, sqlfile: Path | None = None) -> str:
        args = [
            "psql",
            "-X",
            "-w",
            "-v",
            "ON_ERROR_STOP=1",
            "-h",
            str(root),
            "-p",
            "5432",
            "-U",
            "postgres",
            "-d",
            "postgres",
        ]
        if statement is not None:
            args += ["-c", statement]
        if sqlfile is not None:
            args += ["-f", str(sqlfile)]
        env = os.environ.copy()
        env["PGOPTIONS"] = "-c search_path=fresh"
        return run(args, env=env).stdout

    try:
        run(
            [
                "initdb",
                "-A",
                "trust",
                "-U",
                "postgres",
                "--no-locale",
                "--encoding=UTF8",
                "-D",
                str(root / "data"),
            ],
            unprivileged=True,
        )
        run(
            [
                "pg_ctl",
                "-D",
                str(root / "data"),
                "-o",
                f"-k {root} -h '' -p 5432 -c fsync=off",
                "-l",
                str(root / "postgres.log"),
                "-w",
                "start",
            ],
            unprivileged=True,
        )
        pg_started = True

        psql("CREATE SCHEMA fresh")
        psql(sqlfile=schema)
        psql(
            "INSERT INTO fresh._stage_control "
            "VALUES('source','QUALIFIED_WRITER','" + "a" * 64 + "',true)"
        )
        psql(
            "CREATE ROLE runtime_app LOGIN; "
            "GRANT USAGE ON SCHEMA fresh TO runtime_app; "
            "GRANT ALL ON ALL TABLES IN SCHEMA fresh TO runtime_app; "
            "REVOKE ALL ON fresh._stage_control FROM runtime_app; "
            "GRANT SELECT, UPDATE(id) ON fresh._stage_control TO runtime_app"
        )
        # Role identity is distinct from the operator (and has no column
        # UPDATE on the source-seal or promotion flags).
        assert (
            "f"
            in psql(
                "SELECT has_column_privilege("
                "'runtime_app','fresh._stage_control',"
                "'promotion_allowed','UPDATE')"
            ).lower()
        )

        repository = root / "source"
        run(["git", "init", "-q", str(repository)])
        run(
            [
                "git",
                "-C",
                str(repository),
                "-c",
                "user.name=Test",
                "-c",
                "user.email=test@example.invalid",
                "commit",
                "-q",
                "--allow-empty",
                "-m",
                "fresh",
            ]
        )

        with socket.socket() as s:
            s.bind(("127.0.0.1", 0))
            port = s.getsockname()[1]
        token = secrets.token_urlsafe(40)
        tokenfile = root / "runtime-bearer"
        tokenfile.write_text(token)
        tokenfile.chmod(0o600)
        assert stat.S_IMODE(tokenfile.stat().st_mode) == 0o600

        env = os.environ.copy()
        env.update(
            {
                "ORDIVON_PG_BIND": f"127.0.0.1:{port}",
                "ORDIVON_PG_TOKEN": token,
                "ORDIVON_PG_DSN": f"host={root} user=runtime_app dbname=postgres",
                "ORDIVON_PG_SCHEMA": "fresh",
                "ORDIVON_PG_SOURCE_SHA256": "a" * 64,
                "ORDIVON_PG_STORE_ROOT": str(root / "store"),
                "ORDIVON_PG_RUNNER": str(runner),
                "ORDIVON_PG_EXECUTABLE_ROOTS_JSON": '["/usr/bin","/bin"]',
                "ORDIVON_PG_PRINCIPAL": "pg-consumer",
            }
        )
        with (root / "runtime.log").open("wb") as log:
            server = subprocess.Popen([str(binary)], env=env, stdout=log, stderr=log)
        for _ in range(120):
            if server.poll() is not None:
                pytest.fail("fresh PG MCP process exited before accepting a connection")
            with socket.socket() as s:
                s.settimeout(0.2)
                if s.connect_ex(("127.0.0.1", port)) == 0:
                    break
            time.sleep(0.05)
        else:
            pytest.fail("fresh PG MCP endpoint did not start")

        async def scenario() -> None:
            caller = McpOwnerCaller(
                {
                    "runtime.linux": OwnerEndpoint(
                        url=f"http://127.0.0.1:{port}/mcp",
                        bearer_token_file=str(tokenfile),
                    )
                }
            )
            gateway = GatewayService(caller)
            # The native Gateway capability discovery must consume PG runtime.describe,
            # not infer provider readiness merely because its route exists.
            discovered = await gateway.capability_describe("execution.linux")
            assert len(discovered.capabilities) == 1
            assert discovered.capabilities[0].capability == "execution.linux"
            assert discovered.capabilities[0].available is True
            workspace = await caller.call_tool(
                "runtime.linux",
                "workspace.open",
                {
                    "workspaceId": "ws-gateway-native",
                    "sourceRepo": str(repository),
                    "sourceRevision": "HEAD",
                },
            )
            assert workspace["workspaceId"] == "ws-gateway-native"
            request_id = "gateway-native-" + secrets.token_hex(6)
            output = "GATEWAY_NATIVE_PG_" + request_id
            receipt = await gateway.execution_submit(
                capability="execution.linux",
                request_id=request_id,
                workspace_id="ws-gateway-native",
                executable="/usr/bin/printf",
                args=[output],
            )
            assert receipt.native_id.startswith("job-")
            assert receipt.owner_id == "runtime.linux"
            again = await gateway.execution_submit(
                capability="execution.linux",
                request_id=request_id,
                workspace_id="ws-gateway-native",
                executable="/usr/bin/printf",
                args=[output],
            )
            assert again.native_id == receipt.native_id
            resolution = await gateway.execution_resolve(
                capability="execution.linux",
                request_id=request_id,
            )
            assert resolution.resolution == "found"
            assert resolution.native_id == receipt.native_id
            assert resolution.workspace_id == "ws-gateway-native"

            for _ in range(20):
                observed = await gateway.execution_get(receipt.operation_ref, wait_ms=1500)
                if observed.terminal:
                    break
            assert observed.terminal
            assert observed.native_id == receipt.native_id
            assert observed.exit_code == 0
            assert observed.execution_disposition == "succeeded"
            assert observed.artifacts_available is True
            assert observed.artifact_projection_complete is True
            assert observed.artifact_ids
            chunks = [
                await gateway.artifact_read(
                    receipt.operation_ref,
                    artifact_id,
                    max_bytes=1024,
                )
                for artifact_id in observed.artifact_ids
            ]
            assert any(output in chunk.content for chunk in chunks)
            assert all(chunk.native_id == receipt.native_id for chunk in chunks)

            # Real northbound Agent MCP -> Gateway MCP -> PG owner MCP.
            # This must exercise both deployed SDKs rather than just calling
            # the GatewayService method directly.
            async with Client(build_server(gateway), raise_exceptions=True) as agent:
                tool_names = {tool.name for tool in (await agent.list_tools()).tools}
                assert {
                    "execution.submit",
                    "execution.resolve",
                    "execution.get",
                    "execution.cancel",
                    "artifact.read",
                } <= tool_names
                agent_request = request_id + "-agent"
                agent_output = "AGENT_VIA_GATEWAY_PG_" + agent_request
                submitted = await agent.call_tool(
                    "execution.submit",
                    {
                        "capability": "execution.linux",
                        "requestId": agent_request,
                        "workspaceId": "ws-gateway-native",
                        "executable": "/usr/bin/printf",
                        "args": [agent_output],
                    },
                )
                assert not submitted.is_error, submitted.structured_content
                north = submitted.structured_content
                assert isinstance(north, dict), submitted
                north_ref = north["operation_ref"]
                found = await agent.call_tool(
                    "execution.resolve",
                    {"capability": "execution.linux", "requestId": agent_request},
                )
                assert not found.is_error
                assert found.structured_content["operation_ref"] == north_ref
                for _ in range(20):
                    got = await agent.call_tool(
                        "execution.get",
                        {"operationRef": north_ref, "waitMs": 1500},
                    )
                    assert not got.is_error
                    if got.structured_content["terminal"]:
                        break
                assert got.structured_content["terminal"]
                assert got.structured_content["exit_code"] == 0
                assert got.structured_content["artifact_projection_complete"]
                found_bytes = False
                for artifact_id in got.structured_content["artifact_ids"]:
                    chunk = await agent.call_tool(
                        "artifact.read",
                        {"operationRef": north_ref, "artifactId": artifact_id, "maxBytes": 1024},
                    )
                    assert not chunk.is_error
                    found_bytes |= agent_output in chunk.structured_content["content"]
                assert found_bytes, "northbound MCP must retain actual Runner stdout"

            # Exercise the actual Gateway cancellation route as a distinct Job.
            cancel_receipt = await gateway.execution_submit(
                capability="execution.linux",
                request_id=request_id + "-cancel",
                workspace_id="ws-gateway-native",
                executable="/usr/bin/sleep",
                args=["30"],
                timeout_ms=40_000,
            )
            cancellation = await gateway.execution_cancel(cancel_receipt.operation_ref)
            assert cancellation.native_id == cancel_receipt.native_id
            assert not cancellation.terminal or cancellation.state in (
                "cancelled",
                "canceled",
                "terminated",
                "failed",
            )
            cancelled = await gateway.execution_get(cancel_receipt.operation_ref, wait_ms=1500)
            assert cancelled.native_id == cancel_receipt.native_id
            owner_intent = await caller.call_tool(
                "runtime.linux",
                "job.observe",
                {
                    "schemaVersion": 1,
                    "jobId": cancel_receipt.native_id,
                    "waitMs": 0,
                    "waitUntil": "change_or_terminal",
                    "stdoutTailBytes": 0,
                    "stderrTailBytes": 0,
                },
            )
            assert owner_intent["terminationIntent"] == "stop_requested"
            if not cancelled.terminal:
                assert owner_intent["attemptState"] == "stopping"
                assert owner_intent["resultAvailable"] is False

        asyncio.run(scenario())
    finally:
        if server is not None:
            server.terminate()
            try:
                server.wait(timeout=6)
            except subprocess.TimeoutExpired:
                server.kill()
                server.wait(timeout=6)
        if pg_started:
            run(
                ["pg_ctl", "-D", str(root / "data"), "-m", "immediate", "-w", "stop"],
                unprivileged=True,
            )
        shutil.rmtree(root)
