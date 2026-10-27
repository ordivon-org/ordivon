"""Bounded actual C06 implementation/refinement against Lean-computed model.

Lean verifies the abstract model. This tests all 16 boolean observation
classes for the scoped next-read projection; external effects, JSON provenance,
live environment and unseen Python paths are NOT proved by this bridge.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from ordivon_composition.effect_reconciliation_r1 import qualify_execution_effect_frontier

REPO = Path(__file__).resolve().parents[3]
FORMAL = REPO / "tools" / "formal"
OP = "ordivon-exec:v1:external.pull:effect-bridge-r21"
EFFECT = f"effect:{OP}"
EXPECTED_STANDINGS = {
    "proof:effect": "UNKNOWN",
    "proof:consumer": "UNKNOWN",
    "proof:independent": "REUSE_CANDIDATE",
}
GRAPH = {
    "authorityRefs": [EFFECT, "source:independent"],
    "obligations": [
        {"id": "proof:effect", "dependsOn": [EFFECT], "dependenciesComplete": True},
        {"id": "proof:consumer", "dependsOn": ["proof:effect"], "dependenciesComplete": True},
        {
            "id": "proof:independent",
            "dependsOn": ["source:independent"],
            "dependenciesComplete": True,
        },
    ],
}


def _observed(terminal: bool, recovery: bool, unknown: bool, reconcile: bool) -> dict[str, object]:
    return {
        "kind": "ordivon.gateway-execution-observation",
        "schema_version": 1,
        "owner_id": "external.pull",
        "native_id": "effect-bridge-r21",
        "operation_ref": OP,
        "terminal": terminal,
        "recovery_required": recovery,
        "delivery_disposition": "unknown" if unknown else "committed",
        "state": "reconcile_required" if reconcile else "completed",
        "capability": "external.effect.readback",
        "execution_disposition": "succeeded",
        "exit_code": 0,
    }


def test_effect_reconciliation_matches_kernel_checked_lean_model_full_boolean_cut():
    try:
        lean = subprocess.run(
            ["mise", "which", "lean"],
            cwd=FORMAL,
            capture_output=True,
            text=True,
            check=True,
            timeout=15,
        ).stdout.strip()
    except (OSError, subprocess.CalledProcessError) as exc:
        pytest.skip(f"pinned native Lean unavailable in this environment: {exc}")
    result = subprocess.run(
        [lean, "--run", str(FORMAL / "EffectReconciliationR21.lean")],
        cwd=FORMAL,
        capture_output=True,
        text=True,
        timeout=45,
        check=True,
    )
    seen: set[tuple[bool, bool, bool, bool]] = set()
    routes: set[str] = set()
    for line in result.stdout.splitlines():
        fields = line.split("|")
        assert len(fields) == 5, line
        bits = tuple(x == "1" for x in fields[:4])
        assert len(bits) == 4
        assert all(x in ("0", "1") for x in fields[:4])
        assert bits not in seen
        seen.add(bits)
        observed = qualify_execution_effect_frontier(
            observation=_observed(*bits),
            expected_operation_ref=OP,
            proof_graph=GRAPH,
        )
        routes.add(observed["recommendedNextRead"])
        assert observed["recommendedNextRead"] == fields[4]
        assert observed["automaticRetryAdmissible"] is False
        assert observed["providerEffectEstablished"] is False
        assert observed["proofReuseAdmissible"] is False
        standings = {
            item["id"]: item["standing"] for item in observed["selection"]["standingByObligation"]
        }
        assert standings == EXPECTED_STANDINGS
        assert observed["selection"]["proofReuseAdmissible"] is False
    assert len(seen) == 16  # no vacuous state omission
    assert routes == {
        "OBSERVE_ORIGINAL_OPERATION",
        "RECONCILE_ORIGINAL_OPERATION",
        "VERIFY_DOMAIN_EFFECT_WITH_OWNER",
    }
