"""Native NautilusTrader 2.0rc9 BacktestNode/OMS mechanics on synthetic quotes from OpenBB Cboe daily SPY closing marks.

This is NOT historical exchange quote data, not execution economics, not PG
accounting, and not a valid prior-close -> next-open paper-session source.
"""
from __future__ import annotations
import csv
import os
import json
from datetime import datetime, time, timezone
from decimal import Decimal
from hashlib import sha256
from pathlib import Path

from nautilus_trader.backtest import BacktestNode
from nautilus_trader.common import LogLevel
from nautilus_trader.config import (
    BacktestDataConfig, BacktestEngineConfig, BacktestRunConfig,
    BacktestVenueConfig, DataCatalogConfig, LoggerConfig,
)
from nautilus_trader.execution import DefaultFillModel, MakerTakerFeeModel
from nautilus_trader.model import (
    AccountType, BookType, Currency, Equity, InstrumentId,
    NautilusDataType, OmsType, Price, Quantity, QuoteTick, Symbol,
)
from nautilus_trader.persistence import ParquetDataCatalog
from nautilus_trader.trading import EmaCrossConfig

ROOT=Path(__file__).resolve().parent
SOURCE=Path(os.environ.get("ORDIVON_FINANCE_R3_SPY_CSV",str(ROOT.parent/"output"/"openbb_cboe_SPY_normalized.csv"))).resolve()
if not SOURCE.is_file():
    raise FileNotFoundError(f"Requires the pinned upstream read-only provider capture: {SOURCE}")
source_sha=sha256(SOURCE.read_bytes()).hexdigest()
with SOURCE.open(encoding="utf-8", newline="") as f:
    rows=list(csv.DictReader(f))
rows=rows[-170:]
if len(rows)<100:
    raise AssertionError("Insufficient real ETF daily mark rows for simulator")
asset=Equity(
    instrument_id=InstrumentId.from_str("SPY.SIM"),
    raw_symbol=Symbol("SPY"),
    currency=Currency.from_str("USD"),
    price_precision=2,
    price_increment=Price.from_str("0.01"),
    lot_size=Quantity.from_int(1),
    ts_event=0,
    ts_init=0,
)
ticks=[]
for row in rows:
    session=datetime.fromisoformat(row["session_date"]).date()
    # A SYNTHETIC quote timestamp for an EOD-close-price test; not the
    # actual Cboe quote time, ask, bid or historical market microstructure.
    when=datetime.combine(session, time(21, 0), tzinfo=timezone.utc)
    ns=int(when.timestamp()*1_000_000_000)
    mark=Decimal(row["close"])
    # Manufactures a one-cent spread around the observed EOD mark.
    ticks.append(QuoteTick(
        instrument_id=asset.id,
        bid_price=Price.from_str(str((mark-Decimal("0.01")).quantize(Decimal("0.01")))),
        ask_price=Price.from_str(str((mark+Decimal("0.01")).quantize(Decimal("0.01")))),
        bid_size=Quantity.from_int(100),
        ask_size=Quantity.from_int(100),
        ts_event=ns,
        ts_init=ns,
    ))
store=ROOT/"catalog"
if store.exists():
    import shutil
    shutil.rmtree(store)
store.mkdir()
catalog=ParquetDataCatalog(str(store))
catalog.write_instruments([asset])
catalog.write_quote_ticks(ticks)
native_data=catalog.query_quote_ticks(identifiers=[asset.id.value])
assert len(native_data)==len(ticks)
venue=BacktestVenueConfig(
    name="SIM",
    oms_type=OmsType.NETTING,
    account_type=AccountType.MARGIN,
    book_type=BookType.L1_MBP,
    base_currency=Currency.from_str("USD"),
    starting_balances=["10000 USD"],
    fill_model=DefaultFillModel(prob_fill_on_limit=1.0,prob_slippage=0.0,random_seed=42),
    fee_model=MakerTakerFeeModel(
        maker_rate=Decimal("0.00002"),
        taker_rate=Decimal("0.00002"),
    ),
)
data=BacktestDataConfig(
    data_type=NautilusDataType.QuoteTick,
    catalog=DataCatalogConfig(path=str(store)),
    instrument_id=asset.id,
)
config=BacktestRunConfig(
    venues=[venue],
    data=[data],
    engine=BacktestEngineConfig(logging=LoggerConfig(stdout_level=LogLevel.ERROR)),
    dispose_on_completion=False,
)
node=BacktestNode(configs=[config])
node.build()
node.add_builtin_strategy(
    config.id,"EmaCross",
    EmaCrossConfig(instrument_id=asset.id,trade_size=Quantity.from_int(1),
                   fast_period=3,slow_period=8),
)
results=node.run()
fills_report=node.generate_fills_report(config.id)
orders_report=node.generate_orders_report(config.id)
positions_report=node.generate_positions_report(config.id)
print("NATIVE_REPORT_DETAILS", "orders", len(orders_report), "fills", len(fills_report), "positions", len(positions_report), "fill_cols", list(fills_report.columns))
if fills_report.empty:
    raise AssertionError("Backtest ran but produced zero native OrderFilled rows")
if fills_report["trade_id"].isna().any():
    raise AssertionError("Missing native trade identity")
