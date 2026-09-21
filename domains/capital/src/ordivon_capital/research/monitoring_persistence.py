from __future__ import annotations

import hashlib
import json
import math
import subprocess
from pathlib import Path
from typing import Any

import pyarrow as pa
import pyarrow.parquet as pq


class MonitoringPersistenceError(RuntimeError):
    pass


MONITORING_ARROW_SCHEMA = pa.schema(
    [
        pa.field("factor", pa.string(), nullable=False),
        pa.field("proxy_instrument_id", pa.string(), nullable=False),
        pa.field("overlap_observation_count", pa.int64(), nullable=False),
        pa.field("overlap_to_union_ratio", pa.float64(), nullable=False),
        pa.field("realized_variance_reduction", pa.float64(), nullable=True),
        pa.field("realized_mae", pa.float64(), nullable=False),
        pa.field("beta_delta", pa.float64(), nullable=False),
        pa.field("correlation_delta", pa.float64(), nullable=False),
        pa.field("residual_variance_ratio", pa.float64(), nullable=True),
        pa.field("base_wasserstein_distance", pa.float64(), nullable=False),
        pa.field("proxy_wasserstein_distance", pa.float64(), nullable=False),
    ]
)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _text(value: Any, *, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise MonitoringPersistenceError(f"{field} must be a non-empty string")
    return value


def _integer(value: Any, *, field: str, minimum: int | None = None) -> int:
    if isinstance(value, bool):
        raise MonitoringPersistenceError(f"{field} must be an integer")
    try:
        out = int(value)
    except (TypeError, ValueError) as exc:
        raise MonitoringPersistenceError(f"{field} must be an integer") from exc
    if str(value).strip() not in {str(out), f"{out}.0"} and not isinstance(value, int):
        raise MonitoringPersistenceError(f"{field} must be integral")
    if minimum is not None and out < minimum:
        raise MonitoringPersistenceError(f"{field} must be >= {minimum}")
    return out


def _number(
    value: Any,
    *,
    field: str,
    minimum: float | None = None,
    maximum: float | None = None,
    nullable: bool = False,
) -> float | None:
    if value is None and nullable:
        return None
    try:
        out = float(value)
    except (TypeError, ValueError) as exc:
        raise MonitoringPersistenceError(f"{field} must be numeric") from exc
    if not math.isfinite(out):
        raise MonitoringPersistenceError(f"{field} must be finite")
    if minimum is not None and out < minimum:
        raise MonitoringPersistenceError(f"{field} must be >= {minimum}")
    if maximum is not None and out > maximum:
        raise MonitoringPersistenceError(f"{field} must be <= {maximum}")
    return out


def monitoring_rows(evidence: dict[str, Any]) -> list[dict[str, Any]]:
    monitoring = evidence.get("modelMonitoring")
    if not isinstance(monitoring, dict):
        raise MonitoringPersistenceError("modelMonitoring evidence is required")
    rows_raw = monitoring.get("rows")
    if not isinstance(rows_raw, list) or not rows_raw:
        raise MonitoringPersistenceError("modelMonitoring.rows must be a non-empty list")

    rows: list[dict[str, Any]] = []
    for i, row in enumerate(rows_raw):
        if not isinstance(row, dict):
            raise MonitoringPersistenceError(f"monitoring row {i} must be an object")
        try:
            quality = row["dataQuality"]
            outcomes = row["outcomes"]["primary"]
            drift = row["drift"]
            parameter = drift["parameterDrift"]
            distribution = drift["distributionDrift"]
            flattened = {
                "factor": _text(row["factor"], field=f"rows[{i}].factor"),
                "proxy_instrument_id": _text(
                    row["proxyInstrumentId"],
                    field=f"rows[{i}].proxyInstrumentId",
                ),
                "overlap_observation_count": _integer(
                    quality["overlapObservationCount"],
                    field=f"rows[{i}].overlapObservationCount",
                    minimum=1,
                ),
                "overlap_to_union_ratio": _number(
                    quality["overlapToUnionRatio"],
                    field=f"rows[{i}].overlapToUnionRatio",
                    minimum=0,
                    maximum=1,
                ),
                "realized_variance_reduction": _number(
                    outcomes["realizedVarianceReductionVsUnhedged"],
                    field=f"rows[{i}].realizedVarianceReductionVsUnhedged",
                    nullable=True,
                ),
                "realized_mae": _number(
                    outcomes["realizedMeanAbsoluteError"],
                    field=f"rows[{i}].realizedMeanAbsoluteError",
                    minimum=0,
                ),
                "beta_delta": _number(
                    parameter["betaDelta"],
                    field=f"rows[{i}].betaDelta",
                ),
                "correlation_delta": _number(
                    parameter["correlationDelta"],
                    field=f"rows[{i}].correlationDelta",
                ),
                "residual_variance_ratio": _number(
                    parameter["residualVarianceRatio"],
                    field=f"rows[{i}].residualVarianceRatio",
                    nullable=True,
                ),
                "base_wasserstein_distance": _number(
                    distribution["baseReturnWassersteinDistance"],
                    field=f"rows[{i}].baseReturnWassersteinDistance",
                    minimum=0,
                ),
                "proxy_wasserstein_distance": _number(
                    distribution["proxyReturnWassersteinDistance"],
                    field=f"rows[{i}].proxyReturnWassersteinDistance",
                    minimum=0,
                ),
            }
        except (KeyError, TypeError) as exc:
            raise MonitoringPersistenceError(
                f"monitoring row {i} missing/invalid nested field: {exc}"
            ) from exc
        rows.append(flattened)
    return rows


def monitoring_table(evidence: dict[str, Any]) -> pa.Table:
    rows = monitoring_rows(evidence)
    try:
        return pa.Table.from_pylist(rows, schema=MONITORING_ARROW_SCHEMA)
    except (pa.ArrowInvalid, pa.ArrowTypeError) as exc:
        raise MonitoringPersistenceError("monitoring Arrow schema validation failed") from exc




def _duckdb_version(*, duckdb_binary: Path) -> str:
    proc = subprocess.run(
        [str(duckdb_binary), "--version"],
        capture_output=True,
        text=True,
        check=False,
        timeout=15,
    )
    if proc.returncode != 0:
        raise MonitoringPersistenceError(
            f"DuckDB version probe failed: {proc.stderr.strip()}"
        )
    first = proc.stdout.strip().split()
    if not first or not first[0].startswith("v"):
        raise MonitoringPersistenceError("DuckDB version probe returned unexpected output")
    return first[0].removeprefix("v")


def _duckdb_readback(*, duckdb_binary: Path, parquet_path: Path) -> dict[str, Any]:
    if not duckdb_binary.is_file():
        raise MonitoringPersistenceError(f"DuckDB binary unavailable: {duckdb_binary}")
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
        raise MonitoringPersistenceError(
            f"DuckDB readback failed: {proc.stderr.strip()}"
        )
    try:
        payload = json.loads(proc.stdout)
    except json.JSONDecodeError as exc:
        raise MonitoringPersistenceError(
            "DuckDB readback returned invalid JSON"
        ) from exc
    if not isinstance(payload, list) or len(payload) != 1:
        raise MonitoringPersistenceError(
            "DuckDB readback returned unexpected shape"
        )
    return payload[0]


def persist_monitoring_evidence(
    *,
    evidence_path: Path,
    output_dir: Path,
    duckdb_binary: Path,
) -> dict[str, Any]:
    """Persist monitoring evidence with bounded validation and independent readback."""

    evidence = json.loads(evidence_path.read_text())
    if evidence.get("subject") != "dependence-model-monitoring-r1":
        raise MonitoringPersistenceError(
            "unexpected monitoring evidence subject"
        )

    table = monitoring_table(evidence)
    output_dir.mkdir(parents=True, exist_ok=True)

    parquet_path = output_dir / "dependence_model_monitoring.parquet"
    pq.write_table(table, parquet_path)

    readback = _duckdb_readback(
        duckdb_binary=duckdb_binary,
        parquet_path=parquet_path,
    )
    if int(readback["row_count"]) != table.num_rows:
        raise MonitoringPersistenceError(
            "DuckDB row-count readback mismatch"
        )

    manifest = {
        "schemaVersion": 2,
        "kind": "ordivon.capital.research.model-monitoring-persistence",
        "componentId": "model-monitoring-persistence",
        "sourceEvidenceSha256": _sha256(evidence_path),
        "parquetSha256": _sha256(parquet_path),
        "rowCount": table.num_rows,
        "schema": [
            {
                "name": field.name,
                "type": str(field.type),
                "nullable": field.nullable,
            }
            for field in MONITORING_ARROW_SCHEMA
        ],
        "duckdbReadback": readback,
        "validationImplementation": "LOCAL_BOUNDED_ROW_VALIDATION",
        "storageImplementation": f"PyArrow {pa.__version__} / Parquet",
        "independentReadbackImplementation": f"DuckDB {_duckdb_version(duckdb_binary=duckdb_binary)}",
        "experimentTrackingClaimed": False,
        "lineageAuthorityClaimed": False,
    }
    manifest_path = output_dir / "manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n"
    )

    result = {
        **manifest,
        "parquetPath": str(parquet_path),
        "manifestPath": str(manifest_path),
    }
    result_path = output_dir / "persistence_result.json"
    result_path.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n"
    )
    return result
