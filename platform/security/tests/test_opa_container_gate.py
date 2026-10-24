"""Security owner: native OPA verifier and exactly one pinned toolchain authority."""

from __future__ import annotations

import json
import tomllib
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class OpaVerificationOwnerContract(unittest.TestCase):
    def test_owner_pins_one_native_policy_verifier_without_container(self) -> None:
        source = tomllib.loads((ROOT / "mise.toml").read_text(encoding="utf-8"))
        self.assertTrue(source["tools"]["opa"])
        verify = source["tasks"]["verify"]["run"]
        self.assertEqual(verify.count("mise exec -- opa test -v --fail-on-empty policies"), 1)
        self.assertIn("MISE_OFFLINE=1", verify)
        self.assertIn("MISE_AUTO_INSTALL=false", verify)
        self.assertNotIn("docker run", verify)
        self.assertNotIn("ciContainer", verify)
        self.assertNotIn("uv sync --frozen", verify)

    def test_removed_container_provider_is_not_second_opa_version_authority(self) -> None:
        lock = json.loads((ROOT / "providers.lock.json").read_text(encoding="utf-8"))
        providers = lock["providers"]
        self.assertEqual(len(providers), len({p["name"] for p in providers}))
        self.assertNotIn("opa", {p["name"] for p in providers})
        for row in providers:
            self.assertNotIn("ciContainer", row)


if __name__ == "__main__":
    unittest.main()
