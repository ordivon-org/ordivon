"""Snapshot a producing Owner's ODPS metadata from one immutable Git commit.

Git owns source identity and blob storage. Data only reads the committed tree;
it does not register products, publish physical files, or infer data rights.
Missing local objects require separate explicit acquisition, never implicit hydration.
"""

from __future__ import annotations

import os
import re
import subprocess
from pathlib import Path

from .git_identity import (
    _MAX_OBJECTS,
    partition_object_batches,
    qualify_batch_sizes,
    verify_object_batch,
)
from .git_transport import capture_git_output

_OBJECT_ID = re.compile(r"[0-9a-f]{40}|[0-9a-f]{64}\Z")
_MAX_LISTING_BYTES = 16 * 1024 * 1024
_MAX_SCALAR_BYTES = 64 * 1024


def _git(
    repo: Path,
    *args: str,
    input_bytes: bytes | None = None,
    max_output: int = _MAX_SCALAR_BYTES,
) -> bytes:
    # Clear foreign repository selectors, then explicitly install this
    # observer's local-only policy. Do not inherit a caller's fetch policy.
    env = {
        key: value for key, value in os.environ.items() if not key.startswith("GIT_")
    }
    env.update(GIT_NO_LAZY_FETCH="1", GIT_OPTIONAL_LOCKS="0")
    try:
        return capture_git_output(
            ["/usr/bin/git", "--no-replace-objects", "-C", str(repo), *args],
            input_bytes=input_bytes,
            max_output=max_output,
            timeout=20,
            env=env,
        )
    except (OSError, subprocess.SubprocessError) as error:
        raise ValueError("committed ODPS source cannot be resolved") from error


def _require_repo_root(repo: Path) -> Path:
    """An explicit checkout cannot silently resolve to its parent repository."""
    root = repo.resolve(strict=True)
    actual = Path(os.fsdecode(_git(root, "rev-parse", "--show-toplevel").rstrip(b"\n")))
    if actual.resolve(strict=True) != root:
        raise ValueError("Git source path is not the exact checkout root")
    return root


def tracked_owner_products(repo: Path) -> list[Path]:
    """Discover tracked paths in the same explicit checkout, not foreign Git env."""
    root = _require_repo_root(repo)
    paths = _git(
        root, "ls-files", "-z", "--", "*/odps.json", max_output=_MAX_LISTING_BYTES
    )
    return sorted(root / path.decode("utf-8") for path in paths.split(b"\0") if path)


def committed_owner_products(repo: Path, revision: str) -> tuple[str, list[bytes]]:
    """Return (exact commit OID, immutable ODPS blob bytes) from one Git tree.

    Resolve symbolic revisions once, then read only that exact locally available
    commit. Missing objects or incomplete native observations fail closed. Ignore
    uncommitted index/worktree changes and untracked files. Reject symlinked
    ODPS entries and unbounded blobs instead of silently following filesystem
    paths or claiming physical data availability.
    """
    if not isinstance(revision, str) or not revision or revision.startswith("-"):
        raise ValueError("Git source revision must be a nonempty revision")
    repo = _require_repo_root(repo)
    commit = (
        _git(repo, "rev-parse", "--verify", "--end-of-options", revision + "^{commit}")
        .decode("ascii")
        .strip()
    )
    if _OBJECT_ID.fullmatch(commit) is None:
        raise ValueError("Git source revision did not resolve to an exact commit")
    root_tree = (
        _git(repo, "rev-parse", "--verify", commit + "^{tree}").decode("ascii").strip()
    )
    tree = _git(
        repo,
        "ls-tree",
        "-r",
        "-t",
        "-z",
        "--full-tree",
        commit,
        max_output=_MAX_LISTING_BYTES,
    )
    # Native ls-tree -z emits one nonempty row per unique path, terminated
    # by NUL. Qualify framing and path multiplicity before object dispatch.
    if not tree.endswith(b"\x00"):
        raise ValueError("incomplete Git tree listing")
    entries = tree.split(b"\x00")
    entries.pop()
    seen_paths: set[bytes] = set()
    tree_ids = {root_tree}
    objects: list[tuple[str, str]] = []
    for entry in entries:
        metadata, separator, path = entry.partition(b"\t")
        if not separator or not metadata or not path or path in seen_paths:
            raise ValueError("incomplete or duplicate Git tree listing")
        seen_paths.add(path)
        mode, kind, oid = metadata.decode("ascii").split(" ")
        if kind == "tree":
            tree_ids.add(oid)
            continue
        if not path.endswith(b"/odps.json"):
            continue
        if mode not in ("100644", "100755") or kind != "blob":
            raise ValueError("ODPS tracked source is not a regular Git blob")
        objects.append((path.decode("utf-8"), oid))
    if not objects:
        raise ValueError("Git commit has no producer-owned ODPS inputs")
    # Qualify the commit and every distinct tree in the native traversal.
    # Static corruption can otherwise redirect the listing to a different,
    # individually valid blob. The repository is assumed quiescent: this is
    # not an atomic snapshot across separate Git commands.
    algorithm = _git(repo, "rev-parse", "--show-object-format").decode("ascii").strip()
    blob_ids = sorted({oid for _, oid in objects})
    if 1 + len(tree_ids) + len(blob_ids) > _MAX_OBJECTS:
        raise ValueError("Git cut exceeds bounded object count")
    expected = [
        (commit, "commit"),
        *((oid, "tree") for oid in sorted(tree_ids)),
        *((oid, "blob") for oid in blob_ids),
    ]
    request = "".join(oid + "\n" for oid, _ in expected).encode("ascii")
    headers = qualify_batch_sizes(
        _git(
            repo,
            "cat-file",
            "--batch-check",
            input_bytes=request,
            max_output=len(expected) * (len(commit) + 17),
        ),
        expected,
        algorithm,
    )
    # Complete preflight before any content request. Each chunk is
    # bounded independently; only one commit is permitted, in chunk zero.
    blobs: dict[str, bytes] = {}
    for index, batch in enumerate(partition_object_batches(headers)):
        batch_request = b"".join(
            header.split(b" ", 1)[0] + b"\n" for header, _ in batch
        )
        blobs.update(
            verify_object_batch(
                _git(
                    repo,
                    "cat-file",
                    "--batch",
                    input_bytes=batch_request,
                    max_output=sum(len(header) + size + 2 for header, size in batch),
                ),
                batch,
                algorithm,
                commit=commit,
                root_tree=root_tree,
                require_commit=index == 0,
            )
        )
    for oid in blob_ids:
        raw = blobs[oid]
        # cat-file is an object lookup, not an integrity check: even a
        # same-length corrupt loose blob may be returned under the old OID.
        # Native hash-object uses the repository's object format, without
        # filters or object-store writes, over exactly the returned bytes.
        observed_oid = (
            _git(repo, "hash-object", "--no-filters", "--stdin", input_bytes=raw)
            .decode("ascii")
            .strip()
        )
        if observed_oid != oid:
            raise ValueError("Git ODPS blob identity mismatch")
    # Retain every path, including paths with identical content. Deduplicate
    # native reads and hashes only, not producer identity or multiplicity.
    return commit, [blobs[oid] for _, oid in sorted(objects)]
