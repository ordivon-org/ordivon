#!/usr/bin/env python3
"""Opt-in R29: original Harness PG (other database) + native ClaimFinalizerOnly.

Runs ONLY with explicit R29_NATIVE_BIN/R29_NATIVE_RUNNER/R29_RUNTIME_SOURCE.
Creates a fresh Unix-socket-only PostgreSQL cluster, TWO distinct databases
and roles, a disposable Native Runtime MCP process and ONE native Git Workspace.
Never reads production DSNs, uses installed tokens, or touches installed units.
The independent Coding consumer is test-scoped, NOT final user acceptance.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
from pathlib import Path
import secrets
import shutil
import socket
import stat
import subprocess
import tempfile
import time
from dataclasses import replace

import psycopg
from ordivon_harness.agent_run import HarnessAgentRun
from ordivon_harness.mcp_http_client import (
    LoopbackClaimFinalizerEndpoint, LoopbackMcpEndpoint, OfficialMcpClient,
)
from ordivon_harness.postgres_store import PostgresHarnessStore
from ordivon_harness.runtime_port import HarnessWorkspaceAdmissionUnavailable
from ordivon_harness.ordivon.model import ScriptedTurnAdapter
from tests.test_r3_supported_agent_run import (
    FakeRuntime, completed, contract, execution_binding,
)

SOURCE = "5ae84bdb6a89781fd380c91696f4c904c8a69ec9"
BIN_DIR = Path("/var/tmp/ordivon-r35-fulljobartifacts-native-bin-20261121")


def checked_executable(key: str, filename: str) -> Path:
    path = Path(os.environ[key]).resolve(strict=True)
    if path != BIN_DIR / filename or not path.is_file():
        raise RuntimeError(f"{key} must use this run's disposable exact native binary")
    return path


def run(cmd: list[str], *, stdout=None) -> subprocess.CompletedProcess:
    return subprocess.run(
        cmd, check=True, text=True,
        stdout=stdout if stdout is not None else subprocess.DEVNULL,
        stderr=subprocess.PIPE, timeout=45,
    )


def call(client: OfficialMcpClient, name: str, args: dict) -> dict:
    error, data = client.call_tool(name, args)
    if error:
        raise AssertionError(f"native {name} rejected: {str(data)[:500]}")
    return data


def main() -> None:
    native_bin = checked_executable("R29_NATIVE_BIN", "ordivon-runtime-pg")
    runner_bin = checked_executable("R29_NATIVE_RUNNER", "ordivon-runtime-runner")
    source = Path(os.environ["R29_RUNTIME_SOURCE"]).resolve(strict=True)
    assert (source / "services/runtime/crates/ordivon-runtime-core/sql/pg_fresh_epoch.sql").is_file()
    source_repo = Path("/root/projects/ordivon").resolve(strict=True)
    assert SOURCE in run(["git", "-C", str(source_repo), "rev-parse", SOURCE], stdout=subprocess.PIPE).stdout

    root = Path(tempfile.mkdtemp(prefix="ordivon-r29-native-crossdb-", dir="/var/tmp"))
    # PG bootstrap runs as the existing postgres OS user, never root.
    run(["chown", "postgres:postgres", str(root)])
    root.chmod(0o755)
    sock = root / "socket"
    sock.mkdir()
    run(["chown", "postgres:postgres", str(sock)])
    # Unix-only trust auth must not expose the disposable PG socket to
    # unrelated local users on the shared execution host.
    sock.chmod(0o700)
    runtime_process: subprocess.Popen | None = None
    pg_started = False
    pgsocket_port = 39000 + secrets.randbelow(11000)
    try:
        run(["runuser", "-u", "postgres", "--", "initdb", "-D", str(root / "pg"),
             "--auth-local=trust", "--auth-host=reject", "--no-instructions"])
        run(["runuser", "-u", "postgres", "--", "pg_ctl", "-D", str(root / "pg"),
             "-o", (f"-c listen_addresses='' -c unix_socket_directories={sock} "
                    f"-c port={pgsocket_port} -c dynamic_shared_memory_type=mmap -c fsync=off"),
             "-l", str(root / "pg" / "postgres.log"), "-w", "start"])
        pg_started = True
        server_dsn = f"host={sock} port={pgsocket_port} dbname=postgres user=postgres"
        source_digest = "a" * 64

        with psycopg.connect(server_dsn, autocommit=True) as pg:
            pg.execute("CREATE SCHEMA fresh")
            pg.execute("SET search_path TO fresh")
            sql_file = (source / "services/runtime/crates/ordivon-runtime-core/sql/pg_fresh_epoch.sql")
            pg.execute(sql_file.read_text(encoding="utf-8"))
            pg.execute(
                "INSERT INTO fresh._stage_control VALUES('source','QUALIFIED_WRITER',%s,true)",
                (source_digest,),
            )
            identifier, timeline = pg.execute(
                "SELECT (SELECT system_identifier::text FROM pg_control_system()),"
                " (SELECT timeline_id FROM pg_control_checkpoint())"
            ).fetchone()
            epoch = hashlib.sha256(
                ("ordivon-pg-writer-epoch-v1\0" + source_digest + "\0"
                 + identifier + "\0" + str(timeline)).encode()
            ).hexdigest()
            pg.execute(
                "INSERT INTO fresh._stage_control VALUES('epoch','QUALIFIED_EPOCH',%s,true)",
                (epoch,),
            )
            pg.execute("CREATE ROLE runtime_app LOGIN")
            pg.execute("GRANT USAGE ON SCHEMA fresh TO runtime_app")
            pg.execute("GRANT ALL ON ALL TABLES IN SCHEMA fresh TO runtime_app")
            pg.execute("REVOKE ALL ON fresh._stage_control FROM runtime_app")
            pg.execute("GRANT SELECT, UPDATE(id) ON fresh._stage_control TO runtime_app")
            pg.execute("CREATE ROLE harness_app LOGIN")
            pg.execute("CREATE DATABASE harness_r29 OWNER harness_app")

        harness_dsn = f"host={sock} port={pgsocket_port} dbname=harness_r29 user=harness_app"
        with PostgresHarnessStore(harness_dsn, schema="harness", initialize=True):
            pass

        ordinary_token = root / "ordinary-bearer"
        dedicated_token = root / "claim-finalizer-bearer"
        ordinary_token.write_text("ordinary-" + secrets.token_urlsafe(42))
        dedicated_token.write_text("dedicated-" + secrets.token_urlsafe(42))
        ordinary_token.chmod(0o600)
        dedicated_token.chmod(0o600)
        assert ordinary_token.read_text() != dedicated_token.read_text()
        assert stat.S_IMODE(dedicated_token.stat().st_mode) == 0o600

        port_sock = socket.socket()
        port_sock.bind(("127.0.0.1", 0))
        tcp_port = port_sock.getsockname()[1]
        port_sock.close()
        env = os.environ.copy()
        for key in (
            "ORDIVON_PG_HARNESS_ISSUER_SCHEMA", "ORDIVON_PG_RELEASE_SOURCE_REPO",
            "ORDIVON_REMOTE_BEARER_TOKEN_FILE", "ORDIVON_TRUST_CF_ACCESS",
        ):
            env.pop(key, None)
        env.update({
            "ORDIVON_PG_DSN": f"host={sock} port={pgsocket_port} dbname=postgres user=runtime_app",
            "ORDIVON_PG_SCHEMA": "fresh",
            "ORDIVON_PG_SOURCE_SHA256": source_digest,
            "ORDIVON_PG_STORE_ROOT": str(root / "runtime-store"),
            "ORDIVON_PG_RUNNER": str(runner_bin),
            "ORDIVON_PG_EXECUTABLE_ROOTS_JSON": json.dumps(["/usr/bin", "/bin"]),
            "ORDIVON_PG_BIND": f"127.0.0.1:{tcp_port}",
            "ORDIVON_PG_TOKEN": ordinary_token.read_text(),
            "ORDIVON_PG_PRINCIPAL": "ordinary-r29",
            "ORDIVON_PG_HARNESS_TOKEN_FILE": str(dedicated_token),
            "ORDIVON_PG_HARNESS_PRINCIPAL": "claim-finalizer-r29",
        })
        with (root / "runtime.log").open("w") as log:
            runtime_process = subprocess.Popen(
                [str(native_bin)], env=env, stdout=log, stderr=subprocess.STDOUT
            )
        deadline = time.monotonic() + 15
        while time.monotonic() < deadline:
            if runtime_process.poll() is not None:
                raise AssertionError("isolated native PG MCP exited before TCP listen")
            try:
                with socket.create_connection(("127.0.0.1", tcp_port), timeout=0.4):
                    break
            except OSError:
                time.sleep(0.08)
        else:
            raise AssertionError("isolated native PG MCP did not start")

        ordinary = OfficialMcpClient(
            LoopbackMcpEndpoint(f"http://127.0.0.1:{tcp_port}/mcp"),
            bearer_token_file=ordinary_token,
        )
        dedicated = OfficialMcpClient(
            LoopbackClaimFinalizerEndpoint(f"http://127.0.0.1:{tcp_port}/harness/mcp"),
            bearer_token_file=dedicated_token,
        )
        ordinary_tools = {t["name"] for t in ordinary.list_tools()}
        dedicated_tools = {t["name"] for t in dedicated.list_tools()}
        assert "workspace.open" in ordinary_tools
        assert "workspace.claim.release" not in ordinary_tools
        assert dedicated_tools == {
            "workspace.get", "workspace.claim.reserve",
            "workspace.claim.get", "workspace.claim.release",
        }, dedicated_tools
        print("R29_CROSSDB_NATIVE_CLAIMONLY_FOUR_TOOL_CATALOG=PASS", flush=True)

        suffix = secrets.token_hex(6)
        workspace_id = "ws-harness-r29-native-claimonly-" + suffix
        original = call(ordinary, "workspace.open", {
            "schemaVersion": 1, "workspaceId": workspace_id,
            "sourceRepo": str(source_repo), "sourceRevision": SOURCE,
        })
        assert original["workspaceId"] == workspace_id
        # The disposable Native store has the original checkout at the
        # documented StoreConfig.workspaces_root(), not at the recipient Git.
        native_source_worktree = root / "runtime-store" / "workspaces" / workspace_id
        assert native_source_worktree.is_dir()
        assert run(["git", "-C", str(native_source_worktree), "rev-parse",
                    "--show-toplevel"], stdout=subprocess.PIPE).stdout.strip() == str(
                        native_source_worktree.resolve()
                    )
        value = contract("r29-crossdb-" + suffix, tools=True)
        binding = replace(execution_binding(value), workspace_ref=workspace_id)
        adapter_calls: list[str] = []
        scripted = ScriptedTurnAdapter((completed("model-call:r29-native-claimonly"),))

        def adapter(v):
            adapter_calls.append(v.harness_run_id)
            return scripted

        run_handle = HarnessAgentRun.create(
            harness_dsn, "harness", value, adapter,
            execution_binding=binding, runtime=FakeRuntime(),
            workspace_claim_client=dedicated,
        )
        assert run_handle.status()["status"] == "created"
        assert scripted.requests == [], "Run creation must not invoke the Provider"
        claim = run_handle.workspace_claim.require_held()
        assert claim["state"] == "held" and claim["runRef"] == value.harness_run_id
        with psycopg.connect(server_dsn) as pg:
            rt_count = pg.execute("SELECT count(*) FROM fresh.workspace_consumer_claims").fetchone()[0]
            assert rt_count == 1
        with psycopg.connect(harness_dsn) as pg:
            h_count = pg.execute("SELECT count(*) FROM harness.runs").fetchone()[0]
            assert h_count == 1
        print("R29_SEPARATE_PG_DATABASES_ONE_NATIVE_CLAIM_ONE_RUN=PASS", flush=True)

        wrong = replace(binding, workspace_ref="ws-harness-r29-invalid-W2")
        try:
            HarnessAgentRun.open(
                harness_dsn, "harness", value.harness_run_id, adapter,
                execution_binding=wrong, runtime=FakeRuntime(),
                workspace_claim_client=dedicated,
            )
        except HarnessWorkspaceAdmissionUnavailable:
            pass
        else:
            raise AssertionError("caller W2 was admitted for original W1")
        assert scripted.requests == [], "Wrong Workspace may not call the Provider"

        pre = call(ordinary, "workspace.get", {
            "schemaVersion": 1, "workspaceId": workspace_id,
        })
        denied, refusal = ordinary.call_tool("workspace.close", {
            "schemaVersion": 1, "workspaceId": workspace_id,
            "force": False, "consumerReleased": True,
            "expectedSourceStateDigest": pre["sourceStateDigest"],
        })
        assert denied and refusal.get("error", {}).get("code") == "CONCURRENCY_LIMIT", refusal
        assert run_handle.workspace_claim.require_held()["claimId"] == claim["claimId"]
        print("R29_FINALIZER_CLAIM_DENIES_NORMAL_CLOSE_BEFORE_ACCEPTANCE=PASS", flush=True)

        # A real native Job publishes TWO scoped outputs: a unique Run output
        # and actual Coding task source. An unrelated downstream Git consumer
        # must retain BOTH before test-scoped release of their original pin.
        original_bytes = ("R29_CROSSDB_NATIVE_TEST_OUTPUT_" + suffix).encode()
        filename = "r29-original-unique.txt"
        harness_src = Path(__file__).resolve().parents[2]
        fixture = harness_src / "fixtures/harness-edit-addressing-repeated-v1/feature_flags.py"
        oracle = harness_src / "evals/harness-edit-addressing-002/oracle/feature_flags.py"
        original_coding = fixture.read_text(encoding="utf-8")
        assert original_coding.count("return False") == 2
        call(ordinary, "workspace.mutate", {
            "schemaVersion": 1, "workspaceId": workspace_id,
            "mutations": [
                {"mode": "WRITE", "relativePath": filename,
                 "content": original_bytes.decode()},
                {"mode": "WRITE", "relativePath": "feature_flags.py",
                 "content": original_coding},
            ],
        })
        issued_id = "r29-original-job-" + suffix
        physical = call(ordinary, "workspace.exec", {
            "schemaVersion": 1, "clientRequestId": issued_id,
            "execution": {
                "workspaceId": workspace_id, "executable": "/usr/bin/bash",
                "cwdRelative": ".",
                "args": ["-lc",
                         "python3 -c 'from pathlib import Path; "
                         "p=Path(\"feature_flags.py\"); v=p.read_text(); "
                         "a,b,c=v.rpartition(\"return False\"); "
                         "assert b; p.write_text(a+\"return True\"+c)' && "
                         "git add r29-original-unique.txt feature_flags.py && "
                         "git -c user.name='R29 Source' "
                         "-c user.email='r29@example.invalid' commit -m 'original output'"],
                "timeoutMs": 30000,
            },
            "waitMs": 2000,
        })
        native_job_id = physical["jobId"]
        for _ in range(30):
            if physical.get("executionTerminal"):
                break
            physical = call(ordinary, "job.observe", {
                "jobId": native_job_id, "waitMs": 2000,
            })
        assert physical["executionTerminal"] and physical["exitCode"] == 0, physical
        stable = call(ordinary, "workspace.get", {
            "schemaVersion": 1, "workspaceId": workspace_id,
        })
        assert stable["activeJobIds"] == [], stable
        original_read = call(ordinary, "workspace.read", {
            "schemaVersion": 1, "workspaceId": workspace_id,
            "relativePath": filename, "mode": "FULL", "maxBytes": 4096,
        })
        assert original_read["content"].encode() == original_bytes
        actual_coding = call(ordinary, "workspace.read", {
            "schemaVersion": 1, "workspaceId": workspace_id,
            "relativePath": "feature_flags.py", "mode": "FULL", "maxBytes": 4096,
        })["content"].encode()
        assert actual_coding == oracle.read_bytes(), "native Job must produce the exact hidden-QA target"
        denied, _ = ordinary.call_tool("workspace.close", {
            "schemaVersion": 1, "workspaceId": workspace_id,
            "force": False, "consumerReleased": True,
            "expectedSourceStateDigest": stable["sourceStateDigest"],
        })
        assert denied, "Native job terminal alone cannot release original claim"
        print("R29_ACTUAL_OS_JOB_TERMINAL_CLAIM_STILL_HELD_ORIGINAL_BYTES=PASS", flush=True)

        final_run = run_handle.run(({"role": "user", "content": "Deliver original bytes"},))
        assert final_run.loop_result.stop_code.value == "candidate_completed"
        final = run_handle.inspect_finalization_source()
        assert final["sourceStanding"] == "source-settled"
        # Reuse the ORIGINAL independent Coding Domain evaluator and normal Git.
        # This trusted test driver controls both temporary roots; it does NOT
        # prove a real external user ACK or protected Finalizer credentials.
        gate_path = harness_src / "evals/harness-edit-addressing-002/delivery_gate.py"
        spec = importlib.util.spec_from_file_location("r31_original_coding_delivery_gate", gate_path)
        assert spec is not None and spec.loader is not None
        gate = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(gate)
        source_candidate = root / "native-coding-candidate.py"
        source_candidate.write_bytes(actual_coding)
        recipient_repo = root / "independent-coding-consumer-git"
        recipient_repo.mkdir()
        run(["git", "-C", str(recipient_repo), "init", "-q"])
        recipient = recipient_repo / filename
        recipient.write_bytes(original_bytes)
        received_coding = recipient_repo / "feature_flags.py"
        # A caller who points at a plausible Git commit containing DIFFERENT
        # bytes must not be allowed to treat that as independent delivery.
        received_coding.write_bytes(original_coding.encode())

        def consumer_commit(message: str) -> str:
            # This disposable receiver owns exactly two expected outputs;
            # stage removals too, so partial-delivery failure is observable.
            run(["git", "-C", str(recipient_repo), "add", "-A"])
            run(["git", "-C", str(recipient_repo),
                 "-c", "user.name=Independent Coding Receiver",
                 "-c", "user.email=receiver@example.invalid",
                 "commit", "-q", "-m", message])
            return run(["git", "-C", str(recipient_repo), "rev-parse", "HEAD"],
                       stdout=subprocess.PIPE).stdout.strip()

        wrong_commit = consumer_commit("incorrect content before actual receipt")
        try:
            gate.qualify(source_candidate, recipient_repo, wrong_commit)
        except gate.DeliveryGateError as exc:
            assert "does not match" in str(exc)
        else:
            raise AssertionError("stale consumer Git blob was accepted as delivered")
        assert run_handle.workspace_claim.require_held()["state"] == "held"
        print("R31_EXTERNAL_GIT_WRONG_ORIGINAL_BYTES_STILL_HELD=PASS", flush=True)

        # Domain QA and the named Coding source can be green while another
        # original unsubmitted artifact would still be lost by NativeClose.
        # The consumer graph must cover ALL scoped unique outputs, not just the
        # one source file selected by a task-level QA gate.
        received_coding.write_bytes(actual_coding)
        recipient.unlink()
        partial_commit = consumer_commit("Coding QA passes but other output missing")
        partial = gate.qualify(source_candidate, recipient_repo, partial_commit)
        assert partial["consumerGitByteReadbackQualified"] is True
        assert partial["completeOriginalOutputSetReadbackQualified"] is False
        try:
            gate.qualify(
                source_candidate, recipient_repo, partial_commit,
                original_workspace_repo=native_source_worktree,
                original_base_commit=SOURCE,
            )
        except gate.DeliveryGateError as exc:
            assert "omitted" in str(exc), str(exc)
        else:
            raise AssertionError("QA-picked single output wrongly qualified whole native source")
        assert run_handle.workspace_claim.require_held()["state"] == "held"
        print("R33_ACTUAL_NATIVE_SOURCE_GIT_SCOPE_OMITTED_SECOND_BLOB_DENIED=PASS", flush=True)

        recipient.write_bytes(original_bytes)
        consumer_sha = consumer_commit("accepted ALL scoped original Git worktree outputs")
        # This stronger R35 negative must fail *after* QA and all Git source
        # outputs are delivered: NativePG registered artifacts are another
        # independent original output family and cannot silently be dropped.
        assert gate.qualify(
            source_candidate, recipient_repo, consumer_sha,
            original_workspace_repo=native_source_worktree,
            original_base_commit=SOURCE,
        )["completeOriginalOutputSetReadbackQualified"] is True
        original_artifacts = physical.get("artifacts")
        assert isinstance(original_artifacts, list) and original_artifacts, physical
        try:
            gate.qualify(
                source_candidate, recipient_repo, consumer_sha,
                original_workspace_repo=native_source_worktree,
                original_base_commit=SOURCE,
                original_native_job_id=native_job_id,
                original_native_client=ordinary,
            )
        except gate.DeliveryGateError as exc:
            assert "omitted" in str(exc), str(exc)
        else:
            raise AssertionError("complete original Coding Git wrongly covered native Artifacts")
        assert run_handle.workspace_claim.require_held()["state"] == "held"
        print("R35_NATIVE_OS_JOB_ARTIFACTS_OMITTED_GIT_QA_GREEN_CLAIM_HELD=PASS", flush=True)
        for artifact in original_artifacts:
            artifact_id = artifact["artifactId"]
            native_bytes = call(ordinary, "artifact.read", {
                "schemaVersion": 1, "jobId": native_job_id,
                "artifactId": artifact_id, "offset": 0, "maxBytes": 1024 * 1024,
            })
            assert native_bytes["eof"] is True
            actual = native_bytes["content"].encode("utf-8")
            assert native_bytes["nextOffset"] == len(actual)
            assert len(actual) == artifact["retainedBytes"]
            assert native_bytes["digest"] == artifact["digest"]
            assert "sha256:" + hashlib.sha256(actual).hexdigest() == artifact["digest"]
            target = recipient_repo / "artifacts" / artifact_id
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(actual)
        consumer_sha = consumer_commit("accepted original Git and full native PG Artifact set")
        independent = gate.qualify(
            source_candidate, recipient_repo, consumer_sha,
            original_workspace_repo=native_source_worktree,
            original_base_commit=SOURCE,
            original_native_job_id=native_job_id,
            original_native_client=ordinary,
        )
        assert independent["completeOriginalOutputSetReadbackQualified"] is True
        assert independent["nativeJobArtifactSetReadbackQualified"] is True
        assert independent["nativeJobArtifactCount"] == len(original_artifacts)
        print("R35_NATIVE_OS_JOB_COMPLETE_REGISTERED_ARTIFACT_SET_IMMUTABLE_GIT_PASS", flush=True)
        assert set(independent["originalOutputPaths"]) == {
            "feature_flags.py", filename,
        }, independent["originalOutputPaths"]
        assert independent["originalRunFullOutputCoverage"] == "UNKNOWN"
        assert independent["productionFinalizerEligible"] is False
        assert independent["domainQA"] == "passed"
        assert independent["domainQATrials"] == 3
        assert independent["consumerGitByteReadbackQualified"] is True
        assert independent["finalUserDeliveryProven"] is False
        assert independent["userAcknowledgement"] == "UNKNOWN"
        expected_sha = hashlib.sha256(original_bytes).hexdigest()
        acknowledgement = {
            "harnessRunId": value.harness_run_id,
            "runReceiptDigest": final["runReceiptDigest"],
            "accepted": True,
            "sha256": expected_sha,
            "consumerCommit": consumer_sha,
        }
        print("R31_ORIGINAL_CODING_HIDDENQA_AND_DURABLE_GIT_BYTE_READBACK=PASS", flush=True)
        try:
            run_handle.release_workspace_after_delivery(
                recipient_ack=acknowledgement,
                verify_delivered_and_drained=lambda _s, _a: False,
            )
        except HarnessWorkspaceAdmissionUnavailable:
            pass
        else:
            raise AssertionError("incomplete external drain accepted release")
        assert run_handle.workspace_claim.require_held()["state"] == "held"

        def accepted(source_state, ack) -> bool:
            actual = call(ordinary, "workspace.get", {
                "schemaVersion": 1, "workspaceId": workspace_id,
            })
            return bool(
                source_state["sourceStanding"] == "source-settled"
                and actual["activeJobIds"] == []
                and ack["consumerCommit"] == consumer_sha
                and run(["git", "-C", str(recipient_repo), "show",
                         consumer_sha + ":" + filename],
                        stdout=subprocess.PIPE).stdout.encode() == original_bytes
                and run(["git", "-C", str(recipient_repo), "show",
                         consumer_sha + ":feature_flags.py"],
                        stdout=subprocess.PIPE).stdout.encode() == actual_coding
                and hashlib.sha256(original_bytes).hexdigest() == ack["sha256"]
            )

        # The Run-facing production method cannot promote caller-controlled
        # Git+ACK+callback into an independently authorized Domain/OS proof.
        # Even this physically convincing TEST recipient must be refused.
        assert accepted(final, acknowledgement)
        try:
            run_handle.release_workspace_after_delivery(
                recipient_ack=acknowledgement,
                verify_delivered_and_drained=accepted,
            )
        except HarnessWorkspaceAdmissionUnavailable:
            pass
        else:
            raise AssertionError("caller callback incorrectly released original Claim")
        assert run_handle.workspace_claim.require_held()["state"] == "held"
        print("R34_ORIGINAL_RUN_SELF_CERTIFIED_DOMAIN_RELEASE_DENIED=PASS", flush=True)
        # TEST-ONLY simulated trusted-finalizer action. This deliberately
        # bypasses the product gate and proves that the *privileged native raw
        # endpoint itself* has no independent Domain/NoFutureSpawn authority.
        # It MUST NOT be offered to normal production Harness Run callers.
        released = call(dedicated, "workspace.claim.release", {
            "schemaVersion": 1,
            "clientRequestId": run_handle.workspace_claim.request_id,
        })
        assert released["state"] == "released"
        closed = call(ordinary, "workspace.close", {
            "schemaVersion": 1, "workspaceId": workspace_id,
            "force": False, "consumerReleased": True,
            "expectedSourceStateDigest": stable["sourceStateDigest"],
        })
        assert closed["removed"] is True
        assert recipient.read_bytes() == original_bytes
        assert run(["git", "-C", str(recipient_repo), "show",
                    consumer_sha + ":feature_flags.py"],
                   stdout=subprocess.PIPE).stdout.encode() == actual_coding
        for artifact in original_artifacts:
            artifact_id = artifact["artifactId"]
            retained = run(["git", "-C", str(recipient_repo), "show",
                            consumer_sha + ":artifacts/" + artifact_id],
                           stdout=subprocess.PIPE).stdout.encode("utf-8")
            assert len(retained) == artifact["retainedBytes"]
            assert "sha256:" + hashlib.sha256(retained).hexdigest() == artifact["digest"]
        print("R35_POST_WORKSPACE_DELETE_ALL_NATIVE_ARTIFACT_GIT_BLOBS_READABLE=PASS", flush=True)
        # Workspace physical deletion has occurred; verified independent Git
        # source blob remains readable. User completion is STILL UNKNOWN.
        assert independent["finalUserDeliveryProven"] is False
        print("R31_POST_NATIVE_CLOSE_EXTERNAL_CODING_COMMIT_REMAINS_READABLE=PASS", flush=True)
        tombstone = call(dedicated, "workspace.claim.get", {
            "schemaVersion": 1, "clientRequestId": run_handle.workspace_claim.request_id,
        })
        assert tombstone["state"] == "released"
        assert call(ordinary, "job.list", {"clientRequestId": issued_id, "limit": 2})[
            "jobs"
        ][0]["jobId"] == native_job_id
        print("R29_CROSSDB_SCOPED_BYTE_ACK_RELEASED_NATIVE_CLOSED=PASS", flush=True)

        # Independent adverse witness: HTTP credential separation prevents
        # ordinary callers releasing, but cannot certify a privileged caller's
        # decision. This is a disposable NEGATIVE and not a green finalizer.
        unaccepted_workspace = "ws-harness-r29-premature-" + suffix
        call(ordinary, "workspace.open", {
            "schemaVersion": 1, "workspaceId": unaccepted_workspace,
            "sourceRepo": str(source_repo), "sourceRevision": SOURCE,
        })
        unaccepted_contract = contract("r29-premature-" + suffix, tools=True)
        unaccepted_binding = replace(
            execution_binding(unaccepted_contract), workspace_ref=unaccepted_workspace,
        )
        unaccepted_run = HarnessAgentRun.create(
            harness_dsn, "harness", unaccepted_contract, adapter,
            execution_binding=unaccepted_binding, runtime=FakeRuntime(),
            workspace_claim_client=dedicated,
        )
        assert unaccepted_run.status()["status"] == "created"
        premature_state = call(ordinary, "workspace.get", {
            "schemaVersion": 1, "workspaceId": unaccepted_workspace,
        })
        before_error, before_result = ordinary.call_tool("workspace.close", {
            "schemaVersion": 1, "workspaceId": unaccepted_workspace,
            "force": False, "consumerReleased": True,
            "expectedSourceStateDigest": premature_state["sourceStateDigest"],
        })
        assert before_error and before_result.get("error", {}).get("code") == "CONCURRENCY_LIMIT"
        # Raw privileged MCP release *incorrectly* accepts no original Run
        # terminal, no received bytes, and no independent Domain proof.
        premature = call(dedicated, "workspace.claim.release", {
            "schemaVersion": 1,
            "clientRequestId": unaccepted_run.workspace_claim.request_id,
        })
        assert premature["state"] == "released"
        removed = call(ordinary, "workspace.close", {
            "schemaVersion": 1, "workspaceId": unaccepted_workspace,
            "force": False, "consumerReleased": True,
            "expectedSourceStateDigest": premature_state["sourceStateDigest"],
        })
        assert removed["removed"] is True
        assert unaccepted_run.status()["status"] == "created", "PG Run must still be incomplete"
        print("R29_PRIVILEGED_CLAIMONLY_PREACK_EARLY_RELEASE=REAL_PHYSICAL_RED", flush=True)

        # The APPLICATION release helper also relies on an externally supplied
        # verifier callback. A caller that owns the dedicated token and can
        # manufacture its own callback can lie about actual domain acceptance.
        # This is NOT a production entitlement or a completed Domain ACK.
        fake_ack_workspace = "ws-harness-r29-fake-domain-" + suffix
        call(ordinary, "workspace.open", {
            "schemaVersion": 1, "workspaceId": fake_ack_workspace,
            "sourceRepo": str(source_repo), "sourceRevision": SOURCE,
        })
        fake_contract = contract("r29-untrusted-ack-" + suffix, tools=True)
        fake_binding = replace(
            execution_binding(fake_contract), workspace_ref=fake_ack_workspace,
        )
        fake_run = HarnessAgentRun.create(
            harness_dsn, "harness", fake_contract,
            lambda _: ScriptedTurnAdapter((completed("model-call:r29-untrusted-ack"),)),
            execution_binding=fake_binding, runtime=FakeRuntime(),
            workspace_claim_client=dedicated,
        )
        fake_run.run(({"role": "user", "content": "Pretend deliver"},))
        fake_source = fake_run.inspect_finalization_source()
        assert fake_source["sourceStanding"] == "source-settled"
        forged_ack = {
            "harnessRunId": fake_contract.harness_run_id,
            "runReceiptDigest": fake_source["runReceiptDigest"],
            "accepted": True,
        }
        # No recipient ever received bytes for this Run; a fabricated
        # receipt and True callback now MUST NOT reach the native release API.
        try:
            fake_run.release_workspace_after_delivery(
                recipient_ack=forged_ack,
                verify_delivered_and_drained=lambda _source, _ack: True,
            )
        except HarnessWorkspaceAdmissionUnavailable:
            pass
        else:
            raise AssertionError("caller-fabricated ACK released unaccepted source")
        assert fake_run.workspace_claim.require_held()["state"] == "held"
        fake_ws_state = call(ordinary, "workspace.get", {
            "schemaVersion": 1, "workspaceId": fake_ack_workspace,
        })
        denied, refusal = ordinary.call_tool("workspace.close", {
            "schemaVersion": 1, "workspaceId": fake_ack_workspace,
            "force": False, "consumerReleased": True,
            "expectedSourceStateDigest": fake_ws_state["sourceStateDigest"],
        })
        assert denied and refusal.get("error", {}).get("code") == "CONCURRENCY_LIMIT", refusal
        print("R34_FAKE_ACK_TRUE_CALLBACK_CANNOT_RELEASE_NATIVE_CLAIM=PASS", flush=True)
        print("R29_HARNESS_NATIVE_CLAIMONLY_PHYSICAL_CONSUMER=PASS", flush=True)
    finally:
        if runtime_process is not None:
            runtime_process.terminate()
            try:
                runtime_process.wait(timeout=8)
            except subprocess.TimeoutExpired:
                runtime_process.kill()
                runtime_process.wait(timeout=5)
        if pg_started:
            run(["runuser", "-u", "postgres", "--", "pg_ctl", "-D", str(root / "pg"),
                 "-m", "immediate", "-w", "stop"])
        shutil.rmtree(root)
        print("R29_SCRATCH_PG18_TWO_DATABASES_AND_REALM_DESTROYED=YES", flush=True)


if __name__ == "__main__":
    main()
