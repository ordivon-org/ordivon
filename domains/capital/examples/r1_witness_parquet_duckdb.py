from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq

DUCKDB = Path("/opt/ordivon/external/duckdb/1.5.5-1/duckdb")


def record(*, venue: str, append_sequence: int, payload: dict[str, object]) -> dict[str, object]:
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return {
        "venue": venue,
        "append_sequence": append_sequence,
        "raw_digest": "sha256:" + hashlib.sha256(raw).hexdigest(),
        "raw_bytes": raw,
    }


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    out = root / ".artifacts"
    out.mkdir(exist_ok=True)

    records = [
        record(
            venue="OKX",
            append_sequence=1,
            payload={"seq": 101, "bid": "100", "ask": "101"},
        ),
        record(
            venue="BINANCE",
            append_sequence=2,
            payload={"seq": 501, "bid": "99.9", "ask": "100.9"},
        ),
    ]
    assert [row["append_sequence"] for row in records] == [1, 2]
    assert len({row["raw_digest"] for row in records}) == len(records)

    table = pa.table(
        {
            "venue": [row["venue"] for row in records],
            "append_sequence": [row["append_sequence"] for row in records],
            "raw_digest": [row["raw_digest"] for row in records],
            "raw_bytes": [row["raw_bytes"] for row in records],
        }
    )
    parquet = out / "r1-storage-witness.parquet"
    pq.write_table(table, parquet)

    if not DUCKDB.is_file():
        raise SystemExit(f"canonical DuckDB binary unavailable: {DUCKDB}")
    query = (
        "select venue, append_sequence, raw_digest, "
        "sha256(raw_bytes) as duckdb_sha256 "
        f"from read_parquet('{parquet.resolve().as_posix()}') "
        "order by append_sequence"
    )
    rows = json.loads(
        subprocess.check_output([str(DUCKDB), "-json", "-c", query], text=True)
    )
    assert [row["append_sequence"] for row in rows] == [1, 2]
    for expected, observed in zip(records, rows, strict=True):
        assert observed["venue"] == expected["venue"]
        assert observed["raw_digest"] == expected["raw_digest"]
        assert "sha256:" + observed["duckdb_sha256"] == expected["raw_digest"]

    print(
        json.dumps(
            {
                "standing": "PASS_PARQUET_DUCKDB_PRIMITIVE_READBACK",
                "records": len(rows),
                "parquetOwner": "PyArrow 25.0.1",
                "duckdbOwner": "DuckDB 1.5.5",
                "duckdbInterface": "isolated-binary",
                "digestAndOrderRoundTrip": True,
                "semanticWitnessAuthorityClaimed": False,
                "externalFinancialWriteAttempted": False,
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
