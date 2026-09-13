#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os

import psycopg
from psycopg.rows import dict_row

from ordivon_host_v2.board import ensure_task_route_anchor_in_tx


def backfill(dsn: str, *, include_terminal: bool = False) -> dict[str, int]:
    with psycopg.connect(dsn, row_factory=dict_row) as conn, conn.transaction():
        where = "" if include_terminal else "WHERE state='open'"
        rows = conn.execute(f"SELECT task_id FROM tasks {where} ORDER BY task_id").fetchall()
        created = 0
        existing = 0
        for row in rows:
            result = ensure_task_route_anchor_in_tx(conn, row["task_id"])
            if result["admission"] == "committed":
                created += 1
            else:
                existing += 1
        return {"considered": len(rows), "created": created, "existing": existing}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dsn", default=os.environ.get("ORDIVON_HOST_V2_DSN"))
    parser.add_argument("--include-terminal", action="store_true")
    args = parser.parse_args()
    if not args.dsn:
        raise RuntimeError("set ORDIVON_HOST_V2_DSN or pass --dsn")
    result = backfill(args.dsn, include_terminal=args.include_terminal)
    print(
        "route-anchor-backfill "
        + " ".join(f"{key}={value}" for key, value in sorted(result.items()))
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
