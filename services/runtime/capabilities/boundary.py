from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ActionContext:
    actor: str
    context: str
    reason: str
    idempotency_key: str


def require_action_context(action: str, action_context: ActionContext | None) -> ActionContext:
    if action_context is None:
        raise ValueError(f"{action} requires action context with actor, context, reason, and idempotency_key.")

    missing = [
        field_name
        for field_name in ("actor", "context", "reason", "idempotency_key")
        if not getattr(action_context, field_name, "").strip()
    ]
    if missing:
        raise ValueError(f"{action} missing required action context fields: {', '.join(missing)}")

    return action_context


def build_action_context(
    action: str,
    *,
    actor: str,
    context: str,
    reason: str,
    idempotency_key: str,
) -> ActionContext:
    return require_action_context(
        action,
        ActionContext(
            actor=actor,
            context=context,
            reason=reason,
            idempotency_key=idempotency_key,
        ),
    )
