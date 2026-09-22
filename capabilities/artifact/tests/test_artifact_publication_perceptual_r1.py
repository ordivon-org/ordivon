from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from PIL import Image

from artifact_capabilities.publication.attestation import (
    build_publication_carrier_attestation,
)
from artifact_capabilities.publication.contract import CarrierObservation
from artifact_capabilities.publication.inventory import build_carrier_inventory
from artifact_capabilities.publication.perceptual import (
    ObserverFinding,
    ObserverReport,
    combine_carrier_and_perceptual,
    evaluate_perceptual_conformance,
)
from artifact_capabilities.publication.visual import compare_raster_sets


class PublicationPerceptualR1Tests(unittest.TestCase):
    CARRIER = "sha256:" + "a" * 64

    def _report(
        self,
        role: str,
        *,
        observer: str,
        key: str,
        standing: str = "PASS",
        findings: tuple[ObserverFinding, ...] = (),
    ) -> ObserverReport:
        return ObserverReport(
            observer_id=observer,
            role=role,
            independence_key=key,
            carrier_sha256=self.CARRIER,
            standing=standing,
            pages_expected=20,
            pages_reviewed=20,
            figures_expected=4,
            figures_reviewed=4,
            tables_expected=5,
            tables_reviewed=5,
            findings=findings,
        )

    def _three_passes(self) -> tuple[ObserverReport, ...]:
        return (
            self._report("BLIND_VISION", observer="vision-a", key="attempt-a"),
            self._report("VENUE_AWARE_VISION", observer="vision-b", key="attempt-b"),
            self._report("SEMANTIC_LAYOUT", observer="layout-c", key="attempt-c"),
        )

    def test_three_independent_passes_supersede_legacy_perceptual_human_gate(self) -> None:
        perceptual = evaluate_perceptual_conformance(
            carrier_sha256=self.CARRIER,
            deterministic_standing="PASS",
            expected_pages=20,
            expected_figures=4,
            expected_tables=5,
            observer_reports=self._three_passes(),
        )
        self.assertEqual(perceptual["standing"], "PASS_AGENT_ENSEMBLE")
        self.assertFalse(perceptual["authorReviewRequired"])
        carrier = {
            "machineStanding": "PASS",
            "pdfSha256": self.CARRIER,
            "humanGates": ["HUMAN_PERCEPTUAL_SIGNOFF"],
        }
        release = combine_carrier_and_perceptual(carrier, perceptual)
        self.assertEqual(release["standing"], "PASS")
        self.assertEqual(
            release["supersededLegacyGates"],
            ["HUMAN_PERCEPTUAL_SIGNOFF"],
        )

    def test_uncertainty_escalates_to_specialist_not_author(self) -> None:
        finding = ObserverFinding(
            finding_id="figure-4-legibility",
            predicate="NORMAL_SCALE_READABILITY",
            severity="UNCERTAIN",
            page=12,
        )
        reports = (
            self._report("BLIND_VISION", observer="vision-a", key="attempt-a"),
            self._report(
                "VENUE_AWARE_VISION",
                observer="vision-b",
                key="attempt-b",
                standing="UNCERTAIN",
                findings=(finding,),
            ),
            self._report("SEMANTIC_LAYOUT", observer="layout-c", key="attempt-c"),
        )
        result = evaluate_perceptual_conformance(
            carrier_sha256=self.CARRIER,
            deterministic_standing="PASS",
            expected_pages=20,
            expected_figures=4,
            expected_tables=5,
            observer_reports=reports,
        )
        self.assertEqual(result["standing"], "ESCALATE_SPECIALIST")
        self.assertEqual(result["escalationTarget"], "INDEPENDENT_PUBLICATION_SPECIALIST")
        self.assertFalse(result["authorReviewRequired"])

    def test_major_finding_fails_closed(self) -> None:
        finding = ObserverFinding(
            finding_id="table-2-clipped",
            predicate="TABLE_CLIPPING",
            severity="MAJOR",
            page=7,
        )
        reports = (
            self._report("BLIND_VISION", observer="vision-a", key="attempt-a"),
            self._report(
                "VENUE_AWARE_VISION",
                observer="vision-b",
                key="attempt-b",
                standing="FAIL",
                findings=(finding,),
            ),
            self._report("SEMANTIC_LAYOUT", observer="layout-c", key="attempt-c"),
        )
        result = evaluate_perceptual_conformance(
            carrier_sha256=self.CARRIER,
            deterministic_standing="PASS",
            expected_pages=20,
            expected_figures=4,
            expected_tables=5,
            observer_reports=reports,
        )
        self.assertEqual(result["standing"], "FAIL")

    def test_duplicate_independence_key_escalates(self) -> None:
        reports = (
            self._report("BLIND_VISION", observer="vision-a", key="same-attempt"),
            self._report("VENUE_AWARE_VISION", observer="vision-b", key="same-attempt"),
            self._report("SEMANTIC_LAYOUT", observer="layout-c", key="attempt-c"),
        )
        result = evaluate_perceptual_conformance(
            carrier_sha256=self.CARRIER,
            deterministic_standing="PASS",
            expected_pages=20,
            expected_figures=4,
            expected_tables=5,
            observer_reports=reports,
        )
        self.assertEqual(result["standing"], "ESCALATE_SPECIALIST")

    def test_incomplete_coverage_escalates(self) -> None:
        report = ObserverReport(
            observer_id="vision-a",
            role="BLIND_VISION",
            independence_key="attempt-a",
            carrier_sha256=self.CARRIER,
            standing="PASS",
            pages_expected=20,
            pages_reviewed=19,
            figures_expected=4,
            figures_reviewed=4,
            tables_expected=5,
            tables_reviewed=5,
            findings=(),
        )
        result = evaluate_perceptual_conformance(
            carrier_sha256=self.CARRIER,
            deterministic_standing="PASS",
            expected_pages=20,
            expected_figures=4,
            expected_tables=5,
            observer_reports=(
                report,
                self._report("VENUE_AWARE_VISION", observer="vision-b", key="attempt-b"),
                self._report("SEMANTIC_LAYOUT", observer="layout-c", key="attempt-c"),
            ),
        )
        self.assertEqual(result["standing"], "ESCALATE_SPECIALIST")

    def test_visual_diff_detects_changed_page(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            a = root / "a.png"
            b = root / "b.png"
            c = root / "c.png"
            Image.new("RGB", (30, 30), "white").save(a)
            Image.new("RGB", (30, 30), "white").save(b)
            changed = Image.new("RGB", (30, 30), "white")
            changed.putpixel((10, 10), (0, 0, 0))
            changed.save(c)
            same = compare_raster_sets((a,), (b,))
            diff = compare_raster_sets((a,), (c,))
            self.assertEqual(same["standing"], "PASS")
            self.assertEqual(diff["standing"], "CHANGED")
            self.assertEqual(diff["changedPages"][0]["page"], 1)

    def test_inventory_is_routing_evidence_not_semantic_truth(self) -> None:
        pages = (
            "Anonymous Author\n86   Fig. 1. Overview\n281   Table 1. Counts\n",
            "Fig. 2. Results\n",
        )
        observation = CarrierObservation(
            pdf_sha256="a" * 64,
            page_count=2,
            text="\f".join(pages),
            pages=pages,
            qpdf_pass=True,
            all_fonts_embedded=True,
            type3_fonts=0,
            overfull_boxes=0,
            undefined_citations=0,
            undefined_references=0,
        )
        inventory = build_carrier_inventory(observation)
        self.assertEqual(inventory["pageCount"], 2)
        self.assertEqual(len(inventory["figures"]), 2)
        self.assertEqual(len(inventory["tables"]), 1)
        self.assertIn("not-document-semantic-truth", inventory["truthRole"])

    def test_attestation_requires_release_pass_and_full_digest_binding(self) -> None:
        evidence = {
            "structural": "sha256:" + "b" * 64,
            "perceptual": "sha256:" + "c" * 64,
            "independentVerifier": "sha256:" + "d" * 64,
        }
        value = build_publication_carrier_attestation(
            carrier_sha256=self.CARRIER,
            venue_contract_sha256="sha256:" + "e" * 64,
            evidence=evidence,
            release_standing="PASS",
            page_coverage=(20, 20),
            figure_coverage=(4, 4),
            table_coverage=(5, 5),
        )
        self.assertEqual(value["standing"], "PASS_PUBLICATION_CARRIER_ATTESTATION")
        with self.assertRaises(ValueError):
            build_publication_carrier_attestation(
                carrier_sha256=self.CARRIER,
                venue_contract_sha256="sha256:" + "e" * 64,
                evidence=evidence,
                release_standing="ESCALATE_SPECIALIST",
                page_coverage=(20, 20),
                figure_coverage=(4, 4),
                table_coverage=(5, 5),
            )


if __name__ == "__main__":
    unittest.main()
