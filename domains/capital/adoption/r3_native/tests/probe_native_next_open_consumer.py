"""Integrated Finance native next-open consumer proof (READ ONLY, no PG writes).

Consumes Nautilus 2.0rc9 BacktestNode and the CURRENT integrated Capital
bridge by default; optional historical peer source is read by exact Git ID.
The simulated instruction is immutable Git bytes, NOT investment authority.
"""
from __future__ import annotations

import json
import os
import runpy
import subprocess
import sys
from dataclasses import replace
from datetime import date, datetime, time
from decimal import Decimal
from hashlib import sha256
from pathlib import Path
from types import ModuleType
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parents[3]  # domains/capital/adoption/r3_native -> monorepo root
CAPITAL = ROOT.parents[1]
CAP_SRC = CAPITAL / "src"
assert (CAP_SRC / "ordivon_capital/accounting/paper_close.py").is_file()
sys.path.insert(0, str(CAP_SRC))

PEER_COMMIT = "9f7f948af44233c862b10e34741859bc3cf2c122"
PEER_PATH = "domains/capital/src/ordivon_capital/trading/nautilus_paper_bridge.py"
# Consume the CURRENT integrated Finance bridge unless replaying a pinned peer.
bridge_mode = os.environ.get("ORDIVON_FINANCE_R3_BRIDGE_MODE", "integrated")
if bridge_mode == "integrated":
    from ordivon_capital.trading import nautilus_paper_bridge as native_bridge
elif bridge_mode == "peer":
    payload = subprocess.check_output(
        ["git", "-C", str(REPO), "show", f"{PEER_COMMIT}:{PEER_PATH}"]
    )
    native_bridge = ModuleType("ordivon_capital.trading.nautilus_paper_bridge")
    native_bridge.__package__ = "ordivon_capital.trading"
    native_bridge.__file__ = f"git:{PEER_COMMIT}:{PEER_PATH}"
    exec(compile(payload, native_bridge.__file__, "exec"), native_bridge.__dict__)
else:
    raise ValueError("unsupported bridge source mode")
from ordivon_capital.accounting.paper_close import PaperValuation, value_session
from ordivon_capital.portfolio.strategic_contribution import plan_strategic_contribution

run = runpy.run_path(str(ROOT / "nautilus/next_open_native.py"), run_name="__main__")
node = run["node"]
config = run["config"]
orders = node.get_engine_cache(config.id).orders()
fills = node.generate_fills_report(config.id).reset_index().to_dict("records")
assert len(orders) == len(fills) == 1
assert fills[0]["account_id"] == "SIM-001"
instruction=run["instruction"]
assert instruction["standing"] == "SIMULATION_FIXTURE_ONLY"
assert not instruction["investmentPolicyAdmitted"]
assert not instruction["historicalPointInTimeAdmitted"]
assert not instruction["externalFinancialWriteAllowed"]
assert instruction["accountId"] == fills[0]["account_id"]
assert instruction["instrumentId"] == str(orders[0].instrument_id)
assert instruction["quantity"] == int(orders[0].quantity)
assert run["out"]["simulated_client_order_id"] == str(orders[0].client_order_id)
assert run["out"]["simulated_instruction_sha256"] == sha256(run["instruction_bytes"]).hexdigest()
assert run["out"]["current_tree_instruction_blob"] == run["INTENT_BLOB"]
assert run["out"]["consumer_source_cut"] == run["source_cut"]
assert run["out"]["simulated_intent_id"] == instruction["intentId"]
assert run["out"]["native_order_matches_committed_intent"] is True
assert run["out"]["native_account_id"] == instruction["accountId"]
assert run["out"]["source_capture_sha256"] == instruction["sourceCaptureSha256"]
assert run["out"]["simulated_order_limit"] == instruction["limitPrice"]

