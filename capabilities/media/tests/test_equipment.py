from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from ordivon_studio.equipment import (
    EquipmentPlan,
    capability_coverage,
    compile_operation,
    discover_equipment,
    discover_equipment_for_capability,
    load_equipment_world,
    local_provider_surface,
    propose_operation,
    select_for_capability,
    summarize_trial,
    verification_contract,
)

ROOT = Path(__file__).resolve().parents[1]


class EquipmentWorldTests(unittest.TestCase):
    def test_world_is_unique_and_agent_readable(self) -> None:
        world = load_equipment_world(ROOT / "research/equipment/equipment-world.json")
        ids = [item["id"] for item in world["equipment"]]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertIn("ffmpeg", ids)
        self.assertIn("davinci-resolve", ids)
        self.assertIn("reaper", ids)
        self.assertIn("stream-deck", ids)
        self.assertIn("frictionReduction", world["evaluationAxes"])
        by_id = {item["id"]: item for item in world["equipment"]}
        self.assertEqual(by_id["typst"]["retention"], "core-equipment")
        self.assertEqual(by_id["imagemagick"]["retention"], "core-equipment")
        self.assertEqual(by_id["godot"]["retention"], "specialist-on-demand")
        self.assertEqual(by_id["blender"]["retention"], "specialist-on-demand")
        self.assertEqual(by_id["reaper"]["retention"], "specialist-on-demand")
        self.assertIn("audio.project.render", by_id["reaper"]["capabilities"])
        media_world = json.loads((ROOT / "research/expression/media-world-model.json").read_text(encoding="utf-8"))
        self.assertEqual(media_world["equipmentWorld"], "research/equipment/equipment-world.json")
        hypotheses = {item["id"]: item["state"] for item in media_world["foundationHypotheses"]}
        self.assertEqual(hypotheses["spatial-3d"], "provisional")
        self.assertEqual(hypotheses["live-realtime"], "provisional")
        self.assertEqual(media_world["expansionEvidence"], "research/equipment/evidence/e8-capability-expansion-20260814.json")
        self.assertIn("workstation", world["ownership"])
        self.assertIn("long-horizon continuity", world["ownership"]["host"][0])

    def test_capability_selection_prefers_present_retained_equipment(self) -> None:
        world = load_equipment_world(ROOT / "research/equipment/equipment-world.json")
        inventory = {"equipment": [
            {"id": "ffmpeg", "present": True},
            {"id": "ffprobe", "present": True},
        ]}
        matches = select_for_capability(world, "media.probe", inventory=inventory)
        self.assertTrue(matches[0]["selectable"])
        self.assertEqual(matches[0]["readiness"], "READY")
        self.assertEqual(matches[0]["actionability"], "STUDIO_NATIVE")

    def test_physical_presence_does_not_grant_external_authority(self) -> None:
        world = load_equipment_world(ROOT / "research/equipment/equipment-world.json")
        inventory = {"equipment": [
            {"id": "figma", "present": True},
            {"id": "touchdesigner", "present": True},
            {"id": "blender", "present": True},
        ]}
        figma = select_for_capability(world, "design.node.read", inventory=inventory)[0]
        self.assertTrue(figma["present"])
        self.assertEqual(figma["readiness"], "AUTH_REQUIRED")
        self.assertEqual(figma["actionability"], "AUTH_BLOCKED")
        self.assertFalse(figma["selectable"])
        touch = select_for_capability(world, "realtime.visual", inventory=inventory)[0]
        self.assertEqual(touch["readiness"], "LICENSE_REQUIRED")
        self.assertFalse(touch["selectable"])
        blender = select_for_capability(world, "scene.render", inventory=inventory)[0]
        self.assertEqual(blender["readiness"], "READY")
        self.assertEqual(blender["actionability"], "DIRECTLY_INVOCABLE")
        self.assertTrue(blender["selectable"])

    def test_capability_scoped_discovery_does_not_probe_unrelated_equipment(self) -> None:
        world = load_equipment_world(ROOT / "research/equipment/equipment-world.json")
        with mock.patch("ordivon_studio.equipment.discover_equipment", return_value={"equipment": []}) as discover:
            discover_equipment_for_capability(world, "scene.render")
        scoped_world = discover.call_args.args[0]
        self.assertEqual([item["id"] for item in scoped_world["equipment"]], ["blender"])

    def test_capability_coverage_makes_non_actionable_catalog_rows_explicit(self) -> None:
        world = load_equipment_world(ROOT / "research/equipment/equipment-world.json")
        coverage = capability_coverage(world)
        by_pair = {(row["equipmentId"], row["capability"]): row["actionability"] for row in coverage["rows"]}
        self.assertEqual(by_pair[("blender", "scene.render")], "DIRECTLY_INVOCABLE")
        self.assertEqual(by_pair[("obs-studio", "live.state.observe")], "DESCRIPTIVE_ONLY")
        self.assertEqual(by_pair[("figma", "design.node.read")], "AUTH_BLOCKED")
        self.assertEqual(by_pair[("touchdesigner", "realtime.visual")], "LICENSE_BLOCKED")
        self.assertEqual(by_pair[("typst", "document.query")], "DESCRIPTIVE_ONLY")

    def test_blender_proposal_requires_declared_semantic_postcondition(self) -> None:
        world = load_equipment_world(ROOT / "research/equipment/equipment-world.json")
        inventory = {"equipment": [{"id": "blender", "present": True}]}
        with mock.patch("ordivon_studio.equipment.discover_equipment_for_capability", return_value=inventory):
            incomplete = propose_operation(world, "scene.render", {"script": "scene.py"}, equipment_id="blender")
            complete = propose_operation(
                world,
                "scene.render",
                {"script": "scene.py", "expectedArtifacts": ["render.png", "scene.blend"]},
                equipment_id="blender",
            )
        self.assertFalse(incomplete["ready"])
        self.assertIn("VERIFICATION_CONTRACT_INCOMPLETE", incomplete["blockers"])
        self.assertEqual(incomplete["verification"]["kind"], "DECLARED_ARTIFACTS")
        self.assertTrue(complete["ready"])
        self.assertEqual(complete["verification"]["artifacts"], ["render.png", "scene.blend"])

    def test_external_authority_blocker_stops_proposal_before_plan_compilation(self) -> None:
        world = load_equipment_world(ROOT / "research/equipment/equipment-world.json")
        inventory = {"equipment": [{"id": "figma", "present": True}]}
        with mock.patch("ordivon_studio.equipment.discover_equipment_for_capability", return_value=inventory):
            proposal = propose_operation(world, "design.node.read", {}, equipment_id="figma")
        self.assertFalse(proposal["ready"])
        self.assertIsNone(proposal["plan"])
        self.assertIn("AUTH_REQUIRED", proposal["blockers"])
        self.assertIn("AUTH_BLOCKED", proposal["blockers"])
        self.assertEqual(proposal["authorityTransition"]["owner"], "user-plus-figma-auth-provider")
        self.assertFalse(proposal["authorityTransition"]["automatic"])
        self.assertIn("fresh authenticated provider identity", proposal["authorityTransition"]["requiredEvidence"])

    def test_touchdesigner_blocker_names_license_owner_without_bypass(self) -> None:
        world = load_equipment_world(ROOT / "research/equipment/equipment-world.json")
        inventory = {"equipment": [{"id": "touchdesigner", "present": True}]}
        with mock.patch("ordivon_studio.equipment.discover_equipment_for_capability", return_value=inventory):
            proposal = propose_operation(world, "realtime.visual", {}, equipment_id="touchdesigner")
        self.assertFalse(proposal["ready"])
        self.assertEqual(proposal["authorityTransition"]["owner"], "user-plus-derivative-license-authority")
        self.assertIn("license bypass", proposal["authorityTransition"]["prohibited"])

    def test_provider_verification_contracts_remain_owner_specific(self) -> None:
        obs = verification_contract("obs-studio", "live.scene.switch", {})
        resolve = verification_contract("davinci-resolve", "timeline.create", {})
        reaper = verification_contract("reaper", "audio.project.render", {})
        self.assertEqual(obs["kind"], "STATE_REOBSERVE_AND_RECOVER")
        self.assertEqual(resolve["kind"], "OPERATION_RESULT_RECONCILIATION")
        self.assertEqual(reaper["kind"], "RENDER_ARTIFACT")
        self.assertFalse(reaper["ready"])

    def test_compile_operation_is_plan_only(self) -> None:
        if Path("/usr/bin/ffmpeg").is_file():
            plan = compile_operation(
                "ffmpeg",
                "image.resize",
                {"input": "in.png", "output": "out.png", "width": 10, "height": 20},
            )
            self.assertIsInstance(plan, EquipmentPlan)
            self.assertEqual(plan.transport, "process")
            self.assertIn("scale=10:20", plan.args)

    def test_windows_native_reaper_plan_translates_wsl_mounted_project_path(self) -> None:
        with mock.patch("ordivon_studio.equipment._first_existing", return_value="/mnt/c/reaper.exe"):
            plan = compile_operation(
                "reaper",
                "audio.project.render",
                {"project": "/mnt/c/Users/test/project.rpp"},
            )
        self.assertEqual(plan.args[-1], "C:\\Users\\test\\project.rpp")

    def test_external_equipment_plans_preserve_authority_boundaries(self) -> None:
        obs = compile_operation("obs-studio", "live.scene.switch", {})
        self.assertEqual(obs.transport, "provider-descriptor-only")
        self.assertTrue(any("disabled by default" in note for note in obs.notes))
        observe = compile_operation("obs-studio", "live.state.observe", {})
        self.assertEqual(observe.transport, "provider-descriptor-only")
        self.assertIsNone(observe.executable)
        figma = compile_operation("figma", "design.variables", {})
        self.assertEqual(figma.transport, "figma-mcp-or-plugin")
        self.assertTrue(any("OAuth" in note for note in figma.notes))

    def test_friction_reduction_can_retain_without_unique_capability(self) -> None:
        report = summarize_trial(
            equipment_id="imagemagick",
            fallback_id="ffmpeg",
            capability_delta=[],
            friction_delta={"commandsReduced": 1, "medianWallTimeRatio": 0.9},
            ceiling_delta=[],
            costs={"highPersistentCost": False},
            evidence_level="executed",
        )
        self.assertEqual(report["decision"], "retain")

    def test_high_cost_unique_tool_becomes_specialist(self) -> None:
        report = summarize_trial(
            equipment_id="blender",
            fallback_id="python-projection",
            capability_delta=["editable-3d-scene"],
            friction_delta={},
            ceiling_delta=["production-3d-render"],
            costs={"highPersistentCost": True},
            evidence_level="executed",
        )
        self.assertEqual(report["decision"], "specialist-on-demand")

    def test_physical_missing_stays_challenger(self) -> None:
        report = summarize_trial(
            equipment_id="stream-deck",
            fallback_id=None,
            capability_delta=["physical-low-latency-control"],
            friction_delta={},
            ceiling_delta=[],
            costs={},
            evidence_level="physical-missing",
        )
        self.assertEqual(report["decision"], "challenger")


    def test_local_provider_surface_hides_protocol_folklore_but_preserves_owner_boundaries(self) -> None:
        world = load_equipment_world(ROOT / "research/equipment/equipment-world.json")
        surface = local_provider_surface(world)
        self.assertFalse(surface["mcpRequired"])
        self.assertTrue(surface["runtimeOwnsPhysicalExecution"])
        by_id = {item["equipmentId"]: item for item in surface["providers"]}
        self.assertEqual(set(by_id), {"davinci-resolve", "obs-studio", "reaper"})
        self.assertEqual(by_id["obs-studio"]["defaultLifecycle"], "websocket-server-disabled-by-default")
        self.assertIn("re-observe", by_id["obs-studio"]["convergence"])
        self.assertIn("native-rpp", by_id["reaper"]["stateAuthority"])
        self.assertEqual(by_id["davinci-resolve"]["transport"], "studio.resolve-adapter")
        self.assertNotIn("password", json.dumps(surface).lower())

    def test_workstation_binding_is_physical_discovery_not_semantic_authority(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            executable = root / "inkscape"
            executable.write_text("#!/bin/sh\necho Inkscape 1.4\n", encoding="utf-8")
            executable.chmod(0o755)
            binding_tool = root / "equipment-binding"
            binding_tool.write_text(
                "#!/usr/bin/env python3\nimport json\nprint(json.dumps({\"schemaVersion\":1,\"kind\":\"ordivon.workstation-equipment-binding\",\"state\":\"AVAILABLE\",\"executionTarget\":\"local_linux\",\"provider\":\"workstation.isolated-equipment\",\"bindingDigest\":\"sha256:" + "a"*64 + "\",\"executable\":\"" + str(executable) + "\",\"environment\":{\"libraryDirs\":[],\"pythonSitePackages\":[]},\"providerIdentity\":{\"ownerTask\":\"task:test\"},\"validUntilMs\":9999999999999}))\n",
                encoding="utf-8",
            )
            binding_tool.chmod(0o755)
            world = {
                "equipment": [{
                    "id": "inkscape", "family": "vector", "capabilities": ["vector.export"],
                    "retention": "specialist-on-demand", "reason": "test",
                    "discovery": [{"kind": "workstation-isolated-binding", "platform": "linux", "equipmentId": "game-inkscape-e1", "executable": "inkscape", "versionArgs": ["--version"]}],
                }]
            }
            with mock.patch.dict(os.environ, {"ORDIVON_EQUIPMENT_BINDING": str(binding_tool)}):
                inventory = discover_equipment(world)
                plan = compile_operation("inkscape", "vector.export", {"input": "in.svg", "output": "out.png"})
            row = inventory["equipment"][0]
            self.assertTrue(row["present"])
            self.assertEqual(row["candidates"][0]["provider"], "workstation.isolated-equipment")
            self.assertTrue(row["candidates"][0]["bindingDigest"].startswith("sha256:"))
            self.assertEqual(plan.executable, str(executable))
            self.assertIn("EquipmentBinding", " ".join(plan.notes))
            self.assertNotIn("capability", row["candidates"][0])

    def test_discovery_redacts_secret_like_keys(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            executable = root / "tool"
            executable.write_text("#!/bin/sh\necho tool 1.0\n", encoding="utf-8")
            executable.chmod(0o755)
            config = root / "config.json"
            config.write_text(json.dumps({"port": 1234, "server_password": "secret-value"}), encoding="utf-8")
            world = {
                "equipment": [{
                    "id": "x",
                    "family": "test",
                    "capabilities": [],
                    "retention": "candidate",
                    "reason": "test",
                    "discovery": [{"platform": "linux", "path": str(executable), "versionArgs": ["--version"]}],
                    "configuration": [{"kind": "glob", "pattern": str(config), "redact": ["server_password"]}],
                }]
            }
            inventory = discover_equipment(world)
            projection = inventory["equipment"][0]["configuration"][0]["safeProjection"]
            self.assertEqual(projection["port"], 1234)
            self.assertEqual(projection["server_password"], "<redacted-present>")
            self.assertNotIn("secret-value", json.dumps(inventory))


if __name__ == "__main__":
    unittest.main()
