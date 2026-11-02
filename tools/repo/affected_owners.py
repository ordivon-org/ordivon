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


def _deployed_relocation_origins(owners: tuple[Owner, ...]) -> tuple[tuple[str, Owner], ...]:
    """Route deleted former source locators through the existing Structure R2 map.

    The current Owner manifest still owns verification; historical source
    names are not new owners. Only an exact deployed move whose origin is
    absent and whose target matches a current Owner can qualify old paths.
    """
    root = MANIFEST_PATH.resolve().parents[2]
    mapping = json.loads(
        (root / "docs/architecture/structure-r2-transition-r1.json").read_text(encoding="utf-8")
    )
    by_root = {owner.root: owner for owner in owners}
    aliases: list[tuple[str, Owner]] = []
    for row in mapping["mappings"]:
        if row.get("mode") != "move" or row.get("standing") != "DEPLOYED":
            continue
        sources = row.get("sourcePaths")
        targets = row.get("targetPaths")
        if not isinstance(sources, list) or not isinstance(targets, list):
            continue
        if len(sources) != 1 or len(targets) != 1:
            continue
        old, new = sources[0], targets[0]
        if not isinstance(old, str) or not isinstance(new, str):
            continue
        owner = by_root.get(new)
        if owner is None or owner.name != row.get("owner"):
            continue
        if (root / old).exists() or not (root / new).is_dir():
            continue
        aliases.append((old, owner))
    return tuple(aliases)


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
    relocated = _deployed_relocation_origins(owners)
    unregistered = sorted({
        path for raw in paths
        if (path := _normalize(raw)).startswith(EXECUTABLE_OWNER_ROOTS)
        and not any(path.startswith(owner.root) for owner in owners)
        and not any(path.startswith(source) for source, _ in relocated)
    })
    if unregistered:
        raise ValueError(f"unregistered owner path: {', '.join(unregistered)}")


def owners_for_paths(
    paths: Iterable[str], *, owners: tuple[Owner, ...] = OWNERS
) -> tuple[Owner, ...]:
    normalized = tuple(_normalize(path) for path in paths if path.strip())
    relocated = _deployed_relocation_origins(owners)
    if any(path in CROSS_CUTTING_PATHS for path in normalized):
        return owners
    # Repo mechanics (repo:ci) runs unconditionally before owner-task
    # selection. Only source-history also has an observed native Owner
    # consumer: Composition select-impact executes this exact producer.
    # Do not expand unrelated repo producer edits to all 18 domain queues.
    history_consumer_changed = "tools/repo/source_history_legos.py" in normalized
    # Existing extensions/chatgpt-skills-mcp consumers discover and read actual project
    # Skills under .agents/skills, outside the extensions/chatgpt-skills-mcp code root.
    project_skill_consumer_changed = any(
        path.startswith(".agents/skills/") for path in normalized
    )
    selected: list[Owner] = []
    for owner in owners:
        if (
            any(path.startswith(owner.root) for path in normalized)
            or any(
                path.startswith(source)
                for source, previous_owner in relocated
                for path in normalized
                if previous_owner.name == owner.name
            )
            or (history_consumer_changed and owner.name == "composition")
            or (project_skill_consumer_changed and owner.name == "skills")
            # Tagged Runtime release builds and attests Runtime artifacts.
            or (
                owner.name == "runtime"
                and ".github/workflows/runtime-release.yml" in normalized
            )
        ):
            selected.append(owner)
    return tuple(selected)


def requires_core_formal_verification(paths: Iterable[str]) -> bool:
    """Route proof-source edits to the *existing* Formal task, not a new Owner.

    The affected-owner queue alone can legitimately be empty for tools/formal/.
    A separate source-bound check is required so those edits never skip
    verification in the protected root GitHub workflow.
    """
    # The root task definition consumes the Formal verifier too:
    # editing the task wiring can change effects without changing proof files.
    return any(
        (normalized := _normalize(path)) == "mise.toml"
        or normalized.startswith("tools/formal/")
        # This exact Harness adapter is an executable input of the existing
        # Formal SOURCE_FILES readset. Changing it invalidates the native
        # timeout bridge proof regardless of owner-root classification.
        or normalized == "services/harness/src/ordivon_harness/plugin_gateway_effect.py"
        for path in paths
    )


def changed_paths(base: str, head: str) -> tuple[str, ...]:
    # Preserve both sides of a cross-owner move, rather than allowing Git's
    # similarity detection to hide the source owner from verification.
    proc = subprocess.run(
        [
            # SourceCut membership must be the actual immutable Git DAG, not
            # a locally installed refs/replace overlay. A replacement commit
            # could otherwise omit a changed Formal verifier source.
            "git", "--no-replace-objects", "diff", "--name-only", "--no-renames", "-z",
            "--diff-filter=ACDMRTUXB", f"{base}...{head}",
        ],
        # Object replacement and the separate legacy graft file can each
        # rewrite ancestry without changing the requested commit IDs. Both
        # are excluded from exact SourceCut delta/verification selection.
        # Protect the real working repository's immutable SourceCut from
        # inherited Git namespace/object-store overrides (e.g. agent tools
        # invoking this selector from another Git worktree). A different
        # repository must not determine required consumer verification.
        env={
            **{key: value for key, value in os.environ.items()
               if not key.startswith("GIT_")},
            "GIT_GRAFT_FILE": os.devnull,
        },
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
