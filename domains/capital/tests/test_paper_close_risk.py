"""Real cross-owner consumer: paper Accounting + Markets -> Risk and Governance."""

from __future__ import annotations

import copy
import hashlib
import json
import os
import subprocess
import sys
from dataclasses import asdict
from datetime import date, datetime
from pathlib import Path
from uuid import uuid4

import pytest

from ordivon_capital.accounting.paper_close import (
    PaperBuy,
    PaperSell,
    PaperSession,
    value_session,
)
from ordivon_capital.markets.etf_eod_snapshot import admit_etf_eod_snapshot
from ordivon_capital.risk.paper_close_risk import (
    PaperRiskEvidenceError,
    review_paper_close_risk,
)

ROOT = Path(__file__).resolve().parents[1]


def _evidence():
    captured = "2026-01-09T21:10:00Z"
    raw = json.dumps({
        "schemaVersion": 1,
        "kind": "ordivon.finance.markets.etf-eod-snapshot",
        "sourceId": "paper-risk-synthetic",
        "currency": "USD",
        "priceBasis": "RAW_UNADJUSTED_CLOSE",
        "rights": {"status": "AUTHORIZED_PRIVATE_PAPER_USE", "evidenceRef": "synthetic"},
        "corporateActions": {"coverage": "COMPLETE", "evidenceRef": "synthetic", "events": []},
        "capturedAt": captured,
        "supersedesSha256": None,
        "marks": [{
            "sessionDate": "2026-01-09",
            "instrumentId": "ETF",
            "priceMinor": 10200,
            "availableAt": captured,
            "availabilityBasis": "FIRST_OBSERVED",
        }],
    }, sort_keys=True).encode("utf-8")
    binding = {
        "expected_sha256": "sha256:" + hashlib.sha256(raw).hexdigest(),
        "expected_source_id": "paper-risk-synthetic",
        "expected_rights_ref": "synthetic",
        "expected_corporate_actions_ref": "synthetic",
        "expected_instruments": ["ETF"],
        "expected_session_closes": {"2026-01-09": "2026-01-09T21:00:00Z"},
        "decision_at": captured,
    }
    snapshot = admit_etf_eod_snapshot(raw, **binding)
    first = date(2026, 1, 8)
    second = date(2026, 1, 9)
    day0 = PaperSession(first, None, 1_000_000, 300_000, {}, ())
    day1 = PaperSession(
        second, first, 0, 0, {},
        (PaperBuy(
            "test-buy", "ETF", 10, 10000, 100,
            datetime.fromisoformat("2026-01-08T16:15:00-05:00"),
            datetime.fromisoformat("2026-01-09T09:30:00-05:00"),
        ),),
    )
    return raw, binding, snapshot, day0, day1


def _receipt(snapshot, day0, day1):
    previous = value_session(None, day0)
    filled = PaperSession(
        day1.session, day1.previous_session, day1.contribution_minor,
        day1.reserve_contribution_minor, snapshot.prices_for("2026-01-09"), day1.buys,
    )
    valuation = value_session(previous, filled)
    return {
        "schema_version": 1,
        "mode": "PAPER",
        "account_key": "paper-risk-test",
        "request_sha256": "a" * 64,
        "previous_request_sha256": "b" * 64,
        "valuation": asdict(valuation) | {"session": valuation.session.isoformat()},
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
            "instrument_ids": sorted({mark.instrument_id for mark in snapshot.marks}),
            "supersedes_sha256": snapshot.supersedes_sha256,
        },
    }


def test_same_paper_close_produces_existing_exposure_and_incomplete_budget() -> None:
    raw, binding, snapshot, day0, day1 = _evidence()
    receipt = _receipt(snapshot, day0, day1)
    result = review_paper_close_risk(receipt=receipt, snapshot=snapshot)
    assert result["standing"] == "RISK_BUDGET_INCOMPLETE"
    assert result["netAssetValueMinor"] == 1_001_900
    assert result["grossPositionValueMinor"] == 102_000
    assert result["unsettledPayablesMinor"] == 100_100
    assert result["unencumberedCashMinor"] == 599_900
    assert result["risk"]["nodes"]["exposureLedger"]["grossNotionalUsd"] == "1020.000000"
    assert result["risk"]["nodes"]["riskBudgetRegistration"]["standing"] == "UNSET"
    assert result["realMoneyOrdersAuthorized"] is False
    assert result["accountingPersistenceReverified"] is False
    assert result["sourceProviderAuthenticityIndependentlyVerified"] is False


