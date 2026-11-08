from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
import re
import stat
import tempfile
from collections import Counter
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any, BinaryIO, TextIO

import psycopg
from psycopg import sql
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb

SHA256_RE = re.compile(r"^sha256:[0-9a-f]{64}$")


class EpisodeStoreError(ValueError):
    pass


@contextmanager
def _frozen_source(path: Path) -> Iterator[tuple[BinaryIO, str, int]]:
    """Freeze bytes from ONE regular-file descriptor before parsing or PG commit.

    Reuse the OS's O_NOFOLLOW, fstat and private anonymous temporary file.
    The immutable copy makes the parsed rows and committed source digest
    refer to exactly the same observed bytes. It does not prove external
    source authenticity or protect against privileged writers in the OS.
    """
    flags = (
        os.O_RDONLY
        | getattr(os, "O_CLOEXEC", 0)
        | getattr(os, "O_NONBLOCK", 0)
        | getattr(os, "O_NOFOLLOW", 0)
    )
    handle = os.open(path, flags)
    with (
        os.fdopen(handle, "rb") as source,
        tempfile.TemporaryFile(mode="w+b") as frozen,
    ):
        before = os.fstat(source.fileno())
        if not stat.S_ISREG(before.st_mode):
            raise EpisodeStoreError("source must be a regular file")
        digest = hashlib.sha256()
        size = 0
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
            size += len(block)
            frozen.write(block)
        after = os.fstat(source.fileno())

        def identity(st: os.stat_result) -> tuple[int, int, int, int, int]:
            return st.st_dev, st.st_ino, st.st_size, st.st_mtime_ns, st.st_ctime_ns

        if identity(before) != identity(after) or size != before.st_size:
            raise EpisodeStoreError("source changed during byte snapshot")
        frozen.seek(0)
        yield frozen, "sha256:" + digest.hexdigest(), size


def _canonical_digest(value: Any) -> str:
    payload = json.dumps(
        value, sort_keys=True, ensure_ascii=False, separators=(",", ":")
    ).encode()
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def _require_sha256(value: str, label: str) -> str:
    if not SHA256_RE.fullmatch(value):
        raise EpisodeStoreError(f"{label} must be sha256:<64 lowercase hex>")
    return value


def _simple_identifier(value: str, label: str) -> str:
    if not value or not value.replace("_", "").isalnum():
        raise EpisodeStoreError(f"{label} must be a simple identifier")
    return value


def _load_episodes_from_lines(
    handle: TextIO, profile_id: str, label: Path
) -> list[dict[str, Any]]:
    episodes: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for line_number, line in enumerate(handle, start=1):
        if not line.strip():
            continue
        value = json.loads(line)
        if not isinstance(value, dict):
            raise EpisodeStoreError(f"{label}:{line_number}: root must be object")
        if value.get("kind") != "ordivon.experimental-episode-binding":
            raise EpisodeStoreError(f"{label}:{line_number}: unexpected kind")
        if value.get("profileId") != profile_id:
            raise EpisodeStoreError(
                f"{label}:{line_number}: profileId does not match {profile_id}"
            )
        episode_id = value.get("episodeId")
        projection_digest = value.get("projectionDigest")
        if not isinstance(episode_id, str) or not episode_id:
            raise EpisodeStoreError(f"{label}:{line_number}: invalid episodeId")
        if not isinstance(projection_digest, str):
            raise EpisodeStoreError(f"{label}:{line_number}: missing projectionDigest")
        _require_sha256(projection_digest, "projectionDigest")
        key = (episode_id, projection_digest)
        if key in seen:
            raise EpisodeStoreError(
                f"{label}:{line_number}: duplicate episode/projection identity"
            )
        seen.add(key)
        episodes.append(value)
    return episodes


def _load_episodes(path: Path, profile_id: str) -> list[dict[str, Any]]:
    """Keep the existing standalone parser interface for bounded local tests."""
    with path.open("r", encoding="utf-8") as handle:
        return _load_episodes_from_lines(handle, profile_id, path)


