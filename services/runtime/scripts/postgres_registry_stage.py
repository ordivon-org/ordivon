#!/usr/bin/env python3
"""Copy a frozen SQLite Runtime registry into NON-AUTHORITATIVE PostgreSQL staging.

This tool does not mutate SQLite, deploy a Rust adapter, install a second writer,
or authorize promotion. It requires an independently captured SQLite snapshot
with an exact SHA-256 receipt, uses native PG COPY with constraints, and performs
independent typed row-by-row readback before recording VERIFIED_NON_AUTHORITY.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sqlite3
import struct
import time
from pathlib import Path


SAFE_SCHEMA = re.compile(r"^rw12_stage_[a-z0-9_]{1,46}$")
SQL_TYPES = {"INTEGER": "BIGINT", "TEXT": "TEXT", "BLOB": "BYTEA", "REAL": "DOUBLE PRECISION"}


def file_digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def row_digest_update(h: object, values: tuple) -> None:
    # Canonical length-delimited representation prevents concatenation aliases.
    for value in values:
        if value is None:
            kind, raw = b"N", b""
        elif isinstance(value, int) and not isinstance(value, bool):
            kind, raw = b"I", str(value).encode("ascii")
        elif isinstance(value, float):
            kind, raw = b"F", struct.pack(">d", value)
        elif isinstance(value, str):
            kind, raw = b"T", value.encode("utf-8")
        elif isinstance(value, (bytes, bytearray, memoryview)):
            kind, raw = b"B", bytes(value)
        else:
            raise ValueError("unsupported source/target data type: " + type(value).__name__)
        h.update(kind)
        h.update(len(raw).to_bytes(8, "big"))
        h.update(raw)


def source_tables(con: sqlite3.Connection) -> list[str]:
    return [
        row[0]
        for row in con.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
        )
    ]


def column_specs(con: sqlite3.Connection, name: str) -> list[tuple]:
    specs = con.execute('PRAGMA table_info("' + name + '")').fetchall()
    if not specs:
        raise ValueError("table without columns: " + name)
    if any(spec[2].upper() not in SQL_TYPES for spec in specs):
        raise ValueError("unsupported SQLite declared type: " + name)
    return specs


def ordered_sqlite_rows(con: sqlite3.Connection, name: str, specs: list[tuple]):
    keys = [s[1] for s in sorted(specs, key=lambda r: r[5]) if s[5]]
    if not keys:
        raise ValueError("unkeyed source table: " + name)
    order = ",".join('"' + key + '"' for key in keys)
    return con.execute('SELECT * FROM "' + name + '" ORDER BY ' + order), keys


def pg_order_keys(keys: list[str], specs: list[tuple]) -> object:
    from psycopg import sql

    types = {s[1]: s[2].upper() for s in specs}
    values = [
        sql.SQL('{} COLLATE "C"').format(sql.Identifier(key)) if types[key] == "TEXT" else sql.Identifier(key)
        for key in keys
    ]
    return sql.SQL(",").join(values)


def verify_snapshot(snapshot: Path, manifest: Path) -> dict:
    if not snapshot.is_absolute() or not snapshot.is_file():
        raise ValueError("snapshot must be an existing absolute file")
    receipt = json.loads(manifest.read_text(encoding="utf-8"))
    counts = receipt.get("rowCounts")
    with snapshot.open("rb") as handle:
        file_header = handle.read(16)
    if (
        file_header != b"SQLite format 3\x00"
        or receipt.get("kind") != "ordivon-rw12-source-snapshot"
        or receipt.get("complete") is not True
        or receipt.get("snapshotBytes") != snapshot.stat().st_size
        or receipt.get("sha256") != file_digest(snapshot)
        or not isinstance(counts, dict)
        or not {"jobs", "attempts", "idempotency_keys"}.issubset(counts)
    ):
        raise ValueError("source snapshot digest or identity mismatch")
    return receipt


def migrate(snapshot: Path, receipt: Path, dsn: str, stage_schema: str) -> dict:
    if not SAFE_SCHEMA.fullmatch(stage_schema):
        raise ValueError("invalid/non-stage PostgreSQL schema name")
    meta = verify_snapshot(snapshot, receipt)
    # Required only during native PostgreSQL execution, not Runtime's
    # pure source/contract checks or default unittest discovery.
    import psycopg
    from psycopg import sql

    con = sqlite3.connect("file:" + str(snapshot) + "?mode=ro&immutable=1", uri=True)
    con.execute("PRAGMA query_only=ON")
    try:
        tables = source_tables(con)
        if set(tables) != set(meta["rowCounts"]):
            raise ValueError("source tables differ from frozen receipt")
        # Staged result is not the service's schema/DB or its writer credential.
        with psycopg.connect(dsn, autocommit=True) as pg:
            with pg.transaction():
                pg.execute(sql.SQL("CREATE SCHEMA {}").format(sql.Identifier(stage_schema)))
                pg.execute(
                    sql.SQL(
                        "CREATE TABLE {}._stage_control ("
                        "id TEXT PRIMARY KEY CHECK (id='source'), "
                        "state TEXT NOT NULL CHECK (state IN ('COPYING','VERIFIED_NON_AUTHORITY')), "
                        "source_sha256 TEXT NOT NULL, "
                        "promotion_allowed BOOLEAN NOT NULL DEFAULT FALSE CHECK (NOT promotion_allowed))"
                    ).format(sql.Identifier(stage_schema))
                )
                pg.execute(
                    sql.SQL(
                        "INSERT INTO {}._stage_control(id,state,source_sha256,promotion_allowed) "
                        "VALUES ('source','COPYING',%s,FALSE)"
                    ).format(sql.Identifier(stage_schema)),
                    (meta["sha256"],),
                )
            totals: dict[str, dict] = {}
            for table in tables:
                specs = column_specs(con, table)
                columns = [s[1] for s in specs]
                definitions = []
                for _cid, name, decl, nonnull, _default, pk in specs:
                    definitions.append(
                        sql.SQL("{} {}{}").format(
                            sql.Identifier(name),
                            sql.SQL(SQL_TYPES[decl.upper()]),
                            sql.SQL(" NOT NULL") if nonnull or pk else sql.SQL(""),
                        )
                    )
                with pg.transaction():
                    pg.execute(
                        sql.SQL("CREATE TABLE {}.{} ({})").format(
                            sql.Identifier(stage_schema),
                            sql.Identifier(table),
                            sql.SQL(",").join(definitions),
                        )
                    )
                    query = sql.SQL("COPY {}.{} ({}) FROM STDIN").format(
                        sql.Identifier(stage_schema),
                        sql.Identifier(table),
                        sql.SQL(",").join(map(sql.Identifier, columns)),
                    )
                    rows, keys = ordered_sqlite_rows(con, table, specs)
                    signature = hashlib.sha256()
                    count = 0
                    with pg.cursor().copy(query) as cp:
                        for row in rows:
                            row = tuple(row)
                            row_digest_update(signature, row)
                            cp.write_row(row)
                            count += 1
                    if count != meta["rowCounts"][table]:
                        raise ValueError("source row count drift: " + table)
                totals[table] = {
                    "count": count,
                    "source_row_sha256": signature.hexdigest(),
                    "keys": keys,
                }
                print("PG_COPIED", table, count, flush=True)
            # Build actual constraints after bulk load. These are staging validation
            # constraints, NOT the missing Runtime PG CAS/trigger implementation.
            for table in tables:
                specs = column_specs(con, table)
                keys = [s[1] for s in sorted(specs, key=lambda r: r[5]) if s[5]]
                with pg.transaction():
                    pg.execute(
                        sql.SQL("ALTER TABLE {}.{} ADD PRIMARY KEY ({})").format(
                            sql.Identifier(stage_schema),
                            sql.Identifier(table),
                            sql.SQL(",").join(map(sql.Identifier, keys)),
                        )
                    )
                    for i, idx_name, unique, origin, partial in con.execute('PRAGMA index_list("' + table + '")'):
                        if not unique or origin == "pk" or partial:
                            continue
                        index_cols = [row[2] for row in con.execute('PRAGMA index_info("' + idx_name + '")')]
                        if any(not col for col in index_cols):
                            raise ValueError("expression UNIQUE index requires manual refinement")
                        pg.execute(
                            sql.SQL("CREATE UNIQUE INDEX {} ON {}.{} ({})").format(
                                sql.Identifier("stage_unique_" + str(i) + "_" + table),
                                sql.Identifier(stage_schema),
                                sql.Identifier(table),
                                sql.SQL(",").join(map(sql.Identifier, index_cols)),
                            )
                        )
            # Install checked source-declared FK edges, including Job/Attempt cycles.
            for table in tables:
                edges: dict[int, list] = {}
                for edge in con.execute('PRAGMA foreign_key_list("' + table + '")'):
                    edges.setdefault(edge[0], []).append(edge)
                with pg.transaction():
                    for i, group in sorted(edges.items()):
                        group.sort(key=lambda r: r[1])
                        target = group[0][2]
                        delete = group[0][6].upper()
                        if delete not in ("CASCADE", "RESTRICT", "NO ACTION", "SET NULL"):
                            raise ValueError("unsupported FK delete action")
                        pg.execute(
                            sql.SQL(
                                "ALTER TABLE {}.{} ADD CONSTRAINT {} FOREIGN KEY ({}) "
                                "REFERENCES {}.{} ({}) ON DELETE {}"
                            ).format(
                                sql.Identifier(stage_schema),
                                sql.Identifier(table),
                                sql.Identifier("stage_fk_" + str(i) + "_" + table),
                                sql.SQL(",").join(sql.Identifier(e[3]) for e in group),
                                sql.Identifier(stage_schema),
                                sql.Identifier(target),
                                sql.SQL(",").join(sql.Identifier(e[4]) for e in group),
                                sql.SQL(delete),
                            )
                        )
            # PG readback is independent of the COPY cursor and exact typed payload
            # (not merely source count, revision or digest metadata).
            for table in tables:
                specs = column_specs(con, table)
                keys = totals[table]["keys"]
                pg_sig = hashlib.sha256()
                read_count = 0
                with pg.transaction():
                    with pg.cursor(name="rw12_" + table) as cursor:
                        cursor.execute(
                            sql.SQL("SELECT * FROM {}.{} ORDER BY {}").format(
                                sql.Identifier(stage_schema),
                                sql.Identifier(table),
                                pg_order_keys(keys, specs),
                            )
                        )
                        while chunk := cursor.fetchmany(4096):
                            for row in chunk:
                                row_digest_update(pg_sig, tuple(row))
                                read_count += 1
                if read_count != totals[table]["count"] or pg_sig.hexdigest() != totals[table]["source_row_sha256"]:
                    raise ValueError("independent PG typed row parity FAIL: " + table)
                totals[table]["target_row_sha256"] = pg_sig.hexdigest()
                print("PG_READBACK_VERIFIED", table, read_count, flush=True)
            with pg.transaction():
                pg.execute(
                    sql.SQL(
                        "UPDATE {}._stage_control SET state='VERIFIED_NON_AUTHORITY' "
                        "WHERE id='source' AND state='COPYING' AND promotion_allowed=FALSE"
                    ).format(sql.Identifier(stage_schema))
                )
            result = {
                "kind": "ordivon-runtime-pg-staging-non-authority",
                "snapshot_sha256": meta["sha256"],
                "postgres_schema": stage_schema,
                "promotion_allowed": False,
                "row_total": sum(item["count"] for item in totals.values()),
                "tables": totals,
                "verified_at_ms": int(time.time() * 1000),
            }
            return result
    finally:
        con.close()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--snapshot", type=Path, required=True)
    parser.add_argument("--receipt", type=Path, required=True)
    parser.add_argument("--postgres-dsn", required=True)
    parser.add_argument("--schema", required=True)
    parser.add_argument("--result", type=Path, required=True)
    args = parser.parse_args()
    if args.result.exists():
        raise ValueError("refusing to replace prior stage receipt")
    result = migrate(args.snapshot, args.receipt, args.postgres_dsn, args.schema)
    args.result.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print("STAGE_VERIFIED_NOT_PROMOTABLE", result["row_total"], flush=True)


if __name__ == "__main__":
    main()
