from pathlib import Path

from ordivon_capital.market.standards_inventory import validate_inventory

ROOT = Path(__file__).resolve().parents[1]


def _inventory():
    return validate_inventory(
        inventory_path=ROOT / "config/quantitative_component_inventory.json",
        schema_path=ROOT / "schema/quantitative_component_inventory.schema.json",
    )


def test_quantitative_component_inventory_validates_against_json_schema_2020_12():
    inventory = _inventory()
    assert inventory["framework"]["name"] == (
        "Federal Reserve SR 26-2 Revised Guidance on Model Risk Management"
    )


def test_custom_regime_card_is_retired_and_dependence_model_requires_validation():
    by_id = {row["id"]: row for row in _inventory()["components"]}
    assert by_id["regime-card-r1"]["status"] == "RETIRED"
    dependence = by_id["portfolio-dependence-analysis"]
    assert dependence["status"] == "VALIDATION_REQUIRED"
    assert dependence["validation"]["standing"] == "DEVELOPMENT_TESTED"
    tail = by_id["historical-expected-shortfall"]
    assert tail["sr26ModelStanding"] == "NON_MODEL"
    assert tail["classification"] == "NON_MODEL_CALCULATION"


def test_active_source_and_current_docs_do_not_depend_on_lego_or_lens_router():
    active_paths = [
        ROOT / "src/ordivon_capital/market",
        ROOT / "docs/ARCHITECTURE.md",
        ROOT / "docs/COMPOSITION_FIRST_2026-09-14.md",
        ROOT / "docs/PORTFOLIO_RISK_MONITORING_R1.md",
        ROOT / "docs/PORTFOLIO_SCENARIO_ANALYSIS_R1.md",
        ROOT / "docs/MARKET_SENSORS_R1.md",
    ]
    forbidden = ("regime-shift", "Lens Router", "Portfolio Risk LEGO")
    for path in active_paths:
        files = path.rglob("*.py") if path.is_dir() else [path]
        for file in files:
            text = file.read_text()
            for token in forbidden:
                assert token not in text, f"{token!r} remains active in {file}"


def test_active_analytical_component_ids_are_registered():
    inventory = _inventory()
    registered = {row["id"] for row in inventory["components"]}
    source_paths = [
        ROOT / "src/ordivon_capital/market/market_sensors.py",
        ROOT / "src/ordivon_capital/market/portfolio_risk.py",
        ROOT / "src/ordivon_capital/market/portfolio_counterfactuals.py",
        ROOT / "src/ordivon_capital/market/prospective_validation.py",
        ROOT / "src/ordivon_capital/market/crypto_public_shadow.py",
        ROOT / "src/ordivon_capital/market/model_monitoring.py",
        ROOT / "src/ordivon_capital/market/monitoring_persistence.py",
    ]
    import re
    declared = set()
    for path in source_paths:
        declared.update(re.findall(r'"componentId":\s*"([^"]+)"', path.read_text()))
    assert declared
    assert declared <= registered


def test_retired_custom_ontology_does_not_reenter_active_source():
    forbidden = (
        "truthRole",
        "causalStanding",
        "causalEvidenceAvailable",
        "sameCutScope",
        "regime-shift",
        "Lens Router",
        "Portfolio Risk LEGO",
        "EffectAuthority",
        "ExternalFinancialWriteAdmission",
    )
    for path in (ROOT / "src/ordivon_capital/market").glob("*.py"):
        text = path.read_text()
        for token in forbidden:
            assert token not in text, f"retired token {token!r} re-entered {path}"