print("NATIVE_FILL_EXAMPLE", fills_report.head(2).to_json(date_format="iso"))
native_cache=node.get_engine_cache(config.id)
native_orders=native_cache.orders()
# API-specific, same-engine audit: reports and event history must refine
# the same native order identities and economics. Not external venue proof.
import pandas as pd
from collections import Counter

if fills_report.index.name != "client_order_id":
    raise AssertionError("Nautilus v2 fill report client order index changed")
if orders_report.index.name != "client_order_id":
    raise AssertionError("Nautilus v2 orders report client order index changed")
native_fill_rows = fills_report.reset_index().to_dict("records")
native_order_ids = {str(o.client_order_id) for o in native_orders}
native_event_rows = []
for order in native_orders:
    for evt in order.events():
        event_kind = type(evt).__name__
        if event_kind.startswith("OrderFill") and event_kind != "OrderFilled":
            raise AssertionError("Native fill correction not supported by this bounded simulation")
        if event_kind == "OrderFilled":
            native_event_rows.append(evt.to_dict())

keys = lambda seq: Counter((str(row["client_order_id"]), str(row["trade_id"])) for row in seq)
if keys(native_fill_rows) != keys(native_event_rows):
    raise AssertionError("Native fill report and native cached order events do not reconcile")
if len(native_fill_rows) != len(native_event_rows) or not native_fill_rows:
    raise AssertionError("Native report vs events row counts mismatch or absent")
events_by_key = {}
event_ids = [str(e["event_id"]) for e in native_event_rows]
if len(set(event_ids)) != len(event_ids):
    raise AssertionError("Repeated event UUID inside the same native run")
for event in native_event_rows:
    key = (str(event["client_order_id"]), str(event["trade_id"]))
    if key in events_by_key:
        raise AssertionError("Same trade identity appears twice: restatement/replay not qualified")
    events_by_key[key] = event
for fill in native_fill_rows:
    key = (str(fill["client_order_id"]), str(fill["trade_id"]))
    event = events_by_key[key]
    if key[0] not in native_order_ids:
        raise AssertionError("A native fill lacks a cached native order")
    for field in ("event_id", "account_id", "instrument_id", "order_side",
                  "last_qty", "last_px", "commission", "currency"):
        if str(event[field]) != str(fill[field]):
            raise AssertionError(f"Native event/report disagree on {field}")
    if int(event["ts_event"]) != int(pd.Timestamp(fill["ts_event"]).value):
        raise AssertionError("Native event/report nanosecond timestamp mismatch")
all_accounts = sorted({str(r["account_id"]) for r in native_fill_rows})
native_order_accounts = {str(row["account_id"]) for row in orders_report.reset_index().to_dict("records")}
if len(all_accounts) != 1 or native_order_accounts != set(all_accounts):
    raise AssertionError("Single-paper-account qualification cannot merge accounts")
print("NATIVE_REPORT_EVENT_WITNESS", len(native_fill_rows),
      "account", all_accounts[0],
      "key=client_order_id+trade_id",
      "event/report economics identical", True)
print("NATIVE_ORDER_CACHE", len(native_orders))
if native_orders:
    sample_order=native_orders[0]
    sample_events=getattr(sample_order,"events",lambda:[])()
    print("NATIVE_ORDER_EVENT_TYPES", [type(e).__name__ for e in sample_events])
    native_fills=[e for e in sample_events if type(e).__name__=="OrderFilled"]
    if native_fills:
        e=native_fills[0]
        print("NATIVE_ORDER_FILLED_EVENT", {
            "trade_id":str(e.trade_id),
            "event_id":str(e.event_id),
            "account_id":str(e.account_id),
            "client_order_id":str(e.client_order_id),
            "last_qty":str(e.last_qty),
            "last_px":str(e.last_px),
            "commission":str(e.commission),
            "ts_event":e.ts_event,
            "reconciliation":bool(e.reconciliation),
        })
summary={
    "kind":"ordivon.finance.r3.nautilus-rc9-synthetic-oms-qualification",
    "source_file_sha256":source_sha,
    "source_kind":"OpenBB Cboe historical normalized EOD closing marks",
    "quote_origin":"SYNTHETIC from EOD close +/- 0.01 USD",
    "timestamp_origin":"SYNTHETIC each session 21:00 UTC; not verified venue session clock",
    "native_catalog_rows":len(native_data),
    "backtest_result_count":len(results),
    "native_orders":len(orders_report),
    "native_fill_events":len(fills_report),
    "native_positions":len(positions_report),
    "native_report_event_reconciled":True,
    "native_single_account":all_accounts[0],
    "native_report_client_id_is_index":True,
    "event_corrections_present":False,
    "external_venue_history_complete":"UNKNOWN",
    "native_result_repr":[repr(x)[:1500] for x in results],
    "capital_effect":"NONE",
    "pg_effect":"NONE",
    "effect_semantics":"SIMULATION_ONLY_NOT_BROKER_NOT_PIT_NOT_REAL_SPREAD",
    "native_fill_model":"DefaultFillModel(limit=1,slippage=0,seed=42)",
}
(ROOT/"native_backtest_result.json").write_text(json.dumps(summary,indent=2),encoding="utf-8")
print("NAUTILUS_NATIVE_BACKTEST",json.dumps(summary))
