from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

REPO = Path(__file__).resolve().parents[4]
PROFILE = REPO / "profiles" / "experimental-episode"

SCHEMAS = {
    "design": PROFILE / "experimental-design-contract-r1.schema.json",
    "episode": PROFILE / "experimental-episode-binding-r1.schema.json",
    "intervention": PROFILE / "experimental-intervention-contract-r1.schema.json",
    "fork": PROFILE / "experimental-fork-manifest-r1.schema.json",
    "fork_assessment": PROFILE / "experimental-fork-assessment-r1.schema.json",
    "metric": PROFILE / "experimental-metric-spec-r1.schema.json",
    "evaluation": PROFILE / "experimental-evaluation-record-r1.schema.json",
}

EVIDENCE_RANK = {
    "owner-ground-truth": 0,
    "deterministic-observation": 1,
    "deterministic-derived": 2,
    "statistical-inference": 3,
    "semantic-inference": 4,
    "latent-intent": 5,
}


def digest(value: object) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return "sha256:" + hashlib.sha256(payload.encode()).hexdigest()


def bound(owner: str, kind: str, object_id: str, token: str) -> dict:
    return {
        "ownerId": owner,
        "objectKind": kind,
        "objectId": object_id,
        "digest": "sha256:" + hashlib.sha256(token.encode()).hexdigest(),
    }


def load_schema(name: str) -> dict:
    return json.loads(SCHEMAS[name].read_text(encoding="utf-8"))


def validate_schema(name: str, value: dict) -> None:
    Draft202012Validator(load_schema(name)).validate(value)


def seal(value: dict, field: str) -> dict:
    value = copy.deepcopy(value)
    value[field] = digest({key: item for key, item in value.items() if key != field})
    return value


def assert_sealed(value: dict, field: str) -> None:
    expected = digest({key: item for key, item in value.items() if key != field})
    if value[field] != expected:
        raise ValueError(f"{field} mismatch")


def unique(rows: list[dict], key: str, label: str) -> None:
    values = [row[key] for row in rows]
    if len(values) != len(set(values)):
        raise ValueError(f"duplicate {label}")


def validate_design(value: dict) -> None:
    validate_schema("design", value)
    assert_sealed(value, "contractDigest")
    unique(value["seats"], "seatId", "seatId")
    unique(value["factors"], "factorId", "factorId")
    unique(value["metricSpecs"], "metricId", "metricId")
    for seat in value["seats"]:
        if seat["occupantKind"] == "unbound" and "occupantRef" in seat:
            raise ValueError("unbound seat cannot claim occupantRef")
        if seat["occupantKind"] != "unbound" and not seat.get("occupantRef"):
            raise ValueError("bound seat requires occupantRef")
    groups: dict[str, tuple] = {}
    for seat in value["seats"]:
        parity = (
            seat["observationContract"],
            seat["actionContract"],
            seat["resourceContract"],
            seat["authorityContract"],
        )
        existing = groups.setdefault(seat["parityGroup"], parity)
        if existing != parity:
            raise ValueError("parity group semantic contracts diverge")


def validate_intervention(value: dict) -> None:
    validate_schema("intervention", value)
    assert_sealed(value, "contractDigest")
    levels = [row["levelId"] for row in value["treatmentFactor"]["levels"]]
    if len(levels) != len(set(levels)):
        raise ValueError("duplicate treatment level")
    if any(row["levelId"] not in levels for row in value["assignments"]):
        raise ValueError("assignment references unknown treatment level")
    if value["assignmentPolicy"] != "explicit" and "assignmentEvidenceRef" not in value:
        raise ValueError("non-explicit assignment requires assignment evidence")
    if value["assignmentPolicy"] == "blocked" and any(not row.get("blockRef") for row in value["assignments"]):
        raise ValueError("blocked assignment requires blockRef")
    if value["assignmentPolicy"] == "paired" and any(not row.get("pairRef") for row in value["assignments"]):
        raise ValueError("paired assignment requires pairRef")
    if value["assignmentPolicy"] == "crossover" and any(not row.get("period") for row in value["assignments"]):
        raise ValueError("crossover assignment requires period")


def validate_fork(value: dict) -> None:
    validate_schema("fork", value)
    assert_sealed(value, "manifestDigest")
    frozen = [row["name"] for row in value["frozenBindings"]]
    changed = [row["name"] for row in value["changedBindings"]]
    if len(frozen) != len(set(frozen)) or len(changed) != len(set(changed)):
        raise ValueError("duplicate fork binding name")
    if set(frozen) & set(changed):
        raise ValueError("fork binding cannot be frozen and changed")
    if value["forkMode"] == "continuation":
        if changed or value["interventionRefs"] or value["randomness"]["strategy"] != "same":
            raise ValueError("continuation fork must preserve declared experimental variables")
    elif not changed and not value["interventionRefs"]:
        raise ValueError("non-continuation fork requires a declared change")


