"""First-layer Capital LEGO consumer qualification (SOURCE-only).

Never asserts account state, installed provider, order effect, or Formal PASS.
"""

from __future__ import annotations

import ast
import copy
import json
from pathlib import Path

import pytest

CAPITAL = Path(__file__).resolve().parents[1]
PLAN = CAPITAL / "planning" / "lego-plan-r1.json"


def _qualify_native_plan(plan: dict) -> None:
    assert plan["kind"] == "ordivon.project-lego-plan"
    nodes = plan["nodes"]
    identities = [node["id"] for node in nodes]
    assert len(identities) == len(set(identities))
    for node in nodes:
        for role in (
            "id",
            "responsibility",
            "inputs",
            "outputs",
            "behavioralContract",
            "acceptance",
        ):
            assert node.get(role), (node.get("id"), role)
        assert node["effectBoundary"] == "NON_LIVE_SOURCE_ONLY"
        assert node["formalQualification"] == ("ABSTRACT_AND_REAL_PROVIDER_REFINEMENT_UNKNOWN")
        for source in node["evidence"]:
            assert ".." not in Path(source).parts
            assert (CAPITAL / source).is_file(), (node["id"], source)
        for consumer in node["consumerEvidence"]:
            assert consumer["standing"] == "NATIVE_TEST_STATIC_CONSUMER_ONLY"
            path = consumer["path"]
            assert path.startswith("tests/")
            tree = ast.parse((CAPITAL / path).read_text(encoding="utf-8"))
            assert any(
                isinstance(row, ast.ImportFrom)
                and row.module
                and row.module.startswith("ordivon_capital.")
                for row in ast.walk(tree)
            ), (node["id"], path)


def _plan() -> dict:
    return json.loads(PLAN.read_text(encoding="utf-8"))


def test_first_layer_eight_semantic_boundaries_are_source_qualified() -> None:
    plan = _plan()
    assert len(plan["nodes"]) == 8
    _qualify_native_plan(plan)


def test_missing_runtime_effect_boundary_cannot_be_qualified() -> None:
    plan = copy.deepcopy(_plan())
    del plan["nodes"][0]["effectBoundary"]
    with pytest.raises(KeyError):
        _qualify_native_plan(plan)


def test_false_consumer_source_cannot_be_qualified() -> None:
    plan = copy.deepcopy(_plan())
    plan["nodes"][0]["consumerEvidence"][0]["path"] = "tests/not_a_capital_consumer.py"
    with pytest.raises(FileNotFoundError):
        _qualify_native_plan(plan)


def test_false_formal_promotion_is_rejected() -> None:
    plan = copy.deepcopy(_plan())
    plan["nodes"][0]["formalQualification"] = "INSTALLED_VERIFIED"
    with pytest.raises(AssertionError):
        _qualify_native_plan(plan)
