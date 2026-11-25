"""Check actual dependency admission, separate from installed PG cutover."""
import importlib.metadata as metadata
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def _run_check(tmp_path, case):
    # Only the sync carrier is stubbed: the real check executes under the real
    # installed interpreter against the copied exact or deliberately changed lock.
    scripts = tmp_path / "scripts"
    scripts.mkdir()
    check = scripts / "check-capabilities"
    shutil.copy2(ROOT / "scripts/check-capabilities", check)
    sync = tmp_path / "mise"
    sync.write_text("#!/bin/sh\nexit 0\n")
    sync.chmod(0o755)
    lock = (ROOT / "uv.lock").read_text()
    entry = 'name = "pytest"\nversion = "' + metadata.version("pytest") + '"'
    assert entry in lock
    if case == "drift":
        lock = lock.replace(entry, 'name = "pytest"\nversion = "0.0.0"', 1)
    elif case == "missing":
        lock = lock.replace(entry, 'name = "not-pytest"\nversion = "0.0.0"', 1)
    elif case == "ambiguous":
        lock += '\n[[package]]\nname = "pytest"\nversion = "0.0.0"\n'
    if case != "absent":
        (tmp_path / "uv.lock").write_text(lock)
    return subprocess.run(
        [str(check)], cwd=tmp_path, capture_output=True, text=True, check=False,
        env={**os.environ, "ORDIVON_CAPITAL_MISE": str(sync),
             "ORDIVON_CAPITAL_PYTHON": sys.executable},
    )


def test_capabilities_reports_actual_versions_and_pending_cutover(tmp_path):
    result = _run_check(tmp_path, "valid")
    assert result.returncode == 0, result.stderr
    first, second = map(json.loads, result.stdout.splitlines())
    assert first["versions"]["pyarrow"] == metadata.version("pyarrow")
    assert first["versions"]["psycopg"] == metadata.version("psycopg")
    assert second["databaseOwner"] == "PostgreSQL"
    assert second["installedCutover"] == "PENDING"


@pytest.mark.parametrize("case", ("drift", "missing", "ambiguous", "absent"))
def test_capabilities_rejects_unqualified_lock_identity(tmp_path, case):
    result = _run_check(tmp_path, case)
    assert result.returncode != 0, result.stdout
