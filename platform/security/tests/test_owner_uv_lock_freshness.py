"""Owner-native regression for editable manifest / frozen lock divergence."""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import tempfile
import tomllib
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class OwnerUvLockFreshness(unittest.TestCase):
    def test_verify_uses_one_freshness_aware_sync(self) -> None:
        data = tomllib.loads((ROOT / "mise.toml").read_text(encoding="utf-8"))
        script = data["tasks"]["verify"]["run"]
        sync = "uv sync --locked --python 3.15.1"
        self.assertIn(sync, script)
        self.assertNotIn("uv lock --check", script)
        self.assertNotIn("uv sync --frozen", script)
        self.assertLess(script.index(sync), script.index("ruff check"))

    def test_s03_plan_binds_real_lock_consumer_without_formal_or_installed_promotion(self) -> None:
        plan = json.loads(
            (ROOT / "planning" / "lego-plan-r1.json").read_text(encoding="utf-8")
        )
        s03 = next(n for n in plan["nodes"] if n["id"] == "S03")
        task = tomllib.loads((ROOT / "mise.toml").read_text(encoding="utf-8"))[
            "tasks"
        ]["verify"]["run"]
        bindings = s03["consumerBindings"]
        assert any(
            b["path"] == "mise.toml"
            and b["symbol"] == "tasks.verify.run"
            and b["operation"].split(" before ")[0] in task
            and b["standing"] == "SOURCE_DECLARED_NATIVE_TASK_NOT_INSTALLED"
            for b in bindings
        )
        assert any(
            b["path"] == "tests/test_owner_uv_lock_freshness.py"
            and b["symbol"] == "OwnerUvLockFreshness"
            and b["standing"] == "SOURCE_EXECUTABLE_TEST_CONSUMER"
            for b in bindings
        )
        self.assertIn("uv sync --locked --python 3.15.1", s03["behavioralContract"])
        self.assertIn("uv.lock", s03["inputs"][0])
        self.assertTrue(s03["formalObligations"])
        self.assertTrue(all(x.startswith("OPEN:") for x in s03["formalObligations"]))
        self.assertIn("no installed or policy admission authority", s03["outputs"][0])

    def test_frozen_sync_alone_accepts_stale_lock(self) -> None:
        original = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
        # Remove owner dev requirements and generate a legitimate small lock.
        without_dev, changed = re.subn(
            r'(?m)^dev = \[\n(?:  "[^"]+",?\n)+\]',
            "dev = []",
            original,
            count=1,
        )
        self.assertEqual(changed, 1)
        with tempfile.TemporaryDirectory(prefix="ordivon-lock-drift-") as directory:
            temp = Path(directory)
            (temp / "pyproject.toml").write_text(without_dev, encoding="utf-8")
            shutil.copy2(ROOT / "uv.lock", temp / "uv.lock")
            # CI has a different package cache and VIRTUAL_ENV; neither must
            # decide the oracle for a project manifest / lock inconsistency.
            env = {k: v for k, v in os.environ.items() if k != "VIRTUAL_ENV"}
            env["UV_CACHE_DIR"] = str(temp / "isolated-cache")

            def uv(*args: str) -> subprocess.CompletedProcess[str]:
                return subprocess.run(
                    ["uv", *args], cwd=temp, env=env, text=True,
                    capture_output=True, timeout=40, check=False,
                )

            base = uv("lock", "--offline", "--python", "3.15.1")
            self.assertEqual(base.returncode, 0, base.stderr)
            fresh = uv(
                "sync", "--locked", "--offline", "--python", "3.15.1",
                "--no-dev", "--no-install-project",
            )
            self.assertEqual(fresh.returncode, 0, fresh.stderr)
            # Change only the local project identity: no registry packages
            # need to be downloaded to prove lock drift.
            stale = without_dev.replace('version = "0.1.0"', 'version = "0.1.1"', 1)
            self.assertNotEqual(stale, without_dev)
            (temp / "pyproject.toml").write_text(stale, encoding="utf-8")
            frozen = uv(
                "sync", "--frozen", "--offline", "--python", "3.15.1",
                "--no-dev", "--no-install-project",
            )
            self.assertEqual(frozen.returncode, 0, frozen.stderr)
            strict = uv(
                "sync", "--locked", "--offline", "--python", "3.15.1",
                "--no-dev", "--no-install-project",
            )
            self.assertNotEqual(strict.returncode, 0, strict.stderr)
            self.assertIn("lockfile", strict.stderr.lower())


if __name__ == "__main__":
    unittest.main()
