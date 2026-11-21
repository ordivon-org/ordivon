"""Source-free, mature-calendar negative controls for private Finance data."""

from __future__ import annotations

import hashlib
import json
import unittest

import exchange_calendars as xcals
import pandas as pd

from adoption.r3_native.market_daily_close_consumer import (
    FOCUS,
    INDEX_SYMBOLS,
    MAG7,
    ResearchPanelError,
    describe_close_panel,
)

SYMBOLS = list(
    dict.fromkeys(
        (
            *FOCUS,
            *MAG7,
            "MAGS",
            "IWM",
            "RSP",
            "XLC",
            "SOXX",
            "INTC",
            "MU",
            "TSM",
            "ASML",
            "ARM",
            "MRVL",
            "CRWV",
            "ANET",
            "DELL",
            "VRT",
            "PLTR",
            "TLT",
            "IEF",
            "HYG",
            "LQD",
            "SHY",
            "XLE",
            "GLD",
            "SNDK",
        )
    )
)


def _digest(raw: bytes) -> str:
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def source_fixture():
    sessions = xcals.get_calendar("XNYS").sessions_in_range("2025-01-02", "2026-11-13")
    values = pd.DataFrame(
        {
            symbol: [100.0 + i * 0.1 + j / 100 for i in range(len(sessions))]
            for j, symbol in enumerate(SYMBOLS)
        },
        index=sessions,
    )
    values.index.name = "session_date"
    raw = values.to_csv().encode()
    records = []
    for symbol in SYMBOLS:
        records.append(
            {
                "symbol": symbol,
                "historicalPITVerified": False,
                "adjustedTotalReturnsVerified": False,
                "compatibleWithMarketsAdjustedCloseAdmission": False,
                "compatibleWithLiveOrPaperEodAdmission": False,
                "sourceSplit": (
                    {"all": "cboe-official-index-level"}
                    if symbol in INDEX_SYMBOLS
                    else {
                        "through20261112": "openbb-cboe",
                        "session20261113": "nasdaq-native-historical",
                    }
                ),
                "firstObservedSession": str(sessions[0].date()),
                "lastObservedSession": str(sessions[-1].date()),
                "validRows": len(sessions),
                "latestSessionClose": str(float(values[symbol].iloc[-1])),
            }
        )
    manifest = {
        "kind": "ordivon.finance.close-only-research-panel",
        "schemaVersion": 1,
        "calendarSource": "exchange_calendars XNYS",
        "EXTERNAL_RIGHTS": "UNKNOWN",
        "HISTORICAL_PIT": "UNKNOWN",
        "CORPORATE_ACTIONS": "UNKNOWN",
        "LIVE_OR_PAPER_AUTHORITY": False,
        "NO_IMPUTATION": True,
        "firstSession": str(sessions[0].date()),
        "lastSession": str(sessions[-1].date()),
        "sessions": len(sessions),
        "series": len(SYMBOLS),
        "records": records,
        "panelDigest": _digest(raw),
    }
    return values, raw, manifest


def to_bytes(value: dict) -> bytes:
    return json.dumps(value, sort_keys=True).encode()


