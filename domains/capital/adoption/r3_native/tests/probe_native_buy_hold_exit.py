"""Real Qlib OOS score -> existing Portfolio budget -> native Nautilus/Paper.

Executable *simulation*, using frozen model output, not alpha evidence,
historically proven PIT, real broker authority or production PG posting.
"""
from __future__ import annotations

import csv
from hashlib import sha256
import json
import os
import sys
from datetime import UTC, date, datetime, time
from decimal import Decimal
from io import StringIO
from pathlib import Path
from zoneinfo import ZoneInfo

if sys.flags.optimize:
    raise RuntimeError("Financial acceptance assertions require normal Python mode")

from nautilus_trader.backtest import BacktestNode
from nautilus_trader.common import LogLevel
from nautilus_trader.config import (
    BacktestDataConfig, BacktestEngineConfig, BacktestRunConfig,
    BacktestVenueConfig, DataCatalogConfig, LoggerConfig,
)
from nautilus_trader.execution import DefaultFillModel, MakerTakerFeeModel
from nautilus_trader.model import (
    AccountType, BookType, Currency, Equity, InstrumentId, NautilusDataType,
    OmsType, OrderSide, Price, Quantity, QuoteTick, Symbol, TimeInForce,
)
from nautilus_trader.persistence import ParquetDataCatalog
from nautilus_trader.trading import Strategy, StrategyConfig
from ordivon_capital.accounting.paper_close import PaperSession, value_session
from ordivon_capital.trading.nautilus_paper_bridge import next_open_paper_session
from ordivon_capital.portfolio.strategic_contribution import plan_strategic_contribution

HOLD = int(os.environ["ORDIVON_FINANCE_R3_HOLD_SESSIONS"])
if HOLD not in (5, 20):
    raise ValueError("Only preregistered 5/20-session research hypotheses are tested")
NO_ENTRY = os.environ.get("ORDIVON_FINANCE_R3_TEST_NO_ENTRY") == "1"
NO_EXIT = os.environ.get("ORDIVON_FINANCE_R3_TEST_NO_EXIT") == "1"
# The research output is actually produced by the installed Qlib 0.9.7
# DatasetH/LightGBM/Recorder, and it determines the native instrument.
# No fabricated score or strategy event passes as a model prediction.
DECISION_DAY = os.environ.get("ORDIVON_FINANCE_R3_DECISION_DAY", "2025-10-01")
RESEARCH = Path(os.environ["ORDIVON_FINANCE_R3_RESEARCH_OUT_DIR"])
MODEL_STUDY = json.loads((RESEARCH / "native_study_result.json").read_text(encoding="utf-8"))
if (MODEL_STUDY.get("signal_quality", {}).get("holding_sessions") != HOLD
        or MODEL_STUDY.get("portfolio_target") is not None
        or MODEL_STUDY.get("forecast", {}).get("point_in_time_eligible") is not False):
    raise RuntimeError("Qlib study not the requested simulation-only holding horizon")
if (MODEL_STUDY.get("signal_quality", {}).get("exit_price_kind") != "next_open"
        or MODEL_STUDY.get("signal_quality", {}).get("matches_native_fixed_holding_exit_event") is not True
        or MODEL_STUDY.get("forecast", {}).get("native_strategy_exit_event_matches_target") is not True):
    raise RuntimeError("Qlib exit label must match native T+H+1 OPEN sale")
with (RESEARCH / "qlib_test_predictions.csv").open(newline="", encoding="utf-8") as fp:
    signal_rows = [
        row for row in csv.DictReader(fp) if row["datetime"] == DECISION_DAY
    ]
if len(signal_rows) != 3 or {r["instrument"] for r in signal_rows} != {"IWM", "QQQ", "SPY"}:
    raise RuntimeError("Qlib predicted test day/ETF universe not exact")
from math import isfinite
scores = {r["instrument"]: float(next(v for k, v in r.items()
                                  if k not in {"datetime", "instrument"}))
          for r in signal_rows}
if not all(isfinite(v) for v in scores.values()):
    raise RuntimeError("Qlib decision contains nonfinite OOS scores")
