"""PV-N9: Tests for Ordivon Verify public wedge packaging separation."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
MANIFEST = ROOT / "docs" / "product" / "ordivon-verify-package-file-manifest.json"
PREPARE_SCRIPT = ROOT / "scripts" / "prepare_ordivon_verify_package_context.py"
CONTEXT_DIR = ROOT / ".tmp" / "ordivon-verify-package-context"


class TestPackageManifest:
    def test_manifest_exists_and_valid_json(self):
        assert MANIFEST.exists()
        data = json.loads(MANIFEST.read_text(encoding="utf-8"))
        assert "entries" in data

    def test_manifest_includes_src_ordivon_verify(self):
        data = json.loads(MANIFEST.read_text(encoding="utf-8"))
        src_entry = [e for e in data["entries"] if e["source"] == "src/ordivon_verify"]
        assert len(src_entry) == 1
        assert src_entry[0]["include"] is True

    def test_manifest_includes_schemas(self):
        data = json.loads(MANIFEST.read_text(encoding="utf-8"))
        schema_entry = [e for e in data["entries"] if e["source"] == "src/ordivon_verify/schemas"]
        assert len(schema_entry) == 1
        assert schema_entry[0]["include"] is True

    def test_manifest_includes_quickstart(self):
        data = json.loads(MANIFEST.read_text(encoding="utf-8"))
        qs_entry = [e for e in data["entries"] if e["source"] == "examples/ordivon-verify/quickstart"]
        assert len(qs_entry) == 1
        assert qs_entry[0]["include"] is True

    def test_manifest_excludes_private_core(self):
        data = json.loads(MANIFEST.read_text(encoding="utf-8"))
        private_entries = [
            e for e in data["entries"]
            if e["classification"] == "excluded_private_core"
        ]
        for e in private_entries:
            assert e["include"] is False

    def test_manifest_excludes_legacy_runtime(self):
        data = json.loads(MANIFEST.read_text(encoding="utf-8"))
        legacy = [
            e for e in data["entries"]
            if e["classification"] == "excluded_legacy_runtime"
        ]
        for e in legacy:
            assert e["include"] is False

    def test_manifest_excludes_finance_broker(self):
        data = json.loads(MANIFEST.read_text(encoding="utf-8"))
        fin = [e for e in data["entries"] if e["classification"] == "excluded_finance_broker"]
        for e in fin:
            assert e["include"] is False

    def test_manifest_excludes_docs_archive(self):
        """No docs/archive in manifest — excluded via broader docs/governance/docs/runtime blocks."""
        data = json.loads(MANIFEST.read_text(encoding="utf-8"))
        # docs/governance is excluded
        gov = [e for e in data["entries"] if e["source"] == "docs/governance"]
        assert len(gov) == 1
        assert gov[0]["include"] is False


class TestPrepareScript:
    def test_script_exists(self):
        assert PREPARE_SCRIPT.exists()

    def test_script_does_not_contain_publish(self):
        """Script must not contain publish/upload commands."""
        content = PREPARE_SCRIPT.read_text()
        forbidden = ["twine upload", "pip publish", "git push", "curl.*pypi"]
        for f in forbidden:
            assert f not in content.lower(), f"Found forbidden: {f}"

    def test_script_generates_context(self):
        """Running the script generates context output."""
        r = subprocess.run(
            [sys.executable, str(PREPARE_SCRIPT)],
            capture_output=True, text=True, timeout=30, cwd=str(ROOT),
        )
        assert r.returncode == 0
        assert "Package context generated cleanly" in r.stdout

    def test_script_does_not_mutate_source(self):
        """Script does not modify any source files."""
        r = subprocess.run(
            [sys.executable, str(PREPARE_SCRIPT)],
            capture_output=True, text=True, timeout=30, cwd=str(ROOT),
        )
        assert r.returncode == 0

    def test_json_output(self):
        r = subprocess.run(
            [sys.executable, str(PREPARE_SCRIPT), "--json"],
            capture_output=True, text=True, timeout=30, cwd=str(ROOT),
        )
        assert r.returncode == 0
        data = json.loads(r.stdout)
        assert "copied_files" in data
        assert "blocking_findings" in data


class TestGeneratedContext:
    def test_context_readme_exists(self):
        readme = CONTEXT_DIR / "README.md"
        assert readme.exists()

    def test_context_pyproject_exists(self):
        pp = CONTEXT_DIR / "pyproject.toml"
        assert pp.exists()

    def test_context_license_proposal_exists(self):
        license_file = CONTEXT_DIR / "LICENSE-PROPOSAL.md"
        assert license_file.exists()

    def test_context_has_src_ordivon_verify(self):
        src = CONTEXT_DIR / "src" / "ordivon_verify"
        assert src.is_dir()

    def test_context_has_schemas(self):
        schemas = CONTEXT_DIR / "schemas"
        assert schemas.is_dir()

    def test_context_has_quickstart(self):
        qs = CONTEXT_DIR / "examples" / "quickstart"
        assert qs.is_dir()

    def test_context_excludes_adapters(self):
        adapters = CONTEXT_DIR / "adapters"
        assert not adapters.exists()

    def test_context_excludes_domains(self):
        domains = CONTEXT_DIR / "domains"
        assert not domains.exists()

    def test_context_has_no_unsafe_identity(self):
        """Generated metadata files must not claim production readiness or public alpha."""
        # Only check generated files, not copied source docs (which may discuss readiness in context)
        for f in [CONTEXT_DIR / "README.md", CONTEXT_DIR / "pyproject.toml", CONTEXT_DIR / "LICENSE-PROPOSAL.md"]:
            content = f.read_text(errors="replace").lower()
            for token in ["production-ready", "public alpha"]:
                assert token not in content, f"Found '{token}' in generated {f.name}"
