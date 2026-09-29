from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
import sys
from typing import Iterable

R9_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = R9_ROOT.parents[2]
R4_ROOT = REPO_ROOT / "studies" / "security" / "ai-redteam-foundry-r4"
R8_ROOT = REPO_ROOT / "studies" / "security" / "ai-redteam-foundry-r8"
for root in (R4_ROOT, R8_ROOT):
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))

from foundry_r4 import canonical_digest  # noqa: E402
from foundry_r8 import SearchResultRef  # noqa: E402

_DIGEST_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
_ASSIGNMENT_METHODS = frozenset({"manual_analysis", "deterministic_rule", "external_clusterer"})


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
class FamilyHypothesis:
    hypothesis_id: str
    mechanism: str
    scope: str
    rationale_digest: str
    falsifier_digest: str

    def __post_init__(self) -> None:
        _text(self.hypothesis_id, "hypothesis id")
        _text(self.mechanism, "mechanism")
        _text(self.scope, "scope")
        _digest(self.rationale_digest, "rationale digest")
        _digest(self.falsifier_digest, "falsifier digest")

    @property
    def digest(self) -> str:
        return canonical_digest(self.to_dict())

    @property
    def family_id(self) -> str:
        return "family:" + self.digest.split(":", 1)[1][:24]

    def to_dict(self) -> dict[str, str]:
        return {
            "hypothesisId": self.hypothesis_id,
            "mechanism": self.mechanism,
            "scope": self.scope,
            "rationaleDigest": self.rationale_digest,
            "falsifierDigest": self.falsifier_digest,
        }


@dataclass(frozen=True, slots=True)
class FamilyAssignment:
    result_digest: str
    hypothesis_id: str
    method: str
    method_ref: str
    assignment_evidence_digest: str

    def __post_init__(self) -> None:
        _digest(self.result_digest, "result digest")
        _text(self.hypothesis_id, "hypothesis id")
        if self.method not in _ASSIGNMENT_METHODS:
            raise ValueError(f"assignment method must be one of {sorted(_ASSIGNMENT_METHODS)}")
        _text(self.method_ref, "method ref")
        _digest(self.assignment_evidence_digest, "assignment evidence digest")

    @property
    def digest(self) -> str:
        return canonical_digest(self.to_dict())

    def to_dict(self) -> dict[str, str]:
        return {
            "resultDigest": self.result_digest,
            "hypothesisId": self.hypothesis_id,
            "method": self.method,
            "methodRef": self.method_ref,
            "assignmentEvidenceDigest": self.assignment_evidence_digest,
        }


@dataclass(frozen=True, slots=True)
class FamilyLedgerEntry:
    family_id: str
    hypothesis: FamilyHypothesis
    member_result_digests: tuple[str, ...]
    providers: tuple[str, ...]
    provider_attack_families: tuple[str, ...]
    target_ids: tuple[str, ...]
    provider_positive_member_count: int
    observer_bound_member_count: int

    def __post_init__(self) -> None:
        _text(self.family_id, "family id")
        if self.family_id != self.hypothesis.family_id:
            raise ValueError("family id must be derived from the exact root-cause hypothesis")
        members = tuple(sorted(set(self.member_result_digests)))
        if not members:
            raise ValueError("family ledger entry requires at least one member")
        for digest in members:
            _digest(digest, "member result digest")
        object.__setattr__(self, "member_result_digests", members)
        object.__setattr__(self, "providers", tuple(sorted(set(self.providers))))
        object.__setattr__(self, "provider_attack_families", tuple(sorted(set(self.provider_attack_families))))
        object.__setattr__(self, "target_ids", tuple(sorted(set(self.target_ids))))
        for label, value in (
            ("provider positive member count", self.provider_positive_member_count),
            ("observer bound member count", self.observer_bound_member_count),
        ):
            if not isinstance(value, int) or value < 0 or value > len(members):
                raise ValueError(f"{label} is out of range")

    @property
    def digest(self) -> str:
        return canonical_digest(self.to_dict())

    def to_dict(self) -> dict[str, object]:
        return {
            "schemaVersion": 1,
            "kind": "ordivon.ai-redteam-vulnerability-family",
            "familyId": self.family_id,
            "hypothesis": self.hypothesis.to_dict(),
            "memberResultDigests": list(self.member_result_digests),
            "providers": list(self.providers),
            "providerAttackFamilies": list(self.provider_attack_families),
            "targetIds": list(self.target_ids),
            "providerPositiveMemberCount": self.provider_positive_member_count,
            "observerBoundMemberCount": self.observer_bound_member_count,
        }


