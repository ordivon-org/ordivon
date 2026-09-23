from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXPECTED = {"Observe","Normalize","Validate","Measure","Model","Counterfactual","Decide","Authorize","Reserve","Effect","Reconcile","Account"}

def test_functional_lego_map_is_complete_over_current_source_modules():
    doc = json.loads((ROOT / "planning/functional-lego-map-r1.json").read_text())
    assert doc["truthRole"] == "COMPOSITION_LENS_NOT_SOURCE_OWNER_TAXONOMY"
    assert set(doc["functionalLegos"]) == EXPECTED
    current_modules = {
        p.relative_to(ROOT).as_posix()
        for p in (ROOT / "src/ordivon_capital").glob("*/*.py")
        if p.name != "__init__.py"
    }
    assert set(doc["moduleCoverage"]) == current_modules
    for roles in doc["moduleCoverage"].values():
        assert roles
        assert set(roles) <= EXPECTED

def test_decide_and_effect_do_not_invent_general_current_owners():
    doc = json.loads((ROOT / "planning/functional-lego-map-r1.json").read_text())
    assert doc["functionalLegos"]["Decide"]["standing"] == "BOUNDARY_NO_GENERAL_IMPLEMENTATION_OWNER"
    assert doc["functionalLegos"]["Effect"]["standing"] == "NONLIVE_ONLY_NO_CANONICAL_PRODUCTION_IMPLEMENTATION"
