#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
CONSTITUTION = ROOT / "docs" / "architecture" / "architecture-constitution-r1.json"
REANCHOR = ROOT / "docs" / "architecture" / "ARCHITECTURE_REANCHOR_R1.md"
CURRENT = ROOT / "docs" / "architecture" / "CURRENT_ARCHITECTURE.md"
STRUCTURE = ROOT / "docs" / "architecture" / "STRUCTURE_R2.md"
STRUCTURE_PLAN = ROOT / "docs" / "architecture" / "structure-r2-transition-r1.json"
README = ROOT / "README.md"
CAPABILITY_FABRIC_SPEC = ROOT / "docs" / "architecture" / "CAPABILITY_PROJECTION_FABRIC_R1.md"
CAPABILITY_FABRIC_PLAN = ROOT / "docs" / "architecture" / "capability-projection-fabric-lego-r1.json"

EXPECTED_CAPABILITY_FABRIC_DO_NOT_BUILD = {
    "universal-capability-registry-service",
    "gateway-capability-database",
    "global-profile-bundle-owner",
    "gateway-credential-vault",
    "gateway-workflow-engine",
    "gateway-scheduler",
    "blind-retry-after-ambiguous-effect",
}
EXPECTED_CAPABILITY_FABRIC_FIRST_WAVE = {"CPF-10", "CPF-11", "CPF-12", "CPF-13"}

EXPECTED_KERNEL = {
    "cognitive-circuit",
    "interface-contract",
    "authority-obligation",
    "verification-obligation",
}
EXPECTED_CANCELLED_WAVES = {"S3", "S4", "S6", "S7", "S9"}
EXPECTED_SUBSTRATE = {
    "agentRun": "harness",
    "physicalExecution": "runtime",
    "semanticContinuity": "host",
    "northboundRoutingProjection": "gateway",
    "durableWorkflow": "temporal-or-provider-native",
    "providerEffect": "provider",
    "discovery": "catalogs-and-skills",
}
REQUIRED_LAWS = {
    "physical-truth-outranks-documentation",
    "one-natural-owner-per-durable-truth",
    "placement-does-not-transfer-authority",
    "composition-does-not-mint-authority",
    "capability-provider-authority-are-distinct",
    "observation-evidence-verification-decision-are-distinct",
    "no-universal-lifecycle-ontology",
    "harness-owns-only-bounded-agent-run",
    "runtime-owns-physical-execution-not-semantic-completion",
    "host-owns-continuity-not-physical-execution",
    "gateway-owns-routing-projection-not-owner-truth",
    "workflow-stays-external-by-default",
    "unknown-effects-reconcile-never-blind-replay",
    "delete-custom-by-default",
}


class ArchitectureConstitutionError(ValueError):
    pass


def _load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ArchitectureConstitutionError(f"{path} root must be an object")
    return value


def validate_constitution(value: dict[str, Any]) -> None:
    if value.get("schemaVersion") != 1 or value.get("kind") != "ordivon.architecture-constitution":
        raise ArchitectureConstitutionError("architecture constitution identity drifted")
    if value.get("status") != "CURRENT_ARCHITECTURE_CONSTITUTION":
        raise ArchitectureConstitutionError("architecture constitution must be current")
    if value.get("purpose") != "verified-composition-system":
        raise ArchitectureConstitutionError("Ordivon purpose drifted from verified composition")
    if set(value.get("minimalSemanticKernel", [])) != EXPECTED_KERNEL:
        raise ArchitectureConstitutionError("minimal semantic kernel drifted")
    if value.get("substrateOwners") != EXPECTED_SUBSTRATE:
        raise ArchitectureConstitutionError("substrate owner boundary drifted")
    if set(value.get("cancelledPathRelocationWaves", [])) != EXPECTED_CANCELLED_WAVES:
        raise ArchitectureConstitutionError("cancelled Structure R2 path waves drifted")
    if REQUIRED_LAWS - set(value.get("laws", [])):
        raise ArchitectureConstitutionError("required architecture laws are missing")
    truth_order = value.get("truthOrder")
    if not isinstance(truth_order, list) or truth_order[:2] != [
        "current-physical-truth",
        "canonical-source-configuration",
    ]:
        raise ArchitectureConstitutionError("physical/source truth must precede documentation")
    if truth_order.index("current-documentation") < truth_order.index("test-verification-evidence"):
        raise ArchitectureConstitutionError("documentation must not outrank verification evidence")


