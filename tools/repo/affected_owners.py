#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import tomllib
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Iterable

MANIFEST_PATH = Path(__file__).with_name("owners.toml")


@dataclass(frozen=True)
class Owner:
    name: str
    root: str
    task: str
    queue_task: str


def load_owners(path: Path = MANIFEST_PATH) -> tuple[Owner, ...]:
    data = tomllib.loads(path.read_text(encoding="utf-8"))
    if data.get("schema_version") != 1:
        raise ValueError("owner manifest schema_version must be 1")
    if data.get("truth_role") != "repository-mechanics-only-not-domain-authority":
        raise ValueError("owner manifest truth_role must remain repository-mechanics-only")
    rows = data.get("owners")
    if not isinstance(rows, list) or not rows:
        raise ValueError("owner manifest must contain at least one [[owners]] row")

    owners: list[Owner] = []
    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            raise ValueError(f"owner row {index} must be a table")
        name = row.get("name")
        root = row.get("root")
        task = row.get("verify_task")
        queue_task = row.get("queue_verify_task", task)
        if not all(isinstance(value, str) and value.strip() for value in (name, root, task, queue_task)):
            raise ValueError(
                f"owner row {index} requires non-empty name/root/verify_task and optional queue_verify_task"
            )
        if root.startswith("/") or not root.endswith("/"):
            raise ValueError(f"owner {name}: root must be repository-relative and end with '/': {root}")
        normalized = PurePosixPath(root).as_posix().rstrip("/") + "/"
        if normalized != root:
            raise ValueError(f"owner {name}: root is not canonical: {root}")
        owners.append(Owner(name=name, root=root, task=task, queue_task=queue_task))

    names = [owner.name for owner in owners]
    roots = [owner.root for owner in owners]
    tasks = [owner.task for owner in owners]
    queue_tasks = [owner.queue_task for owner in owners]
    for label, values in (
        ("name", names),
        ("root", roots),
        ("verify_task", tasks),
        ("queue_verify_task", queue_tasks),
    ):
        if len(values) != len(set(values)):
            raise ValueError(f"owner manifest contains duplicate {label}")

    for i, left in enumerate(owners):
        for right in owners[i + 1 :]:
            if left.root.startswith(right.root) or right.root.startswith(left.root):
                raise ValueError(
                    f"owner roots must not overlap: {left.name}={left.root} {right.name}={right.root}"
                )
    return tuple(owners)


OWNERS: tuple[Owner, ...] = load_owners()

CROSS_CUTTING_PATHS = frozenset(
    {
        "mise.toml",
        ".github/workflows/ci.yml",
        "tools/repo/owners.toml",
        "tools/repo/affected_owners.py",
        "tools/repo/test_affected_owners.py",
        "tools/repo/convergence_plan.py",
        "tools/repo/test_convergence_plan.py",
        "tools/repo/check_github_governance.py",
        "tools/repo/dependency_contracts.toml",
        "tools/repo/check_owner_boundaries.py",
        "tools/repo/test_owner_boundaries.py",
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
        choices=("json", "names", "tasks", "queue-tasks"),
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
    elif args.format == "queue-tasks":
        for owner in selected:
            print(owner.queue_task)
    else:
        print(
            json.dumps(
                {
                    "changedPaths": list(paths),
                    "owners": [
                        {
                            "name": owner.name,
                            "root": owner.root,
                            "task": owner.task,
                            "queueTask": owner.queue_task,
                        }
                        for owner in selected
                    ],
                },
                sort_keys=True,
            )
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
