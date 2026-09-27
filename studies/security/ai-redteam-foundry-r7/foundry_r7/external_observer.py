from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
import sys

R7_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = R7_ROOT.parents[2]
R5_ROOT = REPO_ROOT / "studies" / "security" / "ai-redteam-foundry-r5"
R6_ROOT = REPO_ROOT / "studies" / "security" / "ai-redteam-foundry-r6"
for root in (R5_ROOT, R6_ROOT):
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))

from foundry_r5 import InMemorySyntheticWorld, canonical_digest  # noqa: E402
from foundry_r6 import EffectReceipt  # noqa: E402

_DIGEST_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
_INDEPENDENCE = frozenset({
    "process_local_independent_code_path",
    "independent_process",
    "independent_kernel",
})
_THREAT_CLASSES = frozenset({"semantic_only", "synthetic_agent", "hostile_code"})


def _text(value: str, label: str) -> str:
    if not isinstance(value, str) or not value or value != value.strip():
        raise ValueError(f"{label} must be non-empty canonical text")
    return value


def _digest(value: str, label: str) -> str:
    _text(value, label)
    if _DIGEST_RE.fullmatch(value) is None:
        raise ValueError(f"{label} must be sha256:<64 lowercase hex>")
    return value


@dataclass(frozen=True, slots=True)
class ObserverBinding:
    observer_id: str
    observer_revision: str
    independence_class: str
    applicable_threat_classes: tuple[str, ...]

    def __post_init__(self) -> None:
        _text(self.observer_id, "observer id")
        _text(self.observer_revision, "observer revision")
        if self.independence_class not in _INDEPENDENCE:
            raise ValueError(f"independence class must be one of {sorted(_INDEPENDENCE)}")
        canonical = tuple(sorted(set(self.applicable_threat_classes)))
        if not canonical or any(item not in _THREAT_CLASSES for item in canonical):
            raise ValueError("observer must declare supported threat classes")
        if self.independence_class == "process_local_independent_code_path" and "hostile_code" in canonical:
            raise ValueError("process-local observer cannot claim hostile-code applicability")
        object.__setattr__(self, "applicable_threat_classes", canonical)

    def to_dict(self) -> dict[str, object]:
        return {
            "observerId": self.observer_id,
            "observerRevision": self.observer_revision,
            "independenceClass": self.independence_class,
            "applicableThreatClasses": list(self.applicable_threat_classes),
        }


@dataclass(frozen=True, slots=True)
class ObservationAnchor:
    observer_id: str
    observer_revision: str
    environment_digest: str
    world_spec_digest: str
    state_digest: str
    trace_digest: str
    event_count: int
    outbound_count: int
    outbound_digest: str

    @property
    def digest(self) -> str:
        return canonical_digest(self.to_dict())

    def to_dict(self) -> dict[str, object]:
        return {
            "observerId": self.observer_id,
            "observerRevision": self.observer_revision,
            "environmentDigest": self.environment_digest,
            "worldSpecDigest": self.world_spec_digest,
            "stateDigest": self.state_digest,
            "traceDigest": self.trace_digest,
            "eventCount": self.event_count,
            "outboundCount": self.outbound_count,
            "outboundDigest": self.outbound_digest,
        }


@dataclass(frozen=True, slots=True)
class ConsequenceObservation:
    binding: ObserverBinding
    environment_digest: str
    world_spec_digest: str
    effect_id: str
    effect_request_digest: str
    before_state_digest: str
    after_state_digest: str
    before_trace_digest: str
    after_trace_digest: str
    before_event_count: int
    after_event_count: int
    before_outbound_count: int
    after_outbound_count: int
    outbound_snapshot_digest: str
    synthetic_secret_crossing_ids: tuple[str, ...]
    resource_content_digests: tuple[tuple[str, str], ...]

    def __post_init__(self) -> None:
        _digest(self.environment_digest, "environment digest")
        _digest(self.world_spec_digest, "world spec digest")
        _text(self.effect_id, "effect id")
        _digest(self.effect_request_digest, "effect request digest")
        for value, label in (
            (self.before_state_digest, "before state digest"),
            (self.after_state_digest, "after state digest"),
            (self.before_trace_digest, "before trace digest"),
            (self.after_trace_digest, "after trace digest"),
            (self.outbound_snapshot_digest, "outbound snapshot digest"),
        ):
            _digest(value, label)
        for value, label in (
            (self.before_event_count, "before event count"),
            (self.after_event_count, "after event count"),
            (self.before_outbound_count, "before outbound count"),
            (self.after_outbound_count, "after outbound count"),
        ):
            if not isinstance(value, int) or value < 0:
                raise ValueError(f"{label} must be a non-negative integer")
        if self.after_event_count < self.before_event_count or self.after_outbound_count < self.before_outbound_count:
            raise ValueError("observation window counters cannot move backwards")
        object.__setattr__(self, "synthetic_secret_crossing_ids", tuple(sorted(set(self.synthetic_secret_crossing_ids))))
        resources = tuple(sorted(self.resource_content_digests))
        if len({item[0] for item in resources}) != len(resources):
            raise ValueError("duplicate observed resource id")
        for resource_id, digest in resources:
            _text(resource_id, "resource id")
            _digest(digest, "resource content digest")
        object.__setattr__(self, "resource_content_digests", resources)

    @property
    def digest(self) -> str:
        return canonical_digest(self.to_dict())

    def to_dict(self) -> dict[str, object]:
        return {
            "schemaVersion": 1,
            "kind": "ordivon.ai-redteam-consequence-observation",
            "binding": self.binding.to_dict(),
            "environmentDigest": self.environment_digest,
            "worldSpecDigest": self.world_spec_digest,
            "effectId": self.effect_id,
            "effectRequestDigest": self.effect_request_digest,
            "beforeStateDigest": self.before_state_digest,
            "afterStateDigest": self.after_state_digest,
            "beforeTraceDigest": self.before_trace_digest,
            "afterTraceDigest": self.after_trace_digest,
            "beforeEventCount": self.before_event_count,
            "afterEventCount": self.after_event_count,
            "beforeOutboundCount": self.before_outbound_count,
            "afterOutboundCount": self.after_outbound_count,
            "outboundSnapshotDigest": self.outbound_snapshot_digest,
            "syntheticSecretCrossingIds": list(self.synthetic_secret_crossing_ids),
            "resourceContentDigests": [
                {"resourceId": resource_id, "contentDigest": digest}
                for resource_id, digest in self.resource_content_digests
            ],
        }

    def security_v2_observation(self, *, threat_class: str) -> dict[str, object]:
        if threat_class not in self.binding.applicable_threat_classes:
            raise ValueError("observer binding is not applicable to requested threat class")
        return {
            "plane": "world-truth",
            "payload": {
                "stateDigest": self.after_state_digest,
                "traceDigest": self.after_trace_digest,
                "observationDigest": self.digest,
                "observerId": self.binding.observer_id,
                "observerRevision": self.binding.observer_revision,
                "independenceClass": self.binding.independence_class,
                "environmentDigest": self.environment_digest,
                "worldSpecDigest": self.world_spec_digest,
                "effectId": self.effect_id,
                "effectRequestDigest": self.effect_request_digest,
            },
        }


