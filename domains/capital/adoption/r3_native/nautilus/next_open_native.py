"""Native Git-bound retrospective simulation-only instruction -> Nautilus Limit IOC.

This is not historical PIT, authorized PortfolioIntent, PG posting or live trading.
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
import subprocess

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

# This is a Git-committed test fixture, NOT a Finance governance authority.
# Git cat-file obtains one immutable Git content-addressed blob. A mutable working-copy JSON is never
# read as a source of economic intent.
INTENT_BLOB = "bea945d370123b4b0f42e3a8e4bc5e60faeda120"
INTENT_PATH = "domains/capital/adoption/r3_native/nautilus/simulation_instruction.fixture.json"
repo = ROOT.parents[4]
source_cut = subprocess.check_output([
    "git", "-C", str(repo), "rev-parse", "HEAD"
]).decode("ascii").strip()
tree_blob = subprocess.check_output([
    "git", "-C", str(repo), "rev-parse", f"{source_cut}:{INTENT_PATH}"
]).decode("ascii").strip()
if tree_blob != INTENT_BLOB:
    raise ValueError("current source cut does not contain the pinned instruction Git blob")
instruction_bytes = subprocess.check_output([
    "git", "-C", str(repo), "cat-file", "blob", INTENT_BLOB
])
instruction_sha256 = sha256(instruction_bytes).hexdigest()
def reject_duplicate_fields(pairs):
    record = {}
    for key, value in pairs:
        if key in record:
            raise ValueError("duplicate simulation instruction field")
        record[key] = value
    return record

instruction = json.loads(instruction_bytes, object_pairs_hook=reject_duplicate_fields)
required_instruction = {
    "schemaVersion", "kind", "standing", "intentId", "accountId",
    "instrumentId", "symbol", "side", "quantity", "limitPrice",
    "maxCommitmentMinor", "feeReserveMinor", "currency", "previousSession",
    "tradeSession", "simulatedDecisionAt", "sourceCaptureSha256",
    "researchDatasetSha256", "investmentPolicyAdmitted",
    "historicalPointInTimeAdmitted", "externalFinancialWriteAllowed",
}
if type(instruction) is not dict or set(instruction) != required_instruction:
    raise ValueError("simulation instruction shape is not the frozen contract")
if (type(instruction["schemaVersion"]) is not int or instruction["schemaVersion"] != 1
        or instruction["kind"] != "ordivon.finance.r3.simulation-frozen-instruction"
        or instruction["standing"] != "SIMULATION_FIXTURE_ONLY"
        or instruction["investmentPolicyAdmitted"] is not False
        or instruction["historicalPointInTimeAdmitted"] is not False
        or instruction["externalFinancialWriteAllowed"] is not False):
    raise ValueError("simulation fixture may not claim live, risk or PIT authority")
if (instruction["sourceCaptureSha256"] != capture_sha
        or instruction["researchDatasetSha256"] != manifest.get("qlib_dataset_sha256")):
    raise ValueError("simulation intent and native research source digests disagree")
if (instruction["accountId"] != "SIM-001"
        or instruction["currency"] != "USD"
        or instruction["instrumentId"] != "SPY.SIM"
        or instruction["symbol"] != "SPY"
        or instruction["side"] != "BUY"):
    raise ValueError("simulation instruction does not bind the native account/instrument")
if (type(instruction["intentId"]) is not str or not instruction["intentId"]
        or len(instruction["intentId"]) > 128):
    raise ValueError("simulation instruction has no stable intent identity")
if type(instruction["limitPrice"]) is not str:
    raise ValueError("simulation limit must be an exact decimal string")
if type(instruction["quantity"]) is not int or instruction["quantity"] < 1:
    raise ValueError("simulation quantity must be a positive integer")
if (type(instruction["maxCommitmentMinor"]) is not int
        or type(instruction["feeReserveMinor"]) is not int):
    raise ValueError("simulation budget must be exact integer minor units")
limit_price = Decimal(instruction["limitPrice"])
if (not limit_price.is_finite() or limit_price <= 0
        or limit_price.as_tuple().exponent < -2
        or instruction["feeReserveMinor"] < 0
        or limit_price * 100 * instruction["quantity"] +
        instruction["feeReserveMinor"] > instruction["maxCommitmentMinor"]):
    raise ValueError("simulation native limit exceeds exact budget incl fee reserve")

records=list(csv.DictReader(StringIO(payload.decode("utf-8"))))
today={r["session_date"]:r for r in records}
prev_date = instruction["previousSession"]
next_date = instruction["tradeSession"]
a=today[prev_date]; b=today[next_date]
# Counterfactual inputs change only simulated future quotes. They MUST NOT
# pretend that the committed upstream Cboe capture or intent was altered.
shock=os.environ.get("ORDIVON_FINANCE_R3_TEST_OPEN_SHOCK_USD")
if shock is not None:
    if os.environ.get("ORDIVON_FINANCE_R3_SIMULATION_SCENARIO") != "COUNTERFACTUAL_ONLY":
        raise ValueError("future-price perturbation is not an admitted source")
    delta=Decimal(shock)
    if not delta.is_finite() or not Decimal("-1000") <= delta <= Decimal("1000"):
        raise ValueError("counterfactual shock must be finite and bounded")
    b=dict(b)
    b["open"]=str(Decimal(b["open"])+delta)
ny=ZoneInfo("America/New_York")
def nanos(date, hour,minute,second=0):
    return int(datetime.combine(
        datetime.fromisoformat(date).date(),time(hour,minute,second),ny
    ).astimezone(timezone.utc).timestamp()*1_000_000_000)

prev_decision_ns=nanos(prev_date,16,1)
next_open_ns=nanos(next_date,9,30)
next_close_ns=nanos(next_date,16,1)
declared_simulated_at = datetime.fromisoformat(instruction["simulatedDecisionAt"])
if (declared_simulated_at.tzinfo is None
        or int(declared_simulated_at.timestamp()*1_000_000_000) != prev_decision_ns):
    raise ValueError("simulation instruction decision time does not match prior close")
if prev_decision_ns >= next_open_ns:
    raise ValueError("simulation intent is not prior-session economic intent")

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
        order=self.order_factory.limit(
            instrument_id=instrument.id,
            order_side=OrderSide.BUY if instruction["side"] == "BUY" else OrderSide.SELL,
            quantity=Quantity.from_int(instruction["quantity"]),
            price=Price.from_str(str(limit_price)),
            time_in_force=TimeInForce.IOC,
        )
        self.submitted_instruction_sha256=instruction_sha256
        self.submitted_client_order_id=str(order.client_order_id)
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
native_strategy=NativeNextOpenOrder(StrategyConfig())
node.add_strategy(config.id,native_strategy)
results=node.run()
cache=node.get_engine_cache(config.id)
orders=cache.orders()
native_order_report=node.generate_orders_report(config.id).reset_index().to_dict("records")
if (len(orders) != 1 or len(native_order_report) != 1
        or native_strategy.submitted_instruction_sha256 != instruction_sha256
        or native_strategy.submitted_client_order_id != str(orders[0].client_order_id)
        or native_order_report[0]["client_order_id"] != str(orders[0].client_order_id)
        or native_order_report[0]["account_id"] != instruction["accountId"]):
    raise RuntimeError("native order/report/immutable simulation intent identity diverged")
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
  "simulated_instruction_sha256":instruction_sha256,
  "consumer_source_cut":source_cut,
  "current_tree_instruction_blob":tree_blob,
  "simulated_intent_id":instruction["intentId"],
  "native_order_matches_committed_intent":True,
  "native_account_id":native_order_report[0]["account_id"],
  "simulated_instruction_git_blob_sha1":INTENT_BLOB,
  "simulated_instruction_standing":instruction["standing"],
  "simulated_investment_policy_admitted":False,
  "simulated_source_was_known_at_historical_decision":False,
  "simulated_account_id":instruction["accountId"],
  "simulated_order_limit":str(limit_price),
  "simulated_quantity":instruction["quantity"],
  "simulated_client_order_id":str(orders[0].client_order_id) if len(orders)==1 else None,
  "counterfactual_open_shock_usd":str(shock) if shock is not None else None,
  "next_open_price":b["open"],
  "input_kind":"OHLCV derived SYNTHETIC +/- 0.01 USD, not real quotes",
  "source_capture_sha256":capture_sha,
  "source_manifest_sha256":sha256(manifest_bytes).hexdigest(),
  "capture_input_consumption":"one_hash_checked_byte_image",
  "real_pit":False,
  "execution_economics_qualified":False,
  "intraday_market_data_qualified":False,
  "latency_scope":"default zero-latency synthetic sample only",
  "PG_effect":"NONE",
}
(ROOT/"next_open_result.json").write_text(json.dumps(out,indent=2),encoding="utf-8")
print("NEXT_OPEN_NATIVE_RESULT",json.dumps(out,default=str))