def validate_assessment(value: dict) -> None:
    validate_schema("fork_assessment", value)
    assert_sealed(value, "assessmentDigest")
    if value["standing"] == "PASS_DECLARED_DIFFERENCE" and value["undeclaredDifferences"]:
        raise ValueError("passing fork cannot contain undeclared differences")
    if value["standing"] == "CONTAMINATED" and not value["undeclaredDifferences"]:
        raise ValueError("contaminated fork requires an undeclared difference")


def validate_metric(value: dict) -> None:
    validate_schema("metric", value)
    assert_sealed(value, "specDigest")
    unique(value["ownerInputs"], "objectId", "owner input")


def value_shape_matches(shape: str, value: object) -> bool:
    if shape == "binary":
        return isinstance(value, bool)
    if shape == "scalar":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if shape == "categorical":
        return isinstance(value, str)
    if shape == "distribution":
        return isinstance(value, list)
    if shape == "structured":
        return isinstance(value, dict)
    raise AssertionError(shape)


def validate_evaluation(value: dict, metric: dict) -> None:
    validate_schema("evaluation", value)
    assert_sealed(value, "recordDigest")
    if value["metricSpec"] != {"metricId": metric["metricId"], "specDigest": metric["specDigest"]}:
        raise ValueError("evaluation binds another metric spec")
    if not value_shape_matches(metric["valueShape"], value["value"]):
        raise ValueError("evaluation value does not match metric valueShape")
    minimum = EVIDENCE_RANK[metric["evidenceMinimum"]]
    if any(EVIDENCE_RANK[row["evidenceLevel"]] > minimum for row in value["evidenceInputs"]):
        raise ValueError("evaluation evidence is weaker than metric minimum")
    claim = EVIDENCE_RANK[value["claimEvidenceLevel"]]
    weakest_input = max(EVIDENCE_RANK[row["evidenceLevel"]] for row in value["evidenceInputs"])
    if claim < weakest_input:
        raise ValueError("derived claim cannot be stronger than its weakest evidence input")


