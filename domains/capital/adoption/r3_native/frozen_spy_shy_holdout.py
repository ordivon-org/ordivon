"""Frozen SPY/SHY partial-forward Cboe observation; research-only, no broker.

Reuse official OpenBB V5, existing Research freeze and Portfolio passive replay.
Vendor rights, historical PIT, corporate actions and alpha remain UNKNOWN.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import os
from collections.abc import Callable
from datetime import UTC, date, datetime
from decimal import Decimal
from pathlib import Path

from ordivon_capital.portfolio.passive_benchmark import replay_passive_benchmark
from ordivon_capital.research.experiment_protocol import freeze_experiment_plan

SYMBOLS = ("SHY", "SPY")
HYPOTHESIS = "spy-shy-60-40-vs-spy-forward-r1"


def _policy(frozen_path: Path, policy_path: Path) -> tuple[dict, dict]:
    frozen = json.loads(frozen_path.read_text(encoding="utf-8"))
    request_bytes = policy_path.read_bytes()
    request = json.loads(request_bytes)
    if frozen != freeze_experiment_plan(frozen["plan"]):
        raise ValueError("frozen study does not match the existing Research validator")
    plan = frozen["plan"]
    if (plan["hypothesisId"] != HYPOTHESIS
        or plan["effectBoundary"] != "RESEARCH_ONLY"
        or plan["partitions"]["holdout"]["start"] != "2026-11-09"
        or plan["configDigest"] != "sha256:" + hashlib.sha256(request_bytes).hexdigest()):
        raise ValueError("changed precommitted study or policy")
    policy = request["policy"]
    if (policy["weightsBps"] != {"SPY": 6000, "SHY": 4000}
        or policy["benchmarkSymbol"] != "SPY"
        or policy["startingCapital"] != "100000"
        or policy["currency"] != "USD"
        or policy["strategyAnnualExpenseFraction"] != "0.002"
        or policy["benchmarkAnnualExpenseFraction"] != "0.001"
        or policy["periodsPerYear"] != 252):
        raise ValueError("not the original precommitted SPY/SHY policy")
    return frozen, policy


def _closes(frame: object, *, start: str, end: str, received: datetime) -> tuple[bytes, dict[str, Decimal]]:
    raw = frame.sort_index().to_csv(index_label="session_date").encode("utf-8")
    reader = csv.DictReader(io.StringIO(raw.decode("utf-8")))
    if not reader.fieldnames or not {"session_date", "open", "high", "low", "close", "volume"}.issubset(reader.fieldnames):
        raise ValueError("provider result lacks original OHLCV fields")
    values: dict[str, Decimal] = {}
    for row in reader:
        day = date.fromisoformat(row["session_date"][:10]).isoformat()
        if not start <= day <= end or day >= received.date().isoformat():
            raise ValueError("source contains a future or out-of-period trading session")
        if day in values:
            raise ValueError("duplicate provider trading session")
        close = Decimal(row["close"])
        if not close.is_finite() or close <= 0:
            raise ValueError("market prices must be finite and positive")
        values[day] = close
    if len(values) < 2:
        raise ValueError("need at least two matched postfreeze market sessions")
    return raw, values


def observe(
    frozen_path: Path, policy_path: Path, through: str, private_output: Path,
    fetch: Callable[[str, str, str], tuple[str, object, datetime, datetime]],
) -> dict:
    frozen, policy = _policy(frozen_path, policy_path)
    start = frozen["plan"]["partitions"]["holdout"]["start"]
    end = date.fromisoformat(through).isoformat()
    if not start < end <= frozen["plan"]["partitions"]["holdout"]["end"]:
        raise ValueError("observation cut outside the frozen future holdout")
    if private_output.exists():
        raise ValueError("private observation destination already exists")

    observed: dict[str, dict[str, Decimal]] = {}
    bytes_by_symbol: dict[str, bytes] = {}
    receipts: dict[str, dict] = {}
    for symbol in SYMBOLS:
        provider, frame, begin, finish = fetch(symbol, start, end)
        if any(t.tzinfo is None or t.utcoffset() is None for t in (begin, finish)):
            raise ValueError("provider clocks must be timezone-aware")
        begin, finish = begin.astimezone(UTC), finish.astimezone(UTC)
        if provider != "cboe" or begin > finish or finish <= datetime.fromisoformat(frozen["plan"]["frozenAt"]).astimezone(UTC):
            raise ValueError("provider or capture clock cannot be trusted")
        raw, prices = _closes(frame, start=start, end=end, received=finish)
        observed[symbol], bytes_by_symbol[symbol] = prices, raw
        receipts[symbol] = {
            "provider": provider, "requestedAt": begin.isoformat(),
            "receivedAt": finish.isoformat(), "firstSession": min(prices),
            "lastSession": max(prices), "rowCount": len(prices),
            "normalizedSha256": hashlib.sha256(raw).hexdigest(),
            "normalizedFile": f"openbb_cboe_{symbol}_normalized.csv",
            "rawProviderWireCaptured": False,
        }
    sessions = sorted(set(observed["SPY"]) & set(observed["SHY"]))
    if sessions != sorted(observed["SPY"]) or sessions != sorted(observed["SHY"]):
        raise ValueError("incomplete paired ETF sessions")
    weights = {s: Decimal(v) / Decimal(10000) for s, v in policy["weightsBps"].items()}
    strategy_fee = Decimal(policy["strategyAnnualExpenseFraction"]) / Decimal(252)
    benchmark_fee = Decimal(policy["benchmarkAnnualExpenseFraction"]) / Decimal(252)
    periods = []
    for prior, current in zip(sessions, sessions[1:]):
        ret = {s: observed[s][current] / observed[s][prior] - 1 for s in SYMBOLS}
        periods.append({
            "periodEndAt": current + "T23:59:59+00:00", "depositAtStart": "0",
            "strategyGrossReturn": str(sum(weights[s] * ret[s] for s in SYMBOLS)),
            "benchmarkGrossReturn": str(ret["SPY"]),
            "strategyExpenseFractionAtStart": str(strategy_fee),
            "benchmarkExpenseFractionAtStart": str(benchmark_fee),
            "strategyFixedFeeAtStart": "0", "benchmarkFixedFeeAtStart": "0",
        })
    comparison = replay_passive_benchmark(
        opening_balance=policy["startingCapital"], currency="USD", periods=periods,
    )
    report = {
        "schemaVersion": 1, "kind": "ordivon.finance.research.partial-forward-observation",
        "standing": "PARTIAL_FORWARD_DESCRIPTIVE_SOURCE_UNVERIFIED",
        "frozenPlanDigest": frozen["planDigest"], "observedSessions": sessions,
        "returnPeriods": len(periods), "sourceReceipts": receipts,
        "economicComparison": comparison,
        "historicalPITVerified": False, "independentSourceAuthenticityVerified": False,
        "dataRightsIndependentlyVerified": False, "corporateActionsQualified": False,
        "completeHoldoutVerified": False, "alphaVerified": False,
        "realMoneyOrdersAuthorized": False,
        "notEvaluated": [
            "Complete holdout through 2027-03-31",
            "Vendor rights, original source wire and publisher observation clock",
            "Dividends, splits, transaction costs, tax and real-money trading",
            "Statistical significance, independent alpha and investor utility",
        ],
    }
    # Source bytes never appear in Git, Host messages or stdout. Keep this
    # operator-chosen folder outside a Git checkout and access restricted.
    private_output.mkdir(parents=True, exist_ok=False, mode=0o700)
    for s, raw in bytes_by_symbol.items():
        with os.fdopen(os.open(private_output / receipts[s]["normalizedFile"], os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600), "wb") as f:
            f.write(raw)
    with os.fdopen(os.open(private_output / "partial-forward-report.json", os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600), "w", encoding="utf-8") as f:
        json.dump(report, f, sort_keys=True, indent=2)
        f.write("\n")
    return report


def main() -> int:
    cli = argparse.ArgumentParser(description="Frozen forward SPY/SHY observation, non-live/private")
    cli.add_argument("--frozen", type=Path, required=True)
    cli.add_argument("--policy", type=Path, required=True)
    cli.add_argument("--through", required=True)
    cli.add_argument("--private-output", type=Path, required=True)
    a = cli.parse_args()
    from openbb import obb  # Official mature provider; pinned only in native R3 environment.

    def fetch(symbol: str, start: str, end: str) -> tuple:
        requested = datetime.now(UTC)
        result = obb.cboe.equity.historical(symbol=symbol, start_date=start, end_date=end, provider="cboe")
        received = datetime.now(UTC)
        return str(result.provider), result.to_dataframe(), requested, received

    print(json.dumps(observe(a.frozen, a.policy, a.through, a.private_output, fetch), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
