from __future__ import annotations

import json
import subprocess
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any

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

    if creative_library_root is not None:
        catalog_path = creative_library_root / "artifacts/creative-library/catalog-v1.json"
        if catalog_path.is_file():
            catalog = _json(catalog_path)
            catalog_relpath = str(catalog_path.relative_to(creative_library_root))
            summary = catalog.get("summary") if isinstance(catalog.get("summary"), dict) else {}
            catalog_evidence_id = "evidence:creative-library:catalog-v1"
            add_node(
                catalog_evidence_id,
                "Evidence",
                owner="media",
                evidenceKind="creative-library-catalog",
                standing=catalog.get("archiveStanding"),
                catalogDigest=catalog.get("catalogDigest"),
                workCount=summary.get("workCount"),
                carrierCount=summary.get("carrierCount"),
                relationCount=summary.get("relationCount"),
                sourcePath=catalog_relpath,
            )
            add_relation(catalog_evidence_id, "sourcedFrom", "source:creative-library", evidence=catalog_relpath)

            for work in catalog.get("works", []):
                if not isinstance(work, dict) or not isinstance(work.get("workId"), str):
                    continue
                identity = work["workId"]
                work_id = f"work:{identity}"
                hero = work.get("heroCarrier") if isinstance(work.get("heroCarrier"), dict) else {}
                launch = work.get("launchCarrier") if isinstance(work.get("launchCarrier"), dict) else {}
                projection = {
                    "catalogDigest": catalog.get("catalogDigest"),
                    "sourceRepository": work.get("sourceRepo"),
                    "sourceRevision": work.get("sourceRevision"),
                    "sourcePath": work.get("sourcePath"),
                    "sourceKind": work.get("sourceKind"),
                    "sourceTreeDigest": work.get("sourceTreeDigest"),
                    "modalities": sorted(value for value in work.get("modalities", []) if isinstance(value, str)),
                    "room": work.get("room"),
                    "series": work.get("series"),
                    "carrierCount": work.get("carrierCount"),
                    "evidenceLevel": work.get("evidenceLevel"),
                    "humanStanding": work.get("humanStanding"),
                    "physicalStanding": work.get("physicalStanding"),
                    "featured": work.get("featured"),
                    "hasDerivedPreview": work.get("derivedPreview") is not None,
                    "heroCarrier": {k: hero.get(k) for k in ("kind", "relativePath") if hero.get(k) is not None},
                    "launchCarrier": {k: launch.get(k) for k in ("kind", "relativePath") if launch.get(k) is not None},
                }
                existing = nodes.get(work_id)
                if existing is None:
                    add_node(
                        work_id,
                        "Work",
                        owner=work.get("owner"),
                        sourceIdentity=identity,
                        title=work.get("title", identity),
                        status=work.get("status"),
                        outputKinds=[],
                        sourcePath=work.get("sourcePath"),
                        collections=["creative-library"],
                        catalogProjection=projection,
                    )
                elif existing.get("kind") == "Work":
                    existing["collections"] = sorted(
                        set(existing.get("collections", [])) | {"creative-library"}
                    )
                    existing["catalogProjection"] = projection
                else:
                    raise ValueError(f"creative-library work identity collides with non-Work node: {work_id}")
                add_relation(work_id, "sourcedFrom", "source:creative-library", evidence=catalog_relpath)

            relation_map = {"DERIVATIVE_OF": "derivativeOf", "CONSUMER_OF": "consumerOf"}
            for relation in catalog.get("relations", []):
                if not isinstance(relation, dict):
                    continue
                parent = relation.get("parent_work_id")
                child = relation.get("child_work_id")
                relation_type = relation_map.get(str(relation.get("relation_type")))
                if not isinstance(parent, str) or not isinstance(child, str) or relation_type is None:
                    continue
                parent_id = f"work:{parent}"
                child_id = f"work:{child}"
                if parent_id not in nodes or child_id not in nodes:
                    continue
                add_relation(
                    child_id, relation_type, parent_id, evidence=catalog_relpath,
                    detail=str(relation.get("evidence_summary")) if relation.get("evidence_summary") else None,
                )

        evidence_candidates = list(
            (creative_library_root / "artifacts/creative-library/evidence").glob("*.json")
        )
        evidence_candidates.extend([
            creative_library_root / "artifacts/creative-library/derived/godot-derived-previews-r1.json",
            creative_library_root / "artifacts/creative-library/derived/kicad-derived-preview-r1.json",
            creative_library_root / "artifacts/creative-library/derived/cad-cross-work-derived-preview-r1.json",
        ])
        for candidate in sorted(set(evidence_candidates)):
            if not candidate.is_file():
                continue
            value = _json(candidate)
            row = value.get("row") if isinstance(value.get("row"), dict) else None
            evidence_id = "evidence:creative-library:" + candidate.stem
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
            derived_projection = {}
            if row is not None:
                for key in (
                    "sourceCarrier",
                    "sourceCarrierSha256",
                    "previewSourceWorkId",
                    "previewSourceRevision",
                    "previewSourcePath",
                    "previewSourceBlobObjectId",
                    "sharedGeometryPath",
                    "sharedGeometryByteEqual",
                    "derivedPath",
                    "sha256",
                    "truthBoundary",
                ):
                    if row.get(key) is not None:
                        derived_projection[key] = row.get(key)
                generation_evidence = row.get("previewGenerationEvidence")
                if isinstance(generation_evidence, list):
                    derived_projection["previewGenerationEvidence"] = [
                        str(item) for item in generation_evidence if isinstance(item, str)
                    ]
            add_node(
                evidence_id,
                "Evidence",
                owner="media",
                evidenceKind=value.get("kind", "creative-library"),
                standing=standing,
                renderer=renderer_tool,
                sourcePath=str(candidate.relative_to(creative_library_root)),
                derivedProjection=derived_projection or None,
            )
            add_relation(evidence_id, "sourcedFrom", "source:creative-library", evidence=str(candidate.relative_to(creative_library_root)))
            if isinstance(work_id_value, str):
                work_id = f"work:{work_id_value}"
                existing_work = nodes.get(work_id)
                if existing_work is None:
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
                        collections=["creative-library"],
                    )
                elif existing_work.get("kind") == "Work":
                    existing_work["collections"] = sorted(
                        set(existing_work.get("collections", [])) | {"creative-library"}
                    )
                else:
                    raise ValueError(f"derived-preview work identity collides with non-Work node: {work_id}")
                add_relation(work_id, "evidencedBy", evidence_id, evidence=str(candidate.relative_to(creative_library_root)))
            rendered = str(renderer_tool or "").lower()
            if "kicad" in rendered and "equipment:kicad" in nodes:
                add_relation("equipment:kicad", "evidencedBy", evidence_id, evidence=str(candidate.relative_to(creative_library_root)))
            if "ngspice" in rendered and "equipment:ngspice" in nodes:
                add_relation("equipment:ngspice", "evidencedBy", evidence_id, evidence=str(candidate.relative_to(creative_library_root)))

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
