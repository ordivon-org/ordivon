from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load(path: str):
    return json.loads((ROOT / path).read_text())


def test_okx_live_provider_uses_external_mature_clients_and_unified_secret_root():
    x = load("config/okx_live_provider.json")
    assert x["kind"] == "ordivon.market-capital.okx-live-provider"
    assert x["endpointClass"] == "LIVE"
    assert x["credentialBinding"] == "/root/.config/ordivon/secrets/okx/live-trade/config.toml"
    assert x["credentialCopyIntoRepository"] is False
    assert x["officialClient"]["name"] == "@okx_ai/okx-trade-cli"
    assert x["officialClient"]["version"] == "1.4.7"
    assert x["executionProvider"]["name"] == "NautilusTrader"
    assert x["executionProvider"]["version"] == "2.0.0rc4"
    assert x["networkAuthority"]["host"] == "openapi.okx.com"


def test_provider_trade_capability_does_not_mint_effect_admission():
    x = load("config/okx_live_provider.json")
    assert x["providerTradeCapabilityMayBeBound"] is True
    assert x["externalWritePolicyStanding"] == "NOT_ADMITTED"
    assert x["orderSubmissionAllowed"] is False
    assert x["withdrawalAllowed"] is False
    assert x["transferAllowed"] is False


def test_probe_contains_no_financial_write_command():
    s = (ROOT / "tools/okx_live_provider_probe.py").read_text()
    for command in ('"spot", "place"', '"spot", "cancel"', '"spot", "amend"', '"account", "transfer"'):
        assert command not in s
    assert "orderSubmissionAttempted\": False" in s
    assert "externalFinancialWriteAttempted\": False" in s
