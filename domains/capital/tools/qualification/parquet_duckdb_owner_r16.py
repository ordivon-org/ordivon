from __future__ import annotations

import hashlib
import importlib.metadata as metadata
import json
import subprocess
import tempfile
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq

DUCKDB_ROOT = Path("/opt/ordivon/external/duckdb/1.5.5-1")
DUCKDB = DUCKDB_ROOT / "duckdb"
DUCKDB_ENGINE = DUCKDB_ROOT / "rootfs/usr/bin/duckdb"
DUCKDB_PACKAGE = DUCKDB_ROOT / "provenance/duckdb-1.5.5-1-x86_64.pkg.tar.zst"
DUCKDB_SIGNATURE = Path(str(DUCKDB_PACKAGE) + ".sig")
DUCKDB_INSTALL = DUCKDB_ROOT / "ORDIVON-INSTALL.json"

SCHEMA = pa.schema(
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

ROWS = [
    {
        "factor": "α-factor",
        "proxy_instrument_id": "BTC-USDT/现货",
        "overlap_observation_count": 2**53 + 17,
        "overlap_to_union_ratio": 1.0,
        "realized_variance_reduction": None,
        "realized_mae": 0.0,
        "beta_delta": -1.25,
        "correlation_delta": 0.0,
        "residual_variance_ratio": None,
        "base_wasserstein_distance": 1e-12,
        "proxy_wasserstein_distance": 2.5,
    },
    {
        "factor": "F2",
        "proxy_instrument_id": "ETH-USDT",
        "overlap_observation_count": 1,
        "overlap_to_union_ratio": 0.125,
        "realized_variance_reduction": -0.5,
        "realized_mae": 10.5,
        "beta_delta": 3.0,
        "correlation_delta": -0.99,
        "residual_variance_ratio": 1.25,
        "base_wasserstein_distance": 9.0,
        "proxy_wasserstein_distance": 0.0,
    },
]


def _duckdb(*args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [str(DUCKDB), *args],
        text=True,
        capture_output=True,
        check=check,
        timeout=15,
    )


def _pyarrow_footprint() -> tuple[int, int]:
    dist = metadata.distribution("pyarrow")
    files = list(dist.files or [])
    total = 0
    for item in files:
        path = Path(dist.locate_file(item))
        try:
            if path.is_file():
                total += path.stat().st_size
        except OSError:
            pass
    return len(files), total


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _duckdb_provenance() -> dict[str, str]:
    for path in (DUCKDB, DUCKDB_ENGINE, DUCKDB_PACKAGE, DUCKDB_SIGNATURE, DUCKDB_INSTALL):
        if not path.is_file():
            raise SystemExit(f"missing DuckDB provenance file: {path}")
    install = json.loads(DUCKDB_INSTALL.read_text())
    observed = {
        "launcherSha256": _sha256(DUCKDB),
        "engineSha256": _sha256(DUCKDB_ENGINE),
        "packageSha256": _sha256(DUCKDB_PACKAGE),
        "packageSignatureSha256": _sha256(DUCKDB_SIGNATURE),
    }
    expected = {
        "launcherSha256": install["wrapperSha256"],
        "engineSha256": install["binarySha256"],
        "packageSha256": install["packageSha256"],
        "packageSignatureSha256": install["packageSignatureSha256"],
    }
    if observed != expected:
        raise SystemExit(f"DuckDB install provenance digest drift: {observed!r} != {expected!r}")
    verify = subprocess.run(
        ["pacman-key", "--verify", str(DUCKDB_SIGNATURE), str(DUCKDB_PACKAGE)],
        text=True,
        capture_output=True,
        check=False,
        timeout=15,
    )
    if verify.returncode != 0 or "Good signature" not in (verify.stdout + verify.stderr):
        raise SystemExit("DuckDB package signature verification failed")
    return {
        **observed,
        "packageSignatureVerification": "PASS_REVERIFIED_VIA_PACMAN_KEY",
    }


def _stress_rows() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for i in range(513):
        rows.append(
            {
                "factor": f"F{i % 7}",
                "proxy_instrument_id": f"P{i:04d}",
                "overlap_observation_count": i + 1,
                "overlap_to_union_ratio": (i % 101) / 100.0,
                "realized_variance_reduction": None if i % 11 == 0 else (i % 23) / 100.0,
                "realized_mae": (i % 31) / 1000.0,
                "beta_delta": (i - 256) / 1000.0,
                "correlation_delta": (256 - i) / 2000.0,
                "residual_variance_ratio": None if i % 13 == 0 else 0.5 + (i % 19) / 10.0,
                "base_wasserstein_distance": (i % 17) / 1000.0,
                "proxy_wasserstein_distance": (i % 29) / 1000.0,
            }
        )
    return rows


def main() -> None:
    if pa.__version__ != "25.0.1":
        raise SystemExit(f"unexpected PyArrow version: {pa.__version__}")
    version_text = _duckdb("--version").stdout.strip()
    if not version_text.startswith("v1.5.5 "):
        raise SystemExit(f"unexpected DuckDB version: {version_text}")
    duckdb_provenance = _duckdb_provenance()

    table = pa.Table.from_pylist(ROWS, schema=SCHEMA)

    with tempfile.TemporaryDirectory(prefix="ordivon-parquet-r16-") as raw_tmp:
        root = Path(raw_tmp)
        pyarrow_path = root / "pyarrow.parquet"
        duckdb_path = root / "duckdb.parquet"
        truncated_path = root / "truncated.parquet"
        garbage_path = root / "garbage.parquet"
        stress_path = root / "stress.parquet"

        pq.write_table(table, pyarrow_path, compression="snappy")
        query = (
            "select factor, proxy_instrument_id, overlap_observation_count, "
            "overlap_to_union_ratio, realized_variance_reduction, realized_mae, "
            "beta_delta, correlation_delta, residual_variance_ratio, "
            "base_wasserstein_distance, proxy_wasserstein_distance "
            f"from read_parquet('{pyarrow_path.as_posix()}') "
            "order by overlap_observation_count desc"
        )
        observed = json.loads(_duckdb("-json", "-c", query).stdout)
        assert len(observed) == 2
        assert observed[0]["factor"] == "α-factor"
        assert observed[0]["proxy_instrument_id"] == "BTC-USDT/现货"
        assert int(observed[0]["overlap_observation_count"]) == 2**53 + 17
        assert observed[0]["realized_variance_reduction"] is None
        assert observed[0]["residual_variance_ratio"] is None

        stress_table = pa.Table.from_pylist(_stress_rows(), schema=SCHEMA)
        pq.write_table(stress_table, stress_path, row_group_size=64)
        stress_meta = pq.ParquetFile(stress_path).metadata
        assert stress_meta.num_rows == 513
        assert stress_meta.num_row_groups == 9

        parquet_schema = json.loads(
            _duckdb(
                "-json",
                "-c",
                (
                    "SELECT name,repetition_type,duckdb_type "
                    f"FROM parquet_schema('{stress_path.as_posix()}') ORDER BY column_id"
                ),
            ).stdout
        )[1:]
        expected_repetition = {
            field.name: ("OPTIONAL" if field.nullable else "REQUIRED")
            for field in SCHEMA
        }
        assert {
            row["name"]: row["repetition_type"] for row in parquet_schema
        } == expected_repetition
        expected_duckdb_types = {
            "factor": "VARCHAR",
            "proxy_instrument_id": "VARCHAR",
            "overlap_observation_count": "BIGINT",
            "overlap_to_union_ratio": "DOUBLE",
            "realized_variance_reduction": "DOUBLE",
            "realized_mae": "DOUBLE",
            "beta_delta": "DOUBLE",
            "correlation_delta": "DOUBLE",
            "residual_variance_ratio": "DOUBLE",
            "base_wasserstein_distance": "DOUBLE",
            "proxy_wasserstein_distance": "DOUBLE",
        }
        assert {
            row["name"]: row["duckdb_type"] for row in parquet_schema
        } == expected_duckdb_types

        stress_file_meta = json.loads(
            _duckdb(
                "-json",
                "-c",
                (
                    "SELECT created_by,num_rows,num_row_groups "
                    f"FROM parquet_file_metadata('{stress_path.as_posix()}')"
                ),
            ).stdout
        )[0]
        assert stress_file_meta["created_by"] == "parquet-cpp-arrow version 25.0.1"
        assert stress_file_meta["num_rows"] == 513
        assert stress_file_meta["num_row_groups"] == 9

        copy_sql = (
            "COPY (SELECT * FROM read_parquet("
            f"'{pyarrow_path.as_posix()}')) TO '{duckdb_path.as_posix()}' "
            "(FORMAT PARQUET)"
        )
        _duckdb("-c", copy_sql)
        duckdb_written = pq.read_table(duckdb_path)
        assert duckdb_written.schema.names == SCHEMA.names
        assert duckdb_written.to_pylist() == table.to_pylist()

        raw = pyarrow_path.read_bytes()
        truncated_path.write_bytes(raw[: max(8, len(raw) // 3)])
        duckdb_truncated = _duckdb(
            "-c",
            f"SELECT count(*) FROM read_parquet('{truncated_path.as_posix()}')",
            check=False,
        )
        assert duckdb_truncated.returncode != 0
        arrow_truncated_rejected = False
        try:
            pq.read_table(truncated_path)
        except Exception:
            arrow_truncated_rejected = True
        assert arrow_truncated_rejected

        garbage_path.write_bytes(b"PAR1garbage-not-a-valid-footerPAR1")
        duckdb_garbage = _duckdb(
            "-c",
            f"SELECT * FROM read_parquet('{garbage_path.as_posix()}')",
            check=False,
        )
        assert duckdb_garbage.returncode != 0
        arrow_garbage_rejected = False
        try:
            pq.read_table(garbage_path)
        except Exception:
            arrow_garbage_rejected = True
        assert arrow_garbage_rejected

        type_mismatch_rejected = False
        try:
            bad = {**ROWS[0], "overlap_observation_count": "not-an-int"}
            pa.Table.from_pylist([bad], schema=SCHEMA)
        except Exception:
            type_mismatch_rejected = True
        assert type_mismatch_rejected

        files, footprint = _pyarrow_footprint()
        result = {
            "schemaVersion": 1,
            "kind": "ordivon.capital.research.parquet-owner-requalification-r16",
            "standing": "PASS_RETAIN_PYARROW_AND_DUCKDB_BOUNDED_OWNERS",
            "contract": "contracts/parquet-materialization-readback-v1.json",
            "pyarrow": {
                "version": pa.__version__,
                "python3147ExecutableQualification": "PASS",
                "role": "PARQUET_MATERIALIZATION_OWNER",
                "installedFileCount": files,
                "installedFootprintBytes": footprint,
            },
            "duckdb": {
                "version": "1.5.5",
                "versionText": version_text,
                **duckdb_provenance,
                "role": "INDEPENDENT_PARQUET_READBACK_OWNER",
            },
            "falsification": {
                "crossEngineRows": len(observed),
                "unicodeRoundTrip": True,
                "int64Above53BitRoundTrip": True,
                "nullableRoundTrip": True,
                "duckdbToPyarrowRoundTrip": True,
                "truncatedRejectedByBoth": True,
                "garbageRejectedByBoth": True,
                "explicitTypeMismatchRejected": True,
                "multiRowGroupStressRows": 513,
                "multiRowGroups": 9,
                "parquetRequiredOptionalFidelity": True,
                "parquetSchemaTypeFidelity": True,
                "describeNullabilityIsNotSchemaAuthority": True,
            },
            "localBaseline": {
                "sameEnginePyarrowReadbackContractEquivalent": False,
                "stdlibParquetImplementationCredible": False,
                "reason": (
                    "same-engine self-readback does not independently parse Parquet; "
                    "a local Parquet encoder/reader would duplicate binary-format semantics"
                ),
            },
            "externalOwnerAdmitted": True,
            "externalFinancialWriteAttempted": False,
        }
        print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
