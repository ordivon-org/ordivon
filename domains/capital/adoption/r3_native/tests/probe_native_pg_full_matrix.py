"""Explicit TEST-ONLY Windows PG18 native Finance consumer cross-ABI matrix.

Single process owns the life cycle of a *fresh disposable* localhost PG18
cluster and invokes the two pre-existing mature Python environments:
  Python 3.15 NautilusTrader + psycopg3.3.6  -> PostgreSQL PaperClose
  Python 3.11 Riskfolio/SciPy + psycopg3.3.6 -> committed Risk/Portfolio readback
No production PostgreSQL service, broker, fund movement or Python ABI mixing.
"""
from __future__ import annotations

import os
import socket
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve()
ROOT = HERE.parents[1]
PG_ROOT = Path(os.environ["ORDIVON_FINANCE_R3_PG_SANDBOX_ROOT"]).resolve()
PG_BIN = Path(os.environ["ORDIVON_FINANCE_R3_PG18_BIN"]).resolve()
NATIVE = Path(os.environ["ORDIVON_FINANCE_R3_NATIVE_PY"]).resolve()
RISK = Path(os.environ["ORDIVON_FINANCE_R3_RISK_PY"]).resolve()
ORIGINAL_DATA = Path(os.environ["ORDIVON_FINANCE_R3_SPY_CSV"]).resolve()
CLUSTER = PG_ROOT / "cluster"
PG_ARGS = ["-h", "127.0.0.1", "-p", "55491", "-U", "sandbox_finance_r3"]
DSN = "host=127.0.0.1 port=55491 dbname=ordivon_paper user=sandbox_finance_r3 connect_timeout=3"

sandbox_marker = PG_ROOT / ".finance-r3-disposable-pg18"
if not sandbox_marker.is_file() or sandbox_marker.read_text(encoding="utf-8").strip() != "ORDIVON_FINANCE_R3_DISPOSABLE_TEST_ONLY":
    raise RuntimeError("explicit disposable Finance R3 PostgreSQL test root marker required")
assert PG_ROOT.is_dir() and ORIGINAL_DATA.is_file()
assert all(x.is_file() for x in (
    NATIVE, RISK, PG_BIN / "pg_ctl.exe", PG_BIN / "initdb.exe",
    PG_BIN / "createdb.exe", PG_BIN / "dropdb.exe", PG_BIN / "psql.exe",
))
assert (PG_ROOT / "pyclient315" / "site" / "psycopg").is_dir()
assert (PG_ROOT / "pyclient" / "psycopg").is_dir()

def call(*args: str, env: dict[str, str] | None = None) -> None:
    cmd = [str(x) for x in args]
    result = subprocess.run(cmd, env=env, check=False)
    if result.returncode:
        raise RuntimeError(
            f"TEST-ONLY native process failed (exit={result.returncode}, exe={Path(cmd[0]).name})"
        )


def probe_stdout(*args: str) -> str:
    return subprocess.check_output(
        list(map(str, args)), text=True,
    ).strip()


def pg_run() -> None:
    # The service has NO relationship to either running Ordivon PostgreSQL
    # service; reject any already-bound port even if a known service appears.
    with socket.socket() as sk:
        sk.settimeout(0.5)
        if sk.connect_ex(("127.0.0.1", 55491)) == 0:
            raise RuntimeError("test port already bound; refuse to contact unknown cluster")
    if not (CLUSTER / "PG_VERSION").exists():
        call(
            PG_BIN / "initdb.exe", "-D", CLUSTER, "-A", "trust",
            "-U", "sandbox_finance_r3", "--no-instructions",
            "--encoding=UTF8", "--locale=C",
        )
    if (CLUSTER / "PG_VERSION").read_text().strip() != "18":
        raise RuntimeError("refusing non-PG18 cluster")
    common = os.environ.copy()
    common.update({
        "ORDIVON_FINANCE_R3_SANDBOX_PG_DATA": str(CLUSTER),
        "ORDIVON_FINANCE_R3_SANDBOX_PG_DSN": DSN,
        "ORDIVON_FINANCE_R3_SOURCE_MANIFEST": str(ROOT / "native_study_result.evidence.json"),
        "ORDIVON_FINANCE_R3_SPY_CSV": str(ORIGINAL_DATA),
        "PYTHONDONTWRITEBYTECODE": "1",
    })
    native_env = dict(common, PYTHONPATH=str(PG_ROOT / "pyclient315" / "site"))
    risk_env = dict(common, PYTHONPATH=str(PG_ROOT / "pyclient"))
    running = False
    try:
        def boot() -> None:
            nonlocal running
            call(
                PG_BIN / "pg_ctl.exe", "-D", CLUSTER, "-l", PG_ROOT / "postgresql.log",
                "-o", "-h 127.0.0.1 -p 55491 -c max_connections=20 -c shared_buffers=16MB",
                "-w", "start",
            )
            running = True
            observed = probe_stdout(
                PG_BIN / "psql.exe", "-X", "-A", "-t", *PG_ARGS,
                "-d", "postgres", "-c", "select current_setting('data_directory')",
            )
            if Path(observed).resolve() != CLUSTER.resolve():
                raise RuntimeError("PostgreSQL data-directory mismatch - no database mutation")

        def halt() -> None:
            nonlocal running
            call(PG_BIN / "pg_ctl.exe", "-D", CLUSTER, "-m", "fast", "-w", "stop")
            running = False

        boot()
        # The database is intentionally test-only and disposable. The exact
        # fresh cluster path above was verified before these commands.
        call(PG_BIN / "dropdb.exe", "--if-exists", *PG_ARGS, "ordivon_paper")
        call(PG_BIN / "createdb.exe", *PG_ARGS, "ordivon_paper")
        call(
            NATIVE, ROOT / "tests/probe_native_pg_paper_close.py", "write",
            env=native_env,
        )
        call(
            RISK, ROOT / "tests/probe_pg_risk_portfolio_readback.py",
            env=risk_env,
        )
        halt()
        print("R3_NATIVE_PG18_DURABILITY_STOP_COMPLETE", flush=True)
        boot()
        call(
            NATIVE, ROOT / "tests/probe_native_pg_paper_close.py", "verify-restart",
            env=native_env,
        )
        print("R3_NATIVE_PG_RISK_PORTFOLIO_RESTARTED_MATRIX_PASS", flush=True)
    finally:
        if running:
            halt()
        print("R3_EPHEMERAL_POSTGRESQL_SERVICE_STOPPED", flush=True)


if __name__ == "__main__":
    pg_run()
