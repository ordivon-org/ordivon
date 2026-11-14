"""Read-only closed-session, source-bound descriptive Finance market consumer.

Source authority: existing Markets. Neither raw closing prices nor hashes
grant adjusted-total-return, PIT, Paper Accounting, or live trading rights.
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
from pathlib import Path

import exchange_calendars as xcals
import numpy as np
import pandas as pd

KIND = "ordivon.finance.close-only-research-panel"
INDEX_SYMBOLS = frozenset(("VIX", "VXN", "VVIX", "VIX9D"))
MAG7 = ("AAPL", "MSFT", "AMZN", "GOOGL", "META", "TSLA", "NVDA")
FOCUS = ("SPY", "QQQ", "SMH", "AVGO", "AMD", "ORCL", "SPCX", "VIX", "VXN", "VVIX", "VIX9D")
REQUIRED = frozenset((*FOCUS, *MAG7, "MAGS"))
MAX_BYTES = 8_000_000


class ResearchPanelError(ValueError):
    """Unqualified provenance, calendar, or price coverage."""


def _unique_keys(pairs: list[tuple[str, object]]) -> dict:
    result = {}
    for key, value in pairs:
        if key in result:
            raise ResearchPanelError(f"duplicate manifest key {key}")
        result[key] = value
    return result


def _sha(raw: bytes) -> str:
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def _round(value: float) -> float:
    return round(float(value), 8)


def describe_close_panel(panel_bytes: bytes, manifest_bytes: bytes) -> dict:
    """Compute source-bounded observations only, never forecasts or trade orders."""
    if not (0 < len(panel_bytes) <= MAX_BYTES and 0 < len(manifest_bytes) <= MAX_BYTES):
        raise ResearchPanelError("source bytes are empty or unbounded")
    try:
        manifest = json.loads(manifest_bytes, object_pairs_hook=_unique_keys)
        if (
            manifest["schemaVersion"] != 1
            or manifest["kind"] != KIND
            or manifest["panelDigest"] != _sha(panel_bytes)
            or manifest["calendarSource"] != "exchange_calendars XNYS"
            or manifest["EXTERNAL_RIGHTS"] != "UNKNOWN"
            or manifest["HISTORICAL_PIT"] != "UNKNOWN"
            or manifest["CORPORATE_ACTIONS"] != "UNKNOWN"
            or manifest["LIVE_OR_PAPER_AUTHORITY"] is not False
            or manifest["NO_IMPUTATION"] is not True
        ):
            raise ResearchPanelError("manifest falsely promotes research evidence")
        records = manifest["records"]
        symbols = [row["symbol"] for row in records]
        if not (
            len(symbols) == manifest["series"] == len(set(symbols)) and REQUIRED.issubset(symbols)
        ):
            raise ResearchPanelError("symbol set does not match research contract")
        for row in records:
            if (
                row["historicalPITVerified"] is not False
                or row["adjustedTotalReturnsVerified"] is not False
                or row["compatibleWithMarketsAdjustedCloseAdmission"] is not False
                or row["compatibleWithLiveOrPaperEodAdmission"] is not False
            ):
                raise ResearchPanelError("unjustified per-symbol data promotion")
            origins = row["sourceSplit"]
            if row["symbol"] in INDEX_SYMBOLS:
                if origins != {"all": "cboe-official-index-level"}:
                    raise ResearchPanelError("index source role mismatch")
            elif origins != {
                "through20261112": "openbb-cboe",
                "session20261113": "nasdaq-native-historical",
            }:
                raise ResearchPanelError("equity source role mismatch")
        df = pd.read_csv(io.BytesIO(panel_bytes), dtype={"session_date": str})
        if list(df.columns) != ["session_date", *symbols] or len(df) != manifest["sessions"]:
            raise ResearchPanelError("panel columns/sessions mismatch")
        dates = pd.DatetimeIndex(
            pd.to_datetime(df.pop("session_date"), format="%Y-%m-%d", errors="raise")
        )
        if dates.has_duplicates or not dates.is_monotonic_increasing:
            raise ResearchPanelError("duplicate or unordered sessions")
        if (
            str(dates[0].date()) != manifest["firstSession"]
            or str(dates[-1].date()) != manifest["lastSession"]
            or len(dates) < 205
        ):
            raise ResearchPanelError("panel date bounds invalid")
        if not dates.equals(xcals.get_calendar("XNYS").sessions_in_range(dates[0], dates[-1])):
            raise ResearchPanelError("market panel contains a holiday or omits an exchange session")
        df.index = dates
        df = df.apply(pd.to_numeric, errors="raise")
        array = df.to_numpy(dtype=float)
        if not np.isfinite(array[~pd.isna(array)]).all() or (df <= 0).any().any():
            raise ResearchPanelError("nonpositive or nonfinite price")
        if df.iloc[-2:].isna().any().any():
            raise ResearchPanelError("recent price missing; no forward-fill allowed")
        for row in records:
            values = df[row["symbol"]].dropna()
            if (
                str(values.index[0].date()) != row["firstObservedSession"]
                or str(values.index[-1].date()) != row["lastObservedSession"]
                or len(values) != row["validRows"]
                or float(values.iloc[-1]) != float(row["latestSessionClose"])
                or df.loc[values.index[0] :, row["symbol"]].isna().any()
            ):
                raise ResearchPanelError("per-symbol coverage/source mismatch")
        current, previous = df.iloc[-1], df.iloc[-2]
        daily = current / previous - 1
        qqq = df["QQQ"].dropna()
        ema = qqq.ewm(span=200, adjust=False, min_periods=200).mean()
        sma = qqq.rolling(200, min_periods=200).mean()
        if not np.isfinite([ema.iloc[-1], sma.iloc[-1]]).all():
            raise ResearchPanelError("insufficient EMA200 observations")
        down_count = sum(daily[s] < 0 for s in MAG7)
        return {
            "kind": "ordivon.finance.readonly-multimarket-close-research-r1",
            "sourcePanelSha256": _sha(panel_bytes),
            "manifestSha256": _sha(manifest_bytes),
            "asOfExchangeSession": manifest["lastSession"],
            "exchangeCalendarSessions": len(dates),
            "seriesCount": len(symbols),
            "standing": "RETROSPECTIVE_CLOSE_ONLY_SOURCE_UNQUALIFIED",
            "latest": {
                s: {"close": _round(current[s]), "dailyReturnPct": _round(daily[s] * 100)}
                for s in FOCUS
            },
            "qqq": {
                "ema200": _round(ema.iloc[-1]),
                "sma200": _round(sma.iloc[-1]),
                "closeMinusEmaPct": _round((current["QQQ"] / ema.iloc[-1] - 1) * 100),
                "crossedBelowEmaToday": bool(
                    previous["QQQ"] >= ema.iloc[-2] and current["QQQ"] < ema.iloc[-1]
                ),
            },
            "crossAsset": {
                "qqqMinusSpyDailyPctPoints": _round((daily["QQQ"] - daily["SPY"]) * 100),
                "smhMinusQqqDailyPctPoints": _round((daily["SMH"] - daily["QQQ"]) * 100),
                "mag7DownCount": int(down_count),
                "mag7ConstituentCount": len(MAG7),
                "vxnOverVix": _round(current["VXN"] / current["VIX"]),
            },
            "evidenceLimits": {
                "priceBasis": "UNADJUSTED_CLOSE_PROVISIONAL",
                "historicalPIT": "UNKNOWN",
                "corporateActionsAndVendorRights": "UNKNOWN",
                "forecastSkillVerified": False,
                "tradingAlphaVerified": False,
                "capitalAuthority": False,
                "liveOrders": False,
                "paperAccountingEffect": False,
            },
        }
    except ResearchPanelError:
        raise
    except (KeyError, TypeError, ValueError, IndexError, OverflowError) as exc:
        raise ResearchPanelError("malformed close-only source or manifest") from exc


def main() -> int:
    parser = argparse.ArgumentParser(description="Read-only Finance closes consumer")
    parser.add_argument("--panel", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    args = parser.parse_args()
    result = describe_close_panel(args.panel.read_bytes(), args.manifest.read_bytes())
    print(json.dumps(result, indent=2, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