# Explicit adversarial *test-only* score intervention, never represented as
# real Qlib output. Tests that changing a decision changes the native fill.
override = os.environ.get("ORDIVON_FINANCE_R3_TEST_FORCE_ASSET")
if override is not None:
    if override not in scores:
        raise ValueError("Counterfactual must use an existing captured ETF")
    scores[override] = max(scores.values()) + 1.0
SYMBOL = min(scores, key=lambda sym: (-scores[sym], sym))
SOURCE = Path(os.environ["ORDIVON_FINANCE_R3_CAPTURE_DIR"]) / f"openbb_cboe_{SYMBOL}_normalized.csv"
MANIFEST = Path(os.environ["ORDIVON_FINANCE_R3_SOURCE_MANIFEST"])
OUT = Path(os.environ["ORDIVON_FINANCE_R3_RUN_OUT_DIR"])
# Never mistake a prior successful Paper receipt for this failed/new run.
if OUT.is_dir() and any(OUT.iterdir()):
    raise RuntimeError("Native Paper simulation requires a fresh empty output directory")
OUT.mkdir(parents=True, exist_ok=True)
# Reuse existing Portfolio economic budget, not a second position sizer.
# This is a read-only plan: the Qlib-selected ETF does not grant order rights.
allocation = plan_strategic_contribution({
    "schemaVersion": 1,
    "kind": "ordivon.finance.portfolio.strategic-contribution-request",
    "currency": "USD",
    "cashMinor": 1_000_000,
    "protectedReserveMinor": 900_000,
    "contributionMinor": 100_000,
    "holdingsMinor": {SYMBOL: 0},
    "targetWeightsBps": {SYMBOL: 10_000},
})
if (allocation["allocationsMinor"][SYMBOL] != 100_000
        or allocation["protectedReserveMinor"] != 900_000
        or allocation["executionAuthorized"] is not False):
    raise RuntimeError("Existing Portfolio sleeve/reserve was not preserved")

# Reuse the existing immutable research capture receipt; no competing
# external data acquisition or historical PIT attestation is introduced.
source_bytes = SOURCE.read_bytes()
manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
asset_receipts = [
    r for r in manifest.get("provider_receipts", [])
    if r.get("symbol") == SYMBOL and r.get("provider") == "cboe"
]
if len(asset_receipts) != 1 or asset_receipts[0].get("normalized_sha256") != sha256(source_bytes).hexdigest():
    raise ValueError("QLib-selected ETF source differs from the captured provider evidence")
rows = list(csv.DictReader(StringIO(source_bytes.decode("utf-8"))))
sessions = [row["session_date"] for row in rows]
lookup = {row["session_date"]: row for row in rows}
start = sessions.index(DECISION_DAY)
entry_index = start + 1
exit_index = entry_index + HOLD  # Hold H FULL sessions; exit NEXT OPEN.
if exit_index + 1 >= len(sessions):
    raise ValueError("Historical price window insufficient for sale settlement")
entry_date = sessions[entry_index]
exit_date = sessions[exit_index]
exit_previous = sessions[exit_index - 1]
ny = ZoneInfo("America/New_York")
def ts(day, hour, minute=0):
    return datetime.combine(
        date.fromisoformat(day), time(hour, minute), tzinfo=ny
    ).astimezone(UTC)
def ns(instant):
    return int(instant.timestamp() * 1_000_000_000)
def cents(decimal):
    return int((Decimal(str(decimal)) * 100).to_integral_exact())

instrument = Equity(
    instrument_id=InstrumentId.from_str(f"{SYMBOL}.SIM"),
    raw_symbol=Symbol(SYMBOL), currency=Currency.from_str("USD"),
    price_precision=2, price_increment=Price.from_str("0.01"),
    lot_size=Quantity.from_int(1), ts_event=0, ts_init=0,
)
ticks = []
for day_index in range(start, exit_index + 1):
    day = sessions[day_index]
    points = []
    if day_index > start:
        points.append((9, 30, lookup[day]["open"]))
    if day_index < exit_index:
        points.append((16, 0, lookup[day]["close"]))
    for hour, minute, mark_text in points:
        at = ns(ts(day, hour, minute))
        mark = Decimal(mark_text)
        ticks.append(QuoteTick(
            instrument_id=instrument.id,
            bid_price=Price.from_str(str(mark - Decimal("0.01"))),
            ask_price=Price.from_str(str(mark + Decimal("0.01"))),
            bid_size=Quantity.from_int(100),
            ask_size=Quantity.from_int(100),
            ts_event=at, ts_init=at,
        ))