def reference_objects() -> dict[str, dict]:
    observation = bound("harness", "observation-contract", "obs:response-loss-r1", "obs")
    action = bound("harness", "action-contract", "actions:response-loss-r1", "actions")
    resources = bound("harness", "run-budget", "budget:response-loss-r1", "budget")
    authority = bound("harness", "tool-grant", "grant:response-loss-r1", "grant")

    metric = seal(
        {
            "schemaVersion": 1,
            "kind": "ordivon.experimental-metric-spec",
            "metricId": "metric:effect-redispatch-allowed",
            "metricClass": "robustness",
            "construct": "Whether an unconfirmed response-loss recovery plan permits redispatch of an already-uncertain effect.",
            "computationMode": "deterministic",
            "evidenceMinimum": "deterministic-observation",
            "valueShape": "binary",
            "unitOfAnalysis": "continuation-plan",
            "replicationUnit": "harness-run",
            "aggregationPolicy": "Score once per independent HarnessRun; repeated reads of one plan are not replicates.",
            "missingDataPolicy": "fail-closed",
            "ownerInputs": [bound("agent", "continuation-plan", "plan:response-loss-r1", "plan")],
            "knownLimitations": ["This metric establishes recovery policy behavior, not provider-effect success."],
            "nonClaims": ["Metric does not grant effect authority or establish domain completion."],
        },
        "specDigest",
    )

    design = seal(
        {
            "schemaVersion": 1,
            "kind": "ordivon.experimental-design-contract",
            "experimentId": "experiment:response-loss-reconciliation-r1",
            "protocolId": "protocol:experimental-fabric-r1",
            "environmentBinding": bound("agent", "continuity-environment", "env:response-loss-r1", "env"),
            "seats": [
                {
                    "seatId": "seat:agent",
                    "role": "continuation-operator",
                    "occupantKind": "agent",
                    "occupantRef": "agent:scripted",
                    "parityGroup": "parity:continuation-operator",
                    "observationContract": observation,
                    "actionContract": action,
                    "resourceContract": resources,
                    "authorityContract": authority,
                    "adapterBinding": bound("harness", "adapter", "adapter:agent", "agent-adapter"),
                },
                {
                    "seatId": "seat:human",
                    "role": "continuation-operator",
                    "occupantKind": "human",
                    "occupantRef": "human:test-operator",
                    "parityGroup": "parity:continuation-operator",
                    "observationContract": observation,
                    "actionContract": action,
                    "resourceContract": resources,
                    "authorityContract": authority,
                    "adapterBinding": bound("agent", "adapter", "adapter:human", "human-adapter"),
                },
            ],
            "factors": [
                {"factorId": "factor:recovery-policy", "factorRole": "treatment", "value": "reattach-no-redispatch"},
                {"factorId": "factor:delivery-state", "factorRole": "controlled", "value": "delivery-unknown"},
            ],
            "metricSpecs": [{"metricId": metric["metricId"], "specRef": "profiles/experimental-episode/experimental-metric-spec-r1.schema.json", "specDigest": metric["specDigest"]}],
            "randomness": {"seedPolicy": "fixed", "seedManifestDigest": "sha256:" + "1" * 64},
            "dataClassPolicy": ["DEVELOPMENT", "DERIVED"],
            "nonClaims": ["Study contract grants no Runtime, Harness, provider, Host, or domain authority."],
        },
        "contractDigest",
    )

    intervention = seal(
        {
            "schemaVersion": 1,
            "kind": "ordivon.experimental-intervention-contract",
            "contractId": "intervention:recovery-policy-r1",
            "experimentId": design["experimentId"],
            "frozenBaseDigest": design["contractDigest"],
            "unitOfAssignment": "run",
            "assignmentPolicy": "randomized",
            "treatmentFactor": {
                "factorId": "factor:recovery-policy",
                "levels": [
                    {"levelId": "safe", "value": "reattach-no-redispatch"},
                    {"levelId": "unsafe-control", "value": "blind-redispatch"},
                ],
            },
            "assignments": [
                {"unitRef": "run:1", "levelId": "safe"},
                {"unitRef": "run:2", "levelId": "unsafe-control"},
            ],
            "assignmentEvidenceRef": bound("study", "allocation-manifest", "allocation:response-loss-r1", "allocation"),
            "nonClaims": ["Assignment contract does not authorize either recovery policy to execute a real provider effect."],
        },
        "contractDigest",
    )

    fork = seal(
        {
            "schemaVersion": 1,
            "kind": "ordivon.experimental-fork-manifest",
            "forkId": "fork:response-loss-policy-r1",
            "experimentId": design["experimentId"],
            "parentEpisode": {"episodeId": "episode:response-loss-parent", "projectionDigest": "sha256:" + "2" * 64},
            "forkMode": "policy",
            "externalWorldMode": "closed",
            "frozenBindings": [
                {"name": "environment", "binding": design["environmentBinding"]},
                {"name": "observation-contract", "binding": observation},
                {"name": "action-contract", "binding": action},
            ],
            "changedBindings": [
                {
                    "name": "recovery-policy",
                    "before": bound("agent", "recovery-policy", "policy:safe", "safe"),
                    "after": bound("study", "recovery-policy", "policy:unsafe-control", "unsafe"),
                }
            ],
            "interventionRefs": [{"contractId": intervention["contractId"], "contractDigest": intervention["contractDigest"]}],
            "randomness": {"strategy": "same", "seedRef": "seed:response-loss-r1"},
            "nonClaims": ["Fork manifest declares comparison structure only; it performs no provider effect."],
        },
        "manifestDigest",
    )

    assessment = seal(
        {
            "schemaVersion": 1,
            "kind": "ordivon.experimental-fork-assessment",
            "forkId": fork["forkId"],
            "manifestDigest": fork["manifestDigest"],
            "standing": "PASS_DECLARED_DIFFERENCE",
            "observedFrozenBindings": fork["frozenBindings"],
            "observedChangedBindings": [
                {"name": "recovery-policy", "beforeDigest": fork["changedBindings"][0]["before"]["digest"], "afterDigest": fork["changedBindings"][0]["after"]["digest"]}
            ],
            "undeclaredDifferences": [],
            "nonClaims": ["Assessment does not establish live external-world counterfactual equivalence."],
        },
        "assessmentDigest",
    )

    evaluation = seal(
        {
            "schemaVersion": 1,
            "kind": "ordivon.experimental-evaluation-record",
            "evaluationId": "evaluation:response-loss-no-redispatch-r1",
            "experimentId": design["experimentId"],
            "metricSpec": {"metricId": metric["metricId"], "specDigest": metric["specDigest"]},
            "subjects": [{"episodeId": "episode:response-loss-parent", "projectionDigest": "sha256:" + "2" * 64}],
            "forkRefs": [{"forkId": fork["forkId"], "manifestDigest": fork["manifestDigest"], "assessmentDigest": assessment["assessmentDigest"]}],
            "value": False,
            "claimEvidenceLevel": "deterministic-derived",
            "evidenceInputs": [
                {
                    "evidenceLevel": "deterministic-observation",
                    "binding": bound("agent", "continuation-plan", "plan:response-loss-r1", "plan"),
                }
            ],
            "providerBinding": bound("study", "deterministic-verifier", "verifier:experimental-fabric-r1", "verifier"),
            "limitations": ["Development fixture validates protocol semantics; live owner behavior remains covered by owner tests."],
            "nonClaims": ["Evaluation does not establish provider effect status or domain completion."],
        },
        "recordDigest",
    )

    return {
        "metric": metric,
        "design": design,
        "intervention": intervention,
        "fork": fork,
        "assessment": assessment,
        "evaluation": evaluation,
    }


