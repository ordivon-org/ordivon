from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
import sys
from typing import Iterable

R10_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = R10_ROOT.parents[2]
R1_ROOT = REPO_ROOT / "studies" / "security" / "ai-redteam-foundry-r1"
R4_ROOT = REPO_ROOT / "studies" / "security" / "ai-redteam-foundry-r4"
R8_ROOT = REPO_ROOT / "studies" / "security" / "ai-redteam-foundry-r8"
R9_ROOT = REPO_ROOT / "studies" / "security" / "ai-redteam-foundry-r9"
for root in (R1_ROOT, R4_ROOT, R8_ROOT, R9_ROOT):
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))

from foundry.providers import ProviderArtifactRef  # noqa: E402
from foundry_r4 import canonical_digest  # noqa: E402
from foundry_r8 import AttackSearchRunSpec, SearchResultRef  # noqa: E402
from foundry_r9 import DiscoveryFrontier, FamilyLedgerEntry, VulnerabilityFamilyLedger  # noqa: E402

_DIGEST_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
_PHASES = ("original_replay", "family_mutation", "defense_aware_reattack")
_STANDINGS = frozenset({"PASS", "FAIL", "INCOMPLETE"})


def _text(value: str, label: str) -> str:
    if not isinstance(value, str) or not value or value != value.strip():
        raise ValueError(f"{label} must be non-empty canonical text")
    return value


def _digest(value: str, label: str) -> str:
    _text(value, label)
    if _DIGEST_RE.fullmatch(value) is None:
        raise ValueError(f"{label} must be sha256:<64 lowercase hex>")
    return value


@dataclass(frozen=True, slots=True)
class PatchBinding:
    patch_id: str
    patch_owner: str
    patch_artifact_digest: str
    target_before_id: str
    target_before_digest: str
    target_after_id: str
    target_after_digest: str

    def __post_init__(self) -> None:
        for value, label in (
            (self.patch_id, "patch id"),
            (self.patch_owner, "patch owner"),
            (self.target_before_id, "target before id"),
            (self.target_after_id, "target after id"),
        ):
            _text(value, label)
        for value, label in (
            (self.patch_artifact_digest, "patch artifact digest"),
            (self.target_before_digest, "target before digest"),
            (self.target_after_digest, "target after digest"),
        ):
            _digest(value, label)
        if self.target_before_digest == self.target_after_digest:
            raise ValueError("patch binding must identify a changed target state")

    @property
    def digest(self) -> str:
        return canonical_digest(self.to_dict())

    def to_dict(self) -> dict[str, str]:
        return {
            "patchId": self.patch_id,
            "patchOwner": self.patch_owner,
            "patchArtifactDigest": self.patch_artifact_digest,
            "targetBeforeId": self.target_before_id,
            "targetBeforeDigest": self.target_before_digest,
            "targetAfterId": self.target_after_id,
            "targetAfterDigest": self.target_after_digest,
        }


@dataclass(frozen=True, slots=True)
class RegressionSearchPhase:
    phase: str
    search_run_digest: str
    target_after_id: str
    target_after_digest: str
    provider_completion_digest: str
    review_evidence_digest: str
    expected_candidate_count: int
    observed_result_count: int
    coverage_complete: bool
    review_complete: bool
    family_ledger_digest: str
    discovery_frontier_digest: str
    observed_family_ids: tuple[str, ...]
    unassigned_provider_positive_count: int

    def __post_init__(self) -> None:
        if self.phase not in _PHASES:
            raise ValueError(f"phase must be one of {_PHASES}")
        _text(self.target_after_id, "target after id")
        for value, label in (
            (self.search_run_digest, "search run digest"),
            (self.target_after_digest, "target after digest"),
            (self.provider_completion_digest, "provider completion digest"),
            (self.review_evidence_digest, "review evidence digest"),
            (self.family_ledger_digest, "family ledger digest"),
            (self.discovery_frontier_digest, "discovery frontier digest"),
        ):
            _digest(value, label)
        for label, value in (
            ("expected candidate count", self.expected_candidate_count),
            ("observed result count", self.observed_result_count),
            ("unassigned provider-positive count", self.unassigned_provider_positive_count),
        ):
            if not isinstance(value, int) or value < 0:
                raise ValueError(f"{label} must be a non-negative integer")
        if self.expected_candidate_count < 1:
            raise ValueError("expected candidate count must be >= 1")
        if self.observed_result_count > self.expected_candidate_count:
            raise ValueError("observed results cannot exceed the committed candidate count")
        if self.coverage_complete and self.observed_result_count != self.expected_candidate_count:
            raise ValueError("complete search coverage requires the exact committed candidate count")
        if self.unassigned_provider_positive_count > self.observed_result_count:
            raise ValueError("unassigned provider-positive count cannot exceed observed results")
        if self.phase == "original_replay" and self.expected_candidate_count != 1:
            raise ValueError("original replay must bind exactly one replay candidate")
        families = tuple(sorted(set(self.observed_family_ids)))
        for family_id in families:
            _text(family_id, "observed family id")
        object.__setattr__(self, "observed_family_ids", families)

    @property
    def standing(self) -> str:
        if not self.coverage_complete or not self.review_complete or self.unassigned_provider_positive_count:
            return "INCOMPLETE"
        if self.observed_family_ids:
            return "FAIL"
        return "PASS"

    @property
    def digest(self) -> str:
        return canonical_digest(self.to_dict())

    def to_dict(self) -> dict[str, object]:
        return {
            "phase": self.phase,
            "searchRunDigest": self.search_run_digest,
            "targetAfterId": self.target_after_id,
            "targetAfterDigest": self.target_after_digest,
            "providerCompletionDigest": self.provider_completion_digest,
            "reviewEvidenceDigest": self.review_evidence_digest,
            "expectedCandidateCount": self.expected_candidate_count,
            "observedResultCount": self.observed_result_count,
            "coverageComplete": self.coverage_complete,
            "reviewComplete": self.review_complete,
            "familyLedgerDigest": self.family_ledger_digest,
            "discoveryFrontierDigest": self.discovery_frontier_digest,
            "observedFamilyIds": list(self.observed_family_ids),
            "unassignedProviderPositiveCount": self.unassigned_provider_positive_count,
            "standing": self.standing,
        }


