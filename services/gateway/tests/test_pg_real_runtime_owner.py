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
                        "Owner job.observe refused current native Job: "
                        f"{got.structured_content}"
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
