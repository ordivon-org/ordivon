from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = json.loads((ROOT / "config/candidate_tool_surface_registry.json").read_text())


def test_nautilus_candidate_tools_are_not_current_scripts():
    assert REGISTRY["standing"] == "CANDIDATE_TOOLS_ISOLATED_FROM_CURRENT_OPERATIONAL_SCRIPTS"
    assert REGISTRY["currentOwnerStanding"] == "NOT_ADMITTED"
    for item in REGISTRY["relocations"]:
        assert not (ROOT / item["oldPath"]).exists()
        assert (ROOT / item["candidatePath"]).is_file()
    for rel in REGISTRY["candidateOnlyTools"]:
        assert (ROOT / rel).is_file()


def test_current_public_data_runners_do_not_gate_on_nautilus():
    for rel in (
        "scripts/run-crypto-public-shadow-r1",
        "scripts/run-crypto-public-shadow-r2",
        "scripts/run-crypto-stream-resilience-r3",
    ):
        text = (ROOT / rel).read_text()
        assert "nautilus" not in text.lower()
        assert "check-crypto-execution-lane" not in text


def test_current_private_and_live_provider_gates_do_not_execute_rc4():
    private = (ROOT / "scripts/check-private-reality-readonly-preflight").read_text()
    assert "/root/external/nautilus-trader" not in private
    assert "LOCAL_BOUNDED_OKX_READONLY_CLIENT" in private

    live = (ROOT / "tools/okx_live_provider_probe.py").read_text()
    assert "nautilus_trader" not in live
    assert "okx_live_config_probe" not in live

    fullpath = (ROOT / "scripts/run-capital-trading-fullpath-closure").read_text()
    assert "nautilusLiveExecutionConfigBound" not in fullpath


def test_current_adapter_policy_names_provider_native_primary_paths():
    cfg = json.loads((ROOT / "config/crypto_data_adapters.json").read_text())
    assert cfg["okx"]["primaryPublicDataPath"] == "OKX_OFFICIAL_PUBLIC_REST_WS"
    assert cfg["binance"]["primaryPublicDataPath"] == "BINANCE_OFFICIAL_PUBLIC_REST_WS"
    assert cfg["okx"]["historicalNautilusNativeAdapter"]["role"] == "HISTORICAL_CANDIDATE_EVIDENCE_ONLY"
    assert cfg["binance"]["historicalNautilusNativeAdapter"]["role"] == "HISTORICAL_CANDIDATE_EVIDENCE_ONLY"

def test_nautilus_specific_effect_adapter_is_not_canonical_source():
    assert not (ROOT / "src/ordivon_capital/trading/nonlive_effect_qualification.py").exists()
    candidate = ROOT / "tools/nautilus_rc4/nonlive_effect_qualification.py"
    assert candidate.is_file()
    text = candidate.read_text()
    assert "reconcile_nautilus_episode" in text
    assert "ordivon_capital.trading.execution_reconciliation" in text

def test_nautilus_only_configs_are_not_canonical_config():
    for name in (
        "crypto_execution_lane.json",
        "crypto_shadow_mechanics.json",
        "nautilus_candidate.json",
    ):
        assert not (ROOT / "config" / name).exists()
        assert (ROOT / "tools/nautilus_rc4/config" / name).is_file()
