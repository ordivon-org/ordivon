from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
import sys

R6_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = R6_ROOT.parents[2]
R5_ROOT = REPO_ROOT / "studies" / "security" / "ai-redteam-foundry-r5"
if str(R5_ROOT) not in sys.path:
    sys.path.insert(0, str(R5_ROOT))

from foundry_r5 import InMemorySyntheticWorld, WorldAction, canonical_digest  # noqa: E402

_DIGEST_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
_SCOPES = frozenset({"synthetic_world", "external_world"})
_OPERATIONS = frozenset({"read", "write", "send", "request", "query"})


def _digest(value: str, label: str) -> str:
    if not isinstance(value, str) or _DIGEST_RE.fullmatch(value) is None:
        raise ValueError(f"{label} must be sha256:<64 lowercase hex>")
    return value


def _text(value: str, label: str) -> str:
    if not isinstance(value, str) or not value or value != value.strip():
        raise ValueError(f"{label} must be non-empty canonical text")
    return value


@dataclass(frozen=True, slots=True)
class EffectAttempt:
    effect_id: str
    actor_id: str
    environment_digest: str
    world_spec_digest: str
    scope: str
    service_id: str
    operation: str
    target: str
    content: str = ""

    def __post_init__(self) -> None:
        _text(self.effect_id, "effect id")
        _text(self.actor_id, "actor id")
        _digest(self.environment_digest, "environment digest")
        _digest(self.world_spec_digest, "world spec digest")
        if self.scope not in _SCOPES:
            raise ValueError(f"scope must be one of {sorted(_SCOPES)}")
        _text(self.service_id, "service id")
        if self.operation not in _OPERATIONS:
            raise ValueError(f"operation must be one of {sorted(_OPERATIONS)}")
        _text(self.target, "target")
        if not isinstance(self.content, str):
            raise TypeError("content must be text")

    @property
    def content_digest(self) -> str:
        return canonical_digest({"content": self.content})

    @property
    def digest(self) -> str:
        return canonical_digest(self.to_dict())

    def to_dict(self) -> dict[str, object]:
        return {
            "schemaVersion": 1,
            "kind": "ordivon.ai-redteam-effect-attempt",
            "effectId": self.effect_id,
            "actorId": self.actor_id,
            "environmentDigest": self.environment_digest,
            "worldSpecDigest": self.world_spec_digest,
            "scope": self.scope,
            "serviceId": self.service_id,
            "operation": self.operation,
            "target": self.target,
            "contentDigest": self.content_digest,
        }


@dataclass(frozen=True, slots=True)
class SecurityAdmissionRef:
    decision_ref: str
    effect_request_digest: str
    evidence_digest: str
    admitted: bool

    def __post_init__(self) -> None:
        _text(self.decision_ref, "decision ref")
        _digest(self.effect_request_digest, "effect request digest")
        _digest(self.evidence_digest, "admission evidence digest")

    def to_dict(self) -> dict[str, object]:
        return {
            "decisionRef": self.decision_ref,
            "effectRequestDigest": self.effect_request_digest,
            "evidenceDigest": self.evidence_digest,
            "admitted": self.admitted,
        }


@dataclass(frozen=True, slots=True)
class EffectReceipt:
    effect_id: str
    effect_request_digest: str
    disposition: str
    route: str
    executor: str
    world_before_digest: str
    world_after_digest: str
    world_trace_digest: str
    security_decision_ref: str | None = None

    @property
    def digest(self) -> str:
        return canonical_digest(self.to_dict())

    def to_dict(self) -> dict[str, object]:
        return {
            "schemaVersion": 1,
            "kind": "ordivon.ai-redteam-effect-receipt",
            "effectId": self.effect_id,
            "effectRequestDigest": self.effect_request_digest,
            "disposition": self.disposition,
            "route": self.route,
            "executor": self.executor,
            "worldBeforeDigest": self.world_before_digest,
            "worldAfterDigest": self.world_after_digest,
            "worldTraceDigest": self.world_trace_digest,
            "securityDecisionRef": self.security_decision_ref,
        }


class ReferenceEffectProxy:
    proxy_id = "ordivon.ai-redteam.reference-effect-proxy-r6"

    def __init__(self, world: InMemorySyntheticWorld) -> None:
        self.world = world
        self._ledger: dict[str, tuple[str, EffectReceipt]] = {}

    def _replay(self, attempt: EffectAttempt) -> EffectReceipt | None:
        previous = self._ledger.get(attempt.effect_id)
        if previous is None:
            return None
        previous_digest, receipt = previous
        if previous_digest != attempt.digest:
            raise ValueError("effect replay identity reused with different request bytes")
        return receipt

    def _record(self, attempt: EffectAttempt, receipt: EffectReceipt) -> EffectReceipt:
        self._ledger[attempt.effect_id] = (attempt.digest, receipt)
        return receipt

    def handle(
        self,
        attempt: EffectAttempt,
        *,
        security_admission: SecurityAdmissionRef | None = None,
    ) -> EffectReceipt:
        replay = self._replay(attempt)
        if replay is not None:
            return replay
        if attempt.world_spec_digest != self.world.spec.digest:
            raise ValueError("effect attempt is bound to a different synthetic world")

        before = self.world.receipt()
        if attempt.scope == "synthetic_world":
            action = WorldAction(
                action_id=f"effect:{attempt.effect_id}",
                actor_id=attempt.actor_id,
                service_id=attempt.service_id,
                operation=attempt.operation,
                target=attempt.target,
                content=attempt.content,
            )
            self.world.apply(action)
            after = self.world.receipt()
            return self._record(
                attempt,
                EffectReceipt(
                    effect_id=attempt.effect_id,
                    effect_request_digest=attempt.digest,
                    disposition="simulated",
                    route="synthetic_world",
                    executor=self.world.provider_id,
                    world_before_digest=before.state_digest,
                    world_after_digest=after.state_digest,
                    world_trace_digest=after.trace_digest,
                ),
            )

        # External effects never execute in the reference proxy. Security admission is necessary but not sufficient.
        if security_admission is None:
            disposition = "blocked_requires_security_admission"
            decision_ref = None
        else:
            if security_admission.effect_request_digest != attempt.digest:
                raise ValueError("Security admission belongs to a different effect request")
            decision_ref = security_admission.decision_ref
            disposition = "delegation_ready_external_provider_required" if security_admission.admitted else "blocked_by_security"

        after = self.world.receipt()
        return self._record(
            attempt,
            EffectReceipt(
                effect_id=attempt.effect_id,
                effect_request_digest=attempt.digest,
                disposition=disposition,
                route="external_world",
                executor=self.proxy_id,
                world_before_digest=before.state_digest,
                world_after_digest=after.state_digest,
                world_trace_digest=after.trace_digest,
                security_decision_ref=decision_ref,
            ),
        )
