from __future__ import annotations

import json
import subprocess
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from .creative_index_artifact import project_artifact_source
from .creative_index_library import project_creative_library_source
from .creative_index_source_values import _json

INDEX_KIND = "ordivon.media.creative-index"


def _revision(root: Path) -> str | None:
    try:
        return subprocess.run(
            ["git", "-C", str(root), "rev-parse", "HEAD"],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
        ).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return None


def build_creative_index(
    media_root: Path,
    *,
    artifact_root: Path | None = None,
    creative_library_root: Path | None = None,
) -> dict[str, Any]:
    """Build a deterministic, disposable graph over owner-native creative facts.

    The index is a projection only. It never changes the source registries and never
    upgrades physical presence, a bridge relation, or consumer evidence into domain truth.
    """
    media_root = media_root.resolve()
    artifact_root = artifact_root.resolve() if artifact_root and artifact_root.exists() else None
    creative_library_root = creative_library_root.resolve() if creative_library_root and creative_library_root.exists() else None

    nodes: dict[str, dict[str, Any]] = {}
    relations: dict[tuple[str, str, str, str], dict[str, Any]] = {}

    def add_node(node_id: str, kind: str, **data: Any) -> None:
        candidate = {"id": node_id, "kind": kind, **data}
        prior = nodes.get(node_id)
        if prior is not None and prior != candidate:
            raise ValueError(f"conflicting creative-index node: {node_id}")
        nodes[node_id] = candidate

    def add_relation(
        source: str, relation: str, target: str, *, evidence: str, detail: str | None = None
    ) -> None:
        key = (source, relation, target, evidence)
        row = {"from": source, "type": relation, "to": target, "evidence": evidence}
        if detail:
            row["detail"] = detail
        relations[key] = row

    sources: list[dict[str, Any]] = []
    for owner, repo in (("media", media_root), ("artifact", artifact_root), ("creative-library", creative_library_root)):
        if repo is None:
            continue
        revision = _revision(repo)
        source_id = f"source:{owner}"
        add_node(source_id, "Source", owner=owner, repository=str(repo), revision=revision)
        sources.append({"id": source_id, "repository": str(repo), "revision": revision})

    world_path = media_root / "research/equipment/equipment-world.json"
    world = _json(world_path)
    binding_to_equipment: dict[str, str] = {}
    for item in world.get("equipment", []):
        if not isinstance(item, dict) or not isinstance(item.get("id"), str):
            continue
        equipment_id = item["id"]
        node_id = f"equipment:{equipment_id}"
        add_node(
            node_id,
            "Equipment",
            owner="media",
            family=item.get("family"),
            retention=item.get("retention"),
            media=sorted(item.get("media", [])),
        )
        add_relation(node_id, "sourcedFrom", "source:media", evidence="research/equipment/equipment-world.json")
        for discovery in item.get("discovery", []):
            if isinstance(discovery, dict) and isinstance(discovery.get("equipmentId"), str):
                binding_to_equipment[discovery["equipmentId"]] = node_id
        for capability in item.get("capabilities", []):
            if not isinstance(capability, str):
                continue
            capability_id = f"capability:{capability}"
            add_node(capability_id, "Capability", name=capability)
            add_relation(node_id, "provides", capability_id, evidence="research/equipment/equipment-world.json")

    for production_path in sorted((media_root / "productions").glob("*/production.json")):
        production = _json(production_path)
        production_id = production.get("id")
        if not isinstance(production_id, str):
            continue
        work_id = f"work:media:{production_id}"
        output_kinds = sorted({o.get("kind") for o in production.get("outputs", []) if isinstance(o, dict) and isinstance(o.get("kind"), str)})
        add_node(
            work_id,
            "Work",
            owner="media",
            sourceIdentity=f"media:{production_id}",
            title=production.get("title", production_id),
            status=production.get("status"),
            outputKinds=output_kinds,
            sourcePath=str(production_path.relative_to(media_root)),
            collections=[],
        )
        add_relation(work_id, "sourcedFrom", "source:media", evidence=str(production_path.relative_to(media_root)))

    for collection_path in sorted(media_root.glob("play/**/*.collection.json")):
        collection = _json(collection_path)
        collection_id = collection.get("id")
        for member in collection.get("members", []):
            if not isinstance(member, dict):
                continue
            identity = member.get("sourceIdentity") or member.get("memberId")
            if not isinstance(identity, str):
                continue
            work_id = f"work:{identity}"
            node = nodes.get(work_id)
            collections = [collection_id] if isinstance(collection_id, str) else []
            payload = {
                "id": work_id,
                "kind": "Work",
                "owner": member.get("sourceOwner"),
                "sourceIdentity": identity,
                "title": member.get("title", identity),
                "status": "curated",
                "outputKinds": [],
                "sourcePath": str(collection_path.relative_to(media_root)),
                "collections": collections,
            }
            if node is None:
                nodes[work_id] = payload
            else:
                merged = sorted(set(node.get("collections", [])) | set(collections))
                node["collections"] = merged
            add_relation(work_id, "sourcedFrom", "source:media", evidence=str(collection_path.relative_to(media_root)))

    if artifact_root is not None:
        project_artifact_source(
            artifact_root,
            nodes=nodes,
            binding_to_equipment=binding_to_equipment,
            add_node=add_node,
            add_relation=add_relation,
        )

    bridge_path = media_root / "research/media/creative-delivery-bridges.json"
    bridges = _json(bridge_path)
    for bridge in bridges.get("relations", []):
        if not isinstance(bridge, dict):
            continue
        capability = bridge.get("capability")
        profile_id = bridge.get("profileId")
        if not isinstance(capability, str) or not isinstance(profile_id, str):
            continue
        source_id = f"capability:{capability}"
        target_id = f"delivery-profile:{profile_id}"
        if source_id in nodes and target_id in nodes:
            add_relation(source_id, "canFeed", target_id, evidence="research/media/creative-delivery-bridges.json")

    if creative_library_root is not None:
        project_creative_library_source(
            creative_library_root, nodes=nodes, add_node=add_node, add_relation=add_relation,
        )

    return {
        "schemaVersion": 1,
        "kind": INDEX_KIND,
        "truthRole": "rebuildable-derived-navigation-not-source-authority",
        "sources": sorted(sources, key=lambda row: row["id"]),
        "nodes": sorted(nodes.values(), key=lambda row: row["id"]),
        "relations": sorted(relations.values(), key=lambda row: (row["from"], row["type"], row["to"], row["evidence"])),
    }



