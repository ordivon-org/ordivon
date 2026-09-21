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

    def test_zero_to_one_delivery_bridges_are_declared(self) -> None:
        bridges=json.loads((ROOT / "research/media/creative-delivery-bridges.json").read_text())
        pairs={(row["capability"],row["profileId"]) for row in bridges["relations"]}
        self.assertTrue({
            ("dataset.export.parquet","dataset-parquet-flat-r1"),
            ("geospatial.export.geopackage","geospatial-geopackage-point-r1"),
            ("web.capture.response.warc","web-archive-warc-response-r1"),
            ("message.compose.rfc5322","message-internet-text-r1"),
            ("world2d.canonicalize.tmj","design-2d-tiled-tmj-object-map-r1"),
        } <= pairs)

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

    def test_cadquery_step_export_joins_bounded_artifact_step_profile(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            artifact = Path(directory)
            profiles = artifact / "artifact-delivery/shadow-profiles"
            examples = artifact / "artifact-delivery/examples"
            bindings = artifact / "artifact-delivery/shadow-bindings"
            profiles.mkdir(parents=True)
            examples.mkdir(parents=True)
            bindings.mkdir(parents=True)
            (profiles / "design-3d-step-solid-r1.json").write_text(json.dumps({
                "id": "design-3d-step-solid-r1",
                "status": "SHADOW_NOT_PRODUCTION_PROFILE",
                "classification": {
                    "family": "design-3d",
                    "format": "STEP Part 21 clear text (.step/.stp)",
                    "purpose": ["cad-exchange", "verification"],
                },
            }), encoding="utf-8")
            (bindings / "cad-step-solid-local-r1.json").write_text(json.dumps({
                "id": "cad-step-solid-local-r1",
                "profileId": "design-3d-step-solid-r1",
                "status": "LOCAL_LIVE_PROVEN",
                "bindings": {
                    "targetCadConsumer": {"tool": "FreeCAD"},
                    "structuralReader": {"tool": "Open CASCADE"},
                },
            }), encoding="utf-8")
            index = build_creative_index(ROOT, artifact_root=artifact)
            nodes = {row["id"]: row for row in index["nodes"]}
            relations = {(row["from"], row["type"], row["to"]) for row in index["relations"]}
            profile = "delivery-profile:design-3d-step-solid-r1"
            evidence = "evidence:artifact-binding:cad-step-solid-local-r1"
            self.assertIn(("equipment:cadquery", "provides", "capability:cad.export.step"), relations)
            self.assertIn(("capability:cad.export.step", "canFeed", profile), relations)
            self.assertIn((profile, "evidencedBy", evidence), relations)
            self.assertEqual(nodes[profile]["status"], "SHADOW_NOT_PRODUCTION_PROFILE")
            self.assertEqual(nodes[evidence]["standing"], "LOCAL_LIVE_PROVEN")
            self.assertEqual(nodes[evidence]["tools"], ["FreeCAD", "Open CASCADE"])
            query = query_creative_index(index, "cad.export.step")
            ids = {row["id"] for row in query["nodes"]}
            self.assertIn("equipment:cadquery", ids)
            self.assertIn(profile, ids)
            self.assertIn(evidence, ids)

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

    def test_creative_library_catalog_projects_works_without_copying_carriers(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            workstation = Path(directory)
            catalog = workstation / "artifacts/creative-library/catalog-v1.json"
            catalog.parent.mkdir(parents=True)
            catalog.write_text(json.dumps({
                "archiveStanding": "SOURCE_COMPLETE_DECLARED_SCOPE_R1",
                "catalogDigest": "sha256:" + "a" * 64,
                "summary": {"workCount": 1, "carrierCount": 99, "relationCount": 0},
                "works": [{
                    "workId": "game:batch-zero", "title": "Batch Zero", "owner": "Game",
                    "status": "historical-jam-prototype", "sourceRepo": "/tmp/game",
                    "sourceRevision": "b" * 40, "sourcePath": "alpha20-ercot",
                    "sourceKind": "reverse_census_git_history", "sourceTreeDigest": "sha256:" + "c" * 64,
                    "modalities": ["html", "text"], "room": "playable", "series": "alpha20",
                    "carrierCount": 99, "evidenceLevel": "A", "humanStanding": "NOT_ASSESSED",
                    "physicalStanding": "DIGITAL_ONLY", "featured": False,
                    "heroCarrier": {"kind": "html", "relativePath": "index.html", "objectId": "x"},
                    "launchCarrier": {"kind": "html", "relativePath": "index.html", "objectId": "x"},
                    "carriers": [{"relativePath": str(i), "kind": "source"} for i in range(99)]
                }],
                "relations": [],
            }), encoding="utf-8")
            index = build_creative_index(ROOT, creative_library_root=workstation)
            node = next(row for row in index["nodes"] if row["id"] == "work:game:batch-zero")
            self.assertEqual(node["title"], "Batch Zero")
            self.assertEqual(node["catalogProjection"]["carrierCount"], 99)
            self.assertEqual(node["catalogProjection"]["modalities"], ["html", "text"])
            self.assertNotIn("carriers", node)
            self.assertNotIn("carriers", node["catalogProjection"])
            self.assertEqual(node["catalogProjection"]["heroCarrier"], {"kind": "html", "relativePath": "index.html"})

    def test_creative_library_catalog_membership_does_not_create_shared_query_hub(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            workstation = Path(directory)
            catalog = workstation / "artifacts/creative-library/catalog-v1.json"
            catalog.parent.mkdir(parents=True)
            catalog.write_text(json.dumps({
                "archiveStanding": "SOURCE_COMPLETE_DECLARED_SCOPE_R1",
                "catalogDigest": "sha256:" + "a" * 64,
                "summary": {"workCount": 2, "carrierCount": 2, "relationCount": 0},
                "works": [
                    {"workId": "game:needle-work", "title": "Needle Work", "owner": "Game", "carrierCount": 1},
                    {"workId": "game:unrelated-work", "title": "Unrelated Work", "owner": "Game", "carrierCount": 1},
                ],
                "relations": [],
            }), encoding="utf-8")
            index = build_creative_index(ROOT, creative_library_root=workstation)
            result = query_creative_index(index, "Needle Work")
            ids = {row["id"] for row in result["nodes"]}
            self.assertIn("work:game:needle-work", ids)
            self.assertIn("source:creative-library", ids)
            self.assertNotIn("work:game:unrelated-work", ids)

    def test_creative_library_catalog_never_overwrites_owner_native_work(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            workstation = Path(directory)
            catalog = workstation / "artifacts/creative-library/catalog-v1.json"
            catalog.parent.mkdir(parents=True)
            catalog.write_text(json.dumps({
                "archiveStanding": "SOURCE_COMPLETE_DECLARED_SCOPE_R1",
                "catalogDigest": "sha256:" + "a" * 64,
                "summary": {"workCount": 1, "carrierCount": 1, "relationCount": 0},
                "works": [{
                    "workId": "media:runtime-introduction", "title": "Historical Runtime Title", "owner": "Media",
                    "status": "historical-recovered", "sourceRepo": "/tmp/media",
                    "sourceRevision": "b" * 40, "sourcePath": "old/runtime", "modalities": ["video"],
                    "carrierCount": 1
                }],
                "relations": [],
            }), encoding="utf-8")
            index = build_creative_index(ROOT, creative_library_root=workstation)
            node = next(row for row in index["nodes"] if row["id"] == "work:media:runtime-introduction")
            self.assertEqual(node["title"], "Ordivon Runtime Introduction")
            self.assertNotEqual(node["status"], "historical-recovered")
            self.assertIn("creative-library", node["collections"])
            self.assertEqual(node["catalogProjection"]["sourcePath"], "old/runtime")

    def test_creative_library_catalog_projects_explicit_lineage_relations(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            workstation = Path(directory)
            catalog = workstation / "artifacts/creative-library/catalog-v1.json"
            catalog.parent.mkdir(parents=True)
            catalog.write_text(json.dumps({
                "archiveStanding": "SOURCE_COMPLETE_DECLARED_SCOPE_R1",
                "catalogDigest": "sha256:" + "a" * 64,
                "summary": {"workCount": 2, "carrierCount": 2, "relationCount": 1},
                "works": [
                    {"workId": "media:parent", "title": "Parent", "owner": "Media", "carrierCount": 1},
                    {"workId": "game:child", "title": "Child", "owner": "Game", "carrierCount": 1},
                ],
                "relations": [{
                    "parent_work_id": "media:parent", "child_work_id": "game:child",
                    "relation_type": "DERIVATIVE_OF", "evidence_summary": "Exact lineage evidence."
                }],
            }), encoding="utf-8")
            index = build_creative_index(ROOT, creative_library_root=workstation)
            relation = next(row for row in index["relations"] if row["type"] == "derivativeOf")
            self.assertEqual(relation["from"], "work:game:child")
            self.assertEqual(relation["to"], "work:media:parent")
            self.assertEqual(relation["detail"], "Exact lineage evidence.")

    def test_cad_cross_work_preview_preserves_exact_geometry_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            workstation = Path(directory)
            catalog = workstation / "artifacts/creative-library/catalog-v1.json"
            catalog.parent.mkdir(parents=True)
            catalog.write_text(json.dumps({
                "archiveStanding": "SOURCE_COMPLETE_DECLARED_SCOPE_R1",
                "catalogDigest": "sha256:" + "a" * 64,
                "summary": {"workCount": 2, "carrierCount": 2, "relationCount": 0},
                "works": [
                    {"workId": "workstation:signal-garden-cam-encoder", "title": "Signal Garden Cam Encoder", "owner": "Workstation", "carrierCount": 1},
                    {"workId": "workstation:signal-garden-cam-triptych", "title": "Signal Garden Cam Triptych", "owner": "Workstation", "carrierCount": 1},
                ],
                "relations": [],
            }), encoding="utf-8")
            preview = workstation / "artifacts/creative-library/derived/cad-cross-work-derived-preview-r1.json"
            preview.parent.mkdir(parents=True)
            preview.write_text(json.dumps({
                "schemaVersion": 1,
                "kind": "ordivon.creative-library.derived-preview",
                "row": {
                    "workId": "workstation:signal-garden-cam-encoder",
                    "standing": "DERIVED_CROSS_WORK_EXACT_GEOMETRY_PREVIEW",
                    "sourceRepo": "/tmp/workstation",
                    "sourceRevision": "b" * 40,
                    "sourcePath": "design/daily/signal-garden-cam-encoder/v1/",
                    "sourceCarrier": "source/upstream-v2/model.step",
                    "sourceCarrierSha256": "sha256:" + "c" * 64,
                    "previewSourceWorkId": "workstation:signal-garden-cam-triptych",
                    "previewSourceRevision": "d" * 40,
                    "previewSourcePath": "preview/overview.png",
                    "previewSourceBlobObjectId": "e" * 40,
                    "previewGenerationEvidence": ["generate.py", "reproducibility.json"],
                    "sharedGeometryPath": "cad/model.step",
                    "sharedGeometryByteEqual": True,
                    "derivedPath": "artifacts/creative-library/derived/model.png",
                    "sha256": "sha256:" + "f" * 64,
                    "truthBoundary": "Exact shared STEP geometry; preview is not physical-mechanism evidence.",
                }
            }), encoding="utf-8")
            index = build_creative_index(ROOT, creative_library_root=workstation)
            evidence_id = "evidence:creative-library:cad-cross-work-derived-preview-r1"
            evidence = next(row for row in index["nodes"] if row["id"] == evidence_id)
            projection = evidence["derivedProjection"]
            self.assertTrue(projection["sharedGeometryByteEqual"])
            self.assertEqual(projection["sourceCarrierSha256"], "sha256:" + "c" * 64)
            self.assertEqual(projection["previewSourceWorkId"], "workstation:signal-garden-cam-triptych")
            self.assertEqual(projection["previewGenerationEvidence"], ["generate.py", "reproducibility.json"])
            relations = {(row["from"], row["type"], row["to"]) for row in index["relations"]}
            self.assertIn(("work:workstation:signal-garden-cam-encoder", "evidencedBy", evidence_id), relations)

    def test_creative_library_derived_preview_projects_real_work_and_tool_evidence(self) -> None:
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
            index = build_creative_index(ROOT, creative_library_root=workstation)
            nodes = {row["id"]: row for row in index["nodes"]}
            relations = {(row["from"], row["type"], row["to"]) for row in index["relations"]}
            evidence = "evidence:creative-library:kicad-derived-preview-r1"
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
