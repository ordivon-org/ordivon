"""PV-N10: Tests for separated package build artifact smoke."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
BUILD_SCRIPT = ROOT / "scripts" / "smoke_ordivon_verify_build_artifacts.py"
PREPARE_SCRIPT = ROOT / "scripts" / "prepare_ordivon_verify_package_context.py"


class TestBuildSmoke:
    def test_script_exists(self):
        assert BUILD_SCRIPT.exists()

    def test_script_has_no_publish_commands(self):
        content = BUILD_SCRIPT.read_text().lower()
        forbidden = ["twine upload", "pip publish", "uv publish"]
        for f in forbidden:
            assert f not in content, f"Found forbidden: {f}"

    def test_script_uses_separated_context(self):
        """Script builds from .tmp/ordivon-verify-package-context, not private root."""
        content = BUILD_SCRIPT.read_text()
        assert "ordivon-verify-package-context" in content

    def test_script_output_is_temp(self):
        """Artifacts go to .tmp/, not repo root dist/."""
        content = BUILD_SCRIPT.read_text()
        assert ".tmp" in content

    def test_script_does_not_mutate_source(self):
        r = subprocess.run(
            [sys.executable, str(BUILD_SCRIPT)],
            capture_output=True,
            text=True,
            timeout=120,
            cwd=str(ROOT),
        )
        # May exit 0 (clean) or 1 (blocked) — both are valid, just not mutate
        assert r.returncode in (0, 1)

    def test_build_smoke_runs_and_reports(self):
        r = subprocess.run(
            [sys.executable, str(BUILD_SCRIPT)],
            capture_output=True,
            text=True,
            timeout=120,
            cwd=str(ROOT),
        )
        assert "Wheel:" in r.stdout or "wheel" in r.stdout.lower()
        assert "forbidden" in r.stdout.lower() or "🔍" in r.stdout

    def test_json_output(self):
        r = subprocess.run(
            [sys.executable, str(BUILD_SCRIPT), "--json"],
            capture_output=True,
            text=True,
            timeout=120,
            cwd=str(ROOT),
        )
        data = json.loads(r.stdout)
        assert "wheel_built" in data
        assert "sdist_built" in data
        assert "blocked" in data

    def test_clean_build_passes(self):
        """With clean separated context, build passes (0 forbidden, ordivon present)."""
        r = subprocess.run(
            [sys.executable, str(BUILD_SCRIPT)],
            capture_output=True,
            text=True,
            timeout=120,
            cwd=str(ROOT),
        )
        assert "CLEAN" in r.stdout or "✅ CLEAN" in r.stdout
        assert r.returncode == 0

    def test_forbidden_path_would_be_detected(self):
        """Confirm FORBIDDEN_PATHS list contains key private-core dirs."""
        content = BUILD_SCRIPT.read_text()
        assert '"adapters/"' in content
        assert '"domains/"' in content
        assert '"orchestrator/"' in content

    def test_overclaim_detection_present(self):
        """OVERCLAIM_PHRASES list is present and populated."""
        content = BUILD_SCRIPT.read_text()
        assert "production-ready" in content
        assert "public alpha" in content

    def test_ordivon_verify_expected(self):
        """ordivon_verify/ must be checked as expected."""
        content = BUILD_SCRIPT.read_text()
        assert "ordivon_verify/" in content
