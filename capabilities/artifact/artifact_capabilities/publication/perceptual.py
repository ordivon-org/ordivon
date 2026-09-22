from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

SHA256_RX = re.compile(r"^sha256:[0-9a-f]{64}$")
ROLES = ("BLIND_VISION", "VENUE_AWARE_VISION", "SEMANTIC_LAYOUT")
SEVERITIES = {"BLOCKER", "MAJOR", "MINOR", "INFO", "UNCERTAIN"}
REPORT_STANDINGS = {"PASS", "FAIL", "UNCERTAIN"}


@dataclass(frozen=True, slots=True)
class ObserverFinding:
    finding_id: str
    predicate: str
    severity: str
    page: int | None = None
    object_type: str | None = None
    confidence: float | None = None
    evidence: dict[str, Any] | None = None

    def __post_init__(self) -> None:
        if self.severity not in SEVERITIES:
            raise ValueError(f"unsupported finding severity: {self.severity}")
        if self.page is not None and self.page < 1:
            raise ValueError("finding page must be positive")
        if self.confidence is not None and not 0 <= self.confidence <= 1:
            raise ValueError("finding confidence must be in [0, 1]")


@dataclass(frozen=True, slots=True)
class ObserverReport:
    observer_id: str
    role: str
    independence_key: str
    carrier_sha256: str
    standing: str
    pages_expected: int
    pages_reviewed: int
    figures_expected: int
    figures_reviewed: int
    tables_expected: int
    tables_reviewed: int
    findings: tuple[ObserverFinding, ...]

    def __post_init__(self) -> None:
        if self.role not in ROLES:
            raise ValueError(f"unsupported observer role: {self.role}")
        if self.standing not in REPORT_STANDINGS:
            raise ValueError(f"unsupported observer standing: {self.standing}")
        if not SHA256_RX.fullmatch(self.carrier_sha256):
            raise ValueError("carrier_sha256 must be sha256:<64 lowercase hex>")
        if not self.observer_id or not self.independence_key:
            raise ValueError("observer_id and independence_key are required")
        for expected, reviewed, label in (
            (self.pages_expected, self.pages_reviewed, "pages"),
            (self.figures_expected, self.figures_reviewed, "figures"),
            (self.tables_expected, self.tables_reviewed, "tables"),
        ):
            if expected < 0 or reviewed < 0:
                raise ValueError(f"{label} coverage values must be non-negative")
            if reviewed > expected:
                raise ValueError(f"{label} reviewed cannot exceed expected")


def _finding_from_json(value: dict[str, Any]) -> ObserverFinding:
    return ObserverFinding(
        finding_id=value["id"],
        predicate=value["predicate"],
        severity=value["severity"],
        page=value.get("page"),
        object_type=value.get("objectType"),
        confidence=value.get("confidence"),
        evidence=value.get("evidence"),
    )


def load_observer_report(path: Path) -> ObserverReport:
    value = json.loads(path.read_text(encoding="utf-8"))
    if value.get("schemaVersion") != 1 or value.get("kind") != "publication-perceptual-observer-report":
        raise ValueError("invalid perceptual observer report")
    coverage = value.get("coverage", {})
    return ObserverReport(
        observer_id=value["observerId"],
        role=value["role"],
        independence_key=value["independenceKey"],
        carrier_sha256=value["carrierSha256"],
        standing=value["standing"],
        pages_expected=coverage["pagesExpected"],
        pages_reviewed=coverage["pagesReviewed"],
        figures_expected=coverage["figuresExpected"],
        figures_reviewed=coverage["figuresReviewed"],
        tables_expected=coverage["tablesExpected"],
        tables_reviewed=coverage["tablesReviewed"],
        findings=tuple(_finding_from_json(x) for x in value.get("findings", [])),
    )


