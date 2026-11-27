"""Behavior contracts for the independent GitHub governance capabilities.

These tests execute real Git inventory and mutate policies; they do not require
functions to remain in a historical source file.
"""
from __future__ import annotations

import os
import subprocess
import tempfile
import unittest
from pathlib import Path

from tools.repo.github_governance.codeowners import active_rooted_codeowners
from tools.repo.github_governance.codeql import validate_monorepo_codeql
from tools.repo.github_governance.dependency_coverage import configured_dirs, update_for
from tools.repo.github_governance.git_paths import dirs_for_lock, tracked

ROOT = Path(__file__).resolve().parents[2]


class GitHubGovernanceModuleContracts(unittest.TestCase):
    def test_codeowners_root_and_later_override_contract(self) -> None:
        self.assertEqual(
            active_rooted_codeowners("* @team\n/services/runtime/ @maintainer\n"),
            {"/services/runtime/": ("@maintainer",)},
        )
        for invalid in (
            "/services/runtime/\n",
            "/services/runtime/ @maintainer\n",
            "* @team\n* @other\n/services/runtime/ @maintainer\n",
            "/services/runtime/ @maintainer\n* @team\n",
            "/services/ @maintainer\n/services/runtime/ @other\n",
        ):
            with self.subTest(invalid=invalid), self.assertRaises(AssertionError):
                    active_rooted_codeowners(invalid)

    def test_dependabot_source_coverage_rejects_ambiguous_owner(self) -> None:
        config = {"updates": [
            {"package-ecosystem": "npm", "directories": ["/a", "/b"]},
            {"package-ecosystem": "cargo", "directory": "/rust"},
        ]}
        self.assertEqual(configured_dirs(update_for(config, "npm")), {"/a", "/b"})
        self.assertEqual(configured_dirs(update_for(config, "cargo")), {"/rust"})
        config["updates"].append({"package-ecosystem": "npm", "directory": "/other"})
        with self.assertRaises(AssertionError):
            update_for(config, "npm")

    def test_codeql_actual_behavior_and_fault_injection(self) -> None:
        source = (ROOT / ".github/workflows/codeql.yml").read_text(encoding="utf-8")
        validate_monorepo_codeql(source)
        for corrupted in (
            source.replace("python, javascript-typescript, rust", "python, rust", 1),
            source.replace("  merge_group:\n", "  omitted_merge_group:\n", 1),
            source.replace("security-events: write", "security-events: read", 1),
        ):
            self.assertNotEqual(corrupted, source)
            with self.subTest(mutant=corrupted[:50]), self.assertRaises(AssertionError):
                    validate_monorepo_codeql(corrupted)

    def test_real_git_inventory_handles_non_utf8_and_newline_paths(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            subprocess.run(["git", "init", "-q", "-b", "main", str(repo)], check=True)
            names = ["part/line\nbreak/Cargo.lock"]
            if os.name != "nt":
                names.append(os.fsdecode(b"part/nonutf-\xff/Cargo.lock"))
            for rel in names:
                file = repo / rel
                file.parent.mkdir(parents=True, exist_ok=True)
                file.write_text("example", encoding="utf-8")
            subprocess.run(["git", "-C", str(repo), "add", "--all"], check=True)
            self.assertEqual(set(tracked(repo, "**/Cargo.lock")), set(names))
            self.assertEqual(
                dirs_for_lock(repo, "**/Cargo.lock", "Cargo.lock"),
                {"/" + str(Path(name).parent) for name in names},
            )


if __name__ == "__main__":
    unittest.main()