# Reuse Capital's existing Portfolio contribution owner; do not create a
# second lot/budget engine. Explicit caller weights only, no optimization.
plan=plan_strategic_contribution({
    "schemaVersion":1,
    "kind":"ordivon.finance.portfolio.strategic-contribution-request",
    "currency":"USD",
    "cashMinor":1000000,
    "protectedReserveMinor":900000,
    "contributionMinor":instruction["maxCommitmentMinor"],
    "holdingsMinor":{"SPY":0},
    "targetWeightsBps":{"SPY":10000},
})
assert plan["standing"] == "READ_ONLY_PROJECTION"
assert plan["allocationsMinor"]["SPY"] == instruction["maxCommitmentMinor"]
assert not plan["executionAuthorized"]
ny = ZoneInfo("America/New_York")
p = date.fromisoformat(run["prev_date"])
t = date.fromisoformat(run["next_date"])
prior_close = datetime.combine(p, time(16,0),ny)
prior_decision = datetime.fromisoformat(instruction["simulatedDecisionAt"])
next_open = datetime.combine(t, time(9,30),ny)
assert prior_decision.timestamp()*1e9 == run["prev_decision_ns"]
assert next_open.timestamp()*1e9 == run["next_open_ns"]

# The B bridge reads *native* orders, reports and events, rather than
# accepting caller-pruned order_events. No fake trade is inserted.
session = native_bridge.next_open_native_paper_session(
    node=node, run_config_id=config.id,
    session=t, previous_session=p, expected_account_id=instruction["accountId"],
    opens_at=next_open, previous_close_at=prior_close,
    settlement_date=date(2026,10,30),
    decisions_by_order={run["out"]["simulated_client_order_id"]:prior_decision},
    instrument_symbols={instruction["instrumentId"]:instruction["symbol"]},
    marks_minor={"SPY":int(Decimal(run["b"]["close"])*100)},
)
assert len(session.buys) == 1 and not session.sells
buy=session.buys[0]
assert buy.filled_at == next_open
assert buy.decided_at == prior_decision
assert buy.price_minor == int(Decimal(fills[0]["last_px"])*100)
assert buy.fill_id.startswith("nautilus-paper:SIM-001:")
assert buy.shares == instruction["quantity"]
assert buy.cost_minor <= plan["allocationsMinor"]["SPY"]
assert buy.cost_minor <= instruction["maxCommitmentMinor"]
# The PG-facing projection must obtain marks from a separate authoritative snapshot.
pg_paper_candidate=replace(session,marks={})
assert not pg_paper_candidate.marks
previous=PaperValuation(
    session=p,cash_minor=1000000,protected_minor=900000,
    positions={},pending={},contribution_minor=1000000,
    payable_minor=0,nav_minor=1000000
)
valuation=value_session(previous,session)
assert valuation.positions == {"SPY":instruction["quantity"]}
assert valuation.cash_minor >= 900000
assert valuation.payable_minor == buy.cost_minor
assert valuation.nav_minor > 0

# Wrong/account-ambiguous target MUST fail before economic projection.
try:
    native_bridge.next_open_native_paper_session(
        node=node,run_config_id=config.id,session=t,previous_session=p,
        expected_account_id="A-NOT-SIM-001",
        opens_at=next_open,previous_close_at=prior_close,
        settlement_date=date(2026,10,30),
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
    "bridge_source_mode": bridge_mode,
    "bridge_source_sha256": sha256(
        Path(native_bridge.__file__).read_bytes() if bridge_mode == "integrated" else payload
    ).hexdigest(),
    "peer_bridge_committed_source": PEER_COMMIT if bridge_mode == "peer" else None,
    "provider_capture_sha256":run["capture_sha"],
    "upstream_portfolio_intent_qualified":False,
    "admitted_PG_execution":False,
    "native_venue":"SIM",
    "simulation_instruction_sha256":run["instruction_sha256"],
    "simulation_instruction_git_blob_sha1":run["INTENT_BLOB"],
    "instruction_standing":instruction["standing"],
    "allocation_owner":"ordivon_capital.portfolio.strategic_contribution",
    "allocation_standing":plan["standing"],
    "simulation_budget_minor":plan["allocationsMinor"]["SPY"],
    "investment_policy_admitted":False,
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
    "pg_mark_snapshot_required":not pg_paper_candidate.marks,
    "settlement_date":str(session.buys[0].settlement_date),
    "external_PG_account_binding":"UNKNOWN",
    "source_is_historically_PIT":False,
    "PG_effect":"NONE",
}

