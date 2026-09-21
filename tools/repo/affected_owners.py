#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
from dataclasses import dataclass
from pathlib import PurePosixPath
from typing import Iterable

@dataclass(frozen=True)
class Owner:
    name: str
    root: str
    task: str

OWNERS: tuple[Owner, ...] = (
    Owner("next", "meta/next/", "next:verify"),
    Owner("runtime", "services/runtime/", "runtime:verify"),
    Owner("host", "services/host/", "host:verify"),
    Owner("harness", "services/harness/", "harness:verify"),
    Owner("skills", "platform/skills/", "skills:verify"),
    Owner("security", "platform/security/", "security:verify"),
    Owner("workstation", "platform/workstation/", "workstation:ci"),
    Owner("network", "platform/network/", "network:ci"),
    Owner("artifact", "capabilities/artifact/", "artifact:verify"),
    Owner("distribution", "capabilities/distribution/", "distribution:verify"),
    Owner("media", "capabilities/media/", "media:verify"),
    Owner("game", "domains/game/", "game:verify"),
    Owner("capital", "domains/capital/", "capital:verify"),
)

CROSS_CUTTING_PATHS = frozenset(
    {
        "mise.toml",
        ".github/workflows/ci.yml",
        "tools/repo/affected_owners.py",
        "tools/repo/test_affected_owners.py",
    }
)

def _normalize(path: str) -> str:
    value = PurePosixPath(path.strip()).as_posix()
    while value.startswith("./"):
        value = value[2:]
    return value

def owners_for_paths(paths: Iterable[str]) -> tuple[Owner, ...]:
    normalized = tuple(_normalize(path) for path in paths if path.strip())
    if any(path in CROSS_CUTTING_PATHS for path in normalized):
        return OWNERS
    selected: list[Owner] = []
    for owner in OWNERS:
        if any(path.startswith(owner.root) for path in normalized):
            selected.append(owner)
    return tuple(selected)

def changed_paths(base: str, head: str) -> tuple[str, ...]:
    proc = subprocess.run(
        ["git", "diff", "--name-only", "--diff-filter=ACDMRTUXB", f"{base}...{head}"],
        check=True,
        text=True,
        stdout=subprocess.PIPE,
    )
    return tuple(line for line in proc.stdout.splitlines() if line)

def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Select monorepo owners affected by an exact Git range."
    )
    parser.add_argument("--base")
    parser.add_argument("--head")
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--changed-file", action="append", default=[])
    parser.add_argument(
        "--format",
        choices=("json", "names", "tasks"),
        default="json",
    )
    return parser

def main() -> int:
    args = _parser().parse_args()
    if args.all:
        selected = OWNERS
        paths: tuple[str, ...] = ()
    else:
        if args.changed_file:
            paths = tuple(args.changed_file)
        else:
            if not args.base or not args.head:
                raise SystemExit("--base and --head are required unless --all or --changed-file is used")
            paths = changed_paths(args.base, args.head)
        selected = owners_for_paths(paths)

    if args.format == "names":
        for owner in selected:
            print(owner.name)
    elif args.format == "tasks":
        for owner in selected:
            print(owner.task)
    else:
        print(
            json.dumps(
                {
                    "changedPaths": list(paths),
                    "owners": [
                        {"name": owner.name, "root": owner.root, "task": owner.task}
                        for owner in selected
                    ],
                },
                sort_keys=True,
            )
        )
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
