from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts import artifact_cad_step as m

CONTRACT = Path(__file__).parent / "fixtures/cad/block-through-hole-contract.json"


def fixture():
    c = json.loads(CONTRACT.read_text())
    return c, {
        "status": "PASS",
        "valid": True,
        **c["topology"],
        "bboxMm": dict(c["bboxMm"]),
        "volumeMm3": c["volumeMm3"],
    }


@pytest.mark.parametrize("value", [True, 1.9, "1", None])
def test_topology_requires_exact_integer_observation(value):
    c, o = fixture()
    o["solids"] = value
    assert any("solids" in x for x in m.compare(o, c, "OCCT"))


@pytest.mark.parametrize("value", [True, "40.0", float("nan"), float("inf"), None])
def test_bbox_requires_finite_numeric_observation(value):
    c, o = fixture()
    o["bboxMm"]["xmax"] = value
    assert any("bbox xmax" in x for x in m.compare(o, c, "OCCT"))


def test_reader_contract_agreement_is_not_self_certifying():
    c, o = fixture()
    assert not m.compare(o, c, "OCCT")
    assert not m.compare(o, c, "FreeCAD")
    o["bboxMm"]["xmax"] += 2 * c["geometryToleranceMm"]
    assert m.compare(o, c, "OCCT") and m.compare(o, c, "FreeCAD")


def test_cross_reader_rejects_missing_and_nonfinite_observations():
    from artifact_verifiers.cad_geometry import compare_readers

    c, o = fixture()
    assert not compare_readers(o, o, c)
    assert compare_readers(o, {**o, "bboxMm": None}, c)
    assert compare_readers(o, {**o, "volumeMm3": float("nan")}, c)


def test_unknown_bbox_metadata_does_not_become_a_metric(tmp_path):
    c, o = fixture()
    c["bboxMm"]["note"] = "annotation"
    assert not m.compare(o, c, "OCCT")
