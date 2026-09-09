"""Experimental AM1/AM2 Agent Loop implementation identity binding.

A LoopDriver identity is deliberately *not* an executable plugin, registry, or
live-replacement API. Historical AM1/AM2 work showed that morphology identity must
be bound to immutable execution authority and that an arbitrary Python factory
provides no mechanical proof of Provider/Tool lifecycle or recovery preservation.

The current product binds only exact system-manifest bytes whose digest is already
fenced by `HarnessRunContract.system_manifest_ref`. A future executable LoopDriver
interface must still earn a non-bypassable implementation-byte/contract proof; it
must not grow back from an arbitrary callable.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from anc_canonical import JsonValue, canonical_digest, validate_json_value

from .core_contracts import HarnessRunContract



def _text(value: str, label: str) -> None:
    if (
        not isinstance(value, str)
        or not value
        or value != value.strip()
        or len(value.encode("utf-8")) > 300
    ):
        raise ValueError(f"{label} must be non-empty and trimmed")


def _digest(value: str, label: str) -> None:
    if (
        not isinstance(value, str)
        or len(value) != 71
        or not value.startswith("sha256:")
        or any(character not in "0123456789abcdef" for character in value[7:])
    ):
        raise ValueError(f"{label} must be sha256:<64 lowercase hex>")


@dataclass(frozen=True, slots=True)
class HarnessLoopDriverRef:
    """Exact Loop implementation identity only; never a loader, registry, or grant."""

    driver_id: str
    driver_digest: str

    def __post_init__(self) -> None:
        _text(self.driver_id, "Harness LoopDriver identity")
        _digest(self.driver_digest, "Harness LoopDriver digest")

    def to_dict(self) -> dict[str, JsonValue]:
        return {"driverId": self.driver_id, "driverDigest": self.driver_digest}

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "HarnessLoopDriverRef":
        if set(value) != {"driverId", "driverDigest"}:
            raise ValueError("HarnessLoopDriverRef fields differ")
        return cls(driver_id=value["driverId"], driver_digest=value["driverDigest"])


def _builtin_ref(driver_id: str, scheduling_mode: str) -> HarnessLoopDriverRef:
    descriptor = {
        "schemaVersion": 1,
        "kind": "ordivon.builtin-loop-driver-semantics",
        "driverId": driver_id,
        "schedulingMode": scheduling_mode,
        "constitutionKernel": "ordivon-agent-loop-v1",
    }
    return HarnessLoopDriverRef(
        driver_id=driver_id,
        driver_digest=canonical_digest(descriptor),
    )


SEQUENTIAL_LOOP_DRIVER = _builtin_ref(
    "loop-driver:sequential-v1", "sequential"
)
DELIBERATE_THEN_ACT_LOOP_DRIVER = _builtin_ref(
    "loop-driver:deliberate-then-act-v1", "deliberate_then_act"
)
_BUILTIN_SCHEDULING_MODES = {
    (SEQUENTIAL_LOOP_DRIVER.driver_id, SEQUENTIAL_LOOP_DRIVER.driver_digest): "sequential",
    (
        DELIBERATE_THEN_ACT_LOOP_DRIVER.driver_id,
        DELIBERATE_THEN_ACT_LOOP_DRIVER.driver_digest,
    ): "deliberate_then_act",
}


def builtin_scheduling_mode(identity: "HarnessLoopDriverIdentity | HarnessLoopDriverRef | None") -> str:
    if identity is None:
        return "sequential"
    key = (identity.driver_id, identity.driver_digest)
    try:
        return _BUILTIN_SCHEDULING_MODES[key]
    except KeyError as error:
        raise ValueError(
            "Harness LoopDriver is identified but has no admitted built-in executable implementation"
        ) from error

@dataclass(frozen=True, slots=True)
class HarnessLoopDriverIdentity:
    """One exact Run-manifest-bound Loop implementation identity, without execution.

    The object proves only that exact manifest bytes fenced by the Run Contract
    declared this `(driverId, driverDigest)` pair. It grants no right to load,
    execute, replace, discover, or promote code.
    """

    driver_id: str
    driver_digest: str
    system_manifest_digest: str

    def __post_init__(self) -> None:
        _text(self.driver_id, "Harness LoopDriver identity")
        _digest(self.driver_digest, "Harness LoopDriver digest")
        _digest(self.system_manifest_digest, "Harness LoopDriver System Manifest digest")

    @classmethod
    def from_contract_manifest(
        cls,
        contract: HarnessRunContract,
        system_manifest: Mapping[str, Any],
        *,
        driver: HarnessLoopDriverRef,
    ) -> "HarnessLoopDriverIdentity":
        """Bind one declared Loop identity to exact manifest bytes already fenced by Contract."""

        if not isinstance(contract, HarnessRunContract):
            raise TypeError("Harness LoopDriver requires an exact HarnessRunContract")
        if not isinstance(driver, HarnessLoopDriverRef):
            raise TypeError("Harness LoopDriver requires an exact HarnessLoopDriverRef")
        if any(not isinstance(key, str) for key in system_manifest):
            raise TypeError("Harness LoopDriver system manifest keys must be strings")
        manifest_value = dict(system_manifest)
        validate_json_value(manifest_value)
        manifest_digest = canonical_digest(manifest_value)
        if manifest_digest != contract.system_manifest_ref.digest:
            raise ValueError("Harness LoopDriver system manifest differs from the Run Contract")
        if manifest_value.get("loopDriver") != driver.to_dict():
            raise ValueError("Harness LoopDriver differs from the Run Contract manifest declaration")
        return cls(
            driver_id=driver.driver_id,
            driver_digest=driver.driver_digest,
            system_manifest_digest=manifest_digest,
        )

    def require_contract(self, system_manifest_digest: str) -> None:
        if system_manifest_digest != self.system_manifest_digest:
            raise ValueError("Harness LoopDriver identity belongs to another Run manifest")


__all__ = [
    "DELIBERATE_THEN_ACT_LOOP_DRIVER",
    "HarnessLoopDriverIdentity",
    "HarnessLoopDriverRef",
    "SEQUENTIAL_LOOP_DRIVER",
    "builtin_scheduling_mode",
]
