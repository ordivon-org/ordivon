"""Risk projection from an admitted Markets mark and one paper Accounting close.

No broker facts or forecast can be inferred from this caller-supplied receipt.
Accounting owns positions/payables; Markets owns admitted USD-cent marks;
the existing Risk/Governance modules own all arithmetic and limit decisions.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import date
from decimal import Decimal
from pathlib import Path
from typing import Any

from ordivon_capital.markets.etf_eod_snapshot import (
    AdmittedEtfEodSnapshot,
    SnapshotAdmissionError,
    admit_etf_eod_snapshot,
)
from ordivon_capital.risk.portfolio_risk import (
    PortfolioRiskError,
    build_exposure_ledger,
    build_portfolio_risk_report,
)

_MINOR_CENTS = Decimal(100)
_SHA = re.compile(r"[0-9a-f]{64}\Z")


class PaperRiskEvidenceError(ValueError):
    """An Accounting receipt and admitted market snapshot disagree."""


def _minor(value: Any, label: str) -> int:
    if type(value) is not int or not 0 <= value <= 2**63 - 1:
        raise PaperRiskEvidenceError(f"{label} must be a nonnegative int64 USD minor amount")
    return value


def _dollars(value: int) -> str:
    return str(Decimal(value) / _MINOR_CENTS)


def _object(value: Any, label: str) -> dict[str, Any]:
    if type(value) is not dict:
        raise PaperRiskEvidenceError(f"{label} must be an object")
    return value


def _session(value: Any) -> str:
    if type(value) is not str:
        raise PaperRiskEvidenceError("paper close session must be ISO date")
    try:
        parsed = date.fromisoformat(value)
    except ValueError as exc:
        raise PaperRiskEvidenceError("invalid paper close session date") from exc
    if parsed.isoformat() != value:
        raise PaperRiskEvidenceError("noncanonical paper close session date")
    return value


def review_paper_close_risk(
    *, receipt: dict[str, Any], snapshot: AdmittedEtfEodSnapshot
) -> dict[str, Any]:
    """Read-only cross-owner consumer, not independent database provenance proof.

    The receipt is the result of the existing PostgresPaperClose close_session.
    Its PostgreSQL write, readback, hash and source transaction must already
    have been checked by the Accounting owner. This pure consumer can catch
    contradictory payloads but cannot verify their external origin.
    """
    body = _object(receipt, "paper receipt")
    if body.get("schema_version") != 1 or body.get("mode") != "PAPER":
        raise PaperRiskEvidenceError("requires the native paper Accounting receipt")
    key = body.get("account_key")
    digest = body.get("request_sha256")
    if type(key) is not str or re.fullmatch(r"[a-z0-9][a-z0-9_-]{0,63}", key) is None:
        raise PaperRiskEvidenceError("invalid paper account identity")
    if type(digest) is not str or _SHA.fullmatch(digest) is None:
        raise PaperRiskEvidenceError("invalid Account close request SHA-256 identity")

    value = _object(body.get("valuation"), "valuation")
    session = _session(value.get("session"))
    market = _object(body.get("market_evidence"), "market evidence")
    expected_market = {
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
    }
    if market != expected_market:
        raise PaperRiskEvidenceError("market evidence differs from admitted snapshot identity")
    try:
        marks = snapshot.prices_for(session)
    except KeyError as exc:
        raise PaperRiskEvidenceError("snapshot does not cover paper close session") from exc
    positions = _object(value.get("positions"), "positions")
    pending = _object(value.get("pending"), "pending")
    settlement_dates = _object(value.get("settlement_dates"), "settlement dates")
    if settlement_dates.keys() - pending.keys():
        raise PaperRiskEvidenceError("settlement date refers to missing open payable")
    for fill_id, clearance in settlement_dates.items():
        if type(fill_id) is not str or not fill_id or _session(clearance) <= session:
            raise PaperRiskEvidenceError("invalid unsettled payable maturity")

    cash = _minor(value.get("cash_minor"), "cash")
    protected = _minor(value.get("protected_minor"), "protected")
    payable = _minor(value.get("payable_minor"), "payable")
    nav = _minor(value.get("nav_minor"), "net asset value")
    total_pending = sum(_minor(amount, f"pending.{fill_id}") for fill_id, amount in pending.items())
    if payable != total_pending:
        raise PaperRiskEvidenceError("payable liability disagrees with open pending fills")
    if cash < payable or protected > cash - payable:
        raise PaperRiskEvidenceError("paper free cash violates payable or protected reserve")
    if not all(type(symbol) is str and type(shares) is int and 0 < shares <= 2**63-1
               and symbol in marks for symbol, shares in positions.items()):
        raise PaperRiskEvidenceError("paper held positions need positive shares and fresh marks")
    notional = {
        symbol: shares * marks[symbol]
        for symbol, shares in sorted(positions.items())
    }
    invested = sum(notional.values())
    if nav != cash - payable + invested:
        raise PaperRiskEvidenceError("paper NAV contradicts market values and unsettled payables")
    if not nav:
        raise PaperRiskEvidenceError("risk exposure requires positive paper equity")
    free_cash = cash - payable - protected

    # Reuse the existing decimal Risk and Governance owners, including the
    # owner-supplied UNSET budget.  No custom risk thresholds are inferred.
    exposure = build_exposure_ledger(
        equity_usd=_dollars(nav),
        available_equity_usd=_dollars(free_cash),
        positions=[
            {"instrumentId": symbol, "signedNotionalUsd": _dollars(market_minor)}
            for symbol, market_minor in notional.items()
        ],
    )
    risk = build_portfolio_risk_report(exposure_ledger=exposure)
    limit = risk["nodes"]["riskLimitEvaluation"]
    return {
        "schemaVersion": 1,
        "kind": "ordivon.finance.paper.close-risk-review",
        "standing": "RISK_BUDGET_" + limit["standing"],
        "mode": "PAPER",
        "session": session,
        "accountKey": key,
        "accountingRequestSha256": digest,
        "accountingPersistenceReverified": False,
        "marketSha256": snapshot.sha256,
        "sourceProviderAuthenticityIndependentlyVerified": False,
        "grossPositionValueMinor": invested,
        "netAssetValueMinor": nav,
        "unsettledPayablesMinor": payable,
        "unencumberedCashMinor": free_cash,
        "availableEquityInterpretation": "UNENCUMBERED_PAPER_CASH_NOT_BROKER_BUYING_POWER",
        "risk": risk,
        "capitalAuthority": "SIMULATION_ONLY",
        "realMoneyOrdersAuthorized": False,
    }


def _pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    record: dict[str, Any] = {}
    for key, value in pairs:
        if key in record:
            raise PaperRiskEvidenceError("duplicate JSON input key")
        record[key] = value
    return record


def main() -> int:
    parser = argparse.ArgumentParser(description="Compose paper Accounting, Markets and Risk")
    parser.add_argument("--receipt", type=Path, required=True)
    parser.add_argument("--snapshot", type=Path, required=True)
    parser.add_argument("--binding", type=Path, required=True)
    args = parser.parse_args()
    try:
        def read(path: Path) -> Any:
            return json.loads(
                path.read_text(encoding="utf-8"), object_pairs_hook=_pairs,
                parse_constant=lambda _: (_ for _ in ()).throw(
                    PaperRiskEvidenceError("nonfinite JSON input constant")
                ),
            )

        snapshot = admit_etf_eod_snapshot(args.snapshot.read_bytes(), **read(args.binding))
        result = review_paper_close_risk(receipt=read(args.receipt), snapshot=snapshot)
    except (OSError, ValueError, TypeError, PortfolioRiskError, SnapshotAdmissionError) as exc:
        print(json.dumps({"standing": "REJECTED", "capitalAuthority": "SIMULATION_ONLY",
                          "reason": str(exc) if isinstance(exc, ValueError)
                          else "invalid source input"}, sort_keys=True), file=sys.stderr)
        return 2
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
