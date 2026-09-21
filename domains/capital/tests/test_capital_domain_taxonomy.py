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
    for domain, names in TAXONOMY["moduleMap"].items():
        for name in names:
            assert (SRC / domain / name).is_file(), (domain, name)


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


def test_markets_domain_does_not_depend_on_decision_or_effect_domains():
    forbidden = {"trading", "portfolio", "risk", "research", "governance", "accounting"}
    offenders = []
    for path in (SRC / "markets").glob("*.py"):
        tree = ast.parse(path.read_text())
        for node in ast.walk(tree):
            module = None
            if isinstance(node, ast.ImportFrom):
                module = node.module
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name.startswith("ordivon_capital."):
                        parts = alias.name.split(".")
                        if len(parts) > 1 and parts[1] in forbidden:
                            offenders.append((path.name, alias.name))
            if module and module.startswith("ordivon_capital."):
                parts = module.split(".")
                if len(parts) > 1 and parts[1] in forbidden:
                    offenders.append((path.name, module))
    assert offenders == []


def test_trading_fullpath_runner_replaces_ambiguous_market_runner_name():
    assert (ROOT / "scripts/run-capital-trading-fullpath-closure").is_file()
    assert not (ROOT / "scripts/run-capital-market-fullpath-closure").exists()


def test_protocol_identity_rename_requires_versioned_migration():
    migration = TAXONOMY["contractIdentityMigration"]
    assert migration["prefix"] == "ordivon.capital.market.*"
    assert migration["standing"] == "DEFERRED_REQUIRES_VERSIONED_SCHEMA_MIGRATION"
