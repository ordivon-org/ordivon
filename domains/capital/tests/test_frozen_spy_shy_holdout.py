"""Original Research freeze + Cboe observation -> existing Portfolio passive replay."""
from __future__ import annotations

import hashlib
import json
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "adoption" / "r3_native"))
from frozen_spy_shy_holdout import format_partial_forward_markdown, observe  # noqa: E402

FROZEN = ROOT / "evidence/finance-research/spy-shy-forward-20261108/frozen-plan.json"
POLICY = ROOT / "examples/paper_fixed_mix_etf_20261106.json"
CLOCK = datetime(2026, 11, 12, 12, 0, tzinfo=UTC)


def fake(symbol: str, start: str, end: str):
    assert start == "2026-11-09" and end == "2026-11-13"
    prices = [100, 102, 101] if symbol == "SPY" else [50, 50, 51]
    frame = pd.DataFrame(
        {"open": prices, "high": prices, "low": prices, "close": prices, "volume": [100, 100, 100]},
        index=["2026-11-09", "2026-11-10", "2026-11-11"],
    )
    return "cboe", frame, CLOCK, CLOCK


def test_reuses_actual_frozen_research_and_existing_portfolio_with_private_bytes(tmp_path):
    folder = tmp_path / "private"
    result = observe(FROZEN, POLICY, "2026-11-13", folder, fake)
    assert result["frozenPlanDigest"] == "sha256:3798e0f219081439f0679dd57f1e4c77aa0842bb11e7561517d28c94023b9501"
    assert result["standing"] == "PARTIAL_FORWARD_DESCRIPTIVE_SOURCE_UNVERIFIED"
    assert result["returnPeriods"] == 2
    assert result["frozenAdjustedCloseMetricReproduced"] is False
    assert result["observedPriceBasis"] == "OPENBB_CBOE_DAILY_CLOSE_ADJUSTMENT_UNKNOWN"
    assert result["observedSessions"] == ["2026-11-09", "2026-11-10", "2026-11-11"]
    assert result["sessionQualification"]["SPY"]["dateStanding"] == (
        "EXCHANGE_SESSION_ALIGNED_SOURCE_UNVERIFIED"
    )
    assert result["sessionQualification"]["SHY"]["requestedEnd"] == "2026-11-11"
    assert result["sessionQualification"]["SPY"]["capitalAuthority"] is False
    assert result["economicComparison"]["standing"] == "DESCRIPTIVE_REPLAY_NO_MARKET_VALIDATION"
    assert result["economicComparison"]["contributedCapital"] == "100000"
    for key in ("alphaVerified", "historicalPITVerified", "completeHoldoutVerified", "realMoneyOrdersAuthorized", "dataRightsIndependentlyVerified"):
        assert result[key] is False
    assert (folder.stat().st_mode & 0o777) == 0o700
    for ticker in ("SPY", "SHY"):
        source = folder / f"openbb_cboe_{ticker}_normalized.csv"
        assert (source.stat().st_mode & 0o777) == 0o600
        assert hashlib.sha256(source.read_bytes()).hexdigest() == result["sourceReceipts"][ticker]["normalizedSha256"]
    assert json.loads((folder / "partial-forward-report.json").read_text()) == result
    with pytest.raises(ValueError, match="already exists"):
        observe(FROZEN, POLICY, "2026-11-13", folder, fake)


def test_modified_original_policy_cannot_rewrite_forward_study(tmp_path):
    altered = json.loads(POLICY.read_text())
    altered["policy"]["weightsBps"] = {"SPY": 7000, "SHY": 3000}
    path = tmp_path / "altered.json"
    path.write_text(json.dumps(altered))
    with pytest.raises(ValueError, match="changed precommitted"):
        observe(FROZEN, path, "2026-11-13", tmp_path / "bad", lambda *_: pytest.fail("should not fetch"))
    assert not (tmp_path / "bad").exists()


