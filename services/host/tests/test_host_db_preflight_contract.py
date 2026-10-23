from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests" / "conftest.py"
BAD_DSN = "postgresql://ordivon_ci@127.0.0.1:1/nonexistent?connect_timeout=1"


def _probe(tmp_path: Path, pytestmark: str, *, bad_dsn: bool):
    shutil.copy2(FIXTURE, tmp_path / "conftest.py")
    (tmp_path / "test_probe.py").write_text(
        "import pytest\n" + pytestmark + "\n\ndef test_probe():\n    assert True\n",
        encoding="utf-8",
    )
    env = os.environ.copy()
    env.pop("ORDIVON_HOST_V2_TEST_DSN", None)
    if bad_dsn:
        env["ORDIVON_HOST_V2_TEST_DSN"] = BAD_DSN
    return subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "-q",
            "-rs",
            "-c",
            str(ROOT / "pyproject.toml"),
            str(tmp_path),
        ],
        cwd=ROOT,
        env=env,
        text=True,
        capture_output=True,
        timeout=14,
        check=False,
    )


def test_changed_skip_reason_does_not_bypass_preflight(tmp_path: Path) -> None:
    result = _probe(
        tmp_path,
        'pytestmark = [pytest.mark.skipif(False, reason="PostgreSQL needed"),'
        ' pytest.mark.usefixtures("host_test_db_ready")]',
        bad_dsn=True,
    )
    assert result.returncode == 4, result.stdout + result.stderr
    assert "HOST_TEST_DB_PREFLIGHT_FAILED" in result.stdout + result.stderr


def test_selected_pure_contract_does_not_connect_to_bad_dsn(tmp_path: Path) -> None:
    result = _probe(tmp_path, "", bad_dsn=True)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "HOST_TEST_DB_PREFLIGHT_FAILED" not in result.stdout + result.stderr


def test_db_module_without_dsn_is_skip_not_pass(tmp_path: Path) -> None:
    result = _probe(
        tmp_path,
        'pytestmark = [pytest.mark.skipif(True, reason="Database unavailable"),'
        ' pytest.mark.usefixtures("host_test_db_ready")]',
        bad_dsn=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "Database unavailable" in result.stdout + result.stderr
