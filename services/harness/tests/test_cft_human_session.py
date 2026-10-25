from __future__ import annotations

import pytest

import json
from pathlib import Path
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/cft_human_session.py"


@pytest.mark.parametrize("dirname", ["sessions?root", "sessions#root", "sessions%23root"])
def test_session_read_only_connection_uses_exact_ledger_dir(tmp_path: Path, dirname: str) -> None:
    from contextlib import closing

    sys.path.insert(0, str(ROOT / "scripts"))
    from cft_human_session import DurableSessionAuthority

    owner = DurableSessionAuthority(root=tmp_path / dirname, slots=(41,))
    with closing(owner._connect(read_only=True)) as db:
        assert db.execute("SELECT COUNT(*) FROM sessions").fetchone()[0] == 0


class CftHumanSessionDoctorTests(unittest.TestCase):
    @pytest.mark.node_qualification
    def test_doctor_projects_standard_session_dependencies_without_mutation(self):
        proc = subprocess.run(
            [sys.executable, str(SCRIPT), "doctor"],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        value = json.loads(proc.stdout)
        self.assertTrue(value["healthy"])
        self.assertEqual(value["standing"], "READY")
        self.assertEqual(value["sessionOwner"], "systemd")
        self.assertEqual(value["cdpAuthority"], "loopback")
        self.assertEqual(value["humanSurface"], "xvfb-x11vnc-novnc")
        self.assertEqual(
            value["browserEquipment"]["equipmentId"], "browser:playwright-chromium"
        )
        self.assertEqual(value["browserEquipment"]["executionTarget"], "local_linux")
        self.assertTrue(value["browserEquipment"]["executableDigest"].startswith("sha256:"))
        self.assertTrue(value["browserEquipment"]["bindingDigest"].startswith("sha256:"))
        self.assertEqual(value["sideEffectsAttempted"], False)
        self.assertNotIn("token", json.dumps(value).lower())
        self.assertNotIn("cookie", json.dumps(value).lower())


if __name__ == "__main__":
    unittest.main()
