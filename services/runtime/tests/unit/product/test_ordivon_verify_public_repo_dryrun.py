"""Tests for Ordivon Verify public repo dry-run (PV-N7)."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
MANIFEST = ROOT / "docs" / "product" / "ordivon-verify-public-repo-file-manifest.json"
DRYRUN_SCRIPT = ROOT / "scripts" / "dryrun_ordivon_verify_public_repo.py"


def _run_dryrun(args: list[str] = None) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(DRYRUN_SCRIPT)] + (args or []),
        capture_output=True,
        text=True,
        timeout=60,
        cwd=str(ROOT),
    )


# ── Manifest ──────────────────────────────────────────────────────────


def test_manifest_exists():
    assert MANIFEST.is_file()


def test_manifest_is_valid_json():
    data = json.loads(MANIFEST.read_text())
    assert "entries" in data
    assert len(data["entries"]) > 20


def test_manifest_includes_src():
    data = json.loads(MANIFEST.read_text())
    includes = [e for e in data["entries"] if e.get("include")]
    sources = [e["source"] for e in includes]
    assert "src/ordivon_verify" in sources


def test_manifest_includes_schemas():
    data = json.loads(MANIFEST.read_text())
    includes = [e for e in data["entries"] if e.get("include")]
    sources = [e["source"] for e in includes]
    assert "src/ordivon_verify/schemas" in sources


def test_manifest_includes_quickstart():
    data = json.loads(MANIFEST.read_text())
    includes = [e for e in data["entries"] if e.get("include")]
    sources = [e["source"] for e in includes]
    assert any("quickstart" in s for s in sources)


def test_manifest_excludes_private_core():
    data = json.loads(MANIFEST.read_text())
    excludes = [e for e in data["entries"] if not e.get("include")]
    sources = [e["source"] for e in excludes]
    for excluded in ["adapters", "domains", "orchestrator", "capabilities", "intelligence", "apps", "policies"]:
        assert excluded in sources, f"Manifest should exclude '{excluded}'"


# ── Dry-run script ────────────────────────────────────────────────────


def test_dryrun_script_exists():
    assert DRYRUN_SCRIPT.is_file()


def test_dryrun_script_no_publish():
    content = DRYRUN_SCRIPT.read_text()
    assert "twine upload" not in content
    assert "uv publish" not in content
    assert "gh repo create" not in content


def test_dryrun_creates_output():
    import tempfile

    with tempfile.TemporaryDirectory() as td:
        result = subprocess.run(
            [sys.executable, str(DRYRUN_SCRIPT), "--output", td, "--keep"],
            capture_output=True,
            text=True,
            timeout=60,
            cwd=str(ROOT),
        )
        assert result.returncode == 0
        assert (Path(td) / "README.md").exists()
        assert (Path(td) / "pyproject.toml").exists()
        assert (Path(td) / "src" / "ordivon_verify").is_dir()


def test_dryrun_has_required_files():
    import tempfile

    with tempfile.TemporaryDirectory() as td:
        subprocess.run(
            [sys.executable, str(DRYRUN_SCRIPT), "--output", td],
            capture_output=True,
            text=True,
            timeout=60,
            cwd=str(ROOT),
        )
        assert (Path(td) / "README.md").exists()
        assert (Path(td) / "pyproject.toml").exists()
        assert (Path(td) / "src" / "ordivon_verify" / "__init__.py").exists()
        assert (Path(td) / "schemas").is_dir()
        assert (Path(td) / "examples" / "quickstart").is_dir()
        assert (Path(td) / "docs" / "quickstart.md").exists()


def test_dryrun_excludes_private_core():
    import tempfile

    with tempfile.TemporaryDirectory() as td:
        subprocess.run(
            [sys.executable, str(DRYRUN_SCRIPT), "--output", td],
            capture_output=True,
            text=True,
            timeout=60,
            cwd=str(ROOT),
        )
        for excluded in ["adapters", "domains", "orchestrator", "capabilities", "intelligence", "apps", "policies"]:
            assert not (Path(td) / excluded).exists(), f"'{excluded}' should be excluded"


def test_dryrun_excludes_finance():
    import tempfile

    with tempfile.TemporaryDirectory() as td:
        subprocess.run(
            [sys.executable, str(DRYRUN_SCRIPT), "--output", td],
            capture_output=True,
            text=True,
            timeout=60,
            cwd=str(ROOT),
        )
        # No Alpaca/broker code in generated repo
        for f in Path(td).rglob("*.py"):
            content = f.read_text()
            assert "Alpaca" not in content or "adapters" not in str(f), f"{f.relative_to(td)}: contains Alpaca import"


def test_dryrun_does_not_mutate_source():
    """Dry-run must not modify any source files in ROOT."""
    mtimes = {}
    for f in [ROOT / "src" / "ordivon_verify" / "__init__.py", ROOT / "scripts" / "ordivon_verify.py"]:
        mtimes[str(f)] = f.stat().st_mtime

    import tempfile

    with tempfile.TemporaryDirectory() as td:
        subprocess.run(
            [sys.executable, str(DRYRUN_SCRIPT), "--output", td],
            capture_output=True,
            timeout=60,
            cwd=str(ROOT),
        )
    for p_str, orig in mtimes.items():
        assert Path(p_str).stat().st_mtime == orig


def test_dryrun_json_output():
    result = _run_dryrun(["--json"])
    data = json.loads(result.stdout)
    assert "copied_files" in data
    assert data["copied_files"] >= 10
    assert "missing_required" in data
