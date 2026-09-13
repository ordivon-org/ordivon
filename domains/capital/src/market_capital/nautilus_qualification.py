from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any
from decimal import Decimal

from nautilus_trader import backtest, config, model, trading
from nautilus_trader.common import LogLevel
from nautilus_trader.config import LoggerConfig
import nautilus_trader

SIM = model.Venue("SIM")
USD = model.Currency.from_str("USD")


def _load(path: Path) -> dict[str, Any]:
    doc = json.loads(path.read_text())
    if not isinstance(doc, dict):
        raise RuntimeError(f"expected JSON object: {path}")
    return doc


def _specs(precommit: dict[str, Any]) -> dict[str, dict[str, Any]]:
    if precommit.get("standing") != "SHADOW_ORDER_PRECOMMIT_FROZEN":
        raise RuntimeError("M6 precommit is not frozen")
    if precommit.get("brokerCredentialsUsed") or precommit.get("externalFinancialWritesAttempted"):
        raise RuntimeError("M6 precommit violated non-live boundary")
    shadows = {x["symbol"]: x for x in precommit["shadowOrders"]}
    fixes = {x["symbol"]: x for x in precommit["fixIntents"]}
    if set(shadows) != {"AAPL", "MSFT", "NVDA"} or set(fixes) != set(shadows):
        raise RuntimeError("unexpected frozen M6 symbol set")
    out: dict[str, dict[str, Any]] = {}
    for symbol in sorted(shadows):
        sh, fx = shadows[symbol], fixes[symbol]
        if sh["quantity"] != fx["orderQty"] or sh["clOrdId"] != fx["clOrdId"]:
            raise RuntimeError(f"M6 shadow/FIX identity mismatch: {symbol}")
        if fx["ordType"] != "1" or fx["timeInForce"] != "2":
            raise RuntimeError(f"M6 semantics drift: {symbol}")
        out[symbol] = {
            "symbol": symbol,
            "quantity": int(sh["quantity"]),
            "clientOrderId": sh["clOrdId"],
            "fixSha256": fx["sha256"],
            "pricingClose": sh["pricingClose"],
            "fixTimeInForce": fx["timeInForce"],
        }
    return out


def _engine(specs: dict[str, dict[str, Any]]) -> backtest.BacktestEngine:
    engine = backtest.BacktestEngine(
        config.BacktestEngineConfig(logging=LoggerConfig(stdout_level=LogLevel.ERROR)),
    )
    engine.add_venue(
        SIM,
        model.OmsType.NETTING,
        model.AccountType.CASH,
        [model.Money.from_str("100000 USD")],
        base_currency=USD,
        use_market_order_acks=True,
    )
    base_ns = 1_789_392_600_000_000_000
    for offset, symbol in enumerate(sorted(specs)):
        row = specs[symbol]
        iid = model.InstrumentId(model.Symbol(symbol), SIM)
        engine.add_instrument(
            model.Equity(
                iid,
                model.Symbol(symbol),
                USD,
                2,
                model.Price.from_str("0.01"),
                0,
                0,
                lot_size=model.Quantity.from_int(1),
            ),
        )
        normalized = Decimal(str(row["pricingClose"])).quantize(Decimal("0.01"))
        px = model.Price.from_str(format(normalized, ".2f"))
        ts = base_ns + offset
        engine.add_data(
            [
                model.QuoteTick(
                    iid,
                    px,
                    px,
                    model.Quantity.from_int(2_000_000),
                    model.Quantity.from_int(2_000_000),
                    ts,
                    ts,
                ),
            ],
        )
    return engine


class _FrozenStrategy(trading.Strategy):
    def __init__(self):
        super().__init__()
        self.specs: dict[str, dict[str, Any]] = {}
        self.tif: Any = model.TimeInForce.DAY
        self.sent: set[str] = set()
        self.rejections: dict[str, str] = {}
        self.denials: dict[str, str] = {}
        self.fills: dict[str, dict[str, str]] = {}

    def on_start(self) -> None:
        for symbol in self.specs:
            self.subscribe_quotes(model.InstrumentId(model.Symbol(symbol), SIM))

    def on_quote(self, quote: Any) -> None:
        symbol = str(quote.instrument_id.symbol)
        if symbol in self.sent:
            return
        self.sent.add(symbol)
        row = self.specs[symbol]
        order = self.order_factory.market(
            quote.instrument_id,
            model.OrderSide.BUY,
            model.Quantity.from_int(row["quantity"]),
            time_in_force=self.tif,
            client_order_id=model.ClientOrderId(row["clientOrderId"]),
            tags=["M6_FROZEN_QUALIFICATION"],
        )
        self.submit_order(order)

    def on_order_rejected(self, event: Any) -> None:
        self.rejections[str(event.client_order_id)] = str(event.reason)

    def on_order_denied(self, event: Any) -> None:
        self.denials[str(event.client_order_id)] = str(event.reason)

    def on_order_filled(self, event: Any) -> None:
        self.fills[str(event.client_order_id)] = {
            "lastQty": str(event.last_qty),
            "lastPx": str(event.last_px),
        }


