import fnmatch
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CENSUS = json.loads((ROOT / "config/external_owner_census.json").read_text())


def test_external_owner_census_has_no_unowned_active_python_module():
    patterns = [
        pattern
        for responsibility in CENSUS["responsibilities"]
        for pattern in responsibility["sourcePatterns"]
    ]
    modules = [
        path.relative_to(ROOT).as_posix()
        for path in (ROOT / "src/ordivon_capital").rglob("*.py")
        if path.name != "__init__.py"
    ]
    uncovered = [
        module for module in modules
        if not any(fnmatch.fnmatch(module, pattern) for pattern in patterns)
    ]
    assert uncovered == []


def test_old_market_capital_python_namespace_is_retired():
    assert not (ROOT / "src" / ("market" + "_capital")).exists()
    for path in [ROOT / "src", ROOT / "tests", ROOT / "scripts", ROOT / "tools"]:
        for file in path.rglob("*"):
            if not file.is_file():
                continue
            try:
                text = file.read_text()
            except UnicodeDecodeError:
                continue
            if file == Path(__file__):
                continue
            legacy_namespace = "market" + "_capital."
            legacy_path = "src/market" + "_capital"
            assert legacy_namespace not in text, file
            assert legacy_path not in text, file


def test_not_instantiated_domains_have_no_local_packages():
    package_names = {path.name for path in (ROOT / "src/ordivon_capital").iterdir() if path.is_dir()}
    for domain in CENSUS["notInstantiatedDomains"]:
        assert domain["standing"] == "NO_LOCAL_DOMAIN_CODE"
        assert domain["domain"] not in package_names


def test_portfolio_surface_is_split_by_real_owner_after_audit():
    by_id = {row["id"]: row for row in CENSUS["responsibilities"]}
    assert by_id["market-portfolio-observation-and-statistics"]["localStanding"] == "THIN_GLUE_AFTER_OWNER_AUDIT"
    assert by_id["market-counterfactual-projection"]["localStanding"] == "RETAINED_IRREDUCIBLE_READONLY_GLUE"
    assert "OPA for risk-limit decisions" in by_id["market-portfolio-observation-and-statistics"]["externalOwners"]
    assert "OPA for pre-trade evidence controls" in by_id["market-counterfactual-projection"]["externalOwners"]


def test_active_contract_identity_places_market_under_capital():
    roots = [
        ROOT / "src", ROOT / "config", ROOT / "schema", ROOT / "contracts",
        ROOT / "scripts", ROOT / "tools", ROOT / "tests", ROOT / "policy",
    ]
    legacy = "ordivon.market" + "-capital."
    offenders = []
    for root in roots:
        if not root.exists():
            continue
        for file in root.rglob("*"):
            if not file.is_file() or file == Path(__file__):
                continue
            try:
                text = file.read_text()
            except UnicodeDecodeError:
                continue
            if legacy in text:
                offenders.append(file.relative_to(ROOT).as_posix())
    assert offenders == []


def test_every_active_responsibility_has_a_resolved_external_owner_standing():
    unresolved = {"SUBSTITUTION_PRIORITY", "MIGRATION_CANDIDATE", "NO_OWNER_FOUND", "OBSOLETE_CUSTOM"}
    offenders = [row["id"] for row in CENSUS["responsibilities"] if row["localStanding"] in unresolved]
    assert offenders == []

def test_research_data_is_external_owned_not_a_capital_data_platform():
    by_id = {row["id"]: row for row in CENSUS["responsibilities"]}
    row = by_id["research-data-and-model-governance"]
    assert row["localStanding"] == "THIN_GLUE_CROSS_DOMAIN_EXTRACTION_PENDING"
    assert "MLflow" in row["externalOwners"]
    assert "OpenLineage target in shared Research/Data substrate" in row["externalOwners"]