@dataclass(frozen=True, slots=True)
class UtilityEvaluationRef:
    suite_id: str
    target_after_id: str
    target_after_digest: str
    case_count: int
    failed_case_count: int
    complete: bool
    artifact_ref: ProviderArtifactRef

    def __post_init__(self) -> None:
        _text(self.suite_id, "utility suite id")
        _text(self.target_after_id, "utility target id")
        _digest(self.target_after_digest, "utility target digest")
        for label, value in (("case count", self.case_count), ("failed case count", self.failed_case_count)):
            if not isinstance(value, int) or value < 0:
                raise ValueError(f"{label} must be a non-negative integer")
        if self.failed_case_count > self.case_count:
            raise ValueError("failed utility cases cannot exceed total cases")
        if self.complete and self.case_count < 1:
            raise ValueError("complete utility evaluation requires at least one case")
        _digest(self.artifact_ref.artifact_digest, "utility artifact digest")

    @property
    def standing(self) -> str:
        if not self.complete:
            return "INCOMPLETE"
        if self.failed_case_count:
            return "FAIL"
        return "PASS"

    @property
    def digest(self) -> str:
        return canonical_digest(self.to_dict())

    def to_dict(self) -> dict[str, object]:
        return {
            "suiteId": self.suite_id,
            "targetAfterId": self.target_after_id,
            "targetAfterDigest": self.target_after_digest,
            "caseCount": self.case_count,
            "failedCaseCount": self.failed_case_count,
            "complete": self.complete,
            "standing": self.standing,
            "artifactRef": {
                "provider": self.artifact_ref.provider,
                "providerVersion": self.artifact_ref.provider_version,
                "artifactKind": self.artifact_ref.artifact_kind,
                "artifactDigest": self.artifact_ref.artifact_digest,
                "byteLength": self.artifact_ref.byte_length,
                "sourcePath": self.artifact_ref.source_path,
            },
        }


@dataclass(frozen=True, slots=True)
class AdaptiveRegressionReceipt:
    source_family_id: str
    source_family_entry_digest: str
    source_hypothesis_digest: str
    source_family_ledger_digest: str
    patch: PatchBinding
    phases: tuple[RegressionSearchPhase, ...]
    utility: UtilityEvaluationRef

    def __post_init__(self) -> None:
        _text(self.source_family_id, "source family id")
        for value, label in (
            (self.source_family_entry_digest, "source family entry digest"),
            (self.source_hypothesis_digest, "source hypothesis digest"),
            (self.source_family_ledger_digest, "source family ledger digest"),
        ):
            _digest(value, label)
        phases = tuple(self.phases)
        names = [phase.phase for phase in phases]
        if sorted(names) != sorted(_PHASES) or len(names) != len(_PHASES):
            raise ValueError("adaptive regression receipt requires exactly one of each regression search phase")
        phases = tuple(sorted(phases, key=lambda item: _PHASES.index(item.phase)))
        for phase in phases:
            if phase.target_after_id != self.patch.target_after_id or phase.target_after_digest != self.patch.target_after_digest:
                raise ValueError("regression phase target does not match patch target-after identity")
        if self.utility.target_after_id != self.patch.target_after_id or self.utility.target_after_digest != self.patch.target_after_digest:
            raise ValueError("utility evaluation target does not match patch target-after identity")
        object.__setattr__(self, "phases", phases)

    @property
    def residual_family_ids(self) -> tuple[str, ...]:
        return tuple(sorted({family_id for phase in self.phases for family_id in phase.observed_family_ids}))

    @property
    def standing(self) -> str:
        standings = [phase.standing for phase in self.phases] + [self.utility.standing]
        if "INCOMPLETE" in standings:
            return "INCOMPLETE"
        if "FAIL" in standings:
            return "FAIL"
        return "PASS"

    @property
    def evidence_digest(self) -> str:
        return canonical_digest(
            {
                "sourceFamilyEntryDigest": self.source_family_entry_digest,
                "sourceFamilyLedgerDigest": self.source_family_ledger_digest,
                "patchDigest": self.patch.digest,
                "phaseDigests": [phase.digest for phase in self.phases],
                "utilityDigest": self.utility.digest,
            }
        )

    @property
    def digest(self) -> str:
        return canonical_digest(self.to_dict())

    def to_dict(self) -> dict[str, object]:
        return {
            "schemaVersion": 1,
            "kind": "ordivon.ai-redteam-adaptive-regression-receipt",
            "sourceFamilyId": self.source_family_id,
            "sourceFamilyEntryDigest": self.source_family_entry_digest,
            "sourceHypothesisDigest": self.source_hypothesis_digest,
            "sourceFamilyLedgerDigest": self.source_family_ledger_digest,
            "patch": self.patch.to_dict(),
            "phases": [phase.to_dict() for phase in self.phases],
            "utility": self.utility.to_dict(),
            "residualFamilyIds": list(self.residual_family_ids),
            "standing": self.standing,
            "evidenceDigest": self.evidence_digest,
        }