def build_ingest_identity(
    *,
    corpus_id: str,
    profile_id: str,
    source_file_digest: str,
    projection_set_digest: str,
    schema_digest: str,
    adapter_digest: str,
) -> tuple[str, dict[str, str]]:
    material = {
        "corpusId": corpus_id,
        "profileId": profile_id,
        "sourceFileDigest": _require_sha256(source_file_digest, "source_file_digest"),
        "projectionSetDigest": _require_sha256(
            projection_set_digest, "projection_set_digest"
        ),
        "schemaDigest": _require_sha256(schema_digest, "schema_digest"),
        "adapterDigest": _require_sha256(adapter_digest, "adapter_digest"),
    }
    return "ingest:" + _canonical_digest(material), material


def _set_role(conn: psycopg.Connection[Any], role: str | None) -> None:
    if role is None:
        return
    safe = _simple_identifier(role, "database role")
    conn.execute(sql.SQL("SET ROLE {}").format(sql.Identifier(safe)))


def _insert_episode(conn: psycopg.Connection[Any], episode: dict[str, Any]) -> bool:
    anchor = episode["anchor"]
    projection_digest = episode["projectionDigest"]
    inserted = (
        conn.execute(
            """
            INSERT INTO episode_projections(
              episode_id, projection_digest, profile_id, data_class,
              anchor_owner_id, anchor_object_kind, anchor_object_id,
              source_record_digest
            )
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
            ON CONFLICT DO NOTHING
            RETURNING 1
            """,
            (
                episode["episodeId"],
                projection_digest,
                episode["profileId"],
                episode["dataClass"],
                anchor["ownerId"],
                anchor["objectKind"],
                anchor["objectId"],
                anchor["sourceRecordDigest"],
            ),
        ).fetchone()
        is not None
    )

    for ref in episode["ownerRefs"]:
        conn.execute(
            """
            INSERT INTO episode_owner_refs(
              episode_id, projection_digest, owner_id, object_kind,
              object_id, relation, digest
            )
            VALUES (%s,%s,%s,%s,%s,%s,%s)
            ON CONFLICT DO NOTHING
            """,
            (
                episode["episodeId"],
                projection_digest,
                ref["ownerId"],
                ref["objectKind"],
                ref["objectId"],
                ref["relation"],
                ref.get("digest"),
            ),
        )

    for binding in episode["evidenceBindings"]:
        conn.execute(
            """
            INSERT INTO episode_evidence_bindings(
              episode_id, projection_digest, kind, evidence_count,
              set_digest, total_bytes, truncated_count
            )
            VALUES (%s,%s,%s,%s,%s,%s,%s)
            ON CONFLICT DO NOTHING
            """,
            (
                episode["episodeId"],
                projection_digest,
                binding["kind"],
                binding["count"],
                binding["setDigest"],
                binding.get("totalBytes"),
                binding.get("truncatedCount"),
            ),
        )

    for dimension in episode["dimensions"]:
        conn.execute(
            """
            INSERT INTO episode_dimensions(
              episode_id, projection_digest, name, value
            )
            VALUES (%s,%s,%s,%s)
            ON CONFLICT DO NOTHING
            """,
            (
                episode["episodeId"],
                projection_digest,
                dimension["name"],
                Jsonb(dimension["value"]),
            ),
        )

    for measure in episode["measures"]:
        conn.execute(
            """
            INSERT INTO episode_measures(
              episode_id, projection_digest, name, value, unit
            )
            VALUES (%s,%s,%s,%s,%s)
            ON CONFLICT DO NOTHING
            """,
            (
                episode["episodeId"],
                projection_digest,
                measure["name"],
                measure["value"],
                measure.get("unit"),
            ),
        )
    return inserted


# Columns are fixed by this Owner's existing Alembic schema. Reuse that
# schema rather than adding an ingest-to-projection tracking table.
_PROJECTION_COLUMNS: dict[str, tuple[str, ...]] = {
    "episode_projections": (
        "episode_id",
        "projection_digest",
        "profile_id",
        "data_class",
        "anchor_owner_id",
        "anchor_object_kind",
        "anchor_object_id",
        "source_record_digest",
    ),
    "episode_owner_refs": (
        "episode_id",
        "projection_digest",
        "owner_id",
        "object_kind",
        "object_id",
        "relation",
        "digest",
    ),
    "episode_evidence_bindings": (
        "episode_id",
        "projection_digest",
        "kind",
        "evidence_count",
        "set_digest",
        "total_bytes",
        "truncated_count",
    ),
    "episode_dimensions": (
        "episode_id",
        "projection_digest",
        "name",
        "value",
    ),
    "episode_measures": (
        "episode_id",
        "projection_digest",
        "name",
        "value",
        "unit",
    ),
}
_PROJECTION_READ_BATCH = 256


