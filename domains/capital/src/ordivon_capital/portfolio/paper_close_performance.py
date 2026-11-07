"""Read-only paper daily economic performance over native Accounting/Risk receipts.

Portfolio interprets committed Accounting NAV; it never reprices instruments,
mutates the journal, invents benchmarks, or grants any financial effects.
Risk verifies the current NAV against one admitted Markets EOD snapshot.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import date
from decimal import ROUND_HALF_EVEN, Decimal, localcontext
from pathlib import Path
from typing import Any

from ordivon_capital.markets.etf_eod_snapshot import (
    AdmittedEtfEodSnapshot,
    admit_etf_eod_snapshot,
)
from ordivon_capital.risk.paper_close_risk import review_paper_close_risk

_SHA = re.compile(r"[0-9a-f]{64}\Z")
_ACCOUNT = re.compile(r"[a-z0-9][a-z0-9_-]{0,63}\Z")
_MAX_MINOR = 2**63 - 1
_DECIMAL18 = Decimal("0.000000000000000001")


class PaperPerformanceError(ValueError):
    """Paper performance inputs are inconsistent or insufficient."""


def _minor(value: Any, label: str) -> int:
    if type(value) is not int or not 0 <= value <= _MAX_MINOR:
        raise PaperPerformanceError(f"{label} must be a nonnegative int64 USD-cent amount")
    return value


def _receipt(value: Any, label: str) -> tuple[dict[str, Any], str, date, int, int]:
    if type(value) is not dict or value.get("schema_version") != 1 or value.get("mode") != "PAPER":
        raise PaperPerformanceError(f"{label} is not an Accounting Paper receipt")
    account = value.get("account_key")
    digest = value.get("request_sha256")
    if type(account) is not str or _ACCOUNT.fullmatch(account) is None:
        raise PaperPerformanceError(f"{label} has invalid paper account identity")
    if type(digest) is not str or _SHA.fullmatch(digest) is None:
        raise PaperPerformanceError(f"{label} has invalid request SHA-256")
    valuation = value.get("valuation")
    if type(valuation) is not dict:
        raise PaperPerformanceError(f"{label} valuation missing")
    stamp = valuation.get("session")
    if type(stamp) is not str:
        raise PaperPerformanceError(f"{label} session must be a canonical ISO date")
    try:
        session = date.fromisoformat(stamp)
    except ValueError as exc:
        raise PaperPerformanceError(f"{label} has invalid session date") from exc
    if session.isoformat() != stamp:
        raise PaperPerformanceError(f"{label} session date is noncanonical")
    nav = _minor(valuation.get("nav_minor"), f"{label}.nav_minor")
    contribution = _minor(
        valuation.get("contribution_minor"), f"{label}.contribution_minor"
    )
    return value, account, session, nav, contribution


def summarize_paper_period(
    *,
    current_receipt: dict[str, Any],
    previous_receipt: dict[str, Any] | None,
    snapshot: AdmittedEtfEodSnapshot,
) -> dict[str, Any]:
    """Project funding-neutral gain without calculating a second NAV.

    The optional prior close must be the exact digest predecessor. It is not
    sufficient to compare two arbitrarily selected dates. The return assumes
    all current-period external capital was available at the period start;
    this is neither a GIPS-certified TWR nor an investor IRR.
    """
    current, account, session, closing_nav, funding = _receipt(
        current_receipt, "current"
    )
    predecessor = current.get("previous_request_sha256")
    previous_session: date | None = None
    previous_nav = 0
    previous_digest = None
    if previous_receipt is not None:
        prior, prior_account, previous_session, previous_nav, _ = _receipt(
            previous_receipt, "previous"
        )
        previous_digest = prior["request_sha256"]
        if prior_account != account:
            raise PaperPerformanceError("previous and current paper accounts differ")
        if previous_session >= session:
            raise PaperPerformanceError("previous close must precede the current session")
        if predecessor != previous_digest:
            raise PaperPerformanceError("Accounting receipt predecessor chain is broken")
    elif predecessor is not None:
        raise PaperPerformanceError("previous Accounting receipt is required")
    # The genesis absence is distinguishable from an omitted predecessor.
    risk = review_paper_close_risk(receipt=current, snapshot=snapshot)
    if risk["netAssetValueMinor"] != closing_nav:
        raise PaperPerformanceError("Risk and Accounting NAV disagree")
    capital_base = previous_nav + funding
    gain = closing_nav - capital_base
    period_return = None
    if previous_session is not None and capital_base:
        with localcontext() as context:
            context.prec = 55
            context.rounding = ROUND_HALF_EVEN
            period_return = format(
                (Decimal(gain) / Decimal(capital_base)).quantize(_DECIMAL18), "f"
            )

    return {
        "schemaVersion": 1,
        "kind": "ordivon.finance.portfolio.paper-close-economic-summary",
        "standing": "READ_ONLY_ACCOUNTING_RECEIPT_CONSUMER",
        "accountKey": account,
        "session": session.isoformat(),
        "previousSession": previous_session.isoformat() if previous_session else None,
        "requestSha256": current["request_sha256"],
        "previousRequestSha256": previous_digest,
        "marketSha256": snapshot.sha256,
        "marketStanding": current["market_evidence"]["standing"],
        "accountingPersistenceReverified": False,
        "sourceProviderAuthenticityIndependentlyVerified": False,
        "previousNavMinor": previous_nav if previous_session else None,
        "contributionMinor": funding,
        "startPeriodCapitalBaseMinor": capital_base if previous_session else None,
        "closingNavMinor": closing_nav,
        "fundingNeutralEconomicGainMinor": gain if previous_session else None,
        "simplePeriodReturnDecimal": period_return,
        "returnConvention": "START_PERIOD_CONTRIBUTION_ASSUMED_NOT_GIPS_TWR_OR_IRR",
        "calendarContinuity": "ASCENDING_CHAIN_ONLY_EXCHANGE_CALENDAR_UNATTESTED",
        "riskStanding": risk["standing"],
        "risk": risk["risk"],
        "capitalAuthority": "SIMULATION_ONLY",
        "realMoneyOrdersAuthorized": False,
    }


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for name, value in pairs:
        if name in result:
            raise PaperPerformanceError("duplicate JSON input key")
        result[name] = value
    return result


def _reject_constant(value: str) -> None:
    raise PaperPerformanceError(f"nonfinite JSON constant: {value}")


def _read_json(path: Path) -> dict[str, Any]:
    obj = json.loads(
        path.read_text(encoding="utf-8"),
        object_pairs_hook=_unique_object,
        parse_constant=_reject_constant,
    )
    if type(obj) is not dict:
        raise PaperPerformanceError("JSON input must be an object")
    return obj


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--current-receipt", type=Path)
    source.add_argument("--account")
    parser.add_argument("--previous-receipt", type=Path)
    parser.add_argument("--session")
    parser.add_argument("--previous-session")
    parser.add_argument("--snapshot", type=Path, required=True)
    parser.add_argument("--binding", type=Path, required=True)
    args = parser.parse_args()
    if bool(args.account) != bool(args.session):
        parser.error("--account and --session must be supplied together")
    if args.current_receipt and args.previous_session:
        parser.error("--previous-session requires --account")
    if args.account and args.previous_receipt:
        parser.error("--previous-receipt is only for offline file mode")
    try:
        snapshot = admit_etf_eod_snapshot(
            args.snapshot.read_bytes(), **_read_json(args.binding)
        )
        persistent = bool(args.account)
        if persistent:
            from ordivon_capital.accounting.postgres_paper_close import (
                read_committed_paper_close,
            )

            dsn = os.environ.get("ORDIVON_CAPITAL_PAPER_PG_DSN", "")
            current = read_committed_paper_close(
                dsn, args.account, date.fromisoformat(args.session)
            )
            previous = (
                read_committed_paper_close(
                    dsn, args.account, date.fromisoformat(args.previous_session)
                )
                if args.previous_session else None
            )
        else:
            current = _read_json(args.current_receipt)
            previous = (
                _read_json(args.previous_receipt) if args.previous_receipt else None
            )
        summary = summarize_paper_period(
            current_receipt=current, previous_receipt=previous, snapshot=snapshot
        )
        if persistent:
            summary["accountingPersistenceReverified"] = True
            summary["accountingReadbackMode"] = "POSTGRESQL_CURRENT_COMMITTED_REQUEST"
    except (OSError, ValueError, TypeError, KeyError) as exc:
        print(
            json.dumps({
                "standing": "REJECTED", "capitalAuthority": "SIMULATION_ONLY",
                "reason": str(exc) if isinstance(exc, ValueError) else "invalid source input",
            }, sort_keys=True),
            file=sys.stderr,
        )
        return 2
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
