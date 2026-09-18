from __future__ import annotations

import json
import sqlite3
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .delivery import (
    DeliveryReceipt,
    PolicyAdapter,
    PolicyObservation,
    PolicyRequest,
    TransportBindingStore,
)
from .transport_credentials import AgentServiceR14


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex}"


def _now_ns() -> int:
    return time.time_ns()


def _canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


@dataclass(frozen=True)
class EffectAuthorizationDecision:
    """One frozen local authorization decision for one exact external delivery effect identity."""

    id: str
    binding_id: str
    delegation_id: str
    allowed: bool
    reason: str | None
    policy_revision: str
    granted_permissions: tuple[str, ...]
    created_at_ns: int


class EffectAuthorizationDecisionStore:
    """Durable exact effect-authorization snapshot, separate from route-time PolicyDecision."""

    def __init__(self, connection: sqlite3.Connection) -> None:
        self._connection = connection

    def get(self, decision_id: str) -> EffectAuthorizationDecision:
        row = self._connection.execute(
            "SELECT * FROM effect_authorization_decisions WHERE id = ?",
            (decision_id,),
        ).fetchone()
        if row is None:
            raise KeyError(decision_id)
        return self._from_row(row)

    def get_by_binding(
        self,
        binding_id: str,
        required: bool = True,
    ) -> EffectAuthorizationDecision | None:
        row = self._connection.execute(
            "SELECT * FROM effect_authorization_decisions WHERE binding_id = ?",
            (binding_id,),
        ).fetchone()
        if row is None:
            if required:
                raise KeyError(binding_id)
            return None
        return self._from_row(row)

    def create(
        self,
        *,
        binding_id: str,
        delegation_id: str,
        observation: PolicyObservation,
    ) -> EffectAuthorizationDecision:
        permissions = tuple(dict.fromkeys(observation.granted_permissions))
        value = EffectAuthorizationDecision(
            id=_id("eauth"),
            binding_id=binding_id,
            delegation_id=delegation_id,
            allowed=bool(observation.allowed),
            reason=observation.reason,
            policy_revision=observation.policy_revision,
            granted_permissions=permissions,
            created_at_ns=_now_ns(),
        )
        try:
            with self._connection:
                self._connection.execute(
                    """
                    INSERT INTO effect_authorization_decisions(
                        id,
                        binding_id,
                        delegation_id,
                        allowed,
                        reason,
                        policy_revision,
                        granted_permissions_json,
                        created_at_ns
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        value.id,
                        value.binding_id,
                        value.delegation_id,
                        1 if value.allowed else 0,
                        value.reason,
                        value.policy_revision,
                        _canonical_json(list(value.granted_permissions)),
                        value.created_at_ns,
                    ),
                )
        except sqlite3.IntegrityError:
            existing = self.get_by_binding(binding_id)
            if (
                existing.delegation_id,
                existing.allowed,
                existing.reason,
                existing.policy_revision,
                existing.granted_permissions,
            ) != (
                value.delegation_id,
                value.allowed,
                value.reason,
                value.policy_revision,
                value.granted_permissions,
            ):
                raise RuntimeError(
                    "effect authorization identity raced with a different decision"
                ) from None
            return existing
        return value

    @staticmethod
    def _from_row(row: sqlite3.Row) -> EffectAuthorizationDecision:
        return EffectAuthorizationDecision(
            id=row["id"],
            binding_id=row["binding_id"],
            delegation_id=row["delegation_id"],
            allowed=bool(row["allowed"]),
            reason=row["reason"],
            policy_revision=row["policy_revision"],
            granted_permissions=tuple(json.loads(row["granted_permissions_json"])),
            created_at_ns=row["created_at_ns"],
        )


class EffectAuthorizationCoordinator:
    """
    Authorize one exact delivery effect immediately before its first external attempt.

    The resulting decision is frozen to the immutable TransportBinding/effect identity.
    It is intentionally distinct from route-time policy and from SemanticSession lifetime.
    """

    def __init__(
        self,
        *,
        bindings: TransportBindingStore,
        delegations: Any,
        records: EffectAuthorizationDecisionStore,
        policy_adapter: PolicyAdapter | None,
    ) -> None:
        self._bindings = bindings
        self._delegations = delegations
        self._records = records
        self._policy_adapter = policy_adapter

    def authorize(self, binding_id: str) -> EffectAuthorizationDecision:
        existing = self._records.get_by_binding(binding_id, required=False)
        if existing is not None:
            return existing
        if self._policy_adapter is None:
            raise RuntimeError("no PolicyAdapter configured for effect authorization")

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
            raise TypeError("PolicyAdapter must return PolicyObservation")
        if not observation.policy_revision.strip():
            raise ValueError("PolicyObservation.policy_revision must be non-empty")
        return self._records.create(
            binding_id=binding.id,
            delegation_id=envelope.id,
            observation=observation,
        )


class EffectAuthorizedDeliveryCoordinator:
    """
    Guard only a new external effect attempt.

    Existing local receipts are replayed without inventing a new authorization event.
    A frozen effect-authorization decision survives retry of the same exact
    delivery_request_id; a new Binding/effect identity requires a new current decision.
    """

    def __init__(
        self,
        *,
        delegate: Any,
        receipts: Any,
        authorizations: EffectAuthorizationCoordinator,
    ) -> None:
        self._delegate = delegate
        self._receipts = receipts
        self._authorizations = authorizations

    def deliver(self, binding_id: str) -> DeliveryReceipt:
        existing = self._receipts.get_by_binding(binding_id, required=False)
        if existing is not None:
            return self._delegate.deliver(binding_id)

        decision = self._authorizations.authorize(binding_id)
        if not decision.allowed:
            raise PermissionError(decision.reason or "delivery effect denied by current policy")
        return self._delegate.deliver(binding_id)


class AgentServiceR15:
    """R15: current effect authorization over the frozen R14 delivery identity."""

    def __init__(
        self,
        r14: AgentServiceR14,
        *,
        effect_policy_adapter: PolicyAdapter | None,
    ) -> None:
        self._r14 = r14
        self._connection = r14._connection
        self.effect_authorization_records = EffectAuthorizationDecisionStore(self._connection)
        self.effect_authorizations = EffectAuthorizationCoordinator(
            bindings=r14.transport_bindings,
            delegations=r14.delegations,
            records=self.effect_authorization_records,
            policy_adapter=effect_policy_adapter,
        )
        self.delivery = EffectAuthorizedDeliveryCoordinator(
            delegate=r14.delivery,
            receipts=r14.delivery_receipts,
            authorizations=self.effect_authorizations,
        )

    def __getattr__(self, name: str) -> Any:
        return getattr(self._r14, name)

    @classmethod
    def open(
        cls,
        db_path: str | Path,
        *,
        policy_adapter: PolicyAdapter | None = None,
        **kwargs: Any,
    ) -> "AgentServiceR15":
        r14 = AgentServiceR14.open(
            db_path,
            policy_adapter=policy_adapter,
            **kwargs,
        )
        cls._initialize_schema(r14._connection)
        return cls(r14, effect_policy_adapter=policy_adapter)

    @staticmethod
    def _initialize_schema(connection: sqlite3.Connection) -> None:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS effect_authorization_decisions (
                id TEXT PRIMARY KEY,
                binding_id TEXT NOT NULL UNIQUE REFERENCES transport_bindings(id),
                delegation_id TEXT NOT NULL REFERENCES delegation_envelopes(id),
                allowed INTEGER NOT NULL CHECK(allowed IN (0, 1)),
                reason TEXT,
                policy_revision TEXT NOT NULL,
                granted_permissions_json TEXT NOT NULL,
                created_at_ns INTEGER NOT NULL
            );
            """
        )
        connection.commit()

    def close(self) -> None:
        self._r14.close()
