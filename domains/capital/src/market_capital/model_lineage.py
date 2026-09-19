from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
from typing import Any

import mlflow
import pandas as pd
import pandera.pandas as pa


class ModelLineageError(RuntimeError):
    pass


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def monitoring_schema() -> pa.DataFrameSchema:
    return pa.DataFrameSchema(
        {
            "factor": pa.Column(str),
            "proxy_instrument_id": pa.Column(str),
            "overlap_observation_count": pa.Column(int, pa.Check.greater_than(0), coerce=True),
            "overlap_to_union_ratio": pa.Column(
                float,
                [pa.Check.greater_than_or_equal_to(0), pa.Check.less_than_or_equal_to(1)],
                coerce=True,
            ),
            "realized_variance_reduction": pa.Column(float, nullable=True, coerce=True),
            "realized_mae": pa.Column(float, pa.Check.greater_than_or_equal_to(0), coerce=True),
            "beta_delta": pa.Column(float, coerce=True),
            "correlation_delta": pa.Column(float, coerce=True),
            "residual_variance_ratio": pa.Column(float, nullable=True, coerce=True),
            "base_wasserstein_distance": pa.Column(float, pa.Check.greater_than_or_equal_to(0), coerce=True),
            "proxy_wasserstein_distance": pa.Column(float, pa.Check.greater_than_or_equal_to(0), coerce=True),
        },
        strict=True,
        coerce=True,
    )


def monitoring_dataframe(evidence: dict[str, Any]) -> pd.DataFrame:
    monitoring = evidence.get("modelMonitoring")
    if not isinstance(monitoring, dict):
        raise ModelLineageError("modelMonitoring evidence is required")
    rows_raw = monitoring.get("rows")
    if not isinstance(rows_raw, list) or not rows_raw:
        raise ModelLineageError("modelMonitoring.rows must be a non-empty list")

    rows: list[dict[str, Any]] = []
    for i, row in enumerate(rows_raw):
        try:
            quality = row["dataQuality"]
            outcomes = row["outcomes"]["primary"]
            drift = row["drift"]
            parameter = drift["parameterDrift"]
            distribution = drift["distributionDrift"]
            rows.append({
                "factor": row["factor"],
                "proxy_instrument_id": row["proxyInstrumentId"],
                "overlap_observation_count": quality["overlapObservationCount"],
                "overlap_to_union_ratio": quality["overlapToUnionRatio"],
                "realized_variance_reduction": outcomes["realizedVarianceReductionVsUnhedged"],
                "realized_mae": outcomes["realizedMeanAbsoluteError"],
                "beta_delta": parameter["betaDelta"],
                "correlation_delta": parameter["correlationDelta"],
                "residual_variance_ratio": parameter["residualVarianceRatio"],
                "base_wasserstein_distance": distribution["baseReturnWassersteinDistance"],
                "proxy_wasserstein_distance": distribution["proxyReturnWassersteinDistance"],
            })
        except KeyError as exc:
            raise ModelLineageError(f"monitoring row {i} missing field: {exc}") from exc

    return monitoring_schema().validate(pd.DataFrame(rows))


def _duckdb_readback(*, duckdb_binary: Path, parquet_path: Path) -> dict[str, Any]:
    if not duckdb_binary.is_file():
        raise ModelLineageError(f"DuckDB binary unavailable: {duckdb_binary}")
    sql = (
        "SELECT count(*) AS row_count, "
        "min(overlap_observation_count) AS min_overlap, "
        "max(overlap_observation_count) AS max_overlap "
        f"FROM read_parquet('{parquet_path.as_posix()}');"
    )
    proc = subprocess.run(
        [str(duckdb_binary), "-json", "-c", sql],
        capture_output=True,
        text=True,
        check=False,
        timeout=15,
    )
    if proc.returncode != 0:
        raise ModelLineageError(f"DuckDB readback failed: {proc.stderr.strip()}")
    try:
        payload = json.loads(proc.stdout)
    except json.JSONDecodeError as exc:
        raise ModelLineageError("DuckDB readback returned invalid JSON") from exc
    if not isinstance(payload, list) or len(payload) != 1:
        raise ModelLineageError("DuckDB readback returned unexpected shape")
    return payload[0]


def persist_monitoring_evidence(
    *,
    evidence_path: Path,
    output_dir: Path,
    duckdb_binary: Path,
) -> dict[str, Any]:
    """Materialize monitoring evidence through Pandera/Parquet/DuckDB/MLflow."""

    evidence = json.loads(evidence_path.read_text())
    if evidence.get("subject") != "dependence-model-monitoring-r1":
        raise ModelLineageError("unexpected monitoring evidence subject")

    df = monitoring_dataframe(evidence)
    output_dir.mkdir(parents=True, exist_ok=True)

    parquet_path = output_dir / "dependence_model_monitoring.parquet"
    df.to_parquet(parquet_path, index=False)

    readback = _duckdb_readback(
        duckdb_binary=duckdb_binary,
        parquet_path=parquet_path,
    )
    if int(readback["row_count"]) != len(df):
        raise ModelLineageError("DuckDB row-count readback mismatch")

    manifest = {
        "schemaVersion": 1,
        "kind": "ordivon.market-capital.model-monitoring-lineage",
        "componentId": "model-monitoring-lineage",
        "sourceEvidenceSha256": _sha256(evidence_path),
        "parquetSha256": _sha256(parquet_path),
        "rowCount": len(df),
        "duckdbReadback": readback,
    }
    manifest_path = output_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")

    tracking_db = output_dir / "mlflow.db"
    mlflow.set_tracking_uri(f"sqlite:///{tracking_db}")
    mlflow.set_experiment("market-capital-model-monitoring")
    with mlflow.start_run(run_name="dependence-model-monitoring-r1") as run:
        mlflow.log_param("source_authority", evidence.get("sourceAuthority"))
        mlflow.log_param("base_instrument_id", evidence.get("baseInstrumentId"))
        mlflow.log_param("holdout_return_count", evidence.get("holdoutReturnCount"))
        mlflow.log_param("validated_component_id", "portfolio-dependence-analysis")
        mlflow.log_metric("monitoring_row_count", len(df))
        mlflow.log_metric(
            "minimum_overlap_observation_count",
            float(df["overlap_observation_count"].min()),
        )
        mlflow.log_artifact(str(evidence_path), artifact_path="inputs")
        mlflow.log_artifact(str(parquet_path), artifact_path="outputs")
        mlflow.log_artifact(str(manifest_path), artifact_path="outputs")
        run_id = run.info.run_id

    result = {
        **manifest,
        "mlflowRunId": run_id,
        "trackingBackend": "MLFLOW_SQLITE",
        "parquetPath": str(parquet_path),
        "manifestPath": str(manifest_path),
    }
    result_path = output_dir / "lineage_result.json"
    result_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    return result
