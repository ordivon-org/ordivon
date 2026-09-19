from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import jsonschema
import mlflow
import pandas as pd
import pandera.pandas as pa

from ordivon_capital.market.sec_companyfacts import build_fundamental_feature, fetch_companyfacts


def load_json(path: Path):
    return json.loads(path.read_text())


def dump_json(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, sort_keys=True) + "\n")


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def dataframe_schema() -> pa.DataFrameSchema:
    return pa.DataFrameSchema(
        {
            "symbol": pa.Column(str),
            "cik": pa.Column(str),
            "entity_name": pa.Column(str),
            "fiscal_year": pa.Column(int),
            "period_end": pa.Column(str),
            "accession": pa.Column(str),
            "net_income": pa.Column(float),
            "assets": pa.Column(float, pa.Check.greater_than(0)),
            "stockholders_equity": pa.Column(float),
            "roa_proxy": pa.Column(float),
            "roe_proxy": pa.Column(float),
            "equity_to_assets": pa.Column(float),
        },
        strict=False,
        coerce=True,
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    args = parser.parse_args()
    root = Path(args.root).resolve()

    issuers = load_json(root / "config/sec_issuers.json")["issuers"]
    raw_dir = root / "data/raw/sec"
    artifacts = root / "artifacts/wave-a-m2"

    features = []
    raw_digests = {}
    for issuer in issuers:
        raw_path = raw_dir / f"{issuer['symbol']}-companyfacts.json"
        facts = fetch_companyfacts(issuer["cik"], raw_path)
        raw_digests[issuer["symbol"]] = digest(raw_path)
        features.append(
            build_fundamental_feature(
                issuer["symbol"], issuer["cik"], issuer["sec_entity_name"], facts
            )
        )

    feature_doc = {"source": "SEC Company Facts API", "features": features}
    feature_json = artifacts / "fundamental_features.json"
    dump_json(feature_json, feature_doc)
    jsonschema.validate(feature_doc, load_json(root / "schema/fundamental_features.schema.json"))

    df = pd.DataFrame(features)
    df = dataframe_schema().validate(df)
    feature_parquet = artifacts / "fundamental_features.parquet"
    feature_parquet.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(feature_parquet, index=False)

    summary = {
        "source": "SEC Company Facts API",
        "metric_semantics": {
            "roa_proxy": "NetIncomeLoss / year-end Assets from the same annual 10-K filing",
            "roe_proxy": "NetIncomeLoss / year-end StockholdersEquity from the same annual 10-K filing",
            "equity_to_assets": "year-end StockholdersEquity / year-end Assets from the same annual 10-K filing"
        },
        "ranking_is_not_alpha_claim": True,
        "rows": [
            {
                "symbol": row["symbol"],
                "fiscal_year": row["fiscal_year"],
                "period_end": row["period_end"],
                "roa_proxy": row["roa_proxy"],
                "roe_proxy": row["roe_proxy"],
                "equity_to_assets": row["equity_to_assets"],
            }
            for row in features
        ],
    }
    summary_path = artifacts / "research_summary.json"
    dump_json(summary_path, summary)

    manifest = {
        "sec_issuers_sha256": digest(root / "config/sec_issuers.json"),
        "raw_companyfacts_sha256": raw_digests,
        "fundamental_features_json_sha256": digest(feature_json),
        "fundamental_features_parquet_sha256": digest(feature_parquet),
        "research_summary_sha256": digest(summary_path),
    }
    manifest_path = artifacts / "manifest.json"
    dump_json(manifest_path, manifest)

    tracking_db = artifacts / "mlflow.db"
    mlflow.set_tracking_uri(f"sqlite:///{tracking_db}")
    mlflow.set_experiment("market-capital-wave-a-m2")
    with mlflow.start_run(run_name="sec-companyfacts-fundamental-features") as run:
        mlflow.log_param("source", "SEC Company Facts API")
        mlflow.log_param("issuer_count", len(features))
        mlflow.log_metric("mean_roa_proxy", float(df["roa_proxy"].mean()))
        mlflow.log_metric("mean_equity_to_assets", float(df["equity_to_assets"].mean()))
        mlflow.log_artifact(str(root / "config/sec_issuers.json"), artifact_path="inputs")
        mlflow.log_artifact(str(feature_json), artifact_path="outputs")
        mlflow.log_artifact(str(feature_parquet), artifact_path="outputs")
        mlflow.log_artifact(str(summary_path), artifact_path="outputs")
        mlflow.log_artifact(str(manifest_path), artifact_path="outputs")
        print(f"MLFLOW_RUN_ID={run.info.run_id}")

    print(df[["symbol", "fiscal_year", "period_end", "roa_proxy", "roe_proxy", "equity_to_assets"]].to_string(index=False))
    print(f"FEATURES={feature_parquet}")
    print(f"MANIFEST={manifest_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
