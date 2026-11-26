"""Exact-byte ephemeral input binding for native single-file verifiers.

Reuse the OS descriptor, stat, hashing and temporary-file primitives rather than
introducing another CAS, transport or evidence format. The caller owns the
private TemporaryDirectory lifetime and removes the snapshot after verification.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .file_stream import observe_stream, open_regular_file


@dataclass(frozen=True)
class InputSnapshot:
    path: Path
    sha256: str
    size: int


def stage_verified_input(
    source: Path, expected_sha256: str, private_root: Path, *, role: str
) -> InputSnapshot:
    """Freeze the exact bytes that a downstream native verifier will read.

    Only use for genuinely self-contained files: relative sidecar references
    must be resolved by the owning family verifier, not silently relocated.
    A same-principal writer to the private directory is outside this guarantee.
    """
    if role not in {"profile", "subject", "contract"}:
        raise ValueError(f"invalid input snapshot role: {role!r}")
    dest_dir = private_root / role
    dest_dir.mkdir(mode=0o700)
    dest = dest_dir / source.name

    try:
        with open_regular_file(source, label=role) as stream, dest.open("xb") as frozen:
            observed_sha256, size = observe_stream(stream, frozen)
    except BaseException:
        dest.unlink(missing_ok=True)
        raise

    if observed_sha256 != expected_sha256:
        dest.unlink(missing_ok=True)
        raise ValueError(f"{role} bytes differ from request digest")
    dest.chmod(0o400)
    return InputSnapshot(path=dest, sha256=observed_sha256, size=size)
