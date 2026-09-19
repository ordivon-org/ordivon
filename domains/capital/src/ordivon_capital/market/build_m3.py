from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import mlflow
import pandas as pd
import pandera.pandas as pa

from ordivon_capital.market.cboe_market_structure import build_daily_market_structure, fetch_cboe_csv


def load_json(path: Path):
    return json.loads(path.read_text())


def dump_json(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, sort_keys=True, default=str) + "\n")


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def daily_schema() -> pa.DataFrameSchema:
    return pa.DataFrameSchema(
        {
            "day": pa.Column("datetime64[ns]"),
            "total_shares": pa.Column(float, pa.Check.greater_than(0), coerce=True),
            "total_notional": pa.Column(float, pa.Check.greater_than(0), coerce=True),
            "total_trade_count": pa.Column(float, pa.Check.greater_than(0), coerce=True),
            "trf_shares": pa.Column(float, pa.Check.greater_than_or_equal_to(0), coerce=True),
            "trf_share": pa.Column(float, [pa.Check.greater_than_or_equal_to(0), pa.Check.less_than_or_equal_to(1)], coerce=True),
        },
        strict=True,
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    args = parser.parse_args()
    root = Path(args.root).resolve()

    config = load_json(root / "config/market_data_sources.json")
    source = config["market_structure"]
    raw_path = root / "data/raw/cboe/market_history_2026.csv"
    artifacts = root / "artifacts/wave-a-m3"

    fetch_cboe_csv(source["url"], raw_path)
    raw = pd.read_csv(raw_path)
    daily = daily_schema().validate(build_daily_market_structure(raw))

    parquet_path = artifacts / "daily_market_structure.parquet"
    parquet_path.parent.mkdir(parents=True, exist_ok=True)
    daily.to_parquet(parquet_path, index=False)

    latest = daily.tail(5).copy()
    latest["day"] = latest["day"].dt.strftime("%Y-%m-%d")
    summary = {
        "provider": source["provider"],
        "dataset": source["dataset"],
        "semantics": source["semantics"],
        "symbol_level_price_data": config["symbol_bars"]["status"],
        "first_day": daily.iloc[0]["day"].strftime("%Y-%m-%d"),
        "last_day": daily.iloc[-1]["day"].strftime("%Y-%m-%d"),
        "trading_days": int(len(daily)),
        "latest_five_days": latest.to_dict("records"),
    }
    summary_path = artifacts / "market_structure_summary.json"
    dump_json(summary_path, summary)

    manifest = {
        "source_config_sha256": digest(root / "config/market_data_sources.json"),
        "raw_cboe_csv_sha256": digest(raw_path),
        "daily_market_structure_parquet_sha256": digest(parquet_path),
        "market_structure_summary_sha256": digest(summary_path),
    }
    manifest_path = artifacts / "manifest.json"
    dump_json(manifest_path, manifest)

    tracking_db = artifacts / "mlflow.db"
    mlflow.set_tracking_uri(f"sqlite:///{tracking_db}")
    mlflow.set_experiment("market-capital-wave-a-m3")
    with mlflow.start_run(run_name="cboe-market-structure") as run:
        mlflow.log_param("provider", source["provider"])
        mlflow.log_param("symbol_level_price_data", config["symbol_bars"]["status"])
        mlflow.log_metric("trading_days", len(daily))
        mlflow.log_metric("latest_trf_share", float(daily.iloc[-1]["trf_share"]))
        mlflow.log_artifact(str(root / "config/market_data_sources.json"), artifact_path="inputs")
        mlflow.log_artifact(str(parquet_path), artifact_path="outputs")
        mlflow.log_artifact(str(summary_path), artifact_path="outputs")
        mlflow.log_artifact(str(manifest_path), artifact_path="outputs")
        print(f"MLFLOW_RUN_ID={run.info.run_id}")

    print(latest.to_string(index=False))
    print(f"PARQUET={parquet_path}")
    print(f"MANIFEST={manifest_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
