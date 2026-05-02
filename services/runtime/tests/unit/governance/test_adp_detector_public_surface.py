"""ADP-3: PV public-surface detection tests."""

from __future__ import annotations
import json, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
DETECTOR = ROOT / "scripts" / "detect_agentic_patterns.py"
PFX = ROOT / "tests" / "fixtures" / "adp_detector" / "public_surface"


def _findings(path: str) -> list[dict]:
    r = subprocess.run(
        [sys.executable, str(DETECTOR), path, "--json"], capture_output=True, text=True, timeout=10, cwd=str(ROOT)
    )
    return json.loads(r.stdout).get("findings", [])


class TestPublicSurfaceDetection:
    def test_safe_pv_not_flagged(self):
        f = _findings(str(PFX / "safe-pv-doc.md"))
        blocking = [x for x in f if x["severity"] == "blocking"]
        assert len(blocking) == 0, f"Safe PV has blocking: {blocking}"

    def test_unsafe_release_flagged(self):
        f = _findings(str(PFX / "unsafe-pv-doc.md"))
        assert any(x["pattern_id"] == "ADP3-PV-RELEASE" for x in f), "Release overclaim not flagged"

    def test_unsafe_ready_flagged(self):
        f = _findings(str(PFX / "unsafe-pv-doc.md"))
        assert any(x["pattern_id"] == "ADP3-PV-READY" for x in f), "READY approval not flagged"

    def test_unsafe_wedge_collapse_flagged(self):
        f = _findings(str(PFX / "unsafe-pv-doc.md"))
        assert any(x["pattern_id"] == "ADP3-PV-WEDGE" for x in f), "Wedge collapse not flagged"
