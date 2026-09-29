from __future__ import annotations

import pytest

from ordivon_agent.work_reattachment_r1 import (
    WorkDiscoveryNotFound,
    WorkReattachmentCoordinator,
    WorkReattachmentError,
    WorkReattachmentRequest,
    WorkReattachmentStanding,
)


def detail(
    work_ref: str,
    *,
    work_kind: str = "social-work-fabric-r2-release",
    actor: str = "actor:agent:social-r2",
    objective: str = "release Social Work Fabric R2",
    refs: tuple[str, ...] = ("git:e8fb",),
):
    return {
        "workRef": work_ref,
        "workKind": work_kind,
        "state": "open",
        "revision": 2,
        "writerActorRef": actor,
        "createdByActorRef": actor,
        "snapshot": {"objective": objective, "referenceRefs": list(refs)},
    }


class FakePort:
    def __init__(self, details, *, has_more=False):
        self.details = dict(details)
        self.has_more = has_more
        self.get_calls = []
        self.list_calls = []

    def get_work(self, work_ref):
        self.get_calls.append(work_ref)
        try:
            return self.details[work_ref]
        except KeyError:
            raise WorkDiscoveryNotFound(work_ref) from None

    def list_works(self, *, state, limit):
        self.list_calls.append((state, limit))
        return {
            "works": [
                {
                    "workRef": value["workRef"],
                    "workKind": value["workKind"],
                    "state": value["state"],
                    "revision": value["revision"],
                }
                for value in self.details.values()
            ][:limit],
            "hasMore": self.has_more,
        }


def request(**overrides):
    values = {
        "work_kind": "social-work-fabric-r2-release",
        "actor_ref": "actor:agent:social-r2",
        "objective": "release Social Work Fabric R2",
        "reference_refs": ("git:e8fb",),
    }
    values.update(overrides)
    return WorkReattachmentRequest(**values)


def test_exact_work_ref_wins_without_inventory_scan():
    canonical = "work:social-work-fabric-r2-release:r1:20260928"
    port = FakePort({canonical: detail(canonical)})
    result = WorkReattachmentCoordinator(port).resolve(request(exact_work_ref=canonical))
    assert result.standing is WorkReattachmentStanding.REATTACH
    assert result.canonical_work_ref == canonical
    assert result.exact_lookup_found is True
    assert port.list_calls == []
    assert result.automatic_creation_allowed is False
    assert result.automatic_merge_allowed is False
    assert result.physical_revalidation_required is True


def test_wrong_guessed_ref_discovers_unique_canonical_work_instead_of_creating():
    stale_guess = "work:social-work-fabric-r2:20260928"
    canonical = "work:social-work-fabric-r2-release:r1:20260928"
    port = FakePort({canonical: detail(canonical)})
    result = WorkReattachmentCoordinator(port).resolve(request(exact_work_ref=stale_guess))
    assert result.standing is WorkReattachmentStanding.REATTACH
    assert result.canonical_work_ref == canonical
    assert result.exact_lookup_attempted is True
    assert result.exact_lookup_found is False
    assert result.automatic_creation_allowed is False
    assert port.get_calls[0] == stale_guess


def test_multiple_exact_field_candidates_fail_closed_as_ambiguous():
    first = "work:social-r2:a"
    second = "work:social-r2:b"
    port = FakePort({first: detail(first), second: detail(second)})
    result = WorkReattachmentCoordinator(port).resolve(request())
    assert result.standing is WorkReattachmentStanding.AMBIGUOUS
    assert result.canonical_work_ref is None
    assert result.candidate_work_refs == (first, second)
    assert result.automatic_creation_allowed is False
    assert result.automatic_merge_allowed is False


def test_no_candidate_does_not_authorize_work_creation():
    port = FakePort({"work:other": detail("work:other", objective="another objective")})
    result = WorkReattachmentCoordinator(port).resolve(request())
    assert result.standing is WorkReattachmentStanding.NOT_FOUND
    assert result.canonical_work_ref is None
    assert result.automatic_creation_allowed is False


def test_incomplete_inventory_never_claims_unique_match():
    canonical = "work:social-r2:only-visible-page"
    port = FakePort({canonical: detail(canonical)}, has_more=True)
    result = WorkReattachmentCoordinator(port).resolve(request(discovery_limit=1))
    assert result.standing is WorkReattachmentStanding.DISCOVERY_INCOMPLETE
    assert result.canonical_work_ref is None
    assert result.candidate_work_refs == (canonical,)
    assert result.discovery_complete is False


def test_reference_refs_and_actor_are_exact_filters_not_fuzzy_ranking():
    wrong_ref = "work:social-r2:wrong-ref"
    wrong_actor = "work:social-r2:wrong-actor"
    right = "work:social-r2:right"
    port = FakePort(
        {
            wrong_ref: detail(wrong_ref, refs=("git:other",)),
            wrong_actor: detail(wrong_actor, actor="actor:agent:other"),
            right: detail(right),
        }
    )
    result = WorkReattachmentCoordinator(port).resolve(request())
    assert result.standing is WorkReattachmentStanding.REATTACH
    assert result.canonical_work_ref == right


def test_malformed_host_projection_fails_closed():
    port = FakePort({})
    port.list_works = lambda **kwargs: {"works": "not-a-list", "hasMore": False}
    with pytest.raises(WorkReattachmentError, match="omitted works"):
        WorkReattachmentCoordinator(port).resolve(request())
