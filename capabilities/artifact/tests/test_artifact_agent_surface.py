import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("artifact_agent_surface", ROOT / "scripts/artifact_agent_surface.py")
M = importlib.util.module_from_spec(SPEC); assert SPEC and SPEC.loader; SPEC.loader.exec_module(M)


class ArtifactAgentSurfaceTests(unittest.TestCase):
    def test_surface_is_thin_and_runtime_owned(self):
        surface = M.surface_projection()
        self.assertEqual(surface["domainId"], "domain:ordivon-artifact")
        self.assertTrue(surface["runtimeOwnsPhysicalExecution"])
        self.assertFalse(surface["mcpRequired"])
        names = {x["name"] for x in surface["tools"]}
        self.assertEqual(names, {"artifact_family_status", "artifact_profile_coverage", "artifact_verify_propose", "artifact_build_propose", "artifact_toolchain_doctor_propose", "artifact_cad_admission_status"})

    def test_electronic_design_profile_is_family_visible_and_service_routed(self):
        status = M.family_status("electronic-design")
        row = status["families"][0]
        self.assertIn("eda-kicad-pcb-gerber-r1", row["currentProfiles"])
        self.assertIn("eda-kicad-pcb-gerber-r1", row["serviceRoutedProfiles"])

    def test_coverage_matrix_is_complete_and_conservative(self):
        matrix = M.profile_coverage()
        taxonomy = json.loads((ROOT / "artifact-delivery/taxonomy-v1.json").read_text())
        expected_count = sum(len(row.get("currentProfiles", [])) for row in taxonomy["families"])
        self.assertEqual(matrix["profileCount"], expected_count)
        self.assertEqual(set(matrix["gateIds"]), set(M.COVERAGE_GATE_IDS))
        self.assertTrue(all(set(row["gates"]) == set(M.COVERAGE_GATE_IDS) for row in matrix["profiles"]))
        self.assertIn("not-occurrence-verdict", matrix["truthRole"])

    def test_presentation_coverage_requires_target_and_delivery_without_claiming_roundtrip(self):
        row = M.profile_coverage(profile_id="pdu-sdu-presentation-r1")["profiles"][0]
        self.assertEqual(row["gates"]["nativeConsumerOpen"]["status"], "EXPLICIT_REQUIRED")
        self.assertEqual(row["gates"]["nativeRender"]["status"], "EXPLICIT_REQUIRED")
        self.assertEqual(row["gates"]["deliveryReadback"]["status"], "EXPLICIT_REQUIRED")
        self.assertEqual(row["gates"]["roundTripEdit"]["status"], "EDITABLE_OUTPUT_DECLARED_BUT_ROUNDTRIP_GATE_UNMODELED")

    def test_eda_coverage_exposes_live_profile_without_inventing_delivery_or_roundtrip(self):
        row = M.profile_coverage(profile_id="eda-kicad-pcb-gerber-r1")["profiles"][0]
        self.assertEqual(row["capabilityStanding"], "LOCAL_LIVE_PROVEN")
        self.assertEqual(row["gates"]["nativeConsumerOpen"]["status"], "EXPLICIT_REQUIRED")
        self.assertEqual(row["gates"]["deliveryReadback"]["status"], "NOT_EXPLICITLY_MODELED")
        self.assertEqual(row["gates"]["roundTripEdit"]["status"], "EDITABLE_OUTPUT_DECLARED_BUT_ROUNDTRIP_GATE_UNMODELED")

    def test_verify_proposal_compiles_existing_service_not_family_logic(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "request.json"
            p.write_text(json.dumps({"profile": {"id": "eda-kicad-pcb-gerber-r1"}}))
            result = M.verify_proposal(str(p))
            if not M.ARTIFACT_PYTHON.is_file(): self.skipTest("managed Artifact Python unavailable")
            self.assertTrue(result["ready"], result)
            self.assertEqual(result["plan"]["executable"], str(M.ARTIFACT_PYTHON))
            self.assertEqual(result["plan"]["args"][0], "scripts/artifact_verify.py")

    def test_cad_boundary_does_not_promote_glb(self):
        status = M.cad_boundary_status()
        self.assertFalse(status["graduated"])
        self.assertTrue(status["boundedCadProfileAdmission"])
        self.assertEqual(status["currentCadProfiles"], ["design-3d-step-solid-r1"])
        self.assertTrue(any("glb" in x for x in status["currentDesign3dProfiles"]))
        self.assertTrue(status["observedToolPresence"]["freecad"])
        self.assertTrue(status["observedToolPresence"]["occtStepInspector"])
        self.assertIn("bounded metric single-solid STEP/BREP profile", status["boundary"])


    def test_service_profile_discovery_does_not_parse_verifier_python_source(self):
        source = (ROOT / "scripts/artifact_agent_surface.py").read_text(encoding="utf-8")
        self.assertNotIn("ast.parse", source)
        self.assertNotIn("ROUTES", source)
        self.assertIn("still-image-png-srgb-r1", M._service_profiles())


    def test_runtime_surface_does_not_depend_on_generated_migration_manifests(self):
        source = (ROOT / "scripts/artifact_agent_surface.py").read_text(encoding="utf-8")
        self.assertNotIn("profile-v2-mapping-manifest-r1.json", source)
        self.assertNotIn("donor-r1/manifest.json", source)


if __name__ == "__main__": unittest.main()
