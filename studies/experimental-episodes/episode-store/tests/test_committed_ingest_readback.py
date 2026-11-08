"""Source bytes -> PostgreSQL receipt -> exact consumer file readback.

PG tests require a dedicated disposable database named ordivon_episode_test.
They never create schema or migrate: invoke Alembic before running them.
"""

from __future__ import annotations

import hashlib
import json
import os
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from queue import Empty, Queue
from threading import Barrier, Event
from unittest.mock import patch
from uuid import uuid4

import psycopg
import pytest
from test_ingest_contract import episode, sha

from ordivon_experimental_episode_store import ingest
from ordivon_experimental_episode_store.ingest import (
    EpisodeStoreError,
    _frozen_source,
    ingest_file,
    read_committed_ingest_source,
)


@pytest.fixture
def pg_dsn() -> str:
    dsn = os.environ.get("ORDIVON_EPISODE_PG_TEST_DSN")
    if not dsn:
        pytest.skip("separate disposable Episode PostgreSQL test DSN is required")
    with psycopg.connect(dsn) as conn:
        dbname = conn.execute("SELECT current_database()").fetchone()[0]
        if dbname != "ordivon_episode_test":
            raise ValueError(
                "PG tests require a dedicated disposable ordivon_episode_test DB"
            )
        assert (
            conn.execute("SELECT to_regclass('projection_ingests')").fetchone()[0]
            is not None
        ), "Alembic migration required"
    return dsn


def input_file(tmp_path: Path, name: str) -> Path:
    path = tmp_path / name
    item = episode()
    item["episodeId"] = "episode:test:" + uuid4().hex
    path.write_text(json.dumps(item, sort_keys=True) + "\n", encoding="utf-8")
    return path


def admit(dsn: str, path: Path, *, corpus: str = "test-corpus") -> dict:
    return ingest_file(
        dsn=dsn,
        db_role=None,
        path=path,
        corpus_id=corpus,
        profile_id="runtime-r5c-v1",
        projection_set_digest=sha("1"),
        schema_digest=sha("2"),
        adapter_digest=sha("3"),
    )


def readback(dsn: str, receipt: dict, path: Path) -> dict:
    return read_committed_ingest_source(
        dsn=dsn, db_role=None, ingest_id=receipt["ingestId"], path=path
    )


def test_frozen_source_is_same_bytes_even_after_path_replacement(
    tmp_path: Path,
) -> None:
    first = input_file(tmp_path, "episodes.jsonl")
    original = first.read_bytes()
    with _frozen_source(first) as (stream, digest, size):
        first.rename(tmp_path / "old.jsonl")
        first.write_bytes(b"replacement\n")
        assert stream.read() == original
        assert digest == "sha256:" + hashlib.sha256(original).hexdigest()
        assert size == len(original)
    assert first.read_bytes() == b"replacement\n"


def test_frozen_source_rejects_symlink(tmp_path: Path) -> None:
    first = input_file(tmp_path, "episodes.jsonl")
    symlink = tmp_path / "latest.jsonl"
    symlink.symlink_to(first)
    with pytest.raises(OSError):
        with _frozen_source(symlink):
            pytest.fail("a symlink must not be frozen")


def test_pg_ingest_replay_and_committed_file_tampering(
    pg_dsn: str, tmp_path: Path
) -> None:
    path = input_file(tmp_path, "source.jsonl")
    accepted = admit(pg_dsn, path, corpus=tmp_path.name)
    assert accepted["episodeCount"] == 1
    assert accepted["replayExistingIngest"] is False
    observed = readback(pg_dsn, accepted, path)
    assert observed["standing"] == "PASS_COMMITTED_INGEST_SOURCE_READBACK"
    assert observed["sourceFileDigest"] == accepted["sourceFileDigest"]
    assert observed["episodeCount"] == 1
    assert observed["sourceByteLength"] == len(path.read_bytes())
    replay = admit(pg_dsn, path, corpus=tmp_path.name)
    assert replay["ingestId"] == accepted["ingestId"]
    assert replay["replayExistingIngest"] is True
    assert readback(pg_dsn, replay, path) == observed

    path.write_text(json.dumps(episode(), indent=2), encoding="utf-8")
    with pytest.raises(EpisodeStoreError, match="source bytes disagree"):
        readback(pg_dsn, accepted, path)
    with pytest.raises(EpisodeStoreError, match="no committed"):
        read_committed_ingest_source(
            dsn=pg_dsn, db_role=None, ingest_id="ingest:" + sha("0"), path=path
        )


