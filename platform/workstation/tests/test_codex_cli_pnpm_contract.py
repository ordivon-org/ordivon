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

    def test_ci_replays_real_frozen_codex_consumer(self):
        workflow = (ROOT / ".github/workflows/ci.yml").read_text()
        self.assertIn("workstation/nix/codex-cli", workflow)
        self.assertIn("pnpm install --frozen-lockfile", workflow)
        self.assertIn("pnpm exec codex --version", workflow)

    def test_existing_owner_has_one_native_materialization_task(self):
        with (ROOT / "mise.toml").open("rb") as stream:
            config = tomllib.load(stream)
        run = config["tasks"]["codex:materialize"]["run"]
        self.assertIn("pnpm install --frozen-lockfile", run)
        self.assertIn("pnpm-lock.yaml", run)
        self.assertIn("codex-pnpm-", run)
        self.assertNotIn("npm ci", run)


if __name__ == "__main__":
    unittest.main()
