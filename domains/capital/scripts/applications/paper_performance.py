"""Composition of admitted Markets snapshots, Accounting readback, and Portfolio reporting.
No new portfolio optimizer, accounting ledger, or external financial effect.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import date
from pathlib import Path
from typing import Any

from ordivon_capital.markets.etf_eod_snapshot import admit_etf_eod_snapshot
from ordivon_capital.portfolio.paper_close_performance import (
    PaperPerformanceError,
    render_paper_daily_markdown,
    summarize_paper_period,
)


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
    parser.add_argument("--format", choices=("json", "markdown"), default="json")
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
    print(
        render_paper_daily_markdown(summary) if args.format == "markdown"
        else json.dumps(summary, ensure_ascii=False, sort_keys=True, allow_nan=False)
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
