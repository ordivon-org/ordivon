from __future__ import annotations

import hashlib
import inspect
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]

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
from artifact_capabilities.publication.visual import (
    attribute_visual_regression,
    compare_raster_sets,
)


class PublicationPerceptualR1Tests(unittest.TestCase):
    CARRIER = "sha256:" + "a" * 64

    def test_evaluator_contract_accepts_owner_bound_lineage(self) -> None:
        self.assertIn(
            "observer_lineage_refs",
            inspect.signature(evaluate_perceptual_conformance).parameters,
        )

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

    def _lineage(
        self,
        reports: tuple[ObserverReport, ...],
        *,
        execution_refs: tuple[str | None, ...] | None = None,
        model_ref: str = "model:shared",
    ) -> dict[str, dict[str, str]]:
        refs = execution_refs or tuple(
            f"runtime:attempt:{index}" for index, _ in enumerate(reports, start=1)
        )
        result: dict[str, dict[str, str]] = {}
        for report, execution_ref in zip(reports, refs, strict=True):
            value = {"modelRef": model_ref}
            if execution_ref is not None:
                value["executionRef"] = execution_ref
            result[report.observer_id] = value
        return result

    def test_shared_required_execution_lineage_escalates_even_with_unique_labels(self) -> None:
        reports = self._three_passes()
        result = evaluate_perceptual_conformance(
            carrier_sha256=self.CARRIER,
            deterministic_standing="PASS",
            expected_pages=20,
            expected_figures=4,
            expected_tables=5,
            observer_reports=reports,
            observer_lineage_refs=self._lineage(
                reports,
                execution_refs=("runtime:attempt:same",) * 3,
            ),
        )
        self.assertEqual(result["standing"], "ESCALATE_SPECIALIST")
        self.assertTrue(
            any(
                reason.get("id") == "observer-lineage-not-disjoint"
                and reason.get("dimension") == "executionRef"
                for reason in result["adjudicationReasons"]
            )
        )

    def test_missing_required_execution_lineage_escalates(self) -> None:
        reports = self._three_passes()
        result = evaluate_perceptual_conformance(
            carrier_sha256=self.CARRIER,
            deterministic_standing="PASS",
            expected_pages=20,
            expected_figures=4,
            expected_tables=5,
            observer_reports=reports,
            observer_lineage_refs=self._lineage(
                reports,
                execution_refs=("runtime:attempt:1", None, "runtime:attempt:3"),
            ),
        )
        self.assertEqual(result["standing"], "ESCALATE_SPECIALIST")
        self.assertTrue(
            any(
                reason.get("id") == "observer-lineage-missing"
                and reason.get("dimension") == "executionRef"
                and reason.get("observerId") == "vision-b"
                for reason in result["adjudicationReasons"]
            )
        )

    def test_same_model_ref_is_not_required_to_be_disjoint_in_r1(self) -> None:
        reports = self._three_passes()
        result = evaluate_perceptual_conformance(
            carrier_sha256=self.CARRIER,
            deterministic_standing="PASS",
            expected_pages=20,
            expected_figures=4,
            expected_tables=5,
            observer_reports=reports,
            observer_lineage_refs=self._lineage(reports, model_ref="model:shared"),
        )
        self.assertEqual(result["standing"], "PASS_AGENT_ENSEMBLE")
        self.assertEqual(result["requiredDisjointLineageDimensions"], ["executionRef"])

    def test_three_independent_passes_supersede_legacy_perceptual_human_gate(self) -> None:
        reports = self._three_passes()
        perceptual = evaluate_perceptual_conformance(
            carrier_sha256=self.CARRIER,
            deterministic_standing="PASS",
            expected_pages=20,
            expected_figures=4,
            expected_tables=5,
            observer_reports=reports,
            observer_lineage_refs=self._lineage(reports),
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
            observer_lineage_refs=self._lineage(reports),
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
            observer_lineage_refs=self._lineage(reports),
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
            observer_lineage_refs=self._lineage(reports),
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
        reports = (
            report,
            self._report("VENUE_AWARE_VISION", observer="vision-b", key="attempt-b"),
            self._report("SEMANTIC_LAYOUT", observer="layout-c", key="attempt-c"),
        )
        result = evaluate_perceptual_conformance(
            carrier_sha256=self.CARRIER,
            deterministic_standing="PASS",
            expected_pages=20,
            expected_figures=4,
            expected_tables=5,
            observer_reports=reports,
            observer_lineage_refs=self._lineage(reports),
        )
        self.assertEqual(result["standing"], "ESCALATE_SPECIALIST")

    def test_verify_cli_consumes_bound_provider_receipts_for_lineage(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            carrier = root / "carrier.json"
            carrier.write_text(
                json.dumps(
                    {
                        "machineStanding": "PASS",
                        "pdfSha256": self.CARRIER,
                        "humanGates": ["HUMAN_PERCEPTUAL_SIGNOFF"],
                    }
                ),
                encoding="utf-8",
            )
            report_paths: list[Path] = []
            receipt_paths: list[Path] = []
            fixtures = (
                ("BLIND_VISION", "vision-a", "attempt-a", "runtime:attempt:1"),
                ("VENUE_AWARE_VISION", "vision-b", "attempt-b", "runtime:attempt:2"),
                ("SEMANTIC_LAYOUT", "layout-c", "attempt-c", "runtime:attempt:3"),
            )
            for role, observer_id, key, execution_ref in fixtures:
                report_path = root / f"{observer_id}.json"
                report_path.write_text(
                    json.dumps(
                        {
                            "schemaVersion": 1,
                            "kind": "publication-perceptual-observer-report",
                            "observerId": observer_id,
                            "role": role,
                            "independenceKey": key,
                            "carrierSha256": self.CARRIER,
                            "standing": "PASS",
                            "inputScope": {"allowed": [], "forbidden": []},
                            "coverage": {
                                "pagesExpected": 20,
                                "pagesReviewed": 20,
                                "figuresExpected": 4,
                                "figuresReviewed": 4,
                                "tablesExpected": 5,
                                "tablesReviewed": 5,
                            },
                            "findings": [],
                        }
                    ),
                    encoding="utf-8",
                )
                digest = "sha256:" + hashlib.sha256(report_path.read_bytes()).hexdigest()
                receipt_path = root / f"{observer_id}.receipt.json"
                receipt_path.write_text(
                    json.dumps(
                        {
                            "schemaVersion": 1,
                            "kind": "publication-perceptual-provider-execution-receipt",
                            "providerId": "fixture-provider",
                            "observerId": observer_id,
                            "role": role,
                            "carrierSha256": self.CARRIER,
                            "observerReportSha256": digest,
                            "independenceKey": key,
                            "lineageRefs": {"executionRef": execution_ref},
                            "standing": "PASS_PROVIDER_EXECUTION_BOUND",
                        }
                    ),
                    encoding="utf-8",
                )
                report_paths.append(report_path)
                receipt_paths.append(receipt_path)

            command = [
                sys.executable,
                str(ROOT / "scripts/publication_perceptual_verify.py"),
                "--carrier-evaluation",
                str(carrier),
                "--pages",
                "20",
                "--figures",
                "4",
                "--tables",
                "5",
            ]
            for report_path in report_paths:
                command.extend(["--observer-report", str(report_path)])
            for receipt_path in receipt_paths:
                command.extend(["--provider-receipt", str(receipt_path)])
            env = dict(os.environ)
            env["PYTHONPATH"] = str(ROOT)
            completed = subprocess.run(
                command,
                cwd=ROOT,
                env=env,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(completed.returncode, 1, completed.stdout + completed.stderr)
            result = json.loads(completed.stdout)
            self.assertEqual(
                result["perceptual"]["standing"],
                "ESCALATE_SPECIALIST",
            )
            self.assertEqual(result["release"]["standing"], "ESCALATE_SPECIALIST")
            self.assertTrue(
                any(
                    reason.get("id") == "observer-lineage-missing"
                    and reason.get("dimension") == "executionRef"
                    for reason in result["perceptual"]["adjudicationReasons"]
                )
            )

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

    def test_visual_attribution_requires_explanation_for_pixel_only_change(self) -> None:
        regression = {
            "kind": "publication-visual-regression",
            "changedPages": [{"page": 1}, {"page": 2}],
        }
        result = attribute_visual_regression(
            regression,
            baseline_pages_text=("old", "same"),
            candidate_pages_text=("new", "same"),
        )
        self.assertEqual(result["standing"], "PENDING_EXPLANATION")
        self.assertEqual(result["unresolvedPages"], [2])
        explained = attribute_visual_regression(
            regression,
            baseline_pages_text=("old", "same"),
            candidate_pages_text=("new", "same"),
            externally_explained_pages={2},
        )
        self.assertEqual(explained["standing"], "PASS")
        self.assertEqual(explained["unexpectedChangeCount"], 0)

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
