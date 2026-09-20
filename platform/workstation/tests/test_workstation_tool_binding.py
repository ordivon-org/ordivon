from __future__ import annotations

import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("workstation_tool_binding", ROOT / "workstation" / "tool_binding.py")
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_professional_binding_is_exact_and_nonsemantic(tmp_path: Path) -> None:
    executable = tmp_path / "tool"
    executable.write_bytes(b"exact-tool-bytes")
    executable.chmod(0o755)
    catalog = {"professional_software": {"demo": {"display_name":"Demo","category":"test","platform":"linux","provider":"filesystem","launchers":[{"name":"demo","path":str(executable)}]}}}
    result = MODULE.resolve_professional(catalog, "demo")
    assert result["kind"] == "ordivon.workstation.v2.tool-binding"
    assert result["observedExecutable"] == str(executable.resolve())
    assert result["executableDigest"] == MODULE.sha256_file(executable)
    assert result["executionTarget"] == "local_linux"
    assert result["versionEvidence"]["standing"] == "UNKNOWN"
    assert "runtime_execution_admitted" in result["nonClaims"]
    assert "domain_success" in result["nonClaims"]


def test_migrated_catalog_contains_current_blender_binding() -> None:
    catalog = MODULE.read_catalog(ROOT / "workstation" / "software.toml")
    blender = catalog["professional_software"]["blender"]
    assert blender["platform"] == "windows"
    assert blender["launchers"] == [{"name":"blender","path":"%LOCALAPPDATA%\\Programs\\Blender-5.2-Portable\\blender.exe"}]


def test_inventory_registry_names_workstation_v2_binding_source() -> None:
    data = json.loads((ROOT / "inventory" / "sources.json").read_text(encoding="utf-8"))
    assert data["kind"] == "ordivon.workstation.v2.machine-inventory-source-registry"
    row = next(item for item in data["sources"] if item["id"] == "workstation-declared-tool-bindings")
    assert row["source"] == "workstation/software.toml"
    assert row["mode"] == "read_only_live_binding"