def _expected_projection_rows(
    episode: dict[str, Any],
) -> dict[str, list[tuple[Any, ...]]]:
    key = (episode["episodeId"], episode["projectionDigest"])
    anchor = episode["anchor"]
    return {
        "episode_projections": [
            key
            + (
                episode["profileId"],
                episode["dataClass"],
                anchor["ownerId"],
                anchor["objectKind"],
                anchor["objectId"],
                anchor["sourceRecordDigest"],
            )
        ],
        "episode_owner_refs": [
            key
            + (
                item["ownerId"],
                item["objectKind"],
                item["objectId"],
                item["relation"],
                item.get("digest"),
            )
            for item in episode["ownerRefs"]
        ],
        "episode_evidence_bindings": [
            key
            + (
                item["kind"],
                item["count"],
                item["setDigest"],
                item.get("totalBytes"),
                item.get("truncatedCount"),
            )
            for item in episode["evidenceBindings"]
        ],
        "episode_dimensions": [
            key + (item["name"], item["value"]) for item in episode["dimensions"]
        ],
        "episode_measures": [
            key + (item["name"], float(item["value"]), item.get("unit"))
            for item in episode["measures"]
        ],
    }


def _check_stored_projection_rows(
    conn: psycopg.Connection[Any], episodes: list[dict[str, Any]]
) -> None:
    """Compare all five native SQL projection tables to exact parsed input.

    Chunk tuple-key lookups instead of introducing an index/registry/second
    database, per-episode N+1 SQL calls, or materializing all historical
    projections. Caller already holds the transaction or reader snapshot.
    """
    for offset in range(0, len(episodes), _PROJECTION_READ_BATCH):
        batch = episodes[offset : offset + _PROJECTION_READ_BATCH]
        expected: dict[str, Counter[str]] = {
            table: Counter() for table in _PROJECTION_COLUMNS
        }
        for record in batch:
            for table, rows in _expected_projection_rows(record).items():
                expected[table].update(
                    json.dumps(row, sort_keys=True, ensure_ascii=False, allow_nan=False)
                    for row in rows
                )

        keys = [
            value
            for record in batch
            for value in (record["episodeId"], record["projectionDigest"])
        ]
        placeholders = sql.SQL(", ").join(sql.SQL("(%s, %s)") for _ in batch)
        for table, columns in _PROJECTION_COLUMNS.items():
            query = sql.SQL(
                "SELECT {} FROM {} WHERE (episode_id, projection_digest) IN ({})"
            ).format(
                sql.SQL(", ").join(map(sql.Identifier, columns)),
                sql.Identifier(table),
                placeholders,
            )
            actual = Counter(
                json.dumps(
                    tuple(row[column] for column in columns),
                    sort_keys=True,
                    ensure_ascii=False,
                    allow_nan=False,
                )
                for row in conn.execute(query, keys).fetchall()
            )
            if actual != expected[table]:
                raise EpisodeStoreError(
                    f"committed projection rows differ from source: {table}"
                )


