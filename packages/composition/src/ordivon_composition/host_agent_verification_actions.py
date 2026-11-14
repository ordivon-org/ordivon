"""Agent-facing Host Work action projection using Composition's existing impact selector.

The projection is deliberately not a proof, receipt, verifier executor, or
Host/Runtime/Git authority. A verified claim remains the natural Owner's fact.
This adapter only stops unrelated checks from being scheduled by default and
makes unqualified evidence an explicit *read/qualify* task rather than a rerun.
"""

from __future__ import annotations

from typing import Any

from .cognitive_circuit_r1 import CircuitContractError
from .verification_impact import select_impacted_obligations

_HOST_SNAPSHOT_FIELDS = frozenset(
    {
        "objective",
        "frontier",
        "established",
        "unresolved",
        "rejected",
        "constraints",
        "nextActions",
        "referenceRefs",
    }
)
_HOST_LIST_FIELDS = frozenset(
    {"established", "unresolved", "rejected", "constraints", "nextActions", "referenceRefs"}
)
_GENERATED_PREFIX = "verification-impact:"


def _require_host_work(work: Any) -> tuple[str, int, dict[str, Any], bool]:
    if not isinstance(work, dict) or work.get("kind") != "ordivon.host-work":
        raise CircuitContractError("agent action projection needs an actual Host Work response")
    work_ref = work.get("workRef")
    revision = work.get("revision")
    snapshot = work.get("snapshot")
    if (
        not isinstance(work_ref, str)
        or not work_ref.startswith("work:")
        or work_ref != work_ref.strip()
        or type(revision) is not int
        or revision < 1
        or not isinstance(snapshot, dict)
    ):
        raise CircuitContractError("Host Work identity/revision/snapshot contract invalid")
    required = {"objective", "frontier", *_HOST_LIST_FIELDS}
    if not required.issubset(snapshot):
        raise CircuitContractError("Host Work lacks current semantic checkpoint fields")
    if any(
        not isinstance(snapshot[key], list)
        or any(not isinstance(value, str) or not value for value in snapshot[key])
        for key in _HOST_LIST_FIELDS
    ):
        raise CircuitContractError("Host Work checkpoint lists are malformed")
    if not all(
        isinstance(snapshot[key], str) and snapshot[key] for key in ("objective", "frontier")
    ):
        raise CircuitContractError("Host Work objective/frontier malformed")
    # A Rust Engagement Work has additional guarded state. A legacy Python
    # Work snapshot.commit cannot safely replace it; project read-only instead.
    can_commit = work.get("state") == "open" and set(snapshot) == _HOST_SNAPSHOT_FIELDS
    return work_ref, revision, snapshot, can_commit


