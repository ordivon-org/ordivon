"""Actual pinned-TLC checks for early revocation and exact issued-set closure.

Run after scripts/tla-formal bootstrap, or with the already supported
ORDIVON_TLA_TOOLS_JAR. A missing default JAR skips explicitly; an explicitly
requested or supplied toolchain must verify. All model mutations are disposable.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
FORMAL = ROOT / "formal"
MODEL = "IssuerRevokeEpochR1"
JAR_ENV = "ORDIVON_TLA_TOOLS_JAR"


class IssuerRevokeEpochModelTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        lock = json.loads((FORMAL / "toolchain.lock.json").read_text(encoding="utf-8"))
        jar = Path(os.environ[JAR_ENV]) if JAR_ENV in os.environ else ROOT / lock["cacheRelativePath"]
        required = os.environ.get("ORDIVON_RUN_ISSUER_EPOCH_MODEL_TEST") == "1" or JAR_ENV in os.environ
        if not jar.is_file() and not required:
            raise unittest.SkipTest("pinned TLC JAR not materialized; run scripts/tla-formal bootstrap")
        subprocess.run(
            ["bash", str(ROOT / "scripts/tla-formal"), "verify"],
            cwd=ROOT, check=True, timeout=20,
        )
        cls.jar = jar.resolve()
        cls.source = (FORMAL / f"{MODEL}.tla").read_text(encoding="utf-8")

    def run_model(self, source, config):
        with tempfile.TemporaryDirectory(prefix="ordivon-issuer-epoch-model-") as directory:
            scratch = Path(directory)
            (scratch / f"{MODEL}.tla").write_text(source, encoding="utf-8")
            (scratch / "case.cfg").write_text(config, encoding="utf-8")
            return subprocess.run(
                ["java", "-Xmx256m", "-XX:+UseSerialGC", "-cp", str(self.jar),
                 "tlc2.TLC", "-workers", "1", "-config", "case.cfg", f"{MODEL}.tla"],
                cwd=scratch, text=True, stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT, timeout=40, check=False,
            )

    def replace_once(self, source, old, new):
        self.assertEqual(source.count(old), 1, "semantic mutation target changed")
        return source.replace(old, new, 1)

    def test_safety_and_early_ack_paths_are_reachable(self):
        config = (FORMAL / f"{MODEL}.safe.cfg").read_text(encoding="utf-8")
        result = self.run_model(self.source, config)
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertIn("Model checking completed. No error has been found.", result.stdout)
        for case, invariant in (
            ("zero-issued", "ZeroIssuedAckUnreachable"),
            ("single-issued", "SingleIssuedAckUnreachable"),
            ("single-issued-drain", "SingleIssuedDrainAckUnreachable"),
        ):
            with self.subTest(case=case):
                config = (FORMAL / f"{MODEL}.{case}-ack-positive-reach.cfg").read_text(
                    encoding="utf-8"
                )
                result = self.run_model(self.source, config)
                self.assertEqual(result.returncode, 12, result.stdout)
                self.assertIn(f"Error: Invariant {invariant} is violated.", result.stdout)
                self.assertIn("revokeAck = TRUE", result.stdout)

    def test_issuer_fence_removal_permits_late_issue_and_is_rejected(self):
        mutant = self.replace_once(
            self.source,
            'Issue(a) ==\n    /\\ issuer = "current"\n    /\\ ~fenced\n',
            "Issue(a) ==\n",
        )
        result = self.run_model(
            mutant, "SPECIFICATION Spec\nPROPERTY IssuedSetStableAfterFence\nCHECK_DEADLOCK FALSE\n"
        )
        self.assertEqual(result.returncode, 13, result.stdout)
        self.assertIn("Error: Action property IssuedSetStableAfterFence is violated.", result.stdout)
        self.assertIn("fenced = TRUE", result.stdout)
        self.assertRegex(result.stdout, r'issued = \{"[ab]"\}')

    def test_partial_ack_of_two_actually_issued_attempts_is_rejected(self):
        # Keep the original two-issued negative control non-vacuous now that
        # a never-issued slot is also resolved at an epoch-wide revoke cut.
        # Restrict this disposable mutant only; the safe model stays general.
        old = 'CommitRevoke ==\n    /\\ issuer = "current"\n'
        mutant = self.replace_once(self.source, old, old + "    /\\ issued = AttemptIds\n")
        start, end = mutant.index("PublishAck ==\n"), mutant.index("Next ==\n")
        block = self.replace_once(
            mutant[start:end],
            "    /\\ \\A a \\in AttemptIds: LaunchFinalized(a)\n",
            "    /\\ \\E a \\in AttemptIds: LaunchFinalized(a)\n",
        )
        mutant = mutant[:start] + block + mutant[end:]
        result = self.run_model(
            mutant, "SPECIFICATION Spec\nINVARIANT NoSpawnAfterAck\nCHECK_DEADLOCK FALSE\n"
        )
        self.assertEqual(result.returncode, 12, result.stdout)
        self.assertIn("Error: Invariant NoSpawnAfterAck is violated.", result.stdout)
        self.assertIn('issued = {"a", "b"}', result.stdout)
        self.assertIn("revokeAck = TRUE", result.stdout)
        self.assertIn("spawnedAfterAck = TRUE", result.stdout)


if __name__ == "__main__":
    unittest.main()
