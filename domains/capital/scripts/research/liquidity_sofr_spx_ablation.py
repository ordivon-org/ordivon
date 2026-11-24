"""One-hypothesis retrospective test: SOFR repo conditions vs price-only SPX predictions.

No API keys, broker effects, market-data redistribution, historical-vintage attestation,
alpha claim, or authorization of trade. The external CSV files are PRIVATE inputs.
"""

from __future__ import annotations

import argparse
import bisect
import csv
import hashlib
import json
import math
from datetime import datetime
from pathlib import Path

import numpy as np
from sklearn.linear_model import Ridge
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

# The natural Markets owner already admits the complete XNYS trading session grid.
from ordivon_capital.markets.equity_session_calendar import require_xnys_session_grid

HORIZON = 5
MIN_TRAINING = 500
FUNDING_LAG_SESSIONS = 2  # strictly conservative; NOT a historical-vintage certification
TURNOVER_BPS_PER_SIDE = 5
PRICE_START = "2018-04-02"
PRICE_END = "2026-11-19"


def _file_bytes(path: Path) -> bytes:
    raw = path.read_bytes()
    if len(raw) > 5_000_000:
        raise ValueError("unbounded input")
    return raw


def load_sources(*, spx: bytes, sofr: bytes):
    raw_px = list(csv.DictReader(spx.decode("utf-8-sig").splitlines()))
    if not raw_px or set(raw_px[0]) != {"DATE", "SPX"}:
        raise ValueError("unexpected CBOE SPX CSV header")
    prices = {}
    for row in raw_px:
        d = datetime.strptime(row["DATE"], "%m/%d/%Y").date()
        if not PRICE_START <= d.isoformat() <= PRICE_END:
            continue
        if d in prices:
            raise ValueError("duplicate SPX session")
        p = float(row["SPX"])
        if not math.isfinite(p) or p <= 0:
            raise ValueError("invalid SPX price index")
        prices[d] = p
    days = sorted(prices)
    require_xnys_session_grid(
        [d.isoformat() for d in days],
        symbol="CBOE_SPX_PRICE_INDEX",
        requested_start=PRICE_START,
        requested_end=PRICE_END,
    )

    rates_raw = list(csv.DictReader(sofr.decode("utf-8-sig").splitlines()))
    required = {
        "Effective Date",
        "Rate Type",
        "Rate (%)",
        "1st Percentile (%)",
        "99th Percentile (%)",
        "Volume ($Billions)",
        "Revision Indicator (Y/N)",
    }
    if not rates_raw or not required.issubset(rates_raw[0]):
        raise ValueError("unexpected official NY Fed SOFR schema")
    rates = {}
    missing_funding_days = []
    for row in rates_raw:
        if row["Rate Type"] != "SOFR":
            raise ValueError("different secured funding rate type")
        d = datetime.strptime(row["Effective Date"], "%m/%d/%Y").date()
        if d in rates:
            raise ValueError("duplicate SOFR effective date")
        if row["Revision Indicator (Y/N)"].strip().upper() == "Y":
            raise ValueError("explicit revision row cannot be treated as first release")
        # The New York Fed correctly reports NEGATIVE repo percentile rates in
        # 2020-2022; negative is not inherently invalid. A few explicit NA
        # percentile rows are excluded rather than silently set to zero.
        try:
            rate = float(row["Rate (%)"])
            lo = float(row["1st Percentile (%)"])
            hi = float(row["99th Percentile (%)"])
            vol = float(row["Volume ($Billions)"])
        except ValueError as exc:
            value_fields = (
                "Rate (%)",
                "1st Percentile (%)",
                "99th Percentile (%)",
                "Volume ($Billions)",
            )
            if not any(row[field].strip().upper() in {"NA", ""} for field in value_fields):
                raise ValueError("unparseable funding numeric field") from exc
            for field in value_fields:
                v = row[field].strip().upper()
                if v not in {"NA", ""}:
                    try:
                        float(v)
                    except ValueError as invalid:
                        raise ValueError("unexpected funding field token") from invalid
            missing_funding_days.append(d.isoformat())
            continue
        if (
            any(not math.isfinite(x) for x in (rate, lo, hi, vol))
            or not (-10 <= lo <= rate <= hi < 100)
            or vol <= 0
        ):
            raise ValueError("invalid funding source row")
        rates[d] = (rate, vol, hi - lo)
    return days, prices, rates, sorted(missing_funding_days)


