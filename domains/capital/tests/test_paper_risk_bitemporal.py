"""A historical Paper session is NOT the Market data observation/as-of date.

Risk consumes Markets' existing admitted snapshot identity. The output must
carry the original two clocks instead of letting downstream consumers confuse
retrospective knowledge with contemporaneously available market data.
"""
from __future__ import annotations

import hashlib
import json
import unittest
from dataclasses import asdict
from datetime import date, datetime

from ordivon_capital.accounting.paper_close import (
    PaperBuy,
    PaperSession,
    value_session,
)
from ordivon_capital.markets.etf_eod_snapshot import admit_etf_eod_snapshot


class PaperRiskBitemporalProjectionTests(unittest.TestCase):
    def test_retrospective_snapshot_clocks_are_not_discarded(self):
        try:
            from ordivon_capital.risk.paper_close_risk import review_paper_close_risk
        except ModuleNotFoundError as exc:
            if exc.name not in {"numpy", "sklearn", "scipy", "pandas"}:
                raise
            self.skipTest(f"native Risk dependency not installed: {exc.name}")

        prev_day = date(2026, 10, 28)
        trade_day = date(2026, 10, 29)
        captured = "2026-11-11T16:14:51Z"
        record = {
            "schemaVersion": 1,
            "kind": "ordivon.finance.markets.etf-eod-snapshot",
            "sourceId": "synthetic:retrospective-temporal-probe",
            "currency": "USD",
            "priceBasis": "RAW_UNADJUSTED_CLOSE",
            "rights": {
                "status": "AUTHORIZED_PRIVATE_PAPER_USE",
                "evidenceRef": "fixture:test-only-rights-declaration",
            },
            "corporateActions": {
                "coverage": "COMPLETE",
                "evidenceRef": "fixture:test-only-actions-declaration",
                "events": [],
            },
            "capturedAt": captured,
            "supersedesSha256": None,
            "marks": [{
                "sessionDate": trade_day.isoformat(),
                "instrumentId": "SPY",
                "priceMinor": 80_000,
                "availableAt": captured,
                "availabilityBasis": "FIRST_OBSERVED",
            }],
        }
        raw = json.dumps(record, sort_keys=True).encode()
        snapshot = admit_etf_eod_snapshot(
            raw,
            expected_sha256="sha256:" + hashlib.sha256(raw).hexdigest(),
            expected_source_id=record["sourceId"],
            expected_rights_ref=record["rights"]["evidenceRef"],
            expected_corporate_actions_ref=record["corporateActions"]["evidenceRef"],
            expected_instruments=["SPY"],
            expected_session_closes={
                trade_day.isoformat(): "2026-10-29T20:00:00Z",
            },
            decision_at=captured,
        )
        initial = value_session(None, PaperSession(
            prev_day, None, 1_000_000, 900_000, {}, (),
        ))
        paper = value_session(initial, PaperSession(
            trade_day, prev_day, 0, 0, snapshot.prices_for(trade_day.isoformat()),
            (PaperBuy(
                "synthetic-fill", "SPY", 1, 76_879, 2,
                datetime.fromisoformat("2026-10-28T16:01:00-04:00"),
                datetime.fromisoformat("2026-10-29T09:30:00-04:00"),
                settlement_date=date(2026, 10, 30),
            ),),
        ))
        receipt = {
            "schema_version": 1,
            "mode": "PAPER",
            "account_key": "bitemporal-test",
            "request_sha256": "a" * 64,
            "valuation": asdict(paper) | {"session": trade_day.isoformat()},
            "market_evidence": {
                "standing": "OPERATOR_BOUND_MARKS",
                "sha256": snapshot.sha256,
                "source_id": snapshot.source_id,
                "rights_ref": snapshot.rights_ref,
                "corporate_actions_ref": snapshot.corporate_actions_ref,
                "captured_at": snapshot.captured_at.isoformat(),
                "valuation_as_of": snapshot.decision_at.isoformat(),
                "session_closes": {
                    item.session_date: item.session_close_at.isoformat()
                    for item in snapshot.marks
                },
                "instrument_ids": ["SPY"],
                "supersedes_sha256": snapshot.supersedes_sha256,
            },
        }
        reviewed = review_paper_close_risk(receipt=receipt, snapshot=snapshot)
        self.assertEqual(reviewed["session"], trade_day.isoformat())
        self.assertEqual(reviewed["marketCapturedAt"], snapshot.captured_at.isoformat())
        self.assertEqual(reviewed["marketValuationAsOf"], snapshot.decision_at.isoformat())
        self.assertNotEqual(reviewed["session"], reviewed["marketValuationAsOf"][:10])
        self.assertEqual(reviewed["capitalAuthority"], "SIMULATION_ONLY")
        self.assertFalse(reviewed["sourceProviderAuthenticityIndependentlyVerified"])
        self.assertFalse(reviewed["realMoneyOrdersAuthorized"])


if __name__ == "__main__":
    unittest.main()