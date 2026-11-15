"""Independent Finance R3 consumer falsifiers; stdlib only, no orders or PG writes."""
from __future__ import annotations

import unittest
from copy import deepcopy
from decimal import Decimal

from test_nautilus_paper_bridge import episode

from ordivon_capital.trading.nautilus_paper_bridge import (
    NautilusPaperBridgeError,
    next_open_paper_session,
)


class FinanceR3AgentBBoundaryTests(unittest.TestCase):
    def test_two_native_accounts_cannot_enter_one_paper_account(self):
        case = episode()
        second_order = deepcopy(case["orders"][0])
        second_order.update(client_order_id="C-2", account_id="A-OTHER")
        second_fill = deepcopy(case["fills"][0])
        second_fill.update(client_order_id="C-2", trade_id="T-2", event_id="E-2", account_id="A-OTHER")
        second_event = deepcopy(case["order_events"][0])
        second_event.update(client_order_id="C-2", trade_id="T-2", event_id="E-2")
        case["orders"].append(second_order)
        case["fills"].append(second_fill)
        case["order_events"].append(second_event)
        case["decisions_by_order"]["C-2"] = case["decisions_by_order"]["C-1"]
        with self.assertRaises(NautilusPaperBridgeError):
            next_open_paper_session(**case)

    def test_native_event_account_instrument_side_cannot_disagree_with_fill(self):
        for key, contradictory in (
            ("account_id", "A-OTHER"),
            ("instrument_id", "QQQ.XNAS"),
            ("order_side", "SELL"),
            ("currency", "EUR"),
        ):
            with self.subTest(key=key):
                case = episode()
                event = case["order_events"][0]
                event.update(
                    account_id="A-001", instrument_id="SPY.XNAS",
                    order_side="BUY", currency="USD",
                )
                event[key] = contradictory
                with self.assertRaises(NautilusPaperBridgeError):
                    next_open_paper_session(**case)

    def test_native_event_uuid_must_match_same_run_fill_report(self):
        case = episode()
        case["fills"][0]["event_id"] = "E-ANOTHER-RUN"
        with self.assertRaisesRegex(NautilusPaperBridgeError, "event identity"):
            next_open_paper_session(**case)

    def test_native_report_dataframe_client_order_index_round_trips(self):
        try:
            import pandas as pd
        except ImportError:
            self.skipTest("native optional pandas is not installed in core Python")
        case = episode()
        case["orders"] = pd.DataFrame(case["orders"]).set_index("client_order_id")
        case["fills"] = pd.DataFrame(case["fills"]).set_index("client_order_id")
        day = next_open_paper_session(**case)
        self.assertEqual(day.buys[0].fill_id, "nautilus-paper:A-001:T-1")
        self.assertEqual(day.buys[0].cost_minor, 100012)
        case["fills"].index.name = "not_client_order_id"
        with self.assertRaisesRegex(NautilusPaperBridgeError, "index"):
            next_open_paper_session(**case)

    def test_correct_close_forecast_can_lose_money_at_next_open(self):
        # Decision after t close predicts the close[t+1]/close[t] return exactly.
        # Its trade is filled at next open, not at the previous close.
        close_t = Decimal("100")
        open_next = Decimal("120")
        close_next = Decimal("110")
        forecast_label = close_next / close_t - 1
        attainable_share_return = close_next / open_next - 1
        capital = Decimal("1000")
        shares = capital // open_next
        execution_nav = capital - shares * open_next + shares * close_next
        theoretical_close_to_close_nav = capital * (1 + forecast_label)
        self.assertEqual(forecast_label, Decimal("0.1"))
        self.assertLess(attainable_share_return, 0)
        self.assertEqual(execution_nav, Decimal("920"))
        self.assertEqual(theoretical_close_to_close_nav, Decimal("1100"))
        self.assertNotEqual(execution_nav, theoretical_close_to_close_nav)



class _NativeEvent:
    def __init__(self, record: dict):
        self.record = record

    def to_dict(self):
        return deepcopy(self.record)


class OrderFilled(_NativeEvent):
    pass


class OrderInitialized(_NativeEvent):
    pass


class OrderCanceled(_NativeEvent):
    pass


class OrderAccepted(_NativeEvent):
    pass


class _NativeOrder:
    def __init__(self, client_id, events):
        self.client_order_id = client_id
        self._events = events

    def events(self):
        return self._events


class _NativeCache:
    def __init__(self, orders):
        self._orders = orders

    def orders(self):
        return self._orders


