#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
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
        normalized = _normalize(root).rstrip("/") + "/"
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
    value = path.strip()
    if value.startswith("/") or ".." in value.split("/") or chr(92) in value:
        raise ValueError(f"noncanonical repository path: {path}")
    return PurePosixPath(value).as_posix()


OWNERS: tuple[Owner, ...] = load_owners()


# Verification admission is strict for executable owners. Read-only owner
# discovery stays permissive so unknown paths remain inspectable.
EXECUTABLE_OWNER_ROOTS = (
    "apps/",
    "services/",
    "platform/",
    "capabilities/",
    "domains/",
    "packages/",
    "extensions/",
    "tools/",
)
CROSS_CUTTING_SOURCE_ROOTS = ("tools/repo/",)


def require_registered_execution_paths(
    paths: Iterable[str], *, owners: tuple[Owner, ...] = OWNERS
) -> None:
    unregistered = sorted({
        path for raw in paths
        if (path := _normalize(raw)).startswith(EXECUTABLE_OWNER_ROOTS)
        and not any(path.startswith(root) for root in CROSS_CUTTING_SOURCE_ROOTS)
        and not any(path.startswith(owner.root) for owner in owners)
    })
    if unregistered:
        raise ValueError(f"unregistered owner path: {', '.join(unregistered)}")


def owners_for_paths(
    paths: Iterable[str], *, owners: tuple[Owner, ...] = OWNERS
) -> tuple[Owner, ...]:
    normalized = tuple(_normalize(path) for path in paths if path.strip())
    if any(
        path in CROSS_CUTTING_PATHS
        or any(path.startswith(root) for root in CROSS_CUTTING_SOURCE_ROOTS)
        for path in normalized
    ):
        return owners
    selected: list[Owner] = []
    for owner in owners:
        if any(path.startswith(owner.root) for path in normalized):
            selected.append(owner)
    return tuple(selected)


def repo_scope_census(
    paths: Iterable[str], *, owners: tuple[Owner, ...] = OWNERS,
) -> dict[str, object]:
    """Rebuild mechanical coverage from Git paths, never invent LEGO identity.

    Every unmatched exact tracked path is visible; docs/config/history are not
    automatically errors. Grouping is navigational and carries no new authority.
    """
    by_owner = {owner.name: 0 for owner in owners}
    outstanding: dict[str, list[str]] = {}
    total = 0
    for raw in paths:
        path = _normalize(raw)
        total += 1
        matches = [owner for owner in owners if path.startswith(owner.root)]
        if len(matches) == 1:
            by_owner[matches[0].name] += 1
        elif len(matches) == 0:
            parts = path.split("/")
            area = "/".join(parts[:2]) if len(parts) > 1 else "[repository-root]"
            outstanding.setdefault(area, []).append(path)
        else:
            raise ValueError(f"overlapping registered owner roots at {path}")
    grouped = [
        {
            "area": area,
            "standing": "UNREGISTERED_REPO_SCOPE_NOT_LEGO_VERDICT",
            "count": len(items),
            "examples": sorted(items)[:6],
        }
        for area, items in outstanding.items()
    ]
    grouped.sort(key=lambda x: (-x["count"], x["area"]))
    owned_count = sum(by_owner.values())
    return {
        "truthRole": "source-cut-mechanical-owner-coverage-not-domain-authority",
        "registeredOwnerCount": len(owners),
        "trackedFileCount": total,
        "matchedTrackedFiles": owned_count,
        "unmatchedTrackedFiles": total - owned_count,
        "registeredScopes": [
            {"owner": o.name, "sourceRoot": o.root, "matchedTrackedFiles": by_owner[o.name]}
            for o in owners
        ],
        "unregisteredAreas": grouped,
    }


def git_tracked_files(source_cut: str) -> tuple[str, tuple[str, ...]]:
    """Use exact Git object identity, never read moving Worktree for census."""
    commit = subprocess.run(
        ["git", "rev-parse", "--verify", f"{source_cut}^{{commit}}"],
        check=True, capture_output=True, text=True,
    ).stdout.strip()
    tree = subprocess.run(
        ["git", "ls-tree", "-r", "-z", "--name-only", commit],
        check=True, capture_output=True,
    ).stdout
    return commit, tuple(os.fsdecode(name) for name in tree.split(b"\0") if name)


def changed_paths(base: str, head: str) -> tuple[str, ...]:
    # Preserve both sides of a cross-owner move, rather than allowing Git's
    # similarity detection to hide the source owner from verification.
    proc = subprocess.run(
        [
            "git", "diff", "--name-only", "--no-renames", "-z",
            "--diff-filter=ACDMRTUXB", f"{base}...{head}",
        ],
        check=True,
        stdout=subprocess.PIPE,
    )
    return tuple(os.fsdecode(path) for path in proc.stdout.split(b"\0") if path)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Select monorepo owners affected by an exact Git range."
    )
    parser.add_argument("--base")
    parser.add_argument("--head")
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--scope-census", action="store_true")
    parser.add_argument("--source-cut", default="HEAD")
    parser.add_argument("--changed-file", action="append", default=[])
    parser.add_argument(
        "--format",
        choices=("json", "names", "tasks", "queue-tasks"),
        default="json",
    )
    return parser


def main() -> int:
    args = _parser().parse_args()
    if args.scope_census:
        commit, paths = git_tracked_files(args.source_cut)
        report = repo_scope_census(paths)
        report["sourceCut"] = commit
        print(json.dumps(report, sort_keys=True, indent=2))
        return 0
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
        require_registered_execution_paths(paths)
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
