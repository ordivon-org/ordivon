"""Regression contract: PG binary and Runner are built without SQLite features."""
from __future__ import annotations

import runpy
import sys
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


if __name__ == "__main__":
    unittest.main()