def test_missing_session_and_wrong_provider_rejected_before_private_publish(tmp_path):
    def gap(symbol, start, end):
        p, frame, begin, received = fake(symbol, start, end)
        if symbol == "SHY":
            frame = frame.drop("2026-11-10")
        return p, frame, begin, received
    with pytest.raises(ValueError, match="incomplete paired"):
        observe(FROZEN, POLICY, "2026-11-13", tmp_path / "gap", gap)
    assert not (tmp_path / "gap").exists()

    def foreign(symbol, start, end):
        _, frame, begin, received = fake(symbol, start, end)
        return "foreign", frame, begin, received
    with pytest.raises(ValueError, match="provider or capture"):
        observe(FROZEN, POLICY, "2026-11-13", tmp_path / "foreign", foreign)


def test_source_future_row_and_outside_holdout_cut_rejected(tmp_path):
    with pytest.raises(ValueError, match="outside the frozen future"):
        observe(FROZEN, POLICY, "2028-01-01", tmp_path / "late", fake)

    def forward_future(symbol, start, end):
        p, frame, begin, received = fake(symbol, start, end)
        frame.index = ["2026-11-09", "2026-11-10", "2026-11-14"]
        return p, frame, begin, received
    with pytest.raises(ValueError, match="future or out-of-period"):
        observe(FROZEN, POLICY, "2026-11-13", tmp_path / "future_row", forward_future)
    assert not (tmp_path / "future_row").exists()


def test_human_facing_report_reuses_economic_result_and_keeps_unknowns(tmp_path):
    report = observe(FROZEN, POLICY, "2026-11-13", tmp_path / "private", fake)
    shown = format_partial_forward_markdown(report)
    assert "60% SPY / 40% SHY" in shown
    assert "SPY 基准期末" in shown
    assert "统计 Alpha 均未认证" in shown
    assert "风险预算未评估" in shown
    assert "冻结研究复权口径的合格复现" in shown
    assert "任何实盘金融写入权限" in shown
    tampered = dict(report)
    tampered["alphaVerified"] = True
    with pytest.raises(ValueError, match="unqualified result"):
        format_partial_forward_markdown(tampered)


@pytest.mark.parametrize("polluted_day,through,received", [
    ("2026-11-15", "2026-11-16", datetime(2026, 11, 16, 12, tzinfo=UTC)),
    ("2026-11-26", "2026-11-27", datetime(2026, 11, 28, 12, tzinfo=UTC)),
])
def test_same_fake_session_in_both_etfs_cannot_pass_as_exchange_day(
    tmp_path, polluted_day, through, received,
):
    import exchange_calendars as xcals

    # A provider may not include its same-day close in this consumer.
    # Use only the already finished dates, then inject the fake session.
    safe_end = min(through, (received.date() - timedelta(days=1)).isoformat())
    dates = [
        d.strftime("%Y-%m-%d")
        for d in xcals.get_calendar("XNYS").sessions_in_range("2026-11-09", safe_end)
    ]
    dates.append(polluted_day)
    dates.sort()

    def both_wrong(symbol, start, end):
        assert end == through and start == "2026-11-09"
        price = 100 if symbol == "SPY" else 50
        frame = pd.DataFrame({
            "open": [price] * len(dates), "high": [price] * len(dates),
            "low": [price] * len(dates), "close": [price] * len(dates),
            "volume": [100] * len(dates),
        }, index=dates)
        return "cboe", frame, received, received

    dest = tmp_path / "invalid-private"
    with pytest.raises(ValueError, match="XNYS_SESSION_GRID_MISMATCH"):
        observe(FROZEN, POLICY, through, dest, both_wrong)
    assert not dest.exists()


def test_both_etfs_cannot_hide_missing_last_completed_xnys_session(tmp_path):
    # November 12 is a valid session; both source files stop at November 11
    # even though they were received November 13 and claim coverage through 13.
    def both_stale(symbol, start, end):
        provider, frame, _, _ = fake(symbol, start, end)
        received = datetime(2026, 11, 13, 12, tzinfo=UTC)
        return provider, frame, received, received

    dest = tmp_path / "stale-private"
    with pytest.raises(ValueError, match="XNYS_SESSION_GRID_MISMATCH"):
        observe(FROZEN, POLICY, "2026-11-13", dest, both_stale)
    assert not dest.exists()