def make_dataset(days, prices, rates, *, lag=FUNDING_LAG_SESSIONS):
    if lag < 2:
        raise ValueError("SOFR effective day may not be treated as observed on that same close")
    effective_days = sorted(rates)
    feature_rows = []
    for i in range(21, len(days) - HORIZON - 1):
        # Funding data MUST have a sufficiently old EFFECTIVE date.
        # This does not assert a historical first-published vintage.
        cutoff = days[i - lag]
        k = bisect.bisect_right(effective_days, cutoff) - 1
        if k < 10:
            continue
        current = rates[effective_days[k]]
        previous = rates[effective_days[k - 5]]
        # Price known at decision close only; entry is NEXT close and exit is
        # 5 subsequent price-index closes later (not a fill assertion).
        momentum = math.log(prices[days[i]] / prices[days[i - 20]])
        funding = (current[0], math.log(current[1] / previous[1]), current[2])
        target = prices[days[i + HORIZON + 1]] / prices[days[i + 1]] - 1
        feature_rows.append(
            {
                "index": i,
                "decision": days[i].isoformat(),
                "effective": effective_days[k].isoformat(),
                "latest_usable_cutoff": cutoff.isoformat(),
                "price": (momentum,),
                "full": (momentum,) + funding,
                "target": target,
                "entry": prices[days[i + 1]],
                "exit": prices[days[i + HORIZON + 1]],
            }
        )
    if len(feature_rows) < 800:
        raise ValueError("insufficient data for walk-forward")
    for r in feature_rows:
        assert r["effective"] <= r["latest_usable_cutoff"] < r["decision"]
    return feature_rows


def _matured_rows(rows, k):
    candidate = rows[k]
    return [r for r in rows[:k] if r["index"] + HORIZON + 1 <= candidate["index"]]


def predict(rows, offset):
    # Independent nonoverlapping evaluation windows, walk-forward retraining.
    # Train on only the rows whose *entire outcome* already ended by the
    # decision close; exclude target windows still in progress.
    results = []
    for k in range(MIN_TRAINING + HORIZON + 1 + offset, len(rows), HORIZON):
        candidate = rows[k]
        matured = _matured_rows(rows, k)
        if len(matured) < MIN_TRAINING:
            continue
        y = np.array([r["target"] for r in matured], dtype=float)
        preds = {"mean": float(np.mean(y))}
        for model, fields in [("price", "price"), ("funding", "full")]:
            X = np.array([r[fields] for r in matured], dtype=float)
            pipe = make_pipeline(StandardScaler(), Ridge(alpha=10.0))
            pipe.fit(X, y)
            preds[model] = float(pipe.predict(np.array([candidate[fields]]))[0])
        results.append({**candidate, "preds": preds})
    return results


