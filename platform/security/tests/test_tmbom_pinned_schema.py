"""The pinned upstream OWASP schema must fail closed on tampering without HTTP."""
from __future__ import annotations

import copy
import hashlib
import json
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


    def test_native_metadata_schema_corpus(self):
        # Synthetic structural document only; this is not a threat assessment.
        base = {
            "version": "1.0",
            "scope": {
                "title": "Synthetic document",
                "description": "Metadata only",
                "business_criticality": "low",
                "data_sensitivity": [],
                "exposure": "internal",
                "tier": "non_critical",
            },
            "trust_zones": [], "trust_boundaries": [], "actors": [],
            "components": [], "data_stores": [], "data_sets": [], "data_flows": [],
        }
        fixtures = [("valid", base, True)]
        for name, keys, value, valid in (
            ("version-number", ("version",), 1, False),
            ("version-suffix", ("version",), "1.beta", False),
            ("version-three", ("version",), "1.2.3", True),
            ("title-unicode", ("scope", "title"), "文档 é", True),
            ("description-array", ("scope", "description"), [], False),
            ("description-empty", ("scope", "description"), "", True),
            ("frozen-boolean", ("frozen",), True, True),
            ("frozen-string", ("frozen",), "true", False),
        ):
            model = copy.deepcopy(base)
            parent = model
            for key in keys[:-1]:
                parent = parent[key]
            parent[keys[-1]] = value
            fixtures.append((name, model, valid))
        for key in ("version", "scope"):
            model = copy.deepcopy(base)
            del model[key]
            fixtures.append(("missing-" + key, model, False))

        with tempfile.TemporaryDirectory() as directory:
            tmp = Path(directory)
            for name, model, valid in fixtures:
                with self.subTest(case=name):
                    path = tmp / (name + ".json")
                    path.write_text(json.dumps(model, ensure_ascii=False), encoding="utf-8")
                    result = subprocess.run(
                        ["bash", str(SCRIPT), path.name],
                        cwd=tmp, text=True, capture_output=True, timeout=20,
                    )
                    self.assertEqual(result.returncode, 0 if valid else 1, result.stderr)
                    if not valid:
                        self.assertIn("Schema validation errors", result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
