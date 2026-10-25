#!/usr/bin/env python3
"""Read-only source-bound Runtime Registry census for selective PG cutover.

This is a migration *decision aid*, not permission to purge or an import tool.
Never imports arbitrary historical rows just because the old database exists.
"""
from __future__ import annotations

import argparse
import json
import sqlite3
from contextlib import closing
from pathlib import Path
from urllib.parse import quote

REQUIRED_TABLES = frozenset(
    {
        "jobs", "attempts", "concurrency_reservations", "idempotency_keys",
        "job_events", "artifacts", "schema_migrations",
        "attempt_supervisor_owners", "job_execution_providers",
        "job_host_dependencies", "job_runtime_release_effects",
    }
)


class SourceUnqualified(ValueError):
    """Source could not support a sound bounded migration census."""


def census(source: Path) -> dict[str, object]:
    # The URI quotes reserved '#', '?', and '%' as physical filename bytes.
    # mode=ro and query_only prevent any source mutation by this program.
    uri = "file:" + quote(str(source.absolute()), safe="/") + "?mode=ro"
    try:
        with closing(sqlite3.connect(uri, uri=True, timeout=3)) as db:
            db.execute("PRAGMA query_only=ON")
            db.execute("BEGIN")  # one consistent WAL snapshot
            names = {
                row[0] for row in db.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                )
            }
            missing = sorted(REQUIRED_TABLES - names)
            if missing:
                raise SourceUnqualified(f"required Registry tables missing: {missing}")
            extra = sorted(
                name for name in names - REQUIRED_TABLES
                if not name.startswith("sqlite_")
            )
            if extra:
                raise SourceUnqualified(f"unclassified Registry tables: {extra}")

            counts = {
                name: db.execute(f'SELECT COUNT(*) FROM "{name}"').fetchone()[0]
                for name in sorted(REQUIRED_TABLES)
            }

            unresolved = db.execute(
                "SELECT COUNT(*) FROM jobs WHERE resolution IS NULL"
            ).fetchone()[0]
            running_or_recovery = db.execute(
                "SELECT COUNT(*) FROM attempts "
                "WHERE state='running' OR recovery_required=1"
            ).fetchone()[0]
            held = db.execute(
                "SELECT COUNT(*) FROM concurrency_reservations "
                "WHERE state!='released'"
            ).fetchone()[0]
            live_closure = db.execute(
                "SELECT COUNT(*) FROM jobs AS j WHERE j.resolution IS NULL "
                "OR EXISTS(SELECT 1 FROM attempts AS a "
                " WHERE a.job_id=j.job_id AND "
                " (a.state='running' OR a.recovery_required=1)) "
                "OR EXISTS(SELECT 1 FROM concurrency_reservations AS r "
                " JOIN attempts AS a ON a.attempt_id=r.attempt_id "
                " WHERE a.job_id=j.job_id AND r.state!='released')"
            ).fetchone()[0]
            terminal = counts["jobs"] - unresolved
            if not 0 <= unresolved <= live_closure <= counts["jobs"]:
                raise SourceUnqualified("impossible Registry live-consumer closure")

            orphans = db.execute(
                "SELECT COUNT(*) FROM attempts AS a LEFT JOIN jobs AS j "
                "ON j.job_id=a.job_id WHERE j.job_id IS NULL"
            ).fetchone()[0]
            if orphans:
                raise SourceUnqualified("attempt references missing parent Jobs")

            return {
                "kind": "ordivon.runtime-pg-migration-retention-census",
                "source": str(source.absolute()),
                "readOnly": True,
                "requiredTablesPresent": True,
                "consumerGraphComplete": False,
                "physicalPgCutoverQualified": False,
                "recordCounts": counts,
                "requiredOperationalClosure": {
                    "unresolvedJobs": unresolved,
                    "runningOrRecoveryAttempts": running_or_recovery,
                    "unreleasedReservations": held,
                    "distinctJobsRequiringLiveRecovery": live_closure,
                },
                "historicalReview": {
                    "terminalJobs": terminal,
                    "idempotencyKeys": counts["idempotency_keys"],
                    "eventReceipts": counts["job_events"],
                    "artifactReferences": counts["artifacts"],
                    "reason": (
                        "Terminal is not consumer-free; prior request replay, "
                        "observability and release-effect obligations are unproven."
                    ),
                },
                "sourceOnly": {
                    "schemaMigrations": counts["schema_migrations"],
                    "meaning": "source version evidence, not PG business rows",
                },
                "emptyNoImport": sorted(
                    name for name, amount in counts.items()
                    if amount == 0 and name != "schema_migrations"
                ),
                "admission": "STOP_UNTIL_CONSUMER_AND_PG_PHYSICAL_PARITY_PROVEN",
            }
    except sqlite3.Error as exc:
        raise SourceUnqualified(f"SQLite read-only source unavailable: {type(exc).__name__}") from exc


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path, help="explicit Runtime Registry source path")
    args = parser.parse_args()
    try:
        report = census(args.source)
    except SourceUnqualified as exc:
        parser.error(str(exc))
    print(json.dumps(report, sort_keys=True, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
