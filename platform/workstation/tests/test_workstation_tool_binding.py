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


def test_managed_windows_binding_projects_exact_native_tool(tmp_path: Path) -> None:
    mount_root = tmp_path / "mnt"
    executable = (
        mount_root
        / "c"
        / "ProgramData"
        / "Ordivon"
        / "RuntimeCandidateR6"
        / "native-tools"
        / "go-ios"
        / "v1.3.2"
        / "ios.exe"
    )
    executable.parent.mkdir(parents=True)
    executable.write_bytes(b"exact-go-ios-test-bytes")
    digest = MODULE.sha256_file(executable).removeprefix("sha256:")
    catalog = {
        "managed_equipment": {
            "go-ios-1-3-2": {
                "executable": (
                    r"C:\ProgramData\Ordivon\RuntimeCandidateR6"
                    r"\native-tools\go-ios\v1.3.2\ios.exe"
                ),
                "execution_target": "windows_native",
                "sha256": digest,
            }
        }
    }

    result = MODULE.resolve_managed(catalog, "go-ios-1-3-2", mount_root=mount_root)

    assert result["state"] == "AVAILABLE"
    assert result["executionTarget"] == "windows_native"
    assert result["observedExecutable"] == str(executable.resolve())
    assert result["configuredExecutable"] == (
        r"C:\ProgramData\Ordivon\RuntimeCandidateR6"
        r"\native-tools\go-ios\v1.3.2\ios.exe"
    )
    assert result["executableDigest"] == "sha256:" + digest


def test_catalog_declares_exact_go_ios_runtime_native_tool() -> None:
    catalog = MODULE.read_catalog(ROOT / "workstation" / "software.toml")
    go_ios = catalog["managed_equipment"]["go-ios-1-3-2"]
    assert go_ios["execution_target"] == "windows_native"
    assert go_ios["executable"] == (
        r"C:\ProgramData\Ordivon\RuntimeCandidateR6"
        r"\native-tools\go-ios\v1.3.2\ios.exe"
    )
    assert go_ios["sha256"] == (
        "c99b04f1d615fa716637efae457d5c554f32259f9d249375de0086e3cc1a1df5"
    )


def test_managed_windows_binding_rejects_digest_mismatch(tmp_path: Path) -> None:
    mount_root = tmp_path / "mnt"
    executable = mount_root / "c" / "ProgramData" / "Ordivon" / "tool.exe"
    executable.parent.mkdir(parents=True)
    executable.write_bytes(b"observed")
    catalog = {
        "managed_equipment": {
            "bad": {
                "executable": r"C:\ProgramData\Ordivon\tool.exe",
                "execution_target": "windows_native",
                "sha256": "0" * 64,
            }
        }
    }

    try:
        MODULE.resolve_managed(catalog, "bad", mount_root=mount_root)
    except RuntimeError as error:
        assert "digest mismatch" in str(error)
    else:
        raise AssertionError("managed Windows digest mismatch must fail closed")


def test_managed_binding_rejects_unknown_execution_target(tmp_path: Path) -> None:
    executable = tmp_path / "tool"
    executable.write_bytes(b"x")
    catalog = {
        "managed_equipment": {
            "bad-target": {
                "executable": str(executable),
                "execution_target": "future_target",
                "sha256": MODULE.sha256_file(executable).removeprefix("sha256:"),
            }
        }
    }

    try:
        MODULE.resolve_managed(catalog, "bad-target")
    except RuntimeError as error:
        assert "unsupported managed equipment execution target" in str(error)
    else:
        raise AssertionError("unknown managed execution target must fail closed")


def test_catalog_declares_exact_mobilecli_runtime_native_tool() -> None:
    catalog = MODULE.read_catalog(ROOT / "workstation" / "software.toml")
    mobilecli = catalog["managed_equipment"]["mobilecli-1-0-20"]
    assert mobilecli["execution_target"] == "windows_native"
    assert mobilecli["executable"] == (
        r"C:\ProgramData\Ordivon\RuntimeCandidateR6"
        r"\native-tools\mobilecli\v1.0.20\mobilecli.exe"
    )
    assert mobilecli["sha256"] == (
        "018dcec38ee4f39ef24fd0987d85e04914294651b8da770c647f21ca04029aa4"
    )
