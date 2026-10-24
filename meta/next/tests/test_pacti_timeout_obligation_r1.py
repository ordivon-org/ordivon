from __future__ import annotations

import json
import tomllib
from pathlib import Path

import pytest
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


def test_owner_timeout_envelope_fails_closed_on_unknown_or_invalid_status() -> None:
    import pytest
    from ordivon_composition import CircuitContractError

    from scripts.pacti_timeout_obligation_r1 import evaluate_owner_timeout_envelope

    grant = {
        "schemaVersion": 1,
        "kind": "ordivon.plugin-gateway-execution-grant",
        "maxTimeoutMs": 300_000,
    }
    for report in (
        {},
        {"config": {}},
        {"config": {"maxRuntimeMs": True}},
        {"config": {"maxRuntimeMs": 0}},
    ):
        with pytest.raises(CircuitContractError, match="runtime.config.maxRuntimeMs"):
            evaluate_owner_timeout_envelope(grant, report)
    with pytest.raises(CircuitContractError, match="Harness owner grant"):
        evaluate_owner_timeout_envelope(
            {
                "schemaVersion": True,
                "kind": "ordivon.plugin-gateway-execution-grant",
                "maxTimeoutMs": 300_000,
            },
            {"config": {"maxRuntimeMs": 900_000}},
        )
    with pytest.raises(CircuitContractError, match="Harness owner grant"):
        evaluate_owner_timeout_envelope(
            {"maxTimeoutMs": 300_000}, {"config": {"maxRuntimeMs": 900_000}}
        )


def test_owner_timeout_envelope_uses_real_pacti_and_scopes_live_claims() -> None:
    # Pacti is a task-local mathematics provider, intentionally NOT a Next
    # project/default CI dependency. Explicit provider runs must execute this
    # integration test; normal CI reports a visible SKIP rather than falsely
    # claiming the external algebra passed.
    pytest.importorskip(
        "pacti", reason="run explicitly with uv run --with pacti==0.3.1"
    )
    from scripts.pacti_timeout_obligation_r1 import evaluate_owner_timeout_envelope

    grant = {
        "schemaVersion": 1,
        "kind": "ordivon.plugin-gateway-execution-grant",
        "maxTimeoutMs": 300_000,
    }
    # This is a supplied owner-style status projection, not a claim to have
    # queried any deployed Runtime. The active Runtime may differ.
    adequate = {"config": {"maxRuntimeMs": 86_400_000}}
    insufficient = {"config": {"maxRuntimeMs": 60_000}}
    good = evaluate_owner_timeout_envelope(grant, adequate)
    bad = evaluate_owner_timeout_envelope(grant, insufficient)
    assert good["modelStanding"] == "COMPATIBLE"
    assert bad["modelStanding"] == "INCOMPATIBLE"
    assert good["observationDigest"] != bad["observationDigest"]
    assert good["pactiVersion"] == bad["pactiVersion"] == "0.3.1"
    assert "freshness" in good["nonClaims"][0]
    assert "does not prove" in good["nonClaims"][1]
    assert "never grants" in good["nonClaims"][2]
