#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from foundry.providers import (  # noqa: E402
    AgentDojoRunAdapter,
    GarakReportAdapter,
    InspectEvalLogAdapter,
    PyritScenarioResultsAdapter,
    discovery_frontier,
    load_fixture,
)


def main() -> None:
    pyrit_path = ROOT / "fixtures/pyrit/scenario-results-attacks.synthetic.json"
    garak_path = ROOT / "fixtures/garak/report.synthetic.jsonl"
    agentdojo_path = ROOT / "fixtures/agentdojo/run.synthetic.json"
    inspect_path = ROOT / "fixtures/inspect/eval-log.synthetic.json"

    pyrit = PyritScenarioResultsAdapter(provider_version="documented-surface-2026-09-26").parse_bytes(
        load_fixture(pyrit_path),
        "fixtures/pyrit/scenario-results-attacks.synthetic.json",
        scenario_result_id="fixture-pyrit-scenario-r1",
        target_id="synthetic:mock-agent-r1",
    )
    garak = GarakReportAdapter(provider_version="documented-surface-2026-09-26").parse_bytes(
        load_fixture(garak_path),
        "fixtures/garak/report.synthetic.jsonl",
        provider_run_id="fixture-garak-run-r1",
    )
    agentdojo = AgentDojoRunAdapter(provider_version="documented-surface-2026-09-26").parse_bytes(
        load_fixture(agentdojo_path),
        "fixtures/agentdojo/run.synthetic.json",
    )
    inspect_eval = InspectEvalLogAdapter(provider_version="documented-surface-2026-09-26").parse_bytes(
        load_fixture(inspect_path),
        "fixtures/inspect/eval-log.synthetic.json",
    )

    report = {
        "schema": "ordivon.ai-redteam.provider-fixture-replay.r1",
        "pyrit": [projection.to_dict() for projection in pyrit],
        "garak": [projection.to_dict() for projection in garak],
        "agentdojo": agentdojo.to_dict(),
        "inspect": inspect_eval.to_dict(),
        "discoveryFrontier": {
            "pyritBudget2": discovery_frontier(pyrit, 2),
            "garakBudget2": discovery_frontier(garak, 2),
        },
    }
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
