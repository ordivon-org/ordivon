from __future__ import annotations

import copy
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

def test_current_structure_r2_plan_is_valid() -> None:
    module.validate_plan(load_plan(), repo_root=ROOT)

def test_semantic_component_type_claim_fails_closed() -> None:
    value = load_plan()
    value["mappings"][0]["semanticTypeClaim"] = "domain"
    with pytest.raises(module.StructureR2Error, match="semantic component type"):
        module.validate_plan(value)

def test_forbidden_semantic_target_root_fails_closed() -> None:
    value = load_plan()
    value["mappings"][0]["targetPaths"] = ["services/web/"]
    with pytest.raises(module.StructureR2Error, match="forbidden semantic root"):
        module.validate_plan(value)

def test_unknown_target_root_fails_closed() -> None:
    value = load_plan()
    value["mappings"][0]["targetPaths"] = ["mystery/web/"]
    with pytest.raises(module.StructureR2Error, match="not admitted"):
        module.validate_plan(value)

def test_missing_current_source_fails_closed() -> None:
    value = load_plan()
    value["mappings"][0]["sourcePaths"] = ["does-not-exist/"]
    with pytest.raises(module.StructureR2Error, match="does not exist"):
        module.validate_plan(value, repo_root=ROOT)

def test_duplicate_mapping_id_fails_closed() -> None:
    value = load_plan()
    value["mappings"].append(copy.deepcopy(value["mappings"][0]))
    with pytest.raises(module.StructureR2Error, match="duplicate mapping id"):
        module.validate_plan(value)

def test_s0_cannot_move_source() -> None:
    value = load_plan()
    s0 = next(w for w in value["waves"] if w["id"] == "S0")
    s0["movesSource"] = True
    with pytest.raises(module.StructureR2Error, match="S0 must not move source"):
        module.validate_plan(value)
