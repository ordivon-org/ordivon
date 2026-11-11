"""Strictly simulated Cboe OHLCV 鈫?native Nautilus T-1-after-close MOO probe.

This is the minimal native Strategy callback to submit ONE AT_THE_OPEN market
order; native BacktestNode owns venue, order, fill and account mechanics.
Quotes and timestamps are SYNTHETIC and do not prove historical execution.
"""
from __future__ import annotations
from datetime import datetime, time, timezone
from decimal import Decimal
from hashlib import sha256
from pathlib import Path
from zoneinfo import ZoneInfo
import csv
from io import StringIO
import json
import os

from nautilus_trader.backtest import BacktestNode
from nautilus_trader.common import LogLevel
from nautilus_trader.config import (
    BacktestDataConfig, BacktestEngineConfig, BacktestRunConfig,
    BacktestVenueConfig, DataCatalogConfig, LoggerConfig
)
from nautilus_trader.execution import DefaultFillModel, MakerTakerFeeModel
from nautilus_trader.model import (
    AccountType, BookType, Currency, Equity, InstrumentId, NautilusDataType,
    OmsType, Price, Quantity, QuoteTick, Symbol, OrderSide, TimeInForce
)
from nautilus_trader.persistence import ParquetDataCatalog
from nautilus_trader.trading import Strategy, StrategyConfig

ROOT=Path(__file__).resolve().parent
SOURCE=Path(os.environ.get("ORDIVON_FINANCE_R3_SPY_CSV",str(ROOT.parent/"output"/"openbb_cboe_SPY_normalized.csv")))
# The study's normalized Cboe capture is a checked byte input; a
# path reopened after hashing could feed DIFFERENT prices to the simulator.
payload=SOURCE.read_bytes()
capture_sha=sha256(payload).hexdigest()
MANIFEST=Path(os.environ.get(
    "ORDIVON_FINANCE_R3_SOURCE_MANIFEST",
    str(ROOT.parent/"output"/"native_study_result.json")
)).resolve()
manifest_bytes=MANIFEST.read_bytes()
manifest=json.loads(manifest_bytes)
receipts=[r for r in manifest["provider_receipts"] if r.get("symbol")=="SPY"]
if len(receipts)!=1 or receipts[0]["normalized_sha256"]!=capture_sha:
    raise ValueError("Native opening capture and research receipt hash disagree")
records=list(csv.DictReader(StringIO(payload.decode("utf-8"))))
today={r["session_date"]:r for r in records}
prev_date="2026-10-28"
next_date="2026-10-29"
a=today[prev_date]; b=today[next_date]
ny=ZoneInfo("America/New_York")
def nanos(date, hour,minute,second=0):
    return int(datetime.combine(
        datetime.fromisoformat(date).date(),time(hour,minute,second),ny
    ).astimezone(timezone.utc).timestamp()*1_000_000_000)

prev_decision_ns=nanos(prev_date,16,1)
next_open_ns=nanos(next_date,9,30)
next_close_ns=nanos(next_date,16,1)

instrument=Equity(
    instrument_id=InstrumentId.from_str("SPY.SIM"),
    raw_symbol=Symbol("SPY"),currency=Currency.from_str("USD"),
    price_precision=2,price_increment=Price.from_str("0.01"),
    lot_size=Quantity.from_int(1),ts_event=0,ts_init=0,
)
def quote(price,ts):
    value=Decimal(price)
    return QuoteTick(
        instrument_id=instrument.id,
        bid_price=Price.from_str(str((value-Decimal("0.01")).quantize(Decimal("0.01")))),
        ask_price=Price.from_str(str((value+Decimal("0.01")).quantize(Decimal("0.01")))),
        bid_size=Quantity.from_int(100),
        ask_size=Quantity.from_int(100),ts_event=ts,ts_init=ts
    )
