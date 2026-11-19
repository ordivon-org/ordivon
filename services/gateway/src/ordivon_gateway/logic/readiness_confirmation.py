"""Pure comparison of two bounded reads from the SAME natural Owner.

A second Gateway status read can confirm stability or uncover changes.
It cannot prove a physical effect, a Principal grant or independent authority.
"""

from __future__ import annotations

from collections import defaultdict

from ..contracts import (
    CapabilityInquiryProjection,
    ReadinessFact,
    ReadinessFactChange,
    ReadinessInquiry,
    ReadinessProbeReceipt,
    ReadinessVerification,
)

_STATUS_PROBE_BY_CATEGORY = {
    "execution": "runtime.describe",
    "release": "runtime.describe",
    "artifact": "runtime.describe",
    "continuity": "host.status",
}
_RUNTIME_STATUS_REQUEST = {"schemaVersion": 1}
_HOST_STATUS_REQUEST = {"detail": "summary"}


def status_probe_owners(category: str, owner_id: str) -> tuple[str, ...]:
    """One read-only status tool per Owner; never infer an effect tool is safe."""
    if category == "artifact":
        return ("runtime.linux", "runtime.windows")
    if category in _STATUS_PROBE_BY_CATEGORY:
        return (owner_id,)
    return ()


def _fact_states(inquiry: ReadinessInquiry) -> dict[tuple[str, str, str], tuple[str, ...]]:
    groups: dict[tuple[str, str, str], list[str]] = defaultdict(list)
    for fact in inquiry.facts:
        groups[(fact.owner_id, fact.predicate, fact.source)].append(fact.state)
    return {key: tuple(sorted(values)) for key, values in groups.items()}


def _latest_fact(inquiry: ReadinessInquiry, owner_id: str, predicate: str) -> ReadinessFact | None:
    return next(
        (row for row in inquiry.facts if row.owner_id == owner_id and row.predicate == predicate),
        None,
    )


def _witness_digest(inquiry: ReadinessInquiry, owner_id: str) -> str | None:
    return next(
        (row.payload_digest for row in inquiry.observations if row.owner_id == owner_id),
        None,
    )


def _probe_result(inquiry: ReadinessInquiry, category: str, owner_id: str) -> str:
    config = _latest_fact(inquiry, owner_id, "gateway.owner_endpoint_qualified")
    if config is None or config.state != "supported":
        return "skipped_unconfigured"
    predicate = (
        "host.status_envelope_valid" if category == "continuity" else "owner.status_observed"
    )
    observed = _latest_fact(inquiry, owner_id, predicate)
    if observed is None or observed.state == "unobserved":
        return "no_result"
    if observed.state in {"invalid", "contradictory"}:
        return "invalid_result"
    if category != "continuity" and any(
        f.owner_id == owner_id and f.state in {"invalid", "contradictory"} for f in inquiry.facts
    ):
        return "invalid_result"
    return "result_observed"


def compare_readiness_observations(
    *,
    category: str,
    owner_id: str,
    initial: CapabilityInquiryProjection,
    latest: CapabilityInquiryProjection,
) -> ReadinessVerification:
    """Retain first full facts, changed predicates, and second-call status.

    This comparison never invents a response where a service read failed.
    It assumes a caller issued exactly one bounded status read round; do not
    call it to claim a probe ran without the capability adapter actually doing so.
    """
    if initial.capability != latest.capability or initial.owner_id != latest.owner_id:
        raise ValueError("readiness comparison requires the same exact capability and Owner")
    if initial.route_digest != latest.route_digest:
        raise ValueError("readiness comparison cannot bridge changed route contracts")

    first_states = _fact_states(initial.inquiry)
    last_states = _fact_states(latest.inquiry)
    keys = sorted(first_states.keys() | last_states.keys())
    changes = [
        ReadinessFactChange(
            owner_id=key[0],
            predicate=key[1],
            source=key[2],
            previous_states=list(first_states.get(key, ())),
            current_states=list(last_states.get(key, ())),
        )
        for key in keys
        if first_states.get(key, ()) != last_states.get(key, ())
    ]
    action = _STATUS_PROBE_BY_CATEGORY.get(category)
    receipts: list[ReadinessProbeReceipt] = []
    for current_owner in status_probe_owners(category, owner_id):
        # Capture the actual second status round without turning the receipt
        # into a pretense of a signed certificate or an execution result.
        outcome = _probe_result(latest.inquiry, category, current_owner)
        receipts.append(
            ReadinessProbeReceipt(
                owner_id=current_owner,
                action=action or "unknown",
                request=(
                    dict(_HOST_STATUS_REQUEST)
                    if action == "host.status"
                    else dict(_RUNTIME_STATUS_REQUEST)
                ),
                outcome=outcome,  # type: ignore[arg-type]
                execution_state=(
                    "not_executed" if outcome == "skipped_unconfigured" else "attempted_read_only"
                ),
                evidence_source="same_owner_status_second_observation",
                first_payload_digest=_witness_digest(initial.inquiry, current_owner),
                latest_payload_digest=_witness_digest(latest.inquiry, current_owner),
            )
        )

    if not receipts or all(row.execution_state == "not_executed" for row in receipts):
        verdict = "no_qualified_probe"
    elif (
        changes
        or initial.readiness_state != latest.readiness_state
        or any(
            receipt.first_payload_digest != receipt.latest_payload_digest for receipt in receipts
        )
    ):
        verdict = "changed_observation"
    elif any(row.outcome != "result_observed" for row in receipts):
        verdict = "still_unresolved"
    else:
        verdict = "same_owner_observation_stable"
    return ReadinessVerification(
        method="one_explicit_bounded_reobservation",
        initial_readiness_state=initial.readiness_state,
        initial_projection_digest=initial.projection_digest,
        latest_projection_digest=latest.projection_digest,
        initial_inquiry=initial.inquiry,
        receipts=receipts,
        fact_changes=changes,
        verdict=verdict,  # type: ignore[arg-type]
    )
