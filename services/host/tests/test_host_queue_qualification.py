from __future__ import annotations

import os
import subprocess
from pathlib import Path

SCRIPT = Path(__file__).parents[1] / "tools" / "host_queue_verify.sh"


def _invoke(tmp_path: Path, *, dsn: str = "", actions: str = "", runner: str = "", major: str = ""):
    fake = tmp_path / "fake"
    fake.mkdir()
    log = tmp_path / "uv-commands"
    psql = fake / "psql"
    psql.write_text("#!/bin/sh\necho " + major + "\n", encoding="utf-8")
    psql.chmod(0o755)
    uv = fake / "uv"
    uv.write_text(f'#!/bin/sh\nprintf "%s\\n" "$*" >> "{log}"\n', encoding="utf-8")
    uv.chmod(0o755)
    env = dict(os.environ)
    env.pop("ORDIVON_HOST_V2_DSN", None)
    env.update(
        {
            "ORDIVON_HOST_V2_TEST_DSN": dsn,
            "GITHUB_ACTIONS": actions,
            "RUNNER_ENVIRONMENT": runner,
            "PATH": f"{fake}:{os.environ['PATH']}",
        }
    )
    result = subprocess.run(
        ["/bin/bash", str(SCRIPT)],
        cwd=SCRIPT.parents[1],
        env=env,
        capture_output=True,
        text=True,
        timeout=8,
        check=False,
    )
    return result, log.read_text() if log.exists() else ""


def test_queue_no_dsn_fails_without_trusted_runner(tmp_path: Path) -> None:
    result, log = _invoke(tmp_path, actions="", runner="")
    assert result.returncode == 2
    assert "HOST_QUEUE_REQUIRES_TEST_DSN" in result.stderr
    assert log == ""


def test_queue_self_hosted_no_dsn_fails_before_side_effect(tmp_path: Path) -> None:
    result, log = _invoke(tmp_path, actions="true", runner="self-hosted")
    assert result.returncode == 2
    assert "HOST_QUEUE_REQUIRES_TEST_DSN" in result.stderr
    assert log == ""


def test_queue_rejects_wrong_postgres_major_before_migrations(tmp_path: Path) -> None:
    result, log = _invoke(tmp_path, dsn="postgresql://test@example.invalid/db", major="170006")
    assert result.returncode == 4
    assert "HOST_QUEUE_POSTGRES_MAJOR_INVALID" in result.stderr
    assert log == ""


def test_queue_rejects_non_numeric_major(tmp_path: Path) -> None:
    result, log = _invoke(tmp_path, dsn="postgresql://test@example.invalid/db", major="unknown")
    assert result.returncode == 4
    assert "HOST_QUEUE_POSTGRES_MAJOR_INVALID" in result.stderr
    assert log == ""


def test_queue_postgres18_invokes_alembic_and_real_test_suite(tmp_path: Path) -> None:
    result, log = _invoke(tmp_path, dsn="postgresql://test@example.invalid/db", major="180006")
    assert result.returncode == 0, result.stderr
    assert log.splitlines() == [
        "lock --check",
        "sync --locked",
        "run alembic upgrade head",
        "run ruff check .",
        "run python -m pytest",
    ]
