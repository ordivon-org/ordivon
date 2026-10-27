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


# Exact Git source area projection. Orthogonal to mechanical verification Owner
# selection and to the independent R2.1 LEGO contract, consumer and proof graph.
@dataclass(frozen=True)
class SourceArea:
    name: str
    role: str
    root: str = ""
    files: tuple[str, ...] = ()


def load_source_areas(manifest: Path = MANIFEST_PATH) -> tuple[SourceArea, ...]:
    data = tomllib.loads(manifest.read_text(encoding="utf-8"))
    known_owners = load_owners(manifest)
    result: list[SourceArea] = []
    for index, item in enumerate(data.get("source_areas", [])):
        name, role = item.get("name"), item.get("role")
        root, files = item.get("root", ""), item.get("files", [])
        if not isinstance(name, str) or not name or not isinstance(role, str) or not role:
            raise ValueError(f"source area {index}: missing name/role")
        if not isinstance(root, str) or not isinstance(files, list) or bool(root) == bool(files):
            raise ValueError(f"source area {name}: exactly one root or files is required")
        if root:
            if not root.endswith("/") or root.startswith("/") or _normalize(root).rstrip("/") + "/" != root:
                raise ValueError(f"source area {name}: noncanonical root")
            if any(root.startswith(o.root) or o.root.startswith(root) for o in known_owners):
                raise ValueError(f"source area {name}: overlaps mechanical Owner")
        if not all(isinstance(x, str) and x and "/" not in x and _normalize(x) == x for x in files):
            raise ValueError(f"source area {name}: invalid exact root file")
        result.append(SourceArea(name, role, root, tuple(files)))
    names = [x.name for x in result]
    roots = [x.root for x in result if x.root]
    files = [y for x in result for y in x.files]
    if len(names) != len(set(names)) or len(roots) != len(set(roots)) or len(files) != len(set(files)):
        raise ValueError("source areas contain duplicate names/roots/files")
    return tuple(result)


def source_area_for_path(path: str, *,
                         owners: tuple[Owner, ...] = OWNERS,
                         areas: tuple[SourceArea, ...] | None = None) -> tuple[str, str]:
    """Location/role only. Never LEGO qualification or evidence of consumers."""
    path = _normalize(path)
    matching_owner = next((o for o in owners if path.startswith(o.root)), None)
    if matching_owner:
        return ("OWNER:" + matching_owner.name, "VERIFICATION_PARTITION_NOT_LEGO")
    matched = [a for a in (areas if areas is not None else load_source_areas())
               if path in a.files or (a.root and path.startswith(a.root))]
    if not matched:
        return ("UNCLASSIFIED", "UNKNOWN_NOT_FALSE")
    # Exact root files trump prefixes; nested explicit core beats generic Skill source.
    matched.sort(key=lambda a: (bool(a.files), len(a.root)), reverse=True)
    return (matched[0].name, matched[0].role)


def tracked_source_area_census(paths: Iterable[str] | None = None) -> dict[str, object]:
    """Git-index path currentness, explicitly not working-tree or runtime truth."""
    repo = Path(__file__).resolve().parents[2]
    if paths is None:
        raw = subprocess.check_output(["git", "-C", str(repo), "ls-files", "-z"])
        paths = [p.decode("utf-8", errors="surrogateescape")
                 for p in raw.split(b"\0") if p]
    counts: dict[str, int] = {}
    unknown: list[str] = []
    for path in paths:
        area, _role = source_area_for_path(path)
        counts[area] = counts.get(area, 0) + 1
        if area == "UNCLASSIFIED":
            unknown.append(path)
    head = subprocess.check_output(
        ["git", "-C", str(repo), "rev-parse", "HEAD"], text=True
    ).strip()
    index_equal = subprocess.run(
        ["git", "-C", str(repo), "diff", "--cached", "--quiet"],
        check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
    ).returncode == 0
    return {
        "kind": "ordivon.repo-source-area-census-r1",
        "sourceCut": head,
        "basis": "git-index-path-projection-only",
        "indexEqualsHead": index_equal,
        "ownerPartitions": len(OWNERS),
        "tracked": sum(counts.values()),
        "byArea": dict(sorted(counts.items())),
        "unclassifiedPaths": sorted(unknown),
        "semanticQualification": "SOURCE_SCOPE_ONLY_NOT_LEGO_CONSUMER_OR_FORMAL_PROOF",
    }


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
)


def require_registered_execution_paths(
    paths: Iterable[str], *, owners: tuple[Owner, ...] = OWNERS
) -> None:
    unregistered = sorted({
        path for raw in paths
        if (path := _normalize(raw)).startswith(EXECUTABLE_OWNER_ROOTS)
        and not any(path.startswith(owner.root) for owner in owners)
    })
    if unregistered:
        raise ValueError(f"unregistered owner path: {', '.join(unregistered)}")


def owners_for_paths(
    paths: Iterable[str], *, owners: tuple[Owner, ...] = OWNERS
) -> tuple[Owner, ...]:
    normalized = tuple(_normalize(path) for path in paths if path.strip())
    if any(path in CROSS_CUTTING_PATHS for path in normalized):
        return owners
    selected: list[Owner] = []
    for owner in owners:
        if any(path.startswith(owner.root) for path in normalized):
            selected.append(owner)
    return tuple(selected)


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
    parser.add_argument("--source-census", action="store_true")
    parser.add_argument("--changed-file", action="append", default=[])
    parser.add_argument(
        "--format",
        choices=("json", "names", "tasks", "queue-tasks"),
        default="json",
    )
    return parser


def main() -> int:
    args = _parser().parse_args()
    if args.source_census:
        result = tracked_source_area_census()
        print(json.dumps(result, sort_keys=True))
        return 2 if result["unclassifiedPaths"] else 0
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
