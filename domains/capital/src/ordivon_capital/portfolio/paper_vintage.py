"""Thin read-only comparison of two already-qualified virtual investment replays.

A source revision can change past adjusted closes and hypothetical NAV. This
consumer makes the *difference* visible without treating either vintage as
true point-in-time market history or creating another investment engine.
"""

from __future__ import annotations

import argparse
import json
from decimal import Decimal
from pathlib import Path
from typing import Any

from .paper_investment import PaperInvestmentError, replay_paper_investment


class PaperVintageError(ValueError):
    """Unqualified comparison or invalid underlying historical replay."""


def _delta(candidate: str, reference: str) -> str:
    change = Decimal(candidate) - Decimal(reference)
    return "0" if change == 0 else format(change, "f")


def compare_paper_vintages(
    *,
    reference_request: dict[str, Any],
    reference_source_bytes: bytes,
    candidate_request: dict[str, Any],
    candidate_source_bytes: bytes,
) -> dict[str, Any]:
    """Compare the same fixed policy over two byte-bound source revisions.

    This is a *retrospective sensitivity* calculation, never a historical
    precommitment witness, statistical validation or real-capital approval.
    """
    if not isinstance(reference_request, dict) or not isinstance(candidate_request, dict):
        raise PaperVintageError("both requests must be objects")
    reference = reference_request.get("source")
    candidate = candidate_request.get("source")
    if not isinstance(reference, dict) or not isinstance(candidate, dict):
        raise PaperVintageError("source identities are required")
    if (
        reference_request.get("policy") != candidate_request.get("policy")
        or not isinstance(reference_request.get("policy"), dict)
    ):
        raise PaperVintageError("vintages must use exactly the same investment policy")
    if (
        reference.get("repository") != candidate.get("repository")
        or reference.get("path") != candidate.get("path")
    ):
        raise PaperVintageError("vintages must share repository and source path")

    try:
        reference_replay = replay_paper_investment(
            request=reference_request, source_bytes=reference_source_bytes
        )
        candidate_replay = replay_paper_investment(
            request=candidate_request, source_bytes=candidate_source_bytes
        )
    except PaperInvestmentError as exc:
        raise PaperVintageError(f"underlying paper replay rejected: {exc}") from exc

    reference_dates = [row["sessionDate"] for row in reference_replay["dailySettlements"]]
    candidate_dates = [row["sessionDate"] for row in candidate_replay["dailySettlements"]]
    base = {
        "schemaVersion": 1,
        "kind": "ordivon.finance.paper.historical-vintage-impact",
        "capitalAuthority": "SIMULATION_ONLY",
        "realMoneyOrders": 0,
        "sourceBytesChanged": reference["sha256"] != candidate["sha256"],
        "referenceReplayId": reference_replay["replayId"],
        "candidateReplayId": candidate_replay["replayId"],
        "referenceSourceSha256": reference["sha256"],
        "candidateSourceSha256": candidate["sha256"],
        "sameDeclaredPolicy": True,
        "sameDeclaredRepositoryPath": True,
        "sourceGitCommitClaimsVerifiedExternally": False,
        "pointInTimeVintagesAttested": False,
        "providerPriceAuthenticityVerified": False,
        "prospectivePerformanceVerified": False,
    }
    if reference_dates != candidate_dates:
        return {
            **base,
            "standing": "INCOMPARABLE_SESSION_COVERAGE",
            "onlyReferenceSessions": sorted(set(reference_dates) - set(candidate_dates)),
            "onlyCandidateSessions": sorted(set(candidate_dates) - set(reference_dates)),
            "reason": "priced session coverage differs; terminal wealth is not compared",
        }

    changed = [
        candidate_row["sessionDate"]
        for reference_row, candidate_row in zip(
            reference_replay["dailySettlements"],
            candidate_replay["dailySettlements"],
            strict=True,
        )
        if Decimal(reference_row["strategyNAV"]) != Decimal(candidate_row["strategyNAV"])
    ]
    return {
        **base,
        "standing": "COMPARABLE_RETROSPECTIVE_ONLY",
        "pricedSessionCount": len(reference_dates),
        "changedStrategySettlementDates": changed,
        "changedStrategySettlementCount": len(changed),
        "strategyTerminalWealthDelta": _delta(
            candidate_replay["finalStrategyNAV"], reference_replay["finalStrategyNAV"]
        ),
        "benchmarkTerminalWealthDelta": _delta(
            candidate_replay["finalBenchmarkNAV"], reference_replay["finalBenchmarkNAV"]
        ),
        "interpretation": "RETROSPECTIVE_SOURCE_REVISION_SENSITIVITY_NOT_PREDICTIVE_EDGE",
    }


def _strict_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    output: dict[str, Any] = {}
    for key, value in pairs:
        if key in output:
            raise PaperVintageError("duplicate JSON key")
        output[key] = value
    return output


def _bad_constant(_: str) -> None:
    raise PaperVintageError("nonfinite JSON constant")


def main() -> int:
    parser = argparse.ArgumentParser(description="Read-only paper source-vintage comparison")
    for name in ("reference-request", "reference-source", "candidate-request", "candidate-source"):
        parser.add_argument("--" + name, required=True, type=Path)
    args = parser.parse_args()
    try:
        reference = json.loads(
            args.reference_request.read_text(encoding="utf-8"),
            object_pairs_hook=_strict_pairs,
            parse_constant=_bad_constant,
        )
        candidate = json.loads(
            args.candidate_request.read_text(encoding="utf-8"),
            object_pairs_hook=_strict_pairs,
            parse_constant=_bad_constant,
        )
        result = compare_paper_vintages(
            reference_request=reference,
            reference_source_bytes=args.reference_source.read_bytes(),
            candidate_request=candidate,
            candidate_source_bytes=args.candidate_source.read_bytes(),
        )
    except (PaperVintageError, ValueError, TypeError, OSError, UnicodeError) as exc:
        print(json.dumps({
            "standing": "REJECTED",
            "capitalAuthority": "SIMULATION_ONLY",
            "reason": str(exc) if isinstance(exc, (PaperVintageError, ValueError)) else "invalid input",
        }, sort_keys=True))
        return 2
    print(json.dumps(result, sort_keys=True, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
