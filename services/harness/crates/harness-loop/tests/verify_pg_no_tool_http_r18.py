#!/usr/bin/env python3
"""R18 run the EXISTING ignored native PG18 no-Tool Rust+HTTP test, offline.

The source-owned Python Harness PostgreSQL Store creates a real no-Tool Run.
A source-owned Rust test independently checks the actual PG CAS/Contract,
performs HTTP to local loopback, then drives NativeAgentLoop. No new PG writer,
Provider router, real model call, Tool execution, production DSN or scheduler.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
import pwd
import random
import shutil
import subprocess
import sys
import tempfile
import time

HARNESS = Path(__file__).resolve().parents[3]
PYTHON = Path(
    "/root/projects/ordivon-harness-private-r1/owner-candidate-r7/services/harness/.venv/bin/python"
)
TARGET = "/var/lib/ordivon/pg-candidate/cache/build/harness-rust-loop"


def checked(args: list[str], *, timeout: int = 100, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=HARNESS, env=env,
                          text=True, capture_output=True, check=False, timeout=timeout)


def as_postgres(args: list[str], *, timeout: int = 100) -> subprocess.CompletedProcess[str]:
    return checked(["/usr/sbin/runuser", "-u", "postgres", "--", *args], timeout=timeout)


def main() -> int:
    # Reuse the same original one-cluster PG18 harness rather than creating
    # a second PostgreSQL/Runner test authority for R20 Provider V4.
    provider_v4 = sys.argv[1:] == ["--provider-v4"]
    if sys.argv[1:] and not provider_v4:
        raise SystemExit("usage: verify_pg_no_tool_http_r18.py [--provider-v4]")
    evidence: dict[str, object] = {
        "kind": "ordivon.harness-r18-pg-no-tool-http-real-consumer",
        "status": "FAIL",
        "realPostgres18": False,
        "sourceOwnedPythonWriter": False,
        "rustVerifiedContractHttpLoop": False,
        "externalProviderCalls": 0,
        "physicalToolCalls": 0,
        "testOnlyJournal": True,
        "isolatedClusterRemoved": False,
        "nativeProviderV4Suite": "NOT_REQUESTED" if not provider_v4 else "FAIL",
        "originalPythonStoreReadback": False,
    }
    tmp = Path(tempfile.mkdtemp(prefix="ordivon-harness-r18-pg18-", dir="/tmp"))
    data, socket = tmp / "data", tmp / "socket"
    data.mkdir(mode=0o700)
    socket.mkdir(mode=0o700)
    postgres_user = pwd.getpwnam("postgres")
    for directory in (tmp, data, socket):
        os.chown(directory, postgres_user.pw_uid, postgres_user.pw_gid)
    port = random.randrange(54500, 59400)
    schema = ("hpg_rust_isolated_a_r20_" if provider_v4 else "hpg_r18_native_") + str(port)
    fixture = tmp / "no-tool-source.json"
    dsn = f"host={socket} port={port} dbname=postgres user=postgres connect_timeout=5"
    started = False
    try:
        if not PYTHON.is_file():
            raise RuntimeError("VERIFIED_PYTHON_ENV_NOT_INSTALLED")
        initialized = as_postgres(
            ["/usr/bin/initdb", "-D", str(data), "-A", "trust", "--no-instructions"],
            timeout=60,
        )
        if initialized.returncode:
            raise RuntimeError(f"initdb failed: {initialized.stderr[-500:]}")
        service = as_postgres(
            ["/usr/bin/pg_ctl", "-D", str(data), "-o",
             f"-F -k {socket} -h '' -p {port}", "-l", str(tmp / "server.log"),
             "-w", "start"], timeout=65,
        )
        if service.returncode:
            raise RuntimeError(f"postgres start failed: {service.stderr[-500:]}")
        started = True
        evidence["realPostgres18"] = True
        env = {
            **os.environ,
            "HARNESS_RUST_TEST_PG_DSN": dsn,
            "HARNESS_RUST_TEST_SCHEMA": schema,
            "HARNESS_RUST_TEST_FIXTURE_PATH": str(fixture),
            "PYTHONPATH": os.pathsep.join((str(HARNESS / "src"), str(HARNESS))),
            "PYTHONDONTWRITEBYTECODE": "1",
            "CARGO_TARGET_DIR": TARGET,
            "CARGO_BUILD_JOBS": "2",
            "CARGO_INCREMENTAL": "0",
        }
        for key in tuple(env):
            if key.endswith("_API_KEY") or key.startswith(("OPENROUTER", "ORDIVON_R10_LIVE_FREE", "HARNESS_R12_REAL_OWNER")):
                del env[key]
        original = r'''
import json, os, socket
from dataclasses import replace
from pathlib import Path
from ordivon_harness.postgres_store import PostgresHarnessStore
from ordivon_harness.core_contracts import HarnessBoundReference
from tests.test_r3_supported_agent_run import contract
contract_obj = replace(
    contract("r18-verified-pg-no-tool", tools=False),
    provider_id="provider:verified-source",
    adapter_id="adapter:verified-source",
    requested_model_id="model:verified-source",
)
with PostgresHarnessStore(
    os.environ["HARNESS_RUST_TEST_PG_DSN"],
    schema=os.environ["HARNESS_RUST_TEST_SCHEMA"],
    initialize=True,
) as store:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as temporary:
        temporary.bind(("127.0.0.1", 0))
        local_port = temporary.getsockname()[1]
    # Original Run Contract sourceRefs binds one immutable Provider target
    # snapshot; the CAS object contains only an opaque credential reference,
    # never a bearer token. No new PostgreSQL Writer or Store exists.
    transport = {
        "schemaVersion": 1,
        "kind": "ordivon.harness-provider-transport-snapshot",
        "providerId": contract_obj.provider_id,
        "adapterId": contract_obj.adapter_id,
        "requestedModelId": contract_obj.requested_model_id,
        "endpoint": f"http://127.0.0.1:{local_port}/v1/chat/completions",
        "credentialRef": "credential:verified-source-r22",
    }
    config_ref = store.put_object(transport, kind="harness-provider-transport-snapshot")
    contract_obj = replace(
        contract_obj,
        source_refs=(*contract_obj.source_refs, HarnessBoundReference(
            ref="provider-config:verified-source-r22",
            kind="harness-provider-transport-snapshot",
            digest=config_ref.digest,
        )),
    )
    admission = store.create_run(contract_obj)
    assert admission.value == "created"
    assert store.load_run(contract_obj.harness_run_id).status.value == "created"
    # Real PG negative: CAS bytes are valid, but the object carries an
    # unrelated Provider identity. Contract/PG digest alone cannot validate
    # the target's semantic Provider ownership.
    foreign = dict(transport, providerId="provider:foreign")
    foreign_ref=store.put_object(foreign,kind="harness-provider-transport-snapshot")
    foreign_run_id="harness-run:test-provider-transport-foreign"
    foreign_contract=replace(
        contract_obj,
        harness_run_id=foreign_run_id,
        caller_run_ref="test-run-provider-transport-foreign",
        source_refs=(*contract_obj.source_refs[:-1],HarnessBoundReference(
            ref="provider-config:foreign-provider-r22",
            kind="harness-provider-transport-snapshot",
            digest=foreign_ref.digest,
        )),
    )
    assert store.create_run(foreign_contract).value=="created"
    assert store.doctor()["healthy"]
Path(os.environ["HARNESS_RUST_TEST_FIXTURE_PATH"]).write_text(
    json.dumps({"no_tool": {"runId": contract_obj.harness_run_id,
                            "providerId": contract_obj.provider_id,
                            "adapterId": contract_obj.adapter_id,
                            "requestedModelId": contract_obj.requested_model_id},
                "config_negative": {"runId": foreign_run_id}}, sort_keys=True),
    encoding="utf-8",
)
print("R18_SOURCE_OWNED_PYTHON_REAL_PG_NO_TOOL_RUN_CREATED")
'''
        p = checked([str(PYTHON), "-B", "-c", original], env=env, timeout=55)
        if p.returncode or "R18_SOURCE_OWNED_PYTHON_REAL_PG_NO_TOOL_RUN_CREATED" not in p.stdout:
            raise RuntimeError("Python original PG creation failed: " + p.stderr[-1100:] + p.stdout[-600:])
        evidence["sourceOwnedPythonWriter"] = True
        r = checked(
            ["/usr/bin/cargo", "test", "--offline", "--locked",
             "--test", "native_pg_no_tool_http", "-p", "ordivon-harness-loop",
             "--", "--ignored", "--nocapture"], env=env, timeout=170,
        )
        evidence["rustTestExitCode"] = r.returncode
        evidence["rustTestTail"] = r.stdout[-1600:]
        if r.returncode or "PG18_VERIFIED_NO_TOOL_REAL_HTTP_RUST_LOOP_PASS" not in r.stdout:
            raise RuntimeError("Rust actual source PG consumer failed: " + r.stdout[-1100:] + r.stderr[-1000:])
        evidence["rustVerifiedContractHttpLoop"] = True
        if provider_v4:
            # All V4 CAS objects are made by the existing real Python
            # Provider source constructors in the same scratch PG Store.
            source_fixture = str(HARNESS / "crates/harness-loop/tests/pg_provider_v4_python_store.py")
            prepared = checked([str(PYTHON), "-B", source_fixture], env=env, timeout=90)
            if prepared.returncode or "PYTHON_PG_REAL_PROVIDER_V4_EVENT_REFERENCES_READY" not in prepared.stdout:
                raise RuntimeError("Original Python V4 fixture failed: " + prepared.stderr[-1200:] + prepared.stdout[-700:])
            evidence["providerV4SourceObjects"] = True
            # The native recovery consumer must use an ACTUAL SQL SELECT-only
            # role; no process-local mock of permissions is permitted.
            reader = "r20_readonly_" + str(port)
            privilege_sql = (
                f"CREATE ROLE {reader} LOGIN; "
                f"GRANT USAGE ON SCHEMA {schema} TO {reader}; "
                f"GRANT SELECT ON ALL TABLES IN SCHEMA {schema} TO {reader}"
            )
            created_role = as_postgres([
                "/usr/bin/psql", "-h", str(socket), "-p", str(port),
                "-d", "postgres", "-v", "ON_ERROR_STOP=1",
                "-c", privilege_sql,
            ], timeout=30)
            if created_role.returncode:
                raise RuntimeError("Read-only test role setup failed: " + created_role.stderr[-900:])
            readonly_dsn = f"host={socket} port={port} dbname=postgres user={reader} connect_timeout=5"
            rust_env = {
                **env,
                "HARNESS_RUST_TEST_PG_WRITER_DSN": dsn,
                "HARNESS_RUST_TEST_PG_DSN": readonly_dsn,
            }
            rust = checked([
                "/usr/bin/cargo", "test", "--offline", "--locked",
                "-p", "ordivon-harness-loop", "--test", "pg_provider_head",
                "--", "--ignored", "--nocapture", "--test-threads=1",
            ], env=rust_env, timeout=250)
            evidence["nativeProviderV4TestTail"] = rust.stdout[-1700:]
            if rust.returncode or "PG18_RUST_WRITER_PYTHON_PROVIDER_V4_UNKNOWN_READBACK_EXACT_PASS" not in rust.stdout or "PG18_NATIVE_RUST_POSITIVE_HTTP_PYTHON_SOURCE_V4_COMPLETED_READBACK_PASS" not in rust.stdout or "PG18_NATIVE_RUST_POSITIVE_HTTP_PRIVACY_REDACTED_COMPLETED_PASS" not in rust.stdout or "PG18_REJECTED_COMPLETED_EVENT_NO_PRIVATE_CAS_ORPHAN_PASS" not in rust.stdout or "PG18_SOURCE_PROVIDER_DISPATCH_BUDGET_GATE_PASS" not in rust.stdout or "PG18_SOURCE_MODEL_PRIVACY_FENCE_UNTRUSTED_WRITER_PASS" not in rust.stdout or "PG18_SOURCE_PROVIDER_V4_COMPLETED_FORGERY_REJECTED_PASS" not in rust.stdout or "PG18_PROVIDER_COMPLETED_DIFFERENT_ATTEMPT_IDENTITY_DENIED_PASS" not in rust.stdout or "PG18_PROVIDER_COMPLETED_CURRENT_PREDECESSOR_FENCE_PASS" not in rust.stdout or "PG18_PYTHON_PROVIDER_V4_VERIFIED_CAS_RECOVERY_PASS" not in rust.stdout:
                raise RuntimeError("Native Rust PG V4 source consumer failed: " + rust.stdout[-1500:] + rust.stderr[-1250:])
            evidence["nativeProviderV4Suite"] = "PASS"
            # Independently reopen via the original Python Store after the
            # Rust Writer's true PG transaction and connection loss.
            python_verify = checked([str(PYTHON), "-B", source_fixture, "verify-native"], env=env, timeout=60)
            if python_verify.returncode or "PYTHON_VALIDATED_RUST_NATIVE_PROVIDER_UNKNOWN_COMPLETED_AND_REDACTED_JOURNALS_PASS" not in python_verify.stdout:
                raise RuntimeError("Python original PG readback failed: " + python_verify.stderr[-1000:])
            evidence["originalPythonStoreReadback"] = True
        evidence["status"] = "PASS"
    except (RuntimeError, OSError, subprocess.TimeoutExpired, AssertionError) as exc:
        evidence["error"] = f"{type(exc).__name__}: {exc}"[:1500]
    finally:
        if started:
            stopped = as_postgres(
                ["/usr/bin/pg_ctl", "-D", str(data), "-m", "immediate", "-w", "stop"],
                timeout=55,
            )
            evidence["postgresStopped"] = stopped.returncode == 0
        else:
            evidence["postgresStopped"] = True
        shutil.rmtree(tmp, ignore_errors=True)
        evidence["isolatedClusterRemoved"] = not tmp.exists()
        if not evidence["isolatedClusterRemoved"] or not evidence["postgresStopped"]:
            evidence["status"] = "FAIL"
    print(json.dumps(evidence, sort_keys=True, ensure_ascii=False))
    return 0 if evidence["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
