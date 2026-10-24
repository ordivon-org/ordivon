"""Owner-native TEST-RUNTIME-PYTHON-OWNER-PIN-001: cold Python selection uses one mise pin."""

import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

SOURCE = Path(__file__).resolve().parents[1] / "owner-environment"


class OwnerPythonPinContract(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="runtime-pin-cdc-")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        (self.root / "scripts").mkdir()
        shutil.copyfile(SOURCE, self.root / "scripts/owner-environment")
        self.script = self.root / "scripts/owner-environment"
        (self.root / "Cargo.lock").write_text("# offline test dummy\n", encoding="utf-8")
        (self.root / "requirements-tooling.lock.txt").write_text("", encoding="utf-8")
        self.bin = self.root / "fake-bin"
        self.bin.mkdir()
        self._exe("uv", """#!/usr/bin/env python3
import json
import os
import sys
from pathlib import Path
args = sys.argv[1:]
with open(os.environ["UV_RECORD"], "a", encoding="utf-8") as log:
    log.write(json.dumps(args) + "\\n")
if args and args[0] == "venv":
    python = Path(args[-1]) / "bin/python"
    python.parent.mkdir(parents=True, exist_ok=True)
    python.symlink_to(sys.executable)
""")
        self._exe("cargo", '#!/bin/sh\nif [ "$1" = "--version" ]; then echo "cargo 1.99.1"; fi\n')
        self._exe("rustc", '#!/bin/sh\necho "rustc 1.99.1"\n')
        self.record = self.root / "uv-record.jsonl"

    def _exe(self, name, body):
        target = self.bin / name
        target.write_text(body, encoding="utf-8")
        target.chmod(0o755)

    def run_owner(self, version, action="bootstrap", override=None):
        (self.root / "mise.toml").write_text(
            '[tools]\npython = "' + version + '"\n', encoding="utf-8"
        )
        env = os.environ.copy()
        env.update({
            "UV_BIN": str(self.bin / "uv"),
            "CARGO_BIN": str(self.bin / "cargo"),
            "RUSTC_BIN": str(self.bin / "rustc"),
            "UV_RECORD": str(self.record),
        })
        env.pop("ORDIVON_OWNER_ENV_DIR", None)
        env.pop("ORDIVON_OWNER_PYTHON", None)
        if override is not None:
            env["ORDIVON_OWNER_PYTHON"] = override
        return subprocess.run(
            ["bash", str(self.script), action],
            cwd=self.root,
            env=env,
            text=True,
            capture_output=True,
            timeout=15,
            check=False,
        )

    def read_uv(self):
        return [json.loads(line) for line in self.record.read_text(encoding="utf-8").splitlines()]

    def test_default_bootstrap_consumes_owner_mise_patch_pin(self):
        result = self.run_owner("3.15.1")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.read_uv()[0][:3], ["venv", "--python", "3.15.1"])
        self.assertTrue((self.root / ".venv-py3.15.1/bin/python").exists())

    def test_explicit_owner_python_override_is_preserved(self):
        result = self.run_owner("3.15.1", override="3.14.9")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.read_uv()[0][:3], ["venv", "--python", "3.14.9"])
        self.assertTrue((self.root / ".venv-py3.14.9/bin/python").exists())

    def test_unpinned_owner_mise_version_fails_closed(self):
        result = self.run_owner("3.15")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("must pin an exact Python patch release", result.stderr)
        self.assertFalse(self.record.exists())

    def test_doctor_rejects_actual_interpreter_mismatch(self):
        prepare = self.run_owner("9.99.99")
        self.assertEqual(prepare.returncode, 0, prepare.stderr)
        result = self.run_owner("9.99.99", action="doctor")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("expects Python 9.99.99", result.stderr)

    def test_doctor_fails_closed_when_ruff_hash_lock_is_missing(self):
        prepare = self.run_owner("3.15.1")
        self.assertEqual(prepare.returncode, 0, prepare.stderr)
        result = self.run_owner("3.15.1", action="doctor")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Ruff hash lock must pin exactly one version", result.stderr)


if __name__ == "__main__":
    unittest.main()
