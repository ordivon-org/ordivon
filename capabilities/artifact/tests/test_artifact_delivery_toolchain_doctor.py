from __future__ import annotations

import importlib.util
from pathlib import Path
import json
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
SPEC = importlib.util.spec_from_file_location(
    "artifact_delivery_toolchain_doctor_test",
    ROOT / "scripts/artifact_delivery_toolchain_doctor.py",
)
assert SPEC is not None and SPEC.loader is not None
DOCTOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(DOCTOR)


class ArtifactDeliveryToolchainDoctorTests(unittest.TestCase):
    def test_openxml_doctor_uses_stable_method_carrier_and_compatible_dotnet8_policy(self) -> None:
        source = (ROOT / "scripts/artifact_delivery_toolchain_doctor.py").read_text()
        lock = json.loads((ROOT / "artifact-delivery/openxml-runtime-v1.lock.json").read_text())
        self.assertEqual(lock["methodId"], "artifact.openxml.conformance.v1")
        self.assertEqual(lock["dotnetPolicy"]["sdkMajorMinor"], "8.0")
        self.assertIn('OPENXML_LOCK["stableDotnet"]', source)
        self.assertIn('OPENXML_LOCK["stableValidator"]', source)
        self.assertNotIn('LOCK["openXml"]["dotnetSdk"]', source)

    def test_missing_executable_becomes_structured_probe_failure(self) -> None:
        missing = ROOT / ".cache" / "doctor-test-definitely-missing" / "tool"
        proc = DOCTOR.run([str(missing), "--version"])
        self.assertEqual(proc.returncode, 127)
        self.assertEqual(proc.stdout, "")
        self.assertIn("executable unavailable", proc.stderr)

    def test_probe_timeout_becomes_structured_probe_failure(self) -> None:
        proc = DOCTOR.run(
            [sys.executable, "-c", "import time; time.sleep(1)"],
            timeout=0.01,
        )
        self.assertEqual(proc.returncode, 124)
        self.assertIn("probe timed out", proc.stderr)


if __name__ == "__main__":
    unittest.main()
