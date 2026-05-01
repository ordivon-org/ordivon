"""Tests for Ordivon Verify local build artifact smoke (PV-N8)."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SMOKE_SCRIPT = ROOT / "scripts" / "smoke_ordivon_verify_build_artifacts.py"


def _run_smoke(args: list[str] = None) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SMOKE_SCRIPT)] + (args or []),
        capture_output=True, text=True, timeout=120, cwd=str(ROOT),
    )


def test_smoke_script_exists():
    assert SMOKE_SCRIPT.is_file()


def test_smoke_script_no_publish():
    content = SMOKE_SCRIPT.read_text()
    assert "twine upload" not in content
    assert "uv publish" not in content
    assert "gh release create" not in content


def test_smoke_builds_wheel():
    """Smoke script must build wheel (even if blocked)."""
    result = _run_smoke()
    assert "Wheel:" in result.stdout and ".whl" in result.stdout


def test_smoke_detects_ordivon_verify():
    """Smoke must confirm ordivon_verify is present in artifact."""
    result = _run_smoke()
    assert "ordivon_verify" in result.stdout.lower()


def test_smoke_json_output():
    """--json must produce valid JSON with expected keys."""
    result = _run_smoke(["--json"])
    data = json.loads(result.stdout)
    assert "wheel_built" in data
    assert "forbidden_in_wheel" in data
    assert "ordivon_verify_present" in data
    assert "blocked" in data


def test_smoke_reports_blocked():
    """Smoke must report blocked status (private core in artifact)."""
    result = _run_smoke()
    # Currently expected to be blocked — pyproject packages full repo
    assert "BLOCKED" in result.stdout


def test_smoke_does_not_mutate_source():
    """Smoke must not modify source files."""
    import os
    mtimes = {}
    for f in [ROOT / "src" / "ordivon_verify" / "__init__.py",
              ROOT / "pyproject.toml"]:
        mtimes[str(f)] = os.stat(f).st_mtime
    _run_smoke()
    for p_str, orig in mtimes.items():
        assert os.stat(p_str).st_mtime == orig


def test_smoke_has_disclaimer():
    result = _run_smoke()
    assert "No upload" in result.stdout or "no upload" in result.stdout.lower()


def test_package_metadata_no_public_alpha():
    """pyproject.toml must not claim public alpha."""
    ppt = (ROOT / "pyproject.toml").read_text()
    assert "public alpha" not in ppt.lower()


def test_schemas_in_package_include():
    """Package find config must include ordivon_verify."""
    ppt = (ROOT / "pyproject.toml").read_text()
    assert "ordivon_verify" in ppt


def test_console_entrypoint_configured():
    ppt = (ROOT / "pyproject.toml").read_text()
    assert "ordivon-verify" in ppt
    assert "ordivon_verify.cli:main" in ppt
