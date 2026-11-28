"""Application CLI: read current PG Paper head before read-only contribution plan."""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any

from ..markets.etf_eod_snapshot import admit_etf_eod_snapshot
from ..portfolio.paper_contribution_plan import (
    PaperContributionError,
    project_paper_account_contribution,
    render_paper_contribution_markdown,
)
from ..portfolio.strategic_contribution import AllocationPolicyError
from ..risk.paper_close_risk import PaperRiskEvidenceError


def _unique_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for key, value in pairs:
        if key in out:
            raise PaperContributionError("duplicate source JSON key")
        out[key] = value
    return out


def _read_object(path: Path) -> dict[str, Any]:
    obj = json.loads(
        path.read_text(encoding="utf-8"),
        object_pairs_hook=_unique_pairs,
        parse_constant=lambda _: (_ for _ in ()).throw(
            PaperContributionError("nonfinite source JSON constant")
        ),
    )
    if type(obj) is not dict:
        raise PaperContributionError("expected JSON object")
    return obj


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--account", required=True)
    parser.add_argument("--market-snapshot", required=True, type=Path)
    parser.add_argument("--market-binding", required=True, type=Path)
    parser.add_argument("--target-weights", required=True, type=Path)
    parser.add_argument("--invest-minor", required=True, type=int)
    parser.add_argument("--format", choices=("json", "markdown"), default="json")
    args = parser.parse_args()
    try:
        # Exact real Paper PG HEAD, not a caller-invented account state.
        from ordivon_capital.accounting.postgres_paper_close import (
            read_latest_committed_paper_close,
        )

        dsn = os.environ.get("ORDIVON_CAPITAL_PAPER_PG_DSN", "")
        receipt = read_latest_committed_paper_close(dsn, args.account)
        if receipt is None:
            raise PaperContributionError("no committed Paper account head; do not create a fake account")
        snapshot = admit_etf_eod_snapshot(
            args.market_snapshot.read_bytes(),
            **_read_object(args.market_binding),
        )
        report = project_paper_account_contribution(
            committed_receipt=receipt,
            snapshot=snapshot,
            target_weights_bps=_read_object(args.target_weights),
            invest_minor=args.invest_minor,
        )
        # Only this CLI has read the current native PostgreSQL account head.
        # The reusable pure projection always starts with persistence=false.
        report["accountingPersistenceReverified"] = True
    except (OSError, ValueError, TypeError, KeyError, PaperRiskEvidenceError,
            AllocationPolicyError) as exc:
        print(json.dumps({
            "standing": "REJECTED",
            "capitalAuthority": "SIMULATION_ONLY",
            "reason": str(exc) if isinstance(exc, ValueError) else "invalid source input",
        }, sort_keys=True), file=sys.stderr)
        return 2
    print(
        render_paper_contribution_markdown(report)
        if args.format == "markdown"
        else json.dumps(report, ensure_ascii=False, sort_keys=True, allow_nan=False)
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
