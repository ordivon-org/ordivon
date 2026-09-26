#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from foundry import HardenedMockTarget, ThreatModel, VulnerableMockTarget  # noqa: E402
from foundry.fuzzing import discovery_frontier_by_budget, run_fuzz_campaign  # noqa: E402


def main() -> None:
    threat = ThreatModel(
        threat_model_id="tm-abstract-fuzz-r1",
        attacker_knowledge="gray-box",
        access="synthetic-typed-operations",
        adaptive=True,
        state_scope="run",
        success_object="invariant-violation",
    )
    vulnerable, vulnerable_findings = run_fuzz_campaign(
        target_factory=VulnerableMockTarget,
        threat_model=threat,
        seed=17,
        budget=32,
    )
    hardened, hardened_findings = run_fuzz_campaign(
        target_factory=HardenedMockTarget,
        threat_model=threat,
        seed=17,
        budget=32,
    )
    report = {
        "schema": "ordivon.ai-redteam.abstract-fuzz.r1",
        "vulnerable": vulnerable.to_dict(),
        "vulnerableFindings": [finding.to_dict() for finding in vulnerable_findings],
        "hardened": hardened.to_dict(),
        "hardenedFindings": [finding.to_dict() for finding in hardened_findings],
        "discoveryFrontier": {
            str(budget): list(families)
            for budget, families in discovery_frontier_by_budget(
                target_factory=VulnerableMockTarget,
                threat_model=threat,
                seed=17,
                budgets=(1, 2, 4, 8, 16, 32),
            ).items()
        },
    }
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
