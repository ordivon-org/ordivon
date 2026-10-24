"""Security owner: native OPA verifier and exactly one pinned toolchain authority."""

from __future__ import annotations

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

    def test_retired_provider_snapshot_is_not_an_independent_version_authority(self) -> None:
        """Only the current owner toolchain and live consumer scripts define tool versions."""
        self.assertFalse(
            (ROOT / "providers.lock.json").exists(),
            "unconsumed provider inventory must not become a second tool version authority",
        )
        for path in (ROOT / "mise.toml", *sorted((ROOT / "scripts").glob("*.sh"))):
            with self.subTest(path=path.name):
                self.assertNotIn("providers.lock.json", path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
