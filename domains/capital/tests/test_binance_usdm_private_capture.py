from pathlib import Path

from ordivon_capital.trading.binance_usdm_private_capture import qualification_summary

ROOT = Path(__file__).resolve().parents[1]


def test_private_capture_source_has_no_trade_or_mutation_calls():
    source = (ROOT / "src/ordivon_capital/trading/binance_usdm_private_capture.py").read_text()
    forbidden = (
        ".new_order(",
        ".change_initial_leverage(",
        ".change_margin_type(",
        ".change_position_mode(",
        ".change_multi_assets_mode(",
        ".modify_",
        ".cancel_",
        "stock/contract",
    )
    assert all(token not in source for token in forbidden)


def test_private_runner_defaults_to_runtime_bound_credential_path():
    source = (ROOT / "src/ordivon_capital/trading/binance_usdm_private_capture.py").read_text()
    assert "/run/ordivon/inputs/binance-observer" in source
    assert "/root/.config/ordivon/secrets/binance" not in source


def test_qualification_summary_omits_account_values_and_order_trade_details():
    result = {
        "symbol": "SNDKUSDT",
        "standing": "READ_ONLY_PRIVATE_REALITY_CAPTURED",
        "privateAccountDataUsed": True,
        "calls": {
            "account_information_v3": {"ok": True, "data": {"total_wallet_balance": "SECRETISH"}},
            "futures_account_configuration": {"ok": True, "data": {"can_trade": True}},
            "get_current_multi_assets_mode": {"ok": True, "data": {"multi_assets_margin": False}},
            "get_current_position_mode": {"ok": True, "data": {"dual_side_position": False}},
            "notional_and_leverage_brackets": {"ok": True, "data": {"actual_instance": []}},
            "position_adl_quantile_estimation": {"ok": True, "data": {"symbol": "SNDKUSDT"}},
            "position_information_v3": {
                "ok": True,
                "data": [{"symbol": "SNDKUSDT", "position_amt": "0.1", "entry_price": "SECRETISH"}],
            },
            "current_all_open_orders": {
                "ok": True,
                "data": [{"order_id": 123, "price": "SECRETISH"}],
            },
            "account_trade_list": {"ok": True, "data": [{"id": 1, "price": "SECRETISH"}]},
            "get_income_history": {"ok": True, "data": [{"income": "SECRETISH"}]},
        },
    }
    out = qualification_summary(result)
    rendered = str(out)
    assert "SECRETISH" not in rendered
    assert out["sndkPositionPresent"] is True
    assert out["positionRowCount"] == 1
    assert out["activePositionCount"] == 1
    assert out["openOrderCount"] == 1
    assert out["tradeRowCount"] == 1
    assert out["incomeSampleRowCount"] == 1
    assert out["incomeHistoryComplete"] is False
    assert out["externalFinancialWriteAttempted"] is False


def test_broad_position_reads_use_official_sdk_without_symbol_filter():
    from pathlib import Path

    src = (
        Path(__file__).resolve().parents[1]
        / "src/ordivon_capital/trading/binance_usdm_private_capture.py"
    ).read_text()
    assert "usdm.position_information_v3,\n            recv_window=5000" in src
    assert "usdm.current_all_open_orders,\n            recv_window=5000" in src
    assert 'parser.add_argument("--symbol", default=None)' in src


def test_binance_runner_uses_network_owner_native_readiness():
    runner = (ROOT / "scripts/capture-binance-usdm-private-r1").read_text()
    assert "/usr/local/libexec/network-v2/finance-ready" in runner
    assert "check-network-v2-public-data" not in runner
    assert "finance-ready binance-wallet" not in runner


def test_old_permission_gate_is_absent_from_observer_source():
    source = (ROOT / "src/ordivon_capital/trading/binance_usdm_private_capture.py").read_text()
    for obsolete in (
        "WRITE_CAPABLE_PERMISSION_FIELDS",
        "permission_gate(",
        "credentialReadOnly",
        "writeCapablePermissions",
        "permissionGate",
        "get_api_key_permission",
        "PERMISSION_NOT_READ_ONLY",
    ):
        assert obsolete not in source


def test_sdk_read_is_truth_source_not_permissions_metadata():
    from ordivon_capital.trading.private_reality import normalize_binance_usdm_observer

    x = normalize_binance_usdm_observer(
        {
            "standing": "READ_ONLY_PRIVATE_REALITY_CAPTURED",
            "externalFinancialWriteAttempted": False,
            "permissionGate": {"safe": False},
            "calls": {"account_information_v3": {"ok": True, "data": {}}},
        }
    )
    assert x["permissionStanding"] == "USER_DATA_GET_VERIFIED"


def test_legacy_permission_metadata_cannot_claim_success_without_provider_get():
    from ordivon_capital.trading.private_reality import normalize_binance_usdm_observer

    snapshot = normalize_binance_usdm_observer(
        {
            "standing": "READ_ONLY_PRIVATE_REALITY_PARTIAL",
            "externalFinancialWriteAttempted": False,
            "permissionGate": {"safe": True},
            "calls": {},
        }
    )
    assert snapshot["permissionStanding"] == "NOT_VERIFIED"
