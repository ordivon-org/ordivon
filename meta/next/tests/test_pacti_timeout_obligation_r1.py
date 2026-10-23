from __future__ import annotations

import json
import tomllib
from pathlib import Path

from ordivon_composition import (
    compile_verification_obligations,
    resolve_verifier_bindings,
)

from scripts.pacti_timeout_obligation_r1 import (
    build_binding_set,
    build_manifest,
    validate_spec,
)

NEXT_ROOT = Path(__file__).resolve().parents[1]
SPEC = (
    NEXT_ROOT
    / "evidence"
    / "acceptance"
    / "verified-reintegration-external-owner-dogfood-r1"
    / "pacti-timeout-obligation-spec-r2.json"
)


def _spec() -> dict:
    return json.loads(SPEC.read_text(encoding="utf-8"))


def test_pacti_timeout_spec_builds_exact_obligation_and_binding() -> None:
    spec = _spec()
    validate_spec(spec)
    manifest = build_manifest(spec)
    obligations = compile_verification_obligations(manifest)
    bindings = build_binding_set(obligations, spec)
    resolution = resolve_verifier_bindings(obligations, bindings)

    assert obligations["requiredGateIds"] == ["gate:pacti-timeout-contract"]
    assert bindings["bindings"][0]["verifierClass"] == "contract-algebra"
    assert bindings["bindings"][0]["nativeSpecificationRef"]["id"] == spec["id"]
    assert resolution["standing"] == "VERIFIER_BINDINGS_RESOLVED"
    assert resolution["executionAuthorityGranted"] is False
    assert resolution["domainAcceptanceEstablished"] is False


def test_pacti_remains_outside_project_dependencies() -> None:
    project = tomllib.loads((NEXT_ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    dependencies = project["project"]["dependencies"]
    all_groups = project.get("dependency-groups", {})
    flattened = [item for values in all_groups.values() for item in values]

    assert not any(item.startswith("pacti") for item in [*dependencies, *flattened])


def test_frozen_pacti_shadow_acceptance_preserves_boundaries() -> None:
    from ordivon_composition import canonical_digest

    evidence_path = (
        NEXT_ROOT
        / "evidence"
        / "acceptance"
        / "verified-reintegration-external-owner-dogfood-r1"
        / "pacti-timeout-obligation-r2.json"
    )
    evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
    run = evidence["run"]

    assert evidence["sourceRevision"] == "7dc50e0908c2d739be5a1a16c1d4582ad9508220"
    assert evidence["runner"]["projectDependencyAdded"] is False
    assert run["specRef"]["digest"] == canonical_digest(_spec())
    assert run["resolution"]["standing"] == "VERIFIER_BINDINGS_RESOLVED"
    assert run["formalResult"]["acceptedCase"]["refinesTopRequirement"] is True
    assert run["formalResult"]["quotient"]["recomposedRefinesTopRequirement"] is True
    assert run["formalResult"]["deliberateMismatch"]["rejected"] is True
    assert run["gateResult"]["standing"] == "SATISFIED"
    assert run["projection"]["mechanicalClosure"] is True
    assert run["projection"]["domainAcceptanceEstablished"] is False
