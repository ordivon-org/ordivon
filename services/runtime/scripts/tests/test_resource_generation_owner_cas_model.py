"""Bounded TLC owner-generation contract, including independent falsifiers.

Uses the existing pinned TLC toolchain and portable unittest collector. An
explicit run may not pass via missing-toolchain skip or zero test selection.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
import re
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
FORMAL = ROOT / "formal"
MODEL = "ResourceGenerationOwnerR1"
JAR_ENV = "ORDIVON_TLA_TOOLS_JAR"


class ResourceGenerationOwnerModelTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        lock = json.loads((FORMAL / "toolchain.lock.json").read_text(encoding="utf-8"))
        jar = Path(os.environ[JAR_ENV]) if JAR_ENV in os.environ else ROOT / lock["cacheRelativePath"]
        required = os.environ.get("ORDIVON_RUN_RESOURCE_GENERATION_MODEL_TEST") == "1" or JAR_ENV in os.environ
        if not jar.is_file() and not required:
            raise unittest.SkipTest("pinned TLC JAR unavailable; run scripts/tla-formal bootstrap")
        subprocess.run(["bash", str(ROOT / "scripts/tla-formal"), "verify"],
                       cwd=ROOT, check=True, timeout=20)
        cls.jar = jar.resolve()
        cls.source = (FORMAL / f"{MODEL}.tla").read_text(encoding="utf-8")
        cls.safe_config = (FORMAL / f"{MODEL}.cfg").read_text(encoding="utf-8")

    def run_model(self, config):
        with tempfile.TemporaryDirectory(prefix="ordivon-resource-generation-") as directory:
            scratch = Path(directory)
            (scratch / f"{MODEL}.tla").write_text(self.source, encoding="utf-8")
            (scratch / "case.cfg").write_text(config, encoding="utf-8")
            return subprocess.run(
                ["java", "-Xmx256m", "-XX:+UseSerialGC", "-cp", str(self.jar),
                 "tlc2.TLC", "-workers", "1", "-config", "case.cfg", f"{MODEL}.tla"],
                cwd=scratch, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True, timeout=40, check=False,
            )

    def require_trace(self, config, invariant):
        result = self.run_model(config)
        self.assertEqual(result.returncode, 12, result.stdout)
        self.assertIn(f"Error: Invariant {invariant} is violated.", result.stdout)
        self.assertRegex(result.stdout, r"(?m)^State [1-9][0-9]*:")
        print(f"TLC exact counterexample: {invariant}", flush=True)
        return result.stdout

    def mutant(self, policy, invariant):
        return self.require_trace(
            f'SPECIFICATION Spec\nCONSTANTS\nPolicy = "{policy}"\nMaxRevision = 3\n'
            f'INVARIANTS TypeOK {invariant}\nCHECK_DEADLOCK FALSE\n',
            invariant,
        )

    def test_safe_three_revisions(self):
        result = self.run_model(self.safe_config)
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertIn("Model checking completed. No error has been found.", result.stdout)
        census = re.search(r"\d+ states generated, \d+ distinct states found", result.stdout)
        self.assertIsNotNone(census, result.stdout)
        print("TLC bounded safe:", census.group(0), flush=True)

    def test_actual_content_aba_is_reachable(self):
        trace = self.require_trace(self.safe_config + "\nINVARIANT NeverReturnedToA\n",
                                   "NeverReturnedToA")
        self.assertIn('nativeContent = "B"', trace)

    def test_positive_settlement_after_issuer_crash_is_reachable(self):
        trace = self.require_trace(self.safe_config + "\nINVARIANT NeverRecoveredAfterCrash\n",
                                   "NeverRecoveredAfterCrash")
        self.assertIn("issuerAlive = FALSE", trace)
        self.assertIn('phase = "completed"', trace)

    def test_pointer_only_mutant(self):
        trace = self.mutant("ignoreRevision", "NoStaleAdmission")
        self.assertIn('nativeContent = "B"', trace)
        final = trace.rsplit("State ", 1)[-1]
        self.assertIn('bad = {"stale"}', final)
        self.assertIn("revision = 3", final)
        self.assertIn('activeContent = "A"', final)

    def test_pending_supersession_mutant(self):
        self.mutant("supersede", "NoPendingSupersession")

    def test_wrong_effect_settlement_mutant(self):
        self.mutant("wrongEffect", "NoForeignSettlement")

    def test_issued_is_terminal_mutant(self):
        trace = self.mutant("earlySettlement", "NoEarlySettlement")
        self.assertIn('phase = "issued"', trace)

    def test_unbound_receipt_mutant(self):
        self.mutant("forgedReceipt", "NoForgedReceipt")


if __name__ == "__main__":
    unittest.main()