def test_all_profile_schemas_are_valid_draft_2020_12() -> None:
    for path in SCHEMAS.values():
        Draft202012Validator.check_schema(json.loads(path.read_text(encoding="utf-8")))


def test_response_loss_reference_protocol_validates() -> None:
    values = reference_objects()
    validate_metric(values["metric"])
    validate_design(values["design"])
    validate_intervention(values["intervention"])
    validate_fork(values["fork"])
    validate_assessment(values["assessment"])
    validate_evaluation(values["evaluation"], values["metric"])


def test_parity_group_rejects_semantic_contract_drift() -> None:
    value = reference_objects()["design"]
    value["seats"][1]["actionContract"] = bound("harness", "action-contract", "actions:other", "other")
    value = seal(value, "contractDigest")
    with pytest.raises(ValueError, match="parity group"):
        validate_design(value)


def test_continuation_fork_rejects_declared_policy_change() -> None:
    value = reference_objects()["fork"]
    value["forkMode"] = "continuation"
    value = seal(value, "manifestDigest")
    with pytest.raises(ValueError, match="continuation fork"):
        validate_fork(value)


def test_passing_fork_rejects_undeclared_difference() -> None:
    value = reference_objects()["assessment"]
    value["undeclaredDifferences"] = [{"name": "seed", "beforeDigest": "sha256:" + "3" * 64, "afterDigest": "sha256:" + "4" * 64}]
    value = seal(value, "assessmentDigest")
    with pytest.raises(ValueError, match="passing fork"):
        validate_assessment(value)


def test_crossover_requires_period_and_assignment_evidence() -> None:
    value = reference_objects()["intervention"]
    value["assignmentPolicy"] = "crossover"
    value.pop("assignmentEvidenceRef")
    value = seal(value, "contractDigest")
    with pytest.raises(ValueError, match="assignment evidence"):
        validate_intervention(value)

    value = reference_objects()["intervention"]
    value["assignmentPolicy"] = "crossover"
    value = seal(value, "contractDigest")
    with pytest.raises(ValueError, match="period"):
        validate_intervention(value)


def test_evaluation_rejects_evidence_weaker_than_metric_minimum() -> None:
    values = reference_objects()
    evaluation = values["evaluation"]
    evaluation["evidenceInputs"][0]["evidenceLevel"] = "semantic-inference"
    evaluation["claimEvidenceLevel"] = "semantic-inference"
    evaluation = seal(evaluation, "recordDigest")
    with pytest.raises(ValueError, match="weaker than metric minimum"):
        validate_evaluation(evaluation, values["metric"])


