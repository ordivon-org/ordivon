from __future__ import annotations

import pytest

from ordivon_host_v2.canonical import canonical_digest
from ordivon_host_v2.models import CheckpointInput


def test_rfc8785_digest_is_key_order_invariant() -> None:
    assert canonical_digest({"b": 2, "a": 1}) == canonical_digest({"a": 1, "b": 2})


def test_writer_label_is_metadata_validation() -> None:
    CheckpointInput(payload={"frontier": "x"}, writer_label="chat:a")
    with pytest.raises(ValueError):
        CheckpointInput(payload={}, writer_label="  ")
