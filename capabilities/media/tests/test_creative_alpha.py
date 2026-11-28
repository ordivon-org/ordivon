from __future__ import annotations

import unittest

from ordivon_studio.research.creative_observer import build_observer_bundle
from ordivon_studio.research.creative_protocol import (
    VARIANTS,
    build_holdout_protocol,
    build_visible_protocol,
)
from ordivon_studio.research.grounded_contracts import qa_result_schema
from ordivon_studio.research.grounded_text_tasks import build_comprehension_tasks
from ordivon_studio.research.trial_registration import seed_commitment


class CreativeAlphaTest(unittest.TestCase):
    def test_visible_protocol_keeps_holdout_content_absent(self) -> None:
        secret = "never-visible-holdout-seed"
        protocol = build_visible_protocol(holdout_seed_commitment=seed_commitment(secret))
        self.assertNotIn(secret, str(protocol))
        self.assertEqual(protocol["holdout"]["status"], "sealed")
        self.assertEqual(protocol["primaryContrast"], {"treatment": "explicit-chain", "control": "fragmented"})
        self.assertEqual(len(protocol["mechanisms"]), 2)

    def test_variants_have_identical_fact_sets_and_only_reorder_them(self) -> None:
        protocol = build_visible_protocol(holdout_seed_commitment=seed_commitment("holdout"))
        for item in protocol["mechanisms"]:
            manifest = item["manifest"]
            section_maps = {
                variant["variantId"]: {section["evidenceId"]: section["text"] for section in variant["sections"]}
                for variant in manifest["variants"]
            }
            self.assertEqual(set(section_maps), set(VARIANTS))
            self.assertEqual(section_maps["explicit-chain"], section_maps["fragmented"])
            self.assertEqual(section_maps["explicit-chain"], section_maps["evidence-delayed"])
            orders = {variant["variantId"]: [section["evidenceId"] for section in variant["sections"]] for variant in manifest["variants"]}
            self.assertNotEqual(orders["explicit-chain"], orders["fragmented"])
            self.assertNotEqual(orders["explicit-chain"], orders["evidence-delayed"])

    def test_text_and_browser_observers_share_answer_contract(self) -> None:
        protocol = build_visible_protocol(holdout_seed_commitment=seed_commitment("fixture"))
        receipts = []
        for mechanism in protocol["mechanisms"]:
            manifest = mechanism["manifest"]
            representatives = [
                {
                    "variantId": variant["variantId"],
                    "screenshotDigest": "fixture-screenshot",
                    "viewportEvidenceDigest": "fixture-viewport",
                    "viewportEvidence": [
                        dict(section, top=10, bottom=20)
                        for section in variant["sections"][:2]
                    ],
                }
                for variant in manifest["variants"]
            ]
            receipts.append({
                "experimentId": manifest["experimentId"],
                "receiptDigest": "fixture-receipt",
                "representativeEncounters": representatives,
                "integrity": dict.fromkeys((
                    "allAssignmentsUnique",
                    "allExposuresRealizedExactlyOnce",
                    "allPropensitiesExplicit",
                    "allVariantDigestsBound",
                ), True),
            })
        browser = build_observer_bundle(protocol=protocol, web_receipts=receipts, replicates=1)
        text_tasks = build_comprehension_tasks(replicates=1)
        expected = qa_result_schema([f"Q{i}" for i in range(1, 7)], ["O1", "O2", "O3", "O4"])
        self.assertEqual(len(browser["tasks"]), 6)
        self.assertEqual(len(text_tasks), 4)
        for task in [*browser["tasks"], *text_tasks]:
            self.assertEqual(task["resultSchema"], expected)
        answers = expected["properties"]["answers"]
        self.assertEqual((answers["minItems"], answers["maxItems"]), (6, 6))
        self.assertEqual(answers["items"]["properties"]["evidenceIds"]["maxItems"], 6)
        self.assertFalse(answers["items"]["additionalProperties"])
        # Each consumer receives an independent mutable wire object.
        browser["tasks"][0]["resultSchema"]["required"].clear()
        self.assertEqual(browser["tasks"][1]["resultSchema"], expected)
        self.assertEqual(text_tasks[0]["resultSchema"], expected)

    def test_holdout_requires_exact_seed_commitment_and_frozen_contrast(self) -> None:
        seed = "sealed-content-seed"
        selection = {
            "contrast": {"treatment": "explicit-chain", "control": "fragmented"},
            "sourceScoreDigest": "sha256:score",
            "selectionDigest": "sha256:selection",
        }
        with self.assertRaises(ValueError):
            build_holdout_protocol(holdout_seed="wrong", expected_commitment=seed_commitment(seed), visible_selection=selection)
        protocol = build_holdout_protocol(holdout_seed=seed, expected_commitment=seed_commitment(seed), visible_selection=selection)
        self.assertEqual(protocol["mechanismId"], "C")
        self.assertEqual(protocol["contrast"], selection["contrast"])


if __name__ == "__main__": unittest.main()
