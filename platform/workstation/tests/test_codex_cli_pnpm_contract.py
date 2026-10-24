"""Codex CLI's versioned Home Manager consumer uses owner-native pnpm."""
import json
import tomllib
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class CodexPnpmConsumerContract(unittest.TestCase):
    def test_nix_consumer_and_locked_manager_share_one_pnpm_authority(self):
        cli = ROOT / "workstation/nix/codex-cli"
        manifest = json.loads((cli / "package.json").read_text())
        with (ROOT / "mise.toml").open("rb") as stream:
            pnpm = tomllib.load(stream)["tools"]["pnpm"]
        self.assertEqual(manifest["packageManager"], f"pnpm@{pnpm}")
        self.assertTrue((cli / "pnpm-lock.yaml").is_file())
        self.assertFalse((cli / "package-lock.json").exists())
        home = (ROOT / "workstation/nix/nix/home.nix").read_text()
        self.assertIn("codex-pnpm-", home)
        self.assertNotIn("codex-npm-", home)
        self.assertIn("node_modules/@openai/codex/bin/codex.js", home)

    def test_owner_native_ci_has_no_duplicate_nested_github_workflow(self):
        # This project is verified by the root owner selector. Do not add an
        # independently maintained nested workflow just for Codex.
        with (ROOT / "mise.toml").open("rb") as stream:
            config = tomllib.load(stream)
        self.assertIn("codex:materialize", config["tasks"])
        cli = ROOT / "workstation/nix/codex-cli"
        manifest = json.loads((cli / "package.json").read_text())
        self.assertEqual(manifest["dependencies"]["@openai/codex"], "0.164.0")

    def test_existing_owner_has_one_native_materialization_task(self):
        with (ROOT / "mise.toml").open("rb") as stream:
            config = tomllib.load(stream)
        run = config["tasks"]["codex:materialize"]["run"]
        self.assertIn("pnpm install --frozen-lockfile", run)
        self.assertIn("pnpm-lock.yaml", run)
        self.assertIn("pnpm-workspace.yaml", run)
        self.assertNotIn("minimumReleaseAge: 0", run)
        self.assertIn("codex-pnpm-", run)
        self.assertNotIn("npm ci", run)


if __name__ == "__main__":
    unittest.main()