def test_response_loss_owner_dogfood_generates_evaluation_from_current_plan(tmp_path) -> None:
    from ordivon_harness.api import (
        NO_TOOL_AGENT_GRANT_DIGEST,
        NO_TOOL_AGENT_SURFACE_DIGEST,
        AgentTurnResult,
        HarnessAgentRun,
        HarnessBoundReference,
        HarnessPrivacyPolicy,
        HarnessRunContract,
    )
    from ordivon_harness.ordivon.model import AgentRunConclusion, ScriptedTurnAdapter

    from ordivon_agent import (
        AgentContinuationCoordinator,
        ResponseContinuityReceipt,
        ResponseContinuityStore,
        ResponseDeliveryState,
    )

    def raw_sha(label: str) -> str:
        return "sha256:" + hashlib.sha256(label.encode()).hexdigest()

    paused_turn = AgentTurnResult(
        model_call_id="model-call:experimental-fabric-response-loss",
        model_id=ScriptedTurnAdapter.model_id,
        content="Need caller input.",
        tool_calls=(),
        conclusion=AgentRunConclusion(
            status="needs_input",
            summary="Need caller input before continuing.",
            unresolved_unknowns=("caller reply",),
        ),
        usage={"inputTokens": 1, "outputTokens": 1},
        finish_reason="stop",
        raw_response_digest=raw_sha("paused-turn"),
    )
    contract = HarnessRunContract(
        harness_run_id="harness-run:experimental-fabric-response-loss-r1",
        harness_implementation_id="ordivon-harness@experimental-fabric-r1",
        caller_id="caller:experimental-fabric",
        caller_run_ref="conversation:experimental-fabric-response-loss-r1",
        objective_ref=HarnessBoundReference(
            "objective:experimental-fabric-response-loss-r1", "objective", raw_sha("objective")
        ),
        context_refs=(
            HarnessBoundReference(
                "context:experimental-fabric-response-loss-r1", "context", raw_sha("context")
            ),
        ),
        provider_id="provider:scripted",
        adapter_id=ScriptedTurnAdapter.adapter_id,
        requested_model_id=ScriptedTurnAdapter.model_id,
        tool_catalog_digest=NO_TOOL_AGENT_SURFACE_DIGEST,
        tool_grant_digest=NO_TOOL_AGENT_GRANT_DIGEST,
        budget={
            "maxModelCalls": 4,
            "maxToolCalls": 0,
            "maxObservationBytes": 65536,
            "maxWallTimeMs": 10000,
            "maxTotalTokens": 10000,
            "maxModelRetries": 1,
            "maxToolCorrections": 2,
            "maxConclusionCorrections": 3,
            "maxObservationOnlyTurns": 4,
            "maxNoProgressTurns": 3,
        },
        completion_contract={"mode": "record"},
        system_manifest_ref=HarnessBoundReference(
            "manifest:experimental-fabric-response-loss-r1",
            "system-manifest",
            raw_sha("manifest"),
        ),
        created_at_ms=1000,
        privacy=HarnessPrivacyPolicy(),
    )

    run = HarnessAgentRun.create(
        tmp_path / "harness",
        contract,
        lambda _contract: ScriptedTurnAdapter((paused_turn,)),
    )
    assert run.run(({"role": "user", "content": "start"},)).paused

    with ResponseContinuityStore(tmp_path / "responses") as responses:
        prepared = responses.create(
            ResponseContinuityReceipt(
                response_id="response:experimental-fabric-response-loss-r1",
                caller_id=contract.caller_id,
                caller_run_ref=contract.caller_run_ref,
                harness_run_id=contract.harness_run_id,
                source_run_revision=run.recovery_status()["runRevision"],
                output_digest=raw_sha("response-body"),
                evidence_refs=("evidence:experimental-fabric-response-loss-r1",),
                observed_attention_sequence=1,
                presented_attention_sequence=0,
                state=ResponseDeliveryState.PREPARED,
                revision=1,
                created_at_ms=2000,
                updated_at_ms=2000,
            )
        )
        responses.transition(
            prepared.response_id,
            expected_revision=prepared.revision,
            state=ResponseDeliveryState.DELIVERY_UNKNOWN,
            updated_at_ms=2001,
        )
        plan = AgentContinuationCoordinator(responses).inspect(run)

    assert plan.action.value == "represent-unconfirmed-response"
    assert plan.response_rehydration_required is True
    assert plan.effect_redispatch_allowed is False

    plan_projection = {
        "action": plan.action.value,
        "callerId": plan.caller_id,
        "callerRunRef": plan.caller_run_ref,
        "harnessRunId": plan.harness_run_id,
        "runRevision": plan.run_revision,
        "responseRehydrationRequired": plan.response_rehydration_required,
        "effectRedispatchAllowed": plan.effect_redispatch_allowed,
        "responseState": plan.latest_response.state.value if plan.latest_response else None,
    }
    observed_binding = {
        "ownerId": "agent",
        "objectKind": "continuation-plan",
        "objectId": f"continuation-plan:{plan.harness_run_id}:{plan.run_revision}",
        "digest": digest(plan_projection),
    }

    values = reference_objects()
    metric = values["metric"]
    metric["ownerInputs"] = [observed_binding]
    metric = seal(metric, "specDigest")
    validate_metric(metric)

    evaluation = values["evaluation"]
    evaluation["metricSpec"] = {
        "metricId": metric["metricId"],
        "specDigest": metric["specDigest"],
    }
    evaluation["value"] = plan.effect_redispatch_allowed
    evaluation["evidenceInputs"] = [
        {"evidenceLevel": "deterministic-observation", "binding": observed_binding}
    ]
    evaluation = seal(evaluation, "recordDigest")
    validate_evaluation(evaluation, metric)
    assert evaluation["value"] is False