def bind_search_phase(
    *,
    phase: str,
    run: AttackSearchRunSpec,
    results: Iterable[SearchResultRef],
    family_ledger: VulnerabilityFamilyLedger,
    frontier: DiscoveryFrontier,
    patch: PatchBinding,
    provider_completion_digest: str,
    review_evidence_digest: str,
    expected_candidate_count: int,
    coverage_complete: bool,
    review_complete: bool,
) -> RegressionSearchPhase:
    _digest(provider_completion_digest, "provider completion digest")
    _digest(review_evidence_digest, "review evidence digest")
    if run.target_id != patch.target_after_id:
        raise ValueError("R8 search target id does not match the patched target")
    rows = tuple(results)
    if any(item.candidate.search_run_digest != run.digest for item in rows):
        raise ValueError("R8 result belongs to a different search run")
    result_digests = tuple(sorted(item.digest for item in rows))
    if tuple(sorted(family_ledger.input_result_digests)) != result_digests:
        raise ValueError("R9 family ledger is not bound to the exact R8 result set")
    if frontier.search_run_digest != run.digest:
        raise ValueError("R9 discovery frontier belongs to a different R8 search run")
    if len(frontier.points) != len(rows):
        raise ValueError("R9 discovery frontier does not cover the exact observed result count")
    if expected_candidate_count > run.budget.max_candidates:
        raise ValueError("regression phase expectation exceeds the R8 committed candidate budget")
    if phase == "original_replay" and run.control.adaptivity != "fixed_sequence":
        raise ValueError("original replay must use a fixed-sequence R8 search run")

    entries_by_family = {entry.family_id: entry for entry in family_ledger.entries}
    if len(entries_by_family) != len(family_ledger.entries):
        raise ValueError("R9 family ledger contains duplicate family ids")
    observed_families = tuple(sorted(entries_by_family))
    unassigned = set(family_ledger.unassigned_result_digests)
    positive_unassigned = sum(item.provider_positive is True and item.digest in unassigned for item in rows)

    return RegressionSearchPhase(
        phase=phase,
        search_run_digest=run.digest,
        target_after_id=patch.target_after_id,
        target_after_digest=patch.target_after_digest,
        provider_completion_digest=provider_completion_digest,
        review_evidence_digest=review_evidence_digest,
        expected_candidate_count=expected_candidate_count,
        observed_result_count=len(rows),
        coverage_complete=coverage_complete,
        review_complete=review_complete,
        family_ledger_digest=family_ledger.digest,
        discovery_frontier_digest=frontier.digest,
        observed_family_ids=observed_families,
        unassigned_provider_positive_count=positive_unassigned,
    )


def build_regression_receipt(
    *,
    source_family_entry: FamilyLedgerEntry,
    source_family_ledger: VulnerabilityFamilyLedger,
    patch: PatchBinding,
    phases: Iterable[RegressionSearchPhase],
    utility: UtilityEvaluationRef,
) -> AdaptiveRegressionReceipt:
    matching = [entry for entry in source_family_ledger.entries if entry.family_id == source_family_entry.family_id]
    if len(matching) != 1 or matching[0].digest != source_family_entry.digest:
        raise ValueError("source family entry is not the exact entry committed by the supplied R9 ledger")
    return AdaptiveRegressionReceipt(
        source_family_id=source_family_entry.family_id,
        source_family_entry_digest=source_family_entry.digest,
        source_hypothesis_digest=source_family_entry.hypothesis.digest,
        source_family_ledger_digest=source_family_ledger.digest,
        patch=patch,
        phases=tuple(phases),
        utility=utility,
    )
