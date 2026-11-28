"""Non-privileged regression tests for isolated PITR scratch cleanup."""
from __future__ import annotations

import io
import json
import runpy
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest.mock import patch


probe = runpy.run_path(str(Path(__file__).with_name("pg_recovery_pitr_probe.py")))
stop_scratch_clusters = probe["stop_scratch_clusters"]
main = probe["main"]


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


class ScratchEntrypointTests(unittest.TestCase):
    def test_success_is_reported_after_owned_scratch_is_removed(self) -> None:
        with tempfile.TemporaryDirectory() as parent:
            root = Path(parent) / "owned-scratch"
            root.mkdir()
            (root / "evidence").write_text("synthetic", encoding="utf-8")
            stdout = io.StringIO()
            with (
                patch.dict(main.__globals__, {"execute": lambda _: {"status": "PASS"}}),
                patch("os.geteuid", return_value=0, create=True),
                patch("tempfile.mkdtemp", return_value=str(root)),
                redirect_stdout(stdout),
            ):
                main()
            self.assertFalse(root.exists())
            self.assertEqual(json.loads(stdout.getvalue())["scratchCleanup"], "confirmed")

    def test_uncertain_shutdown_preserves_scratch_without_success(self) -> None:
        with tempfile.TemporaryDirectory() as parent:
            root = Path(parent) / "owned-scratch"
            root.mkdir()
            evidence = root / "evidence"
            evidence.write_text("synthetic", encoding="utf-8")
            stdout, stderr = io.StringIO(), io.StringIO()

            def failed_execute(path: Path) -> dict:
                self.assertEqual(path, root)
                raise RuntimeError("synthetic uncertainty")

            with (
                patch.dict(main.__globals__, {"execute": failed_execute}),
                patch("os.geteuid", return_value=0, create=True),
                patch("tempfile.mkdtemp", return_value=str(root)),
                redirect_stdout(stdout),
                redirect_stderr(stderr),
                self.assertRaisesRegex(RuntimeError, "synthetic uncertainty"),
            ):
                main()
            self.assertEqual(stdout.getvalue(), "")
            self.assertIn(str(root), stderr.getvalue())
            self.assertEqual(evidence.read_text(encoding="utf-8"), "synthetic")

    def test_deletion_failure_cannot_report_success(self) -> None:
        with tempfile.TemporaryDirectory() as parent:
            root = Path(parent) / "owned-scratch"
            root.mkdir()
            stdout = io.StringIO()
            with (
                patch.dict(main.__globals__, {"execute": lambda _: {"status": "PASS"}}),
                patch("os.geteuid", return_value=0, create=True),
                patch("tempfile.mkdtemp", return_value=str(root)),
                patch("shutil.rmtree", side_effect=OSError("synthetic deletion failure")),
                redirect_stdout(stdout),
                self.assertRaisesRegex(OSError, "synthetic deletion failure"),
            ):
                main()
            self.assertTrue(root.exists())
            self.assertEqual(stdout.getvalue(), "")


if __name__ == "__main__":
    unittest.main()
