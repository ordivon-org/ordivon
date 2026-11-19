"""Bounded cross-DB claim contract. Not installed API proof."""
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
MODEL = ROOT / "formal" / "WorkspaceCrossDatabaseClaimR1.tla"
RUNNER = ROOT / "scripts" / "tla-formal"

def test_runtime_claim_and_close_are_separate_from_harness_state():
    text = MODEL.read_text()
    for name in ("NativeReserve(r) ==", "NativeActivate(r) ==",
                 "NativeRelease(r) ==", "NativeClose ==",
                 "ClosedHasNoOutstandingPins ==",
                 "UnreleasedGrantsHeld ==", "StableEligibleEventuallyClosed =="):
        assert name in text
    assert "latest_resolution" not in text[text.index("Eligible =="):text.index("NativeClose ==")]

def test_tlc_counterexamples_are_wired_into_native_runner():
    text = MODEL.read_text()
    runner = RUNNER.read_text()
    scenarios = {"reachability":"ClosedUnreachable",
                 "unsafe-close":"ClosedHasNoOutstandingPins",
                 "unsafe-late":"ClosedHasNoOutstandingPins",
                 "unsafe-grant":"UnreleasedGrantsHeld"}
    for label, invariant in scenarios.items():
        path = ROOT / "formal" / ("WorkspaceCrossDatabaseClaimR1."+label+".cfg")
        assert "INVARIANT "+invariant in path.read_text()
    for phrase in ("UnsafeCrossDatabaseClose ==",
                   "UnsafeLateForeignClaim(r) ==",
                   "UnsafeUnqualifiedGrant(r) =="):
        assert phrase in text
    for phrase in ("check-workspace-crossdb)", "falsify-workspace-crossdb)",
                   "Workspace cross-DB $label counterexample PASS"):
        assert phrase in runner
