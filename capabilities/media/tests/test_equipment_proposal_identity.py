"""The selected provider is consumed once, not discovered again by compilation."""
from __future__ import annotations

import hashlib
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from ordivon_studio.equipment import propose_operation


def digest(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


class EquipmentProposalIdentityTests(unittest.TestCase):
    def test_real_alternating_binding_and_observation_drift(self):
        for drift in (False, True):
            with self.subTest(drift=drift), tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                count = root / "count"
                rows = []
                for i in (1, 2):
                    path = root / f"tool{i}"
                    script = f"#!/bin/sh\necho version-{i}\n"
                    if drift and i == 1:
                        # During actual version probing, mutate this disposable fixture.
                        script += 'printf "\\n# changed\\n" >> "$0"\n'
                    path.write_text(script)
                    path.chmod(0o700)
                    rows.append({
                        "schemaVersion": 1, "kind": "ordivon.workstation-equipment-binding",
                        "equipmentId": "game-aseprite-e1", "state": "AVAILABLE",
                        "executionTarget": "local_linux", "provider": "fixture",
                        "providerIdentity": {}, "environment": {},
                        "bindingDigest": "sha256:" + str(i) * 64,
                        "executableDigest": digest(path), "executable": str(path),
                        "validUntilMs": None,
                    })
                binding = root / "binding"
                binding.write_text(
                    "#!/usr/bin/env python3\nfrom pathlib import Path\nimport json\n"
                    f"p=Path({str(count)!r})\ni=int(p.read_text()) if p.exists() else 0\n"
                    f"p.write_text(str(i+1))\nprint(json.dumps({rows!r}[min(i,1)]))\n"
                )
                binding.chmod(0o700)
                world = {"equipment": [{
                    "id": "aseprite", "family": "sprite", "capabilities": ["sprite.runtime.export"],
                    "discovery": [{"kind": "workstation-managed-binding",
                                   "equipmentId": "game-aseprite-e1", "platform": "linux"}],
                }]}
                with patch.dict(os.environ, {"ORDIVON_EQUIPMENT_BINDING": str(binding)}):
                    result = propose_operation(
                        world, "sprite.runtime.export", {"source": "a.aseprite", "output": "a.png"}
                    )
                self.assertEqual(count.read_text(), "1")
                if drift:
                    self.assertFalse(result["ready"])
                    self.assertIsNone(result["plan"])
                    self.assertIn("SELECTED_EQUIPMENT_BINDING_CHANGED", result["blockers"])
                else:
                    self.assertTrue(result["ready"])
                    self.assertEqual(result["plan"]["executable"], rows[0]["executable"])
                    self.assertEqual(result["plan"]["selectedBinding"], {
                        "equipmentId": rows[0]["equipmentId"],
                        "bindingDigest": rows[0]["bindingDigest"],
                        "executableDigest": rows[0]["executableDigest"],
                        "standing": "observed-at-proposal",
                    })
                    self.assertNotEqual(result["plan"]["executable"], rows[1]["executable"])
