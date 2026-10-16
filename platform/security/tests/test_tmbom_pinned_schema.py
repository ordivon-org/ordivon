"""The pinned upstream OWASP schema must fail closed on tampering without HTTP."""
from __future__ import annotations

import hashlib
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
UPSTREAM_SCHEMA = ROOT / "schemas/owasp-threat-model-v1.0.2.schema.json"
SCRIPT = ROOT / "scripts/validate_tmbom.sh"
EXPECTED_SHA256 = "428772fecfed799921e90bb7e7acf7ce7bb8e379128e43c4e7f4346a528539be"


class TMBOmSchemaTests(unittest.TestCase):
    def test_pinned_upstream_schema_bytes_are_exact(self):
        self.assertEqual(hashlib.sha256(UPSTREAM_SCHEMA.read_bytes()).hexdigest(), EXPECTED_SHA256)

    def test_schema_tampering_fails_before_any_validator_runs(self):
        with tempfile.TemporaryDirectory() as d:
            tmp = Path(d)
            (tmp / "scripts").mkdir()
            (tmp / "schemas").mkdir()
            shutil.copy2(SCRIPT, tmp / "scripts/validate_tmbom.sh")
            (tmp / "schemas/owasp-threat-model-v1.0.2.schema.json").write_bytes(
                UPSTREAM_SCHEMA.read_bytes() + b"\n"
            )
            result = subprocess.run(
                ["bash", str(tmp / "scripts/validate_tmbom.sh"), "dummy.json"],
                text=True, capture_output=True, cwd=tmp, check=False, timeout=10,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("schema digest mismatch", result.stderr)


if __name__ == "__main__":
    unittest.main()
