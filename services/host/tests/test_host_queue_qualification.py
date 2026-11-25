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
    args: tuple[str, ...] = (),
    disposable: str = "",
    image_id: str = "sha256:" + "a" * 64,
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
    docker_log = tmp_path / "docker-commands"
    docker = fake / "docker"
    docker.write_text(
        "#!/bin/sh\n"
        f'printf "%s\\n" "$*" >> "{docker_log}"\n'
        'case "$1" in\n'
        "  run) echo fixture-container;;\n"
        f"  inspect) echo {image_id};;\n"
        "  port) echo 127.0.0.1:54321;;\n"
        "esac\n",
        encoding="utf-8",
    )
    docker.chmod(0o755)
    env = dict(os.environ)
    env.pop("ORDIVON_HOST_V2_DSN", None)
    env["PYTEST_ADDOPTS"] = "--collect-only -k nonexistent"
    env.update(
        {
            "ORDIVON_HOST_V2_TEST_DSN": dsn,
            "GITHUB_ACTIONS": actions,
            "ORDIVON_HOST_QUEUE_LOCAL_DISPOSABLE": disposable,
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
        ["/bin/bash", str(SCRIPT), *args],
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


def test_queue_rejects_pg19_without_explicit_local_disposable(tmp_path: Path) -> None:
    result, log = _invoke(tmp_path, args=("--postgres-major=19",))
    assert result.returncode == 2
    assert "HOST_QUEUE_PG19_REQUIRES_LOCAL_DISPOSABLE" in result.stderr
    assert log == ""
    assert not (tmp_path / "docker-commands").exists()


def test_queue_rejects_pg19_with_caller_dsn(tmp_path: Path) -> None:
    result, log = _invoke(
        tmp_path,
        args=("--postgres-major=19",),
        disposable="1",
        dsn="postgresql://test@example.invalid/db",
        major="190000",
    )
    assert result.returncode == 2
    assert "HOST_QUEUE_PG19_REQUIRES_LOCAL_DISPOSABLE" in result.stderr
    assert log == ""
    assert not (tmp_path / "docker-commands").exists()


def test_queue_rejects_pg19_in_ci(tmp_path: Path) -> None:
    result, log = _invoke(
        tmp_path,
        args=("--postgres-major=19",),
        disposable="1",
        actions="true",
        runner="github-hosted",
        major="190000",
    )
    assert result.returncode == 2
    assert "HOST_QUEUE_PG19_REQUIRES_LOCAL_DISPOSABLE" in result.stderr
    assert log == ""
    assert not (tmp_path / "docker-commands").exists()


def test_queue_rejects_unsupported_major_argument(tmp_path: Path) -> None:
    result, log = _invoke(tmp_path, args=("--postgres-major=20",), disposable="1")
    assert result.returncode == 2
    assert "HOST_QUEUE_INVALID_ARGUMENT" in result.stderr
    assert log == ""
    assert not (tmp_path / "docker-commands").exists()


def test_queue_pg19_local_launch_validates_major_and_isolates_fixtures(tmp_path: Path) -> None:
    result, log = _invoke(tmp_path, args=("--postgres-major=19",), disposable="1", major="190000")
    assert result.returncode == 0, result.stderr
    docker = (tmp_path / "docker-commands").read_text().splitlines()
    assert docker[0].endswith(" postgres:19")
    assert "inspect --format {{.Image}} fixture-container" in docker
    assert len([line for line in docker if " createdb " in line]) == 9
    assert docker[-1] == "rm -f fixture-container"
    assert log.splitlines().count("run alembic upgrade head") == 4
    assert log.splitlines().count("run alembic upgrade 0014") == 4
    assert "run alembic upgrade 0016" in log
    assert "run alembic upgrade 0015" in log
    assert (
        log.splitlines()[-1]
        == "run python -m pytest --host-require-complete-suite --strict-config --strict-markers"
    )
    assert "host_queue_postgres_major=19" in result.stdout
    assert "host_queue_image=sha256:" + "a" * 64 in result.stdout


def test_queue_pg19_rejects_wrong_observed_major_and_cleans_container(tmp_path: Path) -> None:
    result, log = _invoke(tmp_path, args=("--postgres-major=19",), disposable="1", major="180007")
    assert result.returncode == 4
    assert "HOST_QUEUE_POSTGRES_MAJOR_INVALID: expected 19" in result.stderr
    assert log == ""
    assert (tmp_path / "docker-commands").read_text().splitlines()[-1] == "rm -f fixture-container"


def test_queue_rejects_missing_image_identity_before_migration(tmp_path: Path) -> None:
    result, log = _invoke(
        tmp_path, args=("--postgres-major=19",), disposable="1", major="190000", image_id="unknown"
    )
    assert result.returncode == 4
    assert "HOST_QUEUE_IMAGE_ID_INVALID" in result.stderr
    assert log == ""
    assert (tmp_path / "docker-commands").read_text().splitlines()[-1] == "rm -f fixture-container"


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
