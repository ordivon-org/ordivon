from __future__ import annotations

import json
from functools import wraps

from mcp.server.mcpserver.exceptions import ToolError
from psycopg_pool import PoolTimeout, TooManyRequests
from pydantic import ValidationError

from .errors import ActorRefNotFound, ConflictError, WorkNotFound
from .social_errors import MessageNotFound, SpaceNotFound, TopicNotFound


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
    elif isinstance(exc, ValueError):
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
            ValueError,
        ) as exc:
            raise ToolError(
                json.dumps(_domain_error_payload(exc), sort_keys=True, separators=(",", ":"))
            ) from None

    return wrapped
