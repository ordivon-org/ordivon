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

    def test_artifact_shadow_binding_becomes_profile_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            artifact = Path(directory)
            profiles = artifact / "artifact-delivery/shadow-profiles"
            examples = artifact / "artifact-delivery/examples"
            bindings = artifact / "artifact-delivery/shadow-bindings"
            profiles.mkdir(parents=True)
            examples.mkdir(parents=True)
            bindings.mkdir(parents=True)
            (profiles / "eda-spice-transient-measure-r1.json").write_text(json.dumps({
                "id": "eda-spice-transient-measure-r1",
                "status": "SHADOW_NOT_PRODUCTION_PROFILE",
                "classification": {"family": "electronic-design", "format": "SPICE-family text netlist", "purpose": ["simulation"]},
            }), encoding="utf-8")
            (bindings / "eda-spice-transient-local-r1.json").write_text(json.dumps({
                "id": "eda-spice-transient-local-r1",
                "profileId": "eda-spice-transient-measure-r1",
                "status": "LOCAL_LIVE_PROVEN",
                "bindings": {"nativeSimulator": {"tool": "ngspice"}},
            }), encoding="utf-8")
            index = build_creative_index(ROOT, artifact_root=artifact)
            relations = {(row["from"], row["type"], row["to"]) for row in index["relations"]}
            evidence = "evidence:artifact-binding:eda-spice-transient-local-r1"
            self.assertIn(("delivery-profile:eda-spice-transient-measure-r1", "evidencedBy", evidence), relations)
            query = query_creative_index(index, "circuit.simulate.transient")
            ids = {row["id"] for row in query["nodes"]}
            self.assertIn(evidence, ids)
            self.assertEqual(query["neighborhoodDepth"], 3)

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

    def test_workstation_derived_preview_projects_real_work_and_tool_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            workstation = Path(directory)
            preview = workstation / "artifacts/creative-library/derived/kicad-derived-preview-r1.json"
            preview.parent.mkdir(parents=True)
            preview.write_text(json.dumps({
                "schemaVersion": 1,
                "kind": "ordivon.creative-library.derived-preview",
                "row": {
                    "workId": "game:seen-not-approved-pcb",
                    "sourceRepo": "/tmp/game",
                    "sourceRevision": "a" * 40,
                    "sourcePath": "play/seen-not-approved-pcb",
                    "renderer": {"equipmentId": "laboratory-kicad-cli-10-0-5", "executable": "/tmp/kicad-cli"},
                    "standing": "DERIVED_VISUAL_PROJECTION_NOT_ORIGINAL_CARRIER"
                }
            }), encoding="utf-8")
            index = build_creative_index(ROOT, workstation_root=workstation)
            nodes = {row["id"]: row for row in index["nodes"]}
            relations = {(row["from"], row["type"], row["to"]) for row in index["relations"]}
            evidence = "evidence:workstation:kicad-derived-preview-r1"
            self.assertIn("work:game:seen-not-approved-pcb", nodes)
            self.assertIn(("work:game:seen-not-approved-pcb", "evidencedBy", evidence), relations)
            self.assertIn(("equipment:kicad", "evidencedBy", evidence), relations)

    def test_query_does_not_fan_out_through_source_hubs(self) -> None:
        index = {
            "truthRole": "test",
            "sources": [],
            "nodes": [
                {"id": "capability:match", "kind": "Capability", "name": "needle"},
                {"id": "source:x", "kind": "Source", "owner": "x"},
                {"id": "evidence:unrelated", "kind": "Evidence", "owner": "x"},
            ],
            "relations": [
                {"from": "capability:match", "type": "sourcedFrom", "to": "source:x", "evidence": "a"},
                {"from": "evidence:unrelated", "type": "sourcedFrom", "to": "source:x", "evidence": "b"},
            ],
        }
        result = query_creative_index(index, "needle")
        ids = {row["id"] for row in result["nodes"]}
        self.assertIn("source:x", ids)
        self.assertNotIn("evidence:unrelated", ids)

    def test_query_returns_matching_nodes_and_bounded_neighbors(self) -> None:
        index = build_creative_index(ROOT)
        result = query_creative_index(index, "scene.render")
        ids = {row["id"] for row in result["nodes"]}
        self.assertIn("capability:scene.render", ids)
        self.assertIn("equipment:blender", ids)


if __name__ == "__main__":
    unittest.main()
