"""PG lifecycle adapter: only completed, quiet, known Workspace evidence is closable."""
from __future__ import annotations

from importlib.machinery import SourceFileLoader
from importlib.util import module_from_spec, spec_from_loader
from pathlib import Path
import sys
import unittest

ENTRY = Path(__file__).resolve().parents[1] / "ordivon-runtime-pg-reclaim"
sys.path.insert(0, str(ENTRY.parent))
loader = SourceFileLoader("ordivon_runtime_pg_reclaim", str(ENTRY))
spec = spec_from_loader(loader.name, loader)
assert spec is not None
mod = module_from_spec(spec)
loader.exec_module(mod)


class PgWorkspaceReclaimTests(unittest.TestCase):
    def setUp(self):
        self.params = dict(now_ms=10_000_000, created_ms=1_000_000,
                           latest_job_ms=5_000_000, latest_resolution="succeeded",
                           unresolved=0, min_age_ms=3_000_000)

    def test_reclaims_only_old_terminal_success(self):
        self.assertTrue(mod.eligible(**self.params))

    def test_does_not_conflate_failed_or_lost_job_with_delivery(self):
        for resolution in ("failed", "lost", "timed_out", "cancelled", None):
            self.assertFalse(mod.eligible(**{**self.params, "latest_resolution": resolution}))

    def test_active_job_blocks(self):
        self.assertFalse(mod.eligible(**{**self.params, "unresolved": 1}))

    def test_no_job_proof_blocks(self):
        self.assertFalse(mod.eligible(**{**self.params, "latest_job_ms": None}))

    def test_grace_counts_last_job_not_only_creation(self):
        self.assertFalse(mod.eligible(**{**self.params, "latest_job_ms": 8_000_000}))

    def test_boolean_and_future_creation_not_valid_times(self):
        self.assertFalse(mod.eligible(**{**self.params, "created_ms": True}))
        self.assertFalse(mod.eligible(**{**self.params, "created_ms": 20_000_000}))

    def test_identity_must_precede_job(self):
        self.assertFalse(mod.eligible(**{**self.params, "created_ms": 6_000_000}))


if __name__ == "__main__":
    unittest.main()
