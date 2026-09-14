from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKSTATION = ROOT / "workstation"
sys.path.insert(0, str(WORKSTATION))
SPEC = importlib.util.spec_from_file_location("equipment_binding_v2", WORKSTATION / "equipment_binding.py")
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(MODULE)


def test_managed_compat_shape(tmp_path: Path) -> None:
    executable = tmp_path / "tool"; executable.write_bytes(b"x"); executable.chmod(0o755)
    digest = MODULE.core.sha256_file(executable).removeprefix("sha256:")
    value = MODULE.bind_managed({"managed_equipment":{"e":{"executable":str(executable),"execution_target":"local_linux","sha256":digest}}}, "e")
    assert value["kind"] == "ordivon.workstation-equipment-binding"
    assert value["equipmentId"] == "e" and value["state"] == "AVAILABLE"
    assert value["executable"] == str(executable.resolve())
    assert value["provider"] == "workstation.v2.managed-external"


def test_professional_compat_shape(tmp_path: Path) -> None:
    executable = tmp_path / "tool"; executable.write_bytes(b"x"); executable.chmod(0o755)
    catalog={"professional_software":{"demo":{"display_name":"Demo","category":"test","platform":"linux","provider":"filesystem","launchers":[{"name":"demo","path":str(executable)}]}}}
    value=MODULE.bind_professional(catalog,"demo","demo")
    assert value["kind"] == "ordivon.workstation-equipment-binding"
    assert value["equipmentId"] == "professional:demo:demo"
    assert value["executionTarget"] == "local_linux"
