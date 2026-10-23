from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
from pathlib import Path
from typing import Any

import psycopg
from psycopg import sql
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb

SHA256_RE = re.compile(r"^sha256:[0-9a-f]{64}$")


class EpisodeStoreError(ValueError):
    pass


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return "sha256:" + digest.hexdigest()


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


def _load_episodes(path: Path, profile_id: str) -> list[dict[str, Any]]:
    episodes: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            value = json.loads(line)
            if not isinstance(value, dict):
                raise EpisodeStoreError(f"{path}:{line_number}: root must be object")
            if value.get("kind") != "ordivon.experimental-episode-binding":
                raise EpisodeStoreError(f"{path}:{line_number}: unexpected kind")
            if value.get("profileId") != profile_id:
                raise EpisodeStoreError(
                    f"{path}:{line_number}: profileId does not match {profile_id}"
                )
            episode_id = value.get("episodeId")
            projection_digest = value.get("projectionDigest")
            if not isinstance(episode_id, str) or not episode_id:
                raise EpisodeStoreError(f"{path}:{line_number}: invalid episodeId")
            if not isinstance(projection_digest, str):
                raise EpisodeStoreError(
                    f"{path}:{line_number}: missing projectionDigest"
                )
            _require_sha256(projection_digest, "projectionDigest")
            key = (episode_id, projection_digest)
            if key in seen:
                raise EpisodeStoreError(
                    f"{path}:{line_number}: duplicate episode/projection identity"
                )
            seen.add(key)
            episodes.append(value)
    return episodes


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
    episodes = _load_episodes(path, profile_id)
    source_digest = _sha256_file(path)
    ingest_id, identity = build_ingest_identity(
        corpus_id=corpus_id,
        profile_id=profile_id,
        source_file_digest=source_digest,
        projection_set_digest=projection_set_digest,
        schema_digest=schema_digest,
        adapter_digest=adapter_digest,
    )

    with psycopg.connect(dsn, row_factory=dict_row) as conn, conn.transaction():
        _set_role(conn, db_role)
        existing = conn.execute(
            "SELECT * FROM projection_ingests WHERE ingest_id = %s", (ingest_id,)
        ).fetchone()
        if existing is not None:
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

        inserted = sum(_insert_episode(conn, episode) for episode in episodes)
        standing = "PASS_IDEMPOTENT_PROJECTION_INGEST"
        conn.execute(
            """
            INSERT INTO projection_ingests(
              ingest_id, corpus_id, profile_id, source_file_digest,
              projection_set_digest, schema_digest, adapter_digest,
              episode_count, inserted_projection_count, standing
            )
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
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
        )

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
