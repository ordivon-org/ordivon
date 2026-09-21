from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = json.loads((ROOT / "config/legacy_replay_surface_registry.json").read_text())


def test_legacy_replay_registry_is_explicit_and_paths_are_isolated():
    assert REGISTRY["standing"] == "ISOLATED_FROM_CURRENT_OPERATIONAL_SCRIPTS"
    assert len(REGISTRY["moves"]) == 13
    for move in REGISTRY["moves"]:
        assert move["oldPath"].startswith("scripts/")
        assert not (ROOT / move["oldPath"]).exists()
        assert (ROOT / move["currentReplayPath"]).is_file()


def test_current_canonical_pipeline_does_not_call_legacy_replay_tools():
    current = (
        "scripts/run-r0-r5-closure",
        "scripts/run-capital-trading-fullpath-closure",
        "scripts/run-canonical-tests",
        "mise.toml",
    )
    replay_roots = (
        "tools/legacy_replay/",
        "tools/tigerbeetle_0_17_9/replay/",
        "tools/nautilus_rc4/run-m6-differential",
    )
    offenders = []
    for rel in current:
        text = (ROOT / rel).read_text()
        for marker in replay_roots:
            if marker in text:
                offenders.append((rel, marker))
    assert offenders == []


def test_historical_provider_identities_are_preserved_inside_replay_surface():
    lean = (ROOT / "tools/legacy_replay/lean_wave_b/run-lean-wave-b-m1").read_text()
    assert "OrdivonMarketCapital.MarketCapitalValidationAlgorithm" in lean
    tiger = (ROOT / "tools/tigerbeetle_0_17_9/replay/run-tigerbeetle-durable-restart-smoke-r32").read_text()
    assert "market-capital:tigerbeetle:r32-test-funding" in tiger


def test_current_scripts_do_not_advertise_legacy_market_capital_replay_identity():
    offenders = []
    for path in (ROOT / "scripts").iterdir():
        if not path.is_file():
            continue
        try:
            text = path.read_text()
        except UnicodeDecodeError:
            continue
        if "OrdivonMarketCapital.MarketCapitalValidationAlgorithm" in text:
            offenders.append(path.name)
        if "market-capital:tigerbeetle:" in text:
            offenders.append(path.name)
    assert offenders == []
