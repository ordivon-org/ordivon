"""Read-only projection of Artifact-owned delivery profiles and evidence.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from pathlib import Path
from typing import Any

from .creative_index_source_utils import _first_string, _json


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