@dataclass(frozen=True, slots=True)
class VulnerabilityFamilyLedger:
    entries: tuple[FamilyLedgerEntry, ...]
    input_result_digests: tuple[str, ...]
    assignment_digests: tuple[str, ...]
    unassigned_result_digests: tuple[str, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "entries", tuple(sorted(self.entries, key=lambda item: item.family_id)))
        for name in ("input_result_digests", "assignment_digests", "unassigned_result_digests"):
            values = tuple(sorted(set(getattr(self, name))))
            for digest in values:
                _digest(digest, name)
            object.__setattr__(self, name, values)

    @property
    def digest(self) -> str:
        return canonical_digest(self.to_dict())

    def to_dict(self) -> dict[str, object]:
        return {
            "schemaVersion": 1,
            "kind": "ordivon.ai-redteam-vulnerability-family-ledger",
            "entries": [entry.to_dict() for entry in self.entries],
            "inputResultDigests": list(self.input_result_digests),
            "assignmentDigests": list(self.assignment_digests),
            "unassignedResultDigests": list(self.unassigned_result_digests),
        }


@dataclass(frozen=True, slots=True)
class DiscoveryFrontierPoint:
    sequence: int
    candidate_digest: str
    newly_discovered_family_ids: tuple[str, ...]
    cumulative_family_ids: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "sequence": self.sequence,
            "candidateDigest": self.candidate_digest,
            "newlyDiscoveredFamilyIds": list(self.newly_discovered_family_ids),
            "cumulativeFamilyIds": list(self.cumulative_family_ids),
        }


@dataclass(frozen=True, slots=True)
class DiscoveryFrontier:
    search_run_digest: str
    points: tuple[DiscoveryFrontierPoint, ...]
    discovered_family_ids: tuple[str, ...]
    unassigned_result_count: int

    def __post_init__(self) -> None:
        _digest(self.search_run_digest, "search run digest")
        if not isinstance(self.unassigned_result_count, int) or self.unassigned_result_count < 0:
            raise ValueError("unassigned result count must be a non-negative integer")
        object.__setattr__(self, "discovered_family_ids", tuple(sorted(set(self.discovered_family_ids))))

    @property
    def digest(self) -> str:
        return canonical_digest(self.to_dict())

    def to_dict(self) -> dict[str, object]:
        return {
            "schemaVersion": 1,
            "kind": "ordivon.ai-redteam-discovery-frontier",
            "searchRunDigest": self.search_run_digest,
            "points": [point.to_dict() for point in self.points],
            "discoveredFamilyIds": list(self.discovered_family_ids),
            "unassignedResultCount": self.unassigned_result_count,
        }


