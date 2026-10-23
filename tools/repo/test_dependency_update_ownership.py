#!/usr/bin/env python3
"""Keep dependency-update authority and cross-directory grouping unambiguous."""
from __future__ import annotations

import json
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]


class DependencyUpdateOwnershipTests(unittest.TestCase):
    def test_python_uv_lock_has_one_updater(self):
        renovate = json.loads((ROOT / "renovate.json").read_text(encoding="utf-8"))
        self.assertIn("pep621", renovate["enabledManagers"])
        self.assertTrue(renovate["lockFileMaintenance"]["enabled"])
        # Native Renovate grouping: one same-name PR across independent uv owners.
        self.assertEqual(
            renovate["packageRules"],
            [{"matchManagers": ["pep621"], "groupName": "Python {{depName}}"}],
        )
        config = yaml.safe_load((ROOT / ".github/dependabot.yml").read_text(encoding="utf-8"))
        ecosystems = [item["package-ecosystem"] for item in config["updates"]]
        self.assertNotIn("uv", ecosystems)

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
            cargo["directories"],
            ["/services/runtime", "/domains/game/kits/room-action-r0"],
        )
        self.assertEqual(cargo["groups"]["same-dependency"], {"group-by": "dependency-name"})
        self.assertNotIn("directory", cargo)
        self.assertEqual(by_ecosystem["github-actions"]["directory"], "/")


if __name__ == "__main__":
    unittest.main()
