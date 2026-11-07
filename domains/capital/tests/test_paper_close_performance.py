"""Actual Markets -> Accounting -> Risk -> Portfolio source consumer tests."""

from __future__ import annotations

import copy
import hashlib
import json
import os
import subprocess
import sys
from dataclasses import asdict
from datetime import date, datetime
from decimal import ROUND_DOWN, ROUND_UP, localcontext
from pathlib import Path
from uuid import uuid4

import pytest

from ordivon_capital.accounting.paper_close import (
    PaperBuy,
    PaperSession,
    value_session,
)
from ordivon_capital.markets.etf_eod_snapshot import admit_etf_eod_snapshot
from ordivon_capital.portfolio.paper_close_performance import (
    PaperPerformanceError,
    summarize_paper_period,
)

ROOT = Path(__file__).resolve().parents[1]


def _market(day="2026-01-09", price=10_200):
    captured = f"{day}T21:10:00Z"
    source = {
        "schemaVersion": 1,
        "kind": "ordivon.finance.markets.etf-eod-snapshot",
        "sourceId": "performance-synthetic",
        "currency": "USD",
        "priceBasis": "RAW_UNADJUSTED_CLOSE",
        "rights": {"status": "AUTHORIZED_PRIVATE_PAPER_USE", "evidenceRef": "synthetic"},
        "corporateActions": {
            "coverage": "COMPLETE", "evidenceRef": "synthetic", "events": []
        },
        "capturedAt": captured,
        "supersedesSha256": None,
        "marks": [{
            "sessionDate": day,
            "instrumentId": "ETF",
            "priceMinor": price,
            "availableAt": captured,
            "availabilityBasis": "FIRST_OBSERVED",
        }],
    }
    raw = json.dumps(source, sort_keys=True).encode()
    binding = {
        "expected_sha256": "sha256:" + hashlib.sha256(raw).hexdigest(),
        "expected_source_id": "performance-synthetic",
        "expected_rights_ref": "synthetic",
        "expected_corporate_actions_ref": "synthetic",
        "expected_instruments": ["ETF"],
        "expected_session_closes": {day: f"{day}T21:00:00Z"},
        "decision_at": captured,
    }
    return raw, binding, admit_etf_eod_snapshot(raw, **binding)


def _case(*, funding=100_000):
    raw, binding, snapshot = _market()
    first = PaperSession(date(2026, 1, 8), None, 1_000_000, 300_000, {}, ())
    prior = value_session(None, first)
    buy = PaperBuy(
        "performance-buy", "ETF", 10, 10_000, 100,
        datetime.fromisoformat("2026-01-08T16:15:00-05:00"),
        datetime.fromisoformat("2026-01-09T09:30:00-05:00"),
    )
    second = PaperSession(
        date(2026, 1, 9), first.session, funding, 0,
        snapshot.prices_for("2026-01-09"), (buy,),
    )
    current = value_session(prior, second)
    previous_receipt = {
        "schema_version": 1,
        "mode": "PAPER",
        "account_key": "daily-performance-test",
        "request_sha256": "a" * 64,
        "previous_request_sha256": None,
        "valuation": asdict(prior) | {"session": prior.session.isoformat()},
        "market_evidence": {"standing": "CALLER_SUPPLIED_MARKS"},
    }
    current_receipt = {
        "schema_version": 1,
        "mode": "PAPER",
        "account_key": "daily-performance-test",
        "request_sha256": "b" * 64,
        "previous_request_sha256": previous_receipt["request_sha256"],
        "valuation": asdict(current) | {"session": current.session.isoformat()},
        "market_evidence": {
            "standing": "OPERATOR_BOUND_MARKS",
            "sha256": snapshot.sha256,
            "source_id": snapshot.source_id,
            "rights_ref": snapshot.rights_ref,
            "corporate_actions_ref": snapshot.corporate_actions_ref,
            "captured_at": snapshot.captured_at.isoformat(),
            "valuation_as_of": snapshot.decision_at.isoformat(),
            "session_closes": {
                mark.session_date: mark.session_close_at.isoformat()
                for mark in snapshot.marks
            },
            "instrument_ids": ["ETF"],
            "supersedes_sha256": None,
        },
    }
    return raw, binding, snapshot, previous_receipt, current_receipt, first, second


def test_funding_neutral_gain_uses_accounting_nav_and_risk_oracle():
    _, _, snapshot, previous, current, _, _ = _case()
    report = summarize_paper_period(
        current_receipt=current, previous_receipt=previous, snapshot=snapshot
    )
    assert report["previousNavMinor"] == 1_000_000
    assert report["contributionMinor"] == 100_000
    assert report["startPeriodCapitalBaseMinor"] == 1_100_000
    assert report["closingNavMinor"] == 1_101_900
    assert report["fundingNeutralEconomicGainMinor"] == 1_900
    assert report["simplePeriodReturnDecimal"] == "0.001727272727272727"
    assert report["riskStanding"] == "RISK_BUDGET_INCOMPLETE"
    assert report["marketSha256"] == snapshot.sha256
    assert report["accountingPersistenceReverified"] is False
    assert report["sourceProviderAuthenticityIndependentlyVerified"] is False
    assert report["realMoneyOrdersAuthorized"] is False


