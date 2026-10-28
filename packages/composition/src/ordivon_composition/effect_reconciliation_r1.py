#!/usr/bin/env python3
"""Task-local effect uncertainty fence over the existing Gateway observation.

R2.1 contract: classify what must be observed/reconciled and send UNKNOWN to
the existing incremental proof selector. No dispatch, retry, new effect store
or authority. Only Gateway/Runtime owns execution truth; only the effect owner
can certify provider-side completion.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from .cognitive_circuit_r1 import CircuitContractError, _load_json
from .verification_obligation_r1 import select_impacted_obligations

OWNERS = frozenset({"runtime.linux", "runtime.windows", "external.pull"})
DELIVERY = frozenset({"unknown", "in_progress", "committed"})


def qualify_execution_effect_frontier(
    *,
    observation: dict[str, Any],
    expected_operation_ref: str,
    proof_graph: dict[str, Any],
) -> dict[str, Any]:
    """Read-only task-local projection; supplied JSON is not owner-authenticated."""
    if (
        not isinstance(observation, dict)
        or observation.get("kind") != "ordivon.gateway-execution-observation"
        or type(observation.get("schema_version")) is not int
        or observation["schema_version"] != 1
    ):
        raise CircuitContractError("Gateway observation kind/version required")
    owner, native_id = observation.get("owner_id"), observation.get("native_id")
    ref = observation.get("operation_ref")
    if (
        not isinstance(owner, str)
        or owner not in OWNERS
        or not isinstance(native_id, str)
        or not native_id
        or native_id != native_id.strip()
        or not native_id.isprintable()
        or ":" in native_id
        or ref != f"ordivon-exec:v1:{owner}:{native_id}"
        or ref != expected_operation_ref
    ):
        raise CircuitContractError("Gateway observation identity mismatch")
    if type(observation.get("terminal")) is not bool:
        raise CircuitContractError("Gateway terminality requires JSON boolean")
    recovery = observation.get("recovery_required")
    if recovery is not None and type(recovery) is not bool:
        raise CircuitContractError("Gateway recovery_required requires JSON boolean")
    delivery = observation.get("delivery_disposition")
    if delivery is not None and (not isinstance(delivery, str) or delivery not in DELIVERY):
        raise CircuitContractError("Gateway delivery disposition is unqualified")
    for field in ("state", "capability"):
        v = observation.get(field)
        if not isinstance(v, str) or not v or v != v.strip():
            raise CircuitContractError(f"Gateway {field} is missing")
    disposition = observation.get("execution_disposition")
    if disposition is not None and (not isinstance(disposition, str) or not disposition.strip()):
        raise CircuitContractError("Gateway execution disposition invalid")
    exit_code = observation.get("exit_code")
    if exit_code is not None and type(exit_code) is not int:
        raise CircuitContractError("Gateway exit_code must be integer")
    if not isinstance(proof_graph, dict) or set(proof_graph) != {"authorityRefs", "obligations"}:
        raise CircuitContractError("task-local proof graph needs exact fields")

    effect_ref = f"effect:{ref}"
    # Missing reference => selector unindexed change => conservative UNKNOWN
    # for all nodes, not incorrect zero impact.
    impact = select_impacted_obligations(
        authority_refs=proof_graph["authorityRefs"],
        obligations=proof_graph["obligations"],
        changed_refs=[],
        unknown_refs=[effect_ref],
    )
    if recovery is True or delivery == "unknown" or observation["state"] == ("reconcile_required"):
        next_read = "RECONCILE_ORIGINAL_OPERATION"
    elif not observation["terminal"]:
        next_read = "OBSERVE_ORIGINAL_OPERATION"
    else:
        # A terminal process with exit code zero and committed delivery
        # is still NOT evidence of a successful external effect.
        next_read = "VERIFY_DOMAIN_EFFECT_WITH_OWNER"
    return {
        "kind": "ordivon.task-local-external-effect-reconciliation-frontier",
        "truthRole": "caller-supplied-gateway-shape-not-owner-authenticated",
        "operationRef": ref,
        "effectRef": effect_ref,
        "recommendedNextRead": next_read,
        "automaticRetryAdmissible": False,
        "providerEffectEstablished": False,
        "proofReuseAdmissible": False,
        "selection": impact,
        "nonClaims": [
            "This adapter neither dispatches nor retries an operation.",
            "Gateway-shaped JSON does not authenticate an owner readback.",
            "Runtime result and committed delivery are not external effect receipts.",
            "External provider idempotency and effect completion remain unknown.",
            "Unindexed effect reference broadens UNKNOWN, never narrows impact.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Read-only external-effect frontier")
    parser.add_argument("gateway_observation", type=Path)
    parser.add_argument("proof_graph", type=Path)
    parser.add_argument("--expected-operation-ref", required=True)
    args = parser.parse_args()
    try:
        result = qualify_execution_effect_frontier(
            observation=_load_json(args.gateway_observation),
            expected_operation_ref=args.expected_operation_ref,
            proof_graph=_load_json(args.proof_graph),
        )
    except (OSError, json.JSONDecodeError, CircuitContractError) as exc:
        raise SystemExit(f"effect reconciliation refused: {exc}") from exc
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
