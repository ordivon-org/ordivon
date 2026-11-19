#!/usr/bin/env python3
"""Disposable PG18 physical Rust/Git contract test. Never touches installed DB.

Starts a private local Unix-socket PostgreSQL as the existing postgres OS user,
executes the ignored native Rust Workspace claim interleaving test, and shuts it
down. All temporary tables, roles, Workspaces, and Git repos are self-owned.
"""
from __future__ import annotations

import os
from pathlib import Path
import pwd
import shutil
import socket
import subprocess
import sys
import tempfile


def command(args: list[str], *, env: dict[str, str] | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(args, check=True, env=env, text=True)


def as_postgres(args: list[str]) -> subprocess.CompletedProcess:
    return command(["/usr/bin/runuser", "-u", "postgres", "--", *args])


def main() -> int:
    pg_init = shutil.which("initdb")
    pg_ctl = shutil.which("pg_ctl")
    if not pg_init or not pg_ctl:
        raise RuntimeError("PostgreSQL initdb/pg_ctl required; no installed database used")
    version = subprocess.check_output([pg_init, "--version"], text=True).strip()
    if not version.startswith("initdb (PostgreSQL) 18."):
        raise RuntimeError(f"Require disposable PG18 rather than unqualified version: {version}")
    postgres_user = pwd.getpwnam("postgres")
    root = Path(tempfile.mkdtemp(prefix="ordivon-workspace-claim-pg18-"))
    data, sock = root / "data", root / "sock"
    os.chown(root, postgres_user.pw_uid, postgres_user.pw_gid)
    sock.mkdir(mode=0o700)
    os.chown(sock, postgres_user.pw_uid, postgres_user.pw_gid)
    started = False
    try:
        as_postgres([
            pg_init, "-D", str(data), "--no-instructions",
            "--auth-local=trust", "--auth-host=trust", "--encoding=UTF8", "--locale=C",
        ])
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(("127.0.0.1", 0))
            port = s.getsockname()[1]
        as_postgres([
            pg_ctl, "-D", str(data), "-l", str(root / "postgres.log"),
            "-o", f"-c listen_addresses='' -c unix_socket_directories={sock} -p {port}",
            "-w", "start",
        ])
        started = True
        dsn = f"host={sock} port={port} dbname=postgres user=postgres"
        # A second ephemeral Database is deliberately NOT a shared PG
        # advisory lock domain. This first-party negative control must stay RED
        # for a design relying on the same numeric key across databases.
        try:
            import psycopg
        except ImportError:
            raise RuntimeError("psycopg is required by the existing PG Runtime tooling")
        with psycopg.connect(dsn, autocommit=True) as admin:
            admin.execute("CREATE DATABASE separate_harness_fixture")
        with psycopg.connect(dsn, autocommit=True) as pg:
            pg.execute("CREATE SCHEMA disposable_upgrade_fixture")
            pg.execute("SET search_path TO disposable_upgrade_fixture")
            sql = Path("services/runtime/crates/ordivon-runtime-core/sql/pg_workspace_claim_r1.sql").read_text()
            pg.execute(sql)
            cols = pg.execute(
                "SELECT attname FROM pg_attribute WHERE attrelid='workspace_consumer_claims'::regclass "
                "AND attnum>0 AND NOT attisdropped"
            ).fetchall()
            assert "store_root" in {row[0] for row in cols}
            pg.execute("SET search_path TO public")
            pg.execute("DROP SCHEMA disposable_upgrade_fixture CASCADE")
        print("PG18_ADDITIVE_OPERATOR_MIGRATION_PASS", flush=True)
        with psycopg.connect(dsn) as runtime, psycopg.connect(
            f"host={sock} port={port} dbname=separate_harness_fixture user=postgres"
        ) as harness:
            key = 7812345678901234567
            runtime_lock = runtime.execute("SELECT pg_try_advisory_xact_lock(%s)", (key,)).fetchone()[0]
            harness_lock = harness.execute("SELECT pg_try_advisory_xact_lock(%s)", (key,)).fetchone()[0]
            assert runtime_lock and harness_lock, "two DBs must NOT be treated as one PG lock domain"
            runtime.rollback()
            harness.rollback()
        print("PG18_TWO_DATABASE_LOCK_NEGATIVE_CONTROL_PASS", flush=True)
        env = dict(os.environ)
        env["ORDIVON_PG_TEST_DSN"] = dsn
        env["RUST_BACKTRACE"] = "1"
        env.pop("PGPASSWORD", None)
        command([
            "cargo", "test", "--manifest-path", "services/runtime/Cargo.toml",
            "-p", "ordivon-runtime-core", "--no-default-features",
            "--features", "postgres-registry-admission",
            "--lib", "claim_physical_pg_tests::runtime_owned_pin_prevents_close_and_rejects_postclose_birth",
            "--", "--ignored", "--nocapture",
        ], env=env)
        print("RUNTIME_NATIVE_PG18_GIT_CLAIM_PHYSICAL_PASS", flush=True)
        return 0
    finally:
        if started:
            try:
                as_postgres([pg_ctl, "-D", str(data), "-m", "immediate", "-w", "stop"])
            except Exception as error:
                print(f"WARNING disposable PostgreSQL shutdown uncertain: {error}", file=sys.stderr)
        shutil.rmtree(root, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())
