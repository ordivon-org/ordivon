"""Native Nautilus -> strict PaperSession -> actual isolated PostgreSQL 18 PaperClose.

Opt-in development probe only. Requires freshly initialized dedicated localhost
PG cluster and both explicit DSN and physical data-directory binding. It rejects
production databases, and uses retrospective / operator-declared synthetic marks.
There are no real orders, external transfers, or PIT-qualified investment intents.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import runpy
import sys
from dataclasses import replace
from datetime import UTC, date, datetime
from decimal import Decimal
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
CAPITAL_SRC = ROOT.parents[1] / "src"
sys.path.insert(0, str(CAPITAL_SRC))

import psycopg
from psycopg.conninfo import conninfo_to_dict

from ordivon_capital.accounting.paper_close import PaperSession
from ordivon_capital.accounting.postgres_paper_close import (
    PostgresPaperClose,
    read_committed_paper_close,
    read_latest_committed_paper_close,
)
from ordivon_capital.markets.etf_eod_snapshot import (
    SnapshotAdmissionError,
    admit_etf_eod_snapshot,
)
from ordivon_capital.trading.nautilus_paper_bridge import next_open_native_paper_session

OUT = ROOT / "output" / "native_pg_paper_e2e.json"
NY = ZoneInfo("America/New_York")
PAPER_KEY = "r3a_native_pg_ephemeral_only"
ZERO_KEY = "r3a_native_pg_no_fills_only"


def must_be_disposable_pg() -> str:
    dsn = os.environ["ORDIVON_FINANCE_R3_SANDBOX_PG_DSN"]
    expected = os.environ["ORDIVON_FINANCE_R3_SANDBOX_PG_DATA"]
    args = conninfo_to_dict(dsn)
    if {k: args.get(k) for k in ("host", "port", "dbname", "user")} != {
        "host": "127.0.0.1",
        "port": "55491",
        "dbname": "ordivon_paper",
        "user": "sandbox_finance_r3",
    }:
        raise RuntimeError("NOT an isolated dedicated Finance R3 sandbox PG DSN")
    with psycopg.connect(dsn) as db:
        actual = db.execute(
            "select current_database(), current_user, "
            "current_setting('data_directory'), inet_server_port()"
        ).fetchone()
    assert actual is not None
    observed_path = str(Path(actual[2]).resolve()).lower().replace("/", "\\")
    expected_path = str(Path(expected).resolve()).lower().replace("/", "\\")
    marker = Path(expected).parent / ".finance-r3-disposable-pg18"
    test_root_qualified = marker.is_file() and marker.read_text(encoding="utf-8").strip() == "ORDIVON_FINANCE_R3_DISPOSABLE_TEST_ONLY"
    if (actual[0] != "ordivon_paper"
        or actual[1] != "sandbox_finance_r3"
        or actual[3] != 55491
        or observed_path != expected_path
        or not test_root_qualified):
        raise RuntimeError("PG data-directory authority is not the isolated test cluster")
    return dsn


def canonical_bytes(value: object) -> bytes:
    return json.dumps(
        value, ensure_ascii=True, sort_keys=True, separators=(",", ":"),
    ).encode("utf-8")


def close_snapshot(*, session: str, price_minor: int, capture: str, export: bool = True):
    """Operator-declared synthetic/test mark, NOT a verified vendor-source fact."""
    # Capture is 2026-11-11 -- later than the Oct trade. Never backdate it.
    raw = canonical_bytes({
        "schemaVersion": 1,
        "kind": "ordivon.finance.markets.etf-eod-snapshot",
        "sourceId": "SIMULATED_TEST_MARK_POSTFACTO_NOT_A_CBOE_RECEIPT",
        "currency": "USD",
        "priceBasis": "RAW_UNADJUSTED_CLOSE",
        "rights": {
            "status": "AUTHORIZED_PRIVATE_PAPER_USE",
            "evidenceRef": "TEST_ONLY_SYNTHETIC_NOT_VENDOR_RIGHTS",
        },
        "corporateActions": {
            "coverage": "COMPLETE",
            "evidenceRef": "TEST_ONLY_SYNTHETIC_NO_REAL_ACTION_CLAIM",
            "events": [],
        },
        "capturedAt": capture,
        "supersedesSha256": None,
        "marks": [{
            "sessionDate": session,
            "instrumentId": "SPY",
            "priceMinor": price_minor,
            "availableAt": capture,
            "availabilityBasis": "FIRST_OBSERVED",
        }],
    })
    binding = dict(
        expected_sha256="sha256:" + hashlib.sha256(raw).hexdigest(),
        expected_source_id="SIMULATED_TEST_MARK_POSTFACTO_NOT_A_CBOE_RECEIPT",
        expected_rights_ref="TEST_ONLY_SYNTHETIC_NOT_VENDOR_RIGHTS",
        expected_corporate_actions_ref="TEST_ONLY_SYNTHETIC_NO_REAL_ACTION_CLAIM",
        expected_instruments=("SPY",),
        expected_session_closes={session: session + "T20:00:00Z"},
        decision_at=capture,
    )
    snapshot = admit_etf_eod_snapshot(raw, **binding)
    assert snapshot.prices_for(session) == {"SPY": price_minor}
    if export:
        # Immutable-by-digest consumer inputs to the separate mature
        # Python3.11 Risk/SciPy environment; no source/provider re-fetch.
        OUT.parent.mkdir(parents=True, exist_ok=True)
        (OUT.parent / f"pg_synthetic_mark_{session}.json").write_bytes(raw)
        (OUT.parent / f"pg_synthetic_binding_{session}.json").write_bytes(
            canonical_bytes(binding)
        )
    # The exact same backfilled mark MUST NOT be treated as available in Oct.
    try:
        admit_etf_eod_snapshot(
            raw, **(binding | {"decision_at": "2026-10-28T20:01:00Z"})
        )
    except SnapshotAdmissionError as exc:
        assert "captured after" in str(exc)
    else:
        raise AssertionError("POSTFACTO market mark was accepted at historical intent time")
    return snapshot


def calendar_bytes():
    rows = [
        {"date": day, "open": "13:30:00Z", "close": "20:00:00Z", "clears": True}
        for day in ("2026-10-28", "2026-10-29", "2026-10-30")
    ]
    return canonical_bytes({
        "market_source": "TEST_ONLY_SYNTHETIC_NY_CALENDAR",
        "clearing_source": "TEST_ONLY_SYNTHETIC_TPLUS1",
        "days": rows,
    })


def require_fixture_source(run):
    doc = run["instruction"]
    assert doc["standing"] == "SIMULATION_FIXTURE_ONLY"
    assert doc["investmentPolicyAdmitted"] is False
    assert doc["historicalPointInTimeAdmitted"] is False
    assert doc["externalFinancialWriteAllowed"] is False
    assert run["out"]["native_order_matches_committed_intent"] is True
    assert doc["accountId"] == run["out"]["native_account_id"]
    assert doc["sourceCaptureSha256"] == run["capture_sha"]
    assert doc["researchDatasetSha256"] == run["manifest"]["qlib_dataset_sha256"]
    return doc


def write_and_test(dsn: str):
    # Native engine owns Order / Fill / Cache mechanics. No second OMS.
    run = runpy.run_path(str(ROOT / "nautilus/next_open_native.py"), run_name="__main__")
    instruction = require_fixture_source(run)
    node = run["node"]
    cfg = run["config"]
    actual_orders = node.get_engine_cache(cfg.id).orders()
    assert len(actual_orders) == 1
    fills = node.generate_fills_report(cfg.id).reset_index().to_dict("records")
    assert len(fills) == 1 and fills[0]["account_id"] == instruction["accountId"]
    t = date.fromisoformat(run["next_date"])
    p = date.fromisoformat(run["prev_date"])
    opened = datetime.fromisoformat(t.isoformat() + "T09:30:00-04:00")
    prior_close = datetime.fromisoformat(p.isoformat() + "T16:00:00-04:00")
    decision = datetime.fromisoformat(instruction["simulatedDecisionAt"])
    session = next_open_native_paper_session(
        node=node, run_config_id=cfg.id, session=t, previous_session=p,
        expected_account_id=instruction["accountId"],
        opens_at=opened, previous_close_at=prior_close,
        settlement_date=date(2026, 10, 30),
        decisions_by_order={run["out"]["simulated_client_order_id"]: decision},
        instrument_symbols={instruction["instrumentId"]: instruction["symbol"]},
        marks_minor={},
    )
    assert len(session.buys) == 1 and len(session.sells) == 0 and session.marks == {}
    buy = session.buys[0]
    assert buy.shares == instruction["quantity"] == 1
    assert buy.cost_minor == 76881
    assert str(buy.filled_at.astimezone(UTC)) == "2026-10-29 13:30:00+00:00"
    assert buy.fill_id.startswith("nautilus-paper:SIM-001:")

    # First available at actual 2026-11-11 capture, not the Oct decision.
    captured = datetime.fromisoformat(run["manifest"]["captured_at"])
    if captured.date() <= t:
        raise RuntimeError("fixture capture no longer demonstrates PIT separation")
    capture = captured.astimezone(UTC).isoformat(timespec="microseconds").replace("+00:00", "Z")
    trade_mark = close_snapshot(
        session=t.isoformat(),
        price_minor=int(Decimal(run["b"]["close"]) * 100),
        capture=capture,
    )
    next_day = date(2026, 10, 30)
    close2 = int(Decimal(run["today"][next_day.isoformat()]["close"]) * 100)
    following_mark = close_snapshot(
        session=next_day.isoformat(), price_minor=close2, capture=capture
    )
    cal = calendar_bytes()
    cal_sha = hashlib.sha256(cal).hexdigest()

    store = PostgresPaperClose(dsn)
    opening = PaperSession(
        session=p, previous_session=None,
        contribution_minor=1_000_000, reserve_contribution_minor=900_000,
        marks={}, buys=(),
    )
    initial = store.close_session(PAPER_KEY, opening)
    assert initial["valuation"]["nav_minor"] == 1_000_000
    assert initial["valuation"]["protected_minor"] == 900_000
    assert initial["valuation"]["positions"] == {}
    assert store.close_session(PAPER_KEY, opening) == initial

    posted = store.close_session(
        PAPER_KEY, session, mark_snapshot=trade_mark,
        calendar_bytes=cal, calendar_sha256=cal_sha,
    )
    after_trade = posted["valuation"]
    assert posted["market_evidence"]["standing"] == "OPERATOR_BOUND_MARKS"
    assert posted["market_evidence"]["captured_at"].startswith("2026-11-11")
    assert posted["execution_evidence"]["fill_count"] == 1
    assert posted["execution_evidence"]["settlement_date"] == "2026-10-30"
    assert after_trade["positions"] == {"SPY": 1}
    assert after_trade["payable_minor"] == buy.cost_minor
    assert after_trade["cash_minor"] == 1_000_000
    assert after_trade["protected_minor"] == 900_000
    assert after_trade["nav_minor"] == 1_000_055
    assert read_committed_paper_close(dsn, PAPER_KEY, t) == posted
    # Replaying same economic facts is idempotent across freshly opened
    # PostgreSQL connections. A changed mark at the SAME session conflicts.
    replayed = PostgresPaperClose(dsn).close_session(
        PAPER_KEY, session, mark_snapshot=trade_mark,
        calendar_bytes=cal, calendar_sha256=cal_sha,
    )
    assert replayed == posted
    changed_mark = close_snapshot(
        session=t.isoformat(),
        price_minor=int(Decimal(run["b"]["close"]) * 100) + 1,
        capture=capture, export=False,
    )
    try:
        PostgresPaperClose(dsn).close_session(
            PAPER_KEY, session, mark_snapshot=changed_mark,
            calendar_bytes=cal, calendar_sha256=cal_sha,
        )
    except ValueError as exc:
        assert "conflicting inputs" in str(exc)
    else:
        raise AssertionError("conflicting economic mark silently replaced committed receipt")
    assert read_committed_paper_close(dsn, PAPER_KEY, t) == posted

    # T+1 real PG settlement on 2026-10-30 (Friday). No new fill.
    settlement_day = PaperSession(
        session=next_day, previous_session=t,
        contribution_minor=0, reserve_contribution_minor=0,
        marks={}, buys=(),
    )
    settled = PostgresPaperClose(dsn).close_session(
        PAPER_KEY, settlement_day, mark_snapshot=following_mark,
        calendar_bytes=cal, calendar_sha256=cal_sha,
    )
    valuation = settled["valuation"]
    assert settled["previous_request_sha256"] == posted["request_sha256"]
    assert valuation["cash_minor"] == 1_000_000 - buy.cost_minor
    assert valuation["protected_minor"] == 900_000
    assert valuation["payable_minor"] == 0
    assert valuation["pending"] == {}
    assert valuation["positions"] == {"SPY": 1}
    assert valuation["nav_minor"] == valuation["cash_minor"] + close2
    assert read_latest_committed_paper_close(dsn, PAPER_KEY) == settled
    assert PostgresPaperClose(dsn).close_session(
        PAPER_KEY, settlement_day, mark_snapshot=following_mark,
        calendar_bytes=cal, calendar_sha256=cal_sha,
    ) == settled

    # Genuine 0-Fill terminal state from native Limit IOC +500 USD gap
    # -> empty PaperSession -> PG 0-effect daily close on separate account.
    old_shock = os.environ.get("ORDIVON_FINANCE_R3_TEST_OPEN_SHOCK_USD")
    old_scenario = os.environ.get("ORDIVON_FINANCE_R3_SIMULATION_SCENARIO")
    try:
        os.environ["ORDIVON_FINANCE_R3_SIMULATION_SCENARIO"] = "COUNTERFACTUAL_ONLY"
        os.environ["ORDIVON_FINANCE_R3_TEST_OPEN_SHOCK_USD"] = "500.00"
        canceled = runpy.run_path(
            str(ROOT / "nautilus/next_open_native.py"), run_name="__main__"
        )
    finally:
        if old_shock is None:
            os.environ.pop("ORDIVON_FINANCE_R3_TEST_OPEN_SHOCK_USD", None)
        else:
            os.environ["ORDIVON_FINANCE_R3_TEST_OPEN_SHOCK_USD"] = old_shock
        if old_scenario is None:
            os.environ.pop("ORDIVON_FINANCE_R3_SIMULATION_SCENARIO", None)
        else:
            os.environ["ORDIVON_FINANCE_R3_SIMULATION_SCENARIO"] = old_scenario
    assert canceled["out"]["fill_count"] == 0
    zero = next_open_native_paper_session(
        node=canceled["node"], run_config_id=canceled["config"].id,
        session=t, previous_session=p, expected_account_id=instruction["accountId"],
        opens_at=opened, previous_close_at=prior_close,
        settlement_date=next_day,
        decisions_by_order={canceled["out"]["simulated_client_order_id"]:decision},
        instrument_symbols={instruction["instrumentId"]: instruction["symbol"]},
        marks_minor={},
    )
    assert not zero.buys and not zero.sells
    zero_opening = store.close_session(ZERO_KEY, opening)
    zero_posted = store.close_session(
        ZERO_KEY, zero, mark_snapshot=trade_mark,
        calendar_bytes=cal, calendar_sha256=cal_sha,
    )
    assert zero_posted["valuation"]["cash_minor"] == 1_000_000
    assert zero_posted["valuation"]["payable_minor"] == 0
    assert zero_posted["valuation"]["positions"] == {}
    assert zero_posted["valuation"]["nav_minor"] == 1_000_000
    assert zero_posted["execution_evidence"]["fill_count"] == 0
    assert zero_posted["previous_request_sha256"] == zero_opening["request_sha256"]

    # No account leakage or duplicated transfers.
    with psycopg.connect(dsn) as db:
        rows = db.execute(
            "SELECT account_key, session, request_sha256 "
            "FROM ordivon_paper.daily_close ORDER BY account_key, session"
        ).fetchall()
        assert len(rows) == 5, rows
        transfers = db.execute(
            "SELECT operation, status, amount "
            "FROM ordivon_capital.transfers ORDER BY operation, amount"
        ).fetchall()
        assert transfers
    result = {
        "kind": "ordivon.finance.r3.native-etf-isolated-postgresql-paper-proof",
        "evidence_standing": "SIMULATED_POSTFACTO_PAPER_LEDGER_ONLY",
        "source_cut": run["source_cut"],
        "native_engine": "NautilusTrader 2.0.0rc9",
        "postgres_server": "18.6 disposable localhost separate cluster",
        "psycopg_client": psycopg.__version__,
        "native_frozen_instruction_sha256": run["instruction_sha256"],
        "source_capture_sha256": run["capture_sha"],
        "provider_historical_pit_admitted": False,
        "operator_mark_captured_at": capture,
        "operator_mark_original_vendor_authenticity_verified": False,
        "historical_decision_at": instruction["simulatedDecisionAt"],
        "first_order_trade_id": str(fills[0]["trade_id"]),
        "native_buy_fill_count": len(fills),
        "native_canceled_fill_count": 0,
        "native_canceled_paper_buy_count": len(zero.buys),
        "native_cancelled_pg_cash_nav_unchanged": True,
        "market_snapshot_sha256": trade_mark.sha256,
        "calendar_sha256": cal_sha,
        "PG_close_request_sha256": posted["request_sha256"],
        "PG_settlement_request_sha256": settled["request_sha256"],
        "PG_close_traded_nav_minor": after_trade["nav_minor"],
        "risk_and_performance_consumed_real_pg_readback": False,
        "PG_settled_cash_minor": valuation["cash_minor"],
        "PG_settlement_nav_minor": valuation["nav_minor"],
        "PG_zero_fill_nav_minor": zero_posted["valuation"]["nav_minor"],
        "PG_receipt_rows": len(rows),
        "PG_ledger_transfer_rows": len(transfers),
        "PG_same_request_replayed_without_extra_rows": True,
        "PG_conflicting_replay_rejected": True,
        "PG_restart_readback_proven": False,
        "real_money_orders_or_transfers": 0,
        "PG_system": "TEST_ONLY_FRESH_PRIVATE_POSTGRES_CLUSTER",
    }
    OUT.parent.mkdir(parents=True,exist_ok=True)
    OUT.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print("R3_PG_NATIVE_WRITE_AND_TPLUS1_PASS",json.dumps(result,sort_keys=True))


def verify_after_database_restart(dsn: str):
    result = json.loads(OUT.read_text(encoding="utf-8"))
    assert result["PG_restart_readback_proven"] is False
    assert result["risk_and_performance_consumed_real_pg_readback"] is True
    day = date(2026, 10, 29)
    maturity = date(2026, 10, 30)
    posted = read_committed_paper_close(dsn, PAPER_KEY, day)
    settled = read_latest_committed_paper_close(dsn, PAPER_KEY)
    assert settled is not None
    assert settled["valuation"]["session"] == maturity.isoformat()
    assert posted["request_sha256"] == result["PG_close_request_sha256"]
    assert settled["request_sha256"] == result["PG_settlement_request_sha256"]
    assert settled["previous_request_sha256"] == posted["request_sha256"]
    assert settled["valuation"]["cash_minor"] == result["PG_settled_cash_minor"]
    assert settled["valuation"]["nav_minor"] == result["PG_settlement_nav_minor"]
    zero = read_latest_committed_paper_close(dsn,ZERO_KEY)
    assert zero is not None and zero["valuation"]["nav_minor"] == 1_000_000
    with psycopg.connect(dsn) as db:
        assert db.execute("SELECT COUNT(*) FROM ordivon_paper.daily_close").fetchone() == (5,)
        assert db.execute("SELECT COUNT(*) FROM ordivon_capital.transfers").fetchone()[0] == result["PG_ledger_transfer_rows"]
    result["PG_restart_readback_proven"] = True
    OUT.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print("R3_PG_NATIVE_RESTART_READBACK_PASS",json.dumps(result,sort_keys=True))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("phase", choices=("write","verify-restart"))
    phase = parser.parse_args().phase
    dsn = must_be_disposable_pg()
    if phase == "write":
        write_and_test(dsn)
    else:
        verify_after_database_restart(dsn)


if __name__ == "__main__":
    main()
