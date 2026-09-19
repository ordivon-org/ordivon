import json
import subprocess
from pathlib import Path

import pytest

from ordivon_capital.market.binance_usdm_provider import (
    BinanceUsdmProviderError,
    normalize_exchange_symbol,
    qualify_provider_contract,
)
from ordivon_capital.market.binance_usdm_public_capture import (
    _book_summary,
    _current_and_next_session,
)

ROOT = Path(__file__).resolve().parents[1]


def _config():
    return json.loads((ROOT / "config/binance_usdm_equity_perp_provider.json").read_text())


def test_provider_contract_is_fail_closed_and_tradfi_agreement_is_human_only():
    cfg = _config()
    out = qualify_provider_contract(cfg)
    assert out["standing"] == "PUBLIC_AND_CLIENT_SURFACES_QUALIFIED_PRIVATE_USER_DATA_PENDING"
    assert out["externalFinancialWriteAllowed"] is False
    assert cfg["tradFiAgreement"]["automationMayInvoke"] is False
    assert cfg["tradFiAgreement"]["userExplicitActionRequired"] is True
    assert cfg["effectPolicy"]["tradeEndpointsAllowed"] is False
    assert cfg["effectPolicy"]["tradFiAgreementMutationAllowed"] is False


def test_exchange_info_filters_own_tick_step_and_min_notional_not_precision_fields():
    raw = {
        "symbols": [{
            "symbol": "SNDKUSDT",
            "status": "TRADING",
            "contractType": "PERPETUAL",
            "baseAsset": "SNDK",
            "quoteAsset": "USDT",
            "marginAsset": "USDT",
            "pricePrecision": 8,
            "quantityPrecision": 8,
            "underlyingType": "TRADIFI",
            "underlyingSubType": ["EQUITY"],
            "triggerProtect": "0.05",
            "liquidationFee": "0.01",
            "marketTakeBound": "0.30",
            "orderTypes": ["LIMIT", "MARKET"],
            "timeInForce": ["GTC", "IOC", "FOK"],
            "filters": [
                {"filterType": "PRICE_FILTER", "tickSize": "0.01"},
                {"filterType": "LOT_SIZE", "stepSize": "0.01"},
                {"filterType": "MARKET_LOT_SIZE", "stepSize": "0.01"},
                {"filterType": "MIN_NOTIONAL", "notional": "5"},
            ],
        }]
    }
    out = normalize_exchange_symbol(raw, "SNDKUSDT")
    assert out["tickSize"] == "0.01"
    assert out["stepSize"] == "0.01"
    assert out["marketStepSize"] == "0.01"
    assert out["minNotional"] == "5"
    assert out["pricePrecisionInformationalOnly"] == 8
    assert out["quantityPrecisionInformationalOnly"] == 8


def test_exchange_info_missing_authoritative_filter_fails_closed():
    raw = {"symbols": [{"symbol": "SNDKUSDT", "filters": []}]}
    with pytest.raises(BinanceUsdmProviderError):
        normalize_exchange_symbol(raw, "SNDKUSDT")


def test_network_v2_registry_contains_usdm_rest_and_ws_exact_authorities():
    cfg = json.loads((ROOT / "config/network_v2_public_data.json").read_text())
    rest = cfg["authorities"]["binanceUsdmRest"]
    ws = cfg["authorities"]["binanceUsdmWs"]
    assert rest["host"] == "fapi.binance.com"
    assert rest["proxy"] == "http://127.0.0.1:19287"
    assert ws["host"] == "fstream.binance.com"
    assert ws["proxy"] == "http://127.0.0.1:19289"
    assert cfg["directFallback"] is False


def test_official_usdm_sdk_is_isolated_capability_provider():
    deps = json.loads((ROOT / "config/capability_dependencies.json").read_text())
    row = deps["capabilities"]["binanceUsdmFutures"]
    assert row["provider"] == "Binance Official USDⓈ-M Futures Python SDK"
    assert row["version"] == "17.4.0"
    assert row["interpreter"].endswith("/bin/python")


def test_preflight_introspects_official_sdk_without_credentials_or_network():
    p = subprocess.run(
        [str(ROOT / "scripts/check-binance-usdm-equity-perp-preflight")],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    )
    assert '"credentialsLoaded": false' in p.stdout
    assert '"networkCalled": false' in p.stdout
    assert '"tradeMethodPresentButNotAdmitted": "new_order"' in p.stdout


