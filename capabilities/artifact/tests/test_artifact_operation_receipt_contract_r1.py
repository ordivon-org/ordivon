"""Actual ArtifactOperation -> ReceiptFence consumer, with hostile replay evidence."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from artifact_operations.contract import (
    operation_envelope,
    require_public_file_commitment,
    validate_operation_envelope,
)
from artifact_operations.receipt import ReceiptFence


@pytest.mark.parametrize("version", [True, 1.0, "1"])
def test_operation_schema_version_requires_exact_integer(version: object) -> None:
    operation = operation_envelope("typed/version", "build", {})
    operation["schemaVersion"] = version
    with pytest.raises(ValueError, match="schemaVersion"):
        validate_operation_envelope(operation)


def test_public_file_size_cannot_be_boolean() -> None:
    with pytest.raises(ValueError, match="size"):
        require_public_file_commitment(
            {"path": "/no-real-file", "sha256": "a" * 64, "size": True},
            "source",
        )


@pytest.mark.parametrize("attack", ["absolute", "parent", "symlink"])
def test_replayed_receipt_cannot_rebind_role_outside_committed_outputs(
    tmp_path: Path, attack: str
) -> None:
    outside = tmp_path / "private.bin"
    outside.write_bytes(b"private-owner-bytes")
    fence = ReceiptFence(tmp_path / "state")
    calls = 0

    def producer(directory: Path):
        nonlocal calls
        calls += 1
        (directory / "artifact.bin").write_bytes(b"real-committed-artifact")
        return {"artifact": "artifact.bin"}, {}

    first = fence.run("build", "receipt/identity", {"source": "fixed"}, producer)
    operation_dir = Path(first["operationDirectory"])
    receipt_path = operation_dir / "activity-receipt.json"
    receipt = json.loads(receipt_path.read_text())
    if attack == "absolute":
        receipt["roles"]["artifact"] = str(outside)
    elif attack == "parent":
        receipt["roles"]["artifact"] = "../../../../../private.bin"
    else:
        (operation_dir / "other.bin").symlink_to(outside)
        receipt["roles"]["artifact"] = "other.bin"
    receipt_path.write_text(json.dumps(receipt))

    with pytest.raises(RuntimeError, match="role|output|path"):
        fence.run("build", "receipt/identity", {"source": "fixed"}, producer)
    assert calls == 1, "replay must not silently produce a second effect"


def test_valid_exact_receipt_replays_without_producer(tmp_path: Path) -> None:
    fence = ReceiptFence(tmp_path / "state")
    calls = 0

    def producer(directory: Path):
        nonlocal calls
        calls += 1
        (directory / "artifact.bin").write_bytes(b"valid")
        return {"artifact": "artifact.bin"}, {}

    first = fence.run("build", "valid", {"source": "fixed"}, producer)
    replayed = fence.run("build", "valid", {"source": "fixed"}, producer)
    assert first["roles"]["artifact"]["sha256"] == replayed["roles"]["artifact"]["sha256"]
    assert replayed["replayed"] is True
    assert calls == 1
