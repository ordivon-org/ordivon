#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


class CompositionArchitectureError(ValueError):
    pass


REQUIRED_NODE_KEYS = {
    "id",
    "wave",
    "owner",
    "kind",
    "responsibility",
    "authorityBoundary",
    "files",
    "dependsOn",
    "acceptance",
}


def _nonempty_string(value: Any, *, field: str, node_id: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise CompositionArchitectureError(f"{node_id}: {field} must be a non-empty string")
    return value.strip()


def validate_graph(value: dict[str, Any]) -> None:
    if value.get("schemaVersion") != 1:
        raise CompositionArchitectureError("schemaVersion must be 1")
    if value.get("kind") != "ordivon.composition-architecture-lego-plan":
        raise CompositionArchitectureError("unexpected graph kind")

    nodes = value.get("nodes")
    if not isinstance(nodes, list) or not nodes:
        raise CompositionArchitectureError("nodes must be a non-empty list")

    by_id: dict[str, dict[str, Any]] = {}
    for raw in nodes:
        if not isinstance(raw, dict):
            raise CompositionArchitectureError("every node must be an object")
        missing = REQUIRED_NODE_KEYS - set(raw)
        if missing:
            raise CompositionArchitectureError(f"node missing keys: {sorted(missing)}")
        node_id = _nonempty_string(raw["id"], field="id", node_id="<unknown>")
        if node_id in by_id:
            raise CompositionArchitectureError(f"duplicate node id: {node_id}")
        for field in ("wave", "owner", "kind", "responsibility", "authorityBoundary"):
            _nonempty_string(raw[field], field=field, node_id=node_id)
        for field in ("files", "dependsOn", "acceptance"):
            rows = raw[field]
            if not isinstance(rows, list):
                raise CompositionArchitectureError(f"{node_id}: {field} must be a list")
            if field in {"files", "acceptance"} and not rows:
                raise CompositionArchitectureError(f"{node_id}: {field} must be non-empty")
            if not all(isinstance(item, str) and item.strip() for item in rows):
                raise CompositionArchitectureError(f"{node_id}: {field} entries must be strings")
        if raw["owner"] == "gateway":
            boundary = raw["authorityBoundary"].lower()
            if "non-authoritative" not in boundary:
                raise CompositionArchitectureError(
                    f"{node_id}: Gateway authority boundary must remain explicitly non-authoritative"
                )
        by_id[node_id] = raw

    known = set(by_id)
    for node_id, node in by_id.items():
        unknown = sorted(set(node["dependsOn"]) - known)
        if unknown:
            raise CompositionArchitectureError(
                f"{node_id}: unknown dependencies: {unknown}"
            )

    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(node_id: str) -> None:
        if node_id in visited:
            return
        if node_id in visiting:
            raise CompositionArchitectureError(f"dependency cycle includes {node_id}")
        visiting.add(node_id)
        for dependency in by_id[node_id]["dependsOn"]:
            visit(dependency)
        visiting.remove(node_id)
        visited.add(node_id)

    for node_id in sorted(by_id):
        visit(node_id)

    critical = value.get("criticalPath")
    if not isinstance(critical, list) or not critical:
        raise CompositionArchitectureError("criticalPath must be a non-empty list")
    if len(critical) != len(set(critical)):
        raise CompositionArchitectureError("criticalPath must not contain duplicates")
    unknown_critical = sorted(set(critical) - known)
    if unknown_critical:
        raise CompositionArchitectureError(
            f"criticalPath contains unknown nodes: {unknown_critical}"
        )
    on_demand = {
        node_id for node_id, node in by_id.items() if node["wave"] == "W6_ON_DEMAND"
    }
    if set(critical) & on_demand:
        raise CompositionArchitectureError("on-demand nodes must not enter criticalPath")

    parallel = value.get("initialParallelSet")
    if not isinstance(parallel, list) or not parallel:
        raise CompositionArchitectureError("initialParallelSet must be a non-empty list")
    unknown_parallel = sorted(set(parallel) - known)
    if unknown_parallel:
        raise CompositionArchitectureError(
            f"initialParallelSet contains unknown nodes: {unknown_parallel}"
        )

    do_not_build = value.get("doNotBuild")
    if not isinstance(do_not_build, list) or not do_not_build:
        raise CompositionArchitectureError("doNotBuild must be a non-empty list")
    if not all(isinstance(item, str) and item.strip() for item in do_not_build):
        raise CompositionArchitectureError("doNotBuild entries must be non-empty strings")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "graph",
        nargs="?",
        default="docs/architecture/ordivon-composition-architecture-lego-r1.json",
    )
    args = parser.parse_args()
    path = Path(args.graph)
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(value, dict):
            raise CompositionArchitectureError("graph root must be an object")
        validate_graph(value)
    except (OSError, json.JSONDecodeError, CompositionArchitectureError) as exc:
        print(f"composition architecture check failed: {exc}")
        return 2
    print(f"composition architecture check passed: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