assert len(ticks) == 2 * HOLD + 2

enter_open = ns(ts(entry_date, 9, 30))
leave_open = ns(ts(exit_date, 9, 30))
initial_close = ns(ts(sessions[start], 16))
exit_signal_close = ns(ts(exit_previous, 16))
decisions: dict[str, datetime] = {}

class MatureFixedHolding(Strategy):
    def __init__(self):
        super().__init__(StrategyConfig())
        self.buy_filled = 0
        self.sell_filled = 0
        self.exit_suppressed_without_position = False
    def on_start(self):
        self.subscribe_quotes(instrument.id)
    def on_order_filled(self, event):
        if event.order_side == OrderSide.BUY:
            self.buy_filled += int(Decimal(str(event.last_qty)))
        elif event.order_side == OrderSide.SELL:
            self.sell_filled += int(Decimal(str(event.last_qty)))
    def on_quote(self, tick):
        moment = tick.ts_event
        if moment == enter_open:
            if not self._saw_initial_close:
                raise RuntimeError("Buy cannot precede prior close")
            order = self.order_factory.limit(
                instrument_id=instrument.id, order_side=OrderSide.BUY,
                quantity=Quantity.from_int(1), price=Price.from_str("0.01" if NO_ENTRY else "900.00"),
                time_in_force=TimeInForce.IOC,
            )
            decisions[str(order.client_order_id)] = ts(sessions[start], 16, 1)
            self.submit_order(order)
        elif moment == initial_close:
            self._saw_initial_close = True
        elif moment == exit_signal_close:
            if self.buy_filled == 0:
                # Native IOC was canceled or expired. No order position exists:
                # do not fabricate the offsetting sell or a receipt.
                self.exit_suppressed_without_position = True
                return
            if self.buy_filled != 1:
                raise RuntimeError("Partially filled fixed-size entry unqualified")
            self._saw_exit_signal = True
        elif moment == leave_open:
            if self.exit_suppressed_without_position:
                return
            if not getattr(self, "_saw_exit_signal", False):
                raise RuntimeError("Exit cannot precede prior-day signal")
            order = self.order_factory.limit(
                instrument_id=instrument.id, order_side=OrderSide.SELL,
                quantity=Quantity.from_int(1), price=Price.from_str("9999.00" if NO_EXIT else "0.01"),
                time_in_force=TimeInForce.IOC,
            )
            decisions[str(order.client_order_id)] = ts(exit_previous, 16, 1)
            self.submit_order(order)

store = OUT / "native_catalog"
store.mkdir(parents=True, exist_ok=True)
catalog = ParquetDataCatalog(str(store))
catalog.write_instruments([instrument])
catalog.write_quote_ticks(ticks)
run_config = BacktestRunConfig(
    venues=[BacktestVenueConfig(
        name="SIM", oms_type=OmsType.NETTING,
        account_type=AccountType.MARGIN, book_type=BookType.L1_MBP,
        base_currency=Currency.from_str("USD"),
        starting_balances=["10000 USD"],
        fill_model=DefaultFillModel(
            prob_fill_on_limit=1.0, prob_slippage=0.0, random_seed=42
        ),
        fee_model=MakerTakerFeeModel(
            maker_rate=Decimal("0.00002"), taker_rate=Decimal("0.00002")
        ),
    )],
    data=[BacktestDataConfig(
        data_type=NautilusDataType.QuoteTick,
        catalog=DataCatalogConfig(path=str(store)),
        instrument_id=instrument.id,
    )],
    engine=BacktestEngineConfig(
        logging=LoggerConfig(stdout_level=LogLevel.ERROR)
    ),
    dispose_on_completion=False,
)
node = BacktestNode(configs=[run_config])
node.build()
strategy = MatureFixedHolding()
node.add_strategy(run_config.id, strategy)
native_result = node.run()
order_rows = node.generate_orders_report(run_config.id).reset_index().to_dict("records")
fill_rows = node.generate_fills_report(run_config.id).reset_index().to_dict("records")
cache = node.get_engine_cache(run_config.id)
orders = cache.orders()
# Directly observe the native holding authority, not only Paper projections.
open_native_positions = cache.positions_open()
if NO_EXIT:
    if len(open_native_positions) != 1:
        raise RuntimeError("Canceled exit must leave one actual native position")
