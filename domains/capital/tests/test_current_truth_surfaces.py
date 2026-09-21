from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_current_truth_docs_do_not_claim_monolithic_market_domain():
    targets = (
        "docs/COMPOSITION_FIRST_2026-09-14.md",
        "docs/EXTERNAL_IMPLEMENTATION_QUALIFICATION_R1.md",
        "docs/IMPLEMENTATION_OWNER_REQUALIFICATION_20260921.md",
        "docs/ORDIVON_CAPITAL_EXTERNAL_OWNER_CENSUS_R1.md",
    )
    forbidden = (
        "currently instantiated Market domain",
        "Current Market Capital implications",
        "Local Ordivon Capital / Market-domain responsibility",
        "Prometheus Market-domain TSDB/alerting is not active",
    )
    offenders = []
    for rel in targets:
        text = (ROOT / rel).read_text()
        for phrase in forbidden:
            if phrase in text:
                offenders.append((rel, phrase))
    assert offenders == []


def test_current_owner_census_names_capital_research_not_current_market_domain():
    census = json.loads((ROOT / "config/external_owner_census.json").read_text())
    serialized = json.dumps(census)
    assert "The current Market domain has no MLflow" not in serialized
    assert "The current Capital Research domain has no MLflow" in serialized


def test_current_owner_census_tree_lists_domain_owner_packages():
    text = (ROOT / "docs/ORDIVON_CAPITAL_EXTERNAL_OWNER_CENSUS_R1.md").read_text()
    for package in (
        "markets/",
        "trading/",
        "portfolio/",
        "risk/",
        "research/",
        "governance/",
        "accounting/",
    ):
        assert package in text
    assert "└── market/       currently instantiated Market domain" not in text


def test_current_observability_text_matches_retirement_state():
    text = (ROOT / "docs/IMPLEMENTATION_OWNER_REQUALIFICATION_20260921.md").read_text()
    assert "no active TSDB/PromQL/alert-delivery contract" in text
    assert "retired after live zero-consumer proof" in text