@pytest.mark.parametrize("mutation,fragment", [
    (lambda d: d["valuation"].update({"nav_minor": 1_001_901}), "NAV contradicts"),
    (lambda d: d["valuation"]["pending"].update({"test-buy": 100_200}), "payable liability"),
    (lambda d: d["valuation"]["positions"].update({"ETF": 11}), "NAV contradicts"),
    (lambda d: d["market_evidence"].update({"sha256": "sha256:" + "0"*64}), "market evidence"),
    (lambda d: d["valuation"]["settlement_dates"].update(
        {"test-buy": "2026-01-09"}), "unsettled payable maturity"),
])
def test_no_risk_evidence_from_contradictory_closes(mutation, fragment):
    _, _, snapshot, day0, day1 = _evidence()
    receipt = copy.deepcopy(_receipt(snapshot, day0, day1))
    mutation(receipt)
    with pytest.raises(PaperRiskEvidenceError, match=fragment):
        review_paper_close_risk(receipt=receipt, snapshot=snapshot)


def test_full_risk_cli_consumes_native_market_binding_and_accounting_receipt(tmp_path):
    raw, binding, snapshot, day0, day1 = _evidence()
    receipt = _receipt(snapshot, day0, day1)
    paths = {
        "snapshot": tmp_path / "snapshot.json",
        "binding": tmp_path / "binding.json",
        "receipt": tmp_path / "receipt.json",
    }
    paths["snapshot"].write_bytes(raw)
    paths["binding"].write_text(json.dumps(binding))
    paths["receipt"].write_text(json.dumps(receipt))
    env = os.environ | {"PYTHONPATH": str(ROOT / "src")}
    call = subprocess.run(
        [sys.executable, "-m", "ordivon_capital.risk.paper_close_risk",
         "--receipt", str(paths["receipt"]),
         "--snapshot", str(paths["snapshot"]),
         "--binding", str(paths["binding"])],
        cwd=ROOT, env=env, capture_output=True, text=True, check=False,
    )
    assert call.returncode == 0, call.stderr
    result = json.loads(call.stdout)
    assert result["standing"] == "RISK_BUDGET_INCOMPLETE"
    assert result["capitalAuthority"] == "SIMULATION_ONLY"
    assert result["risk"]["nodes"]["riskLimitEvaluation"]["standing"] == "INCOMPLETE"


def test_real_postgres_paper_close_is_consumed_after_atomic_commit():
    dsn = os.getenv("ORDIVON_CAPITAL_PAPER_PG_TEST_DSN")
    if not dsn:
        pytest.skip("disposable paper PostgreSQL DSN required")
    from ordivon_capital.accounting.postgres_paper_close import PostgresPaperClose

    _, _, snapshot, day0, day1 = _evidence()
    store = PostgresPaperClose(dsn)
    account = "risk-" + uuid4().hex
    store.close_session(account, day0)
    receipt = store.close_session(account, day1, mark_snapshot=snapshot)
    repeated = PostgresPaperClose(dsn).close_session(
        account, day1, mark_snapshot=snapshot,
    )
    assert repeated == receipt
    out = review_paper_close_risk(receipt=receipt, snapshot=snapshot)
    assert out["netAssetValueMinor"] == receipt["valuation"]["nav_minor"]
    assert out["marketSha256"] == snapshot.sha256
    assert out["risk"]["nodes"]["exposureLedger"]["grossNotionalUsd"] == "1020.000000"
    assert out["standing"] == "RISK_BUDGET_INCOMPLETE"



