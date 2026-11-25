"""Shared readiness evidence construction, independent of Owner I/O."""

from __future__ import annotations

import hashlib
import json
from typing import Any

from ..contracts import ReadinessCheck, ReadinessFact, ReadinessOwnerStatusWitness

OwnerObservation = tuple[dict[str, Any] | None, str | None]
OwnerConfiguration = tuple[bool, str | None]


def status_witness(
    owner_id: str,
    tool_name: str,
    *,
    configured: bool,
    observation: OwnerObservation,
) -> ReadinessOwnerStatusWitness:
    """Bind native result bytes without returning unchecked/sensitive Owner JSON."""
    response, _error = observation
    if not configured:
        return ReadinessOwnerStatusWitness(
            owner_id=owner_id,
            tool_name=tool_name,  # type: ignore[arg-type]
            disposition="skipped_unconfigured",
        )
    if response is None:
        return ReadinessOwnerStatusWitness(
            owner_id=owner_id,
            tool_name=tool_name,  # type: ignore[arg-type]
            disposition="no_result",
        )
    try:
        payload = json.dumps(
            response,
            sort_keys=True,
            allow_nan=False,
            ensure_ascii=False,
            separators=(",", ":"),
        ).encode("utf-8")
    except TypeError, ValueError, OverflowError, RecursionError:
        return ReadinessOwnerStatusWitness(
            owner_id=owner_id,
            tool_name=tool_name,  # type: ignore[arg-type]
            disposition="no_result",
        )
    return ReadinessOwnerStatusWitness(
        owner_id=owner_id,
        tool_name=tool_name,  # type: ignore[arg-type]
        disposition="response_received",
        payload_digest="sha256:" + hashlib.sha256(payload).hexdigest(),
        payload_bytes=len(payload),
    )


def _fact(owner_id: str, predicate: str, state: str, source: str) -> ReadinessFact:
    return ReadinessFact(
        owner_id=owner_id,
        predicate=predicate,
        state=state,  # type: ignore[arg-type]
        source=source,
    )


def _check(
    direction: str,
    owner_id: str,
    action: str,
    predicate: str,
    *,
    request: dict[str, Any] | None = None,
    effect: str = "read_only",
) -> ReadinessCheck:
    return ReadinessCheck(
        direction=direction,  # type: ignore[arg-type]
        owner_id=owner_id,
        action=action,
        expected_evidence=predicate,
        request=request,
        effect=effect,  # type: ignore[arg-type]
    )
