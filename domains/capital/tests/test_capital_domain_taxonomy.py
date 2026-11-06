from __future__ import annotations

import ast
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src/ordivon_capital"
TAXONOMY = json.loads((ROOT / "config/capital_domain_taxonomy.json").read_text())


def test_capital_source_packages_match_instantiated_domains():
    expected = {
        "accounting",
        "governance",
        "markets",
        "portfolio",
        "research",
        "risk",
        "trading",
    }
    actual = {p.name for p in SRC.iterdir() if p.is_dir() and not p.name.startswith("__")}
    assert expected <= actual
    assert not (SRC / "market").exists()


def test_taxonomy_module_map_matches_physical_source():
    # This is a two-sided source identity contract: a registry that omits
    # actively importable modules is just as misleading as a stale path.
    physical_domains = {
        path.name for path in SRC.iterdir()
        if path.is_dir() and (path / "__init__.py").is_file()
    }
    declared_domains = set(TAXONOMY["moduleMap"])
    assert declared_domains == physical_domains, {
        "unregisteredDomains": sorted(physical_domains - declared_domains),
        "obsoleteDomains": sorted(declared_domains - physical_domains),
    }
    assert declared_domains == set(TAXONOMY["domains"])
    for domain, names in TAXONOMY["moduleMap"].items():
        expected = {
            path.name for path in (SRC / domain).glob("*.py")
            if path.name != "__init__.py"
        }
        assert len(names) == len(set(names)), (domain, "duplicate module entry")
        assert set(names) == expected, {
            "owner": domain,
            "unregisteredModules": sorted(expected - set(names)),
            "obsoleteModules": sorted(set(names) - expected),
        }


def test_old_market_python_namespace_has_no_active_references():
    old = "ordivon_capital." + "market."
    offenders = []
    for root in (ROOT / "src", ROOT / "tests", ROOT / "scripts", ROOT / "tools"):
        for path in root.rglob("*"):
            if not path.is_file() or path == Path(__file__):
                continue
            try:
                text = path.read_text()
            except UnicodeDecodeError:
                continue
            if old in text:
                offenders.append(path.relative_to(ROOT).as_posix())
    assert offenders == []


def _forbidden_market_imports(source: str) -> list[str]:
    """Resolve standard Python absolute and parent-relative owner imports.

    The prior check missed parent-relative cross-owner imports, such as
    from ..accounting import x. Python import-level semantics suffice.
    """
    forbidden = {"trading", "portfolio", "risk", "research", "governance", "accounting"}
    offenders = []
    for node in ast.walk(ast.parse(source)):
        targets = []
        if isinstance(node, ast.Import):
            targets = [alias.name for alias in node.names]
        elif isinstance(node, ast.ImportFrom):
            if node.level == 2:
                targets = (
                    ["ordivon_capital." + node.module]
                    if node.module
                    else ["ordivon_capital." + alias.name for alias in node.names]
                )
            elif node.level == 0 and node.module:
                targets = [node.module]
        for target in targets:
            if target.startswith("ordivon_capital."):
                parts = target.split(".")
                if len(parts) > 1 and parts[1] in forbidden:
                    offenders.append(target)
    return offenders


def test_markets_domain_does_not_depend_on_decision_or_effect_domains():
    offenders = []
    for path in (SRC / "markets").glob("*.py"):
        for target in _forbidden_market_imports(path.read_text()):
            offenders.append((path.name, target))
    assert offenders == []


def test_market_boundary_recognizes_parent_relative_imports():
    assert _forbidden_market_imports("from ..accounting import paper_close") == [
        "ordivon_capital.accounting"
    ]
    assert _forbidden_market_imports("from .. import trading") == [
        "ordivon_capital.trading"
    ]
    assert _forbidden_market_imports("from .etf_eod_snapshot import admit_etf_eod_snapshot") == []


def test_trading_fullpath_runner_replaces_ambiguous_market_runner_name():
    assert (ROOT / "scripts/run-capital-trading-fullpath-closure").is_file()
    assert not (ROOT / "scripts/run-capital-market-fullpath-closure").exists()


def test_protocol_identity_migration_is_versioned_and_has_no_runtime_v1_shim():
    migration = TAXONOMY["contractIdentityMigration"]
    assert migration["legacyPrefix"] == "ordivon.capital.market.*"
    assert migration["standing"] == "ACCEPTED_V2_NO_RUNTIME_V1_SHIM"
    assert migration["currentSchemaVersion"] == 2
    assert migration["legacyReplay"] == "HISTORICAL_SOURCE_REVISION_OR_BUNDLE_ONLY"
