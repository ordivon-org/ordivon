#!/usr/bin/env python3
"""Read-only PG cutover source-currentness falsifier, not a writer promotion tool.

The staged 11-table PostgreSQL receipt is historical. A checksum-valid stage
is never proof that the installed Runtime's actively changing source is equal.
This bounded probe *only* rejects known stale stages; matching counts remain
UNKNOWN until quiescence, exact row parity and consumer/writer proofs.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import subprocess
import sys


TABLE_ID = re.compile(r"[A-Za-z_][A-Za-z0-9_]*\Z")
DIGEST = re.compile(r"[a-f0-9]{64}\Z")


class EvidenceError(ValueError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise EvidenceError(message)


def load_json(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    require(isinstance(value, dict), "receipt must be a JSON object")
    return value


def inspect(source: Path, snapshot: Path, stage: Path) -> dict:
    source = source.resolve(strict=True)
    original = load_json(snapshot)
    receipt = load_json(stage)

    require(original.get("kind") == "ordivon-rw12-source-snapshot", "wrong snapshot kind")
    require(original.get("complete") is True, "incomplete source snapshot")
    require(original.get("quickCheck") == "ok", "source snapshot integrity not certified")
    require(receipt.get("kind") == "ordivon-runtime-pg-staging-non-authority", "wrong PG receipt kind")
    require(receipt.get("promotion_allowed") is False, "stage no longer non-authority")
    require(
        isinstance(receipt.get("postgres_schema"), str)
        and receipt["postgres_schema"].strip()
        and receipt["postgres_schema"] not in ("public", "pg_catalog"),
        "invalid PG stage schema",
    )
    require(
        Path(original["sourcePath"]).resolve(strict=True) == source,
        "snapshot is not bound to the requested source",
    )
    digest = original.get("sha256")
    require(
        isinstance(digest, str) and bool(DIGEST.fullmatch(digest)) and receipt.get("snapshot_sha256") == digest,
        "PG receipt does not bind the snapshot digest",
    )
    prior = original.get("rowCounts")
    tables = receipt.get("tables")
    require(isinstance(prior, dict) and prior and isinstance(tables, dict), "missing table census")
    require(set(prior) == set(tables), "source/PG table identity mismatch")
    require(
        isinstance(receipt.get("row_total"), int)
        and not isinstance(receipt["row_total"], bool)
        and receipt["row_total"] == sum(v for v in prior.values() if type(v) is int),
        "stage row total mismatch",
    )
    for name, spec in tables.items():
        require(isinstance(name, str) and bool(TABLE_ID.fullmatch(name)), "invalid table identifier")
        require(type(prior[name]) is int and prior[name] >= 0, "invalid source row count")
        require(isinstance(spec, dict) and type(spec.get("count")) is int, "invalid target row count")
        require(spec["count"] == prior[name], "stage and snapshot table counts differ")
        src, target = spec.get("source_row_sha256"), spec.get("target_row_sha256")
        require(
            isinstance(src, str) and bool(DIGEST.fullmatch(src)) and target == src,
            "historical stage lacks independent row-parity evidence",
        )

    # The existing pinned native sqlite3 CLI is used in strict read-only mode
    # solely to FALSIFY a proposed PG cutover from its retiring source.
    # No new direct legacy database API client or second persistence owner.
    # One SQL transaction snapshots the 11 bounded table counts atomically.
    projection = " UNION ALL ".join(
        f"SELECT '{name}' AS table_name, count(*) AS row_count FROM \"{name}\"" for name in sorted(prior)
    )
    sql = "PRAGMA query_only=ON; BEGIN; " + projection + "; ROLLBACK;"
    completed = subprocess.run(
        ["sqlite3", "-readonly", "-batch", "-bail", "-json", str(source), sql],
        capture_output=True,
        text=True,
        check=True,
        timeout=90,
    )
    rows_from_cli = json.loads(completed.stdout)
    require(
        isinstance(rows_from_cli, list) and len(rows_from_cli) == len(prior),
        "SQLite source census incomplete",
    )
    actual = {}
    for row in rows_from_cli:
        require(isinstance(row, dict), "malformed live source census")
        name, count = row.get("table_name"), row.get("row_count")
        require(
            name in prior and name not in actual and type(count) is int and count >= 0,
            "unexpected live source table identity/count",
        )
        actual[name] = count
    require(set(actual) == set(prior), "live source table census incomplete")

    rows = [
        {"table": name, "staged": prior[name], "source": actual[name], "delta": actual[name] - prior[name]}
        for name in sorted(prior)
    ]
    has_drift = any(r["delta"] != 0 for r in rows)
    return {
        "kind": "ordivon-rw12-currentness-falsifier",
        "verdict": "BLOCKED_SOURCE_DRIFT" if has_drift else "UNKNOWN_COUNTS_ONLY",
        "promotion_admitted": False,
        "source_row_total": sum(actual.values()),
        "staged_row_total": receipt["row_total"],
        "delta_rows": sum(actual.values()) - receipt["row_total"],
        "table_rows": rows,
        "proof_scope": "single read-only SQLite snapshot vs historically SHA-bound non-authority PG stage receipt; NOT live PG row parity, consumer qualification, or a writer switch",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--snapshot", type=Path, required=True)
    parser.add_argument("--stage", type=Path, required=True)
    args = parser.parse_args()
    try:
        value = inspect(args.source, args.snapshot, args.stage)
    except (OSError, subprocess.SubprocessError, ValueError, TypeError, KeyError) as error:
        print(
            json.dumps(
                {
                    "kind": "ordivon-rw12-currentness-falsifier",
                    "verdict": "INVALID_EVIDENCE",
                    "promotion_admitted": False,
                    "reason": type(error).__name__,
                },
                sort_keys=True,
            )
        )
        return 2
    print(json.dumps(value, sort_keys=True))
    # This tool never certifies a production PostgreSQL cutover.
    return 3 if value["verdict"] == "BLOCKED_SOURCE_DRIFT" else 4


if __name__ == "__main__":
    sys.exit(main())