elif open_native_positions:
    raise RuntimeError("Native strategy retained an unexpected open position")
print("NATIVE_ECONOMIC_ORDERS", [
    (row["side"], row["status"], row["filled_qty"]) for row in order_rows
])
print("NATIVE_ECONOMIC_FILLS", [
    (row["order_side"], str(row["last_px"]), str(row["commission"])) for row in fill_rows
])
if NO_ENTRY:
    if (len(order_rows) != 1 or len(fill_rows) != 0 or len(orders) != 1
            or strategy.buy_filled != 0 or strategy.sell_filled != 0
            or order_rows[0]["status"] not in {"CANCELED", "EXPIRED"}
            or not strategy.exit_suppressed_without_position):
        raise RuntimeError("A failed native entry incorrectly produced exit/economic effects")
else:
    if (len(order_rows) != 2 or len(fill_rows) != 2 or len(orders) != 2
            or strategy.buy_filled != 1 or strategy.sell_filled != 1
            or {row["status"] for row in order_rows} != {"FILLED"}
            or {row["order_side"] for row in fill_rows} != {"BUY", "SELL"}):
        raise RuntimeError("Mature native strategy did not fully enter and exit")
events = [
    e.to_dict() for order in orders for e in order.events()
    if type(e).__name__ == "OrderFilled"
]
assert len(events) == (0 if NO_ENTRY else 2)
assert len({e["trade_id"] for e in events}) == len(events)
assert len(decisions) == (1 if NO_ENTRY else 2)

# The bridge currently consumes one session, not a whole native multi-day
# cache: select the two ordered events AFTER witnessing the entire native
# order cache. Only this test uses per-session projections.
by_day = {}
for day in (entry_date, exit_date):
    f = [row for row in fill_rows
         if (int(row["ts_event"].timestamp()) == int(ts(day, 9, 30).timestamp()))]
    ids = {str(row["client_order_id"]) for row in f}
    if not ids:
        if not NO_ENTRY:
            raise RuntimeError("Native engine lost expected fill day")
        continue
    by_day[day] = next_open_paper_session(
        session=date.fromisoformat(day),
        previous_session=date.fromisoformat(sessions[sessions.index(day) - 1]),
        expected_account_id="SIM-001",
        opens_at=ts(day, 9, 30),
        previous_close_at=ts(sessions[sessions.index(day) - 1], 16),
        settlement_date=date.fromisoformat(sessions[sessions.index(day) + 1]),
        orders=[row for row in order_rows if str(row["client_order_id"]) in ids],
        decisions_by_order=decisions,
        fills=f,
        order_events=[event for event in events
                      if str(event["client_order_id"]) in ids],
        instrument_symbols={f"{SYMBOL}.SIM": SYMBOL},
        marks_minor={SYMBOL: cents(lookup[day]["close"])} if day != exit_date else {},
    )
    if len(ids) != 1:
        raise RuntimeError("Native order source did not yield unique daily order")

