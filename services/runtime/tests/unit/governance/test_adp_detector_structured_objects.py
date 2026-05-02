"""ADP-3: Structure-aware detection tests for TaskPlan/ReviewRecord."""

from __future__ import annotations
import json, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
DETECTOR = ROOT / "scripts" / "detect_agentic_patterns.py"
SFX = ROOT / "tests" / "fixtures" / "adp_detector" / "structured"


def _findings(path: str) -> list[dict]:
    r = subprocess.run(
        [sys.executable, str(DETECTOR), path, "--json"], capture_output=True, text=True, timeout=10, cwd=str(ROOT)
    )
    return json.loads(r.stdout).get("findings", [])


class TestTaskPlanDetection:
    def test_safe_c0_not_flagged(self):
        f = _findings(str(SFX / "safe-taskplan-c0.json"))
        assert len(f) == 0, f"Safe C0 flagged: {f}"

    def test_unsafe_exec_flagged(self):
        f = _findings(str(SFX / "unsafe-taskplan-exec.json"))
        assert any(x["pattern_id"] == "ADP3-PLAN-EXEC" for x in f), f"Not flagged: {f}"

    def test_unsafe_c4_flagged(self):
        f = _findings(str(SFX / "unsafe-taskplan-c4.json"))
        patterns = {x["pattern_id"] for x in f}
        assert "ADP3-PLAN-C4" in patterns, f"C4 not flagged: {f}"


class TestReviewRecordDetection:
    def test_safe_comment_not_flagged(self):
        f = _findings(str(SFX / "safe-review-comment.json"))
        assert len(f) == 0, f"Safe comment flagged: {f}"

    def test_unsafe_detector_flagged(self):
        f = _findings(str(SFX / "unsafe-review-detector-approval.json"))
        assert any(x["pattern_id"].startswith("ADP3-REVIEW") for x in f), f"Not flagged: {f}"

    def test_unsafe_cr_binding_flagged(self):
        f = _findings(str(SFX / "unsafe-review-cr-binding.json"))
        assert any(x["pattern_id"] == "ADP3-CR-BINDING" for x in f), f"CR binding not flagged: {f}"
