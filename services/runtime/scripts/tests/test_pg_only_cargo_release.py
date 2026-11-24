"""Regression contract: PG binary and Runner are built without SQLite features."""
from __future__ import annotations

import argparse
import hashlib
import runpy
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS))
try:
    _deploy = runpy.run_path(str(SCRIPTS / "ordivon-runtime-deploy"), run_name="pg_release_test")
finally:
    sys.path.remove(str(SCRIPTS))


class PgOnlyReleaseBuildContract(unittest.TestCase):
    def test_two_native_binaries_do_not_share_all_features_invocation(self) -> None:
        cargo = Path("/opt/cargo/bin/cargo")
        dest = Path("/var/cache/ordivon/commit/release")
        cmds = _deploy["candidate_build_commands"](
            cargo, dest, ["ordivon-runtime-pg", "ordivon-runtime-runner"],
            explicit_binary_selection=True,
        )
        self.assertEqual(len(cmds), 2)
        for cmd in cmds:
            self.assertEqual(cmd[:3], [str(cargo), "build", "--release"])
            self.assertIn("--no-default-features", cmd)
            self.assertNotIn("--all-features", cmd)
            self.assertEqual(cmd[-2:], ["--target-dir", str(dest.parent)])
        self.assertEqual(cmds[0][cmds[0].index("-p") + 1], "ordivon-runtime-mcp")
        self.assertEqual(cmds[0][cmds[0].index("--features") + 1], "postgres-runtime")
        self.assertEqual(cmds[1][cmds[1].index("-p") + 1], "ordivon-runtime-core")
        self.assertEqual(cmds[1][cmds[1].index("--features") + 1], "runtime-contract")

    def test_legacy_profiles_keep_the_previous_build_contract(self) -> None:
        cargo = Path("/opt/cargo/bin/cargo")
        dest = Path("/var/cache/ordivon/commit/release")
        expected = [[str(cargo), "build", "--release", "--workspace",
                     "--all-features", "--target-dir", str(dest.parent)]]
        for binaries, selected in (
            (["ordivon-runtime", "ordivon-runtime-runner"], True),
            (["ordivon-runtime-pg", "ordivon-runtime-runner"], False),
        ):
            with self.subTest(binaries=binaries, selected=selected):
                cmds = _deploy["candidate_build_commands"](
                    cargo, dest, binaries, explicit_binary_selection=selected,
                )
                self.assertEqual(cmds, expected)

    def test_native_dual_binary_pg_reclaimer_is_qualified_release_artifact(self) -> None:
        """Reclaimer must be in the SAME immutable release, not a stale sidecar."""
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source"
            (source / "scripts").mkdir(parents=True)
            reclaimer_bytes = b"#!/usr/bin/env python3\nprint('reclaimer current')\n"
            (source / "scripts" / "ordivon-runtime-pg-reclaim").write_bytes(reclaimer_bytes)
            target = root / "target" / "release"
            target.mkdir(parents=True)
            args = argparse.Namespace(
                binaries=["ordivon-runtime-pg", "ordivon-runtime-runner"],
                include_pg_reclaimer=True, candidate_dir=target,
            )
            specs = _deploy["release_artifact_specs"](args)
            self.assertEqual([str(item["name"]) for item in specs], [
                "ordivon-runtime-pg", "ordivon-runtime-runner",
                "ordivon-runtime-pg-reclaim",
            ])
            self.assertEqual(specs[-1]["kind"], "operator")
            for name in args.binaries:
                (target / name).write_bytes(name.encode())
                (target / name).chmod(0o755)
            _deploy["stage_operator_artifacts"](args, source)
            self.assertEqual((target / "ordivon-runtime-pg-reclaim").read_bytes(), reclaimer_bytes)
            candidate = _deploy["candidate_artifacts"](args)
            reclaimer = next(item for item in candidate if item["name"] == "ordivon-runtime-pg-reclaim")
            self.assertEqual(reclaimer["digest"], "sha256:" + hashlib.sha256(reclaimer_bytes).hexdigest())
            source_reclaimer = source / "scripts" / "ordivon-runtime-pg-reclaim"
            source_reclaimer.unlink()
            with self.assertRaisesRegex(RuntimeError, "missing or unsafe"):
                _deploy["stage_operator_artifacts"](args, source)
            source_reclaimer.symlink_to(target / "ordivon-runtime-pg-reclaim")
            with self.assertRaisesRegex(RuntimeError, "missing or unsafe"):
                _deploy["stage_operator_artifacts"](args, source)

    def test_binary_subset_retains_old_mode_and_wrong_opt_in_pair_is_rejected(self) -> None:
        subset = argparse.Namespace(
            binaries=["ordivon-runtime-pg", "ordivon-runtime-runner"],
            include_pg_reclaimer=False,
        )
        self.assertEqual(
            [item["name"] for item in _deploy["release_artifact_specs"](subset)],
            list(subset.binaries),
        )
        invalid = argparse.Namespace(
            binaries=["ordivon-runtime-pg"],
            include_pg_reclaimer=True,
        )
        with self.assertRaisesRegex(RuntimeError, "full native PG binary pair"):
            _deploy["release_artifact_specs"](invalid)


if __name__ == "__main__":
    unittest.main()