def evaluate(results):
    if len(results) < 50:
        raise ValueError("insufficient nonoverlap samples")
    m = {}
    y = np.array([r["target"] for r in results])
    for key in ("mean", "price", "funding"):
        pred = np.array([r["preds"][key] for r in results])
        mse = float(np.mean((y - pred) ** 2))
        m[key] = {
            "mse": mse,
            "signAccuracy": float(np.mean((pred > 0) == (y > 0))),
            "longWindows": int(np.sum(pred > 0)),
        }
    # Illustrative price-index-only sleeve; no dividends, broker, fills or capital
    # authority. Charge 5bps when increasing or decreasing notional exposure.
    cash_growth = {}
    for key in ("price", "funding", "passive"):
        wealth = 1000.0
        last_pos = 0
        trades = 0
        for r in results:
            pos = int(key == "passive" or r["preds"][key] > 0)
            if pos != last_pos:
                wealth *= 1 - TURNOVER_BPS_PER_SIDE / 10000
                trades += 1
            if pos:
                wealth *= 1 + r["target"]
            last_pos = pos
        if last_pos:
            wealth *= 1 - TURNOVER_BPS_PER_SIDE / 10000
            trades += 1
        cash_growth[key] = {"terminalIndexProxyDollars": round(wealth, 2), "entryExitSides": trades}
    return {
        "nNonoverlapWindows": len(results),
        "firstDecision": results[0]["decision"],
        "lastDecision": results[-1]["decision"],
        "predictionMetrics": m,
        "illustrativeSleeves": cash_growth,
        "fundingMseIncrementVsPrice": m["price"]["mse"] - m["funding"]["mse"],
    }


def run(spx: bytes, sofr: bytes):
    days, prices, rates, missing = load_sources(spx=spx, sofr=sofr)
    rows = make_dataset(days, prices, rates)
    by_phase = {str(phase): evaluate(predict(rows, phase)) for phase in range(HORIZON)}
    return {
        "kind": "ordivon.finance.research.sofr-to-spx-retrospective-ablation",
        "standing": "RETROSPECTIVE_LATEST_SNAPSHOT_ONLY_NOT_PIT_OR_ALPHA",
        "capturedSnapshotDigests": {
            "cboe_spx": hashlib.sha256(spx).hexdigest(),
            "nyfed_sofr": hashlib.sha256(sofr).hexdigest(),
        },
        "sourceRows": {
            "cboeSPX": len(days),
            "nyfedSOFR": len(rates),
            "featureRows": len(rows),
            "nyfedRowsWithMissingFields": len(missing),
            "nyfedMissingFieldEffectiveDates": missing,
        },
        "sourceURLs": {
            "cboe_spx": "https://cdn.cboe.com/api/global/us_indices/daily_prices/SPX_History.csv",
            "nyfed_sofr": "https://markets.newyorkfed.org/api/rates/secured/sofr/search.csv?startDate=2018-01-01&endDate=2026-11-19",
        },
        "design": {
            "fundingInformationUsedOnlyIfEffectiveAtLeastXNYSsessionsBeforeClose": FUNDING_LAG_SESSIONS,
            "target": "SPX_CLOSE[t+6]/SPX_CLOSE[t+1]-1",
            "priceFeatures": ["20_session_log_return"],
            "addedFundingFeatures": [
                "SOFR_rate_percent",
                "SOFR_volume_log_change_5observations",
                "SOFR_99th_minus_1st_percentile",
            ],
            "model": "sklearn Ridge(alpha=10)+StandardScaler; walkforward; at least 500 mature-train rows",
            "decisionPhaseOffsets": [0, 1, 2, 3, 4],
            "syntheticCostBpsPerExposureSide": TURNOVER_BPS_PER_SIDE,
        },
        "limitations": [
            "SOFR daily CSV is latest observable historical dataset, NOT first-released vintage.",
            "Publication calendar/time is estimated conservatively; not historical proof.",
            "Cboe SPX is copyrighted price-only nontradeable index, NOT dividend-adjusted SPY ETF.",
            "No broker fills, taxes, slippage, realistic transaction costs or investment recommendation.",
            "Feature/horizon selected as pilot; no corrected multiple-test significance or regime robustness.",
        ],
        "phases": by_phase,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--spx", type=Path, required=True)
    ap.add_argument("--sofr", type=Path, required=True)
    ap.add_argument("--output", type=Path)
    args = ap.parse_args()
    o = run(_file_bytes(args.spx), _file_bytes(args.sofr))
    x = json.dumps(o, ensure_ascii=False, indent=2, sort_keys=True)
    if args.output:
        args.output.write_text(x + "\n")
    print(x)


if __name__ == "__main__":
    main()
