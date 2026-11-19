"""Pure Nautilus -> PaperSession bridge tests; no provider, broker or PG effects."""
from __future__ import annotations

import unittest
from copy import deepcopy
from datetime import UTC, date, datetime

from ordivon_capital.accounting.paper_close import PaperValuation, value_session
from ordivon_capital.trading.nautilus_paper_bridge import (
    NautilusPaperBridgeError,
    next_open_paper_session,
)

PREV = date(2026, 11, 9)
SESSION = date(2026, 11, 10)
OPEN = datetime(2026, 11, 10, 14, 30, tzinfo=UTC)
ORDER_AT = datetime(2026, 11, 9, 22, tzinfo=UTC)


def episode():
    return {
        "session": SESSION,
        "previous_session": PREV,
        "expected_account_id": "A-001",
        "opens_at": OPEN,
        "previous_close_at": datetime(2026, 11, 9, 21, 0, tzinfo=UTC),
        "settlement_date": date(2026, 11, 12),
        "orders": [{
            "client_order_id": "C-1", "account_id": "A-001",
            "instrument_id": "SPY.XNAS", "ts_init": ORDER_AT,
        }],
        "decisions_by_order": {"C-1": ORDER_AT},
        "fills": [{
            "client_order_id": "C-1", "trade_id": "T-1", "event_id": "E-1",
            "account_id": "A-001", "instrument_id": "SPY.XNAS",
            "order_side": "BUY", "last_qty": "2", "last_px": "500.01",
            "currency": "USD", "commission": "0.10 USD", "ts_event": OPEN,
        }],
        "order_events": [{
            "type": "OrderFilled", "event_id": "E-1",
            "client_order_id": "C-1", "trade_id": "T-1",
            "account_id": "A-001", "instrument_id": "SPY.XNAS",
            "order_side": "BUY", "currency": "USD",
            "last_qty": "2", "last_px": "500.01",
            "commission": "0.10 USD", "ts_event": OPEN,
        }],
        "instrument_symbols": {"SPY.XNAS": "SPY"},
        "marks_minor": {"SPY": 50001},
    }


