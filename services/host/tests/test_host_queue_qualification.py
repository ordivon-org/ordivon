from __future__ import annotations

import os
import subprocess
from pathlib import Path

SCRIPT = Path(__file__).parents[1] / "tools" / "host_queue_verify.sh"


def _invoke(
    tmp_path: Path,
    *,
    dsn: str = "",
    actions: str = "",
    runner: str = "",
    major: str = "",
    connect_failures: int = 0,
    fixture_mode: str = "complete",
):
    fake = tmp_path / "fake"
    fake.mkdir()
    log = tmp_path / "uv-commands"
    psql = fake / "psql"
    attempts = tmp_path / "psql-attempts"
    psql.write_text(
        "#!/bin/sh\n"
        f'count=0; [ ! -f "{attempts}" ] || count="$(cat "{attempts}")"\n'
        "count=$((count + 1))\n"
        f'printf "%s\\n" "$count" > "{attempts}"\n'
        f'if [ "$count" -le "{connect_failures}" ]; then exit 1; fi\n'
        'if [ "$5" = "SHOW server_version_num" ]; then\n'
        f"  echo {major}\n"
        "else\n"
        '  case "$3" in\n'
        f'    */db) echo "{major}:123456:1";;\n'
        f'    */alias) echo "{major}:123456:1";;\n'
        '    */wrong-major) echo "170006:123456:99";;\n'
        "    */unobservable) exit 1;;\n"
        f'    */fixture*) echo "{major}:123456:${{3##*fixture}}";;\n'
        "    *) exit 1;;\n"
        "  esac\nfi\n",
        encoding="utf-8",
    )
    psql.chmod(0o755)
    uv = fake / "uv"
    uv.write_text(
        f'#!/bin/sh\nprintf "%s\\n" "$*" >> "{log}"\n'
        'if [ "$*" = "run python -m pytest --host-require-complete-suite --strict-config --strict-markers" ]; then\n'
        '  test -z "${PYTEST_ADDOPTS+x}" || exit 9\nfi\n',
        encoding="utf-8",
    )
    uv.chmod(0o755)
    env = dict(os.environ)
    env.pop("ORDIVON_HOST_V2_DSN", None)
    env["PYTEST_ADDOPTS"] = "--collect-only -k nonexistent"
    env.update(
        {
            "ORDIVON_HOST_V2_TEST_DSN": dsn,
            "GITHUB_ACTIONS": actions,
            "RUNNER_ENVIRONMENT": runner,
            "PATH": f"{fake}:{os.environ['PATH']}",
        }
    )
    fixtures = (
        "BOUNDARY_MESSAGE",
        "BOUNDARY_CHANGE",
        "RECEIPT_TEST",
        "MIGRATION_CLOCK",
        "MIGRATION_HISTORY",
        "MIGRATION_ALLOCATOR",
        "MIGRATION_LOCK",
        "MIGRATION_STARTUP",
        "MIGRATION_CJK",
    )
    for i, fixture in enumerate(fixtures, start=2):
        env[f"ORDIVON_HOST_V2_{fixture}_DSN"] = f"postgresql://test@example.invalid/fixture{i}"
    if fixture_mode != "complete":
        key = "ORDIVON_HOST_V2_RECEIPT_TEST_DSN"
        if fixture_mode == "missing":
            env.pop(key)
        else:
            env[key] = f"postgresql://test@example.invalid/{fixture_mode}"
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


def test_queue_retries_transient_postgres_connection_before_migrations(tmp_path: Path) -> None:
    result, log = _invoke(
        tmp_path,
        dsn="postgresql://test@example.invalid/db",
        major="180006",
        connect_failures=2,
    )
    assert result.returncode == 0, result.stderr
    assert log.splitlines() == [
        "lock --check",
        "sync --locked",
        "run alembic upgrade head",
        "run ruff check .",
        "run python -m pytest --host-require-complete-suite --strict-config --strict-markers",
    ]


def test_queue_exhausts_transient_connection_retries_before_migrations(tmp_path: Path) -> None:
    result, log = _invoke(
        tmp_path,
        dsn="postgresql://test@example.invalid/db",
        major="180006",
        connect_failures=99,
    )
    assert result.returncode == 4
    assert "HOST_QUEUE_TEST_DB_CONNECTION_FAILED" in result.stderr
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
        "run python -m pytest --host-require-complete-suite --strict-config --strict-markers",
    ]


def test_queue_missing_native_fixture_fails_before_migrations(tmp_path: Path) -> None:
    result, log = _invoke(
        tmp_path, dsn="postgresql://test@example.invalid/db", major="180006", fixture_mode="missing"
    )
    assert result.returncode == 4
    assert "HOST_QUEUE_FIXTURE_MISSING: ORDIVON_HOST_V2_RECEIPT_TEST_DSN" in result.stderr
    assert log == ""


def test_queue_native_alias_fails_before_migrations(tmp_path: Path) -> None:
    result, log = _invoke(
        tmp_path, dsn="postgresql://test@example.invalid/db", major="180006", fixture_mode="alias"
    )
    assert result.returncode == 4
    assert "HOST_QUEUE_FIXTURE_ALIAS" in result.stderr
    assert log == ""


def test_queue_unobservable_native_identity_fails_before_migrations(tmp_path: Path) -> None:
    result, log = _invoke(
        tmp_path,
        dsn="postgresql://test@example.invalid/db",
        major="180006",
        fixture_mode="unobservable",
    )
    assert result.returncode == 4
    assert "HOST_QUEUE_FIXTURE_IDENTITY_UNOBSERVABLE" in result.stderr
    assert log == ""


def test_queue_other_fixture_major_fails_before_migrations(tmp_path: Path) -> None:
    result, log = _invoke(
        tmp_path,
        dsn="postgresql://test@example.invalid/db",
        major="180006",
        fixture_mode="wrong-major",
    )
    assert result.returncode == 4
    assert "HOST_QUEUE_FIXTURE_MAJOR_MISMATCH" in result.stderr
    assert log == ""
