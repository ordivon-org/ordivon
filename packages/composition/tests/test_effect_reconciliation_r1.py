from __future__ import annotations

import json
import subprocess
import sys

import pytest

from ordivon_composition.cognitive_circuit_r1 import CircuitContractError
from ordivon_composition.effect_reconciliation_r1 import (
    qualify_execution_effect_frontier,
)

OP = "ordivon-exec:v1:external.pull:operation-one"
EFFECT = f"effect:{OP}"


def gateway_observation(
    *,
    state="reconcile_required",
    terminal=False,
    delivery="unknown",
    recovery=True,
):
    return {
        "schema_version": 1,
        "kind": "ordivon.gateway-execution-observation",
        "operation_ref": OP,
        "owner_id": "external.pull",
        "native_id": "operation-one",
        "capability": "muse.shell.echo",
        "state": state,
        "terminal": terminal,
        "delivery_disposition": delivery,
        "execution_disposition": "succeeded" if terminal else "unknown",
        "recovery_required": recovery,
        "exit_code": 0 if terminal else None,
    }


def graph(*, indexed=True):
    return {
        "authorityRefs": [EFFECT, "source:media"] if indexed else ["source:media"],
        "obligations": [
            {
                "id": "proof:write",
                "dependsOn": [EFFECT] if indexed else ["source:media"],
                "dependenciesComplete": True,
            },
            {
                "id": "proof:consumer",
                "dependsOn": ["proof:write"],
                "dependenciesComplete": True,
            },
            {
                "id": "proof:media",
                "dependsOn": ["source:media"],
                "dependenciesComplete": True,
            },
        ],
    }


def qualify(obs=None, *, indexed=True):
    return qualify_execution_effect_frontier(
        observation=gateway_observation() if obs is None else obs,
        expected_operation_ref=OP,
        proof_graph=graph(indexed=indexed),
    )


def standings(value):
    return {r["id"]: r["standing"] for r in value["selection"]["standingByObligation"]}


def test_expired_started_attempt_reconciles_exact_operation_and_fences_replay():
    result = qualify()
    assert result["recommendedNextRead"] == "RECONCILE_ORIGINAL_OPERATION"
    assert result["automaticRetryAdmissible"] is False
    assert result["providerEffectEstablished"] is False
    assert result["proofReuseAdmissible"] is False
    assert standings(result) == {
        "proof:write": "UNKNOWN",
        "proof:consumer": "UNKNOWN",
        "proof:media": "REUSE_CANDIDATE",
    }


def test_terminal_success_and_committed_delivery_do_not_prove_domain_effect():
    result = qualify(
        gateway_observation(state="completed", terminal=True, delivery="committed", recovery=False)
    )
    assert result["recommendedNextRead"] == "VERIFY_DOMAIN_EFFECT_WITH_OWNER"
    assert result["automaticRetryAdmissible"] is False
    assert standings(result)["proof:write"] == "UNKNOWN"


def test_active_operation_is_observed_not_retried():
    result = qualify(
        gateway_observation(state="started", terminal=False, delivery="in_progress", recovery=False)
    )
    assert result["recommendedNextRead"] == "OBSERVE_ORIGINAL_OPERATION"
    assert result["automaticRetryAdmissible"] is False


def test_undeclared_dynamic_effect_does_not_get_false_zero_impact():
    result = qualify(indexed=False)
    assert result["selection"]["unindexedChangeRefs"] == [EFFECT]
    assert set(standings(result).values()) == {"UNKNOWN"}


@pytest.mark.parametrize(
    "change",
    [
        {"terminal": "false"},
        {"terminal": 0},
        {"recovery_required": "false"},
        {"delivery_disposition": "maybe_committed"},
        {"exit_code": True},
        {"native_id": "other-attempt"},
        {"operation_ref": "other"},
        {"schema_version": True},
        {"kind": "ordivon.fake-observation"},
    ],
)
def test_forged_identity_and_boolean_fields_refused(change):
    bad = gateway_observation()
    bad.update(change)
    with pytest.raises(CircuitContractError):
        qualify(bad)


def test_existing_cli_rejects_wrong_operation_and_emits_bounded_impact(tmp_path):
    observation_path = tmp_path / "gateway.json"
    proof_graph_path = tmp_path / "graph.json"
    observation_path.write_text(json.dumps(gateway_observation()))
    proof_graph_path.write_text(json.dumps(graph()))
    cmd = [
        sys.executable,
        "-m",
        "ordivon_composition.effect_reconciliation_r1",
        str(observation_path),
        str(proof_graph_path),
        "--expected-operation-ref",
        OP,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    value = json.loads(result.stdout)
    assert value["recommendedNextRead"] == "RECONCILE_ORIGINAL_OPERATION"
    assert value["selection"]["proofReuseAdmissible"] is False
    altered = subprocess.run([*cmd[:-1], OP + "-forged"], capture_output=True, text=True)
    assert altered.returncode != 0
    assert "identity mismatch" in altered.stderr
