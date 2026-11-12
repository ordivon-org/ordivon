"""Native Qlib-selected BUY/HOLD/SELL into the existing disposable PostgreSQL Paper ledger.

Consumes exactly the PaperSession inputs produced by the prior real Nautilus/Paper
probe; no second execution, fill, valuation, or accounting algorithm. TEST ONLY.
"""
from __future__ import annotations

import argparse
import json
import os
import runpy
import sys
from datetime import date
from pathlib import Path

if sys.flags.optimize:
    raise RuntimeError("Financial probe must run with normal Python assertions")

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parents[1] / "src"))
from probe_native_pg_paper_close import must_be_disposable_pg
from ordivon_capital.accounting.postgres_paper_close import (
    PostgresPaperClose,
    read_committed_paper_close,
    read_latest_committed_paper_close,
)

HOLD = int(os.environ["ORDIVON_FINANCE_R3_HOLD_SESSIONS"])
if HOLD not in (5, 20):
    raise ValueError("Only preregistered H5/H20 holdings can be consumed")
NO_ENTRY = os.environ.get("ORDIVON_FINANCE_R3_TEST_NO_ENTRY") == "1"
ACCOUNT = f"r3q1_qlib_h{HOLD}_{'zero' if NO_ENTRY else 'filled'}"
EVIDENCE = ROOT / "output" / f"qlib_native_pg_h{HOLD}_{'zero' if NO_ENTRY else 'filled'}.json"


def write(dsn: str) -> None:
    run = runpy.run_path(str(ROOT / "tests" / "probe_native_buy_hold_exit.py"), run_name="__main__")
    statement = run["standing"]
    if not (
        statement["standing"] == "SIMULATION_ONLY_NON_PIT_NOT_CAPITAL_AUTHORIZED"
        and statement["Qlib_target_vs_native_exit_event_identical"] is True
        and statement["historical_point_in_time_qualified"] is False
        and statement["portfolio_automatic_execution_authorized"] is False
        and statement["real_broker_or_PG_effect"] == "NONE"
        and statement["native_open_position_count"] == 0
        and statement["receivable_settled"] is True
    ):
        raise RuntimeError("Unqualified model/native/Paper state")
    fills = run["fill_rows"]
    if len(fills) != (0 if NO_ENTRY else 2):
        raise RuntimeError("Native order effects do not match the requested case")
    if fills and {str(fill["account_id"]) for fill in fills} != {"SIM-001"}:
        raise RuntimeError("Unexpected native simulated account")
    sessions = run["paper_sessions"]
    expected = run["state"]
    if not sessions or sessions[0].previous_session is not None:
        raise RuntimeError("Missing the original Paper opening session")

    # The PG account key is explicitly test-scoped, not a real customer mapping.
    store = PostgresPaperClose(dsn)
    receipts = []
    for session in sessions:
        receipt = store.close_session(ACCOUNT, session)
        if receipt["market_evidence"]["standing"] != "CALLER_SUPPLIED_MARKS":
            raise RuntimeError("Retrospective marks were silently promoted")
        if read_committed_paper_close(dsn, ACCOUNT, session.session) != receipt:
            raise RuntimeError("Actual PG receipt is inconsistent")
        receipts.append(receipt)
    final = receipts[-1]["valuation"]
    if (
        final["cash_minor"] != expected.cash_minor
        or final["nav_minor"] != expected.nav_minor
        or final["protected_minor"] != expected.protected_minor
        or final["positions"] != expected.positions
        or final.get("pending", {}) != expected.pending
        or final.get("pending_sales", {}) != expected.pending_sales
    ):
        raise RuntimeError("Native-derived Paper state differs from durable PG economics")
    if expected.positions or expected.pending or expected.pending_sales:
        raise RuntimeError("Terminal Paper position is not settled")
    if NO_ENTRY and final["cash_minor"] != 1_000_000:
        raise RuntimeError("Canceled entry changed PG cash")
    if not NO_ENTRY and final["cash_minor"] != statement["last_paper_cash_minor"]:
        raise RuntimeError("PG cash differs from native economic outcome")
    if store.close_session(ACCOUNT, sessions[-1]) != receipts[-1]:
        raise RuntimeError("Idempotent close changed receipt")

    result = {
        "kind": "ordivon.finance.r3.qlib-native-postgresql-paper",
        "standing": "SIMULATION_ONLY_RETROSPECTIVE_CALLER_MARKS",
        "nativeAccount": "SIM-001",
        "pgAccountKey": ACCOUNT,
        "realAccountMappingAuthorized": False,
        "pointInTimeMarketDataQualified": False,
        "realBrokerEffects": 0,
        "horizonSessions": HOLD,
        "selectedInstrument": statement["selected_instrument"],
        "nativeFillCount": len(fills),
        "sessionReceipts": [
            {"session": item["valuation"]["session"], "requestSha256": item["request_sha256"]}
            for item in receipts
        ],
        "finalCashMinor": final["cash_minor"],
        "finalNavMinor": final["nav_minor"],
        "protectedMinor": final["protected_minor"],
        "restartReadback": False,
    }
    EVIDENCE.parent.mkdir(parents=True, exist_ok=True)
    EVIDENCE.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    print("Q1_MODEL_NATIVE_PG_WRITE_PASS", json.dumps(result, sort_keys=True), flush=True)


def verify_restart(dsn: str) -> None:
    data = json.loads(EVIDENCE.read_text(encoding="utf-8"))
    if data["restartReadback"] is not False or data["pgAccountKey"] != ACCOUNT:
        raise RuntimeError("Wrong PostgreSQL restart checkpoint")
    for item in data["sessionReceipts"]:
        receipt = read_committed_paper_close(dsn, ACCOUNT, date.fromisoformat(item["session"]))
        if receipt["request_sha256"] != item["requestSha256"]:
            raise RuntimeError("Previously committed PG receipt changed")
    latest = read_latest_committed_paper_close(dsn, ACCOUNT)
    if latest is None or (
        latest["valuation"]["cash_minor"] != data["finalCashMinor"]
        or latest["valuation"]["nav_minor"] != data["finalNavMinor"]
        or latest["valuation"]["protected_minor"] != data["protectedMinor"]
    ):
        raise RuntimeError("Final financial account changed after PG restart")
    data["restartReadback"] = True
    EVIDENCE.write_text(json.dumps(data, indent=2, sort_keys=True), encoding="utf-8")
    print("Q1_MODEL_NATIVE_PG_RESTART_READBACK_PASS", json.dumps(data, sort_keys=True), flush=True)


if __name__ == "__main__":
    cli = argparse.ArgumentParser()
    cli.add_argument("phase", choices=("write", "verify-restart"))
    mode = cli.parse_args().phase
    dsn = must_be_disposable_pg()
    (write if mode == "write" else verify_restart)(dsn)
