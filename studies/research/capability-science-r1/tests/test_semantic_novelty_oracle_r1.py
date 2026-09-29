from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

STUDY = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(STUDY / "scripts"))

from semantic_novelty_oracle_r1 import canonical_bytes, novelty_report, sha256_ref  # noqa: E402


def load_fixture(name: str):
    return json.loads((STUDY / "fixtures" / name).read_text(encoding="utf-8"))


class SemanticNoveltyOracleR1Tests(unittest.TestCase):
    def test_positive_candidate_has_witness_against_every_baseline(self):
        fixture = load_fixture("novelty-positive-r1.json")
        report = novelty_report(fixture)
        self.assertEqual(report["verdict"], "CERTIFIED_NOVEL_WITHIN_BOUNDED_POLICY")
        self.assertEqual(len(report["witnesses"]), len(fixture["library"]))
        self.assertEqual(report["notDistinguishedFromWithinPolicy"], [])

    def test_equivalent_candidate_is_not_admitted_as_novel(self):
        fixture = load_fixture("novelty-negative-r1.json")
        report = novelty_report(fixture)
        self.assertEqual(report["verdict"], "NOVELTY_NOT_ESTABLISHED")
        self.assertIn("cap:stateless-echo", report["notDistinguishedFromWithinPolicy"])

    def test_canonical_digest_is_key_order_independent(self):
        left = {"a": 1, "b": {"x": 2, "y": 3}}
        right = {"b": {"y": 3, "x": 2}, "a": 1}
        self.assertEqual(canonical_bytes(left), canonical_bytes(right))
        self.assertEqual(sha256_ref(left), sha256_ref(right))

    def test_missing_observation_context_fails_closed(self):
        fixture = load_fixture("novelty-positive-r1.json")
        del fixture["candidate"]["observations"]["recover_in_fresh_session"]
        with self.assertRaises(ValueError):
            novelty_report(fixture)

    def test_novelty_never_grants_authority(self):
        fixture = load_fixture("novelty-positive-r1.json")
        report = novelty_report(fixture)
        self.assertFalse(report["authorityGranted"])
        self.assertFalse(report["executionAuthorityGranted"])


if __name__ == "__main__":
    unittest.main()
