from __future__ import annotations

import json
from decimal import Decimal
from typing import Any

import nautilus_trader
from nautilus_trader.backtest import BacktestEngine
from nautilus_trader.common import LogLevel
from nautilus_trader.config import BacktestEngineConfig, LoggerConfig, StrategyConfig
from nautilus_trader.model import (
    AccountType,
    Bar,
    BarType,
    Money,
    OmsType,
    OrderSide,
    Price,
    Quantity,
    StrategyId,
    Venue,
)
from nautilus_trader.testkit.providers import TestInstrumentProvider
from nautilus_trader.trading import Strategy
from nonlive_effect_qualification import (
    reconcile_nautilus_episode,
    reconcile_unknown_after_submission,
)


class ScenarioStrategy(Strategy):
    def __init__(self, config=None):
        super().__init__(config)
        self.instrument_id = None
        self.bar_type = None
        self.scenario = None
        self.events: list[dict[str, Any]] = []
        self.order_id = None
        self.bar_count = 0

    def on_start(self):
        self.subscribe_bars(self.bar_type)

    def _event(self, kind: str, event=None, **extra):
        row: dict[str, Any] = {"event": kind}
        if event is not None and getattr(event, "client_order_id", None) is not None:
            row["clientOrderId"] = str(event.client_order_id)
        row.update(extra)
        self.events.append(row)

    def on_bar(self, bar):
        self.bar_count += 1
        if self.bar_count == 1:
            instrument = self.cache.instrument(self.instrument_id)
            if self.scenario == "FILL":
                order = self.order_factory.market(self.instrument_id, OrderSide.BUY, instrument.make_qty(Decimal("0.001")))
            elif self.scenario == "PARTIAL_FILL_SLICES":
                order = self.order_factory.market(self.instrument_id, OrderSide.BUY, instrument.make_qty(Decimal("1.000")))
            elif self.scenario == "CANCEL":
                order = self.order_factory.limit(
                    self.instrument_id,
                    OrderSide.BUY,
                    instrument.make_qty(Decimal("0.001")),
                    instrument.make_price(Decimal("10000")),
                )
            elif self.scenario == "DENY":
                order = self.order_factory.market(self.instrument_id, OrderSide.BUY, instrument.make_qty(Decimal("10.000")))
            else:
                raise RuntimeError(self.scenario)
            self.order_id = order.client_order_id
            self._event("SUBMIT", clientOrderId=str(order.client_order_id))
            self.submit_order(order)
        elif self.scenario == "CANCEL" and self.bar_count == 2 and self.order_id is not None:
            self._event("CANCEL_REQUEST", clientOrderId=str(self.order_id))
            self.cancel_order(self.order_id)

    def on_order_submitted(self, event): self._event("SUBMITTED", event)
    def on_order_accepted(self, event): self._event("ACCEPTED", event)
    def on_order_rejected(self, event): self._event("REJECTED", event, reason=str(event.reason))
    def on_order_denied(self, event): self._event("DENIED", event, reason=str(event.reason))
    def on_order_pending_cancel(self, event): self._event("PENDING_CANCEL", event)
    def on_order_canceled(self, event): self._event("CANCELED", event)
    def on_order_filled(self, event): self._event("FILLED", event, lastQty=str(event.last_qty), lastPx=str(event.last_px))


def _bars(bar_type: BarType, volume: str):
    v = Quantity.from_str(volume)
    return [
        Bar(bar_type, Price.from_str("50000.00"), Price.from_str("50100.00"), Price.from_str("49900.00"), Price.from_str("50050.00"), v, 1_000_000_000, 1_000_000_000),
        Bar(bar_type, Price.from_str("50050.00"), Price.from_str("50200.00"), Price.from_str("50000.00"), Price.from_str("50100.00"), v, 2_000_000_000, 2_000_000_000),
        Bar(bar_type, Price.from_str("50100.00"), Price.from_str("50300.00"), Price.from_str("50050.00"), Price.from_str("50200.00"), v, 3_000_000_000, 3_000_000_000),
    ]


