"""Typed E7 equipment-retention assessments and bounded benchmark observations."""

from __future__ import annotations

import subprocess
import time
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any


def summarize_trial(
    *,
    equipment_id: str,
    fallback_id: str | None,
    capability_delta: Sequence[str],
    friction_delta: Mapping[str, Any],
    ceiling_delta: Sequence[str],
    costs: Mapping[str, Any],
    evidence_level: str,
) -> dict[str, Any]:
    """Return typed E7 evidence without collapsing heterogeneous value into one scalar."""
    if evidence_level not in {"executed", "ordinary-production", "external-only", "physical-missing"}:
        raise ValueError("invalid evidence level")
    meaningful_friction = any(
        friction_delta.get(key) not in (None, 0, 0.0, False, "none")
        for key in ("manualHandoffsReduced", "commandsReduced", "argumentTokensReduced", "setupStepsReduced", "recoveryStepsReduced", "batchabilityGain")
    ) or (isinstance(friction_delta.get("medianWallTimeRatio"), (int, float)) and friction_delta["medianWallTimeRatio"] < 0.75)
    unique = bool(capability_delta)
    ceiling = bool(ceiling_delta)
    if evidence_level == "physical-missing":
        disposition = "challenger"
    elif evidence_level == "external-only":
        disposition = "candidate"
    elif unique and (costs.get("highPersistentCost") is True or costs.get("guiStateCoupled") is True):
        disposition = "specialist-on-demand"
    elif unique or meaningful_friction:
        disposition = "retain"
    elif ceiling:
        disposition = "specialist-on-demand"
    else:
        disposition = "reject-or-merge"
    return {
        "equipmentId": equipment_id,
        "fallbackId": fallback_id,
        "evidenceLevel": evidence_level,
        "capabilityDelta": list(capability_delta),
        "frictionDelta": dict(friction_delta),
        "qualityCeilingDelta": list(ceiling_delta),
        "costs": dict(costs),
        "decision": disposition,
        "boundary": "Capability, friction, ceiling, and cost remain typed. The decision is a retention rule, not a universal equipment-quality score.",
    }


def median_runtime_ms(command: Sequence[str], *, repeats: int = 5, cwd: Path | None = None) -> float:
    samples: list[float] = []
    for _ in range(repeats):
        started = time.perf_counter_ns()
        subprocess.run(command, cwd=cwd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True, timeout=60)
        samples.append((time.perf_counter_ns() - started) / 1_000_000.0)
    samples.sort()
    return samples[len(samples) // 2]