def test_large_external_contribution_is_not_investment_profit():
    _, _, snapshot, previous, current, _, _ = _case(funding=1_000_000)
    report = summarize_paper_period(
        current_receipt=current, previous_receipt=previous, snapshot=snapshot
    )
    assert report["closingNavMinor"] == 2_001_900
    assert report["fundingNeutralEconomicGainMinor"] == 1_900
    assert report["simplePeriodReturnDecimal"] == "0.000950000000000000"


def test_no_external_contribution_reports_actual_gain():
    _, _, snapshot, previous, current, _, _ = _case(funding=0)
    report = summarize_paper_period(
        current_receipt=current, previous_receipt=previous, snapshot=snapshot
    )
    assert report["fundingNeutralEconomicGainMinor"] == 1_900
    assert report["simplePeriodReturnDecimal"] == "0.001900000000000000"


def test_genesis_is_explicitly_unrated():
    _, _, snapshot = _market(day="2026-01-08")
    first = value_session(
        None, PaperSession(date(2026, 1, 8), None, 1_000_000, 300_000, {}, ())
    )
    current = {
        "schema_version": 1, "mode": "PAPER", "account_key": "genesis",
        "request_sha256": "e" * 64, "previous_request_sha256": None,
        "valuation": asdict(first) | {"session": first.session.isoformat()},
        "market_evidence": {
            "standing": "OPERATOR_BOUND_MARKS",
            "sha256": snapshot.sha256,
            "source_id": snapshot.source_id,
            "rights_ref": snapshot.rights_ref,
            "corporate_actions_ref": snapshot.corporate_actions_ref,
            "captured_at": snapshot.captured_at.isoformat(),
            "valuation_as_of": snapshot.decision_at.isoformat(),
            "session_closes": {"2026-01-08": "2026-01-08T21:00:00+00:00"},
            "instrument_ids": ["ETF"],
            "supersedes_sha256": None,
        },
    }
    output = summarize_paper_period(
        current_receipt=current, previous_receipt=None, snapshot=snapshot
    )
    assert output["closingNavMinor"] == 1_000_000
    assert output["previousNavMinor"] is None
    assert output["fundingNeutralEconomicGainMinor"] is None
    assert output["simplePeriodReturnDecimal"] is None


@pytest.mark.parametrize("mutation,reason", [
    (lambda a, b: b.update(account_key="different"), "accounts differ"),
    (lambda a, b: b.update(previous_request_sha256="0"*64), "predecessor chain"),
    (lambda a, b: a.update(request_sha256="z"*64), "SHA-256"),
    (lambda a, b: a["valuation"].update(session="2026-01-09"), "previous close"),
    (lambda a, b: b["valuation"].update(contribution_minor=-1), "nonnegative"),
    (lambda a, b: b["valuation"].update(nav_minor=1_101_901), "NAV contradicts"),
    (lambda a, b: b["market_evidence"].update(source_id="forged"), "market evidence"),
    (lambda a, b: b["valuation"]["positions"].update(ETF=11), "NAV contradicts"),
])
def test_inconsistent_receipt_chain_and_economic_inputs_rejected(mutation, reason):
    _, _, snapshot, previous, current, _, _ = _case()
    previous, current = copy.deepcopy(previous), copy.deepcopy(current)
    mutation(previous, current)
    with pytest.raises(ValueError, match=reason):
        summarize_paper_period(
            current_receipt=current, previous_receipt=previous, snapshot=snapshot
        )


def test_missing_predecessor_is_not_treated_as_new_account():
    _, _, snapshot, _, current, _, _ = _case()
    with pytest.raises(PaperPerformanceError, match="previous Accounting receipt"):
        summarize_paper_period(
            current_receipt=current, previous_receipt=None, snapshot=snapshot
        )


