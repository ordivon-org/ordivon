"""Check source-bound interpreter qualification through the real CLI."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
VERIFIER = ROOT / "packaging" / "verify_python_version.py"


def run(operation: str, root: Path):
    return subprocess.run(
        [sys.executable, str(VERIFIER), operation, str(root)],
        capture_output=True,
        text=True,
        check=False,
    )


def test_exact_source_version_matches_actual_interpreter() -> None:
    request = run("request", ROOT)
    assert request.returncode == 0, request.stderr
    assert request.stdout.strip() == ".".join(map(str, sys.version_info[:3]))
    verified = run("verify", ROOT)
    assert verified.returncode == 0, verified.stderr


@pytest.mark.parametrize(
    ("version", "requirement"),
    [
        ("3.15\n", "==3.15"),
        ("3.15.1\n3.15.2\n", "==3.15.2"),
        ("3.15.2\n", ">=3.15.2"),
        ("3.15.2\n", "==3.15.1"),
    ],
)
def test_invalid_source_request_is_rejected_before_install(tmp_path, version, requirement):
    (tmp_path / ".python-version").write_text(version, encoding="utf-8")
    (tmp_path / "pyproject.toml").write_text(
        f'[project]\nrequires-python = "{requirement}"\n', encoding="utf-8"
    )
    assert run("request", tmp_path).returncode != 0
    assert run("verify", tmp_path).returncode != 0


def test_wrong_actual_interpreter_is_rejected(tmp_path):
    requested = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro + 1}"
    (tmp_path / ".python-version").write_text(requested + "\n", encoding="utf-8")
    (tmp_path / "pyproject.toml").write_text(
        f'[project]\nrequires-python = "=={requested}"\n', encoding="utf-8"
    )
    assert run("request", tmp_path).returncode == 0
    result = run("verify", tmp_path)
    assert result.returncode != 0
    assert "Gateway release Python mismatch" in result.stderr
