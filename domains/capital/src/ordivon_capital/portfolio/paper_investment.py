"""Offline, virtual-capital daily mark-to-market from fixed GitHub source bytes.

This is intentionally NOT a second OMS or backtest engine. The already qualified
cash-flow-matched passive benchmark owns comparison semantics. Virtual account
marks are retrospective close-price projections, not real brokerage fills.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import tempfile
from datetime import UTC, date, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

from ordivon_capital.markets.historical_close_snapshot import (
    HistoricalCloseError,
    admit_adjusted_close_csv,
)
from ordivon_capital.portfolio.passive_benchmark import (
    replay_passive_benchmark,
)

_ROOT_FIELDS = frozenset({"schemaVersion", "kind", "source", "policy"})
_SOURCE_FIELDS = frozenset({
    "repository", "commit", "commitAt", "path", "sha256", "gitBlobSha", "originStanding",
})
_POLICY_FIELDS = frozenset({
    "startDate", "endDate", "startingCapital", "currency", "weightsBps",
    "benchmarkSymbol", "strategyAnnualExpenseFraction",
    "benchmarkAnnualExpenseFraction", "periodsPerYear", "trialsDeclared",
})
_REPO_COMMIT = re.compile(r"[0-9a-f]{40}\Z")
_ASSET = re.compile(r"[A-Z][A-Z0-9._-]{0,31}\Z")


class PaperInvestmentError(ValueError):
    """A virtual investment study cannot be replayed under this contract."""


def _object(value: Any, expected: frozenset[str], label: str) -> dict[str, Any]:
    if type(value) is not dict or set(value) != expected:
        raise PaperInvestmentError(f"{label}: invalid required fields")
    return value


def _decimal(value: Any, label: str) -> Decimal:
    if type(value) is not str:
        raise PaperInvestmentError(f"{label} must be a decimal string")
    try:
        result = Decimal(value)
    except InvalidOperation as exc:
        raise PaperInvestmentError(f"{label}: invalid decimal") from exc
    if not result.is_finite():
        raise PaperInvestmentError(f"{label}: nonfinite decimal")
    return result


def _date(value: Any, label: str) -> date:
    if type(value) is not str:
        raise PaperInvestmentError(f"{label}: expected ISO date")
    try:
        result = date.fromisoformat(value)
    except ValueError as exc:
        raise PaperInvestmentError(f"{label}: malformed ISO date") from exc
    if result.isoformat() != value:
        raise PaperInvestmentError(f"{label}: noncanonical ISO date")
    return result


def _valid_commit_time(value: Any) -> datetime:
    if type(value) is not str:
        raise PaperInvestmentError("source.commitAt must be ISO timestamp")
    try:
        result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise PaperInvestmentError("source.commitAt malformed timestamp") from exc
    if result.tzinfo is None or result.utcoffset() is None:
        raise PaperInvestmentError("source.commitAt needs timezone")
    return result.astimezone(UTC)


def _git_blob_sha1(raw: bytes) -> str:
    envelope = b"blob " + str(len(raw)).encode("ascii") + b"\0" + raw
    return hashlib.sha1(envelope).hexdigest()


def _drawdown(peak: Decimal, current: Decimal) -> Decimal:
    if peak <= 0:
        return Decimal(0)
    return (peak - current) / peak


def replay_paper_investment(
    *, request: dict[str, Any], source_bytes: bytes
) -> dict[str, Any]:
    """Compare an explicit unoptimized virtual mix against an index and cash.

    No provider orders, no account-side effects. Inputs must be committed source
    bytes, not an inferred market history, and policy must be explicit.
    """
    root = _object(request, _ROOT_FIELDS, "request")
    if type(root["schemaVersion"]) is not int or root["schemaVersion"] != 1:
        raise PaperInvestmentError("unsupported schemaVersion")
    if root["kind"] != "ordivon.finance.paper.replay-request":
        raise PaperInvestmentError("unsupported paper replay kind")
    src = _object(root["source"], _SOURCE_FIELDS, "source")
    policy = _object(root["policy"], _POLICY_FIELDS, "policy")
    if any(type(src[key]) is not str or not src[key].strip()
           for key in ("repository", "path", "commit", "gitBlobSha", "sha256")):
        raise PaperInvestmentError("source identity must be nonblank strings")
    if not _REPO_COMMIT.fullmatch(src["commit"]):
        raise PaperInvestmentError("source commit identity must be a full Git SHA-1")
    if not _REPO_COMMIT.fullmatch(src["gitBlobSha"]):
        raise PaperInvestmentError("source Git blob identity must be a full SHA-1")
    if src["originStanding"] != "UNVERIFIED_UPSTREAM_MARKET_PROVENANCE":
        raise PaperInvestmentError("unsupported upstream market provenance claim")
    committed_at = _valid_commit_time(src["commitAt"])
    if _git_blob_sha1(source_bytes) != src["gitBlobSha"]:
        raise PaperInvestmentError("source Git blob digest mismatch")

    starting = _decimal(policy["startingCapital"], "startingCapital")
    if starting <= 0:
        raise PaperInvestmentError("startingCapital must be positive")
    if policy["currency"] != "USD":
        raise PaperInvestmentError("bounded virtual study currently expects USD")
    begin = _date(policy["startDate"], "startDate")
    end = _date(policy["endDate"], "endDate")
    weights = policy["weightsBps"]
    if type(weights) is not dict or not 1 <= len(weights) <= 16:
        raise PaperInvestmentError("bounded target weights required")
    if any(
        type(symbol) is not str
        or not _ASSET.fullmatch(symbol)
        or type(weight) is not int
        or not 0 <= weight <= 10000
        for symbol, weight in weights.items()
    ):
        raise PaperInvestmentError("weights must be asset keys and integer basis points")
    if sum(weights.values()) != 10000:
        raise PaperInvestmentError("weights must total 10000 basis points")
    benchmark_symbol = policy["benchmarkSymbol"]
    if type(benchmark_symbol) is not str or not _ASSET.fullmatch(benchmark_symbol):
        raise PaperInvestmentError("invalid benchmark instrument")
    period_count = policy["periodsPerYear"]
    if type(period_count) is not int or not 1 <= period_count <= 366:
        raise PaperInvestmentError("periodsPerYear must be positive bounded integer")
    trial_count = policy["trialsDeclared"]
    if type(trial_count) is not int or trial_count < 1:
        raise PaperInvestmentError("trialsDeclared must be positive integer")
    annual_strategy_cost = _decimal(
        policy["strategyAnnualExpenseFraction"], "strategyAnnualExpenseFraction"
    )
    annual_benchmark_cost = _decimal(
        policy["benchmarkAnnualExpenseFraction"], "benchmarkAnnualExpenseFraction"
    )
    if not all(Decimal(0) <= cost <= Decimal(1)
               for cost in (annual_strategy_cost, annual_benchmark_cost)):
        raise PaperInvestmentError("annual fractional expenses must be in [0,1]")
    cost_strategy = annual_strategy_cost / Decimal(period_count)
    cost_benchmark = annual_benchmark_cost / Decimal(period_count)

    try:
        source = admit_adjusted_close_csv(
            raw=source_bytes,
            expected_sha256=src["sha256"],
            instruments=frozenset(weights) | {benchmark_symbol},
            start_date=begin,
            end_date=end,
        )
    except HistoricalCloseError as exc:
        raise PaperInvestmentError(str(exc)) from exc

    previous = source.observations[0]
    strategy = benchmark = starting
    strategy_peak = benchmark_peak = starting
    strategy_max_dd = benchmark_max_dd = Decimal(0)
    daily_marks = [{
        "sessionDate": previous.session.isoformat(),
        "strategyNAV": str(strategy),
        "benchmarkNAV": str(benchmark),
        "cashOnlyNAV": str(starting),
        "strategyGrossReturn": None,
        "benchmarkGrossReturn": None,
        "standing": "VIRTUAL_INITIAL_CLOSE_MARK_NO_BROKER_FILL",
    }]
    benchmark_periods: list[dict[str, str]] = []
    for current in source.observations[1:]:
        returns = {
            symbol: current.prices[symbol] / previous.prices[symbol] - 1
            for symbol in (frozenset(weights) | {benchmark_symbol})
        }
        mix_gross = sum(
            (Decimal(weights[symbol]) / Decimal(10000)) * returns[symbol]
            for symbol in sorted(weights)
        )
        benchmark_gross = returns[benchmark_symbol]
        strategy = strategy * (1 - cost_strategy) * (1 + mix_gross)
        benchmark = benchmark * (1 - cost_benchmark) * (1 + benchmark_gross)
        strategy_peak = max(strategy_peak, strategy)
        benchmark_peak = max(benchmark_peak, benchmark)
        strategy_max_dd = max(strategy_max_dd, _drawdown(strategy_peak, strategy))
        benchmark_max_dd = max(benchmark_max_dd, _drawdown(benchmark_peak, benchmark))
        daily_marks.append({
            "sessionDate": current.session.isoformat(),
            "strategyNAV": str(strategy),
            "benchmarkNAV": str(benchmark),
            "cashOnlyNAV": str(starting),
            "strategyGrossReturn": str(mix_gross),
            "benchmarkGrossReturn": str(benchmark_gross),
            "standing": "VIRTUAL_CLOSE_MARK_DAILY_CONSTANT_MIX",
        })
        benchmark_periods.append({
            "periodEndAt": current.session.isoformat() + "T23:59:59+00:00",
            "depositAtStart": "0",
            "strategyGrossReturn": str(mix_gross),
            "benchmarkGrossReturn": str(benchmark_gross),
            "strategyExpenseFractionAtStart": str(cost_strategy),
            "benchmarkExpenseFractionAtStart": str(cost_benchmark),
            "strategyFixedFeeAtStart": "0",
            "benchmarkFixedFeeAtStart": "0",
        })
        previous = current

    # Reuse the existing passive benchmark as the independent composition
    # contract. Differences indicate a regression in this thin daily adapter.
    passive = replay_passive_benchmark(
        opening_balance=str(starting), currency="USD", periods=benchmark_periods
    )
    if (
        Decimal(passive["strategyTerminalWealth"]) != strategy
        or Decimal(passive["benchmarkTerminalWealth"]) != benchmark
    ):
        raise PaperInvestmentError("paper daily marks contradict passive benchmark")
    fingerprint = hashlib.sha256(
        (src["sha256"] + ":" + json.dumps(
            policy, ensure_ascii=False, sort_keys=True, separators=(",", ":")
        )).encode("utf-8")
    ).hexdigest()
    return {
        "schemaVersion": 1,
        "kind": "ordivon.finance.paper.daily-settlement-replay",
        "standing": "RETROSPECTIVE_PAPER_REPLAY_NO_FORWARD_EDGE_CLAIM",
        "capitalAuthority": "SIMULATION_ONLY",
        "realMoneyOrders": 0,
        "virtualFillConvention": "ADJUSTED_CLOSE_DAILY_CONSTANT_MIX_NO_REAL_ORDERS",
        "sourceSha256Verified": True,
        "gitBlobBytesVerified": True,
        "sourceCommitClaimVerifiedExternally": False,
        "providerPriceAuthenticityVerified": False,
        "prospectiveHoldoutVerified": False,
        "historicalDataPublishedAfterReplayStart": committed_at.date() > begin,
        "source": dict(src),
        "sourceLastRow": source.last_source_row,
        "trialCorrectionApplied": False,
        "trialsDeclared": trial_count,
        "policy": dict(policy),
        "replayId": "sha256:" + fingerprint,
        "firstSession": begin.isoformat(),
        "lastPricedSession": end.isoformat(),
        "replayedReturnPeriods": len(benchmark_periods),
        "skippedNoQuoteDates": list(source.no_quote_dates),
        "finalStrategyNAV": str(strategy),
        "finalBenchmarkNAV": str(benchmark),
        "finalCashNAV": str(starting),
        "strategyMaxDrawdown": str(strategy_max_dd),
        "benchmarkMaxDrawdown": str(benchmark_max_dd),
        "relativeTerminalWealth": str(strategy - benchmark),
        "dailySettlements": daily_marks,
    }


def _strict_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for name, value in pairs:
        if name in result:
            raise PaperInvestmentError("duplicate input JSON key")
        result[name] = value
    return result


def _reject_constant(value: str) -> None:
    raise PaperInvestmentError("nonfinite JSON constant")


def _write_receipt(path: Path, result: dict[str, Any]) -> None:
    payload = (json.dumps(result, sort_keys=True, ensure_ascii=False) + "\n").encode()
    path.parent.mkdir(parents=True, exist_ok=True)

    def assert_existing_receipt_is_identical() -> None:
        if path.is_symlink():
            raise PaperInvestmentError("receipt destination must not be symlink")
        if path.read_bytes() != payload:
            raise PaperInvestmentError("receipt collision: existing different replay")

    if path.is_symlink() or path.exists():
        assert_existing_receipt_is_identical()
        return

    temp_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as temporary:
            temp_path = Path(temporary.name)
            os.fchmod(temporary.fileno(), 0o600)
            temporary.write(payload)
            temporary.flush()
            os.fsync(temporary.fileno())

        # A hard link atomically publishes the fully flushed receipt, but
        # refuses to replace an already published name. os.replace would
        # overwrite a competing writer after the preceding existence check.
        try:
            os.link(temp_path, path)
        except FileExistsError:
            # Same replay is idempotent; a different replay cannot overwrite
            # an existing receipt, even when publication races.
            assert_existing_receipt_is_identical()
    finally:
        if temp_path is not None:
            temp_path.unlink(missing_ok=True)


def main() -> int:
    parser = argparse.ArgumentParser(description="Read-only-source virtual capital replay")
    parser.add_argument("--request", type=Path, required=True)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        req = json.loads(
            args.request.read_text(encoding="utf-8"),
            object_pairs_hook=_strict_pairs,
            parse_constant=_reject_constant,
        )
        result = replay_paper_investment(
            request=req, source_bytes=args.source.read_bytes()
        )
        if args.output:
            _write_receipt(args.output, result)
            summary = {
                key: val for key, val in result.items()
                if key not in ("dailySettlements",)
            }
            summary["receiptWritten"] = True
            summary["receiptPath"] = str(args.output)
            result = summary
        print(json.dumps(result, ensure_ascii=False, sort_keys=True))
        return 0
    except (PaperInvestmentError, OSError, ValueError, TypeError) as exc:
        print(json.dumps({
            "standing": "REJECTED",
            "capitalAuthority": "SIMULATION_ONLY",
            "reason": str(exc) if isinstance(exc, PaperInvestmentError) else "unreadable input",
        }, sort_keys=True))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