def test_exchange_info_normalizer_accepts_official_sdk_snake_case_model_dump():
    raw = {
        "symbols": [{
            "symbol": "SNDKUSDT",
            "status": "TRADING",
            "contract_type": "PERPETUAL",
            "base_asset": "SNDK",
            "quote_asset": "USDT",
            "margin_asset": "USDT",
            "price_precision": 2,
            "quantity_precision": 2,
            "underlying_type": "TRADIFI",
            "underlying_sub_type": ["EQUITY"],
            "trigger_protect": "0.05",
            "liquidation_fee": "0.01",
            "market_take_bound": "0.30",
            "order_types": ["LIMIT", "MARKET"],
            "time_in_force": ["GTC", "IOC"],
            "filters": [
                {"filter_type": "PRICE_FILTER", "tick_size": "0.01"},
                {"filter_type": "LOT_SIZE", "step_size": "0.01"},
                {"filter_type": "MARKET_LOT_SIZE", "step_size": "0.01"},
                {"filter_type": "MIN_NOTIONAL", "notional": "5"},
            ],
        }]
    }
    out = normalize_exchange_symbol(raw, "SNDKUSDT")
    assert out["contractType"] == "PERPETUAL"
    assert out["underlyingType"] == "TRADIFI"
    assert out["tickSize"] == "0.01"
    assert out["stepSize"] == "0.01"
    assert out["minNotional"] == "5"


def test_launch_leverage_is_historical_not_current_user_leverage_authority():
    cfg = _config()
    assert cfg["referenceInstrument"]["launchSpecification"]["maximumLeverageAtLaunch"] == 10
    assert cfg["historicalParameterChanges"][0]["effectiveDate"] == "2026-08-11"
    assert "leverageBracket" in cfg["historicalParameterChanges"][0]["authorityRule"]
    assert cfg["riskTruth"]["leverageBracketOwner"] == "GET /fapi/v1/leverageBracket"


def test_unknown_execution_status_requires_reconciliation_not_blind_retry():
    cfg = _config()
    recovery = cfg["executionRecovery"]
    assert recovery["blindRetryAllowed"] is False
    assert "reconcile" in recovery["unknownExecutionStatusRule"].lower()


def test_public_capture_helpers_preserve_provider_session_and_book_measurements():
    schedule = {
        "market_schedules": {
            "equity": {
                "sessions": [
                    {"start_time": 100, "end_time": 200, "type": "NO_TRADING"},
                    {"start_time": 200, "end_time": 300, "type": "OVERNIGHT"},
                ]
            }
        }
    }
    state = _current_and_next_session(schedule, 150)
    assert state["current"]["type"] == "NO_TRADING"
    assert state["next"]["type"] == "OVERNIGHT"

    book = _book_summary({
        "bids": [["100.00", "2"]],
        "asks": [["100.01", "3"]],
        "E": 10,
        "T": 9,
    })
    assert book["bestBid"] == "100.00000000"
    assert book["bestAsk"] == "100.01000000"
    assert float(book["spreadBps"]) > 0


def test_public_capture_runner_cannot_load_private_credentials_or_trade():
    source = (ROOT / "src/ordivon_capital/market/binance_usdm_public_capture.py").read_text()
    assert 'api_key=""' in source
    assert 'api_secret=""' in source
    assert "new_order" not in source
    assert "private.pem" not in source
    assert "binance/observer" not in source


def test_wallet_sdk_and_wallet_network_authority_are_registered():
    deps = json.loads((ROOT / "config/capability_dependencies.json").read_text())
    wallet = deps["capabilities"]["binanceWallet"]
    assert wallet["provider"] == "Binance Official Wallet Python SDK"
    assert wallet["version"] == "13.4.0"

    net = json.loads((ROOT / "config/network_v2_public_data.json").read_text())
    authority = net["authorities"]["binanceWalletRest"]
    assert authority["host"] == "api.binance.com"
    assert authority["proxy"] == "http://127.0.0.1:19290"
    assert authority["profile"] == "finance-binance-wallet"


def test_private_provider_requires_permission_truth_before_usdm_reads():
    cfg = _config()
    private = cfg["privateReadOnlyTruth"]
    assert "apiRestrictions" in private["permissionTruthOwner"]
    assert "enableReading=true" in private["permissionGate"]
    assert private["tradFiAgreementStanding"] == "UNKNOWN_NO_READ_ONLY_STATUS_API"
    assert private["executionAdmitted"] is False


def test_private_readonly_preflight_is_credential_free():
    p = subprocess.run(
        [str(ROOT / "scripts/check-binance-usdm-private-readonly-preflight")],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    )
    assert "credentialsLoaded=false" in p.stdout
    assert "GET-only" in p.stdout
