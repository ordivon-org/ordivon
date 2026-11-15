"""Exact-byte ephemeral input binding for native single-file verifiers.

Reuse the OS descriptor, stat, hashing and temporary-file primitives rather than
introducing another CAS, transport or evidence format. The caller owns the
private TemporaryDirectory lifetime and removes the snapshot after verification.
"""
from __future__ import annotations

import hashlib
import os
import stat
from dataclasses import dataclass
from pathlib import Path


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

    # O_NONBLOCK prevents blocking on a FIFO before the fstat regular-file
    # check; O_NOFOLLOW rejects a final symlink swapped into the source path.
    flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0)
    flags |= getattr(os, "O_NONBLOCK", 0) | getattr(os, "O_NOFOLLOW", 0)
    handle = os.open(source, flags)
    digest = hashlib.sha256()
    size = 0
    try:
        with os.fdopen(handle, "rb") as stream:
            if not stat.S_ISREG(os.fstat(stream.fileno()).st_mode):
                raise ValueError(f"{role} is not a regular file")
            with dest.open("xb") as frozen:
                for block in iter(lambda: stream.read(1024 * 1024), b""):
                    digest.update(block)
                    size += len(block)
                    frozen.write(block)
    except BaseException:
        dest.unlink(missing_ok=True)
        raise

    observed_sha256 = digest.hexdigest()
    if observed_sha256 != expected_sha256:
        dest.unlink(missing_ok=True)
        raise ValueError(f"{role} bytes differ from request digest")
    dest.chmod(0o400)
    return InputSnapshot(path=dest, sha256=observed_sha256, size=size)