def build_family_ledger(
    results: Iterable[SearchResultRef],
    hypotheses: Iterable[FamilyHypothesis],
    assignments: Iterable[FamilyAssignment],
) -> VulnerabilityFamilyLedger:
    result_rows = tuple(results)
    result_by_digest = {item.digest: item for item in result_rows}
    if len(result_by_digest) != len(result_rows):
        raise ValueError("duplicate R8 result digests are not allowed")

    hypothesis_rows = tuple(hypotheses)
    hypothesis_by_id = {item.hypothesis_id: item for item in hypothesis_rows}
    if len(hypothesis_by_id) != len(hypothesis_rows):
        raise ValueError("hypothesis ids must be unique")

    assignment_rows = tuple(assignments)
    assignment_by_result: dict[str, FamilyAssignment] = {}
    for assignment in assignment_rows:
        if assignment.result_digest not in result_by_digest:
            raise ValueError("family assignment references an unknown R8 result")
        if assignment.hypothesis_id not in hypothesis_by_id:
            raise ValueError("family assignment references an unknown root-cause hypothesis")
        if assignment.result_digest in assignment_by_result:
            raise ValueError("one R8 result cannot be assigned to multiple root-cause families")
        assignment_by_result[assignment.result_digest] = assignment

    grouped: dict[str, list[SearchResultRef]] = {}
    for result_digest, assignment in assignment_by_result.items():
        grouped.setdefault(assignment.hypothesis_id, []).append(result_by_digest[result_digest])

    entries: list[FamilyLedgerEntry] = []
    for hypothesis_id, members in grouped.items():
        hypothesis = hypothesis_by_id[hypothesis_id]
        entries.append(
            FamilyLedgerEntry(
                family_id=hypothesis.family_id,
                hypothesis=hypothesis,
                member_result_digests=tuple(item.digest for item in members),
                providers=tuple(item.candidate.provider for item in members),
                provider_attack_families=tuple(item.candidate.attack_family for item in members),
                target_ids=tuple(item.candidate.target_id for item in members),
                provider_positive_member_count=sum(item.provider_positive is True for item in members),
                observer_bound_member_count=sum(item.observation_digest is not None for item in members),
            )
        )

    unassigned = tuple(sorted(set(result_by_digest) - set(assignment_by_result)))
    return VulnerabilityFamilyLedger(
        entries=tuple(entries),
        input_result_digests=tuple(result_by_digest),
        assignment_digests=tuple(item.digest for item in assignment_rows),
        unassigned_result_digests=unassigned,
    )


def discovery_frontier(
    search_run_digest: str,
    results: Iterable[SearchResultRef],
    hypotheses: Iterable[FamilyHypothesis],
    assignments: Iterable[FamilyAssignment],
) -> DiscoveryFrontier:
    _digest(search_run_digest, "search run digest")
    rows = tuple(item for item in results if item.candidate.search_run_digest == search_run_digest)
    sequences = [item.candidate.sequence for item in rows]
    if len(sequences) != len(set(sequences)):
        raise ValueError("candidate sequence must be unique within one search run")
    rows = tuple(sorted(rows, key=lambda item: item.candidate.sequence))

    hypothesis_by_id = {item.hypothesis_id: item for item in hypotheses}
    assignment_by_result: dict[str, FamilyAssignment] = {}
    for assignment in assignments:
        if assignment.result_digest in assignment_by_result:
            raise ValueError("duplicate assignment for one result")
        assignment_by_result[assignment.result_digest] = assignment

    cumulative: set[str] = set()
    points: list[DiscoveryFrontierPoint] = []
    unassigned = 0
    for result in rows:
        assignment = assignment_by_result.get(result.digest)
        newly: tuple[str, ...] = ()
        if assignment is None:
            unassigned += 1
        else:
            try:
                family_id = hypothesis_by_id[assignment.hypothesis_id].family_id
            except KeyError as exc:
                raise ValueError("frontier assignment references unknown hypothesis") from exc
            if family_id not in cumulative:
                cumulative.add(family_id)
                newly = (family_id,)
        points.append(
            DiscoveryFrontierPoint(
                sequence=result.candidate.sequence,
                candidate_digest=result.candidate.digest,
                newly_discovered_family_ids=newly,
                cumulative_family_ids=tuple(sorted(cumulative)),
            )
        )
    return DiscoveryFrontier(
        search_run_digest=search_run_digest,
        points=tuple(points),
        discovered_family_ids=tuple(sorted(cumulative)),
        unassigned_result_count=unassigned,
    )
