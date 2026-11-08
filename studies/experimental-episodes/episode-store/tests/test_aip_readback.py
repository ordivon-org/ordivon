"""AIP file restoration: explicit exact archive -> native 7z -> PG consumer.

Local 7z archives are SYNTHETIC fixtures. Only a separately observed
Archivematica Storage Service download can establish real provider provenance.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
from pathlib import Path
from unittest.mock import patch
from uuid import uuid4

import psycopg
import pytest
from test_committed_ingest_readback import admit, populated_input
from test_ingest_contract import episode

from ordivon_experimental_episode_store.aip_readback import (
    _exact_object_entry,
    read_archived_episode_source,
)
from ordivon_experimental_episode_store.ingest import EpisodeStoreError


@pytest.fixture
def pg_dsn() -> str:
    dsn = os.environ.get("ORDIVON_EPISODE_PG_TEST_DSN")
    if not dsn:
        pytest.skip("disposable Episode PostgreSQL test DSN is required")
    with psycopg.connect(dsn) as conn:
        if (
            conn.execute("SELECT current_database()").fetchone()[0]
            != "ordivon_episode_test"
        ):
            raise ValueError("only disposable ordivon_episode_test is allowed")
    return dsn


UUID = "00000000-0000-4000-8000-000000000001"
SOURCE_ENTRY = f"synthetic-aip-{UUID}/data/objects/episode-source.jsonl"


@pytest.fixture
def native_7z() -> str:
    executable = shutil.which("7z")
    if executable is None:
        pytest.skip("upstream 7z is required for native archive acceptance")
    return executable


def synthetic_archive(
    tmp_path: Path, native_7z: str, *, source: bytes | None = None
) -> tuple[Path, str]:
    root = tmp_path / f"synthetic-aip-{UUID}"
    object_dir = root / "data" / "objects"
    object_dir.mkdir(parents=True)
    if source is None:
        source = (json.dumps(episode(), sort_keys=True) + "\n").encode()
    (object_dir / "episode-source.jsonl").write_bytes(source)
    archive = tmp_path / "synthetic-test-only.7z"
    subprocess.run(
        [native_7z, "a", "-t7z", "-bso0", "-bsp0", str(archive), root.name],
        cwd=tmp_path,
        capture_output=True,
        check=True,
        timeout=25,
    )
    return archive, "sha256:" + hashlib.sha256(archive.read_bytes()).hexdigest()


def test_exact_aip_source_readback_uses_recovered_file(
    tmp_path: Path, native_7z: str
) -> None:
    source = (json.dumps(episode(), sort_keys=True) + "\n").encode()
    archive, digest = synthetic_archive(tmp_path, native_7z, source=source)
    ingest_id = "ingest:sha256:" + "a" * 64

    def consumer(*, dsn, db_role, ingest_id, path):
        assert dsn == "isolated-test-DSN"
        assert db_role is None
        assert path.read_bytes() == source
        assert ingest_id == "ingest:sha256:" + "a" * 64
        return {
            "ingestId": ingest_id,
            "sourceFileDigest": "sha256:" + hashlib.sha256(source).hexdigest(),
            "sourceByteLength": len(source),
            "episodeCount": 1,
        }

    with patch(
        "ordivon_experimental_episode_store.aip_readback.read_committed_ingest_source",
        side_effect=consumer,
    ) as consumer_call:
        result = read_archived_episode_source(
            archive=archive,
            aip_uuid=UUID,
            package_digest=digest,
            source_entry=SOURCE_ENTRY,
            ingest_id=ingest_id,
            dsn="isolated-test-DSN",
        )
    consumer_call.assert_called_once()
    assert result["standing"] == "PASS_EXPLICIT_ARCHIVE_AND_COMMITTED_PG_READBACK"
    assert result["sourceFileDigest"] == "sha256:" + hashlib.sha256(source).hexdigest()
    assert result["episodeCount"] == 1
    assert result["providerStorageStanding"] == "UNKNOWN_NOT_OBSERVED"
    assert result["retentionOrGcAuthorized"] is False


@pytest.mark.parametrize(
    "entry",
    [
        "/data/objects/episode-source.jsonl",
        "../data/objects/episode-source.jsonl",
        "wrong-00000000-0000-4000-8000-000000000002/data/objects/episode-source.jsonl",
        f"synthetic-aip-{UUID}/data/objects/../episode-source.jsonl",
        f"synthetic-aip-{UUID}/data/objects/*.jsonl",
        f"synthetic-aip-{UUID}/other/objects/episode-source.jsonl",
        f"synthetic-aip-{UUID}\\data\\objects\\episode-source.jsonl",
    ],
)
def test_invalid_or_ambiguous_archive_entry_rejected(entry: str) -> None:
    with pytest.raises(EpisodeStoreError, match="exact original-file path"):
        _exact_object_entry(UUID, entry)


def test_aip_package_digest_mismatch_is_fail_closed(
    tmp_path: Path, native_7z: str
) -> None:
    archive, _ = synthetic_archive(tmp_path, native_7z)
    with patch(
        "ordivon_experimental_episode_store.aip_readback.read_committed_ingest_source"
    ) as pg:
        with pytest.raises(EpisodeStoreError, match="package bytes differ"):
            read_archived_episode_source(
                archive=archive,
                aip_uuid=UUID,
                package_digest="sha256:" + "0" * 64,
                source_entry=SOURCE_ENTRY,
                ingest_id="ingest:sha256:" + "1" * 64,
                dsn="unused-test",
            )
    pg.assert_not_called()


def test_archive_missing_exact_source_entry_is_rejected(
    tmp_path: Path, native_7z: str
) -> None:
    archive, digest = synthetic_archive(tmp_path, native_7z)
    with pytest.raises(EpisodeStoreError, match="exactly one"):
        read_archived_episode_source(
            archive=archive,
            aip_uuid=UUID,
            package_digest=digest,
            source_entry=f"synthetic-aip-{UUID}/data/objects/not-present.jsonl",
            ingest_id="ingest:sha256:" + "1" * 64,
            dsn="unused-test",
        )


def test_wrong_source_bytes_rejected_by_native_consumer(
    tmp_path: Path, native_7z: str
) -> None:
    archive, digest = synthetic_archive(tmp_path, native_7z)
    with patch(
        "ordivon_experimental_episode_store.aip_readback.read_committed_ingest_source",
        side_effect=EpisodeStoreError("source bytes disagree with committed ingest"),
    ):
        with pytest.raises(EpisodeStoreError, match="source bytes disagree"):
            read_archived_episode_source(
                archive=archive,
                aip_uuid=UUID,
                package_digest=digest,
                source_entry=SOURCE_ENTRY,
                ingest_id="ingest:sha256:" + "1" * 64,
                dsn="test",
            )


def test_missing_native_7z_is_not_a_pass(tmp_path: Path, native_7z: str) -> None:
    archive, digest = synthetic_archive(tmp_path, native_7z)
    with patch(
        "ordivon_experimental_episode_store.aip_readback.shutil.which",
        return_value=None,
    ):
        with pytest.raises(EpisodeStoreError, match="upstream 7z executable"):
            read_archived_episode_source(
                archive=archive,
                aip_uuid=UUID,
                package_digest=digest,
                source_entry=SOURCE_ENTRY,
                ingest_id="ingest:sha256:" + "1" * 64,
                dsn="unused-test",
            )


def test_synthetic_archive_roundtrips_through_real_pg_readback(
    pg_dsn: str, tmp_path: Path, native_7z: str
) -> None:
    """The native PG reader is real; the 7z is deliberately NOT an AIP receipt."""
    source = populated_input(tmp_path, "input.jsonl")
    receipt = admit(
        pg_dsn, source, corpus="synthetic-archival-acceptance-" + uuid4().hex
    )
    archive, sha = synthetic_archive(tmp_path, native_7z, source=source.read_bytes())
    accepted = read_archived_episode_source(
        archive=archive,
        aip_uuid=UUID,
        package_digest=sha,
        source_entry=SOURCE_ENTRY,
        ingest_id=receipt["ingestId"],
        dsn=pg_dsn,
    )
    assert accepted["sourceFileDigest"] == receipt["sourceFileDigest"]
    assert accepted["episodeCount"] == 1
    assert accepted["providerStorageStanding"] == "UNKNOWN_NOT_OBSERVED"
    with psycopg.connect(pg_dsn) as conn:
        record = json.loads(source.read_text())
        conn.execute(
            "UPDATE episode_measures SET value = 900 "
            "WHERE episode_id = %s AND projection_digest = %s",
            (record["episodeId"], record["projectionDigest"]),
        )
    with pytest.raises(EpisodeStoreError, match="episode_measures"):
        read_archived_episode_source(
            archive=archive,
            aip_uuid=UUID,
            package_digest=sha,
            source_entry=SOURCE_ENTRY,
            ingest_id=receipt["ingestId"],
            dsn=pg_dsn,
        )


def test_archive_path_swap_after_descriptor_snapshot_cannot_redirect_7z(
    tmp_path: Path, native_7z: str
) -> None:
    original = (json.dumps(episode(), sort_keys=True) + "\n").encode()
    archive, digest = synthetic_archive(tmp_path, native_7z, source=original)
    native_list = __import__(
        "ordivon_experimental_episode_store.aip_readback",
        fromlist=["_list_exact_entry"],
    )._list_exact_entry

    def replace_path_after_frozen_fd(fd, entry, *, max_bytes):
        archive.rename(tmp_path / "previous-good.7z")
        archive.write_bytes(b"replaced pathname contents, not a real archive")
        return native_list(fd, entry, max_bytes=max_bytes)

    def consumer(*, path, ingest_id, **_kwargs):
        assert path.read_bytes() == original
        return {
            "ingestId": ingest_id,
            "sourceFileDigest": "sha256:" + hashlib.sha256(original).hexdigest(),
            "sourceByteLength": len(original),
            "episodeCount": 1,
        }

    with (
        patch(
            "ordivon_experimental_episode_store.aip_readback._list_exact_entry",
            side_effect=replace_path_after_frozen_fd,
        ),
        patch(
            "ordivon_experimental_episode_store.aip_readback.read_committed_ingest_source",
            side_effect=consumer,
        ),
    ):
        result = read_archived_episode_source(
            archive=archive,
            aip_uuid=UUID,
            package_digest=digest,
            source_entry=SOURCE_ENTRY,
            ingest_id="ingest:sha256:" + "a" * 64,
            dsn="mock-pg-consumer",
        )
    assert (
        result["sourceFileDigest"] == "sha256:" + hashlib.sha256(original).hexdigest()
    )
    assert archive.read_bytes() == b"replaced pathname contents, not a real archive"


def test_oversized_declared_archive_entry_denied_without_pg(
    tmp_path: Path, native_7z: str
) -> None:
    archive, sha = synthetic_archive(tmp_path, native_7z)
    with (
        patch(
            "ordivon_experimental_episode_store.aip_readback._MAX_SOURCE_BYTES",
            1,
        ),
        patch(
            "ordivon_experimental_episode_store.aip_readback.read_committed_ingest_source"
        ) as consumer,
    ):
        with pytest.raises(EpisodeStoreError, match="exceeds bounded source size"):
            read_archived_episode_source(
                archive=archive,
                aip_uuid=UUID,
                package_digest=sha,
                source_entry=SOURCE_ENTRY,
                ingest_id="ingest:sha256:" + "b" * 64,
                dsn="mock-pg-consumer",
            )
        consumer.assert_not_called()