class _RiskNegativeStrategy(trading.Strategy):
    def __init__(self):
        super().__init__()
        self.iid: Any = None
        self.done = False
        self.reason: str | None = None

    def on_start(self) -> None:
        self.subscribe_quotes(self.iid)

    def on_quote(self, quote: Any) -> None:
        if self.done:
            return
        self.done = True
        self.submit_order(
            self.order_factory.market(
                self.iid,
                model.OrderSide.BUY,
                model.Quantity.from_int(1_000_000),
                time_in_force=model.TimeInForce.DAY,
                client_order_id=model.ClientOrderId("NEGATIVE-CASH-LIMIT"),
            ),
        )

    def on_order_denied(self, event: Any) -> None:
        self.reason = str(event.reason)


def _run_frozen(specs: dict[str, dict[str, Any]], tif: Any) -> tuple[_FrozenStrategy, list[dict[str, str]]]:
    engine = _engine(specs)
    strategy = _FrozenStrategy()
    strategy.specs = specs
    strategy.tif = tif
    engine.add_strategy(strategy)
    engine.run()
    orders = []
    for order in sorted(engine.cache.orders(), key=lambda x: str(x.instrument_id)):
        orders.append(
            {
                "symbol": str(order.instrument_id.symbol),
                "clientOrderId": str(order.client_order_id),
                "quantity": str(order.quantity),
                "timeInForce": str(order.time_in_force),
                "status": str(order.status),
                "filledQty": str(order.filled_qty),
            },
        )
    return strategy, orders


def _run_risk_negative(specs: dict[str, dict[str, Any]]) -> dict[str, str]:
    engine = _engine({"AAPL": specs["AAPL"]})
    iid = model.InstrumentId(model.Symbol("AAPL"), SIM)
    strategy = _RiskNegativeStrategy()
    strategy.iid = iid
    engine.add_strategy(strategy)
    engine.run()
    order = engine.cache.orders()[0]
    if str(order.status) != "DENIED" or not strategy.reason:
        raise RuntimeError("RiskEngine negative control was not denied")
    if "NOTIONAL_EXCEEDS_FREE_BALANCE" not in strategy.reason:
        raise RuntimeError(f"unexpected RiskEngine denial: {strategy.reason}")
    return {
        "clientOrderId": str(order.client_order_id),
        "quantity": str(order.quantity),
        "status": str(order.status),
        "reason": strategy.reason,
    }


def qualify(precommit_path: Path) -> dict[str, Any]:
    precommit = _load(precommit_path)
    specs = _specs(precommit)

    at_open_strategy, at_open_orders = _run_frozen(specs, model.TimeInForce.AT_THE_OPEN)
    if any(x["timeInForce"] != "AT_THE_OPEN" for x in at_open_orders):
        raise RuntimeError("Nautilus order model did not preserve AT_THE_OPEN")
    for row in at_open_orders:
        src = specs[row["symbol"]]
        if row["clientOrderId"] != src["clientOrderId"] or row["quantity"] != str(src["quantity"]):
            raise RuntimeError(f"Nautilus changed frozen order identity: {row['symbol']}")
    unsupported = {
        cid: reason
        for cid, reason in at_open_strategy.rejections.items()
        if "AT_THE_OPEN is not currently supported" in reason
    }
    if len(unsupported) != 3:
        raise RuntimeError(f"unexpected AT_THE_OPEN qualification outcome: {at_open_strategy.rejections}")

    day_strategy, day_orders = _run_frozen(specs, model.TimeInForce.DAY)
    if any(x["status"] != "FILLED" or x["filledQty"] != x["quantity"] for x in day_orders):
        raise RuntimeError(f"DAY lifecycle control did not fill: {day_orders}")
    if len(day_strategy.fills) != 3:
        raise RuntimeError("DAY lifecycle did not produce three fill events")

    negative = _run_risk_negative(specs)
    return {
        "schemaVersion": 1,
        "kind": "ordivon.market-capital.nautilus-qualification",
        "standing": "PARTIAL_PASS_OMS_RISK_BLOCKED_AT_OPEN_SIMULATION",
        "candidate": {
            "name": "NautilusTrader",
            "version": nautilus_trader.__version__,
        },
        "sourceM6PrecommitSha256": hashlib.sha256(precommit_path.read_bytes()).hexdigest(),
        "frozenIdentityPreserved": True,
        "frozenQuantities": {s: str(specs[s]["quantity"]) for s in sorted(specs)},
        "frozenClientOrderIds": {s: specs[s]["clientOrderId"] for s in sorted(specs)},
        "frozenFixDigests": {s: specs[s]["fixSha256"] for s in sorted(specs)},
        "syntheticQuoteNormalization": "USD equity price normalized to instrument tick 0.01; M6 order identity unchanged",
        "requestedTimeInForce": "AT_THE_OPEN",
        "orderModelRepresentsAtTheOpen": True,
        "simulatedVenueAtTheOpen": {
            "standing": "BLOCKED_UNSUPPORTED_TIF",
            "orders": at_open_orders,
            "rejections": unsupported,
        },
        "dayLifecycleControl": {
            "standing": "PASS_INITIALIZED_SUBMITTED_ACCEPTED_FILLED",
            "orders": day_orders,
            "fills": day_strategy.fills,
        },
        "riskNegativeControl": {
            "standing": "PASS_DENIED_EXCESS_NOTIONAL",
            **negative,
        },
        "brokerConnected": False,
        "brokerCredentialsUsed": False,
        "externalFinancialWritesAttempted": False,
        "m7CausalAcceptanceClaimed": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--precommit", required=True, type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = qualify(args.precommit)
    rendered = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered)
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