def evaluate_perceptual_conformance(
    *,
    carrier_sha256: str,
    deterministic_standing: str,
    expected_pages: int,
    expected_figures: int,
    expected_tables: int,
    observer_reports: Iterable[ObserverReport],
    visual_regression_standing: str = "PASS",
) -> dict[str, Any]:
    """Adjudicate independent perceptual evidence.

    R1 is deliberately conservative: all three required observer roles must be
    present with distinct independence keys and complete coverage. A single
    FAIL/major finding fails; uncertainty escalates to a specialist rather than
    silently passing or defaulting to the paper author.
    """

    if not SHA256_RX.fullmatch(carrier_sha256):
        raise ValueError("carrier_sha256 must be sha256:<64 lowercase hex>")
    if min(expected_pages, expected_figures, expected_tables) < 0:
        raise ValueError("expected coverage counts must be non-negative")

    reports = tuple(observer_reports)
    reasons: list[dict[str, Any]] = []

    if deterministic_standing != "PASS":
        reasons.append({"id": "deterministic-conformance", "standing": deterministic_standing})
    if visual_regression_standing not in {"PASS", "NOT_APPLICABLE"}:
        reasons.append({"id": "visual-regression", "standing": visual_regression_standing})

    by_role: dict[str, list[ObserverReport]] = {}
    for report in reports:
        by_role.setdefault(report.role, []).append(report)
        if report.carrier_sha256 != carrier_sha256:
            reasons.append(
                {
                    "id": "carrier-binding",
                    "observerId": report.observer_id,
                    "expected": carrier_sha256,
                    "observed": report.carrier_sha256,
                }
            )
        expected = (expected_pages, expected_figures, expected_tables)
        declared = (report.pages_expected, report.figures_expected, report.tables_expected)
        reviewed = (report.pages_reviewed, report.figures_reviewed, report.tables_reviewed)
        if declared != expected or reviewed != expected:
            reasons.append(
                {
                    "id": "coverage",
                    "observerId": report.observer_id,
                    "expected": {
                        "pages": expected_pages,
                        "figures": expected_figures,
                        "tables": expected_tables,
                    },
                    "declaredExpected": {
                        "pages": report.pages_expected,
                        "figures": report.figures_expected,
                        "tables": report.tables_expected,
                    },
                    "reviewed": {
                        "pages": report.pages_reviewed,
                        "figures": report.figures_reviewed,
                        "tables": report.tables_reviewed,
                    },
                }
            )

    for role in ROLES:
        count = len(by_role.get(role, []))
        if count != 1:
            reasons.append({"id": "observer-role-cardinality", "role": role, "observed": count})

    observer_ids = [x.observer_id for x in reports]
    independence_keys = [x.independence_key for x in reports]
    if len(observer_ids) != len(set(observer_ids)):
        reasons.append({"id": "observer-id-independence", "message": "observer ids are not unique"})
    if len(independence_keys) != len(set(independence_keys)):
        reasons.append(
            {"id": "observer-execution-independence", "message": "independence keys are not unique"}
        )

    blocker_findings: list[dict[str, Any]] = []
    uncertain_findings: list[dict[str, Any]] = []
    report_fail = False
    report_uncertain = False
    for report in reports:
        report_fail = report_fail or report.standing == "FAIL"
        report_uncertain = report_uncertain or report.standing == "UNCERTAIN"
        for finding in report.findings:
            item = {
                "observerId": report.observer_id,
                "role": report.role,
                "id": finding.finding_id,
                "predicate": finding.predicate,
                "severity": finding.severity,
                "page": finding.page,
            }
            if finding.severity in {"BLOCKER", "MAJOR"}:
                blocker_findings.append(item)
            elif finding.severity == "UNCERTAIN":
                uncertain_findings.append(item)

    if deterministic_standing == "FAIL" or blocker_findings or report_fail:
        standing = "FAIL"
    elif reasons or uncertain_findings or report_uncertain:
        standing = "ESCALATE_SPECIALIST"
    else:
        standing = "PASS_AGENT_ENSEMBLE"

    return {
        "schemaVersion": 1,
        "kind": "publication-perceptual-conformance-evaluation",
        "carrierSha256": carrier_sha256,
        "deterministicStanding": deterministic_standing,
        "visualRegressionStanding": visual_regression_standing,
        "requiredObserverRoles": list(ROLES),
        "observerCount": len(reports),
        "coverage": {
            "pagesExpected": expected_pages,
            "figuresExpected": expected_figures,
            "tablesExpected": expected_tables,
        },
        "blockerFindings": blocker_findings,
        "uncertainFindings": uncertain_findings,
        "adjudicationReasons": reasons,
        "standing": standing,
        "escalationTarget": (
            "INDEPENDENT_PUBLICATION_SPECIALIST"
            if standing == "ESCALATE_SPECIALIST"
            else None
        ),
        "authorReviewRequired": False,
        "nonClaims": [
            "perceptual conformance is not scientific correctness",
            "agent consensus is not authorship or submission authorization",
            (
                "distinct observer metadata is evidence of declared separation, "
                "not cryptographic proof of model independence"
            ),
        ],
    }


def combine_carrier_and_perceptual(
    carrier_evaluation: dict[str, Any],
    perceptual_evaluation: dict[str, Any],
) -> dict[str, Any]:
    """Combine deterministic carrier evaluation with perceptual conformance.

    The legacy HUMAN_PERCEPTUAL_SIGNOFF gate is superseded only when the
    perceptual evaluator reaches PASS_AGENT_ENSEMBLE.
    """

    if carrier_evaluation.get("machineStanding") != "PASS":
        standing = "FAIL"
    else:
        perceptual = perceptual_evaluation.get("standing")
        if perceptual == "PASS_AGENT_ENSEMBLE":
            standing = "PASS"
        elif perceptual == "FAIL":
            standing = "FAIL"
        else:
            standing = "ESCALATE_SPECIALIST"

    legacy_human = carrier_evaluation.get("humanGates", [])
    unsupported = [x for x in legacy_human if x != "HUMAN_PERCEPTUAL_SIGNOFF"]
    if standing == "PASS" and unsupported:
        standing = "PENDING_HUMAN_AUTHORITY"

    return {
        "schemaVersion": 1,
        "kind": "publication-release-conformance",
        "carrierSha256": perceptual_evaluation["carrierSha256"],
        "machineStanding": carrier_evaluation.get("machineStanding"),
        "perceptualStanding": perceptual_evaluation.get("standing"),
        "standing": standing,
        "supersededLegacyGates": (
            ["HUMAN_PERCEPTUAL_SIGNOFF"]
            if perceptual_evaluation.get("standing") == "PASS_AGENT_ENSEMBLE"
            and "HUMAN_PERCEPTUAL_SIGNOFF" in legacy_human
            else []
        ),
        "remainingHumanAuthorityGates": unsupported,
    }
