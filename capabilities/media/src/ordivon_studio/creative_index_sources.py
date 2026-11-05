"""Owner-native source projections for the derived Media creative navigation graph.

Artifact and Creative Library facts are read from their own snapshots. These functions
only add in-memory projection nodes/relations through the caller's graph builder; they
never become an alternative Artifact or Creative Library authority.
"""

from __future__ import annotations

import json
from collections.abc import Callable, Iterable, Mapping
from pathlib import Path
from typing import Any


def _json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def _walk_values(value: Any, key: str) -> Iterable[Any]:
    # DFS enter/leave markers preserve JSON preorder without Python recursion.
    # Only ancestors count as cycles: a shared child in a DAG is still visited
    # once per occurrence, matching the original recursive walk.
    pending = [(value, False)]
    ancestors: set[int] = set()
    while pending:
        current, leaving = pending.pop()
        if leaving:
            ancestors.remove(id(current))
            continue
        if not isinstance(current, (Mapping, list)):
            continue
        marker = id(current)
        if marker in ancestors:
            raise ValueError("creative-index owner metadata contains a cycle")
        ancestors.add(marker)
        pending.append((current, True))
        if isinstance(current, Mapping):
            if key in current:
                yield current[key]
            children = current.values()
        else:
            children = current
        pending.extend((child, False) for child in reversed(tuple(children)))


def _first_string(value: Any, key: str) -> str | None:
    for candidate in _walk_values(value, key):
        if isinstance(candidate, str) and candidate:
            return candidate
    return None


def project_artifact_source(
    artifact_root: Path,
    *,
    nodes: dict[str, dict[str, Any]],
    binding_to_equipment: Mapping[str, str],
    add_node: Callable[..., None],
    add_relation: Callable[..., None],
) -> None:
    """Only Artifact-delivery profiles, bindings and acceptance observations."""
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


def project_creative_library_source(
    creative_library_root: Path,
    *,
    nodes: dict[str, dict[str, Any]],
    add_node: Callable[..., None],
    add_relation: Callable[..., None],
) -> None:
    """Only source-owned library catalog/work evidence; never write it back."""
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
