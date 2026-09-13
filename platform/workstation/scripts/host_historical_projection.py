#!/usr/bin/env python3
from __future__ import annotations

import argparse
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import shutil
import sqlite3
import subprocess
import tempfile
from typing import Any, Iterable, Sequence

import psycopg
from psycopg import sql


@dataclass(frozen=True, slots=True)
class TableSpec:
    name: str
    columns: tuple[str, ...]
    order_by: tuple[str, ...]


# Compatibility contract copied from the final Host v1 PostgreSQL archival projector.
# These 15 tables are the historical source tables. migration_receipts is projector metadata.
TABLES: tuple[TableSpec, ...] = (
    TableSpec("host_metadata", ("key", "value"), ("key",)),
    TableSpec("object_refs", ("digest", "kind", "byte_length", "first_seen_at_ms", "validation_timing"), ("digest",)),
    TableSpec("object_validation", ("digest", "device", "inode", "byte_length", "modified_at_ns", "changed_at_ns", "mode"), ("digest",)),
    TableSpec("legacy_object_refs", ("digest",), ("digest",)),
    TableSpec("streams", ("stream_id", "stream_kind", "revision", "created_at_ms", "updated_at_ms"), ("stream_id",)),
    TableSpec("events", ("sequence", "event_id", "stream_id", "stream_kind", "stream_revision", "event_kind", "payload_digest", "caused_by_event_id", "recorded_at_ms"), ("sequence",)),
    TableSpec("event_object_refs", ("event_id", "digest", "role"), ("event_id", "digest")),
    TableSpec("task_projection", ("task_id", "goal_id", "state", "active_node_id", "ready_frontier_json", "revision", "updated_at_ms"), ("task_id",)),
    TableSpec("task_extension_state", ("task_id", "namespace", "state_digest", "event_id", "revision", "legacy"), ("task_id", "namespace")),
    TableSpec("task_head_validation", ("task_id", "revision", "event_id", "payload_digest", "projection_digest", "descriptor_data_is_object", "descriptor_digest", "descriptor_object_digest"), ("task_id",)),
    TableSpec("leases", ("task_id", "owner_id", "revision", "expires_at_ms"), ("task_id",)),
    TableSpec("board_messages", ("sequence", "client_message_id", "author_label", "message_kind", "topic", "message_digest", "reply_to_client_message_id", "recorded_at_ms"), ("sequence",)),
    TableSpec("news_editions", ("edition_id", "edition_date", "timezone", "current_revision", "current_digest", "created_at_ms", "updated_at_ms"), ("edition_id",)),
    TableSpec("news_publications", ("sequence", "client_publish_id", "edition_id", "edition_date", "timezone", "expected_revision", "revision", "edition_digest", "recorded_at_ms"), ("sequence",)),
    TableSpec("schema_migrations", ("sequence", "from_version", "to_version", "name", "backup_path"), ("sequence",)),
)