def test_pg_commit_reads_frozen_original_after_source_path_swap(
    pg_dsn: str, tmp_path: Path
) -> None:
    """The real ingest cannot hash new path bytes after parsing old bytes."""
    path = input_file(tmp_path, "path.jsonl")
    original = path.read_bytes()
    original_parser = ingest._load_episodes_from_lines
    swapped = False

    def swap_after_frozen_parse(handle, profile_id, label):
        nonlocal swapped
        records = original_parser(handle, profile_id, label)
        path.rename(tmp_path / "original.jsonl")
        path.write_bytes(b"external file replaced between parse and commit")
        swapped = True
        return records

    with patch.object(ingest, "_load_episodes_from_lines", swap_after_frozen_parse):
        receipt = admit(pg_dsn, path, corpus=tmp_path.name + "-swap")
    assert swapped
    assert (
        receipt["sourceFileDigest"] == "sha256:" + hashlib.sha256(original).hexdigest()
    )
    assert (
        readback(pg_dsn, receipt, tmp_path / "original.jsonl")["sourceFileDigest"]
        == receipt["sourceFileDigest"]
    )
    with pytest.raises(EpisodeStoreError, match="source bytes disagree"):
        readback(pg_dsn, receipt, path)


def test_pg_uncommitted_ingest_is_invisible_then_visible(
    pg_dsn: str, tmp_path: Path
) -> None:
    path = input_file(tmp_path, "held.jsonl")
    entered = Event()
    release = Event()
    original_insert = ingest._insert_episode

    def hold_after_insert(db, record):
        result = original_insert(db, record)
        entered.set()
        if not release.wait(timeout=20):
            raise TimeoutError("uncommitted ingest barrier not released")
        return result

    # Exact identity is calculated solely from the source and explicit args,
    # independent of whether PostgreSQL has accepted the transaction.
    digest = "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()
    identity, _ = ingest.build_ingest_identity(
        corpus_id=tmp_path.name + "-held",
        profile_id="runtime-r5c-v1",
        source_file_digest=digest,
        projection_set_digest=sha("1"),
        schema_digest=sha("2"),
        adapter_digest=sha("3"),
    )
    with patch.object(ingest, "_insert_episode", hold_after_insert):
        with ThreadPoolExecutor(max_workers=1) as pool:
            future = pool.submit(admit, pg_dsn, path, corpus=tmp_path.name + "-held")
            try:
                assert entered.wait(timeout=20)
                with pytest.raises(EpisodeStoreError, match="no committed"):
                    read_committed_ingest_source(
                        dsn=pg_dsn, db_role=None, ingest_id=identity, path=path
                    )
            finally:
                release.set()
            receipt = future.result(timeout=30)
    assert readback(pg_dsn, receipt, path)["ingestId"] == identity


def test_pg_writer_abort_before_commit_cannot_publish_partial_ingest(
    pg_dsn: str, tmp_path: Path
) -> None:
    path = input_file(tmp_path, "crash.jsonl")
    digest = "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()
    identity, _ = ingest.build_ingest_identity(
        corpus_id=tmp_path.name + "-crash",
        profile_id="runtime-r5c-v1",
        source_file_digest=digest,
        projection_set_digest=sha("1"),
        schema_digest=sha("2"),
        adapter_digest=sha("3"),
    )
    pid_queue: Queue[int] = Queue(maxsize=1)
    release = Event()
    original_insert = ingest._insert_episode

    def hold_before_commit(db, record):
        result = original_insert(db, record)
        pid_queue.put(
            db.execute("SELECT pg_backend_pid() AS writer_pid").fetchone()["writer_pid"]
        )
        if not release.wait(timeout=20):
            raise TimeoutError("crash witness barrier not released")
        return result

    with patch.object(ingest, "_insert_episode", hold_before_commit):
        with ThreadPoolExecutor(max_workers=1) as pool:
            future = pool.submit(admit, pg_dsn, path, corpus=tmp_path.name + "-crash")
            try:
                try:
                    writer_pid = pid_queue.get(timeout=12)
                except Empty:
                    # Surface the producer's real exception rather than
                    # attributing it to a deadlocked/slow PostgreSQL barrier.
                    if future.done():
                        future.result()
                    raise
                with psycopg.connect(pg_dsn) as supervisor:
                    assert supervisor.execute(
                        "SELECT pg_terminate_backend(%s)", (writer_pid,)
                    ).fetchone() == (True,)
            finally:
                release.set()
            with pytest.raises(psycopg.Error):
                future.result(timeout=30)
    with pytest.raises(EpisodeStoreError, match="no committed"):
        read_committed_ingest_source(
            dsn=pg_dsn, db_role=None, ingest_id=identity, path=path
        )
    receipt = admit(pg_dsn, path, corpus=tmp_path.name + "-crash")
    assert receipt["ingestId"] == identity
    assert readback(pg_dsn, receipt, path)["episodeCount"] == 1


