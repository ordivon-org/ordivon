from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from ordivon_studio.creative_index import build_creative_index, query_creative_index

ROOT = Path(__file__).resolve().parents[1]


class CreativeIndexTests(unittest.TestCase):
    def test_media_only_projection_contains_equipment_capabilities_and_works(self) -> None:
        index = build_creative_index(ROOT)
        nodes = {row["id"]: row for row in index["nodes"]}
        relations = {(row["from"], row["type"], row["to"]) for row in index["relations"]}
        self.assertEqual(index["truthRole"], "rebuildable-derived-navigation-not-source-authority")
        self.assertIn("equipment:blender", nodes)
        self.assertIn("capability:asset.export.gltf", nodes)
        self.assertIn(("equipment:blender", "provides", "capability:asset.export.gltf"), relations)
        self.assertIn("work:media:runtime-introduction", nodes)
        self.assertIn("work:media:gesture-orrery", nodes)

    def test_artifact_profiles_and_bridges_join_without_copying_profile_semantics(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            artifact = Path(directory)
            (artifact / "artifact-delivery/shadow-profiles").mkdir(parents=True)
            (artifact / "artifact-delivery/examples").mkdir(parents=True)
            (artifact / "artifact-delivery/consumer-acceptance").mkdir(parents=True)
            (artifact / "artifact-delivery/shadow-profiles/design-3d-glb-static-mesh-r1.json").write_text(json.dumps({
                "id": "design-3d-glb-static-mesh-r1",
                "status": "SHADOW_NOT_PRODUCTION_PROFILE",
                "classification": {"family": "design-3d", "format": "GLB 2.0", "purpose": ["preview"]},
            }), encoding="utf-8")
            index = build_creative_index(ROOT, artifact_root=artifact)
            relations = {(row["from"], row["type"], row["to"]) for row in index["relations"]}
            self.assertIn((
                "capability:asset.export.gltf",
                "canFeed",
                "delivery-profile:design-3d-glb-static-mesh-r1",
            ), relations)

    def test_consumer_acceptance_connects_workstation_binding_to_media_equipment(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            artifact = Path(directory)
            (artifact / "artifact-delivery/shadow-profiles").mkdir(parents=True)
            (artifact / "artifact-delivery/examples").mkdir(parents=True)
            accept = artifact / "artifact-delivery/consumer-acceptance"
            accept.mkdir(parents=True)
            (artifact / "artifact-delivery/shadow-profiles/design-2d-aseprite-horizontal-sheet-r1.json").write_text(json.dumps({
                "id": "design-2d-aseprite-horizontal-sheet-r1",
                "status": "SHADOW_NOT_PRODUCTION_PROFILE",
                "classification": {"family": "design-2d", "format": "Aseprite", "purpose": ["game-runtime"]},
            }), encoding="utf-8")
            (accept / "a.json").write_text(json.dumps({
                "id": "accept-a",
                "standing": "PASS",
                "artifactOwnedAuthorities": {"profile": {"id": "design-2d-aseprite-horizontal-sheet-r1"}},
                "workstationBinding": {"equipmentId": "game-aseprite-e1"},
                "consumer": {"repository": "/tmp/game", "revision": "a" * 40},
            }), encoding="utf-8")
            index = build_creative_index(ROOT, artifact_root=artifact)
            relations = {(row["from"], row["type"], row["to"]) for row in index["relations"]}
            evidence = "evidence:artifact:accept-a"
            self.assertIn(("equipment:aseprite", "evidencedBy", evidence), relations)
            self.assertIn(("delivery-profile:design-2d-aseprite-horizontal-sheet-r1", "evidencedBy", evidence), relations)

    def test_agent_surface_builds_fresh_query_projection(self) -> None:
        from ordivon_studio.agent_surface import execute_surface_action
        result = execute_surface_action("studio_creative_index_query", {"term": "blender"}, root=ROOT)
        ids = {row["id"] for row in result["nodes"]}
        self.assertIn("equipment:blender", ids)
        self.assertTrue(any(row["id"] == "source:media" for row in result["sources"]))

    def test_query_returns_matching_nodes_and_one_hop_neighbors(self) -> None:
        index = build_creative_index(ROOT)
        result = query_creative_index(index, "scene.render")
        ids = {row["id"] for row in result["nodes"]}
        self.assertIn("capability:scene.render", ids)
        self.assertIn("equipment:blender", ids)


if __name__ == "__main__":
    unittest.main()
