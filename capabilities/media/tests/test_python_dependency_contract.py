"""Native installed-version verification remains tied to the selected lock."""
from __future__ import annotations

import importlib.util
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "python_dependency_contract", ROOT / "scripts/python_dependency_contract.py"
)
contract = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(contract)


class PythonDependencyContractTests(unittest.TestCase):
    def test_actual_versions_match_frozen_lock_even_under_optimization(self):
        result = subprocess.run(
            [sys.executable, "-O", "-c", contract.environment_probe()],
            capture_output=True, text=True, timeout=30,
        )
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_wrong_and_ambiguous_locked_versions_fail_closed(self):
        original = contract.locked_runtime_versions()
        with tempfile.TemporaryDirectory() as folder:
            lock = Path(folder) / "uv.lock"
            raw = (ROOT / "uv.lock").read_text()
            old = f'name = "jsonschema"\nversion = "{original["jsonschema"]}"'
            replacement = 'name = "jsonschema"\nversion = "999.0.0"'
            self.assertIn(old, raw)
            lock.write_text(raw.replace(old, replacement, 1))
            with patch.object(contract, "ROOT", Path(folder)):
                self.assertEqual(contract.locked_runtime_versions()["jsonschema"], "999.0.0")
                result = subprocess.run(
                    [sys.executable, "-O", "-c", contract.environment_probe()],
                    capture_output=True, text=True, timeout=30,
                )
                self.assertEqual(result.returncode, 2, result.stderr)
                with lock.open("a") as stream:
                    stream.write(f"\n[[package]]\n{old}\n")
                with self.assertRaises(ValueError):
                    contract.locked_runtime_versions()
