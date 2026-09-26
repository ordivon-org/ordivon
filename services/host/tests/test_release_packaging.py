from __future__ import annotations

import os
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
