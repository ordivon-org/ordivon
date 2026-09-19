from pathlib import Path

from market_capital.binance_usdm_private_capture import (
    WRITE_CAPABLE_PERMISSION_FIELDS,
    permission_gate,
    qualification_summary,
)

ROOT = Path(__file__).resolve().parents[1]


def test_permission_gate_requires_reading_and_zero_write_capabilities():
    base = {
        "enable_reading": True,
        "ip_restrict": True,
        "create_time": 1,
    }
    for field in WRITE_CAPABLE_PERMISSION_FIELDS:
        base[field] = False
    assert permission_gate(base)["safe"] is True

    for field in WRITE_CAPABLE_PERMISSION_FIELDS:
        row = dict(base)
        row[field] = True
        assert permission_gate(row)["safe"] is False, field


def test_permission_gate_fails_when_reading_is_missing():
    assert permission_gate({"enable_reading": False})["safe"] is False


def test_private_capture_source_has_no_trade_or_mutation_calls():
    source = (ROOT / "src/market_capital/binance_usdm_private_capture.py").read_text()
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
    source = (ROOT / "src/market_capital/binance_usdm_private_capture.py").read_text()
    assert "/run/ordivon/inputs/binance-observer" in source
    assert "/root/.config/ordivon/secrets/binance" not in source


def test_qualification_summary_omits_account_values_and_order_trade_details():
    result = {
        "symbol": "SNDKUSDT",
        "standing": "READ_ONLY_PRIVATE_REALITY_CAPTURED",
        "permissionGate": {"safe": True, "enableReading": True},
        "privateAccountDataUsed": True,
        "calls": {
            "account_information_v3": {"ok": True, "data": {"total_wallet_balance": "SECRETISH"}},
            "futures_account_configuration": {"ok": True, "data": {"can_trade": True}},
            "get_current_multi_assets_mode": {"ok": True, "data": {"multi_assets_margin": False}},
            "get_current_position_mode": {"ok": True, "data": {"dual_side_position": False}},
            "notional_and_leverage_brackets": {"ok": True, "data": {"actual_instance": []}},
            "position_adl_quantile_estimation": {"ok": True, "data": {"symbol": "SNDKUSDT"}},
            "position_information_v3": {"ok": True, "data": [{"symbol": "SNDKUSDT", "position_amt": "0.1", "entry_price": "SECRETISH"}]},
            "current_all_open_orders": {"ok": True, "data": [{"order_id": 123, "price": "SECRETISH"}]},
            "account_trade_list": {"ok": True, "data": [{"id": 1, "price": "SECRETISH"}]},
        },
    }
    out = qualification_summary(result)
    rendered = str(out)
    assert "SECRETISH" not in rendered
    assert out["sndkPositionPresent"] is True
    assert out["positionRowCount"] == 1
    assert out["openOrderCount"] == 1
    assert out["tradeRowCount"] == 1
    assert out["externalFinancialWriteAttempted"] is False
