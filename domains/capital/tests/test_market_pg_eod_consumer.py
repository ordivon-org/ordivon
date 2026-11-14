"""One actual disposable-PG Markets -> Accounting -> Risk -> Portfolio consumer.

Neither the synthetic operator-bound market marks nor a real database
establish publisher authenticity, equity corporate actions, historical PIT,
real fills, policy admission, or live financial permissions.
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
from datetime import date, datetime
from uuid import uuid4

import pytest


@pytest.mark.provider_qualification
def test_native_markets_pg_risk_portfolio_source_and_calendar_chain():
    dsn = os.environ.get("ORDIVON_CAPITAL_PAPER_PG_TEST_DSN")
    if not dsn or os.environ.get("ORDIVON_FINANCE_R3_DISPOSABLE_PG_MARKET_TEST") != "1":
        pytest.skip("explicit, physically isolated PostgreSQL source-consumer probe required")

    if sys.flags.optimize:
        raise RuntimeError("Finance native PG source verification rejects optimized assertions")
    import psycopg
    from psycopg.conninfo import conninfo_to_dict

    from ordivon_capital.accounting.paper_close import PaperBuy, PaperSession
    from ordivon_capital.accounting.postgres_paper_close import (
        PostgresPaperClose,
        read_committed_paper_close,
    )
    from ordivon_capital.markets.etf_eod_snapshot import admit_etf_eod_snapshot
    from ordivon_capital.portfolio.paper_close_performance import summarize_paper_period
    from ordivon_capital.risk.paper_close_risk import review_paper_close_risk

    identity = conninfo_to_dict(dsn)
    allowed = {
        "host": "127.0.0.1", "port": "55581",
        "dbname": "ordivon_paper", "user": "sandbox_finance_r3",
    }
    if {key: identity.get(key) for key in allowed} != allowed:
        raise RuntimeError("refusing non-disposable PostgreSQL connection")
    physical = os.environ["ORDIVON_FINANCE_R3_DISPOSABLE_PG_DATA"]
    with psycopg.connect(dsn) as db:
        actual = db.execute(
            "SELECT current_database(), current_user, "
            "current_setting('data_directory'), inet_server_port()"
        ).fetchone()
    if actual != ("ordivon_paper", "sandbox_finance_r3", physical, 55581):
        raise RuntimeError("refusing unexpected physical PostgreSQL data directory")

    def snapshot(day: str, close: str, capture: str, price: int):
        data = {
            "schemaVersion": 1,
            "kind": "ordivon.finance.markets.etf-eod-snapshot",
            "sourceId": "SYNTHETIC_PG_CHAIN_TEST_NOT_A_VENDOR_SOURCE",
            "currency": "USD",
            "priceBasis": "RAW_UNADJUSTED_CLOSE",
            "rights": {
                "status": "AUTHORIZED_PRIVATE_PAPER_USE",
                "evidenceRef": "TEST_ONLY_DECLARATION_NOT_REAL_RIGHTS",
            },
            "corporateActions": {
                "coverage": "COMPLETE",
                "evidenceRef": "TEST_ONLY_DECLARATION_NOT_AN_ISSUER_RECEIPT",
                "events": [],
            },
            "capturedAt": capture,
            "supersedesSha256": None,
            "marks": [{
                "sessionDate": day,
                "instrumentId": "SPY",
                "priceMinor": price,
                "availableAt": capture,
                "availabilityBasis": "FIRST_OBSERVED",
            }],
        }
        raw = json.dumps(data, sort_keys=True, separators=(",", ":")).encode()
        return admit_etf_eod_snapshot(
            raw,
            expected_sha256="sha256:" + hashlib.sha256(raw).hexdigest(),
            expected_source_id=data["sourceId"],
            expected_rights_ref=data["rights"]["evidenceRef"],
            expected_corporate_actions_ref=data["corporateActions"]["evidenceRef"],
            expected_instruments=("SPY",),
            expected_session_closes={day: close},
            decision_at=capture,
        )

    previous = date(2026, 1, 8)
    current = date(2026, 1, 9)
    prior_snapshot = snapshot(
        previous.isoformat(), "2026-01-08T21:00:00Z",
        "2026-01-08T21:10:00Z", 10_000,
    )
    now_snapshot = snapshot(
        current.isoformat(), "2026-01-09T21:00:00Z",
        "2026-01-09T21:10:00Z", 10_200,
    )

    # Importantly, the buy is an explicitly synthetic past-price order, NOT
    # an ex-ante trade decision certified by the later market-data snapshot.
    account = "r3pgsource_" + uuid4().hex
    store = PostgresPaperClose(dsn)
    opened = store.close_session(
        account,
        PaperSession(previous, None, 1_000_000, 900_000, {}, ()),
        mark_snapshot=prior_snapshot,
    )
    bought = store.close_session(
        account,
        PaperSession(
            current, previous, 0, 0, {},
            buys=(PaperBuy(
                "sim-buy-one-SPY", "SPY", 1, 10_000, 100,
                datetime.fromisoformat("2026-01-08T16:15:00-05:00"),
                datetime.fromisoformat("2026-01-09T09:30:00-05:00"),
                settlement_date=date(2026, 1, 12),
            ),),
        ),
        mark_snapshot=now_snapshot,
    )
    assert bought["market_evidence"]["standing"] == "OPERATOR_BOUND_MARKS"
    assert bought["market_evidence"]["sha256"] == now_snapshot.sha256
    assert bought["valuation"]["payable_minor"] == 10_100
    assert bought["valuation"]["positions"] == {"SPY": 1}
    assert bought["valuation"]["nav_minor"] == 1_000_100
    assert read_committed_paper_close(dsn, account, current) == bought

    risk = review_paper_close_risk(receipt=bought, snapshot=now_snapshot)
    assert risk["accountingPersistenceReverified"] is False
    assert risk["sourceProviderAuthenticityIndependentlyVerified"] is False
    assert risk["realMoneyOrdersAuthorized"] is False
    assert risk["netAssetValueMinor"] == 1_000_100
    report = summarize_paper_period(
        current_receipt=bought, previous_receipt=opened,
        snapshot=now_snapshot,
    )
    assert report["fundingNeutralEconomicGainMinor"] == 100
    assert report["closingNavMinor"] == risk["netAssetValueMinor"]
    assert report["historicalPointInTimeStanding"] == "UNKNOWN_NOT_INDEPENDENTLY_VERIFIED"
    assert report["realMoneyOrdersAuthorized"] is False
    print(
        "FINANCE_R3_DISPOSABLE_PG_MARKETS_RISK_PORTFOLIO_CONSUMER_PASS",
        "nav_minor=1000100", "gain_minor=100", "effect=SIMULATION_ONLY",
        flush=True,
    )
