from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Callable


WRITE_CAPABLE_PERMISSION_FIELDS = (
    "enable_withdrawals",
    "enable_internal_transfer",
    "enable_margin",
    "enable_futures",
    "permits_universal_transfer",
    "enable_vanilla_options",
    "enable_fix_api_trade",
    "enable_spot_and_margin_trading",
    "enable_portfolio_margin_trading",
)


class BinanceUsdmPrivateCaptureError(RuntimeError):
    pass


def _dump(value: Any) -> Any:
    if hasattr(value, "model_dump"):
        return value.model_dump()
    if isinstance(value, list):
        return [_dump(v) for v in value]
    return value


def _oneof(value: Any) -> Any:
    data = _dump(value)
    if isinstance(data, dict) and "actual_instance" in data:
        return data["actual_instance"]
    return data


def permission_gate(permission: dict[str, Any]) -> dict[str, Any]:
    reading = permission.get("enable_reading") is True
    writes = {name: permission.get(name) is True for name in WRITE_CAPABLE_PERMISSION_FIELDS}
    safe = reading and not any(writes.values())
    return {
        "safe": safe,
        "enableReading": reading,
        "writeCapablePermissions": writes,
        "ipRestrict": permission.get("ip_restrict"),
        "createTime": permission.get("create_time"),
    }


def _call(name: str, fn: Callable[..., Any], **kwargs: Any) -> dict[str, Any]:
    try:
        return {"ok": True, "data": _oneof(fn(**kwargs).data())}
    except Exception as exc:
        return {
            "ok": False,
            "errorType": type(exc).__name__,
            "error": str(exc)[:1000],
        }


def capture(
    *,
    symbol: str,
    credential_dir: Path,
    wallet_proxy_host: str = "127.0.0.1",
    wallet_proxy_port: int = 19290,
    usdm_proxy_host: str = "127.0.0.1",
    usdm_proxy_port: int = 19287,
) -> dict[str, Any]:
    from binance_common.configuration import ConfigurationRestAPI
    from binance_sdk_derivatives_trading_usds_futures.derivatives_trading_usds_futures import (
        DerivativesTradingUsdsFutures,
    )
    from binance_sdk_wallet.wallet import Wallet

    api_key_path = credential_dir / "api_key"
    private_key_path = credential_dir / "private.pem"
    if not api_key_path.is_file() or not private_key_path.is_file():
        raise BinanceUsdmPrivateCaptureError("bound observer credential files are missing")

    api_key = api_key_path.read_text().strip()
    private_key = private_key_path.read_bytes()
    if not api_key or not private_key:
        raise BinanceUsdmPrivateCaptureError("bound observer credential files are empty")

    wallet = Wallet(
        config_rest_api=ConfigurationRestAPI(
            api_key=api_key,
            api_secret=None,
            private_key=private_key,
            timeout=10_000,
            proxy={"protocol": "http", "host": wallet_proxy_host, "port": wallet_proxy_port},
        )
    ).rest_api

    permission_call = _call("get_api_key_permission", wallet.get_api_key_permission, recv_window=5000)
    permission = permission_call.get("data") if permission_call.get("ok") else None
    gate = permission_gate(permission if isinstance(permission, dict) else {})

    envelope: dict[str, Any] = {
        "schemaVersion": 1,
        "kind": "ordivon.capital.market.binance-usdm-private-observer",
        "provider": "BINANCE",
        "product": "USDⓈ-M_FUTURES",
        "symbol": symbol,
        "officialSdk": {
            "wallet": "binance-sdk-wallet==13.4.0",
            "usdm": "binance-sdk-derivatives-trading-usds-futures==17.4.0",
        },
        "credentialBinding": "RUNTIME_DIGEST_BOUND_INPUT_AUTHORITY",
        "permission": permission_call,
        "permissionGate": gate,
        "calls": {},
        "standing": "PERMISSION_NOT_VERIFIED",
        "privateAccountDataUsed": False,
        "externalFinancialWriteAttempted": False,
    }

    if not gate["safe"]:
        envelope["standing"] = (
            "PERMISSION_NOT_READ_ONLY"
            if permission_call.get("ok")
            else "PERMISSION_QUERY_FAILED"
        )
        return envelope

    # Only after the API key is proven read-only do we touch USD-M private USER_DATA.
    usdm = DerivativesTradingUsdsFutures(
        config_rest_api=ConfigurationRestAPI(
            api_key=api_key,
            api_secret=None,
            private_key=private_key,
            timeout=10_000,
            proxy={"protocol": "http", "host": usdm_proxy_host, "port": usdm_proxy_port},
        )
    ).rest_api

    calls = {
        "account_information_v3": _call(
            "account_information_v3", usdm.account_information_v3, recv_window=5000
        ),
        "futures_account_balance_v3": _call(
            "futures_account_balance_v3", usdm.futures_account_balance_v3, recv_window=5000
        ),
        "futures_account_configuration": _call(
            "futures_account_configuration", usdm.futures_account_configuration, recv_window=5000
        ),
        "get_current_multi_assets_mode": _call(
            "get_current_multi_assets_mode", usdm.get_current_multi_assets_mode, recv_window=5000
        ),
        "get_current_position_mode": _call(
            "get_current_position_mode", usdm.get_current_position_mode, recv_window=5000
        ),
        "notional_and_leverage_brackets": _call(
            "notional_and_leverage_brackets",
            usdm.notional_and_leverage_brackets,
            symbol=symbol,
            recv_window=5000,
        ),
        "position_adl_quantile_estimation": _call(
            "position_adl_quantile_estimation",
            usdm.position_adl_quantile_estimation,
            symbol=symbol,
            recv_window=5000,
        ),
        "position_information_v3": _call(
            "position_information_v3",
            usdm.position_information_v3,
            symbol=symbol,
            recv_window=5000,
        ),
        "current_all_open_orders": _call(
            "current_all_open_orders",
            usdm.current_all_open_orders,
            symbol=symbol,
            recv_window=5000,
        ),
        "account_trade_list": _call(
            "account_trade_list",
            usdm.account_trade_list,
            symbol=symbol,
            limit=100,
            recv_window=5000,
        ),
    }
    envelope["calls"].update(calls)
    required = (
        "account_information_v3",
        "futures_account_balance_v3",
        "futures_account_configuration",
        "get_current_multi_assets_mode",
        "get_current_position_mode",
        "notional_and_leverage_brackets",
        "position_information_v3",
        "current_all_open_orders",
    )
    envelope["privateAccountDataUsed"] = True
    envelope["standing"] = (
        "READ_ONLY_PRIVATE_REALITY_CAPTURED"
        if all(calls[name]["ok"] for name in required)
        else "READ_ONLY_PERMISSION_VERIFIED_PARTIAL_PRIVATE_REALITY"
    )
    return envelope



