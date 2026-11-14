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
    }
    tmp = Path(tempfile.mkdtemp(prefix="ordivon-harness-r18-pg18-", dir="/tmp"))
    data, socket = tmp / "data", tmp / "socket"
    data.mkdir(mode=0o700)
    socket.mkdir(mode=0o700)
    postgres_user = pwd.getpwnam("postgres")
    for directory in (tmp, data, socket):
        os.chown(directory, postgres_user.pw_uid, postgres_user.pw_gid)
    port = random.randrange(54500, 59400)
    schema = "hpg_r18_native_" + str(port)
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
import json, os
from dataclasses import replace
from pathlib import Path
from ordivon_harness.postgres_store import PostgresHarnessStore
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
    admission = store.create_run(contract_obj)
    assert admission.value == "created"
    assert store.load_run(contract_obj.harness_run_id).status.value == "created"
    assert store.doctor()["healthy"]
Path(os.environ["HARNESS_RUST_TEST_FIXTURE_PATH"]).write_text(
    json.dumps({"no_tool": {"runId": contract_obj.harness_run_id}}, sort_keys=True),
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
