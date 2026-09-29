from __future__ import annotations

import json

import pytest

from ordivon_experimental_episode_store.ingest import (
    EpisodeStoreError,
    _load_episodes,
    build_ingest_identity,
)


def sha(char: str) -> str:
    return "sha256:" + char * 64


def episode(profile: str = "runtime-r5c-v1") -> dict:
    return {
        "schemaVersion": 1,
        "kind": "ordivon.experimental-episode-binding",
        "profileId": profile,
        "episodeId": "episode:1",
        "dataClass": "EXPERIENCE",
        "anchor": {
            "ownerId": "runtime",
            "objectKind": "execution",
            "objectId": "execution:1",
            "sourceRecordDigest": sha("a"),
        },
        "ownerRefs": [],
        "evidenceBindings": [],
        "dimensions": [],
        "measures": [],
        "unresolved": [],
        "nonClaims": ["not owner truth"],
        "projectionDigest": sha("b"),
    }


def test_ingest_identity_is_deterministic_and_profile_bound() -> None:
    args = {
        "corpus_id": "corpus-r1",
        "profile_id": "runtime-r5c-v1",
        "source_file_digest": sha("1"),
        "projection_set_digest": sha("2"),
        "schema_digest": sha("3"),
        "adapter_digest": sha("4"),
    }
    first = build_ingest_identity(**args)
    second = build_ingest_identity(**args)
    assert first == second

    changed = dict(args)
    changed["profile_id"] = "harness-rsi-acceptance-v1"
    assert build_ingest_identity(**changed)[0] != first[0]


def test_load_rejects_profile_mismatch(tmp_path) -> None:
    path = tmp_path / "episodes.jsonl"
    path.write_text(json.dumps(episode("wrong")) + "\n", encoding="utf-8")
    with pytest.raises(EpisodeStoreError, match="profileId"):
        _load_episodes(path, "runtime-r5c-v1")


def test_load_rejects_duplicate_projection_identity(tmp_path) -> None:
    path = tmp_path / "episodes.jsonl"
    value = episode()
    path.write_text(
        json.dumps(value) + "\n" + json.dumps(value) + "\n", encoding="utf-8"
    )
    with pytest.raises(EpisodeStoreError, match="duplicate"):
        _load_episodes(path, "runtime-r5c-v1")


def test_ingest_identity_rejects_fake_digest() -> None:
    with pytest.raises(EpisodeStoreError, match="sha256"):
        build_ingest_identity(
            corpus_id="c",
            profile_id="p",
            source_file_digest="opaque",
            projection_set_digest=sha("2"),
            schema_digest=sha("3"),
            adapter_digest=sha("4"),
        )
