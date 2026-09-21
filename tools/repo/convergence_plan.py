#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import tomllib
from collections import deque
from pathlib import Path
from typing import Iterable

import affected_owners

DEPENDENCY_PATH = Path(__file__).with_name("dependency_contracts.toml")


def _git(*args: str) -> str:
    proc = subprocess.run(
        ["git", *args],
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return proc.stdout.strip()


def _digest(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def load_dependency_graph(
    owners: tuple[affected_owners.Owner, ...] = affected_owners.OWNERS,
    path: Path = DEPENDENCY_PATH,
) -> dict[str, set[str]]:
    names = {owner.name for owner in owners}
    graph = {name: set() for name in names}
    data = tomllib.loads(path.read_text(encoding="utf-8"))
    if data.get("schema_version") != 1:
        raise ValueError("dependency contract schema_version must be 1")
    if data.get("truth_role") != "repository-boundary-policy-not-domain-authority":
        raise ValueError("dependency contract truth_role must remain repository-boundary policy")
    seams = data.get("seams", [])
    if not isinstance(seams, list):
        raise ValueError("dependency contract seams must be a list")
    for index, seam in enumerate(seams):
        if not isinstance(seam, dict):
            raise ValueError(f"dependency seam {index} must be a table")
        left = seam.get("from_owner")
        right = seam.get("to_owner")
        if left not in names or right not in names:
            raise ValueError(f"dependency seam {index} references unknown owner: {left!r}->{right!r}")
        if left == right:
            raise ValueError(f"dependency seam {index} must cross owner boundaries")
        graph[left].add(right)
        graph[right].add(left)
    return graph


def connected_closure(seeds: Iterable[str], graph: dict[str, set[str]]) -> tuple[str, ...]:
    queue = deque(sorted(set(seeds)))
    seen: set[str] = set(queue)
    while queue:
        node = queue.popleft()
        for neighbor in sorted(graph[node]):
            if neighbor not in seen:
                seen.add(neighbor)
                queue.append(neighbor)
    return tuple(sorted(seen))


def component_id(members: Iterable[str]) -> str:
    members = tuple(sorted(set(members)))
    return "owner-component:" + "+".join(members)


def _is_cross_cutting(paths: Iterable[str]) -> bool:
    return any(
        affected_owners._normalize(path) in affected_owners.CROSS_CUTTING_PATHS
        for path in paths
    )


def build_plan(
    *,
    base: str | None = None,
    head: str | None = None,
    changed_files: Iterable[str] = (),
    owners: tuple[affected_owners.Owner, ...] = affected_owners.OWNERS,
    dependency_path: Path = DEPENDENCY_PATH,
) -> dict[str, object]:
    explicit_paths = tuple(path for path in changed_files if path.strip())
    if explicit_paths:
        paths = explicit_paths
        base_revision = None
        head_revision = None
        head_tree = None
    else:
        if not base or not head:
            raise ValueError("base and head are required when changed_files is empty")
        base_revision = _git("rev-parse", f"{base}^{{commit}}")
        head_revision = _git("rev-parse", f"{head}^{{commit}}")
        head_tree = _git("rev-parse", f"{head_revision}^{{tree}}")
        paths = affected_owners.changed_paths(base_revision, head_revision)

    direct = affected_owners.owners_for_paths(paths)
    direct_names = tuple(owner.name for owner in direct)
    cross_cutting = _is_cross_cutting(paths)
    graph = load_dependency_graph(owners=owners, path=dependency_path)

    if cross_cutting:
        verification_names = tuple(sorted(owner.name for owner in owners))
        scope_ids = ("owner-component:ALL",)
        queue_class = "CROSS_CUTTING"
    elif direct_names:
        verification_names = connected_closure(direct_names, graph)
        scope_ids = tuple(
            sorted(
                {
                    component_id(connected_closure((name,), graph))
                    for name in direct_names
                }
            )
        )
        queue_class = "SCOPED"
    else:
        verification_names = ()
        scope_ids = ()
        queue_class = "REPOSITORY_ONLY"

    by_name = {owner.name: owner for owner in owners}
    verify_tasks = tuple(by_name[name].task for name in verification_names)
    queue_verify_tasks = tuple(by_name[name].queue_task for name in verification_names)
    declared_edges = sorted(
        {
            tuple(sorted((left, right)))
            for left, neighbors in graph.items()
            for right in neighbors
            if left != right
        }
    )

    return {
        "schemaVersion": 1,
        "kind": "ordivon.repo-convergence-plan",
        "truthRole": "repository-convergence-projection-not-merge-or-domain-authority",
        "queueClass": queue_class,
        "baseRevision": base_revision,
        "headRevision": head_revision,
        "headTree": head_tree,
        "changedPaths": list(paths),
        "directOwners": list(direct_names),
        "verificationOwners": list(verification_names),
        "verifyTasks": list(verify_tasks),
        "queueVerifyTasks": list(queue_verify_tasks),
        "scopeIds": list(scope_ids),
        "crossCutting": cross_cutting,
        "dependencyStanding": "CONSERVATIVE_UNDIRECTED_CLOSURE_OF_DECLARED_OWNER_SEAMS",
        "independenceClaim": "NOT_ESTABLISHED_BY_THIS_PROJECTION",
        "ownerManifestDigest": _digest(affected_owners.MANIFEST_PATH),
        "dependencyContractDigest": _digest(dependency_path),
        "declaredInteractionEdges": [list(edge) for edge in declared_edges],
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Project one Git candidate into conservative Ordivon convergence scopes."
    )
    parser.add_argument("--base")
    parser.add_argument("--head")
    parser.add_argument("--changed-file", action="append", default=[])
    parser.add_argument(
        "--format", choices=("json", "tasks", "queue-tasks", "scopes"), default="json"
    )
    return parser


def main() -> int:
    args = _parser().parse_args()
    try:
        plan = build_plan(base=args.base, head=args.head, changed_files=args.changed_file)
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc
    if args.format == "tasks":
        for task in plan["verifyTasks"]:
            print(task)
    elif args.format == "queue-tasks":
        for task in plan["queueVerifyTasks"]:
            print(task)
    elif args.format == "scopes":
        for scope in plan["scopeIds"]:
            print(scope)
    else:
        print(json.dumps(plan, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
