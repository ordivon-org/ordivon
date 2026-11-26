"""Bounded uv project-directory source graph; not a dependency resolver.

The caller supplies exact source cuts and retains verification-task authority.
"""

from __future__ import annotations

import os
import posixpath
import re
import subprocess
import tomllib
from collections import defaultdict, deque
from collections.abc import Iterable, Mapping
from pathlib import Path, PurePosixPath

Edge = tuple[str, str]  # consumer directory, provider directory


def _name(value: str) -> str:
    return re.sub(r"[-_.]+", "-", value).lower()


def _canonical(path: str) -> str:
    if (
        not path
        or path.startswith(("/", "../"))
        or "\\" in path
        or posixpath.normpath(path) != path
        or path == ".."
    ):
        raise ValueError(f"noncanonical repository path: {path!r}")
    return path


def project_edges(manifests: Mapping[str, bytes]) -> frozenset[Edge]:
    """All declared uv directory path alternatives, independent of markers.

    Unsupported workspace or file/archive sources are explicit refusal, not
    empty edges. Ordinary index/Git/URL sources are outside this projection.
    """
    projects = {}
    for path, data in manifests.items():
        _canonical(path)
        if PurePosixPath(path).name != "pyproject.toml":
            raise ValueError(f"not a project manifest: {path}")
        projects[str(PurePosixPath(path).parent)] = tomllib.loads(data.decode("utf-8"))
    edges = set()
    for consumer, document in projects.items():
        uv = document.get("tool", {}).get("uv", {})
        if "workspace" in uv:
            raise ValueError(f"workspace source semantics unsupported: {consumer}")
        sources = uv.get("sources", {})
        if not isinstance(sources, dict):
            raise TypeError(f"invalid uv sources: {consumer}")
        for dependency, spec in sources.items():
            alternatives = spec if isinstance(spec, list) else [spec]
            if not alternatives:
                raise ValueError(f"empty source alternatives: {consumer}:{dependency}")
            for source in alternatives:
                if not isinstance(source, dict):
                    raise TypeError(f"invalid uv source: {consumer}:{dependency}")
                if source.get("workspace") is True:
                    raise ValueError(
                        f"workspace source unsupported: {consumer}:{dependency}"
                    )
                if "path" not in source:
                    continue
                path = source["path"]
                if (
                    not isinstance(path, str)
                    or not path
                    or path.startswith("/")
                    or "\\" in path
                    or ":" in path
                    or "\x00" in path
                ):
                    raise ValueError(
                        f"unsupported path source: {consumer}:{dependency}"
                    )
                segments = [part for part in path.split("/") if part not in {"", "."}]
                first_child = next(
                    (i for i, part in enumerate(segments) if part != ".."),
                    len(segments),
                )
                if ".." in segments[first_child:]:
                    raise ValueError(
                        f"ambiguous path traversal: {consumer}:{dependency}"
                    )
                provider = _canonical(
                    posixpath.normpath(posixpath.join(consumer, path))
                )
                target = projects.get(provider)
                name = (
                    target.get("project", {}).get("name")
                    if target is not None
                    else None
                )
                if not isinstance(name, str) or _name(name) != _name(dependency):
                    raise ValueError(
                        f"unresolved project-directory source: {consumer}:{dependency} -> {provider}"
                    )
                edges.add((consumer, provider))
    return frozenset(edges)


def reverse_closure(seeds: Iterable[str], *graphs: Iterable[Edge]) -> frozenset[str]:
    """Reachability in union of source-cut edges; cycles terminate."""
    reverse = defaultdict(set)
    for graph in graphs:
        for consumer, provider in graph:
            reverse[provider].add(consumer)
    seen = set(seeds)
    pending = deque(seen)
    while pending:
        for consumer in reverse[pending.popleft()] - seen:
            seen.add(consumer)
            pending.append(consumer)
    return frozenset(seen)


def affected_projects(
    changed_paths: Iterable[str],
    before: Mapping[str, bytes],
    after: Mapping[str, bytes],
) -> frozenset[str]:
    """Old/new project membership plus union reverse edges."""
    roots = {str(PurePosixPath(path).parent) for path in before.keys() | after.keys()}
    seeds = set()
    for raw in changed_paths:
        path = _canonical(raw)
        # A nested project is also within the enclosing project's source tree.
        seeds.update(
            root
            for root in roots
            if root == "." or path == root or path.startswith(root + "/")
        )
    return reverse_closure(seeds, project_edges(before), project_edges(after))


def git_manifests(repo: Path, commit: str) -> dict[str, bytes]:
    """Read regular tracked manifest blobs from an exact immutable Git commit.

    Caller must choose the correct diff-base/head. No worktree or inherited
    Git object namespace participates.
    """
    if not re.fullmatch(r"[0-9a-f]{40}|[0-9a-f]{64}", commit):
        raise ValueError("exact full commit ID required")
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    env["GIT_GRAFT_FILE"] = os.devnull
    # A verification read must not silently download missing Git objects.
    env["GIT_NO_LAZY_FETCH"] = "1"
    argv = ["git", "-C", str(repo.resolve()), "--no-replace-objects"]

    def read(*args: str) -> bytes:
        return subprocess.check_output([*argv, *args], env=env)

    if read("rev-parse", "--verify", commit + "^{commit}").strip().decode() != commit:
        raise ValueError("not an exact commit ID")
    result = {}
    for row in read("ls-tree", "-r", "-z", commit).split(b"\0"):
        if not row:
            continue
        meta, raw = row.split(b"\t", 1)
        path = os.fsdecode(raw)
        if PurePosixPath(path).name != "pyproject.toml":
            continue
        mode, kind, oid = meta.decode().split()
        if kind != "blob" or mode not in {"100644", "100755"}:
            raise ValueError(f"non-regular tracked manifest: {path}")
        result[path] = read("cat-file", "blob", oid)
    return result
