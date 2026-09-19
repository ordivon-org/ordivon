from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import jsonschema
import mlflow

from ordivon_capital.market.gleif_reference import collect_reference
from ordivon_capital.market.portfolio import build_equal_weight_validation_portfolio


def load_json(path: Path):
    return json.loads(path.read_text())


def dump_json(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, sort_keys=True) + "\n")


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    args = parser.parse_args()
    root = Path(args.root).resolve()

    ips_path = root / "config/ips.json"
    universe_path = root / "config/universe.json"
    artifacts = root / "artifacts/wave-a-m1"
    raw_dir = root / "data/raw/gleif"

    ips = load_json(ips_path)
    universe = load_json(universe_path)
    jsonschema.validate(ips, load_json(root / "schema/ips.schema.json"))

    raw, reference = collect_reference(universe)
    raw_dir.mkdir(parents=True, exist_ok=True)
    for symbol, payload in raw.items():
        dump_json(raw_dir / f"{symbol}.json", payload)

    reference_path = artifacts / "reference_entities.json"
    dump_json(reference_path, reference)
    jsonschema.validate(reference, load_json(root / "schema/reference_entities.schema.json"))

    portfolio = build_equal_weight_validation_portfolio(ips, reference)
    portfolio_path = artifacts / "target_portfolio.json"
    dump_json(portfolio_path, portfolio)
    jsonschema.validate(portfolio, load_json(root / "schema/target_portfolio.schema.json"))

    manifest = {
        "ips_sha256": digest(ips_path),
        "universe_sha256": digest(universe_path),
        "reference_entities_sha256": digest(reference_path),
        "target_portfolio_sha256": digest(portfolio_path),
    }
    manifest_path = artifacts / "manifest.json"
    dump_json(manifest_path, manifest)

    tracking_db = artifacts / "mlflow.db"
    mlflow.set_tracking_uri(f"sqlite:///{tracking_db}")
    mlflow.set_experiment("market-capital-wave-a-m1")
    with mlflow.start_run(run_name="cfa-ips-to-target-portfolio") as run:
        mlflow.log_param("construction_method", ips["construction_method"])
        mlflow.log_param("instrument_count", len(ips["allowed_instruments"]))
        mlflow.log_metric("gross_exposure", portfolio["gross_exposure"])
        mlflow.log_metric("cash_weight", portfolio["cash_weight"])
        mlflow.log_artifact(str(ips_path), artifact_path="inputs")
        mlflow.log_artifact(str(universe_path), artifact_path="inputs")
        mlflow.log_artifact(str(reference_path), artifact_path="outputs")
        mlflow.log_artifact(str(portfolio_path), artifact_path="outputs")
        mlflow.log_artifact(str(manifest_path), artifact_path="outputs")
        print(f"MLFLOW_RUN_ID={run.info.run_id}")

    print(f"REFERENCE={reference_path}")
    print(f"TARGET_PORTFOLIO={portfolio_path}")
    print(f"MANIFEST={manifest_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
