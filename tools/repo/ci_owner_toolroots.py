#!/usr/bin/env python3
"""Project selected CI Owner tasks onto native Mise install roots.

This is an installation projection, not a task selector or dependency solver.
Shell commands are opaque: preserve the established conservative Formal
reference and the explicit Gateway/Security test-only seam.
"""
from __future__ import annotations

import json
import os
from pathlib import Path, PurePosixPath
import subprocess
import sys
import tomllib
from typing import Callable

ManifestReader = Callable[[str], dict | None]


def project(tasks: object, by_task: dict[str, str], read: ManifestReader) -> list[str]:
    if not isinstance(tasks, list) or not all(isinstance(t, str) for t in tasks):
        raise ValueError("invalid selected Owner task list")
    if len(tasks) != len(set(tasks)):
        raise ValueError("duplicate selected Owner task")
    if set(tasks) - by_task.keys():
        raise ValueError("unregistered selected Owner task")

    roots: dict[str, None] = {}

    def include(root: str, *, required: bool = False) -> dict | None:
        path = PurePosixPath(root)
        if path.is_absolute() or ".." in path.parts or path.as_posix() != root or any(
            c in root for c in ("\n", "\r", "\\")
        ):
            raise ValueError("noncanonical tool root")
        manifest = read(root)
        if manifest is None:
            if required:
                raise ValueError("required native tool manifest absent: " + root)
            return None
        roots[root] = None
        return manifest

    for task in tasks:
        manifest = include(by_task[task])
        if manifest is None:
            continue
        native_tasks = manifest.get("tasks", {})
        if not isinstance(native_tasks, dict):
            raise ValueError("invalid native task table")
        # Mise accepts both a command string and an array of command strings.
        # Treat a literal reference conservatively; do not interpret shell.
        for row in native_tasks.values():
            if not isinstance(row, dict):
                continue
            run = row.get("run")
            commands = [run] if isinstance(run, str) else run if isinstance(run, list) else []
            if any(isinstance(command, str) and "tools/formal" in command for command in commands):
                include("tools/formal", required=True)
                break

    if "gateway:verify" in tasks:
        security = include("platform/security", required=True)
        tools = security.get("tools", {}) if security is not None else {}
        if not isinstance(tools, dict) or not isinstance(tools.get("opa"), str) or not tools["opa"].strip():
            raise ValueError("Gateway OPA test needs Security-pinned OPA")
    return list(roots)


def read_at_checkout(repo: Path, head: str, tracked: dict[str, bytes], root: str) -> dict | None:
    relative = root + "/mise.toml"
    path = repo / relative
    if relative not in tracked:
        if path.exists() or path.is_symlink():
            raise ValueError("untracked native tool manifest: " + relative)
        return None
    if tracked[relative] not in (b"100644", b"100755"):
        raise ValueError("nonregular Git native tool manifest: " + relative)
    if not path.is_file() or path.is_symlink() or path.resolve() != path:
        raise ValueError("nonregular native tool manifest: " + relative)
    source = subprocess.check_output(
        ["git", "--no-replace-objects", "show", f"{head}:{relative}"],
        cwd=repo, stderr=subprocess.PIPE, timeout=15,
    )
    if path.read_bytes() != source:
        raise ValueError("native tool manifest differs from Git HEAD: " + relative)
    return tomllib.loads(source.decode("utf-8"))


def main() -> int:
    try:
        repo = Path.cwd().resolve()
        head = subprocess.check_output(
            ["git", "--no-replace-objects", "rev-parse", "--verify", "HEAD"],
            cwd=repo, text=True, timeout=15,
        ).strip()
        if os.environ.get("GITHUB_SHA", head) != head:
            raise ValueError("checkout differs from provider GITHUB_SHA")
        tree = subprocess.check_output(
            ["git", "--no-replace-objects", "ls-tree", "-r", "-z", "--full-tree", head],
            cwd=repo, timeout=15,
        )
        tracked = {}
        for entry in tree.split(b"\0"):
            if entry:
                meta, name = entry.split(b"\t", 1)
                tracked[os.fsdecode(name)] = meta.split()[0]
        from affected_owners import OWNERS
        tasks = json.loads(os.environ["OWNER_TASKS_JSON"])
        by_task = {owner.queue_task: owner.root.rstrip("/") for owner in OWNERS}
        roots = project(tasks, by_task, lambda root: read_at_checkout(repo, head, tracked, root))
        Path(sys.argv[1]).write_text("".join(root + "\n" for root in roots), encoding="utf-8")
        return 0
    except (OSError, ValueError, KeyError, IndexError, subprocess.SubprocessError) as exc:
        print("ERROR: selected Owner toolroot projection: " + str(exc), file=sys.stderr)
        return 43


if __name__ == "__main__":
    raise SystemExit(main())
