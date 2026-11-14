"""Read-only Research audit: Qlib price labels crossing observed ETF ex-dates.

No new return/portfolio/accounting algorithm. ETF ex-dates are *caller-observed
issuer facts*, not authenticated provider bytes or timestamped historical PIT.
A count of observed dividend-exposed labels does not imply complete events,
a corrected total-return label, a usable forecast or real-money authority.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import re
from collections import defaultdict
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path

from ordivon_capital.markets.equity_session_calendar import (
    MarketSessionQualificationError,
    require_xnys_session_grid,
)

_SYMBOL = re.compile(r"[A-Z][A-Z0-9._-]{0,15}\Z")
_SHA = re.compile(r"[0-9a-f]{64}\Z")


class DistributionLabelAuditError(ValueError):
    """Input or source-calendar evidence is insufficient for a bounded audit."""


def _day(raw: object, label: str) -> date:
    if type(raw) is not str:
        raise DistributionLabelAuditError(f"{label} must be a canonical ISO date")
    try:
        result = date.fromisoformat(raw)
        if result.isoformat() != raw:
            raise ValueError("noncanonical date")
        return result
    except ValueError as exc:
        raise DistributionLabelAuditError(f"{label} must be a canonical ISO date") from exc


def audit_native_price_label_dividend_overlap(
    *,
    panel_bytes: bytes,
    observed_events_bytes: bytes,
    expected_panel_sha256: str,
    decision_start: str,
    decision_end: str,
    hold_sessions: int,
) -> dict:
    """Count affected *hypothetical* T+1 OPEN -> T+H+1 OPEN price labels.

    Ownership on the ex-date requires buying before ex-date, and selling at
    the ex-date open does not forfeit the already accrued entitlement.
    Thus an observed event at X overlaps iff entry_session < X <= exit_session.
    No returns, broker fills, tax assumptions or dividends are posted here.
    """
    if type(panel_bytes) is not bytes or not 0 < len(panel_bytes) <= 16_000_000:
        raise DistributionLabelAuditError("bounded source panel bytes required")
    if type(observed_events_bytes) is not bytes or not 0 < len(observed_events_bytes) <= 256_000:
        raise DistributionLabelAuditError("bounded issuer event observation bytes required")
    if (
        type(expected_panel_sha256) is not str
        or not _SHA.fullmatch(expected_panel_sha256)
        or hashlib.sha256(panel_bytes).hexdigest() != expected_panel_sha256
    ):
        raise DistributionLabelAuditError("frozen panel SHA-256 differs from supplied bytes")
    if type(hold_sessions) is not int or hold_sessions not in (5, 20):
        raise DistributionLabelAuditError("only registered H5/H20 next-open labels are audited")
    first = _day(decision_start, "decision_start")
    last = _day(decision_end, "decision_end")
    if first > last:
        raise DistributionLabelAuditError("decision range is inverted")

    try:
        reader = csv.DictReader(io.StringIO(panel_bytes.decode("utf-8"), newline=""))
        fields = reader.fieldnames or []
        if len(fields) != len(set(fields)) or not fields or fields[0] != "session_date":
            raise DistributionLabelAuditError("panel needs a unique leading session_date")
        source_rows = list(reader)
        if not source_rows or len(source_rows) > 10000 or any(None in row for row in source_rows):
            raise DistributionLabelAuditError("invalid or oversized panel rows")
        sessions = tuple(_day(row["session_date"], "panel session") for row in source_rows)
    except (UnicodeError, csv.Error, TypeError) as exc:
        raise DistributionLabelAuditError("panel is not a valid UTF-8 CSV") from exc
    if any(a >= b for a, b in zip(sessions, sessions[1:])):
        raise DistributionLabelAuditError("panel sessions must increase strictly")
    # Reuse the exact natural Markets XNYS source qualification. A vendor's
    # apparent date range cannot certify holiday accuracy or complete gaps.
    try:
        require_xnys_session_grid(
            [day.isoformat() for day in sessions],
            symbol="ISSUER_EVENTS",
            requested_start=sessions[0].isoformat(),
            requested_end=sessions[-1].isoformat(),
        )
    except MarketSessionQualificationError as exc:
        raise DistributionLabelAuditError(str(exc)) from exc

    try:
        observed = json.loads(observed_events_bytes)
    except (ValueError, UnicodeError, TypeError) as exc:
        raise DistributionLabelAuditError("issuer observations must be JSON") from exc
    if type(observed) is not dict or set(observed) != {
        "kind", "observedAt", "coverage", "events"
    } or observed["kind"] != "ordivon.finance.issuer-distribution-observations-r1":
        raise DistributionLabelAuditError("invalid issuer observations schema")
    if observed["coverage"] != "OBSERVED_ONLY_NOT_COMPLETE":
        raise DistributionLabelAuditError("issuer event observations cannot self-certify completeness")
    try:
        instant = datetime.fromisoformat(observed["observedAt"])
        if instant.tzinfo is None or instant.utcoffset() is None:
            raise ValueError("naive observation")
    except (TypeError, ValueError) as exc:
        raise DistributionLabelAuditError("issuer observation instant must carry timezone") from exc

    records = observed["events"]
    if type(records) is not list or not 1 <= len(records) <= 1000:
        raise DistributionLabelAuditError("bounded observed issuer events are required")
    index = {session: i for i, session in enumerate(sessions)}
    by_symbol: dict[str, list[date]] = defaultdict(list)
    seen = set()
    for row in records:
        if type(row) is not dict or set(row) != {
            "symbol", "exDate", "payableDate", "cashUSDPerShare", "issuerUrl"
        }:
            raise DistributionLabelAuditError("unexpected issuer event fields")
        symbol = row["symbol"]
        if type(symbol) is not str or not _SYMBOL.fullmatch(symbol) or symbol not in fields:
            raise DistributionLabelAuditError("issuer event instrument missing from price panel")
        ex_date = _day(row["exDate"], "issuer exDate")
        payable = _day(row["payableDate"], "issuer payableDate")
        if payable < ex_date or ex_date not in index:
            raise DistributionLabelAuditError("issuer event not a source market session")
        if type(row["cashUSDPerShare"]) is not str:
            raise DistributionLabelAuditError("issuer cash amount must be a decimal string")
        try:
            amount = Decimal(row["cashUSDPerShare"])
        except (InvalidOperation, TypeError) as exc:
            raise DistributionLabelAuditError("issuer cash amount must be decimal") from exc
        if not amount.is_finite() or amount <= 0:
            raise DistributionLabelAuditError("issuer cash amount must be positive")
        if (
            type(row["issuerUrl"]) is not str
            or not row["issuerUrl"].startswith("https://")
            or len(row["issuerUrl"]) > 512
        ):
            raise DistributionLabelAuditError("issuer public reference URL required")
        key = (symbol, ex_date)
        if key in seen:
            raise DistributionLabelAuditError("duplicate issuer ex-date for instrument")
        seen.add(key)
        by_symbol[symbol].append(ex_date)
    for symbol in by_symbol:
        if any(not row[symbol] for row in source_rows):
            raise DistributionLabelAuditError(f"{symbol} has a missing source panel quote")

    eligible = [
        t for t, T in enumerate(sessions)
        if first <= T <= last and t + hold_sessions + 1 < len(sessions)
    ]
    if not eligible:
        raise DistributionLabelAuditError("no complete next-open label horizon in source")
    results = {}
    for symbol, events in sorted(by_symbol.items()):
        exposed = 0
        by_event = []
        for ex in sorted(events):
            hits = sum(
                sessions[t + 1] < ex <= sessions[t + hold_sessions + 1] for t in eligible
            )
            by_event.append({"exDate": ex.isoformat(), "affectedCandidateWindows": hits})
        for t in eligible:
            if any(sessions[t + 1] < ex <= sessions[t + hold_sessions + 1] for ex in events):
                exposed += 1
        results[symbol] = {
            "observedIssuerEvents": len(events),
            "candidateExposedWindows": exposed,
            "perObservedExDate": by_event,
            "candidateUnexposedToObservedEvents": len(eligible) - exposed,
            "unknownAdditionalEventsMayOverlap": True,
        }

    return {
        "kind": "ordivon.finance.research.issuer-exdate-label-exposure-r1",
        "sourceSha256": expected_panel_sha256,
        "issuerObservationsSha256": hashlib.sha256(observed_events_bytes).hexdigest(),
        "issuerObservedAtCallerDeclared": observed["observedAt"],
        "sourceFirstSession": sessions[0].isoformat(),
        "sourceLastSession": sessions[-1].isoformat(),
        "decisionFirst": first.isoformat(),
        "decisionLast": last.isoformat(),
        "holdingSessions": hold_sessions,
        "exitEvent": "T_PLUS_H_PLUS_1_OPEN",
        "candidateWindows": len(eligible),
        "firstEligibleDecision": sessions[eligible[0]].isoformat(),
        "lastEligibleDecision": sessions[eligible[-1]].isoformat(),
        "sourceDateStanding": "EXCHANGE_CALENDARS_XNYS_DATE_GRID_ONLY",
        "actualETFPrimaryVenueVerified": False,
        "symbols": results,
        "standing": "OBSERVED_ISSUER_EVENT_EXPOSURE_NOT_TOTAL_RETURN",
        "priceLabelBasis": "OPEN_TO_OPEN_PRICE_ONLY_ADJUSTMENT_UNKNOWN",
        "issuerEventCoverageVerified": False,
        "issuerHistoricalPointInTimeVerified": False,
        "marketPriceAdjustmentAndDividendsVerified": False,
        "historicalPITVerified": False,
        "dataRightsVerified": False,
        "realMoneyOrdersAuthorized": False,
        "accountingEffect": "NONE",
        "externalFinancialEffects": "NONE",
    }


def main() -> None:
    cli = argparse.ArgumentParser(description="Read-only ETF Qlib ex-dividend label exposure audit")
    cli.add_argument("--panel", type=Path, required=True)
    cli.add_argument("--observed-events", type=Path, required=True)
    cli.add_argument("--expected-panel-sha256", required=True)
    cli.add_argument("--decision-first", required=True)
    cli.add_argument("--decision-last", required=True)
    cli.add_argument("--holding-sessions", type=int, choices=(5, 20), required=True)
    args = cli.parse_args()
    result = audit_native_price_label_dividend_overlap(
        panel_bytes=args.panel.read_bytes(),
        observed_events_bytes=args.observed_events.read_bytes(),
        expected_panel_sha256=args.expected_panel_sha256,
        decision_start=args.decision_first,
        decision_end=args.decision_last,
        hold_sessions=args.holding_sessions,
    )
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
