from __future__ import annotations

import ast
import json
import subprocess
import sys
from itertools import product
from pathlib import Path

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


def test_c04_to_c06_plan_consumer_binding_matches_real_import_and_call():
    """Close one actual first-party SOURCE consumer seam, not deployed behavior.

    A planning claim alone is not a runtime consumer. Require the exact C06
    Python source to import AND call the C04 selector, and to preserve the
    explicit unknown-effects safety contract and native test evidence.
    """
    root = Path(__file__).resolve().parents[1]
    plan = json.loads((root / "planning/lego-plan-r1.json").read_text())
    c04 = next(node for node in plan["nodes"] if node["id"] == "C04")
    c06 = next(node for node in plan["nodes"] if node["id"] == "C06")
    assert "C04" in c06["dependencies"]
    path = "packages/composition/src/ordivon_composition/effect_reconciliation_r1.py"
    bindings = [row for row in c04["consumerBindings"] if row["path"] == path]
    assert len(bindings) == 1
    assert "SOURCE_AST_DIRECT_IMPORT_AND_CALL" in bindings[0]["standing"]
    assert "INSTALLED_AND_DOMAIN_EFFECT_UNKNOWN" in bindings[0]["standing"]
    tree = ast.parse((root / "src/ordivon_composition/effect_reconciliation_r1.py").read_text())
    imports = [node for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)]
    assert any(
        node.level == 1
        and node.module == "verification_obligation_r1"
        and any(alias.name == "select_impacted_obligations" for alias in node.names)
        for node in imports
    )
    target = next(
        node
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name == "qualify_execution_effect_frontier"
    )
    assert any(
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "select_impacted_obligations"
        for node in ast.walk(target)
    )
    assert "formal/EffectReplayFence.tla" in c06["evidence"]
    assert "tests/test_effect_reconciliation_r1.py" in c06["evidence"]
    assert "MODEL" in c06["qualification"] and "INSTALLED_EFFECT_UNKNOWN" in c06["qualification"]


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


def test_c06_concrete_decision_matches_formal_policy_over_complete_finite_abstraction():
    """72 classified abstract inputs; test relation, NOT proof of Python refinement.

    The native pinned-TLC EffectReplayFence model exhausts this same input
    partition. Checking these concrete representative JSON inputs provides a
    finite correspondence witness, not proof of runtime/provider behavior.
    """
    tested = 0
    for state, terminal, recovery, delivery, indexed in product(
        ("started", "reconcile_required", "completed"),
        (False, True),
        (False, True),
        ("unknown", "in_progress", "committed"),
        (False, True),
    ):
        record = gateway_observation(
            state=state,
            terminal=terminal,
            recovery=recovery,
            delivery=delivery,
        )
        result = qualify_execution_effect_frontier(
            observation=record,
            expected_operation_ref=OP,
            proof_graph=graph(indexed=indexed),
        )
        if recovery or delivery == "unknown" or state == "reconcile_required":
            expected = "RECONCILE_ORIGINAL_OPERATION"
        elif not terminal:
            expected = "OBSERVE_ORIGINAL_OPERATION"
        else:
            expected = "VERIFY_DOMAIN_EFFECT_WITH_OWNER"
        assert result["recommendedNextRead"] == expected
        assert result["automaticRetryAdmissible"] is False
        assert result["providerEffectEstablished"] is False
        assert result["proofReuseAdmissible"] is False
        expected_standing = (
            {
                "proof:write": "UNKNOWN",
                "proof:consumer": "UNKNOWN",
                "proof:media": "REUSE_CANDIDATE",
            }
            if indexed
            else {"proof:write": "UNKNOWN", "proof:consumer": "UNKNOWN", "proof:media": "UNKNOWN"}
        )
        assert standings(result) == expected_standing
        assert result["selection"]["unindexedChangeRefs"] == ([] if indexed else [EFFECT])
        tested += 1
    assert tested == 72