# Independent adversarial check of the actual native consumer's contract:
# corrupt the immutable Git-show result (without touching Git or any owner
# worktree) and ensure no malformed/overbudget/unqualified instruction can
# generate an Order. This mock represents a corrupt source read, NOT a
# claim that the authenticated Git object was modified in reality.
valid_instruction = json.loads(run["instruction_bytes"])
source_blob = run["instruction_bytes"]
prior_native_output = (ROOT/"nautilus/next_open_result.json").read_bytes()
original_git_show = subprocess.check_output
adversarial_cases = {
    "wrong-account": {"accountId": "A-OTHER"},
    "wrong-instrument": {"instrumentId": "QQQ.SIM"},
    "wrong-source-digest": {"sourceCaptureSha256": "0"*64},
    "future-decision": {"simulatedDecisionAt": "2026-10-29T09:30:00-04:00"},
    "overbudget-limit": {"limitPrice": "1200.00"},
    "zero-quantity": {"quantity": 0},
    "fake-portfolio-admission": {"investmentPolicyAdmitted": True},
    "fake-historical-pit": {"historicalPointInTimeAdmitted": True},
    "fake-external-write": {"externalFinancialWriteAllowed": True},
    "no-fee-reserve": {"feeReserveMinor": -1},
}
for scenario, patch in adversarial_cases.items():
    doc = dict(valid_instruction)
    doc.update(patch)
    tampered_bytes = json.dumps(doc,sort_keys=True).encode("utf-8")
    def forged_git_blob(command, *args, **kwargs):
        if ("cat-file" in command and
                command[-1] == run["INTENT_BLOB"]):
            return tampered_bytes
        return original_git_show(command,*args,**kwargs)
    subprocess.check_output=forged_git_blob
    try:
        try:
            runpy.run_path(str(ROOT/"nautilus/next_open_native.py"),run_name="__main__")
        except ValueError:
            pass
        else:
            raise AssertionError(f"Unqualified instruction accepted: {scenario}")
    finally:
        subprocess.check_output=original_git_show
    assert (ROOT/"nautilus/next_open_result.json").read_bytes()==prior_native_output

# Strict JSON duplicate-key handling is part of the same failure surface.
last_close = source_blob.rstrip()
assert last_close.endswith(b"}")
double_account = last_close[:-1] + b', "accountId":"A-OTHER"}'
def duplicate_git_blob(command, *args, **kwargs):
    if "cat-file" in command and command[-1] == run["INTENT_BLOB"]:
        return double_account
    return original_git_show(command,*args,**kwargs)
subprocess.check_output=duplicate_git_blob
try:
    try:
        runpy.run_path(str(ROOT/"nautilus/next_open_native.py"),run_name="__main__")
    except ValueError:
        pass
    else:
        raise AssertionError("Duplicated economic identity JSON key accepted")
finally:
    subprocess.check_output=original_git_show

# The existing Portfolio allocator is the owner of the exact cash/reserve
# projection; an unaffordable contribution must fail there too.
bad_request={
    "schemaVersion":1,
    "kind":"ordivon.finance.portfolio.strategic-contribution-request",
    "currency":"USD",
    "cashMinor":1000000,
    "protectedReserveMinor":900000,
    "contributionMinor":100001,
    "holdingsMinor":{"SPY":0},
    "targetWeightsBps":{"SPY":10000},
}
try:
    plan_strategic_contribution(bad_request)
except ValueError:
    pass
else:
    raise AssertionError("Portfolio owner admitted contribution through reserve")

print("NATIVE_GIT_INSTRUCTION_FALSIFICATION_PASS",
      "mutated_economic_cases",len(adversarial_cases)+1,
      "source_Git_object_untouched",True,
      "actual_native_order_unchanged",True,
      "unauthorized_portfolio_spend_rejected",True)

# Counterfactual scenarios may alter synthetic NEXT-OPEN quote prices,
# NEVER the immutable Cboe source capture or committed instruction.
import os

