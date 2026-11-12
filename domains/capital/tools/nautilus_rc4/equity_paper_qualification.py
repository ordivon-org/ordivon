"""Synthetic-only rc9 Equity opening-fill -> existing Paper consumer experiment."""
import json
from dataclasses import asdict, dataclass
from datetime import UTC, date, datetime
from decimal import Decimal
from hashlib import sha256

import nautilus_trader
from nautilus_trader.backtest import BacktestEngine
from nautilus_trader.common import LogLevel
from nautilus_trader.config import BacktestEngineConfig, LoggerConfig
from nautilus_trader.execution import FixedFeeModel
from nautilus_trader.model import (
    AccountType,
    Currency,
    Equity,
    InstrumentId,
    Money,
    OmsType,
    OrderFilled,
    OrderSide,
    Price,
    Quantity,
    QuoteTick,
    Symbol,
    Venue,
)
from nautilus_trader.trading import Strategy

from ordivon_capital.accounting.paper_close import PaperBuy, PaperSession, value_session
from ordivon_capital.trading.paper_fill_calendar import admit_paper_session_calendar

USD = Currency.from_str("USD")
PREVIOUS, SESSION, BANK_HOLIDAY, SETTLEMENT = map(
    date.fromisoformat, ("2026-11-09", "2026-11-10", "2026-11-11", "2026-11-12")
)
DECIDED = datetime(2026, 11, 9, 21, 0, tzinfo=UTC)
OPEN = datetime(2026, 11, 10, 14, 30, tzinfo=UTC)
CLOSE = datetime(2026, 11, 10, 21, 0, tzinfo=UTC)
CALENDAR = json.dumps({
    "market_source": "synthetic independent session fixture",
    "clearing_source": "synthetic independent clearing fixture",
    # Synthetic source, with real 2026 market-vs-clearing holiday distinction:
    # NYSE is open Veterans Day; USD bank settlement is closed. No upstream
    # calendar rights/provenance are certified by this fixture.
    "days": [
        {"date": d.isoformat(), "open": "14:30:00Z", "close": "21:00:00Z",
         "clears": d != BANK_HOLIDAY}
        for d in (PREVIOUS, SESSION, BANK_HOLIDAY, SETTLEMENT)
    ],
}).encode()


def minor(value):
    amount = Decimal(str(value)) * 100
    if not amount.is_finite() or amount < 0 or amount != amount.to_integral_value():
        raise ValueError("requires exact nonnegative USD cents")
    return int(amount)


def ns(instant):
    return int(instant.timestamp()) * 1_000_000_000


@dataclass(frozen=True)
class Intent:
    instrument_id: InstrumentId
    shares: int = 2
    decided_at: datetime = DECIDED


