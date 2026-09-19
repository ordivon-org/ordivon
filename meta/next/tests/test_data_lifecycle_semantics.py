from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "evidence/data-lifecycle/github-pilot-r1"


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def custom_properties(prop: dict) -> dict:
    return {row["property"]: row["value"] for row in prop.get("customProperties", [])}


def test_external_semantic_owners_are_explicit() -> None:
    p = load_json(BASE / "semantics/external-semantic-profile.json")
    assert p["externalOwners"] == {
        "statisticalStructure": "sdmx-3.1",
        "observationStatus": "sdmx-cl-obs-status-2.3",
        "unitCodes": "ucum-spec",
        "unitVocabulary": "qudt-units-3.5.1",
        "qualityMeasures": "iso-iec-5259-2-2024",
        "dataContract": "bitol-odcs-3.2.0",
    }


def test_pilot_has_no_old_semantic_heuristics() -> None:
    source = (ROOT / "scripts/data_lifecycle_github_pilot.py").read_text(encoding="utf-8")
    forbidden = [
        'endswith("_pct")',
        'startswith("access_")',
        'if name == "crossref-metadata-coverage"',
        'd["keys"]',
    ]
    for token in forbidden:
        assert token not in source


def test_quality_report_is_profile_driven() -> None:
    profile = load_json(BASE / "semantics/external-semantic-profile.json")
    q = load_json(BASE / "quality-report.json")
    assert q["qualityModelOwner"] == "iso-iec-5259-2-2024"
    assert q["fitnessForUse"] == "descriptive-analytics-pilot"
    checks = q["datasets"]["se4all-energy"]["semanticMeasureChecks"]
    assert set(checks) == set(profile["datasets"]["se4all-energy"]["measures"])
    assert q["datasets"]["se4all-energy"]["semanticMeasureViolationRows"] == 0
    assert checks["transmission_and_distribution_losses_pct"]["maximum"] is None
    assert checks["transmission_and_distribution_losses_pct"]["observedMax"] > 100


def test_odcs_projects_dimensions_units_and_null_semantics() -> None:
    profile = load_json(BASE / "semantics/external-semantic-profile.json")

    se = load_json(BASE / "contracts/se4all-energy.odcs.json")
    se_props = {p["name"]: p for p in se["schema"][0]["properties"]}
    for name, meta in profile["datasets"]["se4all-energy"]["measures"].items():
        cp = custom_properties(se_props[name])
        assert cp["unitUcum"] == meta["unitUcum"]
        assert cp["unitQudt"] == meta["unitQudt"]
        assert cp["quantitySemantics"] == meta["quantitySemantics"]
        assert se_props[name]["semanticType"] == "measure"
    for name in profile["datasets"]["se4all-energy"]["physicalPrimaryKey"]:
        assert se_props[name]["semanticType"] == "dimension"

    cr = load_json(BASE / "contracts/crossref-metadata-coverage.odcs.json")
    cr_props = {p["name"]: p for p in cr["schema"][0]["properties"]}
    subtype_cp = custom_properties(cr_props["document_subtype"])
    assert "sourceNullMeaning" in subtype_cp
    key_cp = custom_properties(cr_props["document_subtype_key"])
    assert key_cp["derivedFromNullableDimension"] == "document_subtype"


def test_acquisition_identity_is_transport_independent() -> None:
    receipt = load_json(BASE / "source/acquisition-policy.json")
    for row in receipt["datasets"].values():
        assert row["sourceIdentity"].startswith("github:rfordatascience/tidytuesday@")
        assert len(row["sha256"]) == 64
        assert row["canonicalUrl"].startswith("https://raw.githubusercontent.com/")
        assert row["allowedTransports"]
