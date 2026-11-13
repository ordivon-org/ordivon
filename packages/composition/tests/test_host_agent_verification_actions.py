"""Only the new Agent action projection contract is under test.

Composition's proof graph fixed-point and Git source qualification have existing
tests. Never rerun PG18/Rust/Gateway to verify a pure read-only Agent adapter.
"""

from __future__ import annotations

import json
import subprocess
import sys

import pytest

from ordivon_composition.cognitive_circuit_r1 import CircuitContractError
from ordivon_composition.host_agent_verification_actions import (
    project_host_agent_verification_actions,
)


def work_fixture() -> dict:
    return {
        "schemaVersion": 1,
        "kind": "ordivon.host-work",
        "workRef": "work:test:agent-knowledge",
        "state": "open",
        "revision": 17,
        "snapshotDigest": "sha256:" + "a" * 64,
        "snapshot": {
            "objective": "Continue existing Host Work without duplicated verification",
            "frontier": "Owner proofs exist; decide impact before verification",
            "established": ["A previous SourceCut passed native Host contract verification"],
            "unresolved": ["Production Principal grants are still unqualified"],
            "rejected": [],
            "constraints": ["No unscoped external execution"],
            "nextActions": [
                "Implement Agent consumer interface",
                "verification-impact:proof:old: stale generated task",
            ],
            "referenceRefs": ["evidence:topic:prior-pass:1"],
        },
    }


def graph_fixture() -> dict:
    return {
        "authorityRefs": ["source:cas", "source:topic", "authority:production-grant"],
        "obligations": [
            {
                "id": "proof:cas",
                "dependsOn": ["source:cas"],
                "dependenciesComplete": True,
            },
            {
                "id": "proof:topic",
                "dependsOn": ["source:topic"],
                "dependenciesComplete": True,
            },
            {
                "id": "proof:grant",
                "dependsOn": ["authority:production-grant"],
                "dependenciesComplete": False,
            },
            {
                "id": "proof:cas-consumer",
                "dependsOn": ["proof:cas", "source:topic"],
                "dependenciesComplete": True,
            },
        ],
    }


def project(*, work=None, graph=None, changed=None, unknown=None, proof_refs=None):
    return project_host_agent_verification_actions(
        work=work if work is not None else work_fixture(),
        impact_graph=graph if graph is not None else graph_fixture(),
        changed_refs=changed if changed is not None else ["source:cas"],
        unknown_refs=unknown,
        proof_refs_by_obligation=proof_refs
        if proof_refs is not None
        else {"proof:topic": "evidence:topic:prior-pass:1"},
    )


def test_exact_impact_produces_only_scoped_recheck_and_read_existing_evidence():
    result = project()
    rows = {row["obligationId"]: row for row in result["actions"]}
    assert rows["proof:cas"]["agentDecision"] == "RECHECK_NAMED_CONSUMER"
    assert rows["proof:cas-consumer"]["agentDecision"] == "RECHECK_NAMED_CONSUMER"
    assert rows["proof:topic"]["agentDecision"] == "READ_EXISTING_OWNER_PROOF"
    assert rows["proof:topic"]["existingProofRef"] == "evidence:topic:prior-pass:1"
    assert rows["proof:grant"]["agentDecision"] == "QUALIFY_DEPENDENCIES_NOT_RERUN"
    assert all(not row["proofVerifiedByProjection"] for row in rows.values())
    assert all(not row["automaticVerifierExecution"] for row in rows.values())
    assert result["summary"] == {
        "scopedRecheckCandidates": 2,
        "qualifyWithoutRerun": 1,
        "reusedOrLocatedExistingEvidence": 1,
        "wholeSuiteRecheckRequested": False,
    }
    snapshot = result["proposedWorkSnapshot"]
    assert snapshot is not None and result["proposedHostCommitEligible"]
    assert result["expectedRevision"] == 17
    assert snapshot["established"] == work_fixture()["snapshot"]["established"]
    assert snapshot["unresolved"] == work_fixture()["snapshot"]["unresolved"]
    assert snapshot["referenceRefs"] == work_fixture()["snapshot"]["referenceRefs"]
    assert snapshot["nextActions"][0] == "Implement Agent consumer interface"
    assert not any("proof:old" in s for s in snapshot["nextActions"])
    assert not any("proof:topic" in s for s in snapshot["nextActions"])
    assert len(snapshot["nextActions"]) == 5
    assert any("prior-evidence" in action for action in snapshot["nextActions"])


