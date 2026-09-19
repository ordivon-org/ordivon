from __future__ import annotations

import argparse
from decimal import Decimal, ROUND_DOWN
import hashlib
import json
from pathlib import Path
from typing import Any

from nautilus_trader import backtest, config, model, trading
from nautilus_trader.common import LogLevel
from nautilus_trader.config import LoggerConfig

USDT = model.Currency.from_str("USDT")
BTC = model.Currency.from_str("BTC")
ETH = model.Currency.from_str("ETH")
VENUES = {"OKX": model.Venue("OKX"), "BINANCE": model.Venue("BINANCE")}


def _load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text())
    if not isinstance(value, dict):
        raise RuntimeError(f"expected JSON object: {path}")
    return value


def _floor_to_step(value: Decimal, step: Decimal) -> Decimal:
    return (value / step).to_integral_value(rounding=ROUND_DOWN) * step


def _instrument_specs(meta: dict[str, Any]) -> dict[tuple[str, str], dict[str, Any]]:
    okx = meta["okx"]
    bn = meta["binance"]
    return {
        ("OKX", "BTC"): {
            "symbol": "BTC-USDT", "pricePrecision": 1, "sizePrecision": 8,
            "priceIncrement": okx["btcUsdt"]["tickSize"],
            "sizeIncrement": okx["btcUsdt"]["lotSize"],
            "minQuantity": okx["btcUsdt"]["minSize"],
        },
        ("OKX", "ETH"): {
            "symbol": "ETH-USDT", "pricePrecision": 2, "sizePrecision": 6,
            "priceIncrement": okx["ethUsdt"]["tickSize"],
            "sizeIncrement": okx["ethUsdt"]["lotSize"],
            "minQuantity": okx["ethUsdt"]["minSize"],
        },
        ("BINANCE", "BTC"): {
            "symbol": "BTCUSDT", "pricePrecision": 2, "sizePrecision": 5,
            "priceIncrement": bn["btcUsdt"]["tickSize"],
            "sizeIncrement": bn["btcUsdt"]["lotStepSize"],
            "minQuantity": bn["btcUsdt"]["lotMinQty"],
            "minNotional": bn["btcUsdt"]["minNotional"],
        },
        ("BINANCE", "ETH"): {
            "symbol": "ETHUSDT", "pricePrecision": 2, "sizePrecision": 4,
            "priceIncrement": bn["ethUsdt"]["tickSize"],
            "sizeIncrement": bn["ethUsdt"]["lotStepSize"],
            "minQuantity": bn["ethUsdt"]["lotMinQty"],
            "minNotional": bn["ethUsdt"]["minNotional"],
        },
    }


def _quotes(observation: dict[str, Any]) -> dict[tuple[str, str], tuple[Decimal, Decimal]]:
    q = observation["observation"]["quotes"]
    return {
        ("OKX", "BTC"): (Decimal(q["OKX"]["BTC-USDT"]["bid"]), Decimal(q["OKX"]["BTC-USDT"]["ask"])),
        ("OKX", "ETH"): (Decimal(q["OKX"]["ETH-USDT"]["bid"]), Decimal(q["OKX"]["ETH-USDT"]["ask"])),
        ("BINANCE", "BTC"): (Decimal(q["BINANCE"]["BTCUSDT"]["bid"]), Decimal(q["BINANCE"]["BTCUSDT"]["ask"])),
        ("BINANCE", "ETH"): (Decimal(q["BINANCE"]["ETHUSDT"]["bid"]), Decimal(q["BINANCE"]["ETHUSDT"]["ask"])),
    }


