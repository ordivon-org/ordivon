"""Test PostgreSQL physical-test admission through behavior, not source-file positions.

Rust unit tests and the disposable PG18 task own the actual Job, Attempt,
cancel, terminal, and replay correctness claims.  This Python suite verifies
that neither physical lane can run without its explicit isolated-test DSN.
"""

import os
from pathlib import Path
import subprocess
import tomllib
import unittest


ROOT = Path(__file__).resolve().parents[2]
MISE = ROOT / "mise.toml"


class PgPhysicalVerificationContractTests(unittest.TestCase):
    def _assert_dsn_required(self, *, task: str, variable: str) -> None:
        with MISE.open("rb") as stream:
            command = tomllib.load(stream)["tasks"][task]["run"]

        env = dict(os.environ)
        env.pop(variable, None)
        # This is the real task's bash command, not an AST or a positional
        # source-file regex.  The missing DSN must stop BEFORE any Cargo/PG
        # process is started, regardless of future Rust file organization.
        result = subprocess.run(
            ["bash", "-c", command],
            cwd=ROOT,
            env=env,
            capture_output=True,
            text=True,
            check=False,
            timeout=15,
        )
        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertIn(variable, result.stderr)
        self.assertIn("required", result.stderr)
        self.assertNotIn("Compiling", result.stderr)
        self.assertNotIn("test result:", result.stdout)

    def test_fresh_physical_lane_cannot_run_without_test_dsn(self) -> None:
        self._assert_dsn_required(
            task="test:postgres-registry:physical",
            variable="ORDIVON_PG_TEST_DSN",
        )

    def test_historical_stage_lane_cannot_run_without_stage_dsn(self) -> None:
        self._assert_dsn_required(
            task="test:postgres-registry:stage",
            variable="ORDIVON_PG_STAGE_TEST_DSN",
        )


if __name__ == "__main__":
    unittest.main()
