"""Tests for Ordivon Verify private package install (PV-N4)."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
PACKAGE_SRC = ROOT / "src" / "ordivon_verify"
SMOKE_SCRIPT = ROOT / "scripts" / "smoke_ordivon_verify_private_install.py"
QUICKSTART = ROOT / "examples" / "ordivon-verify" / "quickstart"
BAD_FIXTURE = ROOT / "tests" / "fixtures" / "ordivon_verify_external_repo"


# ── Package importability ──────────────────────────────────────────────


def test_ordivon_verify_package_importable():
    import ordivon_verify  # noqa: F401


def test_cli_main_importable():
    from ordivon_verify.cli import main  # noqa: F401


def test_report_importable():
    from ordivon_verify.report import build_report  # noqa: F401


def test_runner_importable():
    from ordivon_verify.runner import run_check  # noqa: F401


def test_schemas_package_exists():
    assert (PACKAGE_SRC / "schemas" / "ordivon.verify.schema.json").is_file()
    assert (PACKAGE_SRC / "schemas" / "trust-report.schema.json").is_file()
    assert (PACKAGE_SRC / "schemas" / "verification-debt-ledger.schema.json").is_file()
    assert (PACKAGE_SRC / "schemas" / "verification-gate-manifest.schema.json").is_file()
    assert (PACKAGE_SRC / "schemas" / "document-registry.schema.json").is_file()


# ── Entrypoints ────────────────────────────────────────────────────────


def test_module_entrypoint_exists():
    assert (PACKAGE_SRC / "__main__.py").is_file()


def test_script_wrapper_still_dispatches():
    """Script wrapper must produce READY in native mode."""
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "ordivon_verify.py"), "all"],
        capture_output=True,
        text=True,
        timeout=30,
        cwd=str(ROOT),
    )
    assert result.returncode == 0
    assert "READY" in result.stdout


def test_console_entrypoint_works():
    """uv run ordivon-verify all must produce READY."""
    result = subprocess.run(
        ["uv", "run", "ordivon-verify", "all"],
        capture_output=True,
        text=True,
        timeout=30,
        cwd=str(ROOT),
    )
    assert result.returncode == 0
    assert "READY" in result.stdout


# ── Trust ladder preserved ────────────────────────────────────────────


def test_quickstart_remains_ready():
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "ordivon_verify.py"),
            "all",
            "--root",
            str(QUICKSTART),
            "--config",
            str(QUICKSTART / "ordivon.verify.json"),
        ],
        capture_output=True,
        text=True,
        timeout=30,
        cwd=str(ROOT),
    )
    assert result.returncode == 0
    assert "READY" in result.stdout


def test_bad_fixture_remains_blocked():
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "ordivon_verify.py"),
            "all",
            "--root",
            str(BAD_FIXTURE),
            "--config",
            str(BAD_FIXTURE / "ordivon.verify.json"),
        ],
        capture_output=True,
        text=True,
        timeout=30,
        cwd=str(ROOT),
    )
    assert result.returncode == 1
    assert "BLOCKED" in result.stdout


# ── Package boundary ──────────────────────────────────────────────────


def test_package_no_broker_imports():
    """No ordivon_verify module imports broker/finance/RiskEngine."""
    forbidden = ["adapters.finance", "domains.finance", "Alpaca", "broker", "RiskEngine"]
    for py_file in PACKAGE_SRC.rglob("*.py"):
        content = py_file.read_text()
        for term in forbidden:
            assert term not in content, f"{py_file.name}: imports '{term}'"


def test_package_no_secrets():
    """No API keys or secrets in package source."""
    secret_patterns = ["API_KEY", "SECRET_KEY", "TOKEN", "password"]
    for py_file in PACKAGE_SRC.rglob("*.py"):
        content = py_file.read_text()
        for pat in secret_patterns:
            assert pat not in content, f"{py_file.name}: contains '{pat}'"


# ── Metadata safety ──────────────────────────────────────────────────


def test_package_metadata_no_public_claim():
    """Package metadata must not claim public release."""
    ppt = (ROOT / "pyproject.toml").read_text()
    assert "Private prototype" in ppt or "private" in ppt.lower()


def test_smoke_script_exists():
    assert SMOKE_SCRIPT.is_file()


def test_smoke_script_no_publish():
    """Smoke script must not contain publish/upload commands."""
    content = SMOKE_SCRIPT.read_text()
    forbidden = ["twine upload", "uv publish", "npm publish", "gh release create"]
    for cmd in forbidden:
        assert cmd not in content, f"Smoke script contains '{cmd}'"


def test_smoke_script_runs():
    """Smoke script must execute and return 0."""
    result = subprocess.run(
        [sys.executable, str(SMOKE_SCRIPT)],
        capture_output=True,
        text=True,
        timeout=60,
        cwd=str(ROOT),
    )
    assert result.returncode == 0, f"Smoke failed:\n{result.stdout}\n{result.stderr}"
    assert "PASSED" in result.stdout
