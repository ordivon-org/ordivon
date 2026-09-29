from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest
from ordivon_composition.agent_run_binding_r1 import compile_agent_run_binding

from ordivon_capital.governance.institutional_topology import (
    InstitutionalTopologyError,
    assert_w3_schema_identities,
    canonical_digest,
    evaluate_review_topology,
    project_agent_birth_role_binding,
    validate_office_assignment_document,
    validate_office_registry,
    validate_office_verdict_document,
)

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "schema"
REGISTRY = json.loads((ROOT / "config/capital_office_registry.json").read_text())
DUMMY = "sha256:" + "a" * 64
DECISION = "sha256:" + "d" * 64


def _grant(role: str, *, level: str = "L2_RECOMMEND", grantee_type: str = "OFFICE_ROLE", grantee_id: str | None = None):
    return {
        "schemaVersion": 1,
        "kind": "ordivon.capital.delegation-grant",
        "grantId": f"grant:{role.lower()}",
        "grantingAuthorityClass": "OWNER_PRINCIPAL",
        "principalAuthorityId": "principal:owner",
        "grantee": {"granteeType": grantee_type, "granteeId": grantee_id or role},
        "level": level,
        "scopes": ["capital:review"],
        "effectClasses": [],
        "constitutionDigest": "sha256:" + "c" * 64,
        "validFrom": "2026-09-29T00:00:00+00:00",
        "revocable": True,
        "evidenceDigest": DUMMY,
    }


def _assignment(role: str, *, actor: str, agent: str, level: str = "L2_RECOMMEND"):
    grant = _grant(role, level=level)
    assignment = {
        "schemaVersion": 1,
        "kind": "ordivon.capital.office-assignment",
        "assignmentId": f"assignment:{role.lower()}:{agent}",
        "roleId": role,
        "actorRef": actor,
        "agentId": agent,
        "delegationGrantDigest": canonical_digest(grant),
        "validFrom": "2026-09-29T00:00:00+00:00",
        "revocable": True,
        "evidenceDigest": DUMMY,
    }
    return assignment, grant


def _verdict(assignment: dict, verdict: str = "APPROVE", *, phase: str = "INDEPENDENT_INITIAL", veto: tuple[str, ...] = ()):
    return {
        "schemaVersion": 1,
        "kind": "ordivon.capital.office-verdict",
        "verdictId": f"verdict:{assignment['agentId']}:{phase.lower()}",
        "decisionRef": "capital-decision:test",
        "decisionDigest": DECISION,
        "assignmentDigest": canonical_digest(assignment),
        "roleId": assignment["roleId"],
        "actorRef": assignment["actorRef"],
        "agentId": assignment["agentId"],
        "phase": phase,
        "verdict": verdict,
        "assertedVetoClasses": list(veto),
        "rationale": "bounded independent review",
        "evidenceRefs": ["evidence:test"],
        "unresolvedUnknowns": [],
        "frozenAt": "2026-09-29T01:00:00+00:00",
        "frozen": True,
    }


def _binding(duty: str, assignment: dict):
    return {
        "duty": duty,
        "assignmentDigest": canonical_digest(assignment),
        "roleId": assignment["roleId"],
        "actorRef": assignment["actorRef"],
        "agentId": assignment["agentId"],
    }


def _topology(bindings: list[dict], verdicts: list[dict], *, external: bool = False):
    return {
        "schemaVersion": 1,
        "kind": "ordivon.capital.review-topology",
        "reviewId": "review:test",
        "decisionRef": "capital-decision:test",
        "decisionDigest": DECISION,
        "materiality": "SENSITIVE",
        "externalEffectPlanned": external,
        "dutyBindings": bindings,
        "verdictRefs": [
            {"verdictId": value["verdictId"], "digest": canonical_digest(value)}
            for value in verdicts
        ],
    }


def _evaluate(bindings, pairs, verdicts, *, external=False):
    return evaluate_review_topology(
        _topology(bindings, verdicts, external=external),
        registry=REGISTRY,
        assignments=[item[0] for item in pairs],
        delegations={item[0]["assignmentId"]: item[1] for item in pairs},
        verdicts=verdicts,
    )


def test_w3_schema_identities_are_digest_bound():
    assert_w3_schema_identities(SCHEMA)


def test_office_registry_has_three_lines_and_thirteen_roles():
    value = validate_office_registry(REGISTRY)
    assert len(value["roles"]) == 13
    lines = {row["line"] for row in value["roles"]}
    assert lines == {"GOVERNING_BODY", "FIRST_LINE", "SECOND_LINE", "THIRD_LINE"}
    assurance = next(row for row in value["roles"] if row["roleId"] == "INDEPENDENT_ASSURANCE")
    assert assurance["line"] == "THIRD_LINE"
    assert assurance["independenceRequired"] is True


