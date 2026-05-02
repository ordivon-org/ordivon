"""ADP-3: Registry-aware detection tests."""

from __future__ import annotations
import json, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
DETECTOR = ROOT / "scripts" / "detect_agentic_patterns.py"
RFX = ROOT / "tests" / "fixtures" / "adp_detector" / "registry"


def _findings(path: str) -> list[dict]:
    r = subprocess.run(
        [sys.executable, str(DETECTOR), path, "--json"], capture_output=True, text=True, timeout=10, cwd=str(ROOT)
    )
    return json.loads(r.stdout).get("findings", [])


class TestRegistryDetection:
    def test_safe_registry_not_blocking(self):
        f = _findings(str(RFX / "safe-registry.jsonl"))
        blocking = [x for x in f if x["severity"] == "blocking"]
        assert len(blocking) == 0, f"Safe registry has blocking: {blocking}"

    def test_unsafe_superseded_flagged(self):
        f = _findings(str(RFX / "unsafe-registry.jsonl"))
        assert any(x["pattern_id"] == "ADP3-DG-SUPERSEDED" for x in f), "Superseded not flagged"

    def test_unsafe_receipt_authority_flagged(self):
        f = _findings(str(RFX / "unsafe-registry.jsonl"))
        assert any(x["pattern_id"] == "ADP3-DG-RECEIPT-AUTH" for x in f), "Receipt authority not flagged"

    def test_unsafe_ai_read_archived_flagged(self):
        f = _findings(str(RFX / "unsafe-registry.jsonl"))
        assert any(x["pattern_id"] == "ADP3-DG-AI-STALE" for x in f), "AI read archived not flagged"
