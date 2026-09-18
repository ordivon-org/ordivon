#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GRAPH_DIR = ROOT / "knowledge" / "graphs"

GRAPH_FILES = [
    "ordivon-agent-service-r2.json",
    "ordivon-agent-service-r4-authority-delta.json",
    "ordivon-agent-service-r5-task-runtime-delta.json",
    "ordivon-agent-service-r6-evidence-delta.json",
    "ordivon-agent-service-r7-goal-board-delta.json",
    "ordivon-agent-service-r8-semantics-delta.json",
    "ordivon-agent-service-r9-governed-delivery-delta.json",
    "ordivon-agent-service-r10-trust-remote-delta.json",
    "ordivon-agent-service-r11-remote-evidence-delta.json",
    "ordivon-agent-service-r12-proved-failover-delta.json",
    "ordivon-agent-service-r13-provider-adapters-delta.json",
    "ordivon-agent-service-r14-interface-credential-effect-delta.json",
]

REFERENCE_KEYS = (
    "implementedNodes",
    "implementedBaseNodes",
    "clarifiedDeferredBaseNodes",
    "deferredBaseNodes",
    "refinedBaseNodes",
    "refinedPriorNodes",
)

# Explicitly reviewed compatibility aliases only. These do not authorize arbitrary label drift.
COMPATIBILITY_ALIASES = {
    ("N13", "EvidenceSemanticVerifier", "SemanticVerifier"),
}


class GraphIdentityError(ValueError):
    pass


def _load(name: str) -> dict:
    with (GRAPH_DIR / name).open(encoding="utf-8") as handle:
        return json.load(handle)


def _expect_current(current: dict[str, str], row: dict, *, source: str, key: str) -> None:
    node_id = row["nodeId"]
    label = row["label"]
    if node_id not in current:
        raise GraphIdentityError(f"{source}:{key}: unknown prior node {node_id} -> {label}")
    if current[node_id] != label:
        alias = (node_id, current[node_id], label)
        if alias in COMPATIBILITY_ALIASES:
            return
        raise GraphIdentityError(
            f"{source}:{key}: hard identity collision for {node_id}: "
            f"historical={current[node_id]!r}, referenced={label!r}"
        )


def validate() -> dict:
    base = _load(GRAPH_FILES[0])
    current: dict[str, str] = {}
    for row in base["nodes"]:
        node_id = row["id"]
        label = row["label"]
        if node_id in current:
            raise GraphIdentityError(f"{GRAPH_FILES[0]}: duplicate base node {node_id}")
        current[node_id] = label

    for name in GRAPH_FILES[1:]:
        data = _load(name)

        for key in ("changes", "refinedNodes"):
            for row in data.get(key, []):
                node_id = row["nodeId"]
                previous = row.get("previousLabel")
                label = row["label"]
                if node_id not in current:
                    raise GraphIdentityError(f"{name}:{key}: unknown node {node_id}")
                if previous is not None and current[node_id] != previous:
                    raise GraphIdentityError(
                        f"{name}:{key}: previousLabel mismatch for {node_id}: "
                        f"historical={current[node_id]!r}, declared={previous!r}"
                    )
                current[node_id] = label

        for key in REFERENCE_KEYS:
            for row in data.get(key, []):
                _expect_current(current, row, source=name, key=key)

        for row in data.get("discoveredNodes", []):
            node_id = row["nodeId"]
            label = row["label"]
            if node_id in current:
                raise GraphIdentityError(
                    f"{name}:discoveredNodes: duplicate node id {node_id}: "
                    f"historical={current[node_id]!r}, discovered={label!r}"
                )
            current[node_id] = label

    return {
        "schemaVersion": 1,
        "kind": "ordivon.agent-service-graph-identity-check",
        "status": "PASS",
        "graphFiles": len(GRAPH_FILES),
        "nodeCount": len(current),
        "nodes": dict(sorted(current.items(), key=lambda item: int(item[0][1:]))),
    }


def main() -> int:
    result = validate()
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
