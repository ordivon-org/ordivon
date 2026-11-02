#!/usr/bin/env python3
"""Pacti shadow dogfood through Verification Obligation R1.

This script is intentionally not part of default project dependencies. Run it in an
ephemeral environment with exact pacti==0.3.1. It proves only algebraic compatibility of
the frozen timeout seam model and exercises the task-local obligation/binding thin waist.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from ordivon_composition import (
    CircuitContractError,
    canonical_digest,
    compile_verification_obligations,
    evaluate_gate_results,
    resolve_verifier_bindings,
    validate_gate_result,
)

# One representation is shared by package imports and standalone CLI use.
if __package__:
    from .pacti_timeout_binding_r1 import (
        build_binding_set,
        build_manifest,
        validate_spec,
    )
else:
    from pacti_timeout_binding_r1 import (
        build_binding_set,
        build_manifest,
        validate_spec,
    )


def _load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise CircuitContractError(f"{path}: root must be an object")
    return value


def _contract_bundle(grant_max_ms: int, runtime_max_ms: int):
    try:
        import pacti
        from pacti.contracts import PolyhedralIoContract as Contract
    except ModuleNotFoundError as exc:
        raise CircuitContractError(
            "Pacti is not installed; run with uv --isolated --with pacti==0.3.1"
        ) from exc

    version = getattr(pacti, "__version__", None)
    if version != "0.3.1":
        raise CircuitContractError(f"unexpected Pacti version: {version}")

    grant = Contract.from_strings(
        [],
        ["t_grant >= 1", f"t_grant <= {grant_max_ms}"],
        [],
        ["t_grant"],
    )
    gateway = Contract.from_strings(
        [],
        ["t_gateway - t_grant = 0"],
        ["t_grant"],
        ["t_gateway"],
    )
    runtime = Contract.from_strings(
        ["t_gateway >= 1", f"t_gateway <= {runtime_max_ms}"],
        ["t_runtime - t_gateway = 0"],
        ["t_gateway"],
        ["t_runtime"],
    )
    top = Contract.from_strings(
        [],
        ["t_runtime >= 1", f"t_runtime <= {grant_max_ms}"],
        [],
        ["t_runtime"],
    )
    return grant, gateway, runtime, top


def execute_pacti(spec: dict[str, Any]) -> dict[str, Any]:
    validate_spec(spec)
    accepted = spec["acceptedCase"]
    grant, gateway, runtime, top = _contract_bundle(
        accepted["grantMaxMs"],
        accepted["runtimeMaxMs"],
    )
    known = grant.compose(gateway)
    composed = known.compose(runtime)
    accepted_refines = composed.refines(top)

    quotient = top.quotient(known)
    quotient_recomposes = known.compose(quotient).refines(top)

    mismatch = spec["deliberateMismatch"]
    bad_grant, bad_gateway, bad_runtime, _ = _contract_bundle(
        mismatch["grantMaxMs"],
        mismatch["runtimeMaxMs"],
    )
    from pacti.utils.errors import IncompatibleArgsError

    mismatch_error_type: str | None = None
    mismatch_error: str | None = None
    rejected_by_pacti = False
    try:
        bad_grant.compose(bad_gateway).compose(bad_runtime)
    except IncompatibleArgsError as exc:
        # Only Pacti's real typed rejection can discharge this verifier
        # obligation. Unrelated failures propagate; equal class names do not
        # establish that an external mathematical provider rejected a model.
        mismatch_error_type = type(exc).__name__
        mismatch_error = str(exc)
        rejected_by_pacti = True

    formal = {
        "pactiVersion": spec["pactiVersion"],
        "acceptedCase": {
            "grantMaxMs": accepted["grantMaxMs"],
            "runtimeMaxMs": accepted["runtimeMaxMs"],
            "composedContract": composed.to_dict(),
            "refinesTopRequirement": accepted_refines,
        },
        "quotient": {
            "contract": quotient.to_dict(),
            "recomposedRefinesTopRequirement": quotient_recomposes,
        },
        "deliberateMismatch": {
            "grantMaxMs": mismatch["grantMaxMs"],
            "runtimeMaxMs": mismatch["runtimeMaxMs"],
            "errorType": mismatch_error_type,
            "error": mismatch_error,
            "rejected": rejected_by_pacti,
        },
    }
    formal["formalResultDigest"] = canonical_digest(formal)
    return formal


def evaluate_owner_timeout_envelope(
    grant_wire: dict[str, Any],
    runtime_status: dict[str, Any],
) -> dict[str, Any]:
    """Check a *supplied* Harness grant against a *supplied* Runtime config.

    Reuse Pacti algebra; do not install a new contract kernel, make a stale
    frozen model authoritative, or infer the source/age of either observation.
    The caller must separately establish current source and runtime identity.
    """
    if not isinstance(grant_wire, dict) or (
        type(grant_wire.get("schemaVersion")) is not int
        or grant_wire.get("schemaVersion") != 1
        or grant_wire.get("kind") != "ordivon.plugin-gateway-execution-grant"
    ):
        raise CircuitContractError("expected the Harness owner grant wire")
    grant_max = grant_wire.get("maxTimeoutMs")
    config = runtime_status.get("config") if isinstance(runtime_status, dict) else None
    runtime_max = config.get("maxRuntimeMs") if isinstance(config, dict) else None
    for name, bound in (
        ("grant.maxTimeoutMs", grant_max),
        ("runtime.config.maxRuntimeMs", runtime_max),
    ):
        if type(bound) is not int or bound <= 0 or bound > (2**64 - 1):
            raise CircuitContractError(f"missing or invalid {name} observation")
    if grant_max > 900_000:
        raise CircuitContractError("grant timeout exceeds the Harness owner contract")

    from pacti.utils.errors import IncompatibleArgsError

    grant, gateway, runtime, top = _contract_bundle(grant_max, runtime_max)
    # These are actual Pacti operations, NOT custom limit arithmetic.
    # A failed composition is a counterexample to the declared whole-domain
    # compatibility; it is not permission to weaken the Runtime admission.
    try:
        composed = grant.compose(gateway).compose(runtime)
        refines_top = composed.refines(top)
    except IncompatibleArgsError:
        refines_top = False

    projection = {
        "schemaVersion": 1,
        "kind": "ordivon.pacti-observed-owner-timeout-projection",
        "pactiVersion": "0.3.1",
        "grantMaxMs": grant_max,
        "runtimeMaxMs": runtime_max,
        "modelStanding": "COMPATIBLE" if refines_top else "INCOMPATIBLE",
        "observationDigest": canonical_digest(
            {"grant": grant_wire, "runtimeStatus": runtime_status}
        ),
        "supportScope": "Polyhedral timeout-domain composition/refinement of supplied owner observations only.",
        "nonClaims": [
            "Snapshots are caller supplied; freshness and producer authenticity were not established.",
            "Pacti does not prove Harness/Gateway/Runtime code implements this model.",
            "A compatible model never grants effect execution authority.",
        ],
    }
    projection["projectionDigest"] = canonical_digest(projection)
    return projection


def run(spec: dict[str, Any]) -> dict[str, Any]:
    manifest = build_manifest(spec)
    obligations = compile_verification_obligations(manifest)
    bindings = build_binding_set(obligations, spec)
    resolution = resolve_verifier_bindings(obligations, bindings)
    formal = execute_pacti(spec)

    accepted = formal["acceptedCase"]["refinesTopRequirement"]
    quotient = formal["quotient"]["recomposedRefinesTopRequirement"]
    mismatch = formal["deliberateMismatch"]["rejected"]
    standing = "SATISFIED" if accepted and quotient and mismatch else "UNSATISFIED"

    gate = manifest["gateRequirements"][0]
    result = {
        "schemaVersion": 1,
        "kind": "ordivon.composition-gate-result",
        "circuitId": manifest["circuitId"],
        "manifestDigest": obligations["circuitRef"]["digest"],
        "gateId": gate["id"],
        "verifierOwnerId": gate["verifierOwnerId"],
        "standing": standing,
        "evidenceRefs": [
            f"pacti-provider:{bindings['bindings'][0]['verifierRef']['digest']}",
            f"pacti-spec:{canonical_digest(spec)}",
            f"pacti-run:{formal['formalResultDigest']}",
        ],
        "supportScope": gate["supportScope"],
        "nonClaims": [
            "Pacti PASS establishes only the frozen algebraic contract relation.",
            "Pacti PASS does not prove Gateway or Runtime implementation conformance.",
            "Pacti PASS does not grant execution authority or establish domain acceptance.",
        ],
    }
    from ordivon_composition import compile_manifest

    validate_gate_result(manifest, compile_manifest(manifest), result)
    projection = evaluate_gate_results(manifest, [result])

    output = {
        "schemaVersion": 1,
        "kind": "ordivon.verification-obligation-pacti-shadow-r2",
        "specRef": {
            "id": spec["id"],
            "digest": canonical_digest(spec),
        },
        "obligationSet": obligations,
        "bindingSet": bindings,
        "resolution": resolution,
        "formalResult": formal,
        "gateResult": result,
        "projection": projection,
        "nonClaims": list(spec["nonClaims"]),
    }
    output["resultDigest"] = canonical_digest(output)
    return output


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("spec", type=Path, nargs="?")
    parser.add_argument("--owner-grant", type=Path)
    parser.add_argument("--runtime-status", type=Path)
    args = parser.parse_args()
    observed = args.owner_grant is not None or args.runtime_status is not None
    if observed:
        if (
            args.spec is not None
            or args.owner_grant is None
            or args.runtime_status is None
        ):
            parser.error(
                "owner observation requires both --owner-grant and --runtime-status, without spec"
            )
    elif args.spec is None:
        parser.error("spec or both owner observation files are required")
    try:
        if observed:
            result = evaluate_owner_timeout_envelope(
                _load(args.owner_grant),
                _load(args.runtime_status),
            )
        else:
            result = run(_load(args.spec))
    except (OSError, json.JSONDecodeError, CircuitContractError) as exc:
        raise SystemExit(f"Pacti timeout obligation R2 failed: {exc}") from exc
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
