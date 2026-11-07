"""Native disposable PostgreSQL for optional worker consumer tests only."""

import errno
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

import psycopg
import pytest


@pytest.fixture(scope="session")
def worker_pg_cluster():
    for executable in ("initdb", "pg_ctl"):
        if shutil.which(executable) is None:
            pytest.skip(f"ENV_BLOCKED: worker PostgreSQL integration needs {executable}")
    root = Path(tempfile.mkdtemp(prefix="gateway-worker-pg-", dir="/tmp"))
    root.chmod(0o777)

    def unprivileged():
        if os.geteuid() == 0:
            os.setgid(65534)
            os.setuid(65534)

    def run(*args):
        subprocess.run(
            args,
            check=True,
            capture_output=True,
            text=True,
            timeout=35,
            preexec_fn=unprivileged,
        )

    # PostgreSQL refuses root. Restricted containers may disallow setuid.
    if os.geteuid() == 0:
        try:
            subprocess.run(["true"], user=65534, group=65534, check=True)
        except OSError as exc:
            if exc.errno not in (errno.EPERM, errno.EACCES, errno.EINVAL, errno.ENOSYS):
                raise
            shutil.rmtree(root)
            pytest.skip(
                "ENV_BLOCKED: disposable PostgreSQL requires unprivileged process execution"
            )
    started = False
    try:
        run(
            "initdb",
            "-D",
            str(root / "data"),
            "-U",
            "postgres",
            "-A",
            "trust",
            "--no-locale",
            "-E",
            "UTF8",
        )
        run(
            "pg_ctl",
            "-D",
            str(root / "data"),
            "-l",
            str(root / "server.log"),
            "-o",
            f"-k {root} -c listen_addresses='' -c unix_socket_permissions=0700",
            "-w",
            "start",
        )
        started = True
        yield f"host={root} dbname=postgres user=postgres password='' sslmode=disable"
    finally:
        if started:
            run("pg_ctl", "-D", str(root / "data"), "-m", "immediate", "-w", "stop")
        shutil.rmtree(root)


@pytest.fixture
def pg_dsn(worker_pg_cluster):
    # This DSN is generated here; never use a caller's existing database.
    with psycopg.connect(worker_pg_cluster) as db:
        db.execute("DROP SCHEMA IF EXISTS gateway_external_worker_epoch1 CASCADE")
    return worker_pg_cluster
