"""Bounded cross-DB claim contract. Not installed API proof."""
from pathlib import Path
import json
import os
import subprocess
import tempfile

import unittest
ROOT = Path(__file__).resolve().parents[2]
MODEL = ROOT / "formal" / "WorkspaceCrossDatabaseClaimR1.tla"
RUNNER = ROOT / "scripts" / "tla-formal"

class WorkspaceCrossDatabaseClaimFormalTests(unittest.TestCase):
    def test_runtime_claim_and_close_are_separate_from_harness_state(self) -> None:
        text = MODEL.read_text()
        for name in ("NativeReserve(r,w) ==", "NativeActivate(r) ==",
                     "NativeRelease(r) ==", "NativeClose ==",
                     "ClosedHasNoOutstandingPins ==",
                     "UnreleasedGrantsHeld ==", "StableEligibleEventuallyClosed ==",
                     "IndependentRecipientObserve(r, output, subject) ==",
                     "ReleaseRequiresIndependentRecipientAck ==",
                     "ClosedHasIndependentRecipientAcceptance =="):
            self.assertTrue(name in text)
        self.assertTrue("latest_resolution" not in text[text.index("Eligible =="):text.index("NativeClose ==")])

    def test_tlc_counterexamples_are_wired_into_native_runner(self) -> None:
        text = MODEL.read_text()
        runner = RUNNER.read_text()
        scenarios = {"reachability":"ClosedUnreachable",
                     "unsafe-close":"ClosedHasNoOutstandingPins",
                     "unsafe-late":"ClosedHasNoOutstandingPins",
                     "unsafe-grant":"UnreleasedGrantsHeld",
                     "recipient-reachability":"IndependentAcceptedReleaseUnreachable",
                     "unsafe-selfcert-release":"ReleaseRequiresIndependentRecipientAck",
                     "unsafe-selfcert-close":"ClosedHasIndependentRecipientAcceptance"}
        for label, invariant in scenarios.items():
            path = ROOT / "formal" / ("WorkspaceCrossDatabaseClaimR1."+label+".cfg")
            self.assertTrue("INVARIANT "+invariant in path.read_text())
        for phrase in ("UnsafeCrossDatabaseClose ==",
                       "UnsafeLateForeignClaim(r) ==",
                       "UnsafeUnqualifiedGrant(r) ==",
                       "UnsafeSelfCertifiedRelease(r) ==",
                       "UnsafeCloseAfterFakeAck =="):
            self.assertTrue(phrase in text)
        for phrase in ("check-workspace-crossdb)", "falsify-workspace-crossdb)",
                       "Workspace cross-DB $label counterexample PASS"):
            self.assertTrue(phrase in runner)

    def test_recipient_identity_and_complete_census_gate_is_nonvacuous_and_falsifiable(self) -> None:
        """A same-Run receipt for the wrong Attempt cannot release the Claim."""
        lock = json.loads((ROOT / "formal/toolchain.lock.json").read_text())
        jar = Path(os.environ.get("ORDIVON_TLA_TOOLS_JAR", ROOT / lock["cacheRelativePath"]))
        if not jar.is_file() and "ORDIVON_TLA_TOOLS_JAR" not in os.environ:
            self.skipTest("pinned TLC not materialized; run scripts/tla-formal bootstrap")
        subprocess.run(["bash", str(RUNNER), "verify"], cwd=ROOT, check=True, timeout=20)
        source = MODEL.read_text()

        def run(text, invariant):
            with tempfile.TemporaryDirectory(prefix="ordivon-claim-subject-") as directory:
                scratch = Path(directory)
                (scratch / MODEL.name).write_text(text, encoding="utf-8")
                (scratch / "case.cfg").write_text(
                    f"SPECIFICATION SafeSpec\nINVARIANT {invariant}\nCHECK_DEADLOCK FALSE\n",
                    encoding="utf-8",
                )
                return subprocess.run(
                    ["java", "-Xmx256m", "-XX:+UseSerialGC", "-cp", str(jar.resolve()),
                     "tlc2.TLC", "-workers", "1", "-config", "case.cfg", MODEL.name],
                    cwd=scratch, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                    timeout=120, check=False,
                )

        # A wrong-subject observation really occurs on a valid execution path.
        foreign = run(source, "ForeignRecipientObservationUnreachable")
        self.assertTrue(foreign.returncode == 12, foreign.stdout)
        self.assertTrue("Invariant ForeignRecipientObservationUnreachable is violated." in foreign.stdout)

        # The original positive recipient-release reachability control still applies.
        positive = run(source, "IndependentAcceptedReleaseUnreachable")
        self.assertTrue(positive.returncode == 12, positive.stdout)
        self.assertTrue("Invariant IndependentAcceptedReleaseUnreachable is violated." in positive.stdout)

        # Change only the release guard: a same-Run receipt for a wrong Attempt
        # is independently authenticated but does not refer to the original effect.
        start, end = source.index("NativeRelease(r) =="), source.index("AbortNeverIssuedReservation(r) ==")
        block = source[start:end]
        guard = "    /\\ r \\in RecipientAccepted\n"
        self.assertTrue(block.count(guard) == 1)
        mutated = source[:start] + block.replace(
            guard, '    /\\ (r \\in RecipientAccepted \\/ <<r,"first","wrongAttempt">> \\in recipientWitnesses)\n'
        ) + source[end:]
        bad = run(mutated, "ReleaseRequiresExactRecipientSubject")
        self.assertTrue(bad.returncode == 12, bad.stdout)
        self.assertTrue("Invariant ReleaseRequiresExactRecipientSubject is violated." in bad.stdout)
        final = bad.stdout.rsplit("State ", 1)[-1]
        self.assertTrue("wrongAttempt" in final, bad.stdout)
        self.assertTrue("released" in final, bad.stdout)

        # A complete empty Run and a complete two-output Run both release.
        for invariant in ("CompleteEmptyReleaseUnreachable",
                          "CompleteTwoOutputReleaseUnreachable",
                          "PartialReceiptUnreachable",
                          "UnknownEmptyCensusUnreachable"):
            witness = run(source, invariant)
            self.assertTrue(witness.returncode == 12, witness.stdout)
            self.assertTrue(f"Invariant {invariant} is violated." in witness.stdout)

        # Mutant: one exact receipt is treated as accepting all required outputs.
        # Hold original finalization, delivery and native quiescence fixed.
        partial = source[:start] + block.replace(
            guard, '    /\\ (r \\in RecipientAccepted \\/ (r \\in censusComplete /\\ Cardinality(AcceptedOutputs(r)) = 1))\n'
        ) + source[end:]
        bad_partial = run(partial, "ReleaseRequiresExactRecipientSubject")
        self.assertTrue(bad_partial.returncode == 12, bad_partial.stdout)
        self.assertTrue("Invariant ReleaseRequiresExactRecipientSubject is violated." in bad_partial.stdout)
        final = bad_partial.stdout.rsplit("State ", 1)[-1]
        self.assertTrue('<<"runA",' in final and '"exact"' in final, bad_partial.stdout)
        self.assertTrue('"released"' in final, bad_partial.stdout)

        # Mutant: an absent census is treated as the empty required-output set.
        # The negative is scoped to the actually empty Run so the old identity
        # invariant cannot hide the independent census-completeness failure.
        vacuous = source[:start] + block.replace(
            guard, '    /\\ (r \\in RecipientAccepted \\/ RequiredOutputs(r) = {})\n'
        ) + source[end:]
        bad_empty = run(vacuous, "ReleaseRequiresCompleteOriginalCensus")
        self.assertTrue(bad_empty.returncode == 12, bad_empty.stdout)
        self.assertTrue("Invariant ReleaseRequiresCompleteOriginalCensus is violated." in bad_empty.stdout)
        final = bad_empty.stdout.rsplit("State ", 1)[-1]
        self.assertTrue("censusComplete = {}" in final, bad_empty.stdout)
        self.assertTrue('"released"' in final, bad_empty.stdout)

        # Refinement counterexample: publishing an empty output census before
        # the original delivery record falsely projects an accepted Run.
        begin = source.index("QualifyCompleteOutputCensus(r) ==")
        finish = source.index("NativeRelease(r) ==")
        qualifier = source[begin:finish]
        delivered_guard = "    /\\ r \\in delivered\n"
        self.assertTrue(qualifier.count(delivered_guard) == 1)
        premature = source[:begin] + qualifier.replace(
            delivered_guard, "    /\\ r \\in published\n", 1
        ) + source[finish:]
        bad_order = run(premature, "AcceptanceRequiresDelivery")
        self.assertTrue(bad_order.returncode == 12, bad_order.stdout)
        self.assertTrue("Invariant AcceptanceRequiresDelivery is violated." in bad_order.stdout)
        final = bad_order.stdout.rsplit("State ", 1)[-1]
        self.assertTrue('censusComplete = {"runB"}' in final, bad_order.stdout)
        self.assertTrue("delivered = {}" in final, bad_order.stdout)
