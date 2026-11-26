"""Required named TLC controls for the bounded Root bundle transition model.

The existing tla-formal falsify-root-bundle route calls this module. A
missing or unqualified toolchain fails rather than silently skipping tests.
All mutations and explicit recovery seeds are confined to temporary models.
The witnesses establish abstract recoverability, not fairness or deployment.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
import re
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
FORMAL = ROOT / "formal"
MODEL = "RootBundleTransitionR1"
JAR_ENV = "ORDIVON_TLA_TOOLS_JAR"
SPEC_MARKER = r"Spec == Init /\ [][Next]_vars"
RECOVERY_EDGE = r"    \/ ReacquireRestoredOldResumeLock" + "\n"

# These predicates observe the actual model. Exact seeds are checked for
# reachability from Init before the separately seeded path controls.
OBSERVERS = r'''
AbortedResumed == journal = "abort_terminal" /\ pgAllowed /\ timerOn /\ ~rootLock /\ live = Old
NeverAbortResumed == ~AbortedResumed
NeverNewConsumerAfterResume == ~(QualifiedNewRootIsReachable /\ (activeProcess = "new" \/ pendingEffect))
NeverOldProcessAfterAbort == ~(AbortedResumed /\ activeProcess = "old")
NeverOldEffectAfterAbort == ~(AbortedResumed /\ pendingEffect)
NeverOldProcessAfterRollback == ~(QualifiedRollbackIsReachable /\ activeProcess = "old")
NeverOldEffectAfterRollback == ~(QualifiedRollbackIsReachable /\ pendingEffect)
NeverNewRoot == ~QualifiedNewRootIsReachable
NeverRollback == ~QualifiedRollbackIsReachable
NeverPostSwapCrashRecovery == ~RecoveryAfterRootCrashIsReachable
OverbroadOldRollbackInvariant ==
    (live = Old /\ journal \in {"rollback_prepared", "rolledback"}) => ~pendingEffect
GapSeed(j,pending) ==
    /\ journal = j /\ live = Old /\ spare = New
    /\ pgAllowed = TRUE /\ timerOn = FALSE /\ rootLock = FALSE /\ rootAlive = TRUE
    /\ unitQualified = TRUE /\ activeProcess = "none" /\ pendingEffect = pending
    /\ postSwapCrashSeen = FALSE
AbortSeed == GapSeed("abort_terminal", FALSE)
RollbackSeed == GapSeed("rolledback", FALSE)
AbortPendingSeed == GapSeed("abort_terminal", TRUE)
RollbackPendingSeed == GapSeed("rolledback", TRUE)
NeverAbortSeed == ~AbortSeed
NeverRollbackSeed == ~RollbackSeed
NeverAbortPendingSeed == ~AbortPendingSeed
NeverRollbackPendingSeed == ~RollbackPendingSeed
NeverRecoveredAbort == ~AbortedResumed
NeverRecoveredRollback == ~QualifiedRollbackIsReachable
'''


class RootBundleTransitionModelTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        lock = json.loads((FORMAL / "toolchain.lock.json").read_text(encoding="utf-8"))
        jar = Path(os.environ[JAR_ENV]) if JAR_ENV in os.environ else ROOT / lock["cacheRelativePath"]
        subprocess.run(
            ["bash", str(ROOT / "scripts/tla-formal"), "verify"],
            cwd=ROOT, check=True, timeout=20,
        )
        cls.jar = jar.resolve()
        cls.source = (FORMAL / f"{MODEL}.tla").read_text(encoding="utf-8")
        if cls.source.count(SPEC_MARKER) != 1:
            raise RuntimeError("Root model observation marker drift")
        cls.observed = cls.source.replace(SPEC_MARKER, OBSERVERS + "\n" + SPEC_MARKER, 1)

    def run_model(self, source: str, config: str):
        with tempfile.TemporaryDirectory(prefix="ordivon-root-bundle-model-") as directory:
            scratch = Path(directory)
            (scratch / f"{MODEL}.tla").write_text(source, encoding="utf-8")
            (scratch / "case.cfg").write_text(config, encoding="utf-8")
            return subprocess.run(
                ["java", "-Xmx256m", "-XX:+UseSerialGC", "-cp", str(self.jar),
                 "tlc2.TLC", "-workers", "1", "-config", "case.cfg", f"{MODEL}.tla"],
                cwd=scratch, text=True, stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT, timeout=70, check=False,
            )

    def check_case(self, label, source, init_or_spec, invariant, expected, required_actions=()):
        config = (
            init_or_spec + "\nINVARIANT TypeOK\nINVARIANT " + invariant
            + "\nCHECK_DEADLOCK FALSE\n"
        )
        result = self.run_model(source, config)
        self.assertEqual(result.returncode, expected, result.stdout)
        if expected == 12:
            self.assertIn("Error: Invariant " + invariant + " is violated.", result.stdout)
            self.assertRegex(result.stdout, r"(?m)^State [1-9][0-9]*:")
            for action in required_actions:
                self.assertRegex(
                    result.stdout, r"(?m)^State [0-9]+: <" + re.escape(action) + r" ",
                    f"{label}: missing {action} trace\n{result.stdout}",
                )
            print(f"Root bundle {label} named TLC trace PASS", flush=True)
        else:
            self.assertEqual(expected, 0)
            self.assertIn("Model checking completed. No error has been found.", result.stdout)
            print(f"Root bundle {label} disconnected reachability control PASS", flush=True)

    def test_original_unsafe_transitions(self):
        for label, spec, invariant, action in (
            ("old-inflight", "UnsafeOldProcessSpec",
             "NoOldInterpreterDuringNewPackage", "UnsafeSwapWhileOldInterpreter"),
            ("new-inflight-rollback", "UnsafeRollbackProcessSpec",
             "NoNewInterpreterDuringRolledBackPackage", "UnsafeRollbackWhileNewInterpreter"),
            ("premature-release", "UnsafeEarlyResumeSpec",
             "NoReleaseAdmissionDuringAmbiguousExchange", "UnsafeResumeWithOnlyPreparedJournal"),
            ("partial-file-copy", "UnsafeFileCopySpec",
             "NoPartialRootBundle", "UnsafeCopySingleRootFile"),
        ):
            with self.subTest(case=label):
                self.check_case(label, self.source, "SPECIFICATION " + spec,
                                invariant, 12, (action,))

    def test_original_and_restored_consumer_reachability(self):
        cases = (
            ("legitimate-install", "NeverNewRoot", ()),
            ("legitimate-rollback", "NeverRollback", ("AtomicRollback",)),
            ("postswap-crash-recovery", "NeverPostSwapCrashRecovery",
             ("AtomicBundleExchange", "CrashRootController", "ReopenRootController",
              "RecoverExchangedBytes")),
            ("abort-resume", "NeverAbortResumed",
             ("AbortBeforeExchange", "ResumeAbortedOldRelease")),
            ("new-consumer", "NeverNewConsumerAfterResume", ()),
            ("old-process-abort", "NeverOldProcessAfterAbort",
             ("AbortBeforeExchange", "StartOldProcess")),
            ("old-effect-abort", "NeverOldEffectAfterAbort",
             ("AbortBeforeExchange", "AdmitOldEffect")),
            ("old-process-rollback", "NeverOldProcessAfterRollback",
             ("AtomicRollback", "StartOldProcess")),
            ("old-effect-rollback", "NeverOldEffectAfterRollback",
             ("AtomicRollback", "AdmitOldEffect")),
            ("old-overbroad-invariant", "OverbroadOldRollbackInvariant",
             ("ResumeRolledBackOld", "AdmitOldEffect")),
        )
        for label, invariant, actions in cases:
            with self.subTest(case=label):
                self.check_case(label, self.observed, "SPECIFICATION Spec",
                                invariant, 12, actions)

    def test_exact_crash_seed_reachability(self):
        for seed, resume, pending in (
            ("AbortSeed", "ResumeAbortedOldRelease", False),
            ("RollbackSeed", "ResumeRolledBackOld", False),
            ("AbortPendingSeed", "ResumeAbortedOldRelease", True),
            ("RollbackPendingSeed", "ResumeRolledBackOld", True),
        ):
            with self.subTest(seed=seed):
                actions = (resume, "CrashRootController", "ReopenRootController")
                if pending:
                    actions += ("AdmitOldEffect",)
                self.check_case("reachable-" + seed, self.observed, "SPECIFICATION Spec",
                                "Never" + seed, 12, actions)

    def test_crash_seed_restores_real_consumer(self):
        cases = (
            ("AbortSeed", "NeverOldProcessAfterAbort", "StartOldProcess"),
            ("AbortSeed", "NeverOldEffectAfterAbort", "AdmitOldEffect"),
            ("RollbackSeed", "NeverOldProcessAfterRollback", "StartOldProcess"),
            ("RollbackSeed", "NeverOldEffectAfterRollback", "AdmitOldEffect"),
            ("AbortPendingSeed", "NeverOldProcessAfterAbort", "StartOldProcess"),
            ("RollbackPendingSeed", "NeverOldProcessAfterRollback", "StartOldProcess"),
        )
        for seed, invariant, action in cases:
            with self.subTest(seed=seed, invariant=invariant):
                self.check_case(
                    seed + "-" + invariant, self.observed, "INIT " + seed + "\nNEXT Next",
                    invariant, 12,
                    ("ReacquireRestoredOldResumeLock", "ResumeTimer",
                     "ReleaseOriginalOperatorLock", action),
                )

    def test_disconnected_recovery_edge_is_not_a_recovery_path(self):
        # Merely retaining the action definition is insufficient. Remove
        # exactly its occurrence in Next, not the guard or action body.
        self.assertEqual(self.observed.count(RECOVERY_EDGE), 1)
        mutant = self.observed.replace(RECOVERY_EDGE, "", 1)
        for seed, invariant in (
            ("AbortSeed", "NeverRecoveredAbort"),
            ("RollbackSeed", "NeverRecoveredRollback"),
            ("AbortPendingSeed", "NeverRecoveredAbort"),
            ("RollbackPendingSeed", "NeverRecoveredRollback"),
        ):
            with self.subTest(seed=seed):
                self.check_case(
                    "disconnected-" + seed, mutant, "INIT " + seed + "\nNEXT Next",
                    invariant, 0,
                )


if __name__ == "__main__":
    unittest.main()