def test_readback_rejects_counterfeit_pg_row_identity(
    pg_dsn: str, tmp_path: Path
) -> None:
    path = input_file(tmp_path, "tamper.jsonl")
    receipt = admit(pg_dsn, path, corpus=tmp_path.name + "-tamper")
    with psycopg.connect(pg_dsn) as conn:
        conn.execute(
            "UPDATE projection_ingests SET source_file_digest = %s "
            "WHERE ingest_id = %s",
            (sha("0"), receipt["ingestId"]),
        )
    with pytest.raises(EpisodeStoreError, match="identity is inconsistent"):
        readback(pg_dsn, receipt, path)


def test_two_writers_same_immutable_ingest_share_one_durable_receipt(
    pg_dsn: str, tmp_path: Path
) -> None:
    """Deterministic race: both writers observed no row before either inserts."""
    source = input_file(tmp_path, "same.jsonl")
    corpus = tmp_path.name + "-simultaneous"
    entered = Barrier(2)
    original_insert = ingest._insert_episode

    def join_after_both_miss_existing(db, record):
        entered.wait(timeout=20)
        return original_insert(db, record)

    with patch.object(ingest, "_insert_episode", join_after_both_miss_existing):
        with ThreadPoolExecutor(max_workers=2) as pool:
            jobs = [pool.submit(admit, pg_dsn, source, corpus=corpus) for _ in range(2)]
            results = [job.result(timeout=30) for job in jobs]
    assert len({receipt["ingestId"] for receipt in results}) == 1
    assert sorted(receipt["replayExistingIngest"] for receipt in results) == [
        False,
        True,
    ]
    assert len({receipt["sourceFileDigest"] for receipt in results}) == 1
    assert readback(pg_dsn, results[0], source)["standing"] == (
        "PASS_COMMITTED_INGEST_SOURCE_READBACK"
    )


def test_readback_without_exact_ingest_identity_does_not_open_database() -> None:
    with pytest.raises(EpisodeStoreError, match="exact ingest identity"):
        read_committed_ingest_source(
            dsn="",
            db_role=None,
            ingest_id="ingest:sha256:not-an-object",
            path=Path("/unavailable"),
        )


def test_pg_replay_rejects_counterfeit_existing_receipt(
    pg_dsn: str, tmp_path: Path
) -> None:
    path = input_file(tmp_path, "counterfeit.jsonl")
    corpus = tmp_path.name + "-counterfeit-replay"
    receipt = admit(pg_dsn, path, corpus=corpus)
    with psycopg.connect(pg_dsn) as db:
        db.execute(
            "UPDATE projection_ingests SET projection_set_digest = %s "
            "WHERE ingest_id = %s",
            (sha("0"), receipt["ingestId"]),
        )
    with pytest.raises(EpisodeStoreError, match="existing ingest receipt conflicts"):
        admit(pg_dsn, path, corpus=corpus)