def test_office_assignment_consumes_explicit_delegation_but_actor_ref_is_not_authority():
    assignment, grant = _assignment("RISK_OFFICE", actor="actor:agent:risk", agent="risk-a")
    assert validate_office_assignment_document(assignment, registry=REGISTRY, delegation=grant) == assignment
    projection = project_agent_birth_role_binding(assignment, registry=REGISTRY, delegation=grant)
    assert projection["agentId"] == "risk-a"
    assert projection["actorRef"] == "actor:agent:risk"
    assert projection["hostAuthorizationGranted"] is False
    assert projection["providerAuthorityGranted"] is False
    assert projection["credentialAuthorityGranted"] is False
    assert projection["externalEffectAuthorityGranted"] is False
    assert "OFFICE_ROLE=RISK_OFFICE" in projection["roleCard"]
    assert "AUTHORITY_BOUNDARY=" in projection["roleCard"]


def test_agent_identity_delegation_must_target_exact_agent():
    grant = _grant("RISK_OFFICE", grantee_type="AGENT_IDENTITY", grantee_id="risk-a")
    assignment = _assignment("RISK_OFFICE", actor="actor:agent:risk", agent="risk-a")[0]
    assignment["delegationGrantDigest"] = canonical_digest(grant)
    validate_office_assignment_document(assignment, registry=REGISTRY, delegation=grant)
    bad = copy.deepcopy(assignment)
    bad["agentId"] = "risk-b"
    with pytest.raises(InstitutionalTopologyError, match="agent delegation"):
        validate_office_assignment_document(bad, registry=REGISTRY, delegation=grant)


def test_capability_profile_alone_cannot_staff_office():
    grant = _grant("RISK_OFFICE", grantee_type="CAPABILITY_PROFILE", grantee_id="profile:risk")
    assignment = _assignment("RISK_OFFICE", actor="actor:agent:risk", agent="risk-a")[0]
    assignment["delegationGrantDigest"] = canonical_digest(grant)
    with pytest.raises(InstitutionalTopologyError, match="cannot by itself staff"):
        validate_office_assignment_document(assignment, registry=REGISTRY, delegation=grant)


def test_role_binding_can_enter_generic_composition_without_authority_transfer():
    assignment, grant = _assignment("RESEARCH_OFFICE", actor="actor:agent:research", agent="research-a")
    projection = project_agent_birth_role_binding(assignment, registry=REGISTRY, delegation=grant)
    binding = compile_agent_run_binding(
        source_circuit_ref={"id": "capital:w3:test", "digest": DUMMY},
        run_contract_ref={"id": "harness-run-contract:test", "digest": "sha256:" + "b" * 64},
        adapter_binding_ref={"id": "adapter:test", "digest": "sha256:" + "e" * 64},
        cognition_binding_refs=(
            {"id": f"capital-office-assignment:{assignment['assignmentId']}", "digest": projection["officeAssignmentDigest"]},
        ),
    )
    assert binding["readyForHarness"] is True
    assert binding["authorityGranted"] is False
    assert binding["executionDispatched"] is False
    assert binding["domainAcceptanceEstablished"] is False


def test_post_discussion_checker_verdict_does_not_replace_frozen_initial_judgment():
    maker = _assignment("CHIEF_CAPITAL_OFFICE", actor="actor:agent:cio", agent="cio-a")
    checker = _assignment("RISK_OFFICE", actor="actor:agent:risk", agent="risk-a")
    post = _verdict(checker[0], phase="POST_DISCUSSION")
    result = _evaluate([_binding("MAKER", maker[0]), _binding("CHECKER", checker[0])], [maker, checker], [post])
    assert result["standing"] == "REVIEW_OPEN"
    assert result["checkerInitialVerdict"] is None


def test_independent_checker_approval_only_reaches_downstream_policy_not_effect_authority():
    maker = _assignment("CHIEF_CAPITAL_OFFICE", actor="actor:agent:cio", agent="cio-a")
    checker = _assignment("RISK_OFFICE", actor="actor:agent:risk", agent="risk-a")
    initial = _verdict(checker[0])
    result = _evaluate([_binding("MAKER", maker[0]), _binding("CHECKER", checker[0])], [maker, checker], [initial])
    assert result["standing"] == "READY_FOR_DOWNSTREAM_POLICY"
    assert result["policyGateRequired"] is True
    assert result["authorityGranted"] is False
    assert result["providerAuthorityGranted"] is False
    assert result["credentialAuthorityGranted"] is False
    assert result["externalEffectAuthorityGranted"] is False


def test_risk_veto_blocks_regardless_of_other_approval():
    maker = _assignment("CHIEF_CAPITAL_OFFICE", actor="actor:agent:cio", agent="cio-a")
    checker = _assignment("RISK_OFFICE", actor="actor:agent:risk", agent="risk-a")
    risk_reject = _verdict(checker[0], verdict="REJECT", veto=("RISK_BUDGET",))
    maker_approve = _verdict(maker[0], verdict="APPROVE")
    result = _evaluate([_binding("MAKER", maker[0]), _binding("CHECKER", checker[0])], [maker, checker], [maker_approve, risk_reject])
    assert result["standing"] == "BLOCKED_BY_VETO"
    assert result["vetoClasses"] == ["RISK_BUDGET"]
    assert result["majorityVoteMayOverrideVeto"] is False


