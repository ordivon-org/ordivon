from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any, Iterable, Mapping


INDEX_KIND = "ordivon.media.creative-index"


def _json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


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


def _walk_values(value: Any, key: str) -> Iterable[Any]:
    if isinstance(value, Mapping):
        if key in value:
            yield value[key]
        for child in value.values():
            yield from _walk_values(child, key)
    elif isinstance(value, list):
        for child in value:
            yield from _walk_values(child, key)


def _first_string(value: Any, key: str) -> str | None:
    for candidate in _walk_values(value, key):
        if isinstance(candidate, str) and candidate:
            return candidate
    return None


def build_creative_index(
    media_root: Path,
    *,
    artifact_root: Path | None = None,
    workstation_root: Path | None = None,
) -> dict[str, Any]:
    """Build a deterministic, disposable graph over owner-native creative facts.

    The index is a projection only. It never changes the source registries and never
    upgrades physical presence, a bridge relation, or consumer evidence into domain truth.
    """
    media_root = media_root.resolve()
    artifact_root = artifact_root.resolve() if artifact_root and artifact_root.exists() else None
    workstation_root = workstation_root.resolve() if workstation_root and workstation_root.exists() else None

    nodes: dict[str, dict[str, Any]] = {}
    relations: dict[tuple[str, str, str, str], dict[str, Any]] = {}

    def add_node(node_id: str, kind: str, **data: Any) -> None:
        candidate = {"id": node_id, "kind": kind, **data}
        prior = nodes.get(node_id)
        if prior is not None and prior != candidate:
            raise ValueError(f"conflicting creative-index node: {node_id}")
        nodes[node_id] = candidate

    def add_relation(source: str, relation: str, target: str, *, evidence: str) -> None:
        key = (source, relation, target, evidence)
        relations[key] = {"from": source, "type": relation, "to": target, "evidence": evidence}

    sources: list[dict[str, Any]] = []
    for owner, repo in (("media", media_root), ("artifact", artifact_root), ("workstation", workstation_root)):
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
        profile_paths = list((artifact_root / "artifact-delivery/examples").glob("*.json"))
        profile_paths += list((artifact_root / "artifact-delivery/shadow-profiles").glob("*.json"))
        for profile_path in sorted(profile_paths):
            profile = _json(profile_path)
            profile_id = profile.get("id")
            if not isinstance(profile_id, str):
                continue
            if "artifactClass" in profile:
                artifact_class = profile.get("artifactClass")
                primary = profile.get("primaryOutput") if isinstance(profile.get("primaryOutput"), dict) else {}
                fmt = primary.get("format")
                status = "PRODUCTION_PROFILE"
                purpose = [primary.get("purpose")] if isinstance(primary.get("purpose"), str) else []
                renderer = profile.get("targetRenderer") if isinstance(profile.get("targetRenderer"), dict) else None
            elif "classification" in profile:
                classification = profile.get("classification") if isinstance(profile.get("classification"), dict) else {}
                artifact_class = classification.get("family")
                fmt = classification.get("format")
                status = profile.get("status", "SHADOW_NOT_PRODUCTION_PROFILE")
                purpose = sorted(p for p in classification.get("purpose", []) if isinstance(p, str))
                renderer = None
            else:
                continue
            profile_node = f"delivery-profile:{profile_id}"
            add_node(
                profile_node,
                "DeliveryProfile",
                owner="artifact",
                profileId=profile_id,
                artifactClass=artifact_class,
                format=fmt,
                status=status,
                purpose=purpose,
                sourcePath=str(profile_path.relative_to(artifact_root)),
            )
            add_relation(profile_node, "sourcedFrom", "source:artifact", evidence=str(profile_path.relative_to(artifact_root)))
            if renderer and isinstance(renderer.get("name"), str):
                renderer_id = "equipment:artifact:" + renderer["name"].lower().replace(" ", "-")
                add_node(
                    renderer_id,
                    "Equipment",
                    owner="artifact",
                    family="target-renderer",
                    retention="external-owner",
                    displayName=renderer["name"],
                    platform=renderer.get("platform"),
                )
                add_relation(renderer_id, "renders", profile_node, evidence=str(profile_path.relative_to(artifact_root)))
                add_relation(renderer_id, "sourcedFrom", "source:artifact", evidence=str(profile_path.relative_to(artifact_root)))

        binding_dir = artifact_root / "artifact-delivery/shadow-bindings"
        if binding_dir.is_dir():
            for binding_path in sorted(binding_dir.glob("*.json")):
                binding = _json(binding_path)
                binding_id = binding.get("id")
                profile_id = binding.get("profileId")
                if not isinstance(binding_id, str) or not isinstance(profile_id, str):
                    continue
                evidence_id = f"evidence:artifact-binding:{binding_id}"
                tool_names = sorted({
                    str(item.get("tool"))
                    for item in binding.get("bindings", {}).values()
                    if isinstance(item, dict) and isinstance(item.get("tool"), str)
                }) if isinstance(binding.get("bindings"), dict) else []
                add_node(
                    evidence_id,
                    "Evidence",
                    owner="artifact",
                    evidenceKind="capability-binding",
                    standing=binding.get("status"),
                    tools=tool_names,
                    sourcePath=str(binding_path.relative_to(artifact_root)),
                )
                add_relation(evidence_id, "sourcedFrom", "source:artifact", evidence=str(binding_path.relative_to(artifact_root)))
                profile_node = f"delivery-profile:{profile_id}"
                if profile_node in nodes:
                    add_relation(profile_node, "evidencedBy", evidence_id, evidence=str(binding_path.relative_to(artifact_root)))

        acceptance_dir = artifact_root / "artifact-delivery/consumer-acceptance"
        if acceptance_dir.is_dir():
            for acceptance_path in sorted(acceptance_dir.glob("*.json")):
                acceptance = _json(acceptance_path)
                acceptance_id = acceptance.get("id")
                if not isinstance(acceptance_id, str):
                    continue
                evidence_id = f"evidence:artifact:{acceptance_id}"
                profile_id = None
                owned = acceptance.get("artifactOwnedAuthorities")
                if isinstance(owned, dict) and isinstance(owned.get("profile"), dict):
                    profile_id = owned["profile"].get("id")
                profile_id = profile_id if isinstance(profile_id, str) else _first_string(acceptance, "profileId")
                consumer = acceptance.get("consumer") if isinstance(acceptance.get("consumer"), dict) else {}
                add_node(
                    evidence_id,
                    "Evidence",
                    owner="artifact",
                    evidenceKind="consumer-acceptance",
                    standing=acceptance.get("standing"),
                    consumerRepository=consumer.get("repository"),
                    consumerRevision=consumer.get("revision"),
                    purpose=consumer.get("purpose"),
                    sourcePath=str(acceptance_path.relative_to(artifact_root)),
                )
                add_relation(evidence_id, "sourcedFrom", "source:artifact", evidence=str(acceptance_path.relative_to(artifact_root)))
                if isinstance(profile_id, str) and f"delivery-profile:{profile_id}" in nodes:
                    add_relation(f"delivery-profile:{profile_id}", "evidencedBy", evidence_id, evidence=str(acceptance_path.relative_to(artifact_root)))
                binding = acceptance.get("workstationBinding") if isinstance(acceptance.get("workstationBinding"), dict) else {}
                binding_id = binding.get("equipmentId")
                media_equipment_id = binding_to_equipment.get(binding_id) if isinstance(binding_id, str) else None
                if media_equipment_id:
                    add_relation(media_equipment_id, "evidencedBy", evidence_id, evidence=str(acceptance_path.relative_to(artifact_root)))

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

    if workstation_root is not None:
        for candidate in (
            workstation_root / "artifacts/creative-library/evidence/acceptance-r1.json",
            workstation_root / "artifacts/creative-library/derived/godot-derived-previews-r1.json",
            workstation_root / "artifacts/creative-library/derived/kicad-derived-preview-r1.json",
        ):
            if not candidate.is_file():
                continue
            value = _json(candidate)
            row = value.get("row") if isinstance(value.get("row"), dict) else None
            evidence_id = "evidence:workstation:" + candidate.stem
            standing = value.get("standing") or value.get("status")
            renderer_tool = None
            work_id_value = None
            source_repository = None
            source_revision = None
            source_path_value = None
            if row is not None:
                standing = row.get("standing") or standing
                renderer = row.get("renderer") if isinstance(row.get("renderer"), dict) else {}
                renderer_tool = renderer.get("executable") or renderer.get("equipmentId")
                work_id_value = row.get("workId")
                source_repository = row.get("sourceRepo")
                source_revision = row.get("sourceRevision")
                source_path_value = row.get("sourcePath")
            add_node(
                evidence_id,
                "Evidence",
                owner="workstation",
                evidenceKind=value.get("kind", "creative-library"),
                standing=standing,
                renderer=renderer_tool,
                sourcePath=str(candidate.relative_to(workstation_root)),
            )
            add_relation(evidence_id, "sourcedFrom", "source:workstation", evidence=str(candidate.relative_to(workstation_root)))
            if isinstance(work_id_value, str):
                work_id = f"work:{work_id_value}"
                add_node(
                    work_id,
                    "Work",
                    owner=work_id_value.split(":", 1)[0] if ":" in work_id_value else "external",
                    sourceIdentity=work_id_value,
                    title=work_id_value.split(":", 1)[-1].replace("-", " ").title(),
                    status="historical-source",
                    outputKinds=[],
                    sourcePath=source_path_value,
                    sourceRepository=source_repository,
                    sourceRevision=source_revision,
                    collections=["workstation:creative-library"],
                )
                add_relation(work_id, "evidencedBy", evidence_id, evidence=str(candidate.relative_to(workstation_root)))
            rendered = str(renderer_tool or "").lower()
            if "kicad" in rendered and "equipment:kicad" in nodes:
                add_relation("equipment:kicad", "evidencedBy", evidence_id, evidence=str(candidate.relative_to(workstation_root)))
            if "ngspice" in rendered and "equipment:ngspice" in nodes:
                add_relation("equipment:ngspice", "evidencedBy", evidence_id, evidence=str(candidate.relative_to(workstation_root)))

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
