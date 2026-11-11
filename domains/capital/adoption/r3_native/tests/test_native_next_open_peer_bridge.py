"""Cross-agent native-run integration probe (READ ONLY, no PG writes).

Consumes one Nautilus 2.0rc9 *native BacktestNode* run, then calls the
published, immutable Agent B bridge source by exact Git revision.
This does NOT import or modify Agent B's live/dirty working tree.
"""
from __future__ import annotations
from datetime import date, datetime, time
from decimal import Decimal
from hashlib import sha256
import json
from pathlib import Path
import runpy
import subprocess
import sys
from types import ModuleType
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parents[3]  # domains/capital/adoption/r3_native -> monorepo root
CAPITAL = ROOT.parents[1]
CAP_SRC = CAPITAL / "src"
assert (CAP_SRC / "ordivon_capital/accounting/paper_close.py").is_file()
sys.path.insert(0, str(CAP_SRC))

PEER_COMMIT = "c2e770f488ca1288c8a0a19530ecefd4ee3d45fa"
PEER_PATH = "domains/capital/src/ordivon_capital/trading/nautilus_paper_bridge.py"
payload = subprocess.check_output(
    ["git", "-C", str(REPO), "show", f"{PEER_COMMIT}:{PEER_PATH}"]
)
import ordivon_capital.trading
native_bridge = ModuleType("ordivon_capital.trading.nautilus_paper_bridge")
native_bridge.__package__ = "ordivon_capital.trading"
native_bridge.__file__ = f"git:{PEER_COMMIT}:{PEER_PATH}"
exec(compile(payload, native_bridge.__file__, "exec"), native_bridge.__dict__)
from ordivon_capital.accounting.paper_close import PaperValuation, value_session

run = runpy.run_path(str(ROOT / "nautilus/next_open_native.py"), run_name="__main__")
node = run["node"]
config = run["config"]
orders = node.get_engine_cache(config.id).orders()
fills = node.generate_fills_report(config.id).reset_index().to_dict("records")
assert len(orders) == len(fills) == 1
assert fills[0]["account_id"] == "SIM-001"
ny = ZoneInfo("America/New_York")
p = date.fromisoformat(run["prev_date"])
t = date.fromisoformat(run["next_date"])
prior_close = datetime.combine(p, time(16,0),ny)
prior_decision = datetime.combine(p, time(16,1),ny)
next_open = datetime.combine(t, time(9,30),ny)
assert prior_decision.timestamp()*1e9 == run["prev_decision_ns"]
assert next_open.timestamp()*1e9 == run["next_open_ns"]

# The B bridge reads *native* orders, reports and events, rather than
# accepting caller-pruned order_events. No fake trade is inserted.
session = native_bridge.next_open_native_paper_session(
    node=node, run_config_id=config.id,
    session=t, previous_session=p, expected_account_id="SIM-001",
    opens_at=next_open, previous_close_at=prior_close,
    settlement_date=date(2026,11,2),
    decisions_by_order={str(o.client_order_id):prior_decision for o in orders},
    instrument_symbols={run["instrument"].id.value:"SPY"},
    marks_minor={"SPY":int(Decimal(run["b"]["close"])*100)},
)
assert len(session.buys) == 1 and not session.sells
buy=session.buys[0]
assert buy.filled_at == next_open
assert buy.decided_at == prior_decision
assert buy.price_minor == int(Decimal(fills[0]["last_px"])*100)
assert buy.fill_id.startswith("nautilus-paper:SIM-001:")
assert buy.shares == 1
previous=PaperValuation(
    session=p,cash_minor=1000000,protected_minor=0,
    positions={},pending={},contribution_minor=1000000,
    payable_minor=0,nav_minor=1000000
)
valuation=value_session(previous,session)
assert valuation.positions == {"SPY":1}
assert valuation.payable_minor == buy.cost_minor
assert valuation.nav_minor > 0

# Wrong/account-ambiguous target MUST fail before economic projection.
try:
    native_bridge.next_open_native_paper_session(
        node=node,run_config_id=config.id,session=t,previous_session=p,
        expected_account_id="A-NOT-SIM-001",
        opens_at=next_open,previous_close_at=prior_close,
        settlement_date=date(2026,11,2),
        decisions_by_order={str(o.client_order_id):prior_decision for o in orders},
        instrument_symbols={run["instrument"].id.value:"SPY"},
        marks_minor={"SPY":int(Decimal(run["b"]["close"])*100)},
    )
except native_bridge.NautilusPaperBridgeError:
    rejected_mismatched_account=True
else:
    rejected_mismatched_account=False
assert rejected_mismatched_account

