from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INSTALL = ROOT / "packaging" / "install_release.sh"


def _run(
    *args: str, cwd: Path | None = None, env: dict[str, str] | None = None
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        args,
        cwd=cwd,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )


def _git(repo: Path, *args: str) -> str:
    result = _run("git", *args, cwd=repo)
    assert result.returncode == 0, result.stderr
    return result.stdout.strip()


def _fake_uv(path: Path) -> None:
    path.write_text(
        """#!/bin/sh
set -eu
if [ -n "${ORDIVON_TEST_UV_CALL_LOG:-}" ]; then
  printf '%s\n' "$*" >> "$ORDIVON_TEST_UV_CALL_LOG"
fi
if [ "$1" = "python" ] && [ "$2" = "install" ]; then
  exit 0
fi
if [ "$1" = "python" ] && [ "$2" = "find" ]; then
  printf '%s\\n' /usr/bin/python3
  exit 0
fi
if [ "$1" = "sync" ]; then
  exit 0
fi
printf 'unexpected uv args: %s\\n' "$*" >&2
exit 64
""",
        encoding="utf-8",
    )
    path.chmod(0o755)


def test_install_release_extracts_host_subtree_from_monorepo(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    host = repo / "services" / "host"
    package = host / "src" / "ordivon_host_v2"
    package.mkdir(parents=True)
    (host / ".python-version").write_text("3.14.7\n", encoding="utf-8")
    (host / "uv.lock").write_text("version = 1\n", encoding="utf-8")
    (host / "pyproject.toml").write_text(
        '[project]\nname = "ordivon-host-v2"\nversion = "0.1.0"\n',
        encoding="utf-8",
    )
    (host / "mcp-surface.json").write_text(
        '{"schemaVersion":1,"kind":"ordivon.mcp-tool-surface","service":"ordivon-host-v2",'
        '"packageVersion":"0.1.0","surfaceEpoch":1,"tools":["host.status"]}\n',
        encoding="utf-8",
    )
    (package / "__init__.py").write_text('VALUE = "monorepo-host"\n', encoding="utf-8")
    (repo / "README.md").write_text("monorepo root sentinel\n", encoding="utf-8")

    assert _run("git", "init", "-q", str(repo)).returncode == 0
    _git(repo, "config", "user.name", "test")
    _git(repo, "config", "user.email", "test@example.invalid")
    _git(repo, "add", ".")
    _git(repo, "commit", "-qm", "fixture")
    commit = _git(repo, "rev-parse", "HEAD")

    fake_uv = tmp_path / "uv"
    _fake_uv(fake_uv)
    prefix = tmp_path / "installed"
    env = os.environ.copy()
    env["ORDIVON_HOST_V2_RELEASE_UV"] = str(fake_uv)
    env["ORDIVON_HOST_V2_PYTHON_INSTALL_DIR"] = str(tmp_path / "python")
    uv_call_log = tmp_path / "uv_calls.log"
    env["ORDIVON_TEST_UV_CALL_LOG"] = str(uv_call_log)

    result = _run(str(INSTALL), str(repo), commit, str(prefix), env=env)
    assert result.returncode == 0, result.stderr

    release = prefix / "releases" / commit
    assert (release / ".python-version").read_text(encoding="utf-8") == "3.14.7\n"
    assert (release / "src" / "ordivon_host_v2" / "__init__.py").read_text(
        encoding="utf-8"
    ) == 'VALUE = "monorepo-host"\n'
    assert not (release / "services").exists()
    assert not (release / "README.md").exists()
    assert (prefix / "current").resolve() == release
    assert f"installed_release={commit}" in result.stdout
    assert "source_subtree=services/host" in result.stdout

    # A repeated install must accept the original immutable source. But an
    # already-created *different* release directory cannot bypass Git source
    # verification just because its name matches a valid commit.
    replay = _run(str(INSTALL), str(repo), commit, str(prefix), env=env)
    assert replay.returncode == 0, replay.stderr
    _git(repo, "commit", "--allow-empty", "-qm", "same tree, new release generation")
    next_commit = _git(repo, "rev-parse", "HEAD")
    staged_next = prefix / "releases" / next_commit
    shutil.copytree(release, staged_next)
    (staged_next / "uv.lock").write_text("modified after creation\n", encoding="utf-8")
    uv_before = uv_call_log.read_text(encoding="utf-8")
    blocked = _run(str(INSTALL), str(repo), next_commit, str(prefix), env=env)
    assert blocked.returncode == 2, blocked.stderr
    assert "release source drift" in blocked.stderr
    assert (prefix / "current").resolve() == release
    assert uv_call_log.read_text(encoding="utf-8") == uv_before

    # Git executable bits also belong to the immutable source contract.
    shutil.copyfile(release / "uv.lock", staged_next / "uv.lock")
    executable_drift = staged_next / "src" / "ordivon_host_v2" / "__init__.py"
    executable_drift.chmod(0o755)
    blocked_mode = _run(str(INSTALL), str(repo), next_commit, str(prefix), env=env)
    assert blocked_mode.returncode == 2, blocked_mode.stderr
    assert "release source drift" in blocked_mode.stderr
    assert (prefix / "current").resolve() == release
    assert uv_call_log.read_text(encoding="utf-8") == uv_before


def test_install_release_rejects_standalone_repository_layout(tmp_path: Path) -> None:
    repo = tmp_path / "standalone"
    package = repo / "src" / "ordivon_host_v2"
    package.mkdir(parents=True)
    (repo / ".python-version").write_text("3.14.7\n", encoding="utf-8")
    (repo / "uv.lock").write_text("version = 1\n", encoding="utf-8")
    (repo / "pyproject.toml").write_text(
        '[project]\nname = "ordivon-host-v2"\nversion = "0.1.0"\n',
        encoding="utf-8",
    )
    (package / "__init__.py").write_text('VALUE = "standalone-host"\n', encoding="utf-8")

    assert _run("git", "init", "-q", str(repo)).returncode == 0
    _git(repo, "config", "user.name", "test")
    _git(repo, "config", "user.email", "test@example.invalid")
    _git(repo, "add", ".")
    _git(repo, "commit", "-qm", "fixture")
    commit = _git(repo, "rev-parse", "HEAD")

    fake_uv = tmp_path / "uv"
    _fake_uv(fake_uv)
    prefix = tmp_path / "installed"
    env = os.environ.copy()
    env["ORDIVON_HOST_V2_RELEASE_UV"] = str(fake_uv)
    env["ORDIVON_HOST_V2_PYTHON_INSTALL_DIR"] = str(tmp_path / "python")

    result = _run(str(INSTALL), str(repo), commit, str(prefix), env=env)
    assert result.returncode == 2
    assert "release source must contain services/host/pyproject.toml" in result.stderr
    assert not (prefix / "current").exists()
