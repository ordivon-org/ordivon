"""Non-privileged regression tests for isolated PITR scratch cleanup."""
from __future__ import annotations

import runpy
import tempfile
import unittest
from pathlib import Path


stop_scratch_clusters = runpy.run_path(
    str(Path(__file__).with_name("pg_recovery_pitr_probe.py"))
)["stop_scratch_clusters"]


class ScratchCleanupTests(unittest.TestCase):
    def test_cleanup_attempts_every_cluster_and_rejects_uncertainty(self) -> None:
        names = ["pitr", "sibling", "restore", "primary"]
        for scenario in ("clean", "stop failure", "uncertain start", "residual pid"):
            with self.subTest(scenario=scenario), tempfile.TemporaryDirectory() as name:
                root = Path(name)
                calls = []

                def stop(cluster: str) -> None:
                    calls.append(cluster)
                    if scenario == "stop failure" and cluster == "pitr":
                        raise OSError("synthetic stop failure")

                uncertain = {"primary"} if scenario == "uncertain start" else set()
                if scenario == "residual pid":
                    (root / "primary").mkdir()
                    (root / "primary" / "postmaster.pid").touch()
                if scenario == "clean":
                    stop_scratch_clusters(root, stop, uncertain)
                else:
                    with self.assertRaisesRegex(RuntimeError, "preserving scratch"):
                        stop_scratch_clusters(root, stop, uncertain)
                self.assertEqual(calls, names)


if __name__ == "__main__":
    unittest.main()
