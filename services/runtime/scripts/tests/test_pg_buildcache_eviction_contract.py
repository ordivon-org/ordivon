"""Focused source-level falsifiers for the PostgreSQL build-cache eviction fence.

These pure tests never connect to production PG, dispatch work or remove a real
Runtime cache. They validate admission/identity conditions, not physical
concurrency, systemd process identity or installed source currentness.
"""
from __future__ import annotations

from importlib.machinery import SourceFileLoader
from importlib.util import module_from_spec, spec_from_loader
from pathlib import Path
import sys
import tempfile
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "ordivon-runtime-pg-buildcache-evict"
sys.path.insert(0, str(SCRIPT.parent))
loader = SourceFileLoader("ordivon_pg_buildcache_eviction_contract", str(SCRIPT))
spec = spec_from_loader(loader.name, loader)
assert spec is not None
evict = module_from_spec(spec)
loader.exec_module(evict)

HEAD = "a" * 40
DIGEST = "sha256:" + "b" * 64


class BuildCacheEvictionContractTests(unittest.TestCase):
    def test_valid_exact_source_identity(self):
        evict.validate_identity("ws-safe_01", HEAD, DIGEST)

    def test_rejects_malformed_or_pathlike_workspace_identity(self):
        for ident in ("", "../outside", "/absolute", "has space", "x" * 97):
            with self.subTest(ident=ident), self.assertRaises(ValueError):
                evict.validate_identity(ident, HEAD, DIGEST)

    def test_rejects_unqualified_git_and_digest(self):
        for head, digest in (("main", DIGEST), (HEAD, "sha256:abc"), (HEAD.upper(), DIGEST)):
            with self.subTest(head=head[:8], digest=digest[:12]), self.assertRaises(ValueError):
                evict.validate_identity("ws-safe", head, digest)

    def test_exact_four_hour_boundary_is_eligible_only_when_settled(self):
        now = 1_000_000_000
        quiet = now - evict.MIN_QUIET_MS
        self.assertTrue(evict.qualified_quiet(quiet, now, 0, 0, "succeeded"))
        self.assertFalse(evict.qualified_quiet(quiet + 1, now, 0, 0, "succeeded"))

    def test_unresolved_held_and_non_success_fail_closed(self):
        now = 1_000_000_000
        quiet = now - evict.MIN_QUIET_MS - 1
        for unresolved, held, resolution in (
            (1, 0, "succeeded"), (0, 1, "succeeded"),
            (0, 0, "failed"), (0, 0, "lost"), (0, 0, None)
        ):
            with self.subTest(case=(unresolved, held, resolution)):
                self.assertFalse(
                    evict.qualified_quiet(quiet, now, unresolved, held, resolution)
                )

    def test_missing_and_future_activity_fail_closed(self):
        now = 1_000_000_000
        for last in (0, -1, now + 1):
            with self.subTest(last=last):
                self.assertFalse(evict.qualified_quiet(last, now, 0, 0, "succeeded"))

    def test_symlink_cache_carrier_is_not_admitted(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            real = root / "real"
            real.mkdir()
            link = root / "alias"
            link.symlink_to(real, target_is_directory=True)
            self.assertEqual(evict.direct_directory(real), real)
            with self.assertRaises(RuntimeError):
                evict.direct_directory(link)

    def test_git_source_readback_ignores_inherited_foreign_git_authority(self):
        """A foreign GIT_DIR must not make another Git repo the source witness."""
        import os
        import subprocess
        from unittest.mock import patch

        with tempfile.TemporaryDirectory() as tmp:
            first = Path(tmp) / "workspace"
            other = Path(tmp) / "foreign"
            for repo, message in ((first, "expected-workspace"), (other, "attacker")):
                repo.mkdir()
                subprocess.run(["/usr/bin/git", "-C", str(repo), "init", "-q"],
                               check=True, capture_output=True)
                subprocess.run(
                    ["/usr/bin/git", "-C", str(repo),
                     "-c", "user.name=Temporary Test",
                     "-c", "user.email=temporary@local.invalid",
                     "commit", "-q", "--allow-empty", "-m", message],
                    check=True, capture_output=True,
                )
            correct_head = evict.git(first, "rev-parse", "HEAD")
            foreign_head = evict.git(other, "rev-parse", "HEAD")
            self.assertNotEqual(correct_head, foreign_head)
            with patch.dict(os.environ, {
                "GIT_DIR": str(other / ".git"),
                "GIT_WORK_TREE": str(other),
                "GIT_INDEX_FILE": str(other / ".git" / "index"),
            }):
                self.assertEqual(evict.git(first, "rev-parse", "HEAD"), correct_head)
                self.assertEqual(
                    evict.git(first, "status", "--porcelain", "--untracked-files=normal"),
                    "",
                )

    def test_receipt_is_immutable_and_never_overwritten(self):
        with tempfile.TemporaryDirectory() as tmp:
            receipt = Path(tmp) / "owned" / "plan.json"
            evict.atomic_receipt(receipt, {"effect": "prepared"})
            original = receipt.read_bytes()
            with self.assertRaises(RuntimeError):
                evict.atomic_receipt(receipt, {"effect": "overwritten"})
            self.assertEqual(receipt.read_bytes(), original)


class OpenFdConsumerTests(unittest.TestCase):
    def test_open_fd_inside_cache_is_visible_even_when_cwd_is_elsewhere(self):
        """Observe a real kernel FD without enumerating unrelated CI processes."""
        with tempfile.TemporaryDirectory() as tmp:
            cache = Path(tmp) / "build"
            cache.mkdir()
            artifact = cache / "held-output.o"
            artifact.write_bytes(b"compiler-output")

            # The isolated /proc view contains only this test process. The FD
            # directory itself is the real kernel-owned /proc/<pid>/fd.
            pid = str(__import__("os").getpid())
            proc_root = Path(tmp) / "proc"
            proc = proc_root / pid
            proc.mkdir(parents=True)
            (proc / "cwd").symlink_to(Path.cwd(), target_is_directory=True)
            (proc / "fd").symlink_to(Path("/proc") / pid / "fd", target_is_directory=True)
            with artifact.open("rb"):
                consumers = evict.external_processes_using(cache, proc_root)
                self.assertIn(pid, consumers)

    def test_mapped_cache_file_is_visible_without_fd_observation(self):
        import mmap
        import os

        with tempfile.TemporaryDirectory() as tmp:
            cache = Path(tmp) / "build"
            cache.mkdir()
            artifact = cache / "mapped output"
            artifact.write_bytes(b"compiler-output")
            pid = str(os.getpid())
            proc_root = Path(tmp) / "proc"
            proc = proc_root / pid
            proc.mkdir(parents=True)
            (proc / "cwd").symlink_to(Path.cwd())
            (proc / "fd").mkdir()
            (proc / "maps").symlink_to(Path("/proc") / pid / "maps")
            with artifact.open("rb") as file, mmap.mmap(
                file.fileno(), 0, access=mmap.ACCESS_READ
            ):
                self.assertIn(pid, evict.external_processes_using(cache, proc_root))

    def test_executable_reference_is_a_consumer(self):
        with tempfile.TemporaryDirectory() as tmp:
            cache = Path(tmp) / "build"
            cache.mkdir()
            proc_root = Path(tmp) / "proc"
            proc = proc_root / "123"
            proc.mkdir(parents=True)
            (proc / "cwd").symlink_to(Path.cwd())
            (proc / "fd").mkdir()
            (proc / "exe").symlink_to(cache / "program")
            (proc / "maps").write_text("")
            self.assertEqual(evict.external_processes_using(cache, proc_root), ["123"])

    def test_unreadable_mappings_fail_closed(self):
        from unittest.mock import patch

        with tempfile.TemporaryDirectory() as tmp:
            cache = Path(tmp) / "build"
            cache.mkdir()
            proc_root = Path(tmp) / "proc"
            proc = proc_root / "123"
            proc.mkdir(parents=True)
            (proc / "fd").mkdir()
            with patch.object(Path, "open", side_effect=PermissionError):
                with self.assertRaisesRegex(RuntimeError, "mappings are unreadable"):
                    evict.external_processes_using(cache, proc_root)

    def test_root_reference_is_a_consumer_and_sibling_is_not(self):
        with tempfile.TemporaryDirectory() as tmp:
            cache = Path(tmp) / "build"
            cache.mkdir()
            proc_root = Path(tmp) / "proc"
            for pid, root in (("123", cache), ("124", cache.with_name("build-other"))):
                proc = proc_root / pid
                proc.mkdir(parents=True)
                (proc / "root").symlink_to(root)
                (proc / "fd").mkdir()
                (proc / "maps").write_text("")
            self.assertEqual(evict.external_processes_using(cache, proc_root), ["123"])


if __name__ == "__main__":
    unittest.main()
