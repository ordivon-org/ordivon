#!/usr/bin/env python3
"""One disposable, non-production PostgreSQL fixture for the existing PG18 owner task.

Effect boundary: /var/tmp scratch cluster and existing native Rust owner tests only.
Never reads an operator database DSN and never starts a TCP listener.
"""

from __future__ import annotations

import os
import re
import shutil
import socket
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
# Same Cargo owner invocation as test:postgres-registry:physical; avoid recursively
# invoking mise (nested mise inherits Runtime's ephemeral FD-backed paths).
CARGO_ARGS = (
    "test",
    "--locked",
    "-p",
    "ordivon-runtime-core",
    "--no-default-features",
    "--features",
    "postgres-registry-admission",
    "pg18_",
    "--",
    "--ignored",
    "--nocapture",
    "--test-threads=1",
)
EXPECTED_PG18 = 18
PG18_CASE = re.compile(r"^test pg_admission::live_pg_tests::pg18_[^ ]+ \.\.\. ok$", re.M)
PG18_RESULT = re.compile(r"test result: ok\. (\d+) passed; 0 failed; 0 ignored;")


def fixture_environment(original: dict[str, str], socket_dir: Path, port: int) -> dict[str, str]:
    """Override even an inherited production DSN; never propagate stage authority."""
    result = dict(original)
    result["ORDIVON_PG_TEST_DSN"] = f"host={socket_dir} port={port} user=postgres dbname=postgres"
    result.pop("ORDIVON_PG_STAGE_TEST_DSN", None)
    # Runtime passes an FD-backed Cargo cache to the native tool invocation.
    # Python's subprocess closes unrelated FDs; resolve only this compiler
    # cache to the *same* actual directory before spawning a child Cargo.
    cargo_dir = result.get("CARGO_TARGET_DIR", "")
    if cargo_dir.startswith("/proc/self/fd/"):
        actual = Path(cargo_dir).resolve(strict=True)
        if not actual.is_dir():
            raise RuntimeError("FD-backed Cargo target is not an existing directory")
        result["CARGO_TARGET_DIR"] = str(actual)
    return result


def exact_test_count(output: str) -> int:
    """Require actual physical PG18 executions, not a green zero-test command."""
    observed = len(PG18_CASE.findall(output))
    results = [int(n) for n in PG18_RESULT.findall(output)]
    if observed != EXPECTED_PG18 or EXPECTED_PG18 not in results:
        raise ValueError(f"physical PG18 result unqualified: observed={observed}, summaries={results}")
    return observed


def run_checked(command: list[str], *, timeout: int = 90) -> None:
    process = subprocess.run(command, capture_output=True, text=True, timeout=timeout)
    if process.returncode != 0:
        raise RuntimeError(
            f"disposable PostgreSQL fixture command failed ({command[0]},"
            f" exit={process.returncode}): {process.stderr[-1500:]}"
        )


def main() -> int:
    if sys.platform != "linux":
        raise RuntimeError("disposable PG18 fixture supports Linux only")
    initdb = shutil.which("initdb")
    pg_ctl = shutil.which("pg_ctl")
    cargo = shutil.which("cargo")
    if not all((initdb, pg_ctl, cargo)):
        raise RuntimeError("initdb, pg_ctl and cargo must be installed")
    prefix: list[str] = []
    with tempfile.TemporaryDirectory(prefix="ordivon-pg18-", dir="/var/tmp") as raw:
        root = Path(raw)
        if os.geteuid() == 0:
            import pwd

            account = pwd.getpwnam("nobody")
            os.chown(root, account.pw_uid, account.pw_gid)
            runuser = shutil.which("runuser")
            if not runuser:
                raise RuntimeError("root cannot start PostgreSQL without runuser")
            prefix = [runuser, "-u", "nobody", "--"]
        data_dir = root / "data"
        with socket.socket() as sock:
            sock.bind(("127.0.0.1", 0))
            port = sock.getsockname()[1]
        started = False
        try:
            run_checked(
                prefix
                + [
                    initdb,
                    "-D",
                    str(data_dir),
                    "-A",
                    "trust",
                    "-U",
                    "postgres",
                    "--no-locale",
                    "--encoding=UTF8",
                ],
                timeout=90,
            )
            run_checked(
                prefix
                + [
                    pg_ctl,
                    "-D",
                    str(data_dir),
                    "-o",
                    f"-k {root} -h '' -p {port} -c fsync=off",
                    "-l",
                    str(root / "postgres.log"),
                    "-w",
                    "start",
                ],
                timeout=60,
            )
            started = True
            source = subprocess.check_output(["git", "-C", str(ROOT), "rev-parse", "HEAD"], text=True).strip()
            dirty = bool(subprocess.check_output(["git", "-C", str(ROOT), "status", "--porcelain"], text=True).strip())
            print(f"sourceCut={source} standing={'DIRTY_UNQUALIFIED' if dirty else 'CLEAN'}")
            result = subprocess.run(
                [cargo, *CARGO_ARGS],
                cwd=ROOT,
                env=fixture_environment(os.environ, root, port),
                capture_output=True,
                text=True,
                timeout=400,
            )
            output = result.stdout + "\n" + result.stderr
            for line in output.splitlines():
                if "pg_admission::live_pg_tests::pg18_" in line or (
                    line.startswith("test result:") and "passed" in line
                ):
                    print(line[:230])
            if result.returncode:
                raise RuntimeError(f"PG18 native owner task failed: {output[-3500:]}")
            n = exact_test_count(output)
            print(f"DISPOSABLE_PG18_PASS={n}/{EXPECTED_PG18}")
        finally:
            if started:
                run_checked(
                    prefix + [pg_ctl, "-D", str(data_dir), "-m", "immediate", "-w", "stop"],
                    timeout=45,
                )
    print("DISPOSABLE_POSTGRESQL_STOPPED_AND_REMOVED=1")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (RuntimeError, OSError, ValueError, subprocess.TimeoutExpired) as exc:
        print(f"DISPOSABLE_PG18_UNQUALIFIED: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
