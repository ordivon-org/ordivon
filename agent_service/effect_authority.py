from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

from .delivery import (
    DeliveryReceipt,
    PolicyObservation,
    PolicyRequest,
    TransportBindingStore,
    _delivery_receipt_get_by_binding,
)
from .slice1 import ServiceEvent, ServiceEventStore


class EffectAuthorizedDeliveryCoordinator:
    """
    Guard only a new external effect attempt.

    Existing local delivery receipts replay without inventing a new authorization event.
    A frozen generic effect-authorization receipt survives retry of the same exact
    delivery_request_id; a new Binding/effect identity requires a new current decision.
    """

    def __init__(
        self,
        *,
        delegate: Any,
        bindings: TransportBindingStore,
        delegations: Any,
        events: ServiceEventStore,
        policy_adapter: Any | None,
    ) -> None:
        self._delegate = delegate
        self._bindings = bindings
        self._delegations = delegations
        self._events = events
        self._policy_adapter = policy_adapter

    def _authorization_receipt(self, binding_id: str) -> ServiceEvent:
        historical = self._events.list_for("EffectAuthorization", binding_id)
        if historical:
            if len(historical) != 1 or historical[0].event_type != "EffectAuthorizationEvaluated":
                raise RuntimeError("effect authorization receipt stream is malformed")
            event = historical[0]
            if event.payload.get("bindingId") != binding_id:
                raise RuntimeError("effect authorization receipt binding mismatch")
            return event

        if self._policy_adapter is None:
            raise RuntimeError("no policy provider configured for effect authorization")

        binding = self._bindings.get(binding_id)
        envelope = self._delegations.get(binding.delegation_id)
        request = PolicyRequest(
            delegation_id=envelope.id,
            session_id=envelope.session_id,
            task_id=envelope.task_id,
            source_identity_id=envelope.source_identity_id,
            source_instance_id=envelope.source_instance_id,
            target_identity_id=envelope.target_identity_id,
            target_revision_id=envelope.target_revision_id,
            capability_key=envelope.capability_key,
        )
        observation = self._policy_adapter.evaluate(request)
        if not isinstance(observation, PolicyObservation):
            raise TypeError("policy provider must return PolicyObservation")
        if not observation.policy_revision.strip():
            raise ValueError("PolicyObservation.policy_revision must be non-empty")
        permissions = tuple(dict.fromkeys(observation.granted_permissions))
        return self._events.append(
            "EffectAuthorization",
            binding.id,
            "EffectAuthorizationEvaluated",
            {
                "bindingId": binding.id,
                "delegationId": envelope.id,
                "allowed": bool(observation.allowed),
                "reason": observation.reason,
                "policyRevision": observation.policy_revision,
                "grantedPermissions": list(permissions),
            },
        )

    def deliver(self, binding_id: str) -> DeliveryReceipt:
        existing = _delivery_receipt_get_by_binding(self._events, binding_id, required=False)
        if existing is not None:
            return self._delegate.deliver(binding_id)

        decision = self._authorization_receipt(binding_id)
        if not bool(decision.payload.get("allowed")):
            raise PermissionError(
                decision.payload.get("reason") or "delivery effect denied by current policy"
            )
        return self._delegate.deliver(binding_id)


def _initialize_schema(connection: sqlite3.Connection) -> None:
    legacy_table = connection.execute(
        "SELECT 1 FROM sqlite_master "
        "WHERE type = 'table' AND name = 'effect_authorization_decisions'"
    ).fetchone()
    if legacy_table is not None:
        raise RuntimeError(
            "legacy effect_authorization_decisions schema is unsupported; "
            "perform explicit destructive migration before opening this revision"
        )
