from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import jsonschema
import mlflow

from ordivon_capital.market.portfolio import build_research_gated_validation_portfolio


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
    reference_path = root / "artifacts/wave-a-m1/reference_entities.json"
    research_path = root / "artifacts/wave-a-m2/fundamental_features.json"
    artifacts = root / "artifacts/wave-a-m4"

    for required in [ips_path, reference_path, research_path]:
        if not required.exists():
            raise FileNotFoundError(f"Required upstream Wave A artifact is missing: {required}")

    ips = load_json(ips_path)
    reference = load_json(reference_path)
    research = load_json(research_path)

    portfolio = build_research_gated_validation_portfolio(ips, reference, research)
    portfolio["inputs"]["reference_artifact_sha256"] = digest(reference_path)
    portfolio["inputs"]["research_artifact_sha256"] = digest(research_path)

    portfolio_path = artifacts / "target_portfolio.json"
    dump_json(portfolio_path, portfolio)
    jsonschema.validate(portfolio, load_json(root / "schema/target_portfolio.schema.json"))

    manifest = {
        "ips_sha256": digest(ips_path),
        "reference_artifact_sha256": digest(reference_path),
        "research_artifact_sha256": digest(research_path),
        "target_portfolio_sha256": digest(portfolio_path),
    }
    manifest_path = artifacts / "manifest.json"
    dump_json(manifest_path, manifest)

    tracking_db = artifacts / "mlflow.db"
    mlflow.set_tracking_uri(f"sqlite:///{tracking_db}")
    mlflow.set_experiment("market-capital-wave-a-m4")
    with mlflow.start_run(run_name="research-gated-target-portfolio") as run:
        mlflow.log_param("method", portfolio["method"])
        mlflow.log_param("research_source", research.get("source"))
        mlflow.log_param("position_count", len(portfolio["positions"]))
        mlflow.log_metric("gross_exposure", portfolio["gross_exposure"])
        mlflow.log_artifact(str(ips_path), artifact_path="inputs")
        mlflow.log_artifact(str(reference_path), artifact_path="inputs")
        mlflow.log_artifact(str(research_path), artifact_path="inputs")
        mlflow.log_artifact(str(portfolio_path), artifact_path="outputs")
        mlflow.log_artifact(str(manifest_path), artifact_path="outputs")
        print(f"MLFLOW_RUN_ID={run.info.run_id}")

    print(json.dumps(portfolio, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