def ingest_file(
    *,
    dsn: str,
    db_role: str | None,
    path: Path,
    corpus_id: str,
    profile_id: str,
    projection_set_digest: str,
    schema_digest: str,
    adapter_digest: str,
) -> dict[str, Any]:
    with _frozen_source(path) as (frozen, source_digest, _source_size):
        with io.TextIOWrapper(frozen, encoding="utf-8") as lines:
            episodes = _load_episodes_from_lines(lines, profile_id, path)
    ingest_id, identity = build_ingest_identity(
        corpus_id=corpus_id,
        profile_id=profile_id,
        source_file_digest=source_digest,
        projection_set_digest=projection_set_digest,
        schema_digest=schema_digest,
        adapter_digest=adapter_digest,
    )

    def replay(existing: dict[str, Any]) -> dict[str, Any]:
        expected = {
            "ingest_id": ingest_id,
            "corpus_id": corpus_id,
            "profile_id": profile_id,
            "source_file_digest": source_digest,
            "projection_set_digest": identity["projectionSetDigest"],
            "schema_digest": identity["schemaDigest"],
            "adapter_digest": identity["adapterDigest"],
            "episode_count": len(episodes),
            "standing": "PASS_IDEMPOTENT_PROJECTION_INGEST",
        }
        if any(existing[key] != value for key, value in expected.items()):
            raise EpisodeStoreError(
                "existing ingest receipt conflicts with source identity"
            )
        return {
            "ingestId": ingest_id,
            "profileId": profile_id,
            "sourceFileDigest": source_digest,
            "episodeCount": existing["episode_count"],
            "insertedProjectionCountThisRun": 0,
            "retainedOriginalInsertedProjectionCount": existing[
                "inserted_projection_count"
            ],
            "replayExistingIngest": True,
            "standing": existing["standing"],
        }

    with psycopg.connect(dsn, row_factory=dict_row) as conn, conn.transaction():
        _set_role(conn, db_role)
        existing = conn.execute(
            "SELECT * FROM projection_ingests WHERE ingest_id = %s", (ingest_id,)
        ).fetchone()
        if existing is not None:
            _check_stored_projection_rows(conn, episodes)
            return replay(existing)

        inserted = sum(_insert_episode(conn, episode) for episode in episodes)
        _check_stored_projection_rows(conn, episodes)
        standing = "PASS_IDEMPOTENT_PROJECTION_INGEST"
        admitted = conn.execute(
            """
            INSERT INTO projection_ingests(
              ingest_id, corpus_id, profile_id, source_file_digest,
              projection_set_digest, schema_digest, adapter_digest,
              episode_count, inserted_projection_count, standing
            )
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            ON CONFLICT (ingest_id) DO NOTHING
            RETURNING ingest_id
            """,
            (
                ingest_id,
                corpus_id,
                profile_id,
                source_digest,
                identity["projectionSetDigest"],
                identity["schemaDigest"],
                identity["adapterDigest"],
                len(episodes),
                inserted,
                standing,
            ),
        ).fetchone()
        if admitted is None:
            # Two writers observed no receipt concurrently. The unique index
            # waits for the winner to commit; a fresh READ COMMITTED query
            # can then inspect the winner without an application-level lock.
            winner = conn.execute(
                "SELECT * FROM projection_ingests WHERE ingest_id = %s",
                (ingest_id,),
            ).fetchone()
            if winner is None:
                raise EpisodeStoreError(
                    "concurrent ingest conflict lacks committed receipt"
                )
            _check_stored_projection_rows(conn, episodes)
            return replay(winner)

    return {
        "ingestId": ingest_id,
        "profileId": profile_id,
        "sourceFileDigest": source_digest,
        "episodeCount": len(episodes),
        "insertedProjectionCountThisRun": inserted,
        "retainedOriginalInsertedProjectionCount": inserted,
        "replayExistingIngest": False,
        "standing": standing,
    }


def read_committed_ingest_source(
    *,
    dsn: str,
    db_role: str | None,
    ingest_id: str,
    path: Path,
) -> dict[str, Any]:
    """Independently recheck one committed ingest against physical source bytes.

    PostgreSQL owns the durable ingest receipt. The caller supplies the exact
    ingest identity and explicit file; this reader never infers a storage path
    or changes the DB. An isolated DB snapshot is not a filesystem lease.
    """
    if not dsn or re.fullmatch(r"ingest:sha256:[0-9a-f]{64}", ingest_id) is None:
        raise EpisodeStoreError(
            "explicit database and exact ingest identity are required"
        )
    with psycopg.connect(dsn, row_factory=dict_row) as conn:
        conn.execute("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY")
        _set_role(conn, db_role)
        row = conn.execute(
            "SELECT * FROM projection_ingests WHERE ingest_id = %s", (ingest_id,)
        ).fetchone()
        if row is None:
            raise EpisodeStoreError("no committed projection ingest for identity")
        calculated, _ = build_ingest_identity(
            corpus_id=row["corpus_id"],
            profile_id=row["profile_id"],
            source_file_digest=row["source_file_digest"],
            projection_set_digest=row["projection_set_digest"],
            schema_digest=row["schema_digest"],
            adapter_digest=row["adapter_digest"],
        )
        if (
            calculated != ingest_id
            or row["standing"] != "PASS_IDEMPOTENT_PROJECTION_INGEST"
            or row["episode_count"] < 0
        ):
            raise EpisodeStoreError(
                "committed projection ingest identity is inconsistent"
            )
        with _frozen_source(path) as (frozen, digest, size):
            if digest != row["source_file_digest"]:
                raise EpisodeStoreError("source bytes disagree with committed ingest")
            with io.TextIOWrapper(frozen, encoding="utf-8") as lines:
                episodes = _load_episodes_from_lines(lines, row["profile_id"], path)
            if len(episodes) != row["episode_count"]:
                raise EpisodeStoreError("committed episode count disagrees with source")
            _check_stored_projection_rows(conn, episodes)
    return {
        "ingestId": ingest_id,
        "profileId": row["profile_id"],
        "sourceFileDigest": digest,
        "sourceByteLength": size,
        "episodeCount": len(episodes),
        "standing": "PASS_COMMITTED_INGEST_SOURCE_READBACK",
    }


