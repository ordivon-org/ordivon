from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import agent_automation_release as release  # noqa: E402
import browser_security_browserless_canary as canary  # noqa: E402
import browser_security_pool_runner as pool  # noqa: E402
import browserless_image_promotion as promotion  # noqa: E402

CANONICAL_SECURITY_ROOT = Path("/root/projects/ordivon/platform/security")
CANONICAL_HARNESS_ROOT = Path("/root/projects/ordivon/services/harness")


class SecurityOwnerLocatorTests(unittest.TestCase):
    def test_default_harness_source_is_canonical_monorepo_owner(self) -> None:
        self.assertEqual(release.SOURCE_REPO, CANONICAL_HARNESS_ROOT)
        self.assertEqual(promotion.CANONICAL_SOURCE_REPO, CANONICAL_HARNESS_ROOT)

    def test_default_security_root_is_canonical_monorepo_owner(self) -> None:
        self.assertEqual(release.SECURITY_ROOT, CANONICAL_SECURITY_ROOT)
        self.assertEqual(canary.SECURITY_ROOT, CANONICAL_SECURITY_ROOT)
        self.assertEqual(pool.DEFAULT_SECURITY_ROOT, CANONICAL_SECURITY_ROOT)
        self.assertEqual(promotion.SECURITY_ROOT, CANONICAL_SECURITY_ROOT)

    def _nested_owner_repo(self, root: Path) -> tuple[Path, str, str]:
        repo = root / "repo"
        owner = repo / "platform" / "security"
        owner.mkdir(parents=True)
        subprocess.run(["git", "-C", str(repo), "init", "-q", "-b", "main"], check=True)
        subprocess.run(["git", "-C", str(repo), "config", "user.email", "test@example.invalid"], check=True)
        subprocess.run(["git", "-C", str(repo), "config", "user.name", "test"], check=True)

        (owner / "owner.txt").write_text("security\n", encoding="utf-8")
        subprocess.run(["git", "-C", str(repo), "add", "."], check=True)
        subprocess.run(["git", "-C", str(repo), "commit", "-qm", "security"], check=True)
        owner_revision = subprocess.check_output(
            ["git", "-C", str(repo), "rev-parse", "HEAD"], text=True
        ).strip()

        (repo / "unrelated.txt").write_text("host\n", encoding="utf-8")
        subprocess.run(["git", "-C", str(repo), "add", "unrelated.txt"], check=True)
        subprocess.run(["git", "-C", str(repo), "commit", "-qm", "unrelated"], check=True)
        repo_head = subprocess.check_output(
            ["git", "-C", str(repo), "rev-parse", "HEAD"], text=True
        ).strip()
        return owner, owner_revision, repo_head

    def test_path_scoped_revision_ignores_unrelated_monorepo_commit(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            owner, owner_revision, repo_head = self._nested_owner_repo(Path(td))
            self.assertNotEqual(owner_revision, repo_head)
            self.assertEqual(pool._source_revision(owner), owner_revision)
            self.assertEqual(canary._source_revision(owner), owner_revision)

    def test_promotion_clean_revision_is_owner_scoped(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            owner, owner_revision, _ = self._nested_owner_repo(Path(td))
            with mock.patch.object(promotion, "SECURITY_ROOT", owner):
                self.assertEqual(promotion._security_clean_revision(), owner_revision)

                # Unrelated monorepo dirt must not contaminate Security owner standing.
                repo = owner.parents[1]
                (repo / "outside-dirty.txt").write_text("outside\n", encoding="utf-8")
                self.assertEqual(promotion._security_clean_revision(), owner_revision)

                # Owner-local dirt must still fail closed.
                (owner / "owner.txt").write_text("dirty\n", encoding="utf-8")
                with self.assertRaisesRegex(
                    promotion.PromotionError, "Security owner subtree must be clean"
                ):
                    promotion._security_clean_revision()


if __name__ == "__main__":
    unittest.main()
