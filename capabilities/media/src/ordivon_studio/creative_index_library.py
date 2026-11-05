"""Read-only projection of Creative Library catalogs and derived evidence.
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any

from .creative_index_source_utils import _json


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
                "sourceTreeStanding": work.get("sourceTreeStanding"),
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