def store_summary(dsn: str, db_role: str | None) -> dict[str, Any]:
    with psycopg.connect(dsn, row_factory=dict_row) as conn:
        _set_role(conn, db_role)
        projections = conn.execute(
            """
            SELECT profile_id, count(*) AS n
            FROM episode_projections
            GROUP BY profile_id ORDER BY profile_id
            """
        ).fetchall()
        tables = {}
        for table in (
            "episode_projections",
            "episode_owner_refs",
            "episode_evidence_bindings",
            "episode_dimensions",
            "episode_measures",
            "projection_ingests",
        ):
            tables[table] = conn.execute(
                sql.SQL("SELECT count(*) AS n FROM {}").format(sql.Identifier(table))
            ).fetchone()["n"]
        return {
            "profiles": {row["profile_id"]: row["n"] for row in projections},
            "tables": tables,
        }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)

    ingest = sub.add_parser("ingest")
    ingest.add_argument("input", type=Path)
    ingest.add_argument("--dsn", default=os.environ.get("ORDIVON_EXPERIMENTAL_DSN"))
    ingest.add_argument(
        "--db-role", default=os.environ.get("ORDIVON_EXPERIMENTAL_DB_ROLE")
    )
    ingest.add_argument("--corpus-id", required=True)
    ingest.add_argument("--profile-id", required=True)
    ingest.add_argument("--projection-set-digest", required=True)
    ingest.add_argument("--schema-digest", required=True)
    ingest.add_argument("--adapter-digest", required=True)

    readback = sub.add_parser("readback")
    readback.add_argument("input", type=Path)
    readback.add_argument("--ingest-id", required=True)
    readback.add_argument("--dsn", default=os.environ.get("ORDIVON_EXPERIMENTAL_DSN"))
    readback.add_argument(
        "--db-role", default=os.environ.get("ORDIVON_EXPERIMENTAL_DB_ROLE")
    )

    summary = sub.add_parser("summary")
    summary.add_argument("--dsn", default=os.environ.get("ORDIVON_EXPERIMENTAL_DSN"))
    summary.add_argument(
        "--db-role", default=os.environ.get("ORDIVON_EXPERIMENTAL_DB_ROLE")
    )
    return parser


def main() -> int:
    args = _parser().parse_args()
    if not args.dsn:
        raise SystemExit("set --dsn or ORDIVON_EXPERIMENTAL_DSN")
    if args.command == "readback":
        result = read_committed_ingest_source(
            dsn=args.dsn,
            db_role=args.db_role,
            ingest_id=args.ingest_id,
            path=args.input,
        )
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0
    if args.command == "summary":
        print(
            json.dumps(store_summary(args.dsn, args.db_role), indent=2, sort_keys=True)
        )
        return 0
    result = ingest_file(
        dsn=args.dsn,
        db_role=args.db_role,
        path=args.input,
        corpus_id=args.corpus_id,
        profile_id=args.profile_id,
        projection_set_digest=args.projection_set_digest,
        schema_digest=args.schema_digest,
        adapter_digest=args.adapter_digest,
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