INVARIANTS: dict[str, str] = {
    "event_stream_heads": """
        SELECT COUNT(*) FROM streams s
        LEFT JOIN LATERAL (
            SELECT MAX(e.stream_revision) AS revision FROM events e WHERE e.stream_id=s.stream_id
        ) h ON TRUE
        WHERE h.revision IS NULL OR h.revision <> s.revision
    """,
    "task_projection_heads": """
        SELECT COUNT(*) FROM task_projection p
        JOIN streams s ON s.stream_id=p.task_id
        WHERE p.revision <> s.revision OR s.stream_kind <> 'task'
    """,
    "event_payload_edges": """
        SELECT COUNT(*) FROM events e
        LEFT JOIN event_object_refs r
          ON r.event_id=e.event_id AND r.digest=e.payload_digest AND r.role='payload'
        WHERE r.event_id IS NULL
    """,
    "dangling_board_replies": """
        SELECT COUNT(*) FROM board_messages child
        LEFT JOIN board_messages parent
          ON parent.client_message_id=child.reply_to_client_message_id
        WHERE child.reply_to_client_message_id IS NOT NULL AND parent.client_message_id IS NULL
    """,
    "news_head_mismatch": """
        SELECT COUNT(*) FROM news_editions e
        LEFT JOIN news_publications p
          ON p.edition_id=e.edition_id AND p.revision=e.current_revision
        WHERE p.sequence IS NULL OR p.edition_digest <> e.current_digest
    """,
}


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def row_digest(rows: Iterable[Sequence[Any]]) -> tuple[int, str]:
    h = hashlib.sha256()
    count = 0
    for row in rows:
        encoded = json.dumps(list(row), ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        h.update(len(encoded).to_bytes(8, "big"))
        h.update(encoded)
        count += 1
    return count, h.hexdigest()


def qident(name: str) -> str:
    return '"' + name.replace('"', '""') + '"'


def qstr(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def select_sql(spec: TableSpec, prefix: str = "") -> str:
    cols = ", ".join(qident(c) for c in spec.columns)
    order = ", ".join(qident(c) for c in spec.order_by)
    table = f"{prefix}.{qident(spec.name)}" if prefix else qident(spec.name)
    return f"SELECT {cols} FROM {table} ORDER BY {order}"


def source_rows(source: Path, spec: TableSpec) -> list[tuple[Any, ...]]:
    conn = sqlite3.connect(f"file:{source}?mode=ro&immutable=1", uri=True)
    try:
        return [tuple(row) for row in conn.execute(select_sql(spec))]
    finally:
        conn.close()


def source_digests(source: Path) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for spec in TABLES:
        count, digest = row_digest(source_rows(source, spec))
        result[spec.name] = {"rows": count, "sha256": digest}
    return result


def pg_digests(host: str, port: int, database: str, user: str, schema: str) -> tuple[dict[str, dict[str, Any]], dict[str, int], str]:
    tables: dict[str, dict[str, Any]] = {}
    invariants: dict[str, int] = {}
    with psycopg.connect(host=host, port=port, dbname=database, user=user, autocommit=True) as conn:
        server_version = str(conn.execute("SHOW server_version").fetchone()[0])
        for spec in TABLES:
            cols = sql.SQL(", ").join(sql.Identifier(c) for c in spec.columns)
            order = sql.SQL(", ").join(sql.Identifier(c) for c in spec.order_by)
            query = sql.SQL("SELECT {} FROM {}.{} ORDER BY {}").format(cols, sql.Identifier(schema), sql.Identifier(spec.name), order)
            rows = conn.execute(query).fetchall()
            count, digest = row_digest(rows)
            tables[spec.name] = {"rows": count, "sha256": digest}
        conn.execute(sql.SQL("SET search_path TO {}, public").format(sql.Identifier(schema)))
        for name, query in INVARIANTS.items():
            row = conn.execute(query).fetchone()
            invariants[name] = int(row[0]) if row else 0
    return tables, invariants, server_version


def run_duckdb(database: Path | None, sql_text: str, *, json_output: bool = False, timeout: int = 120) -> str:
    cmd = ["/usr/bin/duckdb"]
    if database is not None:
        cmd.append(str(database))
    if json_output:
        cmd.append("-json")
    cmd += ["-c", sql_text]
    proc = subprocess.run(cmd, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False, timeout=timeout)
    if proc.returncode:
        raise RuntimeError(f"duckdb failed ({proc.returncode}): {proc.stderr[-5000:]}\nSQL={sql_text[:2000]}")
    return proc.stdout


def duckdb_version() -> str:
    proc = subprocess.run(["/usr/bin/duckdb", "--version"], text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
    return proc.stdout.strip()


def export_parquet(source: Path, parquet_dir: Path) -> dict[str, dict[str, Any]]:
    parquet_dir.mkdir(parents=True, exist_ok=True)
    prelude = "SET autoinstall_known_extensions=false; LOAD sqlite_scanner; " + f"ATTACH {qstr(str(source))} AS src (TYPE SQLITE); "
    result: dict[str, dict[str, Any]] = {}
    for spec in TABLES:
        target = parquet_dir / f"{spec.name}.parquet"
        query = select_sql(spec, "src")
        run_duckdb(None, prelude + f"COPY ({query}) TO {qstr(str(target))} (FORMAT PARQUET, COMPRESSION ZSTD);", timeout=120)
        result[spec.name] = {"path": target.name, "bytes": target.stat().st_size, "sha256": sha256_file(target)}
    return result


def create_catalog(catalog: Path, parquet_dir: Path, source_sha256: str) -> None:
    if catalog.exists():
        catalog.unlink()
    statements = [
        "CREATE TABLE projection_metadata(key VARCHAR PRIMARY KEY, value VARCHAR NOT NULL)",
        f"INSERT INTO projection_metadata VALUES ('truth_role','derived-disposable-historical-read-model'),('source_sha256',{qstr(source_sha256)}),('format','Apache Parquet + DuckDB views')",
    ]
    for spec in TABLES:
        p = parquet_dir / f"{spec.name}.parquet"
        statements.append(f"CREATE VIEW {qident(spec.name)} AS SELECT * FROM read_parquet({qstr(str(p))})")
    run_duckdb(catalog, "; ".join(statements) + ";", timeout=120)


def duckdb_table_digest(catalog: Path, spec: TableSpec, scratch: Path) -> tuple[int, str]:
    out = scratch / f"{spec.name}.ndjson"
    if out.exists():
        out.unlink()
    run_duckdb(catalog, f"COPY ({select_sql(spec)}) TO {qstr(str(out))} (FORMAT JSON, ARRAY false);", timeout=120)
    rows: list[tuple[Any, ...]] = []
    with out.open("r", encoding="utf-8") as fh:
        for line in fh:
            if not line.strip():
                continue
            obj = json.loads(line)
            rows.append(tuple(obj[c] for c in spec.columns))
    return row_digest(rows)


def validate_catalog(source: Path, catalog: Path, scratch: Path) -> tuple[dict[str, dict[str, Any]], dict[str, int]]:
    prelude = "SET autoinstall_known_extensions=false; LOAD sqlite_scanner; " + f"ATTACH {qstr(str(source))} AS src (TYPE SQLITE); "
    tables: dict[str, dict[str, Any]] = {}
    for spec in TABLES:
        cols = ", ".join(qident(c) for c in spec.columns)
        left = f"SELECT {cols} FROM src.{qident(spec.name)}"
        right = f"SELECT {cols} FROM main.{qident(spec.name)}"
        check_sql = prelude + (
            "SELECT "
            f"(SELECT COUNT(*) FROM ({left} EXCEPT ALL {right})) AS source_minus_projection, "
            f"(SELECT COUNT(*) FROM ({right} EXCEPT ALL {left})) AS projection_minus_source, "
            f"(SELECT COUNT(*) FROM src.{qident(spec.name)}) AS source_rows, "
            f"(SELECT COUNT(*) FROM main.{qident(spec.name)}) AS projection_rows;"
        )
        payload = json.loads(run_duckdb(catalog, check_sql, json_output=True, timeout=120))
        row = payload[0]
        if any(int(row[k]) != 0 for k in ("source_minus_projection", "projection_minus_source")) or int(row["source_rows"]) != int(row["projection_rows"]):
            raise RuntimeError(f"DuckDB/Parquet equivalence failed for {spec.name}: {row}")
        count, digest = duckdb_table_digest(catalog, spec, scratch)
        if count != int(row["source_rows"]):
            raise RuntimeError(f"DuckDB digest row count mismatch for {spec.name}: {count} != {row['source_rows']}")
        tables[spec.name] = {
            "rows": count,
            "sha256": digest,
            "sourceMinusProjection": int(row["source_minus_projection"]),
            "projectionMinusSource": int(row["projection_minus_source"]),
        }

    invariants: dict[str, int] = {}
    for name, query in INVARIANTS.items():
        payload = json.loads(run_duckdb(catalog, query.strip().rstrip(";") + ";", json_output=True, timeout=120))
        value = int(next(iter(payload[0].values())))
        invariants[name] = value
        if value:
            raise RuntimeError(f"DuckDB invariant {name} has {value} violations")
    return tables, invariants


def logical_fingerprint(tables: dict[str, dict[str, Any]]) -> str:
    normalized = {name: {"rows": value["rows"], "sha256": value["sha256"]} for name, value in sorted(tables.items())}
    return hashlib.sha256(json.dumps(normalized, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def physical_parquet_fingerprint(files: dict[str, dict[str, Any]]) -> str:
    normalized = {name: {"bytes": value["bytes"], "sha256": value["sha256"]} for name, value in sorted(files.items())}
    return hashlib.sha256(json.dumps(normalized, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def build_once(source: Path, destination: Path, source_sha256: str, *, cycle: int) -> dict[str, Any]:
    stage = destination.parent / f".{destination.name}.cycle-{cycle}.tmp"
    if stage.exists():
        shutil.rmtree(stage)
    stage.mkdir(parents=True)
    parquet = stage / "parquet"
    stage_catalog = stage / "host-history.duckdb"
    scratch = stage / ".scratch"
    scratch.mkdir()
    parquet_files = export_parquet(source, parquet)

    # Validate the staged bytes before publication.
    create_catalog(stage_catalog, parquet, source_sha256)
    staged_tables, staged_invariants = validate_catalog(source, stage_catalog, scratch)
    shutil.rmtree(scratch)

    if destination.exists():
        shutil.rmtree(destination)
    stage.rename(destination)

    # DuckDB view definitions persist literal Parquet paths. Recreate the catalog only
    # after publication so the retained read model points at the retained final paths,
    # never at the disposable staging directory.
    final_parquet = destination / "parquet"
    final_catalog = destination / "host-history.duckdb"
    create_catalog(final_catalog, final_parquet, source_sha256)
    final_scratch = destination / ".scratch-final"
    final_scratch.mkdir()
    try:
        tables, invariants = validate_catalog(source, final_catalog, final_scratch)
    finally:
        shutil.rmtree(final_scratch)
    if tables != staged_tables or invariants != staged_invariants:
        raise RuntimeError("final-path DuckDB catalog differs from validated staged projection")

    result = {
        "cycle": cycle,
        "tables": tables,
        "invariants": invariants,
        "logicalFingerprint": logical_fingerprint(tables),
        "parquetFiles": parquet_files,
        "physicalParquetFingerprint": physical_parquet_fingerprint(parquet_files),
        "catalog": {"path": final_catalog.name, "bytes": final_catalog.stat().st_size, "sha256": sha256_file(final_catalog)},
    }
    manifest = {
        "schemaVersion": 1,
        "kind": "ordivon.host-v1-historical-parquet-projection",
        "truthRole": "derived-disposable-historical-read-model",
        "source": str(source),
        "sourceSha256": source_sha256,
        "duckdbVersion": duckdb_version(),
        "tables": {name: {"rows": value["rows"], "sha256": value["sha256"]} for name, value in tables.items()},
        "parquetFiles": parquet_files,
        "logicalFingerprint": result["logicalFingerprint"],
        "physicalParquetFingerprint": result["physicalParquetFingerprint"],
        "invariants": invariants,
        "nonClaims": [
            "Parquet and DuckDB are derived read models, not Host authority.",
            "This package does not recreate Host v1 writer/concurrency/runtime semantics.",
            "The original retired SQLite snapshot and retirement receipt remain the historical authority boundary.",
        ],
    }
    (destination / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    result["manifestSha256"] = sha256_file(destination / "manifest.json")
    return result


def assert_same(expected: dict[str, dict[str, Any]], actual: dict[str, dict[str, Any]], label: str) -> None:
    for spec in TABLES:
        e = expected[spec.name]
        a = actual[spec.name]
        pair_e = (int(e["rows"]), str(e["sha256"]))
        pair_a = (int(a["rows"]), str(a["sha256"]))
        if pair_e != pair_a:
            raise RuntimeError(f"{label} differs for {spec.name}: expected={pair_e} actual={pair_a}")


def main() -> int:
    ap = argparse.ArgumentParser(description="Build a disposable Parquet + DuckDB historical read model from retired Host v1 SQLite")
    ap.add_argument("--source", type=Path, required=True)
    ap.add_argument("--expected-source-sha256", required=True)
    ap.add_argument("--destination", type=Path, required=True)
    ap.add_argument("--pg-host", required=True)
    ap.add_argument("--pg-port", type=int, default=55434)
    ap.add_argument("--pg-database", default="ordivon_host_stage_r1")
    ap.add_argument("--pg-user", default="postgres")
    ap.add_argument("--pg-schema", default="host_retired_final_20260912")
    ap.add_argument("--pg-receipt", type=Path, required=True)
    ap.add_argument("--destructive-rebuilds", type=int, default=2)
    ap.add_argument("--receipt", type=Path, required=True)
    args = ap.parse_args()

    source = args.source.resolve()
    if not source.is_file() or source.is_symlink():
        raise SystemExit(f"unsafe or missing SQLite authority: {source}")
    observed_source_sha = sha256_file(source)
    if observed_source_sha != args.expected_source_sha256:
        raise SystemExit(f"source digest mismatch: expected {args.expected_source_sha256}, observed {observed_source_sha}")
    quick = sqlite3.connect(f"file:{source}?mode=ro&immutable=1", uri=True)
    try:
        row = quick.execute("PRAGMA quick_check").fetchone()
    finally:
        quick.close()
    if row is None or row[0] != "ok":
        raise SystemExit(f"SQLite quick_check failed: {row!r}")

    src = source_digests(source)
    pg_live, pg_invariants, pg_version = pg_digests(args.pg_host, args.pg_port, args.pg_database, args.pg_user, args.pg_schema)
    assert_same(src, pg_live, "live PostgreSQL projection")
    if any(pg_invariants.values()):
        raise RuntimeError(f"live PostgreSQL invariants failed: {pg_invariants}")

    pg_receipt = json.loads(args.pg_receipt.read_text())
    if pg_receipt.get("snapshotSha256") != observed_source_sha:
        raise RuntimeError("PostgreSQL receipt source digest differs from retired SQLite snapshot")
    assert_same(src, pg_receipt["tables"], "PostgreSQL archival receipt")
    if pg_receipt.get("truthRole") != "migration-evidence-not-authority":
        raise RuntimeError("unexpected PostgreSQL truth role")

    destination = args.destination.resolve()
    destination.parent.mkdir(parents=True, exist_ok=True)
    cycles: list[dict[str, Any]] = []
    total_cycles = 1 + args.destructive_rebuilds
    for cycle in range(1, total_cycles + 1):
        if cycle > 1:
            if not destination.exists():
                raise RuntimeError("destructive rebuild expected an existing derived projection")
            shutil.rmtree(destination)
            if destination.exists():
                raise RuntimeError("failed to delete derived projection before rebuild")
        current = build_once(source, destination, observed_source_sha, cycle=cycle)
        assert_same(src, current["tables"], f"Parquet/DuckDB cycle {cycle}")
        cycles.append(current)

    logicals = {item["logicalFingerprint"] for item in cycles}
    if len(logicals) != 1:
        raise RuntimeError(f"logical rebuild fingerprints differ: {logicals}")
    physicals = {item["physicalParquetFingerprint"] for item in cycles}

    final_manifest = json.loads((destination / "manifest.json").read_text())
    result = {
        "schemaVersion": 1,
        "kind": "ordivon.host-v1-historical-projection-r3",
        "standing": "ACCEPTED_BOUNDED",
        "truthRole": "projection-evidence-not-authority",
        "source": {"path": str(source), "sha256": observed_source_sha, "bytes": source.stat().st_size, "quickCheck": "ok"},
        "postgresComparison": {
            "host": args.pg_host,
            "port": args.pg_port,
            "database": args.pg_database,
            "schema": args.pg_schema,
            "serverVersion": pg_version,
            "truthRole": pg_receipt.get("truthRole"),
            "liveRowDigestEquivalence": True,
            "receiptRowDigestEquivalence": True,
            "invariants": pg_invariants,
        },
        "projection": {
            "destination": str(destination),
            "duckdbVersion": final_manifest["duckdbVersion"],
            "tables": final_manifest["tables"],
            "parquetFiles": final_manifest["parquetFiles"],
            "logicalFingerprint": final_manifest["logicalFingerprint"],
            "physicalParquetFingerprint": final_manifest["physicalParquetFingerprint"],
            "invariants": final_manifest["invariants"],
            "manifestSha256": sha256_file(destination / "manifest.json"),
            "duckdbCatalog": {
                "path": str(destination / "host-history.duckdb"),
                "bytes": (destination / "host-history.duckdb").stat().st_size,
                "sha256": sha256_file(destination / "host-history.duckdb"),
            },
        },
        "rebuildProof": {
            "initialBuilds": 1,
            "destructiveRebuilds": args.destructive_rebuilds,
            "totalMaterializations": total_cycles,
            "allLogicalFingerprintsEqual": len(logicals) == 1,
            "allPhysicalParquetFingerprintsEqual": len(physicals) == 1,
            "cycles": [{
                "cycle": item["cycle"],
                "logicalFingerprint": item["logicalFingerprint"],
                "physicalParquetFingerprint": item["physicalParquetFingerprint"],
                "manifestSha256": item["manifestSha256"],
            } for item in cycles],
        },
        "claims": {
            "sqliteToParquetRowEquivalence": True,
            "sqliteToDuckDBRowEquivalence": True,
            "postgresHistoricalProjectionEquivalent": True,
            "derivedProjectionCanBeDeletedAndRebuilt": True,
            "postgresRequiredForHistoricalQuery": False,
            "duckdbIsHostAuthority": False,
            "parquetIsHostAuthority": False,
            "hostWriterRecreated": False,
        },
        "nonClaims": [
            "This does not establish Host v1 writer, lease, concurrency or runtime semantics.",
            "This does not make PostgreSQL, Parquet or DuckDB a Host authority.",
            "This does not authorize deletion of the immutable retired SQLite source or retirement receipt.",
        ],
    }
    args.receipt.parent.mkdir(parents=True, exist_ok=True)
    args.receipt.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