def _sell_case():
    """Use the actual paper state transition and native Market admission."""
    base_raw, base_binding, buy_snapshot, day0, day1 = _evidence()
    first = value_session(None, day0)
    buy_day = PaperSession(
        day1.session, day1.previous_session, 0, 0,
        buy_snapshot.prices_for(day1.session.isoformat()), day1.buys,
    )
    purchase = value_session(first, buy_day)
    clearing = PaperSession(date(2026, 1, 12), day1.session, 0, 0, {"ETF": 10_200}, ())
    cleared = value_session(purchase, clearing)
    sale = PaperSell(
        "risk-sale", "ETF", 10, 10_300, 100,
        datetime.fromisoformat("2026-01-12T16:15:00-05:00"),
        datetime.fromisoformat("2026-01-13T09:30:00-05:00"),
        settlement_date=date(2026, 1, 15),
    )
    day = date(2026, 1, 13)
    close = "2026-01-13T21:00:00Z"
    captured = "2026-01-13T21:10:00Z"
    src = {
        "schemaVersion": 1,
        "kind": "ordivon.finance.markets.etf-eod-snapshot",
        "sourceId": "paper-risk-synthetic-sell",
        "currency": "USD",
        "priceBasis": "RAW_UNADJUSTED_CLOSE",
        "rights": {"status": "AUTHORIZED_PRIVATE_PAPER_USE", "evidenceRef": "synthetic"},
        "corporateActions": {"coverage": "COMPLETE", "evidenceRef": "synthetic", "events": []},
        "capturedAt": captured,
        "supersedesSha256": None,
        "marks": [{
            "sessionDate": day.isoformat(), "instrumentId": "ETF", "priceMinor": 10_300,
            "availableAt": captured, "availabilityBasis": "FIRST_OBSERVED",
        }],
    }
    raw = json.dumps(src, sort_keys=True).encode()
    binding = {
        "expected_sha256": "sha256:" + hashlib.sha256(raw).hexdigest(),
        "expected_source_id": src["sourceId"],
        "expected_rights_ref": "synthetic",
        "expected_corporate_actions_ref": "synthetic",
        "expected_instruments": ["ETF"],
        "expected_session_closes": {day.isoformat(): close},
        "decision_at": captured,
    }
    snapshot = admit_etf_eod_snapshot(raw, **binding)
    sale_day = PaperSession(day, clearing.session, 0, 0, {}, (), sells=(sale,))
    valuation = value_session(
        cleared,
        PaperSession(day, clearing.session, 0, 0, {"ETF": 10_300}, (), sells=(sale,)),
    )
    receipt = _receipt(buy_snapshot, day0, day1)
    receipt["valuation"] = asdict(valuation) | {"session": day.isoformat()}
    receipt["market_evidence"] = {
        "standing": "OPERATOR_BOUND_MARKS",
        "sha256": snapshot.sha256,
        "source_id": snapshot.source_id,
        "rights_ref": snapshot.rights_ref,
        "corporate_actions_ref": snapshot.corporate_actions_ref,
        "captured_at": snapshot.captured_at.isoformat(),
        "valuation_as_of": snapshot.decision_at.isoformat(),
        "session_closes": {
            mark.session_date: mark.session_close_at.isoformat() for mark in snapshot.marks
        },
        "instrument_ids": ["ETF"],
        "supersedes_sha256": None,
    }
    return raw, binding, snapshot, (day0, day1, clearing, sale_day), receipt


def test_paper_sell_receivables_count_in_nav_but_never_in_free_cash():
    _, _, snapshot, _, receipt = _sell_case()
    out = review_paper_close_risk(receipt=receipt, snapshot=snapshot)
    assert out["standing"] == "RISK_BUDGET_INCOMPLETE"
    assert out["netAssetValueMinor"] == 1_002_800
    assert out["unsettledSaleReceivablesMinor"] == 102_900
    assert out["unencumberedCashMinor"] == 599_900
    assert out["grossPositionValueMinor"] == 0
    assert out["risk"]["nodes"]["exposureLedger"]["grossNotionalUsd"] == "0.000000"
    assert out["capitalAuthority"] == "SIMULATION_ONLY"


