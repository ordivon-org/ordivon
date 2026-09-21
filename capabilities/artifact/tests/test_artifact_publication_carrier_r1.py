from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from artifact_capabilities.publication import (
    CarrierObservation,
    evaluate_publication_contract,
    load_publication_contract,
)

ROOT = Path(__file__).resolve().parents[1]


class PublicationCarrierR1Tests(unittest.TestCase):
    def _contract(self) -> dict:
        return {
            "schemaVersion": 1,
            "kind": "publication-carrier-contract",
            "id": "test-fse-like",
            "authority": [
                {"url": "https://example.invalid/venue", "observedAt": "2026-09-21"}
            ],
            "mechanical": {
                "requireQpdfPass": True,
                "requireAllFontsEmbedded": True,
                "maxType3Fonts": 0,
                "maxOverfullBoxes": 0,
                "maxUndefinedCitations": 0,
                "maxUndefinedReferences": 0,
            },
            "textSemantics": {
                "requiredRegex": [
                    {"id": "ccs", "pattern": r"CCS Concepts"},
                    {
                        "id": "keywords",
                        "pattern": r"(?:Additional Key Words and Phrases|Keywords)",
                    },
                ],
                "forbiddenRegex": [
                    {"id": "epoch-year", "pattern": r"\b1970\b"},
                ],
                "forbidMarkdownHeadingResidue": True,
                "detectDuplicateFigureCaptions": True,
            },
            "pageRules": {
                "totalPagesMax": 22,
                "headings": [
                    {
                        "id": "conclusion",
                        "pattern": r"^\s*(?:\d+\.\s+)?Conclusion\s*$",
                        "maxPage": 18,
                    },
                    {
                        "id": "data-availability",
                        "pattern": r"^\s*Data Availability\s*$",
                        "mustFollow": "conclusion",
                    },
                    {
                        "id": "references",
                        "pattern": r"^\s*References\s*$",
                        "minPage": 19,
                    },
                ],
            },
            "reviewerExperience": {
                "humanPerceptualSignoffRequired": True,
            },
        }

    def _observation(self, text: str, pages: tuple[str, ...]) -> CarrierObservation:
        return CarrierObservation(
            pdf_sha256="a" * 64,
            page_count=len(pages),
            text=text,
            pages=pages,
            qpdf_pass=True,
            all_fonts_embedded=True,
            type3_fonts=0,
            overfull_boxes=0,
            undefined_citations=0,
            undefined_references=0,
            human_perceptual_signoff=False,
        )

    def test_contract_loader_rejects_missing_authority(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "contract.json"
            value = self._contract()
            value["authority"] = []
            p.write_text(json.dumps(value))
            with self.assertRaises(ValueError):
                load_publication_contract(p)

    def test_old_paper3_like_carrier_fails_semantic_production_gates(self) -> None:
        contract = self._contract()
        pages = (
            "Anonymous Author(s). 1970\nPublication date: January 1970\n"
            "Fig. 1. Study object\nFigure 1: Study object\nCCS Concepts\nKeywords\n",
            "## 2. Background and Related Work\n",
        ) + tuple("body" for _ in range(15)) + (
            "7. Conclusion\n",
            "Data Availability\nReferences\n",
        )
        obs = self._observation("\f".join(pages), pages)
        result = evaluate_publication_contract(obs, contract)
        self.assertEqual(result["standing"], "FAIL")
        ids = {item["id"] for item in result["findings"]}
        self.assertIn("epoch-year", ids)
        self.assertIn("markdown-heading-residue", ids)
        self.assertIn("duplicate-figure-caption:1", ids)

    def test_clean_carrier_passes_machine_gates_but_human_gate_stays_open(self) -> None:
        contract = self._contract()
        pages = (
            "Anonymous Author(s). 2027\nPublication date: July 2027\n"
            "CCS Concepts: Software and its engineering\nKeywords: OpenAPI\n"
            "Fig. 1. Study object\n",
        ) + tuple("body" for _ in range(16)) + (
            "7. Conclusion\nData Availability\n",
            "References\n",
        )
        obs = self._observation("\f".join(pages), pages)
        result = evaluate_publication_contract(obs, contract)
        self.assertEqual(result["machineStanding"], "PASS")
        self.assertEqual(result["standing"], "PENDING_HUMAN")
        self.assertEqual(result["humanGates"], ["HUMAN_PERCEPTUAL_SIGNOFF"])

    def test_review_mode_line_numbers_do_not_hide_headings(self) -> None:
        contract = self._contract()
        pages = (
            "Anonymous Author(s). 2027\nCCS Concepts\nKeywords\nFig. 1. Study object\n",
        ) + tuple("body" for _ in range(16)) + (
            "859   7. Conclusion\n871   Data Availability\n",
            "887   References\n",
        )
        obs = self._observation("\f".join(pages), pages)
        result = evaluate_publication_contract(obs, contract)
        self.assertEqual(result["machineStanding"], "PASS")
        self.assertEqual(result["standing"], "PENDING_HUMAN")

    def test_missing_ccs_and_keywords_fail(self) -> None:
        contract = self._contract()
        pages = tuple("body" for _ in range(17)) + (
            "7. Conclusion\nData Availability\n",
            "References\n",
        )
        obs = self._observation("\f".join(pages), pages)
        result = evaluate_publication_contract(obs, contract)
        ids = {item["id"] for item in result["findings"]}
        self.assertIn("ccs", ids)
        self.assertIn("keywords", ids)

    def test_page_contract_is_not_reduced_to_total_page_count(self) -> None:
        contract = self._contract()
        pages = tuple("body" for _ in range(18)) + (
            "7. Conclusion\nData Availability\n",
            "References\n",
        )
        obs = self._observation(
            "CCS Concepts\nKeywords\n" + "\f".join(pages),
            pages,
        )
        result = evaluate_publication_contract(obs, contract)
        ids = {item["id"] for item in result["findings"]}
        self.assertIn("conclusion:max-page", ids)

    def test_required_compile_metric_fails_closed_when_unobserved(self) -> None:
        contract = self._contract()
        pages = (
            "Anonymous Author(s). 2027\nCCS Concepts\nKeywords\nFig. 1. Study object\n",
        ) + tuple("body" for _ in range(16)) + (
            "7. Conclusion\nData Availability\n",
            "References\n",
        )
        obs = CarrierObservation(
            pdf_sha256="b" * 64,
            page_count=len(pages),
            text="\f".join(pages),
            pages=pages,
            qpdf_pass=True,
            all_fonts_embedded=True,
            type3_fonts=0,
            overfull_boxes=None,
            undefined_citations=None,
            undefined_references=None,
            human_perceptual_signoff=False,
        )
        result = evaluate_publication_contract(obs, contract)
        ids = {item["id"] for item in result["findings"]}
        self.assertIn("overfull-boxes:unobserved", ids)
        self.assertIn("undefined-citations:unobserved", ids)
        self.assertIn("undefined-references:unobserved", ids)

    def test_repository_contains_external_authority_bound_fse_profile(self) -> None:
        profile = ROOT.parents[1] / "meta/research/venues/fse-2027-research-r1.json"
        value = json.loads(profile.read_text())
        self.assertEqual(value["kind"], "publication-carrier-contract")
        self.assertEqual(value["id"], "fse-2027-research-r1")
        urls = {x["url"] for x in value["authority"]}
        self.assertIn(
            "https://conf.researchr.org/track/fse-2027/fse-2027-papers",
            urls,
        )

    def test_research_profile_keeps_truth_with_study_authority(self) -> None:
        profile = ROOT.parents[1] / "meta/research/publication-closure-profile-r1.json"
        value = json.loads(profile.read_text())
        self.assertEqual(value["truthRole"], "composition-profile-not-scientific-truth")
        self.assertEqual(value["runtimeOwner"], None)
        self.assertEqual(
            value["ownerBindings"]["carrierMechanics"],
            "capabilities/artifact",
        )
        self.assertEqual(value["freezeOrder"][-1], "SUBMISSION_FREEZE")


if __name__ == "__main__":
    unittest.main()