def load_creative_index(path: Path) -> dict[str, Any]:
    value = _json(path)
    if value.get("kind") != INDEX_KIND:
        raise ValueError(f"not a creative index: {path}")
    return value


def query_creative_index(index: Mapping[str, Any], term: str) -> dict[str, Any]:
    needle = term.casefold()
    all_nodes = [node for node in index.get("nodes", []) if isinstance(node, Mapping)]
    all_relations = [relation for relation in index.get("relations", []) if isinstance(relation, Mapping)]
    node_kind = {str(node.get("id")): str(node.get("kind")) for node in all_nodes}
    selected_ids = {
        str(node["id"])
        for node in all_nodes
        if needle in json.dumps(node, ensure_ascii=False, sort_keys=True).casefold()
    }
    frontier = {node_id for node_id in selected_ids if node_kind.get(node_id) != "Source"}
    selected_relations: dict[tuple[str, str, str, str], Mapping[str, Any]] = {}
    max_depth = 3
    max_nodes = 250
    max_relations = 500
    truncated = False
    for _ in range(max_depth):
        if not frontier:
            break
        next_frontier: set[str] = set()
        for relation in all_relations:
            source = relation.get("from")
            target = relation.get("to")
            if source not in frontier and target not in frontier:
                continue
            key = (str(source), str(relation.get("type")), str(target), str(relation.get("evidence")))
            selected_relations[key] = relation
            for endpoint in (source, target):
                if isinstance(endpoint, str) and endpoint not in selected_ids:
                    if node_kind.get(endpoint) == "Source":
                        selected_ids.add(endpoint)
                    else:
                        next_frontier.add(endpoint)
            if len(selected_relations) >= max_relations:
                truncated = True
                break
        if truncated:
            break
        room = max_nodes - len(selected_ids)
        if room <= 0:
            truncated = True
            break
        ordered = sorted(next_frontier)
        if len(ordered) > room:
            ordered = ordered[:room]
            truncated = True
        selected_ids.update(ordered)
        frontier = set(ordered)
    nodes = [node for node in all_nodes if node.get("id") in selected_ids]
    relation_rows = sorted(selected_relations.values(), key=lambda row: (str(row.get("from")), str(row.get("type")), str(row.get("to")), str(row.get("evidence"))))
    return {
        "schemaVersion": 1,
        "kind": "ordivon.media.creative-index-query",
        "truthRole": index.get("truthRole"),
        "term": term,
        "neighborhoodDepth": max_depth,
        "truncated": truncated,
        "sources": list(index.get("sources", [])),
        "nodes": nodes,
        "relations": relation_rows,
    }