def project(events, intent, order_id, expected_identity):
    # Bind the event to the independently queried native Cache and Strategy,
    # not merely the client-order ID present in the event itself.
    if set(expected_identity) != {"account_id", "trader_id", "strategy_id", "venue_order_id"}:
        raise ValueError("missing native identity scope")
    if any(not value or value == "None" for value in expected_identity.values()):
        raise ValueError("native order/account identity is not yet established")
    buys, seen, total = [], set(), 0
    for event in events:
        if (not isinstance(event, OrderFilled) or event.instrument_id != intent.instrument_id
                or event.client_order_id != order_id or event.order_side != OrderSide.BUY
                or event.currency != USD or event.commission.currency != USD
                or any(str(getattr(event, key)) != value for key, value in expected_identity.items())):
            raise ValueError("unbound Equity USD buy fill")
        identity = str(event.trade_id)
        qty = Decimal(str(event.last_qty))
        if identity in seen or qty <= 0 or qty != qty.to_integral_value():
            raise ValueError("duplicate fill or fractional shares")
        total += int(qty)
        if type(intent.shares) is not int or total > intent.shares:
            raise ValueError("fill exceeds frozen target")
        if event.ts_event != ns(OPEN):
            raise ValueError("fill must be at scheduled opening")
        seen.add(identity)
        buys.append(PaperBuy(identity, "SPY", int(qty), minor(event.last_px),
                             minor(event.commission.as_decimal()), intent.decided_at, datetime.fromtimestamp(event.ts_event // 1_000_000_000, UTC), SETTLEMENT))
    if not buys:
        raise ValueError("no opening fill")
    admit_paper_session_calendar(
        CALENDAR, expected_sha256=sha256(CALENDAR).hexdigest(), previous_session=PREVIOUS,
        trade_session=SESSION, fills=((b.decided_at, b.filled_at, b.settlement_date) for b in buys),
    )
    return tuple(buys)


class OpeningStrategy(Strategy):
    def __init__(self, intent):
        super().__init__()
        self.intent, self.events, self.order_id = intent, [], None

    def on_start(self):
        self.subscribe_quotes(self.intent.instrument_id)

    def on_quote(self, tick):
        # Frozen quantity never depends on this or any future quote price.
        if tick.ts_event == ns(OPEN) and self.order_id is None:
            order = self.order_factory.market(self.intent.instrument_id, OrderSide.BUY,
                                              Quantity.from_int(self.intent.shares))
            self.order_id = order.client_order_id
            self.submit_order(order)

    def on_order_filled(self, event):
        self.events.append(event)


def run_episode(fee="0.00", *, opening=True, cash="1000.00", ask="110.02"):
    if nautilus_trader.__version__ != "2.0.0rc9":
        raise ValueError("only rc9 qualified")
    minor(fee)  # Reject sub-cent inputs before upstream Money can round them.
    minor(cash)
    instrument = Equity(InstrumentId.from_str("SPY.PAPER"), Symbol("SPY"), USD,
                        2, Price.from_str("0.01"), 0, 0, lot_size=Quantity.from_int(1))
    intent = Intent(instrument.id)  # Frozen before the next-session input is constructed.
    strategy = OpeningStrategy(intent)
    engine = BacktestEngine(BacktestEngineConfig(logging=LoggerConfig(stdout_level=LogLevel.ERROR)))
    venue = Venue("PAPER")
    try:
        engine.add_venue(venue=venue, oms_type=OmsType.NETTING, account_type=AccountType.CASH,
                         starting_balances=[Money.from_str(f"{cash} USD")],
                         fee_model=FixedFeeModel(Money.from_str(f"{fee} USD")))
        engine.add_instrument(instrument)
        quotes = [(CLOSE, "112.00", "112.00")]
        if opening:
            quotes.insert(0, (OPEN, "110.00", ask))
        engine.add_data([QuoteTick(instrument.id, Price.from_str(bid), Price.from_str(offer),
                                  Quantity.from_int(100), Quantity.from_int(100), ns(t), ns(t))
                         for t, bid, offer in quotes])
        engine.add_strategy(strategy)
        engine.run()
        if strategy.order_id is None:
            raise ValueError("no qualified opening order")
        expected_identity = {
            "account_id": str(engine.cache.account_id(venue)),
            "trader_id": str(strategy.trader_id),
            "strategy_id": str(strategy.strategy_id),
            "venue_order_id": str(engine.cache.venue_order_id(strategy.order_id)),
        }
        buys = project(strategy.events, intent, strategy.order_id, expected_identity)
        previous = value_session(None, PaperSession(PREVIOUS, None, minor(cash), 0, {}, ()))
        paper = value_session(previous, PaperSession(SESSION, PREVIOUS, 0, 0, {"SPY": 11200}, buys))
        native_cash = minor(engine.portfolio.account(venue).balance_total(USD).as_decimal())
        native_nav = minor(engine.portfolio.equity(venue)[USD].as_decimal())
        assert paper.cash_minor - paper.payable_minor == native_cash
        assert paper.nav_minor == native_nav
        assert engine.portfolio.net_position(instrument.id) == sum(b.shares for b in buys)
        # The bank holiday is a trading session, not a settlement date.
        holiday = value_session(paper, PaperSession(
            BANK_HOLIDAY, SESSION, 0, 0, {"SPY": 11200}, ()
        ))
        settled = value_session(holiday, PaperSession(
            SETTLEMENT, BANK_HOLIDAY, 0, 0, {"SPY": 11200}, ()
        ))
        assert holiday.payable_minor == paper.payable_minor
        assert settled.payable_minor == 0
        assert settled.cash_minor == native_cash and settled.nav_minor == native_nav
        return {"standing": "PASS_SYNTHETIC_EQUITY_PAPER", "providerVersion": nautilus_trader.__version__,
                "synthetic": True, "fills": [asdict(b) for b in buys],
                "events": [OrderFilled.to_dict(e) for e in strategy.events],
                "paper": asdict(paper), "nativeCashMinor": native_cash, "nativeNavMinor": native_nav,
                "holidayPayableMinor": holiday.payable_minor,
                "settlementCashMinor": settled.cash_minor, "settlementDate": SETTLEMENT.isoformat(),
                "expectedIdentity": expected_identity}
    finally:
        engine.dispose()


if __name__ == "__main__":
    print(json.dumps([run_episode(fee) for fee in ("0.00", "1.23")], default=str, sort_keys=True))
