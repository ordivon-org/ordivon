"""Independent Python3.11/SciPy Risk+Portfolio consumer of actual native PG receipts.

Reads only committed PostgreSQL 18 PaperClose and the exact market snapshot
bytes written by the separate native Python3.15/Nautilus consumer. No new
risk/portfolio math; no writes to financial tables or real money effects.
"""
from __future__ import annotations

import json
import os
import sys
from datetime import UTC, date, datetime
from pathlib import Path

# Optimized Python removes assertion-based economic/provenance checks.
# This TEST-ONLY runner must never create a PG effect without them.
if sys.flags.optimize:
    raise RuntimeError("Finance R3 native acceptance requires non-optimized Python")

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parents[1] / "src"))

import psycopg
from psycopg.conninfo import conninfo_to_dict

from ordivon_capital.accounting.postgres_paper_close import (
    read_committed_paper_close, read_latest_committed_paper_close,
)
from ordivon_capital.markets.etf_eod_snapshot import admit_etf_eod_snapshot
from ordivon_capital.risk.paper_close_risk import review_paper_close_risk
from ordivon_capital.portfolio.paper_close_performance import summarize_paper_period


def strictly_disposable_dsn():
    dsn = os.environ["ORDIVON_FINANCE_R3_SANDBOX_PG_DSN"]
    bound = os.environ["ORDIVON_FINANCE_R3_SANDBOX_PG_DATA"]
    args = conninfo_to_dict(dsn)
    assert (args["host"],args["port"],args["dbname"],args["user"]) == (
        "127.0.0.1","55491","ordivon_paper","sandbox_finance_r3"
    )
    with psycopg.connect(dsn) as db:
        database, data_dir = db.execute(
            "SELECT current_database(), current_setting('data_directory')"
        ).fetchone()
    assert database == "ordivon_paper"
    assert str(Path(data_dir).resolve()).lower() == str(Path(bound).resolve()).lower()
    marker = Path(bound).parent / ".finance-r3-disposable-pg18"
    assert marker.is_file() and marker.read_text(encoding="utf-8").strip() == "ORDIVON_FINANCE_R3_DISPOSABLE_TEST_ONLY"
    return dsn


def admit_synthetic_retrospective(day):
    name = day.isoformat()
    path = ROOT / "output"
    raw = (path / f"pg_synthetic_mark_{name}.json").read_bytes()
    binding = json.loads((path / f"pg_synthetic_binding_{name}.json").read_bytes())
    snapshot = admit_etf_eod_snapshot(raw, **binding)
    assert "SIMULATED_TEST_MARK_POSTFACTO" in snapshot.source_id
    assert snapshot.captured_at.date() == date(2026,11,11)
    assert snapshot.captured_at.astimezone(UTC).date() > day
    return snapshot