result={
    "kind":"ordivon.finance.r3.next-open-native-bridge-read-only",
    "peer_bridge_committed_source":PEER_COMMIT,
    "native_venue":"SIM",
    "quotes":"SYNTHETIC_FROM_OHLCV_NOT_REAL_L1",
    "native_order_count":len(orders),
    "native_fill_count":len(fills),
    "decision_at":prior_decision.isoformat(),
    "fill_at":buy.filled_at.isoformat(),
    "native_trade_id":str(fills[0]["trade_id"]),
    "price_minor":buy.price_minor,
    "fee_minor":buy.fee_minor,
    "nav_minor":valuation.nav_minor,
    "mismatched_account_rejected":rejected_mismatched_account,
    "external_PG_account_binding":"UNKNOWN",
    "source_is_historically_PIT":False,
    "PG_effect":"NONE",
}

# Economic intent is frozen at T close; perturbing the T+1 opening mark
# must change the native execution price, NEVER side/size or decision time.
from tempfile import TemporaryDirectory
import csv
import io
import os
with TemporaryDirectory(prefix="finance-r3-next-open-ablation-") as temp_dir:
    original_csv = ROOT / "output/openbb_cboe_SPY_normalized.csv"
    raw_csv = original_csv.read_text(encoding="utf-8")
    reader = csv.DictReader(io.StringIO(raw_csv))
    records = list(reader)
    fields = list(reader.fieldnames)
    changed = 0
    for record in records:
        if record["session_date"] == run["next_date"]:
            record["open"] = str(Decimal(record["open"]) + Decimal("10.00"))
            changed += 1
    assert changed == 1
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=fields, lineterminator="\n")
    writer.writeheader()
    writer.writerows(records)
    shock = Path(temp_dir) / "shock_open.csv"
    shock.write_text(buf.getvalue(), encoding="utf-8")
    # This is explicitly a counterfactual capture, so its own manifest
    # names its changed bytes rather than impersonating the real Cboe receipt.
    shock_manifest = json.loads(
        (ROOT / "output/native_study_result.json").read_text(encoding="utf-8")
    )
    for receipt in shock_manifest["provider_receipts"]:
        if receipt["symbol"] == "SPY":
            receipt["normalized_sha256"] = sha256(shock.read_bytes()).hexdigest()
    shock_manifest_file = Path(temp_dir) / "counterfactual_manifest.json"
    shock_manifest_file.write_text(
        json.dumps(shock_manifest), encoding="utf-8"
    )
    prior_manifest = os.environ.get("ORDIVON_FINANCE_R3_SOURCE_MANIFEST")
    os.environ["ORDIVON_FINANCE_R3_SOURCE_MANIFEST"] = str(shock_manifest_file)
    prior_input = os.environ.get("ORDIVON_FINANCE_R3_SPY_CSV")
    os.environ["ORDIVON_FINANCE_R3_SPY_CSV"] = str(shock)
    try:
        shocked = runpy.run_path(str(ROOT / "nautilus/next_open_native.py"), run_name="__main__")
    finally:
        if prior_input is None:
            os.environ.pop("ORDIVON_FINANCE_R3_SPY_CSV", None)
        else:
            os.environ["ORDIVON_FINANCE_R3_SPY_CSV"] = prior_input
        if prior_manifest is None:
            os.environ.pop("ORDIVON_FINANCE_R3_SOURCE_MANIFEST", None)
        else:
            os.environ["ORDIVON_FINANCE_R3_SOURCE_MANIFEST"] = prior_manifest
    shocked_orders = shocked["node"].get_engine_cache(shocked["config"].id).orders()
    shocked_fills = shocked["node"].generate_fills_report(
        shocked["config"].id
    ).reset_index().to_dict("records")
    assert len(shocked_orders) == len(shocked_fills) == 1
    assert shocked_orders[0].side == orders[0].side
    assert shocked_orders[0].quantity == orders[0].quantity
    assert shocked["prev_decision_ns"] == run["prev_decision_ns"]
    assert shocked_fills[0]["ts_event"] == fills[0]["ts_event"]
    assert Decimal(shocked_fills[0]["last_px"]) - Decimal(fills[0]["last_px"]) == Decimal("10.00")
    result["next_open_price_shock_plus_10_unchanged_order_side_qty"] = True
    print("NATIVE_FROZEN_PREVCLOSE_INTENT_ABLATION_PASS",
          "open_price_shock_usd", 10,
          "order_side", str(orders[0].side),
          "qty", str(orders[0].quantity),
          "actual_native_fill_px_before", str(fills[0]["last_px"]),
          "after", str(shocked_fills[0]["last_px"]))
(ROOT/"nautilus/next_open_peer_bridge_result.json").write_text(
    json.dumps(result,indent=2),encoding="utf-8"
)
print("NATIVE_NEXT_OPEN_PAPER_BRIDGE_PASS",json.dumps(result))
