"""Opt-in physical Gateway -> PostgreSQL Runtime consumer acceptance.

The provider is a disposable native PostgreSQL cluster and real PG Runtime MCP
binary. This test does not touch any installed Gateway, SQL role, HBA, or secrets.
Invoke with ORDIVON_GATEWAY_PG_E2E_BINARY=/path/to/verified/ordivon-runtime-pg.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
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
from ordivon_gateway.upstream import McpOwnerCaller, OwnerCallError, OwnerEndpoint


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
            "-A",
            "-t",
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
        # Mirror the existing Rust pg_vertical native PG fixture: a source
        # seal alone cannot authorize effects after a PITR/timeline fork.
        # This is an isolated operator-owned test cluster, never a live PG.
        physical = psql(
            "SELECT (SELECT system_identifier::text FROM pg_control_system())"
            " || '|' || (SELECT timeline_id FROM pg_control_checkpoint())"
        ).strip()
        system_id, timeline = physical.split("|", 1)
        writer_epoch = hashlib.sha256(
            (
                "ordivon-pg-writer-epoch-v1\0"
                + "a" * 64
                + "\0"
                + system_id
                + "\0"
                + str(int(timeline))
            ).encode("utf-8")
        ).hexdigest()
        psql(
            "INSERT INTO fresh._stage_control "
            f"VALUES('epoch','QUALIFIED_EPOCH','{writer_epoch}',true)"
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
        issuer_isolated = os.getenv("ORDIVON_GATEWAY_PG_E2E_ISSUER_ISOLATED") == "1"
        if issuer_isolated:
            assert os.getenv("ORDIVON_GATEWAY_PG_E2E_ISSUER_ADMISSION") == "1"
            harness_tokenfile = root / "harness-private-bearer"
            harness_tokenfile.write_text(secrets.token_urlsafe(40))
            harness_tokenfile.chmod(0o600)
        else:
            harness_tokenfile = None

        # Private-test-only launcher barrier, not a replacement Runner.
        # Native Runtime attests the true Runner binary as executionProvider:
        # wrapping Runner itself correctly fails provider-digest checks.
        # The existing Rust Runtime invokes systemd-run AFTER a committed
        # DISPATCH_ISSUED. Gate only the CLI invocation via a private PATH
        # override, then exec the REAL systemd-run with unchanged arguments.
        # The native Runner binary, service Unit and PG evidence remain real.
        dispatch_gate = os.getenv("ORDIVON_GATEWAY_PG_E2E_DISPATCH_GATE") == "1"
        if dispatch_gate:
            assert os.getenv("ORDIVON_GATEWAY_PG_E2E_REAL_HARNESS_SOURCE") == "1", (
                "dispatch gate must use the genuine PG Harness issuer source"
            )
        gate_enabled = root / "r24-gate-enabled"
        gate_ready = root / "r24-before-systemd-run"
        gate_release = root / "r24-systemd-run-release"
        gate_tools = root / "r24-launcher-tools"
        if dispatch_gate:
            import shlex

            gate_tools.mkdir(mode=0o755)
            launcher = gate_tools / "systemd-run"
            launcher.write_text(
                "#!/usr/bin/bash\n"
                "set -euo pipefail\n"
                f"if test -f {shlex.quote(str(gate_enabled))}; then\n"
                f"  printf 'native-dispatch-committed-before-systemd-run\n' "
                f"> {shlex.quote(str(gate_ready))}\n"
                "  for i in $(seq 1 600); do\n"
                f"    if test -e {shlex.quote(str(gate_release))}; then break; fi\n"
                "    sleep 0.05\n"
                "  done\n"
                f"  test -e {shlex.quote(str(gate_release))} || exit 125\n"
                "fi\n"
                'exec /usr/bin/systemd-run "$@"\n'
            )
            launcher.chmod(0o755)

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
        if os.getenv("ORDIVON_GATEWAY_PG_E2E_ISSUER_ADMISSION") == "1":
            # Same cluster and issuer, with either legacy strict whole-endpoint
            # policy or the distinct authenticated Harness route.
            env["ORDIVON_PG_HARNESS_ISSUER_SCHEMA"] = "harness_r22_source"
            if issuer_isolated:
                assert harness_tokenfile is not None
                env["ORDIVON_PG_HARNESS_TOKEN_FILE"] = str(harness_tokenfile)
                env["ORDIVON_PG_HARNESS_PRINCIPAL"] = "harness-native-test"
        if dispatch_gate:
            # Only this disposable owner process sees the PATH tool barrier.
            # No installed Runtime, global PATH or native Runner is changed.
            env["PATH"] = str(gate_tools) + os.pathsep + env.get("PATH", "/usr/bin:/bin")
        with (root / "runtime.log").open("wb") as log:
            server = subprocess.Popen([str(binary)], env=env, stdout=log, stderr=log)
        for _ in range(120):
            if server.poll() is not None:
                # An early native process exit is not evidence about Gateway's
                # reference forwarding. Keep the failure attributable while
                # preventing the private loopback bearer from entering logs.
                native_log = (root / "runtime.log").read_text(errors="replace")
                native_log = native_log.replace(token, "[REDACTED_BEARER]")
                pytest.fail(
                    f"fresh PG MCP exited before connection (exit={server.returncode}): "
                    f"{native_log[-1200:]}"
                )
            with socket.socket() as s:
                s.settimeout(0.2)
                if s.connect_ex(("127.0.0.1", port)) == 0:
                    break
            time.sleep(0.05)
        else:
            pytest.fail("fresh PG MCP endpoint did not start")

        # Opt-in cross-owner qualification. It exercises the ACTUAL Harness
        # PG Run/Intent/Fence producer against this SAME disposable PG18
        # cluster and native Gateway->Runtime->Runner; ordinary Gateway
        # tests do not depend on Harness' Python environment or package.
        harness_source = os.getenv("ORDIVON_GATEWAY_PG_E2E_REAL_HARNESS_SOURCE") == "1"
        issuer_bound = os.getenv("ORDIVON_GATEWAY_PG_E2E_ISSUER_ADMISSION") == "1"
        if issuer_bound:
            assert harness_source, "issuer admission opt-in requires real Harness PG source"

        def verified_harness_source(
            stage: str, *, expect_rejection: bool = False, **settings: str
        ) -> dict:
            interpreter = os.environ.get("ORDIVON_GATEWAY_PG_E2E_HARNESS_PYTHON")
            assert interpreter and Path(interpreter).is_file(), (
                "opt-in source test requires an existing qualified Harness Python interpreter"
            )
            script = (
                source_root
                / "harness/rust-migration/consumer-acceptance"
                / {
                    "prepare": "real_pg_fenced_gateway_source.py",
                    "supersede": "real_pg_fenced_gateway_supersede.py",
                    "unknown": "real_pg_fenced_gateway_receipt.py",
                    "reconcile": "real_pg_fenced_gateway_receipt.py",
                }[stage]
            )
            assert script.is_file(), "real Harness source and receipt must exist"
            source_env = {
                **os.environ,
                "PYTHONPATH": str(source_root / "harness/src"),
                "ORDIVON_R22_HARNESS_PG_DSN": (
                    f"host={root} port=5432 dbname=postgres user=postgres"
                ),
                "ORDIVON_R22_RUNTIME_WORKSPACE": "ws-gateway-native",
                "ORDIVON_R22_RECEIPT_STAGE": stage,
                **({"ORDIVON_R25_REAL_EPOCH_ISSUER": "1"} if issuer_bound else {}),
                **settings,
            }
            verified = subprocess.run(
                [interpreter, str(script)],
                env=source_env,
                text=True,
                capture_output=True,
                timeout=35,
                check=False,
            )
            if expect_rejection:
                assert verified.returncode != 0, (
                    "wrong native Owner Job must not settle another Harness Tool Intent"
                )
                assert "OWNER_SOURCE_IDENTITY_MISMATCH" in verified.stderr, (
                    "unrelated source/PG failure cannot masquerade as Owner identity rejection: "
                    f"{verified.stderr[-800:]}"
                )
                return {"rejected": True}
            assert verified.returncode == 0, (
                f"Harness source {stage} failed: {verified.stderr[-1200:]}"
            )
            return json.loads(verified.stdout.strip().splitlines()[-1])

        async def scenario() -> None:
            endpoints = {
                "runtime.linux": OwnerEndpoint(
                    url=f"http://127.0.0.1:{port}/mcp",
                    bearer_token_file=str(tokenfile),
                )
            }
            if issuer_isolated:
                assert harness_tokenfile is not None
                endpoints["runtime.harness"] = OwnerEndpoint(
                    url=f"http://127.0.0.1:{port}/harness/mcp",
                    bearer_token_file=str(harness_tokenfile),
                )
                # The two physical ingress profiles must not share a Bearer:
                # a valid normal credential cannot become a Harness authority.
                import urllib.error
                import urllib.request

                for endpoint, wrong_token in [
                    ("/harness/mcp", token),
                    ("/mcp", harness_tokenfile.read_text()),
                ]:
                    request = urllib.request.Request(
                        f"http://127.0.0.1:{port}{endpoint}",
                        data=b"{}",
                        method="POST",
                        headers={"Authorization": f"Bearer {wrong_token}"},
                    )
                    with pytest.raises(urllib.error.HTTPError) as denied:
                        urllib.request.urlopen(request, timeout=2)
                    assert denied.value.code == 401
            caller = McpOwnerCaller(endpoints)
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
            if issuer_isolated:
                projection = await gateway.capability_describe("execution.harness")
                assert projection.capabilities[0].available is True
                ordinary = await gateway.execution_submit(
                    capability="execution.linux",
                    request_id="r26-ordinary-unfenced",
                    workspace_id="ws-gateway-native",
                    executable="/usr/bin/printf",
                    args=["R26_ORDINARY_RUNTIME_NOT_BLOCKED"],
                )
                assert ordinary.owner_id == "runtime.linux"
                for _ in range(30):
                    ordinary_seen = await gateway.execution_get(
                        ordinary.operation_ref, wait_ms=1500
                    )
                    if ordinary_seen.terminal:
                        break
                assert ordinary_seen.terminal and ordinary_seen.exit_code == 0
                print("R26_SAME_PG_DISTINCT_PRINCIPAL_NORMAL_UNFENCED_REAL_JOB_SUCCEEDED")

            if issuer_bound:
                async with Client(build_server(gateway), raise_exceptions=True) as agent:

                    def native_request(source: dict) -> dict:
                        return {
                            "capability": (
                                "execution.harness" if issuer_isolated else "execution.linux"
                            ),
                            "requestId": source["clientRequestId"],
                            "workspaceId": "ws-gateway-native",
                            "executable": "/usr/bin/printf",
                            "args": [source["execution"]["args"][0]],
                            "authorityReferences": source["foreignReferences"],
                            **{
                                field: source["execution"][field]
                                for field in (
                                    "cwdRelative",
                                    "env",
                                    "timeoutMs",
                                    "stdoutLimitBytes",
                                    "stderrLimitBytes",
                                )
                            },
                        }

                    valid_source = verified_harness_source(
                        "prepare", ORDIVON_R22_EXEC_OUTPUT="R25_VALID_ISSUER_PG_NATIVE"
                    )
                    # This disposable cluster explicitly permits the Runtime
                    # app PG role to lock/read issuer Run rows. A production
                    # deployment should use a narrower issuer-defined
                    # SECURITY DEFINER verification function/grant, not grant
                    # arbitrary table UPDATE privilege to the Runtime role.
                    psql(
                        "GRANT USAGE ON SCHEMA harness_r22_source TO runtime_app; "
                        "GRANT EXECUTE ON FUNCTION "
                        "harness_r22_source.harness_current_dispatch_cut(text,bigint,text) "
                        "TO runtime_app"
                    )
                    assert (
                        psql(
                            "SELECT has_table_privilege("
                            "'runtime_app','harness_r22_source.runs','UPDATE')"
                        ).strip()
                        == "f"
                    )
                    assert (
                        psql(
                            "SELECT has_table_privilege("
                            "'runtime_app','harness_r22_source.objects','SELECT')"
                        ).strip()
                        == "f"
                    )
                    valid = await agent.call_tool("execution.submit", native_request(valid_source))
                    assert not valid.is_error, valid.structured_content
                    actual_job = valid.structured_content["native_id"]
                    for _ in range(30):
                        observed = await agent.call_tool(
                            "execution.get",
                            {
                                "operationRef": valid.structured_content["operation_ref"],
                                "waitMs": 1500,
                            },
                        )
                        if observed.is_error:
                            print(
                                "R25_SOURCE_ADMISSION_NATIVE_OBSERVE_ERROR",
                                json.dumps(observed.structured_content, sort_keys=True),
                                flush=True,
                            )
                        assert not observed.is_error, observed.structured_content
                        if observed.structured_content["terminal"]:
                            break
                    assert observed.structured_content["terminal"]
                    assert observed.structured_content["exit_code"] == 0
                    assert (
                        psql(f"SELECT count(*) FROM fresh.jobs WHERE job_id='{actual_job}'").strip()
                        == "1"
                    )
                    print("R25_SAME_PG_ISSUER_CURRENT_NEW_NATIVE_JOB_ADMITTED")

                    if issuer_isolated:
                        bound_ref = valid.structured_content["operation_ref"]
                        assert bound_ref == f"ordivon-exec:v1:runtime.harness:{actual_job}"
                        resolved_owner = await gateway.execution_resolve(
                            capability="execution.harness",
                            request_id=valid_source["clientRequestId"],
                        )
                        assert resolved_owner.native_id == actual_job
                        assert resolved_owner.operation_ref == bound_ref
                        assert resolved_owner.workspace_id == "ws-gateway-native"
                        fetched = await gateway.execution_get(bound_ref, wait_ms=0)
                        assert fetched.native_id == actual_job
                        assert fetched.capability == "execution.harness"
                        assert fetched.terminal is True
                        assert fetched.execution_disposition == "succeeded"
                        assert fetched.artifact_ids
                        chunks = [
                            await gateway.artifact_read(bound_ref, artifact_id, max_bytes=65536)
                            for artifact_id in fetched.artifact_ids
                        ]
                        assert all(chunk.native_id == actual_job for chunk in chunks)
                        assert any(
                            "R25_VALID_ISSUER_PG_NATIVE" in chunk.content for chunk in chunks
                        )
                        print("R26_AUTHENTICATED_GATEWAY_RECOVERY_AND_ARTIFACT_REAL_OWNER")

                    if issuer_isolated:
                        # A terminal Runner Job is not a DomainResult. Exercise
                        # the existing UNKNOWN→Owner Receipt journal consumer
                        # against the independently authenticated Harness PG Job.
                        original_refs = json.dumps(valid_source["foreignReferences"])
                        lost_response = verified_harness_source(
                            "unknown",
                            ORDIVON_R22_EXPECT_RUN=valid_source["runId"],
                            ORDIVON_R22_EXPECT_REQUEST=valid_source["clientRequestId"],
                            ORDIVON_R22_EXPECT_REFS_JSON=original_refs,
                        )
                        assert lost_response["standing"] == "UNKNOWN"
                        verified_owner_result = await caller.call_tool(
                            "runtime.harness",
                            "job.get",
                            {"jobId": actual_job},
                        )
                        assert verified_owner_result["job"]["jobId"] == actual_job
                        assert verified_owner_result["job"]["clientRequestId"] == (
                            valid_source["clientRequestId"]
                        )
                        assert verified_owner_result["job"]["resolution"] == "succeeded"
                        assert verified_owner_result["job"]["semanticCompletionEvaluated"] is False
                        assert verified_owner_result["attempts"][-1]["exitCode"] == 0
                        # Source SQL is authoritative for physical dispatch.
                        # Inspection.episodes is a bounded diagnostic and may
                        # report 0 even when PG events retain DISPATCH_ISSUED.
                        assert psql(
                            "SELECT count(*) FROM fresh.job_events "
                            f"WHERE job_id='{actual_job}' AND event_type='DISPATCH_ISSUED'"
                        ).strip() == "1"
                        # The native observation is the actual Owner Receipt;
                        # inspection corroborates exact identity and attempts.
                        native_observed = await caller.call_tool(
                            "runtime.harness",
                            "job.observe",
                            {"jobId": actual_job, "waitMs": 0},
                        )
                        assert native_observed["jobId"] == actual_job
                        assert native_observed["executionTerminal"] is True
                        assert native_observed["deliveryDisposition"] == "committed"
                        assert native_observed["exitCode"] == 0
                        reconciled = verified_harness_source(
                            "reconcile",
                            ORDIVON_R22_EXPECT_RUN=valid_source["runId"],
                            ORDIVON_R22_EXPECT_REQUEST=valid_source["clientRequestId"],
                            ORDIVON_R22_EXPECT_REFS_JSON=original_refs,
                            ORDIVON_R22_OWNER_JOB=actual_job,
                            ORDIVON_R22_OWNER_OBSERVATION=json.dumps({
                                "jobId": actual_job,
                                "clientRequestId": verified_owner_result["job"][
                                    "clientRequestId"
                                ],
                                "executionTerminal": native_observed["executionTerminal"],
                                "deliveryDisposition": native_observed["deliveryDisposition"],
                                "exitCode": native_observed["exitCode"],
                            }),
                            ORDIVON_R22_OWNER_PRINCIPAL="harness-native-test",
                        )
                        assert reconciled["standing"] == "OWNER_CONFIRMED_RECEIPT"
                        assert reconciled["jobId"] == actual_job
                        assert reconciled["dispatchCount"] == 1
                        assert reconciled["semanticCompletionEvaluated"] is False
                        assert reconciled["previousReceiptDigest"] == lost_response["receiptDigest"]
                        print("R26_AUTHENTICATED_SOURCE_UNKNOWN_TO_OWNER_RECEIPT_NO_DOMAIN_SUCCESS")
                        # Native PG principal is credential-bound, not a
                        # request field. A normal Runtime bearer must not read
                        # the Harness-profile Job, even with its actual Job ID.
                        with pytest.raises(OwnerCallError):
                            await caller.call_tool(
                                "runtime.linux", "job.get", {"jobId": actual_job}
                            )
                        print("R26_CROSS_PRINCIPAL_JOB_READ_REJECTED")
                        # Existing Harness Gateway effect adapter must recognize
                        # the dedicated physical owner alias and consume the
                        # old immutable Job through the real MCP SDK, never
                        # creating a second Runtime attempt on recovery.
                        # Explicit checked-out Harness source for this
                        # optional real-PG consumer; no global wheel fallback.
                        import sys

                        harness_source_path = str(source_root / "harness/src")
                        if harness_source_path not in sys.path:
                            sys.path.insert(0, harness_source_path)
                        from ordivon_harness.agent_plugin import AgentPluginMcpComponent
                        from ordivon_harness.plugin_gateway_effect import (
                            GatewayMcpRuntimeAdapter,
                            PluginGatewayExecutionGrant,
                        )

                        loop = asyncio.get_running_loop()

                        class RealHarnessSdkPort:
                            def call_tool(self, name, arguments):
                                result = asyncio.run_coroutine_threadsafe(
                                    agent.call_tool(name, arguments), loop
                                ).result(timeout=35)
                                assert isinstance(result.structured_content, dict)
                                return result.is_error, result.structured_content

                        adapter = GatewayMcpRuntimeAdapter(
                            AgentPluginMcpComponent(
                                name="r26-authenticated-harness-gateway",
                                transport="streamable-http",
                                url="https://gateway.local.invalid/mcp",
                            ),
                            RealHarnessSdkPort(),
                            PluginGatewayExecutionGrant(
                                capability="execution.harness",
                                workspace_id="ws-gateway-native",
                                executable_allowlist=("/usr/bin/printf",),
                            ),
                        )
                        historical = await asyncio.to_thread(
                            adapter.call_tool,
                            "workspace.exec",
                            {
                                "clientRequestId": valid_source["clientRequestId"],
                                "execution": {
                                    **valid_source["execution"],
                                    "foreignReferences": valid_source["foreignReferences"],
                                },
                            },
                        )
                        assert historical["jobId"] == actual_job
                        assert historical["semanticCompletionEvaluated"] is False
                        assert psql(
                            "SELECT count(*) FROM fresh.job_events "
                            f"WHERE job_id='{actual_job}' AND event_type='DISPATCH_ISSUED'"
                        ).strip() == "1"
                        print("R26_REAL_HARNESS_GATEWAY_EFFECT_ADAPTER_REPLAY_NO_REDISPATCH")

                    # Source revision changes AFTER original COMMIT. Historical
                    # exact replay still resolves the same Job, not a new effect.
                    advanced = verified_harness_source(
                        "supersede",
                        ORDIVON_R22_EXPECT_RUN=valid_source["runId"],
                        ORDIVON_R22_EXPECT_REQUEST=valid_source["clientRequestId"],
                        ORDIVON_R22_EXPECT_REFS_JSON=json.dumps(valid_source["foreignReferences"]),
                        **({"ORDIVON_R24_POST_RECEIPT_REVOKE": "1"} if issuer_isolated else {}),
                    )
                    assert advanced["currentRevision"] > advanced["preparedRevision"]
                    replay = await agent.call_tool("execution.submit", native_request(valid_source))
                    assert not replay.is_error, replay.structured_content
                    assert replay.structured_content["native_id"] == actual_job
                    assert (
                        psql(
                            "SELECT count(*) FROM fresh.job_events "
                            f"WHERE job_id='{actual_job}' AND event_type='DISPATCH_ISSUED'"
                        ).strip()
                        == "1"
                    )
                    print("R25_ISSUER_REVOKED_HISTORICAL_EXACT_JOB_REPLAY_NO_REDISPATCH")

                    stale_source = verified_harness_source(
                        "prepare", ORDIVON_R22_EXEC_OUTPUT="R25_INVALID_REVOKED"
                    )
                    invalid_rev = verified_harness_source(
                        "supersede",
                        ORDIVON_R22_EXPECT_RUN=stale_source["runId"],
                        ORDIVON_R22_EXPECT_REQUEST=stale_source["clientRequestId"],
                        ORDIVON_R22_EXPECT_REFS_JSON=json.dumps(stale_source["foreignReferences"]),
                    )
                    assert invalid_rev["currentRevision"] > invalid_rev["preparedRevision"]
                    rejected = await agent.call_tool(
                        "execution.submit", native_request(stale_source)
                    )
                    assert rejected.is_error, rejected.structured_content
                    assert rejected.structured_content["error"]["code"] == "AUTHORIZATION_DENIED"
                    assert (
                        psql(
                            "SELECT count(*) FROM fresh.jobs "
                            f"WHERE client_request_id='{stale_source['clientRequestId']}'"
                        ).strip()
                        == "0"
                    )
                    print("R25_SAME_PG_REVOKED_ISSUER_REJECTED_BEFORE_NEW_NATIVE_JOB")

                    stopped_source = verified_harness_source(
                        "prepare", ORDIVON_R22_EXEC_OUTPUT="R25_STOPPED_ISSUER"
                    )
                    stopped_step = verified_harness_source(
                        "supersede",
                        ORDIVON_R25_SOURCE_STOP="1",
                        ORDIVON_R22_EXPECT_RUN=stopped_source["runId"],
                        ORDIVON_R22_EXPECT_REQUEST=stopped_source["clientRequestId"],
                        ORDIVON_R22_EXPECT_REFS_JSON=json.dumps(
                            stopped_source["foreignReferences"]
                        ),
                    )
                    assert stopped_step["currentRevision"] > stopped_step["preparedRevision"]
                    stopped = await agent.call_tool(
                        "execution.submit", native_request(stopped_source)
                    )
                    assert stopped.is_error
                    assert stopped.structured_content["error"]["code"] == "AUTHORIZATION_DENIED"
                    assert (
                        psql(
                            "SELECT count(*) FROM fresh.jobs "
                            f"WHERE client_request_id='{stopped_source['clientRequestId']}'"
                        ).strip()
                        == "0"
                    )
                    print("R25_SAME_PG_TERMINAL_RUN_REJECTED_BEFORE_NEW_NATIVE_JOB")

                    absent_run_source = verified_harness_source(
                        "prepare", ORDIVON_R22_EXEC_OUTPUT="R25_MISSING_RUN_REFERENCE"
                    )
                    without_run = native_request(absent_run_source)
                    without_run["authorityReferences"] = [
                        item
                        for item in absent_run_source["foreignReferences"]
                        if item["type"] != "harness_run"
                    ]
                    absent = await agent.call_tool("execution.submit", without_run)
                    assert absent.is_error
                    assert absent.structured_content["error"]["code"] == "AUTHORIZATION_DENIED"
                    assert (
                        psql(
                            "SELECT count(*) FROM fresh.jobs "
                            f"WHERE client_request_id='{absent_run_source['clientRequestId']}'"
                        ).strip()
                        == "0"
                    )
                    print("R25_UNVERIFIABLE_ISSUER_REFERENCE_FAILS_CLOSED")

                    changed_args_source = verified_harness_source(
                        "prepare", ORDIVON_R22_EXEC_OUTPUT="R25_AUTHORIZED_ORIGINAL"
                    )
                    forged_execution = native_request(changed_args_source)
                    forged_execution["args"] = ["R25_UNAUTHORIZED_CHANGED_EXECUTION"]
                    changed_args = await agent.call_tool("execution.submit", forged_execution)
                    assert changed_args.is_error, (
                        "issuer currentness alone must NEVER authorize "
                        "changed native physical bytes"
                    )
                    assert (
                        changed_args.structured_content["error"]["code"] == "AUTHORIZATION_DENIED"
                    )
                    assert (
                        psql(
                            "SELECT count(*) FROM fresh.jobs "
                            f"WHERE client_request_id='{changed_args_source['clientRequestId']}'"
                        ).strip()
                        == "0"
                    )
                    print("R25_ISSUER_ORIGINAL_NATIVE_REQUEST_BYTES_BOUND")

                    # A well-shaped foreign Reference cannot conjure source
                    # authorization for an absent Run or expired Fence.
                    expired_source = verified_harness_source(
                        "prepare",
                        ORDIVON_R22_EXEC_OUTPUT="R25_EXPIRED_ISSUER",
                        ORDIVON_R25_EXPIRED_ISSUER="1",
                    )
                    expired = await agent.call_tool(
                        "execution.submit", native_request(expired_source)
                    )
                    assert expired.is_error, expired.structured_content
                    assert expired.structured_content["error"]["code"] == "AUTHORIZATION_DENIED"
                    assert (
                        psql(
                            "SELECT count(*) FROM fresh.jobs "
                            f"WHERE client_request_id='{expired_source['clientRequestId']}'"
                        ).strip()
                        == "0"
                    )
                    print("R25_SAME_PG_EXPIRED_ISSUER_REJECTED_BEFORE_NEW_NATIVE_JOB")

                    # Race against an independently COMMITTING source writer.
                    racing_source = verified_harness_source(
                        "prepare", ORDIVON_R22_EXEC_OUTPUT="R25_REVOCATION_RACE"
                    )
                    txn_ready = root / "r25-issuer-writer-uncommitted"
                    txn_release = root / "r25-issuer-writer-commit"
                    src_script = (
                        source_root
                        / "harness/rust-migration/consumer-acceptance"
                        / "real_pg_fenced_gateway_supersede.py"
                    )
                    writer_env = {
                        **os.environ,
                        "PYTHONPATH": str(source_root / "harness/src"),
                        "ORDIVON_R22_HARNESS_PG_DSN": (
                            f"host={root} port=5432 dbname=postgres user=postgres"
                        ),
                        "ORDIVON_R25_REAL_EPOCH_ISSUER": "1",
                        "ORDIVON_R22_EXPECT_RUN": racing_source["runId"],
                        "ORDIVON_R22_EXPECT_REQUEST": racing_source["clientRequestId"],
                        "ORDIVON_R22_EXPECT_REFS_JSON": json.dumps(
                            racing_source["foreignReferences"]
                        ),
                        "ORDIVON_R25_REVOKE_PENDING": str(txn_ready),
                        "ORDIVON_R25_REVOKE_RELEASE": str(txn_release),
                    }
                    writer = subprocess.Popen(
                        [os.environ["ORDIVON_GATEWAY_PG_E2E_HARNESS_PYTHON"], str(src_script)],
                        env=writer_env,
                        text=True,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                    )
                    try:
                        for _ in range(300):
                            if txn_ready.exists() or writer.poll() is not None:
                                break
                            await asyncio.sleep(0.025)
                        assert txn_ready.exists(), "issuer writer never acquired real PG row lock"
                        assert writer.poll() is None
                        race_submit = asyncio.create_task(
                            agent.call_tool("execution.submit", native_request(racing_source))
                        )
                        await asyncio.sleep(0.1)
                        assert not race_submit.done(), (
                            "new native Job bypassed uncommitted issuer revision row lock"
                        )
                        assert (
                            psql(
                                "SELECT count(*) FROM fresh.jobs "
                                f"WHERE client_request_id='{racing_source['clientRequestId']}'"
                            ).strip()
                            == "0"
                        )
                        txn_release.touch()
                        rejected_race = await race_submit
                        assert rejected_race.is_error, rejected_race.structured_content
                        assert (
                            psql(
                                "SELECT count(*) FROM fresh.jobs "
                                f"WHERE client_request_id='{racing_source['clientRequestId']}'"
                            ).strip()
                            == "0"
                        )
                        print("R25_REAL_PG_CONCURRENT_REVISION_WRITE_SERIALIZED_WITH_NEW_JOB")
                    finally:
                        txn_release.touch()
                        writer.communicate(timeout=24)
                    assert writer.returncode == 0, "source PG writer did not commit"
                return
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
                # These are caller-declared reference bytes only. Native PG
                # preserves their identity; it cannot prove Harness issuer
                # currentness or grant Runtime physical execution rights.
                harness_fence = {
                    "namespace": "ordivon.harness",
                    "type": "dispatch_fence",
                    "id": "fence:" + secrets.token_hex(12),
                    "generation": "7",
                    "digest": "sha256:" + secrets.token_hex(32),
                }
                harness_refs = [harness_fence]
                source_manifest = None
                source_owner_params: dict[str, object] = {}
                if harness_source:
                    source_manifest = verified_harness_source(
                        "prepare", ORDIVON_R22_EXEC_OUTPUT=agent_output
                    )
                    agent_request = source_manifest["clientRequestId"]
                    harness_refs = source_manifest["foreignReferences"]
                    assert len(harness_refs) == 4
                    assert harness_refs[-1]["type"] == "dispatch_fence"
                    assert source_manifest["fenceDigest"] == harness_refs[-1]["digest"]
                    harness_fence = harness_refs[-1]
                    original_execution = source_manifest["execution"]
                    source_owner_params = {
                        field: original_execution[field]
                        for field in (
                            "cwdRelative",
                            "env",
                            "timeoutMs",
                            "stdoutLimitBytes",
                            "stderrLimitBytes",
                        )
                    }
                    assert source_manifest["preparedRevision"] == int(harness_fence["generation"])
                    print("R22_TRUE_HARNESS_PG_CAS_INTENT_FENCE_PREPARED")
                submitted = await agent.call_tool(
                    "execution.submit",
                    {
                        "capability": "execution.linux",
                        "requestId": agent_request,
                        "workspaceId": "ws-gateway-native",
                        "executable": "/usr/bin/printf",
                        "args": [agent_output],
                        "authorityReferences": harness_refs,
                        **source_owner_params,
                    },
                )
                assert not submitted.is_error, submitted.structured_content
                north = submitted.structured_content
                assert isinstance(north, dict), submitted
                north_ref = north["operation_ref"]
                if source_manifest is not None:
                    lost = verified_harness_source(
                        "unknown",
                        ORDIVON_R22_EXPECT_RUN=source_manifest["runId"],
                        ORDIVON_R22_EXPECT_REQUEST=agent_request,
                        ORDIVON_R22_EXPECT_REFS_JSON=json.dumps(harness_refs),
                    )
                    assert lost["standing"] == "UNKNOWN"
                    print("R22_TRUE_HARNESS_PG_UNKNOWN_AFTER_OWNER_SUBMIT")
                replay = await agent.call_tool(
                    "execution.submit",
                    {
                        "capability": "execution.linux",
                        "requestId": agent_request,
                        "workspaceId": "ws-gateway-native",
                        "executable": "/usr/bin/printf",
                        "args": [agent_output],
                        "authorityReferences": harness_refs,
                        **source_owner_params,
                    },
                )
                assert not replay.is_error, replay.structured_content
                assert replay.structured_content["operation_ref"] == north_ref
                if source_manifest is not None:
                    # Exact original request identity includes the enforceable
                    # stdout/stderr byte ceilings. No new Job may appear if
                    # the same key now requests a larger output allowance.
                    with pytest.raises(OwnerCallError):
                        await gateway.execution_submit(
                            capability="execution.linux",
                            request_id=agent_request,
                            workspace_id="ws-gateway-native",
                            executable="/usr/bin/printf",
                            args=[agent_output],
                            cwd_relative=source_owner_params["cwdRelative"],
                            env=source_owner_params["env"],
                            timeout_ms=source_owner_params["timeoutMs"],
                            stdout_limit_bytes=source_owner_params["stdoutLimitBytes"] + 1,
                            stderr_limit_bytes=source_owner_params["stderrLimitBytes"],
                            authority_references=harness_refs,
                        )
                    print("R22_CHANGED_OUTPUT_LIMIT_SAME_REQUEST_ID_CONFLICTS_NO_REDISPATCH")
                # A different fence generation cannot reuse one committed
                # Job's idempotent clientRequestId.
                with pytest.raises(OwnerCallError):
                    await gateway.execution_submit(
                        capability="execution.linux",
                        request_id=agent_request,
                        workspace_id="ws-gateway-native",
                        executable="/usr/bin/printf",
                        args=[agent_output],
                        authority_references=[
                            *harness_refs[:-1],
                            {**harness_fence, "generation": "99"},
                        ],
                        cwd_relative=source_owner_params.get("cwdRelative", "."),
                        env=source_owner_params.get("env"),
                        timeout_ms=source_owner_params.get("timeoutMs"),
                        stdout_limit_bytes=source_owner_params.get("stdoutLimitBytes"),
                        stderr_limit_bytes=source_owner_params.get("stderrLimitBytes"),
                    )
                committed_plan = json.loads(
                    psql(
                        "SELECT execution_plan_json FROM fresh.jobs "
                        f"WHERE principal='pg-consumer' AND client_request_id='{agent_request}'"
                    ).strip()
                )
                assert committed_plan["foreignReferences"] == harness_refs
                assert (
                    psql(
                        "SELECT count(*) FROM fresh.jobs "
                        f"WHERE principal='pg-consumer' AND client_request_id='{agent_request}'"
                    ).strip()
                    == "1"
                )
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
                    assert not got.is_error, (
                        f"Owner job.observe refused current native Job: {got.structured_content}"
                    )
                    if got.structured_content["terminal"]:
                        break
                assert got.structured_content["terminal"]
                assert got.structured_content["exit_code"] == 0
                assert got.structured_content["artifact_projection_complete"]
                # PostgreSQL's native evidence model is a frozen Job plan
                # plus exact Attempt-bound execution_result/stdio artifacts.
                # The separate SQLite legacy terminal_evidence artifact is
                # not produced by the PG Runner; do not invent that surface.
                native_job_id = psql(
                    "SELECT job_id FROM fresh.jobs "
                    f"WHERE principal='pg-consumer' AND client_request_id='{agent_request}'"
                ).strip()
                native_results = psql(
                    "SELECT count(*) FROM fresh.artifacts r JOIN fresh.jobs j "
                    "ON j.job_id=r.job_id "
                    f"WHERE j.client_request_id='{agent_request}' AND r.kind='execution_result'"
                ).strip()
                assert native_results == "1", "terminal result must be committed as a PG Artifact"
                found_bytes = False
                terminal_result_seen = False
                for artifact_id in got.structured_content["artifact_ids"]:
                    chunk = await agent.call_tool(
                        "artifact.read",
                        # A validated RunnerResult can exceed 1 KiB; a partial
                        # JSON prefix is not a missing terminal artifact.
                        {"operationRef": north_ref, "artifactId": artifact_id, "maxBytes": 65536},
                    )
                    assert not chunk.is_error
                    data = chunk.structured_content["content"]
                    found_bytes |= agent_output in data
                    try:
                        artifact_json = json.loads(data)
                    except TypeError, ValueError:
                        continue
                    if (
                        isinstance(artifact_json, dict)
                        and artifact_json.get("jobId")
                        and "finishedUnixMs" in artifact_json
                        and "status" in artifact_json
                    ):
                        # PG registers different JSON evidence artifacts;
                        # RunnerResult is precisely the finished, status-bearing
                        # result, not the source-observation or start record.
                        assert artifact_json["jobId"] == native_job_id
                        assert artifact_json.get("attemptId", "").startswith("attempt-")
                        assert artifact_json.get("exitCode") == 0
                        terminal_result_seen = True
                assert found_bytes, "northbound MCP must retain actual Runner stdout"
                assert terminal_result_seen, (
                    "Gateway artifact.read must retain PG's validated native Runner "
                    "terminal result, bound to the same durably committed Job identity"
                )
                committed_after_terminal = json.loads(
                    psql(
                        "SELECT execution_plan_json FROM fresh.jobs "
                        f"WHERE principal='pg-consumer' AND client_request_id='{agent_request}'"
                    ).strip()
                )
                assert committed_after_terminal["foreignReferences"] == harness_refs
                if source_manifest is not None:
                    source_execution = source_manifest["execution"]
                    # Source's original full workspace.exec request is
                    # SHA-bound by its ToolIntent. Gateway's public
                    # execution.submit does not expose stdout/stderr output
                    # ceilings, so the real Runtime Plan may silently use
                    # wider default values. A Job/ForeignReference match
                    # proves provenance, NOT exact original physical plan.
                    assert (
                        committed_after_terminal["workspaceId"] == (source_execution["workspaceId"])
                    )
                    assert Path(committed_after_terminal["executable"]) == Path(
                        source_execution["executable"]
                    ).resolve(strict=True)
                    assert committed_after_terminal["args"] == source_execution["args"]
                    assert committed_after_terminal["timeoutMs"] == source_execution["timeoutMs"]
                    assert committed_after_terminal["env"] == source_execution["env"]
                    # Runtime's source-faithful normalized Plan stores the
                    # *resolved* absolute workspace cwd, not the caller's
                    # literal cwdRelative input.
                    assert Path(committed_after_terminal["cwd"]) == (
                        Path(committed_after_terminal["workspacePath"])
                        / source_execution["cwdRelative"]
                    ).resolve(strict=True)
                    source_stdout = source_execution["stdoutLimitBytes"]
                    source_stderr = source_execution["stderrLimitBytes"]
                    runtime_stdout = committed_after_terminal["stdoutLimitBytes"]
                    runtime_stderr = committed_after_terminal["stderrLimitBytes"]
                    assert source_stdout == source_stderr == 262144
                    assert runtime_stdout > 0 and runtime_stderr > 0
                    assert (runtime_stdout, runtime_stderr) == (
                        source_stdout,
                        source_stderr,
                    ), (
                        "R22_RED: actual native Runtime Plan output limits differ from "
                        "durably committed Harness original Tool Intent; "
                        f"source={(source_stdout, source_stderr)}, "
                        f"owner={(runtime_stdout, runtime_stderr)}"
                    )

                    if os.getenv("ORDIVON_GATEWAY_PG_E2E_HARNESS_ADAPTER") == "1":
                        # Consume the ACTUAL typed SDK's Gateway HTTP/Runtime
                        # Owner receipts through the *production* Harness
                        # adapter. These bytes originate in real PG Job and
                        # systemd Runner, not the Harness fake MCP fixture.
                        # Reuse the already-committed Job: NO second dispatch.
                        from ordivon_harness.agent_plugin import AgentPluginMcpComponent
                        from ordivon_harness.plugin_gateway_effect import (
                            GatewayMcpRuntimeAdapter,
                            PluginGatewayExecutionGrant,
                        )

                        loop = asyncio.get_running_loop()

                        class RealSdkHarnessMcpPort:
                            def __init__(self, *, shadow_owner_alias: bool = False):
                                self.shadow_owner_alias = shadow_owner_alias

                            def call_tool(self, name, arguments):
                                # Production Harness port is synchronous; the
                                # official MCP Client is async. This *test-only*
                                # thread adapter keeps the existing Gateway
                                # SDK session and Runtime authority unchanged.
                                response = asyncio.run_coroutine_threadsafe(
                                    agent.call_tool(name, arguments),
                                    loop,
                                ).result(timeout=35)
                                assert isinstance(response.structured_content, dict)
                                payload = response.structured_content
                                if self.shadow_owner_alias and name == "execution.submit":
                                    # After ACTUAL native SDK response, inject a
                                    # second contradictory alias. This is an
                                    # adversarial protocol-consumer boundary,
                                    # NOT a claim the official Gateway emits it.
                                    payload = {**payload, "ownerId": "runtime.windows"}
                                return response.is_error, payload

                        real_component = AgentPluginMcpComponent(
                            name="real-pg-gateway-sdk",
                            transport="streamable-http",
                            url="https://gateway.local.invalid/mcp",
                        )
                        real_grant = PluginGatewayExecutionGrant(
                            capability="execution.linux",
                            workspace_id="ws-gateway-native",
                            executable_allowlist=("/usr/bin/printf",),
                        )
                        harness_adapter = GatewayMcpRuntimeAdapter(
                            real_component,
                            RealSdkHarnessMcpPort(),
                            real_grant,
                        )
                        real_request = {
                            "clientRequestId": agent_request,
                            "execution": source_manifest["execution"],
                        }
                        true_owner_submit = await asyncio.to_thread(
                            harness_adapter.call_tool,
                            "workspace.exec",
                            real_request,
                        )
                        assert true_owner_submit["jobId"] == native_job_id
                        true_owner_resolution = await asyncio.to_thread(
                            harness_adapter.call_tool,
                            "task.list",
                            {
                                "clientRequestId": agent_request,
                                "workspaceId": "ws-gateway-native",
                            },
                        )
                        assert true_owner_resolution["jobs"] == [
                            {
                                "jobId": native_job_id,
                                "clientRequestId": agent_request,
                                "workspaceId": "ws-gateway-native",
                            }
                        ]
                        true_owner_observed = await asyncio.to_thread(
                            harness_adapter.call_tool,
                            "task.observe",
                            {"jobId": native_job_id, "waitMs": 0},
                        )
                        assert true_owner_observed["jobId"] == native_job_id
                        assert true_owner_observed["executionTerminal"] is True
                        assert true_owner_observed["deliveryDisposition"] == "committed"
                        assert true_owner_observed["resultAvailable"] is True
                        assert true_owner_observed["semanticCompletionEvaluated"] is False
                        assert harness_adapter._operation_refs == {native_job_id: north_ref}
                        assert harness_adapter._operation_requests == {native_job_id: agent_request}
                        from ordivon_harness.runtime_port import HarnessRuntimeClientError

                        adversarial_adapter = GatewayMcpRuntimeAdapter(
                            real_component,
                            RealSdkHarnessMcpPort(shadow_owner_alias=True),
                            real_grant,
                        )
                        with pytest.raises(HarnessRuntimeClientError, match="conflicting"):
                            await asyncio.to_thread(
                                adversarial_adapter.call_tool,
                                "workspace.exec",
                                real_request,
                            )
                        # Even a genuine Owner reply cannot be bound to
                        # an internally contradictory foreign source claim.
                        assert adversarial_adapter._operation_refs == {}
                        assert adversarial_adapter._operation_requests == {}
                        native_dispatch_after_harness_adapter = psql(
                            "SELECT count(*) FROM fresh.job_events e JOIN fresh.jobs j "
                            "ON e.job_id=j.job_id WHERE e.event_type='DISPATCH_ISSUED' "
                            f"AND j.principal='pg-consumer' AND j.client_request_id='{agent_request}'"
                        ).strip()
                        assert native_dispatch_after_harness_adapter == "1"
                        print(
                            "R25_ACTUAL_GATEWAY_SDK_TO_HARNESS_RECEIPT_ADAPTER"
                            "_SAME_NATIVE_PG_JOB_NO_SECOND_DISPATCH"
                        )
                        print(
                            "R25_REAL_NATIVE_SDK_RECEIPT_WITH_INJECTED_CONFLICTING"
                            "_OWNER_ALIAS_REJECTED_BEFORE_JOB_BINDING"
                        )
                    # Deliberately discard the original submit response as the
                    # Harness observation. Source already wrote UNKNOWN; the
                    # ONLY recovery input is the true Owner's resolved Job,
                    # terminal receipt and same native PG frozen Plan.
                    owner_obs = {
                        "jobId": native_job_id,
                        "clientRequestId": agent_request,
                        "executionTerminal": got.structured_content["terminal"],
                        "deliveryDisposition": got.structured_content["delivery_disposition"],
                        "exitCode": got.structured_content["exit_code"],
                    }
                    # A different genuine PG Job in the same principal and
                    # Workspace is STILL not the Owner receipt for this Intent.
                    # No receipt is written for a forged clientRequestId/Job.
                    wrong_job = verified_harness_source(
                        "reconcile",
                        expect_rejection=True,
                        ORDIVON_R22_EXPECT_RUN=source_manifest["runId"],
                        ORDIVON_R22_EXPECT_REQUEST=agent_request,
                        ORDIVON_R22_EXPECT_REFS_JSON=json.dumps(harness_refs),
                        ORDIVON_R22_OWNER_JOB=receipt.native_id,
                        ORDIVON_R22_OWNER_OBSERVATION=json.dumps(
                            {
                                **owner_obs,
                                "jobId": receipt.native_id,
                            }
                        ),
                    )
                    assert wrong_job["rejected"] is True
                    print("R22_WRONG_REAL_OWNER_JOB_FAIL_CLOSED_BEFORE_RECEIPT")
                    settled = verified_harness_source(
                        "reconcile",
                        ORDIVON_R22_EXPECT_RUN=source_manifest["runId"],
                        ORDIVON_R22_EXPECT_REQUEST=agent_request,
                        ORDIVON_R22_EXPECT_REFS_JSON=json.dumps(harness_refs),
                        ORDIVON_R22_OWNER_JOB=native_job_id,
                        ORDIVON_R22_OWNER_OBSERVATION=json.dumps(owner_obs),
                    )
                    assert settled["standing"] == "OWNER_CONFIRMED_RECEIPT"
                    assert settled["jobId"] == native_job_id
                    assert settled["dispatchCount"] == 1
                    assert settled["semanticCompletionEvaluated"] is False
                    print("R22_TRUE_PG_OWNER_JOB_HARNESS_UNKNOWN_RECONCILED_NO_REDISPATCH")

                if (
                    source_manifest is not None
                    and os.getenv("ORDIVON_GATEWAY_PG_E2E_POST_REVOKE_REPLAY") == "1"
                ):
                    # Three temporally distinct facts:
                    # 1) this exact native Owner Job *was* admitted and run,
                    # 2) issuer's current Run revision has since superseded
                    #    the original Fence, so NEW work needs fresh authority,
                    # 3) an exact replay of the already committed request must
                    #    resolve historical Job identity without redispatch.
                    superseded_history = verified_harness_source(
                        "supersede",
                        ORDIVON_R24_POST_RECEIPT_REVOKE="1",
                        ORDIVON_R22_EXPECT_RUN=source_manifest["runId"],
                        ORDIVON_R22_EXPECT_REQUEST=agent_request,
                        ORDIVON_R22_EXPECT_REFS_JSON=json.dumps(harness_refs),
                    )
                    assert superseded_history["standing"] == (
                        "FENCE_SUPERSEDED_BY_DURABLE_RUN_REVISION"
                    )
                    assert (
                        superseded_history["currentRevision"]
                        > (superseded_history["preparedRevision"])
                    )
                    assert (
                        superseded_history["historicalReceiptDigest"] == (settled["receiptDigest"])
                    )
                    reissued = await agent.call_tool(
                        "execution.submit",
                        {
                            "capability": "execution.linux",
                            "requestId": agent_request,
                            "workspaceId": "ws-gateway-native",
                            "executable": "/usr/bin/printf",
                            "args": [agent_output],
                            "authorityReferences": harness_refs,
                            **source_owner_params,
                        },
                    )
                    assert not reissued.is_error, reissued.structured_content
                    assert reissued.structured_content["operation_ref"] == north_ref
                    # After revocation, a changed physical intent under the
                    # original RequestId must NOT fall back to a fresh Job or
                    # silently rewrite immutable historical effect identity.
                    with pytest.raises(OwnerCallError) as changed_after_revoke:
                        await gateway.execution_submit(
                            capability="execution.linux",
                            request_id=agent_request,
                            workspace_id="ws-gateway-native",
                            executable="/usr/bin/printf",
                            args=[agent_output],
                            cwd_relative=source_owner_params["cwdRelative"],
                            env=source_owner_params["env"],
                            timeout_ms=source_owner_params["timeoutMs"],
                            stdout_limit_bytes=source_owner_params["stdoutLimitBytes"] + 1,
                            stderr_limit_bytes=source_owner_params["stderrLimitBytes"],
                            authority_references=harness_refs,
                        )
                    assert changed_after_revoke.value.error is not None
                    assert changed_after_revoke.value.error["code"] == "IDEMPOTENCY_CONFLICT"
                    # Verify through native Owner state, not just SDK reply.
                    existing_owner_history = psql(
                        "SELECT COUNT(*) FROM fresh.jobs "
                        f"WHERE principal='pg-consumer' AND client_request_id='{agent_request}'"
                    ).strip()
                    assert existing_owner_history == "1"
                    dispatches_after_revoke = psql(
                        "SELECT count(*) FROM fresh.job_events e JOIN fresh.jobs j "
                        "ON e.job_id=j.job_id WHERE e.event_type='DISPATCH_ISSUED' "
                        f"AND j.principal='pg-consumer' AND j.client_request_id='{agent_request}'"
                    ).strip()
                    assert dispatches_after_revoke == "1"
                    # Full immutable request identity remains bound to the
                    # original frozen Owner Plan even though issuer now rejects
                    # that Fence for any future fresh admission.
                    assert (
                        json.loads(
                            psql(
                                "SELECT execution_plan_json FROM fresh.jobs "
                                f"WHERE principal='pg-consumer' AND client_request_id='{agent_request}'"
                            ).strip()
                        )
                        == committed_after_terminal
                    )
                    print(
                        "R24_POST_ISSUER_REVOCATION_EXACT_REPLAY_SAME_"
                        "PG_JOB_NO_NEW_DISPATCH_HISTORICAL_RECEIPT_STABLE"
                    )

                if (
                    harness_source
                    and os.getenv("ORDIVON_GATEWAY_PG_E2E_STALE_FENCE_FALSIFY") == "1"
                ):
                    # Negative control: source qualifies a real Fence, then
                    # a new durable Run revision supersedes it BEFORE sending.
                    # The PG Owner preserves the stale reference only as
                    # metadata; it does not yet consult the Harness issuer.
                    stale_output = "R22_STALE_FENCE_PHYSICAL_COUNTEREXAMPLE"
                    stale_source = verified_harness_source(
                        "prepare", ORDIVON_R22_EXEC_OUTPUT=stale_output
                    )
                    stale_refs = stale_source["foreignReferences"]
                    superseded = verified_harness_source(
                        "supersede",
                        ORDIVON_R22_EXPECT_RUN=stale_source["runId"],
                        ORDIVON_R22_EXPECT_REQUEST=stale_source["clientRequestId"],
                        ORDIVON_R22_EXPECT_REFS_JSON=json.dumps(stale_refs),
                    )
                    assert superseded["standing"] == ("FENCE_SUPERSEDED_BY_DURABLE_RUN_REVISION")
                    assert superseded["currentRevision"] > superseded["preparedRevision"]
                    stale_result = await agent.call_tool(
                        "execution.submit",
                        {
                            "capability": "execution.linux",
                            "requestId": stale_source["clientRequestId"],
                            "workspaceId": "ws-gateway-native",
                            "executable": "/usr/bin/printf",
                            "args": [stale_output],
                            "authorityReferences": stale_refs,
                            **{
                                field: stale_source["execution"][field]
                                for field in (
                                    "cwdRelative",
                                    "env",
                                    "timeoutMs",
                                    "stdoutLimitBytes",
                                    "stderrLimitBytes",
                                )
                            },
                        },
                    )
                    # This is an EXISTING SECURITY/CONSISTENCY GAP, not
                    # an expected authorization contract or a passing Fence.
                    assert not stale_result.is_error, (
                        "Runtime unexpectedly acquired live Harness issuer"
                        " validation without an issuer admission channel"
                    )
                    stale_ref = stale_result.structured_content["operation_ref"]
                    for _ in range(20):
                        stale_observed = await agent.call_tool(
                            "execution.get",
                            {"operationRef": stale_ref, "waitMs": 1500},
                        )
                        assert not stale_observed.is_error
                        if stale_observed.structured_content["terminal"]:
                            break
                    assert stale_observed.structured_content["terminal"]
                    assert stale_observed.structured_content["exit_code"] == 0
                    stale_plan = json.loads(
                        psql(
                            "SELECT execution_plan_json FROM fresh.jobs "
                            "WHERE principal='pg-consumer' "
                            f"AND client_request_id='{stale_source['clientRequestId']}'"
                        ).strip()
                    )
                    assert stale_plan["foreignReferences"] == stale_refs
                    assert stale_plan["args"] == [stale_output]
                    print(
                        "R22_P0_STALE_HARNESS_FENCE_ADMITTED_AND_PHYSICALLY_EXECUTED"
                        "_BY_METADATA_ONLY_NATIVE_OWNER"
                    )

                if dispatch_gate:
                    # Distinct from the existing R22 negative control (revoke
                    # BEFORE Job admission). Here native PG must have committed
                    # DISPATCH_ISSUED, and systemd has launched its runner
                    # wrapper, before the genuine Harness issuer revokes.
                    # This falsifies a *spawn-current* requirement. It does
                    # not falsify a weaker admission-only authorization policy.
                    post_dispatch_output = "R24_EFFECT_STARTED_AFTER_ISSUER_REVOCATION"
                    live = verified_harness_source(
                        "prepare", ORDIVON_R22_EXEC_OUTPUT=post_dispatch_output
                    )
                    frozen = live["execution"]
                    gate_enabled.touch()
                    pending_get = None
                    try:
                        # Native Runtime may enter dispatch while accepting
                        # workspace.exec or later during job.observe. Do not
                        # deadlock a single MCP submit on our controlled
                        # systemd-run barrier; drive progress asynchronously.
                        submit_task = asyncio.create_task(
                            agent.call_tool(
                                "execution.submit",
                                {
                                    "capability": "execution.linux",
                                    "requestId": live["clientRequestId"],
                                    "workspaceId": "ws-gateway-native",
                                    "executable": "/usr/bin/printf",
                                    "args": [post_dispatch_output],
                                    "context": "trusted_local",
                                    "authorityReferences": live["foreignReferences"],
                                    **{
                                        field: frozen[field]
                                        for field in (
                                            "cwdRelative",
                                            "env",
                                            "timeoutMs",
                                            "stdoutLimitBytes",
                                            "stderrLimitBytes",
                                        )
                                    },
                                },
                            )
                        )
                        for _ in range(300):
                            if gate_ready.exists():
                                break
                            if submit_task.done():
                                # A completed admission may have deferred
                                # native dispatch to the first owner observe.
                                admitted = await submit_task
                                assert not admitted.is_error, admitted.structured_content
                                if pending_get is None or pending_get.done():
                                    if pending_get is not None:
                                        prior = await pending_get
                                        assert not prior.is_error, prior.structured_content
                                    pending_get = asyncio.create_task(
                                        agent.call_tool(
                                            "execution.get",
                                            {
                                                "operationRef": admitted.structured_content[
                                                    "operation_ref"
                                                ],
                                                "waitMs": 1500,
                                            },
                                        )
                                    )
                            await asyncio.sleep(0.05)
                        assert gate_ready.exists(), (
                            "native Runtime never reached the post-DISPATCH_ISSUED "
                            "pre-systemd-run barrier"
                        )
                        gated_job = psql(
                            "SELECT job_id FROM fresh.jobs "
                            "WHERE principal='pg-consumer' "
                            f"AND client_request_id='{live['clientRequestId']}'"
                        ).strip()
                        assert gated_job.startswith("job-")
                        dispatch_count = psql(
                            "SELECT count(*) FROM fresh.job_events "
                            f"WHERE job_id='{gated_job}' AND event_type='DISPATCH_ISSUED'"
                        ).strip()
                        assert dispatch_count == "1", (
                            "must record exactly one durable dispatch before revocation"
                        )
                        assert (
                            psql(
                                "SELECT count(*) FROM fresh.job_events "
                                f"WHERE job_id='{gated_job}' AND event_type='JOB_TERMINAL'"
                            ).strip()
                            == "0"
                        ), "systemd-run has NOT yet launched the real native Runner"
                        revoked = verified_harness_source(
                            "supersede",
                            ORDIVON_R22_EXPECT_RUN=live["runId"],
                            ORDIVON_R22_EXPECT_REQUEST=live["clientRequestId"],
                            ORDIVON_R22_EXPECT_REFS_JSON=json.dumps(live["foreignReferences"]),
                        )
                        assert revoked["standing"] == "FENCE_SUPERSEDED_BY_DURABLE_RUN_REVISION"
                        assert revoked["currentRevision"] == revoked["preparedRevision"] + 1
                        print("R24_REAL_PG_DISPATCH_COMMITTED_BEFORE_ISSUER_REVOCATION")
                    finally:
                        # Resume the unchanged real systemd-run and real
                        # attested native Runner even when assertion fails.
                        gate_release.touch()
                    gated = await submit_task
                    assert not gated.is_error, gated.structured_content
                    if pending_get is not None:
                        # An in-flight read may have driven the dispatch.
                        pending = await pending_get
                        assert not pending.is_error, pending.structured_content
                    assert gated.structured_content["native_id"] == gated_job
                    for _ in range(35):
                        finished = await agent.call_tool(
                            "execution.get",
                            {
                                "operationRef": gated.structured_content["operation_ref"],
                                "waitMs": 1500,
                            },
                        )
                        assert not finished.is_error, finished.structured_content
                        if finished.structured_content["terminal"]:
                            break
                    assert finished.structured_content["terminal"]
                    assert finished.structured_content["exit_code"] == 0
                    recorded_effect = False
                    for artifact_id in finished.structured_content["artifact_ids"]:
                        chunk = await agent.call_tool(
                            "artifact.read",
                            {
                                "operationRef": gated.structured_content["operation_ref"],
                                "artifactId": artifact_id,
                                "maxBytes": 65_536,
                            },
                        )
                        assert not chunk.is_error
                        recorded_effect |= (
                            post_dispatch_output in chunk.structured_content["content"]
                        )
                    assert recorded_effect, (
                        "must prove native target bytes occurred AFTER issuer Run revocation"
                    )
                    # Revocation must not silently turn exact identity
                    # resolution into a second physical dispatch. A future
                    # issuer-based policy must distinguish original COMMITTED
                    # operation replay from admission of a new effect.
                    replay_after_revocation = await agent.call_tool(
                        "execution.submit",
                        {
                            "capability": "execution.linux",
                            "requestId": live["clientRequestId"],
                            "workspaceId": "ws-gateway-native",
                            "executable": "/usr/bin/printf",
                            "args": [post_dispatch_output],
                            "context": "trusted_local",
                            "authorityReferences": live["foreignReferences"],
                            **{
                                field: frozen[field]
                                for field in (
                                    "cwdRelative",
                                    "env",
                                    "timeoutMs",
                                    "stdoutLimitBytes",
                                    "stderrLimitBytes",
                                )
                            },
                        },
                    )
                    assert not replay_after_revocation.is_error
                    assert replay_after_revocation.structured_content["native_id"] == gated_job
                    assert (
                        psql(
                            "SELECT count(*) FROM fresh.job_events "
                            f"WHERE job_id='{gated_job}' AND event_type='DISPATCH_ISSUED'"
                        ).strip()
                        == "1"
                    )
                    assert (
                        psql(
                            "SELECT count(*) FROM fresh.jobs "
                            f"WHERE principal='pg-consumer' "
                            f"AND client_request_id='{live['clientRequestId']}'"
                        ).strip()
                        == "1"
                    )
                    print("R24_P0_SPAWN_CURRENT_NOT_ENFORCED_AFTER_DISPATCH_ISSUED")

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
                    # A vanished native unit after stop intent is mechanical
                    # LOST, not proved CANCELLED. Do not manufacture success.
                    "lost",
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
                if cancellation.state == "lost":
                    assert owner_intent["attemptState"] == "lost"
                    assert owner_intent["executionTerminal"] is True
                if not cancelled.terminal:
                    assert owner_intent["attemptState"] == "stopping"
                    assert owner_intent["resultAvailable"] is False

        asyncio.run(scenario())
    finally:
        # The native Runner gate is test-only. Never allow failed test cleanup
        # to leave an already-admitted systemd unit hung before real exec.
        if "gate_release" in locals() and dispatch_gate:
            gate_release.touch()
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