@dataclass(frozen=True, slots=True)
class ReceiptObservationConsistency:
    effect_id: str
    effect_request_digest: str
    receipt_digest: str
    observation_digest: str
    consistent: bool
    mismatches: tuple[str, ...]

    @property
    def digest(self) -> str:
        return canonical_digest(self.to_dict())

    def to_dict(self) -> dict[str, object]:
        return {
            "schemaVersion": 1,
            "kind": "ordivon.ai-redteam-receipt-observation-consistency",
            "effectId": self.effect_id,
            "effectRequestDigest": self.effect_request_digest,
            "receiptDigest": self.receipt_digest,
            "observationDigest": self.observation_digest,
            "consistent": self.consistent,
            "mismatches": list(self.mismatches),
        }


class SyntheticWorldObserver:
    binding = ObserverBinding(
        observer_id="ordivon.ai-redteam.synthetic-world-observer-r7",
        observer_revision="r7",
        independence_class="process_local_independent_code_path",
        applicable_threat_classes=("synthetic_agent",),
    )

    def start(self, world: InMemorySyntheticWorld, *, environment_digest: str) -> ObservationAnchor:
        _digest(environment_digest, "environment digest")
        receipt = world.receipt()
        return ObservationAnchor(
            observer_id=self.binding.observer_id,
            observer_revision=self.binding.observer_revision,
            environment_digest=environment_digest,
            world_spec_digest=receipt.world_spec_digest,
            state_digest=receipt.state_digest,
            trace_digest=receipt.trace_digest,
            event_count=receipt.event_count,
            outbound_count=receipt.outbound_count,
            outbound_digest=canonical_digest(world.outbound()),
        )

    def finish(
        self,
        anchor: ObservationAnchor,
        world: InMemorySyntheticWorld,
        *,
        effect_id: str,
        effect_request_digest: str,
        resource_ids: tuple[str, ...] = (),
    ) -> ConsequenceObservation:
        if anchor.observer_id != self.binding.observer_id or anchor.observer_revision != self.binding.observer_revision:
            raise ValueError("observation anchor belongs to a different observer")
        receipt = world.receipt()
        if receipt.world_spec_digest != anchor.world_spec_digest:
            raise ValueError("synthetic world specification changed during observation window")
        resource_digests = tuple(
            (resource_id, canonical_digest({"content": world.resource_content(resource_id)}))
            for resource_id in resource_ids
        )
        return ConsequenceObservation(
            binding=self.binding,
            environment_digest=anchor.environment_digest,
            world_spec_digest=receipt.world_spec_digest,
            effect_id=effect_id,
            effect_request_digest=effect_request_digest,
            before_state_digest=anchor.state_digest,
            after_state_digest=receipt.state_digest,
            before_trace_digest=anchor.trace_digest,
            after_trace_digest=receipt.trace_digest,
            before_event_count=anchor.event_count,
            after_event_count=receipt.event_count,
            before_outbound_count=anchor.outbound_count,
            after_outbound_count=receipt.outbound_count,
            outbound_snapshot_digest=canonical_digest(world.outbound()),
            synthetic_secret_crossing_ids=world.synthetic_secret_crossings(),
            resource_content_digests=resource_digests,
        )


def reconcile_receipt(receipt: EffectReceipt, observation: ConsequenceObservation) -> ReceiptObservationConsistency:
    mismatches: list[str] = []
    if receipt.effect_id != observation.effect_id:
        mismatches.append("effect_id")
    if receipt.effect_request_digest != observation.effect_request_digest:
        mismatches.append("effect_request_digest")
    if receipt.world_before_digest != observation.before_state_digest:
        mismatches.append("world_before_digest")
    if receipt.world_after_digest != observation.after_state_digest:
        mismatches.append("world_after_digest")
    if receipt.world_trace_digest != observation.after_trace_digest:
        mismatches.append("world_trace_digest")
    return ReceiptObservationConsistency(
        effect_id=observation.effect_id,
        effect_request_digest=observation.effect_request_digest,
        receipt_digest=receipt.digest,
        observation_digest=observation.digest,
        consistent=not mismatches,
        mismatches=tuple(mismatches),
    )
