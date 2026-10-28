from __future__ import annotations

import json
import subprocess
import sys
import tomllib
from pathlib import Path

import pytest
from ordivon_composition import (
    CircuitContractError,
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


@pytest.mark.parametrize(
    ("case", "field"),
    [
        ("acceptedCase", "grantMaxMs"),
        ("acceptedCase", "runtimeMaxMs"),
        ("deliberateMismatch", "grantMaxMs"),
        ("deliberateMismatch", "runtimeMaxMs"),
    ],
)
def test_pacti_formal_timeout_spec_rejects_boolean_as_integer(
    case: str, field: str
) -> None:
    """Every formal input bound must reject JSON true rather than alias 1 ms."""
    spec = _spec()
    spec[case][field] = True
    with pytest.raises(CircuitContractError, match="must be a positive integer"):
        validate_spec(spec)


def test_pacti_formal_spec_rejects_boolean_schema_version() -> None:
    """True must not alias schemaVersion=1 during formal-spec admission."""
    spec = _spec()
    spec["schemaVersion"] = True
    with pytest.raises(CircuitContractError, match="schemaVersion must equal 1"):
        validate_spec(spec)


def test_pacti_algebra_mismatch_requires_actual_provider_exception_type(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A foreign exception named like Pacti must never satisfy a proof gate."""
    pytest.importorskip("pacti", reason="explicit external Pacti test")
    import scripts.pacti_timeout_obligation_r1 as verifier

    spec = _spec()
    native_contract_bundle = verifier._contract_bundle

    class ForeignError(Exception):
        pass

    # Same apparent string name as Pacti's real error, different type.
    ForeignError.__name__ = "IncompatibleArgsError"

    class BogusContract:
        def compose(self, _other: object) -> object:
            raise ForeignError("unrelated bogus verifier failure")

    def swapped_contract_bundle(grant_max_ms: int, runtime_max_ms: int):
        if grant_max_ms == spec["deliberateMismatch"]["grantMaxMs"]:
            return (BogusContract(), BogusContract(), BogusContract(), BogusContract())
        return native_contract_bundle(grant_max_ms, runtime_max_ms)

    monkeypatch.setattr(verifier, "_contract_bundle", swapped_contract_bundle)
    with pytest.raises(ForeignError, match="unrelated bogus verifier failure"):
        verifier.execute_pacti(spec)
    # The error may not be admitted as a SATISFIED Composition Gate either.
    with pytest.raises(ForeignError, match="unrelated bogus verifier failure"):
        verifier.run(spec)


def test_agent_cli_observes_actual_owner_contract_via_native_pacti(
    tmp_path: Path,
) -> None:
    pytest.importorskip("pacti", reason="the owner CLI needs the real algebra provider")
    grant = tmp_path / "owner-grant.json"
    runtime = tmp_path / "runtime-status.json"
    grant.write_text(
        json.dumps(
            {
                "schemaVersion": 1,
                "kind": "ordivon.plugin-gateway-execution-grant",
                "maxTimeoutMs": 300000,
            }
        ),
        encoding="utf-8",
    )
    runtime.write_text(
        json.dumps({"config": {"maxRuntimeMs": 86400000}}), encoding="utf-8"
    )
    completed = subprocess.run(
        [
            sys.executable,
            str(NEXT_ROOT / "scripts/pacti_timeout_obligation_r1.py"),
            "--owner-grant",
            str(grant),
            "--runtime-status",
            str(runtime),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr
    result = json.loads(completed.stdout)
    assert result["kind"] == "ordivon.pacti-observed-owner-timeout-projection"
    assert result["modelStanding"] == "COMPATIBLE"
    assert result["pactiVersion"] == "0.3.1"
    assert result["grantMaxMs"] == 300000
    assert result["runtimeMaxMs"] == 86400000
    assert "freshness" in result["nonClaims"][0]


@pytest.mark.parametrize(
    ("max_ms", "standing"),
    [(60_000, "INCOMPATIBLE"), (300_000, "COMPATIBLE")],
)
def test_agent_cli_reports_real_pacti_incompatibility_and_boundary(
    tmp_path: Path,
    max_ms: int,
    standing: str,
) -> None:
    pytest.importorskip("pacti", reason="real Pacti algebra required")
    grant = tmp_path / "grant.json"
    status = tmp_path / "status.json"
    grant.write_text(
        json.dumps(
            {
                "schemaVersion": 1,
                "kind": "ordivon.plugin-gateway-execution-grant",
                "maxTimeoutMs": 300_000,
            }
        ),
        encoding="utf-8",
    )
    status.write_text(
        json.dumps({"config": {"maxRuntimeMs": max_ms}}), encoding="utf-8"
    )
    result = subprocess.run(
        [
            sys.executable,
            str(NEXT_ROOT / "scripts/pacti_timeout_obligation_r1.py"),
            "--owner-grant",
            str(grant),
            "--runtime-status",
            str(status),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    body = json.loads(result.stdout)
    assert body["modelStanding"] == standing
    assert "never grants" in body["nonClaims"][-1]
    assert body["grantMaxMs"] == 300_000


@pytest.mark.parametrize(
    "runtime_status", [{}, {"config": {}}, {"config": {"maxRuntimeMs": True}}]
)
def test_agent_cli_refuses_unknown_owner_runtime_input(
    tmp_path: Path,
    runtime_status: dict,
) -> None:
    grant = tmp_path / "grant.json"
    status = tmp_path / "status.json"
    grant.write_text(
        json.dumps(
            {
                "schemaVersion": 1,
                "kind": "ordivon.plugin-gateway-execution-grant",
                "maxTimeoutMs": 300_000,
            }
        ),
        encoding="utf-8",
    )
    status.write_text(json.dumps(runtime_status), encoding="utf-8")
    result = subprocess.run(
        [
            sys.executable,
            str(NEXT_ROOT / "scripts/pacti_timeout_obligation_r1.py"),
            "--owner-grant",
            str(grant),
            "--runtime-status",
            str(status),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode != 0
    assert "missing or invalid runtime.config.maxRuntimeMs" in result.stderr
    assert not result.stdout.strip()


def test_agent_cli_keeps_existing_frozen_spec_entrypoint() -> None:
    pytest.importorskip("pacti", reason="real Pacti algebra required")
    completed = subprocess.run(
        [
            sys.executable,
            str(NEXT_ROOT / "scripts/pacti_timeout_obligation_r1.py"),
            str(SPEC),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr
    assert (
        json.loads(completed.stdout)["kind"]
        == "ordivon.verification-obligation-pacti-shadow-r2"
    )


@pytest.mark.parametrize(
    "args",
    [
        ["--owner-grant", "foo.json"],
        ["--runtime-status", "foo.json"],
        ["--owner-grant", "foo.json", "--runtime-status", "bar.json", "spec.json"],
    ],
)
def test_agent_cli_rejects_partial_or_mixed_authority_inputs(args: list[str]) -> None:
    completed = subprocess.run(
        [
            sys.executable,
            str(NEXT_ROOT / "scripts/pacti_timeout_obligation_r1.py"),
            *args,
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == 2
    assert "without spec" in completed.stderr
    assert completed.stdout == ""
