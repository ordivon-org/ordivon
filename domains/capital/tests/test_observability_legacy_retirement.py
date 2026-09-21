from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_market_capital_observability_artifacts_are_not_current_source():
    retired = (
        "scripts/render-crypto-stream-prometheus",
        "infra/prometheus/market-capital-crypto.rules.yml",
        "infra/systemd/prometheus-node-exporter-market-capital.conf",
        "infra/systemd/prometheus-node-exporter.service.d/20-market-capital-textfile.conf",
    )
    for rel in retired:
        assert not (ROOT / rel).exists(), rel


def test_legacy_metric_family_is_not_emitted_by_current_executable_surfaces():
    prefix = "ordivon_" + "market_capital_"
    offenders = []
    for root_name in ("src", "scripts", "tools", "infra"):
        root = ROOT / root_name
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if not path.is_file():
                continue
            try:
                text = path.read_text()
            except UnicodeDecodeError:
                continue
            if prefix in text:
                offenders.append(path.relative_to(ROOT).as_posix())
    assert offenders == []


def test_taxonomy_marks_legacy_observability_identity_retired_not_retained():
    taxonomy = json.loads((ROOT / "config/capital_domain_taxonomy.json").read_text())
    retained = {r["identity"] for r in taxonomy["retainedCompatibilityIdentities"]}
    assert "ordivon_market_capital_*" not in retained
    retired = taxonomy["retiredCompatibilityIdentities"]
    row = next(r for r in retired if r["identity"].startswith("ordivon_market_capital_*"))
    assert row["standing"] == "RETIRED_NO_ACTIVE_CONSUMER"