def _frame(df):
    if df is None or len(df) == 0:
        return []
    # pandas.to_json converts NaN/NaT to JSON null, keeping the evidence strict JSON.
    return json.loads(df.reset_index().to_json(orient="records", date_format="iso"))


def run_episode(scenario: str) -> dict[str, Any]:
    instrument = TestInstrumentProvider.btcusdt_binance()
    venue = Venue("BINANCE")
    bar_type = BarType.from_str("BTCUSDT.BINANCE-1-MINUTE-LAST-EXTERNAL")
    engine = BacktestEngine(BacktestEngineConfig(logging=LoggerConfig(stdout_level=LogLevel.ERROR)))
    starting = "100000 USDT" if scenario != "DENY" else "100 USDT"
    engine.add_venue(
        venue=venue,
        oms_type=OmsType.NETTING,
        account_type=AccountType.CASH,
        starting_balances=[Money.from_str(starting)],
        liquidity_consumption=(scenario == "PARTIAL_FILL_SLICES"),
    )
    engine.add_instrument(instrument)
    engine.add_data(_bars(bar_type, "0.250000" if scenario == "PARTIAL_FILL_SLICES" else "10.000000"))
    strategy = ScenarioStrategy(StrategyConfig(strategy_id=StrategyId(f"FULLPATH-{scenario}")))
    strategy.instrument_id = instrument.id
    strategy.bar_type = bar_type
    strategy.scenario = scenario
    engine.add_strategy(strategy)
    engine.run()
    episode = {
        "scenario": scenario,
        "events": strategy.events,
        "orders": _frame(engine.generate_orders_report()),
        "fills": _frame(engine.generate_fills_report()),
        "accounts": _frame(engine.generate_account_report(venue=venue)),
    }
    engine.dispose()
    return episode


def main() -> None:
    episodes = {name: run_episode(name) for name in ("FILL", "PARTIAL_FILL_SLICES", "CANCEL", "DENY")}
    qualified: dict[str, Any] = {}
    for name, episode in episodes.items():
        rec = reconcile_nautilus_episode(episode)
        qualified[name] = {"episode": episode, **rec}

    partial_fills = qualified["PARTIAL_FILL_SLICES"]["episode"]["fills"]
    if len(partial_fills) < 2:
        raise SystemExit("liquidity-consumption episode did not produce multiple fill slices")

    unknown = reconcile_unknown_after_submission(client_order_id="NONLIVE-UNKNOWN-1", quantity="0.001")
    qualified["UNKNOWN_AFTER_SUBMISSION"] = unknown

    expected = {
        "FILL": "POST_PENDING_TRANSFER",
        "PARTIAL_FILL_SLICES": "POST_PENDING_TRANSFER",
        "CANCEL": "VOID_PENDING_TRANSFER",
        "DENY": "VOID_PENDING_TRANSFER",
        "UNKNOWN_AFTER_SUBMISSION": "NO_MUTATION",
    }
    observed = {k: v["reconciliation"]["reservationResolution"] for k, v in qualified.items()}
    if observed != expected:
        raise SystemExit(f"effect disposition mismatch: expected={expected} observed={observed}")

    print(json.dumps({
        "schemaVersion": 2,
        "kind": "ordivon.capital.trading.nonlive-effect-matrix",
        "standing": "PASS_NAUTILUS_NONLIVE_EFFECT_RECONCILIATION_MATRIX",
        "provider": "NautilusTrader BacktestEngine simulated exchange",
        "providerVersion": nautilus_trader.__version__,
        "scenarios": qualified,
        "expectedDispositions": expected,
        "observedResolutions": observed,
        "partialFillSliceCount": len(partial_fills),
        "nonLiveProviderWriteAttempted": True,
        "externalFinancialWriteAttempted": False,
        "realMoney": False,
        "liveEndpoint": False,
    }, sort_keys=True))


if __name__ == "__main__":
    main()
