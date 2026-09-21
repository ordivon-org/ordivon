from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load(path: str):
    return json.loads((ROOT / path).read_text())


def test_okx_live_provider_uses_bounded_read_client_and_unified_secret_root():
    x = load("config/okx_live_provider.json")
    assert x["kind"] == "ordivon.capital.market.okx-live-provider"
    assert x["endpointClass"] == "LIVE"
    assert x["credentialBinding"] == "/root/.config/ordivon/secrets/okx/live-trade/config.toml"
    assert x["credentialCopyIntoRepository"] is False
    assert x["credentialClass"] == "ORDER_CAPABLE_LIVE_PROVIDER_CREDENTIAL"
    assert x["providerCapabilityAuditOnly"] is True
    assert x["privateRealityAdmissionGranted"] is False
    assert x["privateRealityObserverLane"]["standing"] == "PENDING_FRESH_PROVIDER_PERMISSION_VERIFICATION"
    assert x["privateRealityObserverLane"]["currentDataAdmission"] == "NOT_ADMITTED"

    assert x["providerApiAuthority"]["owner"] == "OKX"
    assert x["readClient"]["name"] == "LOCAL_BOUNDED_OKX_READONLY_CLIENT"
    assert x["readClient"]["runtime"] == "Python 3.14.7 stdlib"
    assert x["readClient"]["allowedMethods"] == ["GET"]
    assert x["readClient"]["writeMethodsImplemented"] is False
    assert len(x["readClient"]["allowedPaths"]) == 3

    ref = x["externalReferenceClient"]
    assert ref["name"] == "@okx_ai/okx-trade-cli"
    assert ref["version"] == "1.4.7"
    assert ref["standing"] == "DIFFERENTIAL_REFERENCE_NOT_CANONICAL_READ_RUNTIME"
    assert ref["signingDifferential"] == {"cases": 120, "mismatches": 0}
    assert ref["liveStructuralDifferential"] == {"methods": 3, "mismatches": 0}

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


def test_probe_contains_no_financial_write_command_or_external_cli_invocation():
    s = (ROOT / "tools/okx_live_provider_probe.py").read_text()
    for command in (
        '"spot", "place"',
        '"spot", "cancel"',
        '"spot", "amend"',
        '"account", "transfer"',
    ):
        assert command not in s
    assert 'cfg["officialClient"]' not in s
    assert "OkxReadOnlyClient" in s
    assert '"orderSubmissionAttempted": False' in s
    assert '"externalFinancialWriteAttempted": False' in s