def validate_repository(root: Path = ROOT) -> None:
    value = _load(root / CONSTITUTION.relative_to(ROOT))
    validate_constitution(value)

    reanchor = (root / REANCHOR.relative_to(ROOT)).read_text(encoding="utf-8")
    for phrase in (
        "Ordivon is a verified-composition system",
        "There is no global Ordivon `Task -> Run -> Session -> Attempt` tree.",
        "S3, S4, S6, S7 and S9 are cancelled",
        "DELETE CUSTOM BY DEFAULT",
    ):
        if phrase not in reanchor:
            raise ArchitectureConstitutionError(f"re-anchor document missing invariant: {phrase}")

    current = (root / CURRENT.relative_to(ROOT)).read_text(encoding="utf-8")
    if "CURRENT PHYSICAL TRUTH" not in current:
        raise ArchitectureConstitutionError("current architecture still lacks physical-truth ordering")
    if "this document + `deployed-architecture-r1.json`" in current:
        raise ArchitectureConstitutionError("documentation still claims first-order architecture authority")

    structure = (root / STRUCTURE.relative_to(ROOT)).read_text(encoding="utf-8")
    if "SUPERSEDED FOR FUTURE PATH RELOCATION" not in structure:
        raise ArchitectureConstitutionError("Structure R2 is not explicitly superseded")
    plan = _load(root / STRUCTURE_PLAN.relative_to(ROOT))
    if plan.get("status") != "superseded" or plan.get("supersededBy") != "docs/architecture/ARCHITECTURE_REANCHOR_R1.md":
        raise ArchitectureConstitutionError("Structure R2 machine plan is not superseded")
    if set(plan.get("remainingPathMovesCancelled", [])) != EXPECTED_CANCELLED_WAVES:
        raise ArchitectureConstitutionError("Structure R2 cancelled path waves drifted")

    readme = (root / README.relative_to(ROOT)).read_text(encoding="utf-8")
    if "docs/architecture/ARCHITECTURE_REANCHOR_R1.md" not in readme:
        raise ArchitectureConstitutionError("root README must route architecture readers through re-anchor constitution")

    capability_spec = (root / CAPABILITY_FABRIC_SPEC.relative_to(ROOT)).read_text(encoding="utf-8")
    for phrase in (
        "without creating a universal capability registry",
        "Gateway remains a thin, rebuildable, non-authoritative northbound adapter.",
        "Discovery and authorization are separate.",
        "`timeout -> retry` is not an accepted generic policy.",
    ):
        if phrase not in capability_spec:
            raise ArchitectureConstitutionError(f"Capability Projection Fabric violates/misses constitutional boundary: {phrase}")

    capability_plan = _load(root / CAPABILITY_FABRIC_PLAN.relative_to(ROOT))
    if capability_plan.get("kind") != "ordivon.capability-projection-fabric-lego-plan":
        raise ArchitectureConstitutionError("Capability Projection Fabric plan identity drifted")
    if set(capability_plan.get("firstImplementationSet", [])) != EXPECTED_CAPABILITY_FABRIC_FIRST_WAVE:
        raise ArchitectureConstitutionError("Capability Projection Fabric first wave drifted")
    if not EXPECTED_CAPABILITY_FABRIC_DO_NOT_BUILD.issubset(set(capability_plan.get("doNotBuild", []))):
        raise ArchitectureConstitutionError("Capability Projection Fabric lost anti-Mega-Gateway constraints")


def main() -> int:
    try:
        validate_repository()
    except (OSError, json.JSONDecodeError, ArchitectureConstitutionError) as exc:
        print(f"architecture constitution check failed: {exc}")
        return 2
    print("architecture constitution check passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
