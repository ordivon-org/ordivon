from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_fmea_fta_top_events_have_existing_controls_and_tests():
    doc = json.loads((ROOT / "planning/fmea-fta-r1.json").read_text())
    assert doc["standing"] == "ACTIVE_R1"
    ids = {row["id"] for row in doc["topEvents"]}
    assert {
        "false-production-write-admission",
        "blind-resend-after-ambiguous-effect",
        "terminal-accounting-resurrection",
        "risk-budget-inference",
        "historical-evidence-mutation",
        "candidate-framework-becomes-owner",
    } <= ids
    for row in doc["topEvents"]:
        assert row["controls"]
        assert row["tests"]
        for name in row["tests"]:
            assert (ROOT / "tests" / name).is_file()
