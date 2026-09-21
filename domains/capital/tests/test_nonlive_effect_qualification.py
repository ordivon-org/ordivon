from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "tools/nautilus_rc4/nonlive_effect_qualification.py"

spec = importlib.util.spec_from_file_location("nautilus_rc4_nonlive_effect_qualification", MODULE_PATH)
assert spec is not None and spec.loader is not None
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

reconcile_nautilus_episode = module.reconcile_nautilus_episode
reconcile_unknown_after_submission = module.reconcile_unknown_after_submission


def episode(status: str, *, filled: str = "0", fills=None):
    return {
        "orders": [{
            "client_order_id": "C1",
            "venue_order_id": "V1" if status != "DENIED" else "nan",
            "instrument_id": "BTCUSDT.BINANCE",
            "side": "BUY",
            "type": "MARKET",
            "time_in_force": "GTC",
            "status": status,
            "quantity": "1.000000",
            "filled_qty": filled,
            "avg_px": "50000.00" if filled != "0" else "nan",
        }],
        "fills": fills or [],
    }


def test_fill_consumes():
    x = reconcile_nautilus_episode(episode("FILLED", filled="1", fills=[{
        "client_order_id":"C1","venue_order_id":"V1","trade_id":"T1","instrument_id":"BTCUSDT.BINANCE","last_qty":"1","last_px":"50000"
    }]))
    assert x["reconciliation"]["reservationResolution"] == "POST_PENDING_TRANSFER"


def test_cancel_releases():
    x = reconcile_nautilus_episode(episode("CANCELED"))
    assert x["reconciliation"]["standing"] == "RECONCILED_ZERO_FILL_TERMINAL"
    assert x["reconciliation"]["reservationResolution"] == "VOID_PENDING_TRANSFER"


def test_local_deny_maps_to_terminal_reject_and_releases():
    x = reconcile_nautilus_episode(episode("DENIED"))
    assert x["reality"]["orderHistory"][0]["status"] == "REJECTED"
    assert x["reconciliation"]["reservationResolution"] == "VOID_PENDING_TRANSFER"


def test_unknown_after_submission_retains():
    x = reconcile_unknown_after_submission(client_order_id="C1", quantity="1")
    assert x["reconciliation"]["standing"] == "UNKNOWN"
    assert x["reconciliation"]["reservationResolution"] == "NO_MUTATION"