def project_host_agent_verification_actions(
    *,
    work: dict[str, Any],
    impact_graph: dict[str, Any],
    changed_refs: list[str],
    unknown_refs: list[str] | None = None,
    previous_graph: dict[str, Any] | None = None,
    proof_refs_by_obligation: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Select proof impact from the existing task-local graph, then plan actions."""
    selection_inputs = impact_graph
    if not isinstance(impact_graph, dict) or set(impact_graph) != {
        "authorityRefs",
        "obligations",
    }:
        raise CircuitContractError("impact_graph needs exact existing Composition graph fields")

    selection = select_impacted_obligations(
        authority_refs=selection_inputs["authorityRefs"],
        obligations=selection_inputs["obligations"],
        changed_refs=changed_refs,
        unknown_refs=unknown_refs,
        previous_graph=previous_graph,
    )
    return _project_selected_host_actions(
        work=work, selection=selection, proof_refs_by_obligation=proof_refs_by_obligation
    )


def _project_selected_host_actions(
    *,
    work: dict[str, Any],
    selection: dict[str, Any],
    proof_refs_by_obligation: dict[str, str] | None,
) -> dict[str, Any]:
    """Render Agent Work actions from an existing Composition impact selection."""
    work_ref, revision, snapshot, can_commit = _require_host_work(work)
    prior_refs = proof_refs_by_obligation if proof_refs_by_obligation is not None else {}
    ids = {row["id"] for row in selection["standingByObligation"]}
    if not isinstance(prior_refs, dict) or any(
        not isinstance(k, str)
        or k not in ids
        or not isinstance(v, str)
        or not v
        or v not in snapshot["referenceRefs"]
        for k, v in prior_refs.items()
    ):
        raise CircuitContractError(
            "proof reference must identify an existing current Host referenceRef and obligation"
        )

    records: list[dict[str, Any]] = []
    next_steps: list[str] = []
    counts = {"RECHECK_REQUIRED": 0, "UNKNOWN": 0, "REUSE_CANDIDATE": 0}
    for row in selection["standingByObligation"]:
        identity, standing = row["id"], row["standing"]
        counts[standing] += 1
        if standing == "RECHECK_REQUIRED":
            if identity in prior_refs:
                # "Affected" is a dependency finding, not a claim that nobody
                # has already reverified the *new* source. The current Work
                # reference may be an old or a new receipt; ask the natural
                # Owner to establish its exact subject/readset before retry.
                decision = "QUALIFY_EXISTING_IMPACTED_PROOF_FIRST"
                next_steps.append(
                    f"{_GENERATED_PREFIX}{identity}: consult existing Owner proof "
                    f"{prior_refs[identity]} for changed scope/currentness first; "
                    "only then recheck this named obligation if not qualified"
                )
            else:
                decision = "RECHECK_NAMED_CONSUMER"
                # Without a Work reference this is a scoped recheck *candidate*,
                # not a verifier dispatch or proof that no Owner result exists.
                next_steps.append(
                    f"{_GENERATED_PREFIX}{identity}: locate current Owner proof if any; "
                    "otherwise recheck impacted owner/consumer obligation only"
                )
        elif standing == "UNKNOWN":
            decision = "QUALIFY_DEPENDENCIES_NOT_RERUN"
            next_steps.append(
                f"{_GENERATED_PREFIX}{identity}: identify unresolved owner dependency or source scope; do not rerun by default"
            )
        elif identity in prior_refs:
            decision = "READ_EXISTING_OWNER_PROOF"
        else:
            decision = "LOCATE_PRIOR_OWNER_PROOF"
        records.append(
            {
                "obligationId": identity,
                "impactStanding": standing,
                "agentDecision": decision,
                "existingProofRef": prior_refs.get(identity),
                # A Host referenceRef is an address, never an authenticated
                # or current Owner evidence result.
                "proofVerifiedByProjection": False,
                "automaticVerifierExecution": False,
            }
        )

    # Make a *single*, bounded reentry hint visible in Host Work.current.
    # This records only evidence lookup, not a new verification task or PASS.
    if counts["REUSE_CANDIDATE"]:
        next_steps.append(
            f"{_GENERATED_PREFIX}prior-evidence: {counts['REUSE_CANDIDATE']} "
            "unchanged-scope candidates; consult original Owner proof references, "
            "do not rerun verifiers by default "
            f"(impactBasis={selection['basisDigest']})"
        )

    if any(len(step) > 4096 for step in next_steps):
        raise CircuitContractError("generated Host nextAction exceeds safe size")
    proposed_snapshot: dict[str, Any] | None = None
    if can_commit:
        # Replace ONLY our previous generated nextActions, not the Agent's
        # business plan, existing evidence or unrelated constraints. This is
        # stable under repeated projection of identical inputs.
        retained = [
            step for step in snapshot["nextActions"] if not step.startswith(_GENERATED_PREFIX)
        ]
        steps = retained + [step for step in next_steps if step not in retained]
        if len(steps) <= 128:
            proposed_snapshot = {key: snapshot[key] for key in _HOST_SNAPSHOT_FIELDS}
            proposed_snapshot["nextActions"] = steps

    return {
        "schemaVersion": 1,
        "kind": "ordivon.agent-host-verification-action-projection",
        "truthRole": "task-local-rebuildable-agent-scheduling-not-owner-proof",
        "workRef": work_ref,
        "expectedRevision": revision,
        "impactBasisDigest": selection["basisDigest"],
        "impactProjectionDigest": selection["projectionDigest"],
        "actions": records,
        "summary": {
            "scopedRecheckCandidates": counts["RECHECK_REQUIRED"],
            "qualifyWithoutRerun": counts["UNKNOWN"],
            "reusedOrLocatedExistingEvidence": counts["REUSE_CANDIDATE"],
            "wholeSuiteRecheckRequested": False,
        },
        "proposedWorkSnapshot": proposed_snapshot,
        "proposedHostCommitEligible": proposed_snapshot is not None,
        "nonClaims": [
            "Agent actions are non-executing proposals; Runtime jobs are never started.",
            "REUSE_CANDIDATE is not VERIFIED or owner-authorized NO_RECHECK.",
            "Caller supplied readsets, changed refs and prior Work referenceRefs require independent owner qualification.",
            "UNKNOWN means qualify the missing premise; no automatic full verifier replay.",
            "Work CAS expectedRevision must be supplied to the existing Host commit tool by a real authenticated Agent.",
            "No external, installed, Artifact, Security or domain completion authority is granted.",
        ],
    }


def project_host_agent_source_readset_actions(
    *,
    work: dict[str, Any],
    git_source_delta: dict[str, Any],
    source_readset_evidence: dict[str, Any],
    proof_refs_by_obligation: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Direct natural Git/readset -> C04 selection -> Agent Work action bridge.

    Git delta provenance MUST be requalified with the existing native Git
    producer before an external request is used (the CLI performs that).
    Caller-supplied Owner readset completeness and original proof receipt
    remain independently UNQUALIFIED.
    """
    from .verification_impact import select_source_readset_impacts

    source_impact = select_source_readset_impacts(
        git_source_delta=git_source_delta,
        source_readset_evidence=source_readset_evidence,
    )
    result = _project_selected_host_actions(
        work=work,
        selection=source_impact["selection"],
        proof_refs_by_obligation=proof_refs_by_obligation,
    )
    result["sourceReadsetScope"] = {
        "sourceCut": source_impact["sourceCut"],
        "queryPrefix": source_impact["queryPrefix"],
        "sourceScopeRef": source_impact["sourceScopeRef"],
        "readsetDependencyQualification": source_impact["readsetDependencyQualification"],
        "membershipClosureQualification": source_impact["membershipClosureQualification"],
        "sourceReadsetProjectionDigest": source_impact["projectionDigest"],
        "nativeGitRequalifiedByPureFunction": False,
        "ownerCertifiedReadsetClosure": False,
    }
    result["nonClaims"].append(
        "Native Git source requalification belongs to the CLI/owner, not a caller-authored JSON envelope."
    )
    return result
