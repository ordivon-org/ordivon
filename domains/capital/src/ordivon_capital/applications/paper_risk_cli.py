"""Application CLI: read Accounting receipt and Markets snapshot; compute Risk review."""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import date
from pathlib import Path
from typing import Any

from ..markets.etf_eod_snapshot import SnapshotAdmissionError, admit_etf_eod_snapshot
from ..risk.paper_close_risk import PaperRiskEvidenceError, review_paper_close_risk
from ..risk.risk_values import PortfolioRiskError


def _pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    record: dict[str, Any] = {}
    for key, value in pairs:
        if key in record:
            raise PaperRiskEvidenceError("duplicate JSON input key")
        record[key] = value
    return record


def main() -> int:
    parser = argparse.ArgumentParser(description="Compose paper Accounting, Markets and Risk")
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--receipt", type=Path)
    source.add_argument("--account")
    parser.add_argument("--session")
    parser.add_argument("--snapshot", type=Path, required=True)
    parser.add_argument("--binding", type=Path, required=True)
    args = parser.parse_args()
    if bool(args.account) != bool(args.session):
        parser.error("--account and --session must be supplied together")
    try:
        def read(path: Path) -> Any:
            return json.loads(
                path.read_text(encoding="utf-8"), object_pairs_hook=_pairs,
                parse_constant=lambda _: (_ for _ in ()).throw(
                    PaperRiskEvidenceError("nonfinite JSON input constant")
                ),
            )

        snapshot = admit_etf_eod_snapshot(args.snapshot.read_bytes(), **read(args.binding))
        if args.receipt is not None:
            receipt = read(args.receipt)
        else:
            from ordivon_capital.accounting.postgres_paper_close import (
                read_committed_paper_close,
            )

            receipt = read_committed_paper_close(
                os.environ.get("ORDIVON_CAPITAL_PAPER_PG_DSN", ""),
                args.account,
                date.fromisoformat(args.session),
            )
        result = review_paper_close_risk(receipt=receipt, snapshot=snapshot)
        if args.account:
            result["accountingPersistenceReverified"] = True
            result["accountingReadbackMode"] = "POSTGRESQL_CURRENT_COMMITTED_REQUEST"
    except (OSError, ValueError, TypeError, PortfolioRiskError, SnapshotAdmissionError) as exc:
        print(json.dumps({"standing": "REJECTED", "capitalAuthority": "SIMULATION_ONLY",
                          "reason": str(exc) if isinstance(exc, ValueError)
                          else "invalid source input"}, sort_keys=True), file=sys.stderr)
        return 2
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
