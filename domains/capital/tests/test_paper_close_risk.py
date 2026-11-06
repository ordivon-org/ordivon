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