def test_distinct_committed_byte_versions_coexist_without_replacing_prior_reader(
    pg_dsn: str, tmp_path: Path
) -> None:
    """Version N+1 does not erase the content-addressed N+0 receipt."""
    prior = input_file(tmp_path, "version1.jsonl")
    current = tmp_path / "version2.jsonl"
    corpus = tmp_path.name + "-two-source-versions"
    first = admit(pg_dsn, prior, corpus=corpus)
    updated = json.loads(prior.read_text(encoding="utf-8"))
    updated["episodeId"] = "episode:test:" + uuid4().hex
    current.write_text(json.dumps(updated, sort_keys=True) + "\n", encoding="utf-8")
    second = admit(pg_dsn, current, corpus=corpus)
    assert first["ingestId"] != second["ingestId"]
    assert first["sourceFileDigest"] != second["sourceFileDigest"]
    assert (
        readback(pg_dsn, first, prior)["sourceFileDigest"] == first["sourceFileDigest"]
    )
    assert (
        readback(pg_dsn, second, current)["sourceFileDigest"]
        == second["sourceFileDigest"]
    )
    with psycopg.connect(pg_dsn) as conn:
        assert (
            conn.execute(
                "SELECT count(*) FROM projection_ingests WHERE ingest_id = ANY(%s)",
                ([first["ingestId"], second["ingestId"]],),
            ).fetchone()[0]
            == 2
        )


def populated_input(tmp_path: Path, name: str) -> Path:
    source = input_file(tmp_path, name)
    item = json.loads(source.read_text(encoding="utf-8"))
    item["ownerRefs"] = [
        {
            "ownerId": "runtime",
            "objectKind": "event",
            "objectId": "event:test",
            "relation": "produced-by",
            "digest": sha("e"),
        }
    ]
    item["evidenceBindings"] = [
        {
            "kind": "artifact",
            "count": 3,
            "setDigest": sha("c"),
            "totalBytes": 91,
            "truncatedCount": 0,
        }
    ]
    item["dimensions"] = [{"name": "settings", "value": {"list": [1, "two"]}}]
    item["measures"] = [{"name": "cost", "value": 2.5, "unit": "seconds"}]
    source.write_text(json.dumps(item, sort_keys=True) + "\n", encoding="utf-8")
    return source


@pytest.mark.parametrize(
    ("table", "mutation"),
    [
        (
            "episode_projections",
            "UPDATE episode_projections SET data_class = 'DERIVED' "
            "WHERE episode_id = %s AND projection_digest = %s",
        ),
        (
            "episode_owner_refs",
            "UPDATE episode_owner_refs SET relation = 'tampered' "
            "WHERE episode_id = %s AND projection_digest = %s",
        ),
        (
            "episode_evidence_bindings",
            "UPDATE episode_evidence_bindings SET evidence_count = 17 "
            "WHERE episode_id = %s AND projection_digest = %s",
        ),
        (
            "episode_dimensions",
            "UPDATE episode_dimensions SET value = '{\"changed\": true}'::jsonb "
            "WHERE episode_id = %s AND projection_digest = %s",
        ),
        (
            "episode_measures",
            "UPDATE episode_measures SET value = 17 "
            "WHERE episode_id = %s AND projection_digest = %s",
        ),
    ],
)
def test_pg_readback_rejects_modified_projection_table(
    pg_dsn: str, tmp_path: Path, table: str, mutation: str
) -> None:
    path = populated_input(tmp_path, "all-projection-tables.jsonl")
    accepted = admit(pg_dsn, path, corpus=tmp_path.name)
    assert readback(pg_dsn, accepted, path)["episodeCount"] == 1
    episode_row = json.loads(path.read_text(encoding="utf-8"))
    with psycopg.connect(pg_dsn) as conn:
        changed = conn.execute(
            mutation,
            (episode_row["episodeId"], episode_row["projectionDigest"]),
        )
        assert changed.rowcount == 1
    with pytest.raises(EpisodeStoreError, match=f"projection rows differ.*{table}"):
        readback(pg_dsn, accepted, path)
    # No incomplete/changed projection may be mislabeled a successful
    # idempotent replay of a previously accepted logical ingest.
    with pytest.raises(EpisodeStoreError, match=f"projection rows differ.*{table}"):
        admit(pg_dsn, path, corpus=tmp_path.name)


