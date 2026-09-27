from __future__ import annotations

import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = ROOT.parents[2]
for path in (ROOT, REPO_ROOT / "studies" / "security" / "ai-redteam-foundry-r1", REPO_ROOT / "studies" / "security" / "ai-redteam-foundry-r8", REPO_ROOT / "studies" / "security" / "ai-redteam-foundry-r9"):
    sys.path.insert(0, str(path))

from foundry.providers import ProviderArtifactRef  # noqa: E402
from foundry_r9 import FamilyHypothesis, FamilyLedgerEntry, VulnerabilityFamilyLedger  # noqa: E402
from foundry_r10 import AdaptiveRegressionReceipt, PatchBinding, RegressionSearchPhase, UtilityEvaluationRef  # noqa: E402

D = lambda c: "sha256:" + c * 64


class SchemaContractTests(unittest.TestCase):
    def test_receipt_schema_matches_serialization(self) -> None:
        schema = json.loads((ROOT / "schemas" / "adaptive-regression-receipt.schema.json").read_text())
        hypothesis = FamilyHypothesis("hypothesis:schema", "mechanism", "synthetic_agent", D("1"), D("2"))
        entry = FamilyLedgerEntry(hypothesis.family_id, hypothesis, (D("3"),), ("p",), ("surface",), ("target",), 1, 1)
        ledger = VulnerabilityFamilyLedger((entry,), (D("3"),), (D("4"),), ())
        patch = PatchBinding("patch:schema", "owner", D("5"), "before", D("6"), "after", D("7"))
        phases = tuple(RegressionSearchPhase(name, D(digit), "after", D("7"), D("b"), D("c"), 1, 1, True, True, D("d"), D("e"), (), 0) for name, digit in zip(("original_replay", "family_mutation", "defense_aware_reattack"), ("8", "9", "a"), strict=True))
        artifact = ProviderArtifactRef("provider", "v1", "utility.json", D("f"), 10, "utility.json")
        utility = UtilityEvaluationRef("suite", "after", D("7"), 1, 0, True, artifact)
        receipt = AdaptiveRegressionReceipt(entry.family_id, entry.digest, hypothesis.digest, ledger.digest, patch, phases, utility)
        payload = receipt.to_dict()
        self.assertEqual(set(schema["properties"]), set(payload))
        self.assertTrue(set(schema["required"]).issubset(payload))
        self.assertEqual(payload["standing"], "PASS")


if __name__ == "__main__":
    unittest.main()
