"""Snapshot a producing Owner's ODPS metadata from one immutable Git commit.

Git owns source identity and blob storage. Data only reads the committed tree;
it does not register products, publish physical files, or infer data rights.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

_OBJECT_ID = re.compile(r"[0-9a-f]{40}|[0-9a-f]{64}\Z")
_MAX_ODPS_BYTES = 2 * 1024 * 1024


def _git(repo: Path, *args: str) -> bytes:
    try:
        return subprocess.run(
            ["/usr/bin/git", "--no-replace-objects", "-C", str(repo), *args],
            check=True,
            capture_output=True,
            timeout=20,
        ).stdout
    except (OSError, subprocess.SubprocessError) as error:
        raise ValueError("committed ODPS source cannot be resolved") from error


def committed_owner_products(repo: Path, revision: str) -> tuple[str, list[bytes]]:
    """Return (exact commit OID, immutable ODPS blob bytes) from one Git tree.

    Resolve symbolic revisions once, then read only that exact commit. Ignore
    uncommitted index/worktree changes and untracked files. Reject symlinked
    ODPS entries and unbounded blobs instead of silently following filesystem
    paths or claiming physical data availability.
    """
    if not isinstance(revision, str) or not revision or revision.startswith("-"):
        raise ValueError("Git source revision must be a nonempty revision")
    commit = (
        _git(repo, "rev-parse", "--verify", "--end-of-options", revision + "^{commit}")
        .decode("ascii")
        .strip()
    )
    if _OBJECT_ID.fullmatch(commit) is None:
        raise ValueError("Git source revision did not resolve to an exact commit")
    tree = _git(repo, "ls-tree", "-r", "-z", "--full-tree", commit)
    objects: list[tuple[str, str]] = []
    for entry in tree.split(b"\x00"):
        if not entry:
            continue
        metadata, path = entry.split(b"\t", 1)
        if not path.endswith(b"/odps.json"):
            continue
        mode, kind, oid = metadata.decode("ascii").split(" ")
        if mode not in ("100644", "100755") or kind != "blob":
            raise ValueError("ODPS tracked source is not a regular Git blob")
        objects.append((path.decode("utf-8"), oid))
    if not objects:
        raise ValueError("Git commit has no producer-owned ODPS inputs")
    blobs = []
    for _, oid in sorted(objects):
        size = int(_git(repo, "cat-file", "-s", oid).decode("ascii").strip())
        if not 0 < size <= _MAX_ODPS_BYTES:
            raise ValueError("Git ODPS source exceeds bounded input size")
        raw = _git(repo, "cat-file", "blob", oid)
        if len(raw) != size:
            raise ValueError("Git ODPS blob read-back length mismatch")
        blobs.append(raw)
    return commit, blobs
