import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).parents[1]
SPEC = importlib.util.spec_from_file_location("artifact_registry_doctor", ROOT / "scripts/artifact_registry_doctor.py")
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(MODULE)


class ArtifactRegistryDoctorTests(unittest.TestCase):
    def test_source_deployment_boundary_is_loopback_pinned_and_persistent(self) -> None:
        checks = MODULE.static_configuration_checks()
        self.assertTrue(checks)
        self.assertEqual({item["status"] for item in checks}, {"PASS"}, checks)
        self.assertEqual({item["name"] for item in checks}, {"source-zot-config-boundary", "source-quadlet-boundary"})


if __name__ == "__main__":
    unittest.main()
