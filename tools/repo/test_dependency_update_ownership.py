#!/usr/bin/env python3
"""Keep dependency-update authority and cross-directory grouping unambiguous."""
from __future__ import annotations

import json
import tomllib
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]


class DependencyUpdateOwnershipTests(unittest.TestCase):
    def test_unconsumed_opa_toolchain_pins_are_retired(self):
        """Capital uses native Python; Artifact binds an external release OPA carrier."""
        for owner in ("domains/capital", "capabilities/artifact"):
            manifest = tomllib.loads((ROOT / owner / "mise.toml").read_text(encoding="utf-8"))
            self.assertNotIn("opa", manifest["tools"], f"{owner} must not install unused OPA")
        # Do not confuse an unconsumed Mise version pin with Artifact's actual
        # OCI release policy: the production carrier is an explicit external
        # executable whose path and SHA-256 enter the release evidence.
        carrier = (ROOT / "capabilities/artifact/scripts/artifact_oci_package.py").read_text(encoding="utf-8")
        self.assertIn('os.environ.get("ARTIFACT_OPA"', carrier)
        self.assertIn('sha256_file(DEFAULT_OPA)', carrier)
        for owner in ("platform/security", "capabilities/distribution"):
            manifest = tomllib.loads((ROOT / owner / "mise.toml").read_text(encoding="utf-8"))
            self.assertIn("opa", manifest["tools"])

    def test_active_opa_policy_owners_consume_one_current_version(self):
        """Current OPA policy consumers converge; no stale Mise OPA release."""
        owners = ("platform/security", "capabilities/distribution", "meta/next")
        versions = {
            owner: tomllib.loads((ROOT / owner / "mise.toml").read_text(encoding="utf-8"))
            ["tools"]["opa"]
            for owner in owners
        }
        self.assertEqual(len(set(versions.values())), 1, versions)
        self.assertTrue((ROOT / "meta/next/tests/test_research_adopted_policy.py").is_file())

    def test_python_uv_lock_has_one_updater(self):
        renovate = json.loads((ROOT / "renovate.json").read_text(encoding="utf-8"))
        # Python uv and Mise tool versions have distinct canonical file owners.
        # Dependabot continues to own npm/Cargo/Nix, so enabling those Renovate
        # managers would create competing dependency update authorities.
        self.assertEqual(set(renovate["enabledManagers"]), {"pep621", "mise"})
        self.assertTrue(renovate["lockFileMaintenance"]["enabled"])
        self.assertEqual(
            renovate["packageRules"],
            [
                {"matchManagers": ["pep621"], "groupName": "Python {{depName}}"},
                {"matchManagers": ["mise"], "groupName": "Mise {{depName}}"},
            ],
        )
        config = yaml.safe_load((ROOT / ".github/dependabot.yml").read_text(encoding="utf-8"))
        ecosystems = [item["package-ecosystem"] for item in config["updates"]]
        self.assertNotIn("uv", ecosystems)

    def test_mise_toolchain_updates_have_one_nonduplicated_owner(self):
        """Mise pins are real consumers, not covered by Python-only Renovate."""
        renovate = json.loads((ROOT / "renovate.json").read_text(encoding="utf-8"))
        config = yaml.safe_load((ROOT / ".github/dependabot.yml").read_text(encoding="utf-8"))
        self.assertTrue(
            (ROOT / "mise.toml").is_file(), "no root Mise consumer for the manager"
        )
        self.assertEqual(set(renovate["enabledManagers"]), {"pep621", "mise"})
        self.assertNotIn(
            "mise", {row["package-ecosystem"] for row in config["updates"]}
        )
        self.assertFalse(renovate.get("automerge", False))
        self.assertLessEqual(renovate["prConcurrentLimit"], 4)

    def test_same_name_groups_preserve_separate_owner_locks(self):
        config = yaml.safe_load((ROOT / ".github/dependabot.yml").read_text(encoding="utf-8"))
        by_ecosystem = {x["package-ecosystem"]: x for x in config["updates"]}
        self.assertEqual(len(by_ecosystem), len(config["updates"]))
        for name in ("npm", "nix"):
            update = by_ecosystem[name]
            self.assertGreater(len(update["directories"]), 1)
            self.assertEqual(update["groups"]["same-dependency"], {"group-by": "dependency-name"})
            self.assertEqual(len(update["directories"]), len(set(update["directories"])))
        cargo = by_ecosystem["cargo"]
        self.assertEqual(
            set(cargo["directories"]),
            {"/services/runtime", "/domains/game/kits/room-action-r0"},
        )
        self.assertEqual(
            cargo["groups"]["same-dependency"], {"group-by": "dependency-name"}
        )
        self.assertNotIn("directory", cargo)
        for directory in cargo["directories"]:
            self.assertTrue((ROOT / directory.lstrip("/") / "Cargo.toml").is_file())
            self.assertTrue((ROOT / directory.lstrip("/") / "Cargo.lock").is_file())
        self.assertEqual(by_ecosystem["github-actions"]["directory"], "/")


if __name__ == "__main__":
    unittest.main()