class ResearchPanelTest(unittest.TestCase):
    def test_complete_calendar_has_readonly_results(self):
        _, raw, manifest = source_fixture()
        res = describe_close_panel(raw, to_bytes(manifest))
        self.assertEqual(res["asOfExchangeSession"], "2026-11-13")
        self.assertEqual(res["seriesCount"], len(SYMBOLS))
        self.assertEqual(res["crossAsset"]["mag7DownCount"], 0)
        self.assertEqual(res["standing"], "RETROSPECTIVE_CLOSE_ONLY_SOURCE_UNQUALIFIED")
        self.assertFalse(res["evidenceLimits"]["capitalAuthority"])
        self.assertFalse(res["evidenceLimits"]["paperAccountingEffect"])
        self.assertEqual(res["evidenceLimits"]["historicalPIT"], "UNKNOWN")

    def test_bytes_mutation_rejected(self):
        _, raw, manifest = source_fixture()
        with self.assertRaisesRegex(ResearchPanelError, "manifest"):
            describe_close_panel(raw.replace(b"100.0", b"101.0", 1), to_bytes(manifest))

    def test_fake_holiday_not_accepted_even_with_changed_manifest_hash(self):
        data, _, manifest = source_fixture()
        artificial = pd.DataFrame(
            {name: [151.0] for name in data.columns},
            index=pd.DatetimeIndex([pd.Timestamp("2025-05-26")]),
        )
        changed = pd.concat([data, artificial]).sort_index()
        changed.index.name = "session_date"
        raw = changed.to_csv().encode()
        manifest["sessions"] = len(changed)
        manifest["panelDigest"] = _digest(raw)
        for row in manifest["records"]:
            row["validRows"] += 1
        with self.assertRaisesRegex(ResearchPanelError, "holiday"):
            describe_close_panel(raw, to_bytes(manifest))

    def test_missing_latest_quote_cannot_be_filled(self):
        data, _, manifest = source_fixture()
        data.loc[data.index[-1], "QQQ"] = float("nan")
        raw = data.to_csv().encode()
        manifest["panelDigest"] = _digest(raw)
        with self.assertRaisesRegex(ResearchPanelError, "recent price missing"):
            describe_close_panel(raw, to_bytes(manifest))

    def test_research_cannot_claim_paper_authority(self):
        _, raw, manifest = source_fixture()
        manifest["LIVE_OR_PAPER_AUTHORITY"] = True
        with self.assertRaisesRegex(ResearchPanelError, "promotes"):
            describe_close_panel(raw, to_bytes(manifest))

    def test_research_cannot_claim_historical_pit(self):
        _, raw, manifest = source_fixture()
        manifest["records"][0]["historicalPITVerified"] = True
        with self.assertRaisesRegex(ResearchPanelError, "promotion"):
            describe_close_panel(raw, to_bytes(manifest))

    def test_source_role_is_exact(self):
        _, raw, manifest = source_fixture()
        manifest["records"][0]["sourceSplit"]["session20261113"] = "cboe"
        with self.assertRaisesRegex(ResearchPanelError, "source role"):
            describe_close_panel(raw, to_bytes(manifest))

    def test_manifest_contains_no_duplicate_keys(self):
        _, raw, manifest = source_fixture()
        serialized = to_bytes(manifest).decode()
        duplicate = serialized.replace(
            '"calendarSource": "exchange_calendars XNYS",',
            '"calendarSource": "exchange_calendars XNYS", "calendarSource": "exchange_calendars XNYS",',
            1,
        )
        with self.assertRaisesRegex(ResearchPanelError, "duplicate manifest key"):
            describe_close_panel(raw, duplicate.encode())

    def test_per_symbol_last_close_must_match_manifest(self):
        _, raw, manifest = source_fixture()
        manifest["records"][0]["latestSessionClose"] = "-500.0"
        with self.assertRaisesRegex(ResearchPanelError, "coverage"):
            describe_close_panel(raw, to_bytes(manifest))

    def test_nontrading_future_session_cannot_be_promoted(self):
        data, _, manifest = source_fixture()
        next_day = pd.DataFrame(
            {name: [151.0] for name in data.columns},
            index=pd.DatetimeIndex([pd.Timestamp("2026-11-14")]),
        )
        changed = pd.concat([data, next_day]).sort_index()
        changed.index.name = "session_date"
        raw = changed.to_csv().encode()
        manifest["sessions"] = len(changed)
        manifest["lastSession"] = "2026-11-14"
        manifest["panelDigest"] = _digest(raw)
        for row in manifest["records"]:
            row["lastObservedSession"] = "2026-11-14"
            row["validRows"] += 1
            row["latestSessionClose"] = "151.0"
        with self.assertRaisesRegex(ResearchPanelError, "holiday"):
            describe_close_panel(raw, to_bytes(manifest))


if __name__ == "__main__":
    unittest.main()