class _NativeNode:
    def __init__(self, scenario, native_orders=None):
        self.scenario = deepcopy(scenario)
        for order in self.scenario["orders"]:
            count = sum(int(f["last_qty"]) for f in self.scenario["fills"]
                        if f["client_order_id"] == order["client_order_id"])
            order.setdefault("quantity", str(max(1, count)))
            order.setdefault("filled_qty", str(count))
            order.setdefault("status", "FILLED" if count == int(order["quantity"]) else "CANCELED")
        self._orders = native_orders if native_orders is not None else [
            _NativeOrder("C-1", [
                OrderInitialized({"type": "OrderInitialized", "client_order_id": "C-1"}),
                OrderFilled(scenario["order_events"][0]),
            ])
        ]

    def generate_orders_report(self, config_id):
        if config_id != "RUN-1":
            raise KeyError("unknown native run")
        return self.scenario["orders"]

    def generate_fills_report(self, config_id):
        if config_id != "RUN-1":
            raise KeyError("unknown native run")
        return self.scenario["fills"]

    def get_engine_cache(self, config_id):
        if config_id != "RUN-1":
            raise KeyError("unknown native run")
        return _NativeCache(self._orders)


class FinanceR3AgentBNativeSourceTests(unittest.TestCase):
    def test_retained_native_run_can_witness_next_open_paper(self):
        from ordivon_capital.trading.nautilus_paper_bridge import next_open_native_paper_session
        e = episode()
        node = _NativeNode(e)
        args = {key: value for key, value in e.items() if key not in ("orders", "fills", "order_events")}
        result = next_open_native_paper_session(node=node, run_config_id="RUN-1", **args)
        self.assertEqual(result.buys[0].fill_id, "nautilus-paper:A-001:T-1")
        self.assertEqual(result.buys[0].cost_minor, 100012)

    def test_report_cannot_drop_an_order_retained_in_native_cache(self):
        from ordivon_capital.trading.nautilus_paper_bridge import next_open_native_paper_session
        e = episode()
        node = _NativeNode(e)
        node._orders.append(_NativeOrder("C-2", [
            OrderInitialized({"type": "OrderInitialized", "client_order_id": "C-2"}),
        ]))
        args = {key: value for key, value in e.items() if key not in ("orders", "fills", "order_events")}
        with self.assertRaisesRegex(NautilusPaperBridgeError, "inventories disagree"):
            next_open_native_paper_session(node=node, run_config_id="RUN-1", **args)

    def test_incomplete_event_history_and_disposed_engine_fail_closed(self):
        from ordivon_capital.trading.nautilus_paper_bridge import next_open_native_paper_session
        e = episode()
        args = {key: value for key, value in e.items() if key not in ("orders", "fills", "order_events")}
        node = _NativeNode(e)
        node._orders[0]._events.pop()
        with self.assertRaisesRegex(NautilusPaperBridgeError, "event history|terminal.*event"):
            next_open_native_paper_session(node=node, run_config_id="RUN-1", **args)
        node._orders.clear()
        with self.assertRaisesRegex(NautilusPaperBridgeError, "empty native cache"):
            next_open_native_paper_session(node=node, run_config_id="RUN-1", **args)

    def test_native_order_quantity_conserves_all_report_fills(self):
        from ordivon_capital.trading.nautilus_paper_bridge import next_open_native_paper_session
        for field, value in (("filled_qty", "1"), ("filled_qty", "3"), ("quantity", "1")):
            with self.subTest(field=field, value=value):
                e = episode()
                node = _NativeNode(e)
                node.scenario["orders"][0][field] = value
                args = {k: v for k, v in e.items() if k not in ("orders", "fills", "order_events")}
                with self.assertRaisesRegex(NautilusPaperBridgeError, "filled quantity and fill reports"):
                    next_open_native_paper_session(node=node, run_config_id="RUN-1", **args)

    def test_unfilled_native_order_with_zero_report_qty_remains_valid(self):
        from ordivon_capital.trading.nautilus_paper_bridge import next_open_native_paper_session
        e = episode()
        node = _NativeNode(e)
        node.scenario["orders"].append({
            "client_order_id": "C-UNFILLED", "account_id": "A-001",
            "instrument_id": "SPY.XNAS", "quantity": "1", "filled_qty": "0",
            "status": "CANCELED", "ts_init": e["orders"][0]["ts_init"],
        })
        node._orders.append(_NativeOrder("C-UNFILLED", [
            OrderInitialized({"type": "OrderInitialized", "client_order_id": "C-UNFILLED"}),
            OrderCanceled({"type": "OrderCanceled", "client_order_id": "C-UNFILLED"}),
        ]))
        args = {k: v for k, v in e.items() if k not in ("orders", "fills", "order_events")}
        result = next_open_native_paper_session(node=node, run_config_id="RUN-1", **args)
        self.assertEqual(len(result.buys), 1)


    def test_native_canceled_order_without_fills_is_verified_zero_economic_effect(self):
        import pandas as pd

        from ordivon_capital.trading.nautilus_paper_bridge import next_open_native_paper_session
        e = episode()
        e["fills"] = []
        e["order_events"] = []
        event = OrderCanceled({"type": "OrderCanceled", "client_order_id": "C-1"})
        node = _NativeNode(e, native_orders=[_NativeOrder("C-1", [
            OrderInitialized({"type": "OrderInitialized", "client_order_id": "C-1"}),
            event,
        ])])
        node.scenario["fills"] = pd.DataFrame()  # actual native empty report: unnamed index, no columns
        node.scenario["orders"][0].update(quantity="1", filled_qty="0", status="CANCELED")
        args = {k: v for k, v in e.items() if k not in ("orders", "fills", "order_events")}
        day = next_open_native_paper_session(node=node, run_config_id="RUN-1", **args)
        self.assertEqual(day.buys, ())
        self.assertEqual(day.sells, ())

    def test_native_unfinished_order_cannot_be_silently_booked_as_zero_fill(self):
        import pandas as pd

        from ordivon_capital.trading.nautilus_paper_bridge import next_open_native_paper_session
        e = episode()
        e["fills"] = []
        e["order_events"] = []
        node = _NativeNode(e, native_orders=[_NativeOrder("C-1", [
            OrderInitialized({"type": "OrderInitialized", "client_order_id": "C-1"}),
            OrderAccepted({"type": "OrderAccepted", "client_order_id": "C-1"}),
        ])])
        node.scenario["fills"] = pd.DataFrame()
        node.scenario["orders"][0].update(quantity="1", filled_qty="0", status="ACCEPTED")
        args = {k: v for k, v in e.items() if k not in ("orders", "fills", "order_events")}
        with self.assertRaisesRegex(NautilusPaperBridgeError, "nonterminal"):
            next_open_native_paper_session(node=node, run_config_id="RUN-1", **args)

    def test_native_canceled_report_requires_cached_cancel_event(self):
        import pandas as pd

        from ordivon_capital.trading.nautilus_paper_bridge import next_open_native_paper_session
        e = episode()
        e["fills"] = []
        e["order_events"] = []
        node = _NativeNode(e, native_orders=[_NativeOrder("C-1", [
            OrderInitialized({"type": "OrderInitialized", "client_order_id": "C-1"}),
        ])])
        node.scenario["fills"] = pd.DataFrame()
        node.scenario["orders"][0].update(quantity="1", filled_qty="0", status="CANCELED")
        args = {k: v for k, v in e.items() if k not in ("orders", "fills", "order_events")}
        with self.assertRaisesRegex(NautilusPaperBridgeError, "terminal.*event"):
            next_open_native_paper_session(node=node, run_config_id="RUN-1", **args)

    def test_native_partially_filled_open_order_requires_different_consumer(self):
        from ordivon_capital.trading.nautilus_paper_bridge import next_open_native_paper_session
        e = episode()
        node = _NativeNode(e)
        node.scenario["orders"][0].update(quantity="3", filled_qty="2", status="PARTIALLY_FILLED")
        args = {k: v for k, v in e.items() if k not in ("orders", "fills", "order_events")}
        with self.assertRaisesRegex(NautilusPaperBridgeError, "nonterminal"):
            next_open_native_paper_session(node=node, run_config_id="RUN-1", **args)

    def test_native_event_is_proven_to_belong_to_cached_order(self):
        from ordivon_capital.trading.nautilus_paper_bridge import next_open_native_paper_session
        e = episode()
        node = _NativeNode(e)
        node._orders[0]._events[1].record["client_order_id"] = "C-OTHER"
        args = {key: value for key, value in e.items() if key not in ("orders", "fills", "order_events")}
        with self.assertRaisesRegex(NautilusPaperBridgeError, "different cached order"):
            next_open_native_paper_session(node=node, run_config_id="RUN-1", **args)


if __name__ == "__main__":
    unittest.main()