@pytest.mark.parametrize("part,reason", [
    ("receivable_minor", "receivable liability"),
    ("sale_settlement_dates", "sale receivable"),
    ("nav_minor", "NAV contradicts"),
])
def test_paper_sell_bad_receivable_identity_fails_risk(part, reason):
    _, _, snapshot, _, receipt = _sell_case()
    receipt = copy.deepcopy(receipt)
    if part == "receivable_minor":
        receipt["valuation"]["receivable_minor"] = 0
    elif part == "sale_settlement_dates":
        receipt["valuation"]["sale_settlement_dates"] = {}
    else:
        receipt["valuation"]["nav_minor"] -= 100
    with pytest.raises(PaperRiskEvidenceError, match=reason):
        review_paper_close_risk(receipt=receipt, snapshot=snapshot)


def test_readonly_pg_receipt_and_risk_cli_after_simulated_sell(tmp_path: Path):
    dsn = os.getenv("ORDIVON_CAPITAL_PAPER_PG_TEST_DSN")
    if not dsn:
        pytest.skip("disposable paper PostgreSQL DSN required")
    from ordivon_capital.accounting.postgres_paper_close import (
        PostgresPaperClose,
        read_committed_paper_close,
    )

    raw, binding, snapshot, days, expected = _sell_case()
    day0, day1, day2, sale_day = days
    _, _, buy_snapshot, _, _ = _evidence()
    store = PostgresPaperClose(dsn)
    account = "risk-sale-" + uuid4().hex
    store.close_session(account, day0)
    store.close_session(account, day1, mark_snapshot=buy_snapshot)
    store.close_session(account, day2)
    committed = store.close_session(account, sale_day, mark_snapshot=snapshot)
    assert committed["valuation"] == expected["valuation"]
    readback = read_committed_paper_close(dsn, account, sale_day.session)
    assert committed == readback
    assert read_committed_paper_close(dsn, account, sale_day.session) == readback
    with pytest.raises(ValueError, match="no committed"):
        read_committed_paper_close(dsn, account, date(2026, 1, 14))
    paths = {name: tmp_path / (name + ".json") for name in ("snapshot", "binding")}
    paths["snapshot"].write_bytes(raw)
    paths["binding"].write_text(json.dumps(binding))
    cli = subprocess.run(
        [
            sys.executable, "-m", "ordivon_capital.risk.paper_close_risk",
            "--account", account, "--session", sale_day.session.isoformat(),
            "--snapshot", str(paths["snapshot"]), "--binding", str(paths["binding"]),
        ], cwd=ROOT, env=os.environ | {
            "PYTHONPATH": str(ROOT / "src"), "ORDIVON_CAPITAL_PAPER_PG_DSN": dsn,
        }, capture_output=True, text=True, check=False,
    )
    assert cli.returncode == 0, cli.stderr
    report = json.loads(cli.stdout)
    assert report["unsettledSaleReceivablesMinor"] == 102_900
    assert report["unencumberedCashMinor"] == 599_900
    assert report["accountingPersistenceReverified"] is True
    assert report["accountingReadbackMode"] == "POSTGRESQL_CURRENT_COMMITTED_REQUEST"


def test_accounting_readback_rejects_a_tampered_committed_request():
    dsn = os.getenv("ORDIVON_CAPITAL_PAPER_PG_TEST_DSN")
    if not dsn:
        pytest.skip("disposable paper PostgreSQL DSN required")
    import psycopg

    from ordivon_capital.accounting.postgres_paper_close import (
        PostgresPaperClose,
        read_committed_paper_close,
    )

    _, _, snapshot, day0, day1 = _evidence()
    account = "risk-altered-" + uuid4().hex
    store = PostgresPaperClose(dsn)
    store.close_session(account, day0)
    store.close_session(account, day1, mark_snapshot=snapshot)
    assert read_committed_paper_close(dsn, account, day1.session)["valuation"]["nav_minor"] == 1_001_900
    with psycopg.connect(dsn) as db:
        db.execute(
            "UPDATE ordivon_paper.daily_close SET request = jsonb_set("
            "request, '{contribution_minor}', '123'::jsonb) "
            "WHERE account_key = %s AND session = %s", (account, day1.session),
        )
    with pytest.raises(ValueError, match="stored request disagree"):
        read_committed_paper_close(dsn, account, day1.session)
