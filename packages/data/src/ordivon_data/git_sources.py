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

from .git_identity import qualify_batch_sizes, verify_object_batch

_OBJECT_ID = re.compile(r"[0-9a-f]{40}|[0-9a-f]{64}\Z")
_MAX_ODPS_BYTES = 2 * 1024 * 1024


def _git(repo: Path, *args: str, input_bytes: bytes | None = None) -> bytes:
    # Clear foreign repository selectors, then explicitly install this
    # observer's local-only policy. Do not inherit a caller's fetch policy.
    env = {
        key: value for key, value in os.environ.items() if not key.startswith("GIT_")
    }
    env.update(GIT_NO_LAZY_FETCH="1", GIT_OPTIONAL_LOCKS="0")
    try:
        result = subprocess.run(
            ["/usr/bin/git", "--no-replace-objects", "-C", str(repo), *args],
            check=True,
            capture_output=True,
            input=input_bytes,
            timeout=20,
            env=env,
        )
        # A partial native listing with diagnostics is not a complete cut,
        # even when the command exits successfully.
        if result.stderr:
            raise ValueError(
                "committed ODPS source cannot be resolved: native diagnostic"
            )
        return result.stdout
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
    paths = _git(root, "ls-files", "-z", "--", "*/odps.json")
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
    tree = _git(repo, "ls-tree", "-r", "-t", "-z", "--full-tree", commit)
    tree_ids = {root_tree}
    objects: list[tuple[str, str]] = []
    for entry in tree.split(b"\x00"):
        if not entry:
            continue
        metadata, path = entry.split(b"\t", 1)
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
    expected = [(commit, "commit"), *((oid, "tree") for oid in sorted(tree_ids))]
    request = "".join(oid + "\n" for oid, _ in expected).encode("ascii")
    headers = qualify_batch_sizes(
        _git(repo, "cat-file", "--batch-check", input_bytes=request),
        expected,
        algorithm,
    )
    verify_object_batch(
        _git(repo, "cat-file", "--batch", input_bytes=request),
        headers,
        algorithm,
        commit=commit,
        root_tree=root_tree,
    )
    blobs = []
    for _, oid in sorted(objects):
        size = int(_git(repo, "cat-file", "-s", oid).decode("ascii").strip())
        if not 0 < size <= _MAX_ODPS_BYTES:
            raise ValueError("Git ODPS source exceeds bounded input size")
        raw = _git(repo, "cat-file", "blob", oid)
        if len(raw) != size:
            raise ValueError("Git ODPS blob read-back length mismatch")
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
        blobs.append(raw)
    return commit, blobs
