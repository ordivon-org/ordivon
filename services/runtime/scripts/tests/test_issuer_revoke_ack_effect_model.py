"""Pinned TLC checks for the native Manager-cancel / original-effect distinction.

This is a single-Attempt abstract design check, not an installed systemd
or PostgreSQL receiver proof. Native physical evidence is separate.
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
MODEL = "IssuerRevokeAckR1"
JAR_ENV = "ORDIVON_TLA_TOOLS_JAR"


class IssuerRevokeAckEffectModelTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        lock = json.loads((FORMAL / "toolchain.lock.json").read_text(encoding="utf-8"))
        jar = Path(os.environ[JAR_ENV]) if JAR_ENV in os.environ else ROOT / lock["cacheRelativePath"]
        required = os.environ.get("ORDIVON_RUN_ISSUER_ACK_EFFECT_MODEL_TEST") == "1" or JAR_ENV in os.environ
        if not jar.is_file() and not required:
            raise unittest.SkipTest("pinned TLC JAR not materialized; run scripts/tla-formal bootstrap")
        subprocess.run(["bash", str(ROOT / "scripts/tla-formal"), "verify"], cwd=ROOT, check=True, timeout=20)
        cls.jar = jar.resolve()
        cls.source = (FORMAL / f"{MODEL}.tla").read_text(encoding="utf-8")

    def run_model(self, source: str, config: str):
        with tempfile.TemporaryDirectory(prefix="ordivon-issuer-ack-effect-") as directory:
            scratch = Path(directory)
            (scratch / f"{MODEL}.tla").write_text(source, encoding="utf-8")
            (scratch / "case.cfg").write_text(config, encoding="utf-8")
            return subprocess.run(
                ["java", "-Xmx256m", "-XX:+UseSerialGC", "-cp", str(self.jar),
                 "tlc2.TLC", "-workers", "1", "-config", "case.cfg", f"{MODEL}.tla"],
                cwd=scratch, text=True, stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT, timeout=40, check=False,
            )

    def test_safe_ack_excludes_late_original_effect_and_actual_spawn(self):
        config = (FORMAL / f"{MODEL}.manager-effect-safe.cfg").read_text(encoding="utf-8")
        result = self.run_model(self.source, config)
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertIn("Model checking completed. No error has been found.", result.stdout)

    def test_original_effect_after_manager_cancel_is_reachable(self):
        config = (FORMAL / f"{MODEL}.manager-effect-positive-reach.cfg").read_text(encoding="utf-8")
        result = self.run_model(self.source, config)
        self.assertEqual(result.returncode, 12, result.stdout)
        self.assertIn("Error: Invariant ManagerCancelEffectUnreachable is violated.", result.stdout)
        self.assertIn('nativeUnit = "running_manager_cancelled"', result.stdout)
        self.assertIn('nativeUnit = "effect_completed"', result.stdout)
        self.assertIn("revokeAck = FALSE", result.stdout)

    def test_manager_cancel_as_ack_mutant_allows_effect_without_any_new_spawn(self):
        start, end = self.source.index("PublishRevokeAck ==\n"), self.source.index("Next ==\n")
        block = self.source[start:end]
        guard = '    /\\ nativeUnit = "quiescent"\n'
        self.assertEqual(block.count(guard), 1)
        mutant = self.source[:start] + block.replace(
            guard, '    /\\ nativeUnit \\in {"quiescent", "running_manager_cancelled"}\n', 1
        ) + self.source[end:]
        # Keep NoSpawnAfterRevokeAck active: this different counterexample
        # must be witnessed even when there is no new target spawn.
        config = """SPECIFICATION Spec
CONSTANT LaunchPolicy = "drainAck"
INVARIANTS
    TypeOK
    AtMostOnceDispatch
    NoSpawnAfterRevokeAck
    NoOriginalEffectAfterAck
CHECK_DEADLOCK FALSE
"""
        result = self.run_model(mutant, config)
        self.assertEqual(result.returncode, 12, result.stdout)
        self.assertIn("Error: Invariant NoOriginalEffectAfterAck is violated.", result.stdout)
        final = result.stdout.rsplit("State ", 1)[-1]
        self.assertIn('nativeUnit = "effect_after_ack"', final)
        self.assertIn("revokeAck = TRUE", final)
        self.assertIn("spawnedAfterAck = FALSE", final)


if __name__ == "__main__":
    unittest.main()
