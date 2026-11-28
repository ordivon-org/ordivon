from __future__ import annotations

import json
from functools import wraps

from mcp.server.mcpserver.exceptions import ToolError
from psycopg.errors import CheckViolation, SequenceGeneratorLimitExceeded
from psycopg_pool import PoolTimeout, TooManyRequests
from pydantic import ValidationError

from .errors import (
    ActorRefNotFound,
    ConflictError,
    InvalidArgumentError,
    WorkNotFound,
    WorkRevisionUnavailable,
)
from .social_errors import MessageNotFound, SpaceNotFound, TopicNotFound, TopicResumeCursorAhead


def _domain_error_payload(exc: Exception) -> dict[str, object]:
    payload: dict[str, object] = {
        "schemaVersion": 1,
        "kind": "ordivon.host-domain-error",
        "retryable": False,
    }
    if isinstance(exc, WorkNotFound):
        payload.update(
            code="NOT_FOUND",
            resourceKind="work",
            resourceRef=str(exc),
            suggestedAction="discover-before-create",
        )
    elif isinstance(exc, ActorRefNotFound):
        payload.update(
            code="NOT_FOUND",
            resourceKind="actor",
            resourceRef=str(exc),
            suggestedAction="inspect-owner-inventory",
        )
    elif isinstance(exc, SpaceNotFound):
        payload.update(
            code="NOT_FOUND",
            resourceKind="space",
            resourceRef=str(exc),
            suggestedAction="inspect-owner-inventory",
        )
    elif isinstance(exc, TopicNotFound):
        payload.update(
            code="NOT_FOUND",
            resourceKind="topic",
            resourceRef=str(exc),
            suggestedAction="inspect-owner-inventory",
        )
    elif isinstance(exc, MessageNotFound):
        payload.update(
            code="NOT_FOUND",
            resourceKind="message",
            resourceRef=str(exc),
            suggestedAction="inspect-owner-inventory",
        )
    elif isinstance(exc, WorkRevisionUnavailable):
        # CONFLICT and its original detail text remain compatible. Reason,
        # exact observed Work revision and differentiated recovery action
        # come from one PG transaction, not guessed history or foreign effects.
        action = {
            "revision_ahead_of_current": "reread-current-work-before-waiting-for-revision",
            "historical_snapshot_absent": "inspect-retention-and-archive-before-recovery",
            "current_snapshot_missing": "stop-current-work-consumption-and-check-host-integrity",
        }[exc.reason]
        payload.update(
            code="CONFLICT",
            detail=str(exc),
            reason=exc.reason,
            resourceKind="work",
            resourceRef=exc.work_ref,
            requestedRevision=exc.requested_revision,
            observedCurrentRevision=exc.current_revision,
            evidenceBoundary="same-transaction-host-work-and-snapshot-read",
            suggestedAction=action,
        )
    elif isinstance(exc, TopicResumeCursorAhead):
        # Keep the established CONFLICT family. Unlike a successful empty
        # Topic page, this observation disproves the supplied cursor's
        # membership in this Topic's present committed horizon.
        payload.update(
            code="CONFLICT",
            detail=str(exc),
            reason="topic_resume_cursor_ahead",
            resourceKind="topic",
            resourceRef=exc.topic_ref,
            requestedAfterSequence=exc.after_sequence,
            observedTopicHighSequence=exc.topic_high,
            evidenceBoundary="same-transaction-topic-message-horizon",
            suggestedAction="reread-topic-horizon-and-check-cursor-domain",
        )
    elif isinstance(exc, ConflictError):
        payload.update(
            code="CONFLICT",
            detail=str(exc),
            suggestedAction="reread-current-state-and-reconcile",
        )
    elif isinstance(exc, PoolTimeout):
        # Psycopg raises before a pooled connection is checked out. An Agent
        # can retry after bounded backoff without claiming an effect committed
        # or leaking the internal pool/DSN details.
        payload.update(
            code="DEADLINE_EXCEEDED",
            retryable=True,
            suggestedAction="retry-with-bounded-backoff",
        )
    elif isinstance(exc, TooManyRequests):
        payload.update(
            code="RESOURCE_EXHAUSTED",
            retryable=True,
            suggestedAction="retry-with-bounded-backoff",
        )
    elif isinstance(exc, ValidationError):
        payload.update(
            code="INVALID_ARGUMENT",
            issues=exc.errors(include_url=False, include_input=False),
            suggestedAction="correct-request",
        )
    elif isinstance(exc, InvalidArgumentError):
        payload.update(
            code="INVALID_ARGUMENT",
            detail=str(exc),
            suggestedAction="correct-request",
        )
    else:  # pragma: no cover - caller catches only the explicit domain set below.
        raise TypeError(f"unsupported domain error type: {type(exc).__name__}")
    return payload


def _project_domain_errors(func):
    """Map expected Host-domain rejection to MCP ToolError without hiding crashes."""

    @wraps(func)
    def wrapped(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except (CheckViolation, SequenceGeneratorLimitExceeded) as exc:
            # Do not turn unrelated SQL constraint failures into capacity errors.
            if isinstance(exc, CheckViolation) and (
                exc.diag.table_name != "swf_change_clock"
                or exc.diag.constraint_name != "swf_exact_change_clock"
            ):
                raise
            payload = {
                "schemaVersion": 1,
                "kind": "ordivon.host-domain-error",
                "code": "RESOURCE_EXHAUSTED",
                "retryable": False,
                "reason": "generated_coordinate_exhausted",
                "suggestedAction": "coordinate-owner-wire-version-migration",
            }
            raise ToolError(json.dumps(payload, sort_keys=True, separators=(",", ":"))) from None
        except (
            WorkNotFound,
            ActorRefNotFound,
            SpaceNotFound,
            TopicNotFound,
            MessageNotFound,
            ConflictError,
            PoolTimeout,
            TooManyRequests,
            ValidationError,
            InvalidArgumentError,
        ) as exc:
            raise ToolError(
                json.dumps(_domain_error_payload(exc), sort_keys=True, separators=(",", ":"))
            ) from None

    return wrapped