class NautilusPaperBridgeTests(unittest.TestCase):
    def test_native_fill_and_paper_cash_consumer(self):
        day = next_open_paper_session(**episode())
        self.assertEqual(len(day.buys), 1)
        self.assertFalse(day.sells)
        self.assertEqual(day.buys[0].fill_id, "nautilus-paper:A-001:T-1")
        self.assertEqual(day.buys[0].cost_minor, 100012)
        previous = PaperValuation(
            session=PREV, cash_minor=200000, protected_minor=0,
            positions={}, pending={}, contribution_minor=200000,
            payable_minor=0, nav_minor=200000,
        )
        valuation = value_session(previous, day)
        self.assertEqual(valuation.positions, {"SPY": 2})
        self.assertEqual(valuation.payable_minor, 100012)
        self.assertEqual(valuation.nav_minor, 199990)

    def test_two_partial_fills_are_distinct_trades_not_orders(self):
        e = episode()
        second = deepcopy(e["fills"][0])
        second.update(trade_id="T-2", event_id="E-2", last_qty="1", last_px="499.99",
                      commission="0.05 USD")
        e["fills"].append(second)
        e["order_events"].append({
            "type": "OrderFilled", "event_id": "E-2",
            "client_order_id": "C-1", "trade_id": "T-2",
            "account_id": "A-001", "instrument_id": "SPY.XNAS",
            "order_side": "BUY", "currency": "USD",
            "last_qty": "1", "last_px": "499.99",
            "commission": "0.05 USD", "ts_event": OPEN,
        })
        day = next_open_paper_session(**e)
        self.assertEqual([fill.shares for fill in day.buys], [2, 1])
        self.assertEqual(len({fill.fill_id for fill in day.buys}), 2)

    def test_incompatible_money_currency_share_and_time_are_rejected(self):
        incompatible = [
            ("last_qty", "1.25"), ("last_qty", "NaN"),
            ("last_px", "500.005"), ("last_px", "NaN"),
            ("commission", None), ("commission", "0.01 EUR"),
            ("commission", "-0.01 USD"), ("currency", "EUR"),
            ("ts_event", datetime(2026, 11, 10, 14, 31, tzinfo=UTC)),
        ]
        for field, value in incompatible:
            with self.subTest(field=field, value=value):
                e = episode()
                e["fills"][0][field] = value
                with self.assertRaises(NautilusPaperBridgeError):
                    next_open_paper_session(**e)

    def test_native_event_and_report_economics_cannot_disagree(self):
        for field, value in [
            ("last_qty", "3"), ("last_px", "500.02"),
            ("commission", "0.11 USD"),
            ("ts_event", datetime(2026, 11, 10, 14, 31, tzinfo=UTC)),
        ]:
            with self.subTest(field=field):
                e = episode()
                e["order_events"][0][field] = value
                with self.assertRaisesRegex(NautilusPaperBridgeError, "economics disagree"):
                    next_open_paper_session(**e)

    def test_unsupported_fill_correction_variant_fails_closed(self):
        e = episode()
        e["order_events"].append({
            "type": "OrderFillCorrected", "event_id": "E-2",
            "client_order_id": "C-1", "trade_id": "T-1",
        })
        with self.assertRaisesRegex(NautilusPaperBridgeError, "unsupported native fill correction"):
            next_open_paper_session(**e)

    def test_missing_event_history_is_not_a_proven_fill(self):
        e = episode()
        e["order_events"] = None
        with self.assertRaisesRegex(NautilusPaperBridgeError, "history"):
            next_open_paper_session(**e)
        e["order_events"] = []
        with self.assertRaisesRegex(NautilusPaperBridgeError, "event history"):
            next_open_paper_session(**e)

    def test_duplicate_report_rows_are_not_two_fills(self):
        e = episode()
        e["fills"].append(deepcopy(e["fills"][0]))
        with self.assertRaisesRegex(NautilusPaperBridgeError, "unique event"):
            next_open_paper_session(**e)

    def test_restatement_does_not_double_count_quantity(self):
        e = episode()
        e["order_events"].append({
            "type": "OrderFilled", "event_id": "E-2",
            "client_order_id": "C-1", "trade_id": "T-1",
        })
        with self.assertRaisesRegex(NautilusPaperBridgeError, "restatement"):
            next_open_paper_session(**e)

    def test_void_cannot_be_silently_imported(self):
        e = episode()
        e["order_events"].append({
            "type": "OrderFillVoided", "event_id": "E-2",
            "client_order_id": "C-1", "trade_id": "T-1",
        })
        with self.assertRaisesRegex(NautilusPaperBridgeError, "voided"):
            next_open_paper_session(**e)

    def test_order_init_time_is_not_the_investment_decision_time(self):
        e = episode()
        e["orders"][0]["ts_init"] = OPEN
        day = next_open_paper_session(**e)
        self.assertEqual(day.buys[0].decided_at, ORDER_AT)

    def test_previous_close_data_cannot_drive_preclose_investment_decision(self):
        e = episode()
        e["decisions_by_order"]["C-1"] = datetime(2026, 11, 9, 18, 0, tzinfo=UTC)
        with self.assertRaisesRegex(NautilusPaperBridgeError, "scope"):
            next_open_paper_session(**e)

    def test_missing_or_future_investment_decision_fails(self):
        e = episode()
        e["decisions_by_order"] = {}
        with self.assertRaisesRegex(NautilusPaperBridgeError, "upstream investment decision"):
            next_open_paper_session(**e)
        e["decisions_by_order"] = {"C-1": OPEN}
        with self.assertRaisesRegex(NautilusPaperBridgeError, "scope"):
            next_open_paper_session(**e)

    def test_order_account_and_instrument_must_match_fill(self):
        e = episode()
        e["fills"][0]["account_id"] = "A-OTHER"
        with self.assertRaisesRegex(NautilusPaperBridgeError, "mismatch"):
            next_open_paper_session(**e)
        e = episode()
        e["instrument_symbols"].clear()
        with self.assertRaisesRegex(NautilusPaperBridgeError, "mapping"):
            next_open_paper_session(**e)

    def test_all_native_events_must_be_represented_in_report(self):
        e = episode()
        e["order_events"].append({
            "type": "OrderFilled", "event_id": "E-3",
            "client_order_id": "C-1", "trade_id": "T-3",
        })
        with self.assertRaisesRegex(NautilusPaperBridgeError, "not represented"):
            next_open_paper_session(**e)

    def test_unix_nanoseconds_are_not_float_rounded(self):
        e = episode()
        e["orders"][0]["ts_init"] = 1794261600000000000
        day = next_open_paper_session(**e)
        self.assertEqual(day.buys[0].decided_at, ORDER_AT)


if __name__ == "__main__":
    unittest.main()
