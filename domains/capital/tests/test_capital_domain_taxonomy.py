from __future__ import annotations

import ast
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src/ordivon_capital"
TAXONOMY = json.loads((ROOT / "config/capital_domain_taxonomy.json").read_text())


def test_business_domains_are_importable_without_assuming_one_module_per_file():
    import importlib

    for domain in TAXONOMY["domains"]:
        result = importlib.import_module(f"ordivon_capital.{domain}")
        assert result is not None


def test_business_domain_dependency_graph_is_acyclic_and_apps_stay_outside_core():
    """Test actual import dependency semantics, not file locations or retention."""
    domains = set(TAXONOMY["domains"])
    edges = {domain: set() for domain in domains}
    for owner in domains:
        for source in (SRC / owner).rglob("*.py"):
            module = ["ordivon_capital", *source.relative_to(SRC).with_suffix("").parts]
            package = module[:-1]
            for node in ast.walk(ast.parse(source.read_text())):
                targets = []
                if isinstance(node, ast.Import):
                    targets = [alias.name.split(".") for alias in node.names]
                elif isinstance(node, ast.ImportFrom):
                    if node.level:
                        base = package[: len(package) - (node.level - 1)]
                        targets = [base + (node.module.split(".") if node.module else [])]
                    elif node.module:
                        targets = [node.module.split(".")]
                for target in targets:
                    if owner in {"risk", "portfolio"}:
                        assert not (
                            target[0] in {"psycopg", "sqlite3"}
                            or target[:2] == ["ordivon_capital", "accounting"]
                        ), (
                            "Pure risk/portfolio math may not read a database",
                            owner,
                            source.name,
                            target,
                        )
                    if len(target) < 2 or target[0] != "ordivon_capital":
                        continue
                    dest = target[1]
                    assert dest != "applications", (
                        "Core domain imported an application orchestration consumer",
                        owner,
                        source.name,
                    )
                    if dest in domains and dest != owner:
                        edges[owner].add(dest)

    visited: set[str] = set()
    visiting: set[str] = set()

    def traverse(owner: str):
        assert owner not in visiting, ("business domain cycle", owner, edges)
        if owner in visited:
            return
        visiting.add(owner)
        for child in edges[owner]:
            traverse(child)
        visiting.remove(owner)
        visited.add(owner)

    for owner in domains:
        traverse(owner)


def test_no_database_dependency_rule_catches_a_new_bad_import(monkeypatch):
    # Inject an illegal edge in-memory, rather than requiring any old source
    # file or private helper to be kept. The rule must fail on the bad program.
    original = Path.read_text
    portfolio_file = next(
        p for p in (SRC / "portfolio").glob("*.py") if p.name != "__init__.py"
    )

    def injected(path: Path, *args, **kwargs):
        source = original(path, *args, **kwargs)
        if path == portfolio_file:
            source += "\nfrom ordivon_capital.accounting import postgres_ledger\n"
        return source

    monkeypatch.setattr(Path, "read_text", injected)
    with pytest.raises(AssertionError, match="Pure risk/portfolio math"):
        test_business_domain_dependency_graph_is_acyclic_and_apps_stay_outside_core()


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
    assert _forbidden_market_imports("from .. import trading") == ["ordivon_capital.trading"]
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
