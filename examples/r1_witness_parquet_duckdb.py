from __future__ import annotations

from pathlib import Path
import json
import subprocess
import pyarrow as pa
import pyarrow.parquet as pq

from market_capital.semantic import WitnessRecord, validate_same_cut

D = "sha256:" + "c" * 64


def make(seq: int, venue: str, payload: dict, ns: int) -> WitnessRecord:
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return WitnessRecord.build(
        venue=venue,
        connection_id=f"{venue.lower()}-conn-1",
        raw_bytes=raw,
        recv_monotonic_ns=ns,
        recv_wall_time=f"2026-09-11T07:00:0{seq}Z",
        venue_sequence_if_any=str(payload.get("seq")) if payload.get("seq") is not None else None,
        append_sequence=seq,
        recorder_instance="witness-recorder:demo-1",
        recorder_session="session:demo-1",
        clock_domain="monotonic:demo-1",
        config_digest=D,
        code_digest=D,
    )


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    out = root / ".artifacts"
    out.mkdir(exist_ok=True)
    records = validate_same_cut([
        make(1, "OKX", {"seq": 101, "bid": "100", "ask": "101"}, 1_000),
        make(2, "BINANCE", {"seq": 501, "bid": "99.9", "ask": "100.9"}, 1_010),
    ])
    table = pa.table({
        "venue": [r.venue for r in records],
        "connection_id": [r.connection_id for r in records],
        "recv_monotonic_ns": [r.recv_monotonic_ns for r in records],
        "append_sequence": [r.append_sequence for r in records],
        "raw_digest": [r.digest for r in records],
        "raw_bytes": [r.raw_bytes for r in records],
        "recorder_instance": [r.recorder_instance for r in records],
        "recorder_session": [r.recorder_session for r in records],
        "clock_domain": [r.clock_domain for r in records],
    })
    parquet = out / "witness-cut.parquet"
    pq.write_table(table, parquet)
    query = (
        "select venue, append_sequence, raw_digest "
        f"from read_parquet('{parquet.resolve().as_posix()}') order by append_sequence"
    )
    rows = json.loads(subprocess.check_output(["/usr/bin/duckdb", "-json", "-c", query], text=True))
    assert rows[0]["append_sequence"] == 1 and rows[1]["append_sequence"] == 2
    assert rows[0]["raw_digest"] == records[0].digest and rows[1]["raw_digest"] == records[1].digest
    print(json.dumps({
        "standing": "PASS_AUTHORITY_FREE_R1_LOCAL",
        "records": len(rows),
        "duckdbInterface": "system-cli",
        "parquet": str(parquet),
        "sameCutDerivedBeforeExternalStorage": True,
        "externalFinancialWriteAttempted": False,
        "externalFinancialWriteAdmission": "NOT_ADMITTED"
    }, sort_keys=True))


if __name__ == "__main__":
    main()
