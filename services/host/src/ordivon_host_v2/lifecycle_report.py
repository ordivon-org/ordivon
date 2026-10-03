from __future__ import annotations

import argparse
import json
import os
from datetime import datetime
from typing import Any

import psycopg
from psycopg.rows import dict_row

TRUTH_BOUNDARY = (
    "Host lifecycle inventory only; age, Runtime execution, Git state, and inactivity do not "
    "establish semantic completion. Every terminal disposition requires explicit owner evidence "
    "and work.snapshot.commit with an expectedRevision fence."
)


def classify_open_work(row: dict[str, Any], *, observed_at: datetime, stale_days: int) -> dict[str, Any]:
    updated_at = row["updated_at"]
    if updated_at.tzinfo is None:
        raise ValueError("updated_at must be timezone-aware")
    age_seconds = max(0.0, (observed_at - updated_at).total_seconds())
    age_days = age_seconds / 86_400.0
    payload = row["payload"]
    unresolved = payload.get("unresolved", [])
    next_actions = payload.get("nextActions", [])
    legacy = row["kind"] == "legacy-task"
    if legacy:
        review_class = "legacy-migration-review"
    elif age_days >= stale_days:
        review_class = "aged-native-review"
    else:
        review_class = "recent-open"
    return {
        "workRef": row["work_ref"],
        "workKind": row["kind"],
        "revision": int(row["current_revision"]),
        "updatedAt": updated_at.isoformat(),
        "ageDays": round(age_days, 3),
        "reviewClass": review_class,
        "unresolvedCount": len(unresolved),
        "nextActionsCount": len(next_actions),
        "snapshotDigest": row["current_snapshot_digest"],
    }


def build_report(
    rows: list[dict[str, Any]],
    *,
    observed_at: datetime,
    stale_days: int,
) -> dict[str, Any]:
    items = [
        classify_open_work(row, observed_at=observed_at, stale_days=stale_days)
        for row in rows
    ]
    classes: dict[str, int] = {}
    for item in items:
        classes[item["reviewClass"]] = classes.get(item["reviewClass"], 0) + 1
    items.sort(key=lambda item: (-item["ageDays"], item["workRef"]))
    return {
        "schemaVersion": 1,
        "kind": "ordivon.host-work-lifecycle-report",
        "observedAt": observed_at.isoformat(),
        "staleDays": stale_days,
        "openCount": len(items),
        "classes": classes,
        "items": items,
        "truthBoundary": TRUTH_BOUNDARY,
    }


def read_report(dsn: str, *, stale_days: int) -> dict[str, Any]:
    with psycopg.connect(dsn, row_factory=dict_row) as conn, conn.transaction():
        conn.execute("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY")
        observed_at = conn.execute("SELECT now() AS observed_at").fetchone()["observed_at"]
        rows = conn.execute(
            "SELECT w.work_ref,w.kind,w.current_revision,w.current_snapshot_digest,"
            "w.updated_at,s.payload "
            "FROM works w JOIN work_snapshots s "
            "ON s.work_ref=w.work_ref AND s.revision=w.current_revision "
            "WHERE w.state='open' ORDER BY w.updated_at,w.work_ref"
        ).fetchall()
    return build_report(rows, observed_at=observed_at, stale_days=stale_days)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Report Host open-Work lifecycle pressure without mutating Work state."
    )
    parser.add_argument(
        "--stale-days",
        type=int,
        default=7,
        help="Age threshold for native Work review; never interpreted as completion evidence.",
    )
    args = parser.parse_args()
    if args.stale_days < 1:
        parser.error("--stale-days must be >= 1")
    dsn = os.environ["ORDIVON_HOST_V2_DSN"]
    report = read_report(dsn, stale_days=args.stale_days)
    print(json.dumps(report, sort_keys=True, separators=(",", ":")))


if __name__ == "__main__":
    main()