class _MechanicsStrategy(trading.Strategy):
    def __init__(self):
        super().__init__()
        self.specs: dict[tuple[str, str], dict[str, Any]] = {}
        self.quotes: dict[tuple[str, str], tuple[Decimal, Decimal]] = {}
        self.notional = Decimal("10")
        self.sent: set[tuple[str, str]] = set()
        self.fills: dict[str, dict[str, str]] = {}
        self.rejections: dict[str, str] = {}
        self.denials: dict[str, str] = {}

    def on_start(self) -> None:
        for (venue, _asset), spec in self.specs.items():
            iid = model.InstrumentId(model.Symbol(spec["symbol"]), VENUES[venue])
            self.subscribe_quotes(iid)

    def on_quote(self, quote: Any) -> None:
        venue = str(quote.instrument_id.venue)
        symbol = str(quote.instrument_id.symbol)
        asset = "BTC" if "BTC" in symbol else "ETH"
        key = (venue, asset)
        if key in self.sent:
            return
        self.sent.add(key)
        spec = self.specs[key]
        ask = self.quotes[key][1]
        step = Decimal(spec["sizeIncrement"])
        quantity = _floor_to_step(self.notional / ask, step)
        if quantity < Decimal(spec["minQuantity"]):
            raise RuntimeError(f"normalized mechanics quantity below venue minimum: {key}")
        if spec.get("minNotional") and quantity * ask < Decimal(spec["minNotional"]):
            raise RuntimeError(f"normalized mechanics notional below venue minimum: {key}")
        instrument = self.cache.instrument(quote.instrument_id)
        if instrument is None:
            raise RuntimeError(f"instrument missing from cache: {quote.instrument_id}")
        venue_quantity = instrument.make_qty(float(quantity))
        order = self.order_factory.market(
            quote.instrument_id,
            model.OrderSide.BUY,
            venue_quantity,
            time_in_force=model.TimeInForce.IOC,
            client_order_id=model.ClientOrderId(f"MECH-{venue}-{asset}"),
            tags=["SIMULATION_ONLY", "MECHANICS_ONLY", "NON_ECONOMIC"],
        )
        self.submit_order(order)

    def on_order_filled(self, event: Any) -> None:
        self.fills[str(event.client_order_id)] = {
            "lastQty": str(event.last_qty),
            "lastPx": str(event.last_px),
        }

    def on_order_rejected(self, event: Any) -> None:
        self.rejections[str(event.client_order_id)] = str(event.reason)

    def on_order_denied(self, event: Any) -> None:
        self.denials[str(event.client_order_id)] = str(event.reason)


