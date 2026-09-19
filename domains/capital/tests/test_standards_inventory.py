from pathlib import Path

from market_capital.standards_inventory import validate_inventory


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
    assert by_id["portfolio-dependence-analysis"]["status"] == "VALIDATION_REQUIRED"


def test_active_source_and_current_docs_do_not_depend_on_lego_or_lens_router():
    active_paths = [
        ROOT / "src/market_capital",
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