def qualification_summary(result: dict[str, Any]) -> dict[str, Any]:
    calls = result.get("calls") or {}
    position_data = (calls.get("position_information_v3") or {}).get("data")
    if isinstance(position_data, dict) and isinstance(position_data.get("actual_instance"), list):
        position_data = position_data["actual_instance"]
    positions = position_data if isinstance(position_data, list) else []
    orders_data = (calls.get("current_all_open_orders") or {}).get("data")
    orders = orders_data if isinstance(orders_data, list) else []
    trades_data = (calls.get("account_trade_list") or {}).get("data")
    trades = trades_data if isinstance(trades_data, list) else []

    config = (calls.get("futures_account_configuration") or {}).get("data")
    multi = (calls.get("get_current_multi_assets_mode") or {}).get("data")
    posmode = (calls.get("get_current_position_mode") or {}).get("data")

    return {
        "schemaVersion": 1,
        "kind": "ordivon.capital.market.binance-usdm-private-qualification-summary",
        "provider": "BINANCE",
        "product": "USDⓈ-M_FUTURES",
        "symbol": result.get("symbol"),
        "standing": result.get("standing"),
        "permissionGate": result.get("permissionGate"),
        "callStatus": {
            name: {
                "ok": call.get("ok") is True,
                "errorType": call.get("errorType") if call.get("ok") is not True else None,
                "error": call.get("error") if call.get("ok") is not True else None,
            }
            for name, call in calls.items()
            if isinstance(call, dict)
        },
        "accountConfigurationObserved": isinstance(config, dict),
        "accountCanTradeProviderField": config.get("can_trade") if isinstance(config, dict) else None,
        "multiAssetsMode": multi.get("multi_assets_margin") if isinstance(multi, dict) else None,
        "dualSidePosition": posmode.get("dual_side_position") if isinstance(posmode, dict) else None,
        "leverageBracketObserved": (calls.get("notional_and_leverage_brackets") or {}).get("ok") is True,
        "positionAdlObserved": (calls.get("position_adl_quantile_estimation") or {}).get("ok") is True,
        "sndkPositionPresent": any(
            isinstance(row, dict)
            and row.get("symbol") == result.get("symbol")
            and str(row.get("position_amt", "0")) not in ("0", "0.0", "0.00")
            for row in positions
        ),
        "positionRowCount": len(positions),
        "openOrderCount": len(orders),
        "tradeRowCount": len(trades),
        "tradFiAgreementStanding": "UNKNOWN_NO_READ_ONLY_STATUS_API",
        "tradeEligibilityStanding": "NOT_INFERRED_FROM_READ_SURFACE",
        "privateAccountDataUsed": result.get("privateAccountDataUsed") is True,
        "externalFinancialWriteAttempted": False,
    }

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--symbol", default="SNDKUSDT")
    parser.add_argument(
        "--credential-dir",
        type=Path,
        default=Path("/run/ordivon/inputs/binance-observer"),
    )
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = capture(symbol=args.symbol, credential_dir=args.credential_dir)
    rendered = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered)
    print(json.dumps(result, sort_keys=True))
    return 0 if result["standing"] == "READ_ONLY_PRIVATE_REALITY_CAPTURED" else 3


if __name__ == "__main__":
    raise SystemExit(main())
