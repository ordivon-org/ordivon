#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from foundry.agent_surfaces import (  # noqa: E402
    HardenedPersistentMemoryAgent,
    HardenedToolTrustAgent,
    LexicalSyntheticMonitor,
    MonitorCase,
    StructuralSyntheticMonitor,
    VulnerablePersistentMemoryAgent,
    VulnerableToolTrustAgent,
    find_monitor_blind_spots,
    run_memory_poisoning_campaign,
    run_tool_poisoning_campaign,
)


def finding(value):
    return value.to_dict() if value else None


def main() -> None:
    monitor_cases = [
        MonitorCase("overt", True, True, "overt"),
        MonitorCase("covert", False, True, "structural"),
        MonitorCase("benign", False, False, "benign"),
    ]
    report = {
        "schema": "ordivon.ai-redteam.agent-surfaces.synthetic-r1",
        "memory": {
            "vulnerable": finding(run_memory_poisoning_campaign(VulnerablePersistentMemoryAgent())),
            "hardened": finding(run_memory_poisoning_campaign(HardenedPersistentMemoryAgent())),
        },
        "toolTrust": {
            "vulnerable": finding(run_tool_poisoning_campaign(VulnerableToolTrustAgent)),
            "hardened": finding(run_tool_poisoning_campaign(HardenedToolTrustAgent)),
        },
        "monitor": {
            "lexicalBlindSpots": [f.to_dict() for f in find_monitor_blind_spots(LexicalSyntheticMonitor(), monitor_cases)],
            "structuralBlindSpots": [f.to_dict() for f in find_monitor_blind_spots(StructuralSyntheticMonitor(), monitor_cases)],
        },
    }
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
