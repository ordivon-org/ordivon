"""Legacy Artifact JSON digest is one behavioral contract, not six new providers.

The previous local-Main implementation imported a subsequently retired
artifact_core.contracts.canonical_sha256.  Keep the published byte-level digest
contract independently verified without reintroducing that dead dependency.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import random
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
CONSUMERS = {
    "artifact_aseprite": "canonical",
    "artifact_design3d": "canonical",
    "artifact_message": "canon",
    "artifact_ogg_vorbis": "canonical",
    "artifact_software_release_elf": "canonical",
    "artifact_web_archive": "canon",
}
PAYLOADS = [
    {},
    {"z": 0, "a": [True, None, "汉字", {"π": "\n"}]},
    {"a": 1.0, "b": 1, "floating": -0.0},
    {"emoji😀": "text", "euro€": 1, "nested": {"k": ["é", "e\u0301"]}},
    {"large": 2**54 + 1, "small": -3},
]


def consumer(name: str, entrypoint: str):
    location = ROOT / "scripts" / f"{name}.py"
    spec = importlib.util.spec_from_file_location(f"legacy_digest_{name}", location)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return getattr(module, entrypoint)


def legacy_digest(value) -> str:
    payload = json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


@pytest.mark.parametrize("script,entrypoint", CONSUMERS.items())
@pytest.mark.parametrize("payload", PAYLOADS)
def test_all_native_consumers_emit_existing_digest_not_an_unqualified_jcs_switch(
    script: str, entrypoint: str, payload: dict
):
    digest = consumer(script, entrypoint)(payload)
    assert digest == legacy_digest(payload)
    assert len(digest) == 64


@pytest.mark.parametrize("script,entrypoint", CONSUMERS.items())
def test_key_permutation_invariant_and_mutation_sensitive(
    script: str, entrypoint: str
):
    observed = consumer(script, entrypoint)
    payload = {"α": [1, 2, 3], "nested": {"z": -0.0, "a": 1.5}, "plain": "abc"}
    expected = observed(payload)
    rng = random.Random(20261023)
    for _ in range(32):
        items = list(payload.items())
        rng.shuffle(items)
        assert observed(dict(items)) == expected
    assert observed({**payload, "plain": "changed"}) != expected


def test_legacy_wire_encoding_is_distinct_from_rfc8785_number_normalization():
    # Historical published bytes preserve 1.0 and -0.0, unlike RFC 8785.
    assert json.dumps({"n": 1.0, "z": -0.0}, sort_keys=True, separators=(",", ":")) == (
        '{"n":1.0,"z":-0.0}'
    )
