"""One-time R6 SQLite -> PostgreSQL ledger transfer, preserving event identity.

The source file is opened read-only and retained. The destination search must
be empty, and the complete copy commits in one PostgreSQL transaction only
after every source hash-chain event has been independently reproduced.
A caller must provide the exact current consumer search identity and attest
source-writer quiescence before any old data read. This is an admission assertion,
not an independent writer-lock proof. Unconsumed history is not migrated.
"""
from __future__ import annotations

import argparse
import json
import os
import sqlite3
from contextlib import closing
from pathlib import Path
from urllib.parse import quote

from ordivon_studio.grounded_contracts import canonical_digest
from ordivon_studio.research_validity import TrialLedger


def migrate(
    source: Path,
    dsn: str,
    *,
    expected_search_id: str | None = None,
    retention_consumer: str | None = None,
    source_writers_stopped: bool = False,
) -> dict[str, object]:
    # Retention is a current-consumer decision, not an automatic copy of all
    # historical experiments. The caller assertion does not independently
    # prove every external SQLite writer has stopped.
    if not source_writers_stopped:
        raise ValueError("source SQLite writers must be independently stopped before migration")
    if retention_consumer not in {"registered_search_replay", "sealed_holdout_audit"}:
        raise ValueError("explicit current retention consumer required for historical events")
    if not isinstance(expected_search_id, str) or not expected_search_id.strip():
        raise ValueError("exact expected search ID required for current consumer")
    if not source.is_file() or source.is_symlink():
        raise ValueError("legacy SQLite source must be an existing regular file")
    url = "file:" + quote(str(source.resolve()), safe="/") + "?mode=ro"
    with closing(sqlite3.connect(url, uri=True)) as old:
        old.execute("PRAGMA query_only=ON")
        old.execute("BEGIN")
        if old.execute("PRAGMA quick_check").fetchone()[0] != "ok":
            raise ValueError("legacy SQLite integrity check failed")
        rows = old.execute(
            "SELECT seq,event_id,search_id,attempt_id,candidate_id,event_type,"
            "payload_json,prev_hash,event_hash FROM trial_events ORDER BY seq"
        ).fetchall()
        if not rows:
            raise ValueError("legacy SQLite ledger is empty")
        search_ids = {str(row[2]) for row in rows}
        if len(search_ids) != 1:
            raise ValueError("legacy ledger must contain one exact experiment search ID")
        search_id = next(iter(search_ids))
        if search_id != expected_search_id:
            raise ValueError("source contains a different search ID than current consumer")
        expected_prev = None
        semantic_rows = []
        for _, event_id, _, attempt_id, candidate_id, event_type, payload_json, prev_hash, event_hash in rows:
            payload = json.loads(payload_json)
            semantic = {
                "searchId": search_id,
                "attemptId": attempt_id,
                "candidateId": candidate_id,
                "eventType": event_type,
                "payload": payload,
                "prevHash": expected_prev,
            }
            if prev_hash != expected_prev or canonical_digest(semantic) != event_hash:
                raise ValueError("legacy hash-chain does not verify")
            if event_id != "trial-event://" + event_hash.removeprefix("sha256:"):
                raise ValueError("legacy event identity mismatch")
            semantic_rows.append((event_id, attempt_id, candidate_id, event_type, payload, event_hash))
            expected_prev = event_hash
        snapshot = canonical_digest(semantic_rows)

    destination = TrialLedger(dsn, search_id=search_id)
    try:
        with destination.db.transaction():
            count = destination.db.execute(
                "SELECT count(*) FROM ordivon_media_trial.trial_events WHERE search_id=%s",
                (search_id,),
            ).fetchone()[0]
            if count:
                raise ValueError("destination search already contains events")
            for event_id, attempt_id, candidate_id, event_type, payload, event_hash in semantic_rows:
                actual_id = destination.append(attempt_id, candidate_id, event_type, payload)
                if actual_id != event_id or event_hash != "sha256:" + actual_id.split("://", 1)[1]:
                    raise ValueError("PostgreSQL event identity diverged from SQLite source")
            # Complete independent readback BEFORE committing the copied history.
            if not destination.verify():
                raise ValueError("destination PostgreSQL hash-chain mismatch")
            if sum(destination.summary()["eventCounts"].values()) != len(semantic_rows):
                raise ValueError("destination PostgreSQL event count differs")
        return {
            "searchId": search_id,
            "events": len(semantic_rows),
            "sourceSnapshotDigest": snapshot,
            "lastHash": expected_prev,
            "destinationChainValid": True,
            "legacySourceRetained": True,
            "legacySourceDisposition": "PENDING_INDEPENDENT_RETIREMENT_DECISION",
            "retentionConsumer": retention_consumer,
            "quiescenceEvidence": "CALLER_ATTESTED_NOT_INDEPENDENTLY_PROVEN",
        }
    finally:
        destination.close()


def main() -> int:
    parser = argparse.ArgumentParser(description="Transfer one stopped R6 SQLite history into PostgreSQL.")
    parser.add_argument("--sqlite", required=True, type=Path, help="read-only legacy file")
    parser.add_argument("--expected-search-id", required=True, help="current consumer's exact search identity")
    parser.add_argument(
        "--retention-consumer",
        required=True,
        choices=("registered_search_replay", "sealed_holdout_audit"),
        help="specific current consumer requiring retained history",
    )
    parser.add_argument(
        "--source-writers-stopped",
        action="store_true",
        help="operator attests independently stopped legacy SQLite writers",
    )
    args = parser.parse_args()
    print(json.dumps(
        migrate(
            args.sqlite,
            os.environ.get("ORDIVON_MEDIA_TRIAL_PG_DSN", ""),
            expected_search_id=args.expected_search_id,
            retention_consumer=args.retention_consumer,
            source_writers_stopped=args.source_writers_stopped,
        ),
        sort_keys=True,
        indent=2,
    ))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
