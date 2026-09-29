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
PATH_CLASSES_PATH = Path(__file__).with_name("path_classes.toml")


@dataclass(frozen=True)
class Owner:
    name: str
    root: str
    task: str
    queue_task: str
    literal_boundary_target: bool = True


@dataclass(frozen=True)
class PathClassRule:
    kind: str
    reason: str
    prefix: str | None = None
    path: str | None = None


@dataclass(frozen=True)
class PathResolution:
    path: str
    kind: str
    owner: Owner | None
    reason: str


ALLOWED_PATH_CLASSES = frozenset(
    {"REPOSITORY_MECHANICS", "DOCUMENTATION", "GENERATED_EVIDENCE", "ARCHIVED"}
)


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
        literal_boundary_target = row.get("literal_boundary_target", True)
        if not all(isinstance(value, str) and value.strip() for value in (name, root, task, queue_task)):
            raise ValueError(
                f"owner row {index} requires non-empty name/root/verify_task and optional queue_verify_task"
            )
        if not isinstance(literal_boundary_target, bool):
            raise ValueError(f"owner {name}: literal_boundary_target must be boolean")
        if root.startswith("/") or not root.endswith("/"):
            raise ValueError(f"owner {name}: root must be repository-relative and end with '/': {root}")
        normalized = PurePosixPath(root).as_posix().rstrip("/") + "/"
        if normalized != root:
            raise ValueError(f"owner {name}: root is not canonical: {root}")
        owners.append(Owner(name=name, root=root, task=task, queue_task=queue_task, literal_boundary_target=literal_boundary_target))

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


def load_path_classes(path: Path = PATH_CLASSES_PATH) -> tuple[PathClassRule, ...]:
    data = tomllib.loads(path.read_text(encoding="utf-8"))
    if data.get("schema_version") != 1:
        raise ValueError("path class manifest schema_version must be 1")
    if data.get("truth_role") != "repository-path-classification-not-domain-authority":
        raise ValueError("path class manifest truth_role must remain repository classification only")
    rows = data.get("classes")
    if not isinstance(rows, list) or not rows:
        raise ValueError("path class manifest must contain [[classes]] rows")
    result: list[PathClassRule] = []
    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            raise ValueError(f"path class row {index} must be a table")
        kind = row.get("kind")
        reason = row.get("reason")
        prefix = row.get("prefix")
        exact = row.get("path")
        if kind not in ALLOWED_PATH_CLASSES:
            raise ValueError(f"path class row {index} has unsupported kind: {kind!r}")
        if not isinstance(reason, str) or not reason.strip():
            raise ValueError(f"path class row {index} requires reason")
        if (prefix is None) == (exact is None):
            raise ValueError(f"path class row {index} requires exactly one of prefix/path")
        if prefix is not None:
            if not isinstance(prefix, str) or not prefix or not prefix.endswith("/") or prefix.startswith("/"):
                raise ValueError(f"path class row {index} has invalid prefix")
            prefix = PurePosixPath(prefix).as_posix().rstrip("/") + "/"
        if exact is not None:
            if not isinstance(exact, str) or not exact or exact.startswith("/"):
                raise ValueError(f"path class row {index} has invalid path")
            exact = PurePosixPath(exact).as_posix()
        result.append(PathClassRule(kind=kind, reason=reason, prefix=prefix, path=exact))
    return tuple(result)


OWNERS: tuple[Owner, ...] = load_owners()
PATH_CLASS_RULES: tuple[PathClassRule, ...] = load_path_classes()

CROSS_CUTTING_PATHS = frozenset(
    {
        "mise.toml",
        ".github/workflows/ci.yml",
        "tools/repo/owners.toml",
        "tools/repo/path_classes.toml",
        "tools/repo/affected_owners.py",
        "tools/repo/test_affected_owners.py",
        "tools/repo/check_path_ownership.py",
        "tools/repo/source_planes.py",
        "tools/repo/test_source_planes.py",
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


def resolve_path(
    path: str,
    *,
    owners: tuple[Owner, ...] = OWNERS,
    rules: tuple[PathClassRule, ...] = PATH_CLASS_RULES,
) -> PathResolution:
    normalized = _normalize(path)
    if not normalized or normalized == ".":
        raise ValueError("empty/non-file path is not classifiable")
    matches = [owner for owner in owners if normalized.startswith(owner.root)]
    if len(matches) > 1:
        raise ValueError(f"path resolves to multiple owners: {normalized}")
    if matches:
        owner = matches[0]
        return PathResolution(
            path=normalized,
            kind="OWNER_SOURCE",
            owner=owner,
            reason=f"path is beneath first-class owner root {owner.root}",
        )
    for rule in rules:
        if rule.path is not None and normalized == rule.path:
            return PathResolution(normalized, rule.kind, None, rule.reason)
        if rule.prefix is not None and normalized.startswith(rule.prefix):
            return PathResolution(normalized, rule.kind, None, rule.reason)
    raise ValueError(f"UNKNOWN repository path classification: {normalized}")


def resolve_paths(paths: Iterable[str]) -> tuple[PathResolution, ...]:
    return tuple(resolve_path(path) for path in paths if path.strip())


def owners_for_paths(paths: Iterable[str]) -> tuple[Owner, ...]:
    resolutions = resolve_paths(paths)
    normalized = tuple(item.path for item in resolutions)
    if any(path in CROSS_CUTTING_PATHS for path in normalized):
        return OWNERS
    selected_names = {
        item.owner.name
        for item in resolutions
        if item.owner is not None
    }
    return tuple(owner for owner in OWNERS if owner.name in selected_names)


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
        description="Select monorepo owners affected by an exact Git range with total path classification."
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
        resolutions: tuple[PathResolution, ...] = ()
    else:
        if args.changed_file:
            paths = tuple(args.changed_file)
        else:
            if not args.base or not args.head:
                raise SystemExit("--base and --head are required unless --all or --changed-file is used")
            paths = changed_paths(args.base, args.head)
        try:
            resolutions = resolve_paths(paths)
            selected = owners_for_paths(paths)
        except ValueError as exc:
            raise SystemExit(str(exc)) from exc

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
                    "pathClassifications": [
                        {
                            "path": item.path,
                            "kind": item.kind,
                            "owner": item.owner.name if item.owner else None,
                            "reason": item.reason,
                        }
                        for item in resolutions
                    ],
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
