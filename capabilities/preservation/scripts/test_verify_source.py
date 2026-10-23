#!/usr/bin/env python3
"""Preservation source-boundary contract, including optimized Python execution."""
from __future__ import annotations

import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).with_name("verify_source.py")
BOUNDARY = SCRIPT.parents[1] / "SOURCE_BOUNDARY.json"

# Run the real verifier entry point, with only its JSON input substituted.
# In particular Python -O must not disable the owner boundary guarantee.
RUN_VERIFIER = """
import importlib.util
import sys
from pathlib import Path
spec = importlib.util.spec_from_file_location("preservation_source", sys.argv[1])
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
module.BOUNDARY = Path(sys.argv[2])
raise SystemExit(module.main())
"""


class SourceBoundaryContractTests(unittest.TestCase):
    def verify(self, data: dict, *, optimized: bool) -> subprocess.CompletedProcess[str]:
        with tempfile.TemporaryDirectory() as directory:
            boundary = Path(directory) / "SOURCE_BOUNDARY.json"
            boundary.write_text(json.dumps(data), encoding="utf-8")
            return subprocess.run(
                [
                    sys.executable,
                    *(["-O"] if optimized else []),
                    "-c",
                    RUN_VERIFIER,
                    str(SCRIPT),
                    str(boundary),
                ],
                capture_output=True,
                text=True,
                check=False,
                timeout=30,
            )

    def test_accepted_source_manifest_in_normal_and_optimized_python(self) -> None:
        valid = json.loads(BOUNDARY.read_text(encoding="utf-8"))
        for optimized in (False, True):
            with self.subTest(optimized=optimized):
                result = self.verify(valid, optimized=optimized)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_patterns_do_not_match_across_directory_boundaries(self) -> None:
        import importlib.util

        spec = importlib.util.spec_from_file_location("preservation_source", SCRIPT)
        assert spec is not None and spec.loader is not None
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        self.assertTrue(
            module._matches(
                "docs/creative-preservation-pilot.md",
                "docs/creative-preservation-*.md",
            )
        )
        self.assertFalse(
            module._matches(
                "docs/creative-preservation-nested/inside.md",
                "docs/creative-preservation-*.md",
            ),
            "a single-segment glob must never match a nested unregistered path",
        )
        self.assertTrue(
            module._matches(
                "artifacts/creative-preservation/subdir/a.bin",
                "artifacts/creative-preservation/**",
            )
        )

    def test_rejects_invalid_authority_and_identity_in_optimized_python(self) -> None:
        valid = json.loads(BOUNDARY.read_text(encoding="utf-8"))
        cases = (
            ("kind", "ordivon.untrusted-preservation"),
            ("runtime-owned", True),
            ("not-local", False),
        )
        for name, wrong_value in cases:
            with self.subTest(name=name):
                altered = copy.deepcopy(valid)
                if name == "kind":
                    altered["kind"] = wrong_value
                elif name == "runtime-owned":
                    altered["authorityBoundary"]["runtimeFrameworkOwnedByOrdivon"] = wrong_value
                else:
                    altered["authorityBoundary"]["localProfileOnly"] = wrong_value
                result = self.verify(altered, optimized=True)
                self.assertNotEqual(
                    result.returncode, 0,
                    f"optimized Python bypassed source-boundary contract: {name}: "
                    f"{result.stdout}{result.stderr}",
                )


if __name__ == "__main__":
    unittest.main()