def check_written_risk_and_performance():
    dsn = strictly_disposable_dsn()
    p = date(2026,10,28)
    t = date(2026,10,29)
    clear = date(2026,10,30)
    base = read_committed_paper_close(dsn,"r3a_native_pg_ephemeral_only",p)
    bought = read_committed_paper_close(dsn,"r3a_native_pg_ephemeral_only",t)
    settled = read_latest_committed_paper_close(dsn,"r3a_native_pg_ephemeral_only")
    assert settled is not None and settled["valuation"]["session"] == clear.isoformat()
    mark_t = admit_synthetic_retrospective(t)
    mark_clear = admit_synthetic_retrospective(clear)
    assert bought["market_evidence"]["sha256"] == mark_t.sha256
    assert bought["market_evidence"]["valuation_as_of"] == mark_t.decision_at.isoformat()
    assert bought["market_evidence"]["captured_at"] == mark_t.captured_at.isoformat()

    risk_t = review_paper_close_risk(receipt=bought,snapshot=mark_t)
    perf_t = summarize_paper_period(
        current_receipt=bought,previous_receipt=base,snapshot=mark_t
    )
    assert risk_t["netAssetValueMinor"] == bought["valuation"]["nav_minor"] == 1000055
    assert risk_t["marketCapturedAt"] == mark_t.captured_at.isoformat()
    assert perf_t["marketCapturedAt"] == mark_t.captured_at.isoformat()
    assert risk_t["marketValuationAsOf"] == bought["market_evidence"]["valuation_as_of"]
    assert perf_t["marketValuationAsOf"] == risk_t["marketValuationAsOf"]
    assert risk_t["unencumberedCashMinor"] == 23119
    assert perf_t["closingNavMinor"] == 1000055
    assert perf_t["fundingNeutralEconomicGainMinor"] == 55
    assert risk_t["sourceProviderAuthenticityIndependentlyVerified"] is False
    assert perf_t["sourceProviderAuthenticityIndependentlyVerified"] is False
    assert risk_t["realMoneyOrdersAuthorized"] is False

    risk_clear = review_paper_close_risk(receipt=settled,snapshot=mark_clear)
    perf_clear = summarize_paper_period(
        current_receipt=settled,previous_receipt=bought,snapshot=mark_clear
    )
    assert risk_clear["netAssetValueMinor"] == 998691
    assert perf_clear["closingNavMinor"] == 998691
    assert perf_clear["fundingNeutralEconomicGainMinor"] == -1364
    assert risk_clear["unencumberedCashMinor"] == 23119
    assert perf_clear["capitalAuthority"] == "SIMULATION_ONLY"
    assert perf_clear["previousRequestSha256"] == bought["request_sha256"]

    # Separate true terminal 0-fill from missing history in durable PG, too.
    zero = read_latest_committed_paper_close(dsn, "r3a_native_pg_no_fills_only")
    assert zero is not None and zero["valuation"]["nav_minor"] == 1_000_000
    risk_zero=review_paper_close_risk(receipt=zero,snapshot=mark_t)
    assert risk_zero["netAssetValueMinor"] == 1_000_000
    assert risk_zero["grossPositionValueMinor"] == 0

    path=ROOT/"output"/"native_pg_paper_e2e.json"
    result=json.loads(path.read_text(encoding="utf-8"))
    assert result["PG_close_request_sha256"]==bought["request_sha256"]
    assert result["PG_settlement_request_sha256"]==settled["request_sha256"]
    result.update({
        "risk_and_performance_consumed_real_pg_readback":True,
        "risk_trade_unencumbered_cash_minor":risk_t["unencumberedCashMinor"],
        "risk_settlement_unencumbered_cash_minor":risk_clear["unencumberedCashMinor"],
        "portfolio_trade_gain_minor":perf_t["fundingNeutralEconomicGainMinor"],
        "portfolio_settlement_gain_minor":perf_clear["fundingNeutralEconomicGainMinor"],
        "risk_terminal_zero_fill_exposure_minor":risk_zero["grossPositionValueMinor"],
        "market_observation_after_historical_session":True,
        "market_observed_at":mark_t.captured_at.isoformat(),
        "risk_budget_standing":risk_t["standing"],
        "risk_native_math_implemented_by":"ordivon_capital.risk.paper_close_risk",
        "portfolio_performance_implemented_by":"ordivon_capital.portfolio.paper_close_performance",
        "external_risk_or_portfolio_authority":"NOT_ADMITTED",
    })
    path.write_text(json.dumps(result,sort_keys=True,indent=2)+"\n",encoding="utf-8")
    print("R3_PG_DURABLE_RISK_PORTFOLIO_CONSUMERS_PASS",json.dumps({
        "risk_cash_minor":risk_t["unencumberedCashMinor"],
        "period_gain_trade_minor":perf_t["fundingNeutralEconomicGainMinor"],
        "period_gain_settle_minor":perf_clear["fundingNeutralEconomicGainMinor"],
        "zero_fill_risk_exposure_minor":risk_zero["grossPositionValueMinor"],
        "market_observed_at":mark_t.captured_at.isoformat(),
        "historical_PIT":False,
        "client":"psycopg "+psycopg.__version__,
    },sort_keys=True))


if __name__=="__main__":
    check_written_risk_and_performance()
