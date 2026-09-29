from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = ROOT.parents[2]
for path in (ROOT, REPO_ROOT / "studies" / "security" / "ai-redteam-foundry-r1", REPO_ROOT / "studies" / "security" / "ai-redteam-foundry-r8"):
    sys.path.insert(0, str(path))

from foundry.providers import ProviderArtifactRef  # noqa: E402
from foundry_r8 import SearchCandidateRef, SearchResultRef  # noqa: E402
from foundry_r9 import FamilyAssignment, FamilyHypothesis, build_family_ledger, discovery_frontier  # noqa: E402

D = lambda c: "sha256:" + c * 64
RUN = D("a")


def make_result(sequence: int, surface: str, positive: bool | None, observed: bool) -> SearchResultRef:
    digit = format(sequence, "x")
    artifact = ProviderArtifactRef("fixture-provider", "v1", "fixture.json", D(digit), 100 + sequence, f"fixture-{sequence}.json")
    candidate = SearchCandidateRef(RUN, sequence, "fixture-provider", "v1", "run:r9", f"case:{sequence}", surface, "target:r9", D(format(sequence + 3, "x")), D(format(sequence + 7, "x")), artifact)
    return SearchResultRef(candidate, "judge:fixture", "provider-signal", positive, 0.9 if positive else 0.1 if positive is False else None, D("f") if observed else None, f"effect:{sequence}" if observed else None, D("e") if observed else None)


results = (
    make_result(1, "synthetic_indirect_injection", True, True),
    make_result(2, "synthetic_trajectory_shaping", True, False),
    make_result(3, "synthetic_monitor_probe", None, False),
)
h1 = FamilyHypothesis("hypothesis:provenance", "instruction_data_provenance_confusion", "synthetic_agent", D("b"), D("c"))
h2 = FamilyHypothesis("hypothesis:monitor", "monitor_evidence_boundary_confusion", "synthetic_agent", D("d"), D("9"))
assignments = (
    FamilyAssignment(results[0].digest, h1.hypothesis_id, "manual_analysis", "analysis:r9-fixture", D("6")),
    FamilyAssignment(results[1].digest, h1.hypothesis_id, "manual_analysis", "analysis:r9-fixture", D("7")),
)
ledger = build_family_ledger(results, (h1, h2), assignments)
frontier = discovery_frontier(RUN, results, (h1, h2), assignments)
print(json.dumps({
    "schema": "ordivon.ai-redteam.r9-family-ledger-fixture",
    "ledger": ledger.to_dict(),
    "ledgerDigest": ledger.digest,
    "frontier": frontier.to_dict(),
    "frontierDigest": frontier.digest,
}, sort_keys=True, indent=2))
