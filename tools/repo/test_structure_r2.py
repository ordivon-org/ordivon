from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
PLAN = ROOT / "docs" / "architecture" / "structure-r2-transition-r1.json"
MODULE_PATH = ROOT / "tools" / "repo" / "check_structure_r2.py"

spec = importlib.util.spec_from_file_location("check_structure_r2", MODULE_PATH)
assert spec is not None and spec.loader is not None
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def load_plan() -> dict:
    value = json.loads(PLAN.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def test_structure_r2_is_superseded() -> None:
    module.validate_plan(load_plan())


def test_cancelled_path_wave_cannot_reopen() -> None:
    value = load_plan()
    value["remainingPathMovesCancelled"].remove("S3")
    with pytest.raises(module.StructureR2Error, match="cancelled path-only waves drifted"):
        module.validate_plan(value)


def test_open_slice_cannot_return() -> None:
    value = load_plan()
    value["openSlices"] = ["S3"]
    with pytest.raises(module.StructureR2Error, match="cannot retain open slices"):
        module.validate_plan(value)


def test_supersession_target_is_fenced() -> None:
    value = load_plan()
    value["supersededBy"] = "docs/architecture/OTHER.md"
    with pytest.raises(module.StructureR2Error, match="Architecture Re-Anchor R1"):
        module.validate_plan(value)
