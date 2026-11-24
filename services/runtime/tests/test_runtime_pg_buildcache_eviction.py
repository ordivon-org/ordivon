"""Fast negative specifications for the PG-only rebuildable cache adapter."""
import importlib.machinery
import importlib.util
import sys
from pathlib import Path
import tempfile
import unittest

PATH = Path(__file__).resolve().parents[1] / "scripts" / "ordivon-runtime-pg-buildcache-evict"
sys.path.insert(0, str(PATH.parent))
loader = importlib.machinery.SourceFileLoader("ordivon_pg_buildcache_eviction", str(PATH))
spec = importlib.util.spec_from_loader(loader.name, loader)
module = importlib.util.module_from_spec(spec)
loader.exec_module(module)


class TestPgBuildCacheSafety(unittest.TestCase):
    def test_systemd_source_cut_overlays_override_base(self):
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp) / "first.env"
            final = Path(temp) / "last.env"
            base.write_text("ORDIVON_PG_SOURCE_SHA256=old\nOTHER_KEY=unchanged\n")
            final.write_text("ORDIVON_PG_SOURCE_SHA256=current\n")
            value = module.effective_environment(base, [final])
            self.assertEqual(value["ORDIVON_PG_SOURCE_SHA256"], "current")
            self.assertEqual(value["OTHER_KEY"], "unchanged")

    def test_rejects_invalid_identity(self):
        for ident in ("../../etc", "", ".invalid", "x/../y", "x" * 97):
            with self.subTest(ident=ident):
                with self.assertRaises(ValueError):
                    module.validate_identity(ident, "a" * 40, "sha256:" + "b" * 64)

    def test_rejects_source_digest_and_head_drift(self):
        for head, digest in (("A" * 40, "sha256:" + "b" * 64),
                             ("a" * 40, "sha256:x"),
                             ("a" * 39, "sha256:" + "b" * 64)):
            with self.assertRaises(ValueError):
                module.validate_identity("ws-check", head, digest)

    def test_quiet_is_not_domain_success_or_release_proof(self):
        now = 40_000_000
        old = now - module.MIN_QUIET_MS - 1
        self.assertTrue(module.qualified_quiet(old, now, 0, 0, "succeeded"))
        for last, u, held, resolution in (
            (now, 0, 0, "succeeded"), (old, 1, 0, "succeeded"),
            (old, 0, 1, "succeeded"), (old, 0, 0, "failed"),
            (old, 0, 0, None), (0, 0, 0, "succeeded"),
        ):
            self.assertFalse(module.qualified_quiet(last, now, u, held, resolution))

    def test_symlink_directory_is_not_removable_cache(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "real").mkdir()
            (root / "alias").symlink_to(root / "real", target_is_directory=True)
            self.assertEqual(module.direct_directory(root / "real"), root / "real")
            with self.assertRaises(RuntimeError):
                module.direct_directory(root / "alias")


if __name__ == "__main__":
    unittest.main()