def test_unrelated_change_does_not_schedule_cas_or_topic_replay():
    result = project(changed=[])
    assert result["summary"]["scopedRecheckCandidates"] == 0
    assert result["summary"]["qualifyWithoutRerun"] == 1
    assert result["summary"]["reusedOrLocatedExistingEvidence"] == 3
    steps = result["proposedWorkSnapshot"]["nextActions"]
    assert steps[:2] == [
        "Implement Agent consumer interface",
        "verification-impact:proof:grant: identify unresolved owner dependency or source scope; do not rerun by default",
    ]
    assert len(steps) == 3 and "prior-evidence" in steps[-1]


def test_missing_owner_proof_ref_means_find_it_not_run_verifier():
    result = project(changed=[], proof_refs={})
    rows = {row["obligationId"]: row for row in result["actions"]}
    assert rows["proof:topic"]["agentDecision"] == "LOCATE_PRIOR_OWNER_PROOF"
    assert result["summary"]["scopedRecheckCandidates"] == 0


def test_unindexed_change_is_unknown_not_full_suite_execution():
    result = project(changed=["source:unindexed"])
    assert result["summary"]["scopedRecheckCandidates"] == 0
    assert result["summary"]["qualifyWithoutRerun"] == 4
    assert result["summary"]["wholeSuiteRecheckRequested"] is False


def test_agent_projection_is_idempotent_across_repeat_reads():
    first = project()
    work = work_fixture()
    work["revision"] += 1
    work["snapshot"] = first["proposedWorkSnapshot"]
    second = project(work=work)
    assert second["proposedWorkSnapshot"] == first["proposedWorkSnapshot"]
    assert second["expectedRevision"] == 18


def test_terminal_or_rust_engagement_work_does_not_propose_unsafe_legacy_commit():
    completed = work_fixture()
    completed["state"] = "completed"
    assert project(work=completed)["proposedHostCommitEligible"] is False
    rust = work_fixture()
    rust["snapshot"]["engagement"] = {"phase": "submitted"}
    assert project(work=rust)["proposedHostCommitEligible"] is False


def test_untrusted_prior_proof_ref_cannot_be_added_to_existing_host_work():
    with pytest.raises(CircuitContractError, match="existing current Host referenceRef"):
        project(proof_refs={"proof:topic": "evidence:unseen:other-work"})
    with pytest.raises(CircuitContractError, match="existing current Host referenceRef"):
        project(proof_refs={"proof:nonexistent": "evidence:topic:prior-pass:1"})


def test_malformed_host_work_and_impact_graph_fail_closed():
    wrong = work_fixture()
    wrong["revision"] = True
    with pytest.raises(CircuitContractError):
        project(work=wrong)
    with pytest.raises(CircuitContractError):
        project(graph={"obligations": []})
    with pytest.raises(CircuitContractError):
        project(changed=["not-a-typed-ref"])


def test_real_existing_composition_cli_is_agent_consumable(tmp_path):
    work = tmp_path / "work.json"
    graph = tmp_path / "graph.json"
    changed = tmp_path / "changed.json"
    proofs = tmp_path / "proofs.json"
    for path, value in (
        (work, work_fixture()),
        (graph, graph_fixture()),
        (changed, ["source:cas"]),
        (proofs, {"proof:topic": "evidence:topic:prior-pass:1"}),
    ):
        path.write_text(json.dumps(value), encoding="utf-8")
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "ordivon_composition.verification_obligation_r1",
            "agent-host-actions",
            str(work),
            str(graph),
            str(changed),
            "--proof-refs",
            str(proofs),
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    projection = json.loads(result.stdout)
    assert projection["workRef"] == "work:test:agent-knowledge"
    assert projection["summary"]["scopedRecheckCandidates"] == 2
    assert projection["kind"] == "ordivon.agent-host-verification-action-projection"
