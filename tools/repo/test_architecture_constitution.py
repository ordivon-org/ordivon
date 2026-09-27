from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "tools" / "repo" / "check_architecture_constitution.py"
CONSTITUTION = ROOT / "docs" / "architecture" / "architecture-constitution-r1.json"

spec = importlib.util.spec_from_file_location("check_architecture_constitution", MODULE_PATH)
assert spec is not None and spec.loader is not None
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def load_constitution() -> dict:
    value = json.loads(CONSTITUTION.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def test_current_architecture_constitution_is_valid() -> None:
    module.validate_repository(ROOT)


def test_kernel_growth_fails_closed() -> None:
    value = load_constitution()
    value["minimalSemanticKernel"].append("global-session")
    with pytest.raises(module.ArchitectureConstitutionError, match="minimal semantic kernel drifted"):
        module.validate_constitution(value)


def test_gateway_cannot_become_truth_owner() -> None:
    value = copy.deepcopy(load_constitution())
    value["substrateOwners"]["northboundRoutingProjection"] = "gateway-authority"
    with pytest.raises(module.ArchitectureConstitutionError, match="substrate owner boundary drifted"):
        module.validate_constitution(value)


def test_documentation_cannot_outrank_evidence() -> None:
    value = load_constitution()
    order = value["truthOrder"]
    order.remove("current-documentation")
    order.insert(2, "current-documentation")
    with pytest.raises(module.ArchitectureConstitutionError, match="documentation must not outrank"):
        module.validate_constitution(value)