old_scenario = os.environ.get("ORDIVON_FINANCE_R3_SIMULATION_SCENARIO")
old_shock = os.environ.get("ORDIVON_FINANCE_R3_TEST_OPEN_SHOCK_USD")
try:
    os.environ["ORDIVON_FINANCE_R3_SIMULATION_SCENARIO"]="COUNTERFACTUAL_ONLY"
    os.environ["ORDIVON_FINANCE_R3_TEST_OPEN_SHOCK_USD"]="10.00"
    shocked=runpy.run_path(str(ROOT/"nautilus/next_open_native.py"),run_name="__main__")
    shocked_orders=shocked["node"].get_engine_cache(shocked["config"].id).orders()
    shocked_fills=shocked["node"].generate_fills_report(shocked["config"].id).reset_index().to_dict("records")
    assert len(shocked_orders)==len(shocked_fills)==1
    assert shocked_orders[0].side==orders[0].side
    assert shocked_orders[0].quantity==orders[0].quantity
    assert shocked["instruction_sha256"]==run["instruction_sha256"]
    assert shocked["capture_sha"]==run["capture_sha"]
    assert shocked["prev_decision_ns"]==run["prev_decision_ns"]
    assert shocked_fills[0]["ts_event"]==fills[0]["ts_event"]
    assert Decimal(shocked_fills[0]["last_px"])-Decimal(fills[0]["last_px"])==Decimal("10.00")

    # Large overnight gap above the committed native limit must NOT buy
    # one share at an unbounded price. The native OMS, not our adapter,
    # rejects/cancels the IOC execution when its limit cannot cross.
    os.environ["ORDIVON_FINANCE_R3_TEST_OPEN_SHOCK_USD"]="500.00"
    gap=runpy.run_path(str(ROOT/"nautilus/next_open_native.py"),run_name="__main__")
    gap_orders=gap["node"].get_engine_cache(gap["config"].id).orders()
    gap_fills=gap["node"].generate_fills_report(gap["config"].id).reset_index().to_dict("records")
    assert len(gap_orders)==1 and not gap_fills
    assert gap["out"]["simulated_instruction_sha256"]==run["instruction_sha256"]
    assert gap["out"]["fill_count"]==0
    # Confirmed terminal cancellation with zero fills is a real economic
    # zero effect, not missing coverage, pending submission or a position.
    zero_day = native_bridge.next_open_native_paper_session(
        node=gap["node"], run_config_id=gap["config"].id,
        session=t, previous_session=p,
        expected_account_id=instruction["accountId"],
        opens_at=next_open, previous_close_at=prior_close,
        settlement_date=date(2026, 10, 30),
        decisions_by_order={str(o.client_order_id): prior_decision for o in gap_orders},
        instrument_symbols={instruction["instrumentId"]: instruction["symbol"]},
        marks_minor={},
    )
    assert not zero_day.buys and not zero_day.sells
    zero_value = value_session(previous, zero_day)
    assert zero_value.nav_minor == previous.nav_minor
    assert zero_value.positions == previous.positions
    assert zero_value.payable_minor == 0
    result["native_terminal_cancel_zero_fill_paper_valuation_verified"] = True
    result["gap_above_limit_refused_by_native_venue"]=True
    result["next_open_price_shock_plus_10_unchanged_order_side_qty"]=True
    print("NATIVE_FROZEN_INTENT_AND_BUDGET_ABLATION_PASS",
          "intent_sha",run["instruction_sha256"],
          "native_fill_10usd_shock",str(shocked_fills[0]["last_px"]),
          "500usd_gap_native_fill_count",len(gap_fills))
finally:
    if old_scenario is None:
        os.environ.pop("ORDIVON_FINANCE_R3_SIMULATION_SCENARIO",None)
    else:
        os.environ["ORDIVON_FINANCE_R3_SIMULATION_SCENARIO"]=old_scenario
    if old_shock is None:
        os.environ.pop("ORDIVON_FINANCE_R3_TEST_OPEN_SHOCK_USD",None)
    else:
        os.environ["ORDIVON_FINANCE_R3_TEST_OPEN_SHOCK_USD"]=old_shock

(ROOT/"nautilus/next_open_peer_bridge_result.json").write_text(
    json.dumps(result,indent=2),encoding="utf-8"
)
print("NATIVE_NEXT_OPEN_PAPER_BRIDGE_PASS",json.dumps(result))
