from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "workstation_tool_binding",
    ROOT / "workstation" / "tool_binding.py",
)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_declared_projection_is_deterministic_and_nonsemantic() -> None:
    catalog = {
        "professional_software": {
            "z-tool": {
                "display_name": "Z",
                "category": "media",
                "platform": "windows",
                "provider": "filesystem",
                "launchers": [{"name": "z", "path": r"C:\\Z\\z.exe"}],
            },
            "a-tool": {
                "display_name": "A",
                "category": "engineering",
                "platform": "linux",
                "provider": "pacman",
                "launchers": [{"name": "a", "path": "/usr/bin/a"}],
            },
        },
        "managed_equipment": {
            "managed-b": {
                "executable": "/opt/b",
                "execution_target": "local_linux",
            }
        },
    }

    a = MODULE.project_declared_bindings(catalog)
    b = MODULE.project_declared_bindings(catalog)

    assert a == b
    assert a["kind"] == "ordivon.workstation.v2.tool-binding-projection"
    assert a["truthRole"] == "declared-binding-index"
    assert a["projectionDigest"].startswith("sha256:")
    assert [row["bindingId"] for row in a["bindings"]] == [
        "professional:a-tool",
        "professional:z-tool",
        "managed:managed-b",
    ]
    assert all(row["state"] == "DECLARED_UNRESOLVED" for row in a["bindings"])
    assert "executable_available" in a["nonClaims"]
    assert "runtime_execution_admitted" in a["nonClaims"]
    assert "domain_success" in a["nonClaims"]


def test_declared_projection_does_not_resolve_filesystem(tmp_path: Path) -> None:
    catalog = {
        "professional_software": {
            "missing": {
                "display_name": "Missing",
                "category": "test",
                "platform": "linux",
                "provider": "filesystem",
                "launchers": [{"name": "missing", "path": str(tmp_path / "absent")}],
            }
        }
    }
    projection = MODULE.project_declared_bindings(catalog)
    row = projection["bindings"][0]
    assert row["bindingId"] == "professional:missing"
    assert row["state"] == "DECLARED_UNRESOLVED"
    assert "observedExecutable" not in row
    assert "executableDigest" not in row
