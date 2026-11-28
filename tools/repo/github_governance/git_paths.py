from __future__ import annotations

import subprocess
from pathlib import Path


def tracked(root: Path, pattern: str) -> tuple[str, ...]:
    # Git paths are byte sequences and may contain LF, quotes, or non-UTF-8
    # bytes. Its default human-readable quoting cannot certify file identity.
    # Use Git's native NUL-delimited representation, preserving lossless
    # filesystem byte round-tripping through Python's surrogateescape.
    output = subprocess.check_output(
        ["git", "-C", str(root), "ls-files", "-z", "--", pattern],
    )
    return tuple(
        part.decode("utf-8", errors="surrogateescape")
        for part in output.split(b"\0")
        if part
    )

def dirs_for_lock(root: Path, pattern: str, filename: str) -> set[str]:
    result: set[str] = set()
    for path in tracked(root, pattern):
        p = Path(path)
        if p.name != filename:
            continue
        result.add("/" + p.parent.as_posix())
    return result