ticks=[
    quote(a["close"],prev_decision_ns),
    quote(b["open"],next_open_ns),
    quote(b["close"],next_close_ns),
]
class NativeNextOpenOrder(Strategy):
    def __init__(self,config):
        super().__init__(config)
        self.done=False
    def on_start(self):
        self.subscribe_quotes(instrument.id)
    def on_quote(self,quote_tick):
        if quote_tick.ts_event == prev_decision_ns:
            # The economic intent is frozen AFTER the previous close.
            self.decision_at = quote_tick.ts_event
            return
        if self.done or quote_tick.ts_event != next_open_ns:
            return
        if getattr(self, "decision_at", None) != prev_decision_ns:
            raise RuntimeError("No prior-session committed decision")
        # An ordinary native Market order is released only on the
        # next-session open callback. BacktestNode owns the fill semantics.
        # The simulator DOES NOT support TimeInForce.AT_THE_OPEN.
        order=self.order_factory.market(
            instrument_id=instrument.id,
            order_side=OrderSide.BUY,
            quantity=Quantity.from_int(1),
            time_in_force=TimeInForce.IOC,
        )
        self.submit_order(order)
        self.done=True

store=ROOT/"next_open_catalog"
if store.exists():
    import shutil
    shutil.rmtree(store)
store.mkdir()
catalog=ParquetDataCatalog(str(store))
catalog.write_instruments([instrument])
catalog.write_quote_ticks(ticks)
venue=BacktestVenueConfig(
    name="SIM",
    oms_type=OmsType.NETTING,
    account_type=AccountType.MARGIN,
    book_type=BookType.L1_MBP,
    base_currency=Currency.from_str("USD"),
    starting_balances=["10000 USD"],
    fill_model=DefaultFillModel(prob_fill_on_limit=1.0,prob_slippage=0.0,random_seed=42),
    fee_model=MakerTakerFeeModel(maker_rate=Decimal("0.00002"),taker_rate=Decimal("0.00002")),
)
data=BacktestDataConfig(
    data_type=NautilusDataType.QuoteTick,
    catalog=DataCatalogConfig(path=str(store)),
    instrument_id=instrument.id,
)
config=BacktestRunConfig(
    venues=[venue],data=[data],
    engine=BacktestEngineConfig(logging=LoggerConfig(stdout_level=LogLevel.ERROR)),
    dispose_on_completion=False,
)
node=BacktestNode(configs=[config])
node.build()
node.add_strategy(config.id, NativeNextOpenOrder(StrategyConfig()))
results=node.run()
cache=node.get_engine_cache(config.id)
orders=cache.orders()
fills=node.generate_fills_report(config.id).reset_index().to_dict("records")
events=[e.to_dict() for o in orders for e in o.events() if type(e).__name__.startswith("OrderFill")]
all_order_events=[(str(o.client_order_id),[type(e).__name__ for e in o.events()]) for o in orders]
out={
  "result": [repr(r) for r in results],
  "order_count":len(orders),
  "fill_count":len(fills),
  "fill_events":len(events),
  "all_order_events":all_order_events,
  "order_rejection_details":[e.to_dict() for o in orders for e in o.events() if type(e).__name__ in {"OrderRejected","OrderDenied"}],
  "previous_close_decision_ns":prev_decision_ns,
  "next_open_ns":next_open_ns,
  "next_close_ns":next_close_ns,
  "native_fill_ts_events":[str(r["ts_event"]) for r in fills],
  "native_fill_px":[str(r["last_px"]) for r in fills],
  "native_order_ts_init":[str(r["ts_init"]) for r in node.generate_orders_report(config.id).reset_index().to_dict("records")],
  "next_open_price":b["open"],
  "input_kind":"OHLCV derived SYNTHETIC +/- 0.01 USD, not real quotes",
  "source_capture_sha256":capture_sha,
  "source_manifest_sha256":sha256(manifest_bytes).hexdigest(),
  "capture_input_consumption":"one_hash_checked_byte_image",
  "real_pit":False,
  "PG_effect":"NONE",
}
(ROOT/"next_open_result.json").write_text(json.dumps(out,indent=2),encoding="utf-8")
print("NEXT_OPEN_NATIVE_RESULT",json.dumps(out,default=str))
