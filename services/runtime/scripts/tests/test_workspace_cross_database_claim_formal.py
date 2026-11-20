"""Bounded cross-DB claim contract. Not installed API proof."""
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
MODEL = ROOT / "formal" / "WorkspaceCrossDatabaseClaimR1.tla"
RUNNER = ROOT / "scripts" / "tla-formal"

def test_runtime_claim_and_close_are_separate_from_harness_state():
    text = MODEL.read_text()
    for name in ("NativeReserve(r,w) ==", "NativeActivate(r) ==",
                 "IndependentRecipientAccept(r) ==",
                 "NativeRelease(r) ==", "NativeClose ==",
                 "ClosedHasNoOutstandingPins ==",
                 "UnreleasedGrantsHeld ==", "StableEligibleEventuallyClosed ==",
                 "ReleaseRequiresIndependentRecipientAck ==",
                 "ClosedHasIndependentRecipientAcceptance =="):
        assert name in text
    assert "latest_resolution" not in text[text.index("Eligible =="):text.index("NativeClose ==")]
    # The finalizer's claimed delivery and the original recipient's actual
    # acceptance MUST be separate: an arbitrary accepted=true or callback
    # must not authorize NativeRelease or NativeClose.
    assert "r \\in recipientAccepted" in text[
        text.index("NativeRelease(r) =="):text.index("AbortNeverIssuedReservation(r) ==")
    ]
    assert "published \\subseteq recipientAccepted" in text[
        text.index("Eligible =="):text.index("NativeClose ==")
    ]
    assert "recipientAccepted' = recipientAccepted \\cup {r}" in text[
        text.index("IndependentRecipientAccept(r) =="):text.index("NativeRelease(r) ==")
    ]

def test_tlc_counterexamples_are_wired_into_native_runner():
    text = MODEL.read_text()
    runner = RUNNER.read_text()
    # Structural consumer sanity for the SAME configs invoked by TLC in the
    # mature tla-formal script; these assertions do not replace TLC itself.
    scenarios = {
        "reachability": "ClosedUnreachable",
        "original-reachability": "NoOriginalClaimEver",
        "recipient-reachability": "IndependentAcceptedReleaseUnreachable",
        "legacy-unclaimed-close": "LegacyUnclaimedRunPreserved",
        "unsafe-close": "ClosedHasNoOutstandingPins",
        "unsafe-late": "ClosedHasNoOutstandingPins",
        "unsafe-grant": "UnreleasedGrantsHeld",
        "unsafe-adoption": "ClaimBoundToOriginal",
        "unsafe-known-rebind": "ClaimBoundToOriginal",
        "unsafe-caller-release": "ReleaseRequiresOriginalFinalization",
        "unsafe-caller-close": "ClosedHasNoPrematurelyReleasedConsumers",
        "unsafe-selfcert-release": "ReleaseRequiresIndependentRecipientAck",
        "unsafe-selfcert-close": "ClosedHasIndependentRecipientAcceptance",
    }
    for label, invariant in scenarios.items():
        path = ROOT / "formal" / ("WorkspaceCrossDatabaseClaimR1."+label+".cfg")
        assert "INVARIANT "+invariant in path.read_text()
        assert label in runner
        assert "invariant="+invariant in runner
    for phrase in ("UnsafeCrossDatabaseClose ==",
                   "UnsafeLateForeignClaim(r) ==",
                   "UnsafeUnqualifiedGrant(r) =="):
        assert phrase in text
    for phrase in ("check-workspace-crossdb)", "falsify-workspace-crossdb)",
                   "Workspace cross-DB $label counterexample PASS"):
        assert phrase in runner
