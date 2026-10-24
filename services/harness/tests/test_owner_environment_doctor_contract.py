"""Owner-native CDC: Harness doctor consumes current declared tool versions."""

from __future__ import annotations

import os
import shutil
import subprocess
import tomllib
from pathlib import Path

import pytest

OWNER = Path(__file__).resolve().parents[1]
SCRIPT = OWNER / "scripts/owner-environment"


def test_owner_doctor_uses_declared_versions_and_locked_sync():
    text = SCRIPT.read_text()
    assert "sync --locked --group dev --group test" in text
    assert '"$repo/mise.toml" "$repo/pyproject.toml"' in text
    assert "tomllib.loads" in text
    assert "md.version" in text
    # Same lock must serve doctor, queue, and verification: no second uvx
    # installation with the same hard-coded version.
    tasks = (OWNER / "mise.toml").read_text()
    project = tomllib.loads((OWNER / "pyproject.toml").read_text())
    locked = tomllib.loads((OWNER / "uv.lock").read_text())
    pinned = [p.removeprefix("ruff==") for p in project["dependency-groups"]["dev"] if p.startswith("ruff==")]
    resolved = [p["version"] for p in locked["package"] if p["name"] == "ruff"]
    assert len(pinned) == len(resolved) == 1
    assert pinned == resolved
    assert tasks.count("uv run --locked ruff check src tests scripts") == 2
    assert "uvx ruff" not in tasks


def _fake_checkout(tmp_path: Path) -> Path:
    (tmp_path / "scripts").mkdir()
    shutil.copy2(SCRIPT, tmp_path / "scripts/owner-environment")
    shutil.copy2(OWNER / "mise.toml", tmp_path / "mise.toml")
    shutil.copy2(OWNER / "pyproject.toml", tmp_path / "pyproject.toml")
    # The real installed environment is the independent verifier oracle;
    # only the candidate source specification is varied.
    (tmp_path / ".venv").symlink_to(OWNER / ".venv", target_is_directory=True)
    return tmp_path


@pytest.mark.parametrize(
    ("source", "original", "replacement", "expected"),
    [
        ("mise.toml", 'python = "3.15.1"', 'python = "0.0.0"', "Harness requires Python 0.0.0"),
        ("pyproject.toml", 'ruff==0.17.2', 'ruff==0.0.0', "unexpected Ruff version"),
        ("pyproject.toml", 'pytest==9.1.1', 'pytest==0.0.0', "unexpected pytest version"),
    ],
)
def test_doctor_fails_on_declared_manifest_drift(
    tmp_path: Path, source: str, original: str, replacement: str, expected: str
):
    check = _fake_checkout(tmp_path)
    path = check / source
    before = path.read_text()
    assert before.count(original) == 1
    path.write_text(before.replace(original, replacement, 1))
    env = {k: v for k, v in os.environ.items() if k != "VIRTUAL_ENV"}
    result = subprocess.run(
        ["/usr/bin/bash", str(check / "scripts/owner-environment"), "doctor"],
        cwd=check,
        env=env,
        text=True,
        capture_output=True,
        timeout=35,
        check=False,
    )
    assert result.returncode != 0
    assert expected in result.stderr + result.stdout


def test_real_materialized_harness_owner_doctor():
    result = subprocess.run(
        ["/usr/bin/bash", str(SCRIPT), "doctor"],
        cwd=OWNER,
        env={k: v for k, v in os.environ.items() if k != "VIRTUAL_ENV"},
        text=True,
        capture_output=True,
        timeout=35,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "owner environment doctor: valid profile=test" in result.stdout