def test_role_cannot_assert_veto_class_it_does_not_own():
    maker = _assignment("CHIEF_CAPITAL_OFFICE", actor="actor:agent:cio", agent="cio-a")
    bad = _verdict(maker[0], verdict="REJECT", veto=("RISK_BUDGET",))
    with pytest.raises(InstitutionalTopologyError, match="veto class"):
        validate_office_verdict_document(bad, registry=REGISTRY, assignment=maker[0])


def test_maker_and_checker_must_be_independently_staffed():
    maker = _assignment("CHIEF_CAPITAL_OFFICE", actor="actor:agent:same", agent="same-a")
    checker = _assignment("RISK_OFFICE", actor="actor:agent:same", agent="same-a")
    initial = _verdict(checker[0])
    result = _evaluate([_binding("MAKER", maker[0]), _binding("CHECKER", checker[0])], [maker, checker], [initial])
    assert result["standing"] == "BLOCKED_ROLE_CONFLICT"
    assert any("MAKER/CHECKER" in item for item in result["identityConflicts"])


def test_external_effect_review_requires_effect_owner_and_independent_reconciler():
    maker = _assignment("CHIEF_CAPITAL_OFFICE", actor="actor:agent:cio", agent="cio-a")
    checker = _assignment("RISK_OFFICE", actor="actor:agent:risk", agent="risk-a")
    initial = _verdict(checker[0])
    result = _evaluate([_binding("MAKER", maker[0]), _binding("CHECKER", checker[0])], [maker, checker], [initial], external=True)
    assert result["standing"] == "REVIEW_OPEN"
    assert result["missingDuties"] == ["EFFECT_OWNER", "RECONCILER"]


def test_external_effect_review_can_be_structurally_ready_without_granting_effect_authority():
    maker = _assignment("CHIEF_CAPITAL_OFFICE", actor="actor:agent:cio", agent="cio-a")
    checker = _assignment("RISK_OFFICE", actor="actor:agent:risk", agent="risk-a")
    effect = _assignment("EFFECT_OFFICE", actor="actor:agent:effect", agent="effect-a", level="L4_EXECUTE_BOUNDED")
    recon = _assignment("CONTROLLER", actor="actor:agent:controller", agent="controller-a")
    initial = _verdict(checker[0])
    result = _evaluate(
        [_binding("MAKER", maker[0]), _binding("CHECKER", checker[0]), _binding("EFFECT_OWNER", effect[0]), _binding("RECONCILER", recon[0])],
        [maker, checker, effect, recon],
        [initial],
        external=True,
    )
    assert result["standing"] == "READY_FOR_DOWNSTREAM_POLICY"
    assert result["externalEffectAuthorityGranted"] is False


def test_effect_owner_cannot_self_reconcile():
    maker = _assignment("CHIEF_CAPITAL_OFFICE", actor="actor:agent:cio", agent="cio-a")
    checker = _assignment("RISK_OFFICE", actor="actor:agent:risk", agent="risk-a")
    effect = _assignment("EFFECT_OFFICE", actor="actor:agent:effect", agent="effect-a", level="L4_EXECUTE_BOUNDED")
    # Even if the topology lies about the role, the exact binding must agree with the assignment.
    bindings = [_binding("MAKER", maker[0]), _binding("CHECKER", checker[0]), _binding("EFFECT_OWNER", effect[0]), _binding("RECONCILER", effect[0])]
    initial = _verdict(checker[0])
    result = _evaluate(bindings, [maker, checker, effect], [initial], external=True)
    assert result["standing"] == "BLOCKED_ROLE_CONFLICT"
    assert "RECONCILER must bind CONTROLLER" in result["roleErrors"]
    assert any("EFFECT_OWNER/RECONCILER" in item for item in result["identityConflicts"])


def test_third_line_is_not_operating_approval_and_must_be_independently_staffed():
    maker = _assignment("CHIEF_CAPITAL_OFFICE", actor="actor:agent:cio", agent="cio-a")
    checker = _assignment("RISK_OFFICE", actor="actor:agent:risk", agent="risk-a")
    assurance = _assignment("INDEPENDENT_ASSURANCE", actor="actor:agent:audit", agent="audit-a")
    initial = _verdict(checker[0])
    result = _evaluate([_binding("MAKER", maker[0]), _binding("CHECKER", checker[0]), _binding("ASSURANCE", assurance[0])], [maker, checker, assurance], [initial])
    assert result["standing"] == "READY_FOR_DOWNSTREAM_POLICY"
    assert result["assuranceIsOperatingApproval"] is False