def test_pg_refuses_different_payload_under_existing_projection_identity(
    pg_dsn: str, tmp_path: Path
) -> None:
    original = populated_input(tmp_path, "v1.jsonl")
    corpus = "projection-conflict:" + uuid4().hex
    first = admit(pg_dsn, original, corpus=corpus)
    record = json.loads(original.read_text(encoding="utf-8"))
    # The source file differs, yet declares an already occupied logical
    # episode_id + projection_digest. No alternative payload may be accepted.
    record["dataClass"] = "DERIVED"
    alternate = tmp_path / "v2.jsonl"
    alternate.write_text(json.dumps(record, sort_keys=True) + "\n", encoding="utf-8")
    assert (
        hashlib.sha256(original.read_bytes()).digest()
        != hashlib.sha256(alternate.read_bytes()).digest()
    )
    with pytest.raises(EpisodeStoreError, match="episode_projections"):
        admit(pg_dsn, alternate, corpus=corpus)
    assert readback(pg_dsn, first, original)["episodeCount"] == 1
    with psycopg.connect(pg_dsn) as conn:
        count = conn.execute(
            "SELECT count(*) FROM projection_ingests WHERE corpus_id = %s",
            (corpus,),
        ).fetchone()[0]
        assert count == 1


def test_pg_exact_projection_readback_batches_large_corpus(
    pg_dsn: str, tmp_path: Path
) -> None:
    source = populated_input(tmp_path, "batch.jsonl")
    prototype = json.loads(source.read_text(encoding="utf-8"))
    prefix = uuid4().hex
    with source.open("w", encoding="utf-8") as stream:
        for index in range(513):
            record = dict(prototype)
            record["episodeId"] = f"episode:batch:{prefix}:{index}"
            stream.write(json.dumps(record, sort_keys=True) + "\n")
    receipt = admit(pg_dsn, source, corpus=tmp_path.name)
    assert receipt["episodeCount"] == 513
    assert readback(pg_dsn, receipt, source)["episodeCount"] == 513


def test_repeatable_read_keeps_old_projection_snapshot_then_detects_mutation(
    pg_dsn: str, tmp_path: Path
) -> None:
    source = populated_input(tmp_path, "snapshot.jsonl")
    receipt = admit(pg_dsn, source, corpus=tmp_path.name)
    record = json.loads(source.read_text(encoding="utf-8"))
    at_verification = Event()
    resume = Event()
    real_check = ingest._check_stored_projection_rows

    def hold_after_receipt_read(db, records):
        at_verification.set()
        if not resume.wait(timeout=20):
            raise TimeoutError("consumer transaction snapshot barrier timed out")
        return real_check(db, records)

    with patch.object(ingest, "_check_stored_projection_rows", hold_after_receipt_read):
        with ThreadPoolExecutor(max_workers=1) as pool:
            future = pool.submit(readback, pg_dsn, receipt, source)
            try:
                assert at_verification.wait(timeout=20)
                with psycopg.connect(pg_dsn) as writer:
                    writer.execute(
                        "UPDATE episode_measures SET value = 100.0 "
                        "WHERE episode_id = %s AND projection_digest = %s",
                        (record["episodeId"], record["projectionDigest"]),
                    )
            finally:
                resume.set()
            assert future.result(timeout=30)["episodeCount"] == 1

    with pytest.raises(EpisodeStoreError, match="episode_measures"):
        readback(pg_dsn, receipt, source)


@pytest.mark.parametrize(
    ("mutation", "expected_table"),
    [
        (
            "DELETE FROM episode_measures WHERE episode_id = %s "
            "AND projection_digest = %s",
            "episode_measures",
        ),
        (
            "INSERT INTO episode_dimensions "
            "(episode_id, projection_digest, name, value) "
            "VALUES (%s, %s, 'unexpected', '{\"extra\": true}'::jsonb)",
            "episode_dimensions",
        ),
    ],
)
def test_pg_source_readback_rejects_missing_or_extra_projected_rows(
    pg_dsn: str, tmp_path: Path, mutation: str, expected_table: str
) -> None:
    file = populated_input(tmp_path, "exact-multiset.jsonl")
    receipt = admit(pg_dsn, file, corpus=tmp_path.name)
    source = json.loads(file.read_text(encoding="utf-8"))
    with psycopg.connect(pg_dsn) as conn:
        changed = conn.execute(
            mutation, (source["episodeId"], source["projectionDigest"])
        )
        assert changed.rowcount == 1
    with pytest.raises(EpisodeStoreError, match=expected_table):
        readback(pg_dsn, receipt, file)
    with pytest.raises(EpisodeStoreError, match=expected_table):
        admit(pg_dsn, file, corpus=tmp_path.name)
