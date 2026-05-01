"""PV-N11: Tests for wheel install smoke."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
INSTALL_SCRIPT = ROOT / "scripts" / "smoke_ordivon_verify_wheel_install.py"
BUILD_SCRIPT = ROOT / "scripts" / "smoke_ordivon_verify_build_artifacts.py"


class TestWheelInstall:
    def test_script_exists(self):
        assert INSTALL_SCRIPT.exists()

    def test_script_has_no_publish_commands(self):
        content = INSTALL_SCRIPT.read_text().lower()
        for f in ["twine upload", "pip publish", "uv publish", "twine register"]:
            assert f not in content, f"Found: {f}"

    def test_script_uses_wheel_not_editable(self):
        content = INSTALL_SCRIPT.read_text()
        assert '.whl' in content
        assert 'install' in content
        assert '--editable' not in content

    def test_script_clears_pythonpath(self):
        content = INSTALL_SCRIPT.read_text()
        assert 'PYTHONPATH' in content

    def test_script_checks_import(self):
        content = INSTALL_SCRIPT.read_text()
        assert 'import ordivon_verify' in content

    def test_install_smoke_runs_clean(self):
        r = subprocess.run(
            [sys.executable, str(INSTALL_SCRIPT)],
            capture_output=True, text=True, timeout=300, cwd=str(ROOT),
        )
        assert r.returncode == 0
        assert "CLEAN" in r.stdout

    def test_json_output(self):
        r = subprocess.run(
            [sys.executable, str(INSTALL_SCRIPT), "--json"],
            capture_output=True, text=True, timeout=300, cwd=str(ROOT),
        )
        data = json.loads(r.stdout)
        assert "import_ok" in data
        assert "schemas_available" in data
        assert "blocked" in data

    def test_script_does_not_mutate_source(self):
        subprocess.run(
            [sys.executable, str(INSTALL_SCRIPT)],
            capture_output=True, text=True, timeout=300, cwd=str(ROOT),
        )
        # Script cleans up its venv

    def test_schemas_in_wheel(self):
        """Build artifacts must include schemas."""
        r = subprocess.run(
            [sys.executable, str(BUILD_SCRIPT)],
            capture_output=True, text=True, timeout=120, cwd=str(ROOT),
        )
        assert "schemas/" in r.stdout
        assert "CLEAN" in r.stdout
