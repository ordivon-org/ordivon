from __future__ import annotations

import unittest

from ordivon_studio.creative_alpha import VARIANTS, build_holdout_protocol, build_visible_protocol
from ordivon_studio.research_validity import seed_commitment


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
