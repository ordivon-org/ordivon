from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = ROOT.parents[2]
for path in (ROOT, REPO_ROOT / "studies" / "security" / "ai-redteam-foundry-r1", REPO_ROOT / "studies" / "security" / "ai-redteam-foundry-r8", REPO_ROOT / "studies" / "security" / "ai-redteam-foundry-r9"):
    sys.path.insert(0, str(path))

from foundry.providers import ProviderArtifactRef  # noqa: E402
from foundry_r9 import FamilyHypothesis, FamilyLedgerEntry, VulnerabilityFamilyLedger  # noqa: E402
from foundry_r10 import AdaptiveRegressionReceipt, PatchBinding, RegressionSearchPhase, UtilityEvaluationRef  # noqa: E402

D = lambda c: "sha256:" + c * 64

hypothesis = FamilyHypothesis("hypothesis:r10-fixture", "instruction_data_provenance_confusion", "synthetic_agent", D("1"), D("2"))
entry = FamilyLedgerEntry(hypothesis.family_id, hypothesis, (D("3"),), ("pyrit",), ("synthetic_indirect_injection",), ("target:before",), 1, 1)
ledger = VulnerabilityFamilyLedger((entry,), (D("3"),), (D("4"),), ())
patch = PatchBinding("patch:r10-fixture", "owner:fixture", D("5"), "target:before", D("6"), "target:after", D("7"))
phases = tuple(
    RegressionSearchPhase(
        phase=name,
        search_run_digest=D(digit),
        target_after_id="target:after",
        target_after_digest=D("7"),
        provider_completion_digest=D("b"),
        review_evidence_digest=D("c"),
        expected_candidate_count=1 if name == "original_replay" else 4,
        observed_result_count=1 if name == "original_replay" else 4,
        coverage_complete=True,
        review_complete=True,
        family_ledger_digest=D("d"),
        discovery_frontier_digest=D("e"),
        observed_family_ids=(),
        unassigned_provider_positive_count=0,
    )
    for name, digit in zip(("original_replay", "family_mutation", "defense_aware_reattack"), ("8", "9", "a"), strict=True)
)
utility_artifact = ProviderArtifactRef("agentdojo", "fixture-v1", "utility.json", D("f"), 256, "fixtures/utility.json")
utility = UtilityEvaluationRef("utility:r10-fixture", "target:after", D("7"), 16, 0, True, utility_artifact)
receipt = AdaptiveRegressionReceipt(entry.family_id, entry.digest, hypothesis.digest, ledger.digest, patch, phases, utility)
print(json.dumps({
    "schema": "ordivon.ai-redteam.r10-adaptive-regression-fixture",
    "receipt": receipt.to_dict(),
    "receiptDigest": receipt.digest,
}, sort_keys=True, indent=2))
