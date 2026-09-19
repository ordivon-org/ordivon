from __future__ import annotations

import subprocess
from pathlib import Path

import pandas as pd

REQUIRED_COLUMNS = [
    "Day",
    "Market Participant",
    "Total Shares",
    "Total Notional",
    "Total Trade Count",
]


def fetch_cboe_csv(url: str, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [
            "/usr/bin/curl",
            "--location",
            "--fail",
            "--silent",
            "--show-error",
            "--retry",
            "2",
            "--retry-delay",
            "1",
            url,
            "--output",
            str(destination),
        ],
        check=True,
    )


def build_daily_market_structure(raw: pd.DataFrame) -> pd.DataFrame:
    missing = [column for column in REQUIRED_COLUMNS if column not in raw.columns]
    if missing:
        raise ValueError(f"Missing Cboe columns: {missing}")

    frame = raw.copy()
    frame["Day"] = pd.to_datetime(frame["Day"], format="%Y-%m-%d", errors="raise")
    duplicate = frame.duplicated(subset=["Day", "Market Participant"], keep=False)
    if duplicate.any():
        rows = frame.loc[duplicate, ["Day", "Market Participant"]].to_dict("records")
        raise ValueError(f"Duplicate Cboe day/participant rows: {rows[:5]}")

    for column in ["Total Shares", "Total Notional", "Total Trade Count"]:
        frame[column] = pd.to_numeric(frame[column], errors="raise")
        if (frame[column] < 0).any():
            raise ValueError(f"Negative Cboe value in {column}")

    frame["is_trf"] = frame["Market Participant"].str.contains("TRF", case=False, na=False)

    total = (
        frame.groupby("Day", as_index=False)[["Total Shares", "Total Notional", "Total Trade Count"]]
        .sum()
        .rename(
            columns={
                "Day": "day",
                "Total Shares": "total_shares",
                "Total Notional": "total_notional",
                "Total Trade Count": "total_trade_count",
            }
        )
    )
    trf = (
        frame.loc[frame["is_trf"]]
        .groupby("Day", as_index=False)["Total Shares"]
        .sum()
        .rename(columns={"Day": "day", "Total Shares": "trf_shares"})
    )
    out = total.merge(trf, on="day", how="left")
    out["trf_shares"] = out["trf_shares"].fillna(0.0)
    if (out["total_shares"] <= 0).any():
        raise ValueError("Non-positive total market shares")
    out["trf_share"] = out["trf_shares"] / out["total_shares"]
    return out.sort_values("day").reset_index(drop=True)
