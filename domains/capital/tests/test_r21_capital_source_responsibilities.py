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
        for source in node["evidence"]:
            assert ".." not in Path(source).parts
            assert (CAPITAL / source).is_file(), (node["id"], source)
        if node["id"] == "CA10":
            assert set(node["r21Contract"]) == {"I","O","S","pre","post","inv","eff","c","epsilon","prov","unfold"}
            assert node["r21Contract"]["eff"] == "NONE"
            assert node["formalQualification"] == "ABSTRACT_AND_REAL_PROVIDER_REFINEMENT_UNKNOWN"
            assert node["effectBoundary"] == "NON_LIVE_SOURCE_ONLY"
            for consumer in node["consumerEvidence"]:
                assert (CAPITAL / consumer["path"]).is_file()
        elif node["id"] == "CA09":
            assert node["effectBoundary"] == "NO_EXTERNAL_EFFECT"
            assert node["formalQualification"] == (
                "INTEGER_CONSERVATION_INVARIANTS_TESTED_NO_UNIVERSAL_PROOF"
            )
            assert node["r21Contract"]["eff"] == "NONE"
            assert node["r21Contract"]["post"].find("cash after") >= 0
            assert {row["standing"] for row in node["consumerEvidence"]} == {
                "NATIVE_REAL_READ_ONLY_CLI_CONSUMER",
                "NATIVE_TEST_AND_INVARIANT_MATRIX",
            }
            for consumer in node["consumerEvidence"]:
                assert (CAPITAL / consumer["path"]).is_file()
        else:
            assert node["effectBoundary"] == "NON_LIVE_SOURCE_ONLY"
            assert node["formalQualification"] == (
                "ABSTRACT_AND_REAL_PROVIDER_REFINEMENT_UNKNOWN"
            )
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


def test_existing_source_legos_and_frozen_protocol_have_exact_owners() -> None:
    plan = _plan()
    assert {node["id"] for node in plan["nodes"]} == {f"CA{x:02d}" for x in range(1, 11)}
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