def test_real_stdin_files_use_existing_markets_risk_accounting_sources(tmp_path):
    raw, binding, _, previous, current, _, _ = _case()
    (tmp_path / "market.json").write_bytes(raw)
    for name, data in (
        ("binding.json", binding),
        ("previous.json", previous),
        ("current.json", current),
    ):
        (tmp_path / name).write_text(json.dumps(data))
    cmd = [
        sys.executable, "-m", "ordivon_capital.portfolio.paper_close_performance",
        "--snapshot", str(tmp_path / "market.json"),
        "--binding", str(tmp_path / "binding.json"),
        "--current-receipt", str(tmp_path / "current.json"),
        "--previous-receipt", str(tmp_path / "previous.json"),
    ]
    p = subprocess.run(
        cmd, env=os.environ | {"PYTHONPATH": str(ROOT / "src")},
        cwd=ROOT, capture_output=True, text=True, check=False,
    )
    assert p.returncode == 0, p.stderr
    report = json.loads(p.stdout)
    assert report["fundingNeutralEconomicGainMinor"] == 1_900
    assert report["accountingPersistenceReverified"] is False
    assert report["capitalAuthority"] == "SIMULATION_ONLY"
    assert report["returnConvention"].endswith("NOT_GIPS_TWR_OR_IRR")

    (tmp_path / "current.json").write_text(
        json.dumps(current).replace('"account_key":', '"account_key":"bogus",')
    )
    rejected = subprocess.run(
        cmd, env=os.environ | {"PYTHONPATH": str(ROOT / "src")},
        cwd=ROOT, capture_output=True, text=True, check=False,
    )
    assert rejected.returncode == 2
    assert json.loads(rejected.stderr)["standing"] == "REJECTED"


def test_persistent_mode_never_invents_readback_without_paper_database(tmp_path):
    raw, binding, _, _, _, _, _ = _case()
    (tmp_path / "snapshot").write_bytes(raw)
    (tmp_path / "binding").write_text(json.dumps(binding))
    env = os.environ | {"PYTHONPATH": str(ROOT / "src"),
                        "ORDIVON_CAPITAL_PAPER_PG_DSN": ""}
    p = subprocess.run(
        [
            sys.executable, "-m", "ordivon_capital.portfolio.paper_close_performance",
            "--snapshot", str(tmp_path / "snapshot"),
            "--binding", str(tmp_path / "binding"),
            "--account", "daily-performance-test",
            "--session", "2026-01-09", "--previous-session", "2026-01-08",
        ],
        env=env, cwd=ROOT, capture_output=True, text=True, check=False,
    )
    assert p.returncode == 2
    assert json.loads(p.stderr)["standing"] == "REJECTED"


def test_postgresql_committed_paper_close_readback_to_portfolio(tmp_path):
    dsn = os.environ.get("ORDIVON_CAPITAL_PAPER_PG_TEST_DSN")
    if not dsn:
        pytest.skip("disposable paper PostgreSQL DSN not configured")
    from ordivon_capital.accounting.postgres_paper_close import (
        PostgresPaperClose,
        read_committed_paper_close,
    )
    raw, binding, snapshot, _, _, first, second = _case()
    account = "perf-" + uuid4().hex
    store = PostgresPaperClose(dsn)
    old = store.close_session(account, first)
    newer = store.close_session(
        account, PaperSession(
            second.session, second.previous_session,
            second.contribution_minor, second.reserve_contribution_minor,
            {}, second.buys,
        ), mark_snapshot=snapshot,
    )
    assert newer == store.close_session(
        account, PaperSession(second.session, second.previous_session,
                              second.contribution_minor,
                              second.reserve_contribution_minor, {}, second.buys),
        mark_snapshot=snapshot,
    )
    assert old == read_committed_paper_close(dsn, account, first.session)
    assert newer == read_committed_paper_close(dsn, account, second.session)
    summary = summarize_paper_period(
        current_receipt=newer, previous_receipt=old, snapshot=snapshot
    )
    assert summary["fundingNeutralEconomicGainMinor"] == 1_900
    (tmp_path / "snapshot").write_bytes(raw)
    (tmp_path / "binding").write_text(json.dumps(binding))
    p = subprocess.run(
        [
            sys.executable, "-m", "ordivon_capital.portfolio.paper_close_performance",
            "--snapshot", str(tmp_path / "snapshot"),
            "--binding", str(tmp_path / "binding"),
            "--account", account, "--session", "2026-01-09",
            "--previous-session", "2026-01-08",
        ],
        env=os.environ | {"PYTHONPATH": str(ROOT / "src"),
                          "ORDIVON_CAPITAL_PAPER_PG_DSN": dsn},
        cwd=ROOT, capture_output=True, text=True, check=False,
    )
    assert p.returncode == 0, p.stderr
    result = json.loads(p.stdout)
    assert result["accountingPersistenceReverified"] is True
    assert result["accountingReadbackMode"] == "POSTGRESQL_CURRENT_COMMITTED_REQUEST"
    assert result["fundingNeutralEconomicGainMinor"] == 1_900


@pytest.mark.parametrize("rounding", [ROUND_UP, ROUND_DOWN])
def test_period_return_is_independent_of_callers_decimal_rounding(rounding):
    _, _, snapshot, previous, current, _, _ = _case()
    with localcontext() as context:
        context.rounding = rounding
        report = summarize_paper_period(
            current_receipt=current, previous_receipt=previous, snapshot=snapshot
        )
    assert report["simplePeriodReturnDecimal"] == "0.001727272727272727"