opening_session = PaperSession(
    session=date.fromisoformat(sessions[start]), previous_session=None,
    contribution_minor=1_000_000, reserve_contribution_minor=900_000,
    marks={}, buys=(),
)
paper_sessions = [opening_session]
state = value_session(None, opening_session)
for i in range(entry_index, exit_index + 2):
    day = sessions[i]
    if day in by_day:
        session = by_day[day]
    else:
        session = PaperSession(
            session=date.fromisoformat(day),
            previous_session=date.fromisoformat(sessions[i - 1]),
            contribution_minor=0, reserve_contribution_minor=0,
            marks={SYMBOL: cents(lookup[day]["close"])} if i < exit_index else {},
            buys=(),
        )
    paper_sessions.append(session)
    state = value_session(state, session)
    if i == entry_index and not NO_ENTRY and state.positions != {SYMBOL: 1}:
        raise AssertionError("Native buy did not become Paper position")
    if i == exit_index and not NO_ENTRY and (state.positions or len(state.pending_sales) != 1):
        raise AssertionError("Native exit did not become Paper receivable")
if state.positions or state.pending_sales or state.pending:
    raise AssertionError("Paper terminal holdings and settlement not fully cleared")
if NO_ENTRY and state.cash_minor != 1_000_000:
    raise AssertionError("Canceled native entry changed Paper cash")
if state.protected_minor != 900_000:
    raise AssertionError("Protected cash reserve has changed")

fees = sum(Decimal(str(row["commission"]).split()[0]) for row in fill_rows)
if NO_ENTRY:
    price_buy, price_sell = None, None
    expected_cash = Decimal("10000")
else:
    price_buy = Decimal(str(next(row["last_px"] for row in fill_rows if row["order_side"] == "BUY")))
    price_sell = Decimal(str(next(row["last_px"] for row in fill_rows if row["order_side"] == "SELL")))
    expected_cash = Decimal("10000") - price_buy + price_sell - fees
if state.cash_minor != cents(expected_cash):
    raise AssertionError("Nautilus two-leg cash economics diverged from native Paper")
standing = {
    "kind": "ordivon.finance.r3.qlib-signal-native-paper-executable",
    "research_horizon_signal_source": ("native_Qlib_0.9.7_OOS_score" if override is None else "EXPLICIT_TEST_INTERVENTION_ON_NATIVE_QLIB_SCORE"),
    "research_model_sample_decision": DECISION_DAY,
    "native_entry_session": entry_date,
    "native_exit_session": exit_date,
    "signal_scores": scores,
    "selected_instrument": SYMBOL,
    "test_counterfactual_score_intervention": override is not None,
    "historically_precommitted_model_decision": False,
    "Qlib_target_vs_native_exit_event_identical": True,
    "Qlib_research_target_horizon": MODEL_STUDY["signal_quality"]["horizon"],
    "standing": "SIMULATION_ONLY_NON_PIT_NOT_CAPITAL_AUTHORIZED",
    "horizon_complete_sessions": HOLD,
    "source_capture": "OpenBB Cboe retrospective unadjusted OHLCV",
    "source_evidence_is_only_backfilled_normalized_data": True,
    "native_engine": "NautilusTrader BacktestNode Strategy/OrderFilled native",
    "native_order_count": len(order_rows),
    "native_fill_count": len(fill_rows),
    "native_open_position_count": len(open_native_positions),
    "buy_price": str(price_buy) if price_buy is not None else None,
    "sell_price": str(price_sell) if price_sell is not None else None,
    "fee_total": str(fees),
    "last_paper_cash_minor": state.cash_minor,
    "net_cash_gain_usd": str(expected_cash - Decimal("10000")),
    "protected_cash_minor": state.protected_minor,
    "positions_closed": not state.positions,
    "receivable_settled": not state.pending_sales,
    "policy_rule_fixed_before_native_backtest": True,
    "policy_rule_historically_precommitted": False,
    "no_entry_cancelled_exit_suppressed": NO_ENTRY,
    "portfolio_cash_sleeve_minor": allocation["allocationsMinor"][SYMBOL],
    "portfolio_automatic_execution_authorized": allocation["executionAuthorized"],
    "historical_point_in_time_qualified": False,
    "execution_quotes_real": False,
    "market_microstructure_qualified": False,
    "portfolio_intent_admitted": False,
    "real_broker_or_PG_effect": "NONE",
}
(OUT / "native_holding_result.json").write_text(
    json.dumps(standing, indent=2), encoding="utf-8"
)
print("NATIVE_MATURE_BUY_HOLD_SELL_REFINEMENT", json.dumps(standing))