def simulate(config_path: Path, observation_path: Path, metadata_path: Path) -> dict[str, Any]:
    cfg = _load(config_path)
    observation = _load(observation_path)
    metadata = _load(metadata_path)
    if cfg.get("standing") != "LOCAL_SIMULATION_ONLY" or cfg.get("purpose") != "MECHANICS_ONLY_NON_ECONOMIC":
        raise RuntimeError("crypto mechanics config is not simulation-only")
    for key in ("brokerConnectivityAllowed", "brokerCredentialsAllowed", "externalFinancialWritesAllowed", "economicDecisionClaimed", "alphaClaimed"):
        if cfg.get(key) is not False:
            raise RuntimeError(f"{key} must remain false")
    if not observation.get("conclusion", {}).get("boundedContemporaneousComparisonQualified"):
        raise RuntimeError("source public observation is not qualified")

    specs = _instrument_specs(metadata)
    quotes = _quotes(observation)
    engine = backtest.BacktestEngine(config.BacktestEngineConfig(logging=LoggerConfig(stdout_level=LogLevel.ERROR)))
    for venue in VENUES.values():
        engine.add_venue(
            venue,
            model.OmsType.NETTING,
            model.AccountType.CASH,
            [model.Money.from_str(f"{cfg['startingCashUsdtPerVenue']} USDT")],
            base_currency=None,
            use_market_order_acks=True,
        )

    base_ns = 1_789_310_700_000_000_000
    normalized_quotes: dict[str, Any] = {}
    for idx, ((venue, asset), spec) in enumerate(specs.items()):
        iid = model.InstrumentId(model.Symbol(spec["symbol"]), VENUES[venue])
        base_ccy = BTC if asset == "BTC" else ETH
        kwargs: dict[str, Any] = {}
        if spec.get("minNotional"):
            kwargs["min_notional"] = model.Money.from_str(f"{spec['minNotional']} USDT")
        price_increment = format(Decimal(spec["priceIncrement"]), f".{spec['pricePrecision']}f")
        size_increment = format(Decimal(spec["sizeIncrement"]), f".{spec['sizePrecision']}f")
        min_quantity = format(Decimal(spec["minQuantity"]), f".{spec['sizePrecision']}f")
        instrument = model.CurrencyPair(
            iid,
            model.Symbol(spec["symbol"]),
            base_ccy,
            USDT,
            spec["pricePrecision"],
            spec["sizePrecision"],
            model.Price.from_str(price_increment),
            model.Quantity.from_str(size_increment),
            0,
            0,
            min_quantity=model.Quantity.from_str(min_quantity),
            **kwargs,
        )
        engine.add_instrument(instrument)
        bid, ask = quotes[(venue, asset)]
        bid_s = format(bid, f".{spec['pricePrecision']}f")
        ask_s = format(ask, f".{spec['pricePrecision']}f")
        size_s = format(Decimal("100"), f".{spec['sizePrecision']}f")
        ts = base_ns + idx
        engine.add_data([
            model.QuoteTick(
                iid,
                model.Price.from_str(bid_s),
                model.Price.from_str(ask_s),
                model.Quantity.from_str(size_s),
                model.Quantity.from_str(size_s),
                ts,
                ts,
            )
        ])
        normalized_quotes[f"{venue}:{asset}"] = {"bid": bid_s, "ask": ask_s}

    strategy = _MechanicsStrategy()
    strategy.specs = specs
    strategy.quotes = quotes
    strategy.notional = Decimal(cfg["syntheticNotionalUsdtPerInstrument"])
    engine.add_strategy(strategy)
    engine.run()

    orders = []
    for order in sorted(engine.cache.orders(), key=lambda x: str(x.instrument_id)):
        orders.append({
            "clientOrderId": str(order.client_order_id),
            "instrumentId": str(order.instrument_id),
            "quantity": str(order.quantity),
            "timeInForce": str(order.time_in_force),
            "status": str(order.status),
            "filledQty": str(order.filled_qty),
        })
    if len(orders) != 4 or any(x["status"] != "FILLED" or x["filledQty"] != x["quantity"] for x in orders):
        raise RuntimeError(f"crypto mechanics simulation did not fill exactly four intents: orders={orders} denials={strategy.denials} rejections={strategy.rejections}")
    if strategy.rejections or strategy.denials or len(strategy.fills) != 4:
        raise RuntimeError("unexpected crypto mechanics lifecycle outcome")

    return {
        "schemaVersion": 1,
        "kind": "ordivon.capital.market.crypto-shadow-mechanics-result",
        "standing": "PASS_LOCAL_CRYPTO_SPOT_OMS_MECHANICS",
        "purpose": cfg["purpose"],
        "sourceObservationSha256": hashlib.sha256(observation_path.read_bytes()).hexdigest(),
        "sourceMetadataSha256": hashlib.sha256(metadata_path.read_bytes()).hexdigest(),
        "syntheticNotionalUsdtPerInstrument": cfg["syntheticNotionalUsdtPerInstrument"],
        "normalizedQuotes": normalized_quotes,
        "orders": orders,
        "fills": strategy.fills,
        "multiCurrencyCashAccountUsed": True,
        "instrumentRulesApplied": True,
        "brokerConnected": False,
        "brokerCredentialsUsed": False,
        "externalFinancialWritesAttempted": False,
        "economicDecisionClaimed": False,
        "alphaClaimed": False,
        "demoExecutionAttempted": False,
        "liveExecutionAttempted": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument("--observation", required=True, type=Path)
    parser.add_argument("--metadata", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    result = simulate(args.config, args.observation, args.metadata)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
