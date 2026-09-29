from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Any, Protocol


class WorkDiscoveryNotFound(LookupError):
    """Adapter-normalized Host NOT_FOUND for one exact WorkRef."""


class WorkReattachmentError(RuntimeError):
    pass


class WorkReattachmentStanding(StrEnum):
    REATTACH = "reattach"
    NOT_FOUND = "not-found"
    AMBIGUOUS = "ambiguous"
    DISCOVERY_INCOMPLETE = "discovery-incomplete"


class HostWorkDiscoveryPort(Protocol):
    """Read-only Host Work discovery. Implementations must not create or mutate Work."""

    def get_work(self, work_ref: str) -> dict[str, Any]: ...

    def list_works(self, *, state: str, limit: int) -> dict[str, Any]: ...


@dataclass(frozen=True, slots=True)
class WorkReattachmentRequest:
    # Supply only a WorkRef recovered from durable evidence (Host/handoff/reference), never a model guess.
    exact_work_ref: str | None = None
    work_kind: str | None = None
    actor_ref: str | None = None
    objective: str | None = None
    reference_refs: tuple[str, ...] = ()
    discovery_limit: int = 200

    def __post_init__(self) -> None:
        for value, label in (
            (self.exact_work_ref, "exact WorkRef"),
            (self.work_kind, "Work kind"),
            (self.actor_ref, "actor reference"),
            (self.objective, "objective"),
        ):
            if value is not None and (not value or value != value.strip()):
                raise ValueError(f"{label} must be non-empty and trimmed when supplied")
        if not 1 <= self.discovery_limit <= 200:
            raise ValueError("discovery_limit must be in [1,200]")
        if len(self.reference_refs) != len(set(self.reference_refs)):
            raise ValueError("reference_refs must be unique")
        if any(not ref or ref != ref.strip() for ref in self.reference_refs):
            raise ValueError("reference_refs must contain non-empty trimmed values")


@dataclass(frozen=True, slots=True)
class WorkReattachmentResult:
    standing: WorkReattachmentStanding
    canonical_work_ref: str | None
    candidate_work_refs: tuple[str, ...]
    exact_lookup_attempted: bool
    exact_lookup_found: bool
    discovery_complete: bool
    physical_revalidation_required: bool = True
    automatic_creation_allowed: bool = False
    automatic_merge_allowed: bool = False


class WorkReattachmentCoordinator:
    """Recover Host semantic identity without inventing Work from stale conversation state.

    Exact WorkRef remains strongest. If that lookup misses, discovery is deterministic and
    exact-field based: no fuzzy ranking, no chat-transcript authority, no auto-create/merge.
    Host observations navigate continuity only; present-tense Git/Runtime/provider truth must
    still be revalidated at its natural owner after reattachment.
    """

    def __init__(self, port: HostWorkDiscoveryPort) -> None:
        self.port = port

    def resolve(self, request: WorkReattachmentRequest) -> WorkReattachmentResult:
        attempted = request.exact_work_ref is not None
        if request.exact_work_ref is not None:
            # Exact means evidence-bound identity. Guessed refs belong in discovery filters, not here.
            try:
                exact = self.port.get_work(request.exact_work_ref)
            except WorkDiscoveryNotFound:
                exact = None
            if exact is not None:
                work_ref = self._work_ref(exact)
                if work_ref != request.exact_work_ref:
                    raise WorkReattachmentError("exact Work lookup changed identity")
                return WorkReattachmentResult(
                    standing=WorkReattachmentStanding.REATTACH,
                    canonical_work_ref=work_ref,
                    candidate_work_refs=(work_ref,),
                    exact_lookup_attempted=True,
                    exact_lookup_found=True,
                    discovery_complete=True,
                )

        inventory = self.port.list_works(state="open", limit=request.discovery_limit)
        rows = inventory.get("works")
        if not isinstance(rows, list):
            raise WorkReattachmentError("Host Work inventory omitted works")
        has_more = inventory.get("hasMore")
        if type(has_more) is not bool:
            raise WorkReattachmentError("Host Work inventory omitted hasMore")

        details: list[dict[str, Any]] = []
        for row in rows:
            if not isinstance(row, dict):
                raise WorkReattachmentError("Host Work inventory contains a non-object row")
            work_ref = self._work_ref(row)
            if request.work_kind is not None and row.get("workKind") != request.work_kind:
                continue
            try:
                detail = self.port.get_work(work_ref)
            except WorkDiscoveryNotFound:
                # Point-in-time inventory can race a terminal/removal projection; do not invent.
                continue
            if self._matches(detail, request):
                details.append(detail)
                if len(details) >= 2:
                    break

        refs = tuple(sorted(self._work_ref(item) for item in details))
        if len(refs) >= 2:
            return WorkReattachmentResult(
                standing=WorkReattachmentStanding.AMBIGUOUS,
                canonical_work_ref=None,
                candidate_work_refs=refs,
                exact_lookup_attempted=attempted,
                exact_lookup_found=False,
                discovery_complete=not has_more,
            )
        if has_more:
            return WorkReattachmentResult(
                standing=WorkReattachmentStanding.DISCOVERY_INCOMPLETE,
                canonical_work_ref=None,
                candidate_work_refs=refs,
                exact_lookup_attempted=attempted,
                exact_lookup_found=False,
                discovery_complete=False,
            )
        if len(refs) == 1:
            return WorkReattachmentResult(
                standing=WorkReattachmentStanding.REATTACH,
                canonical_work_ref=refs[0],
                candidate_work_refs=refs,
                exact_lookup_attempted=attempted,
                exact_lookup_found=False,
                discovery_complete=True,
            )
        return WorkReattachmentResult(
            standing=WorkReattachmentStanding.NOT_FOUND,
            canonical_work_ref=None,
            candidate_work_refs=(),
            exact_lookup_attempted=attempted,
            exact_lookup_found=False,
            discovery_complete=True,
        )

    @staticmethod
    def _work_ref(value: dict[str, Any]) -> str:
        work_ref = value.get("workRef")
        if not isinstance(work_ref, str) or not work_ref or work_ref != work_ref.strip():
            raise WorkReattachmentError("Host Work projection omitted a valid WorkRef")
        return work_ref

    @staticmethod
    def _matches(value: dict[str, Any], request: WorkReattachmentRequest) -> bool:
        if request.work_kind is not None and value.get("workKind") != request.work_kind:
            return False
        if request.actor_ref is not None and request.actor_ref not in {
            value.get("createdByActorRef"),
            value.get("writerActorRef"),
        }:
            return False
        snapshot = value.get("snapshot")
        if not isinstance(snapshot, dict):
            raise WorkReattachmentError("Host Work projection omitted snapshot")
        if request.objective is not None and snapshot.get("objective") != request.objective:
            return False
        if request.reference_refs:
            refs = snapshot.get("referenceRefs")
            if not isinstance(refs, list) or any(not isinstance(ref, str) for ref in refs):
                raise WorkReattachmentError("Host Work snapshot omitted valid referenceRefs")
            if not set(request.reference_refs).issubset(refs):
                return False
        return True


__all__ = [
    "HostWorkDiscoveryPort",
    "WorkDiscoveryNotFound",
    "WorkReattachmentCoordinator",
    "WorkReattachmentError",
    "WorkReattachmentRequest",
    "WorkReattachmentResult",
    "WorkReattachmentStanding",
]
