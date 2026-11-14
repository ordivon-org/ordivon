"""Task-local GitHub Owner justification qualification for Agent's current Host Work.

Limited scope: GitHub Actions workflow completion at an EXACT immutable Git SHA.
No implication that the program, release, installation or scientific claim is
correct. Owner truth comes from a fresh native gh run view read, not caller JSON.
A supported AND/OR justification says ONLY that the requested native workflow
check(s) completed successfully for the matched source identity.
"""

from __future__ import annotations

import json
import re
import subprocess
from collections.abc import Callable
from pathlib import Path
from typing import Any

from .cognitive_circuit_r1 import CircuitContractError, canonical_digest
from .host_agent_verification_actions import _HOST_SNAPSHOT_FIELDS, _require_host_work

_GENERATED_PREFIX = "verification-justification:"
_GITHUB_REPO = re.compile(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+\Z")
_SHA = re.compile(r"(?:[0-9a-f]{40}|[0-9a-f]{64})\Z")
_RUN_REF = re.compile(r"github:run:([1-9][0-9]{0,18})\Z")


def _text(value: Any, *, label: str, limit: int = 300) -> str:
    if not isinstance(value, str) or not value or len(value) > limit or value.strip() != value:
        raise CircuitContractError(f"{label} must be a bounded canonical nonempty string")
    if any(ord(c) < 32 or ord(c) == 127 for c in value):
        raise CircuitContractError(f"{label} must not contain control characters")
    return value


def _contract(
    *,
    work: dict[str, Any],
    contract: dict[str, Any],
    local_source_cut: str,
) -> tuple[str, int, dict[str, Any], bool, str, list[dict[str, Any]], dict[str, str]]:
    work_ref, rev, snapshot, can_commit = _require_host_work(work)
    if (
        not isinstance(contract, dict)
        or set(contract) != {"kind", "repo", "targetSourceCut", "claims"}
        or contract["kind"] != "ordivon.github-workflow-justification-contract"
    ):
        raise CircuitContractError("exact GitHub workflow justification contract required")
    repo = _text(contract["repo"], label="GitHub repository", limit=180)
    if _GITHUB_REPO.fullmatch(repo) is None:
        raise CircuitContractError("GitHub repository must be owner/repo")
    sha = _text(contract["targetSourceCut"], label="target SourceCut", limit=64)
    if _SHA.fullmatch(sha) is None or sha != local_source_cut:
        raise CircuitContractError("target SourceCut must match current native Git commit")
    claims = contract["claims"]
    if not isinstance(claims, list) or not 1 <= len(claims) <= 24:
        raise CircuitContractError("bounded nonempty claims required")

    required: dict[str, str] = {}
    claim_ids: set[str] = set()
    for claim in claims:
        if not isinstance(claim, dict) or set(claim) != {"id", "consumerRef", "anyOf"}:
            raise CircuitContractError("exact Claim/consumer/justification shape required")
        cid = _text(claim["id"], label="claim ID")
        if cid in claim_ids:
            raise CircuitContractError("duplicate claim ID")
        claim_ids.add(cid)
        if claim["consumerRef"] != work_ref:
            raise CircuitContractError("Claim consumer must be the exact current Host Work")
        paths = claim["anyOf"]
        if not isinstance(paths, list) or not 1 <= len(paths) <= 16:
            raise CircuitContractError("bounded nonempty OR paths required")
        justification_ids: set[str] = set()
        for path in paths:
            if not isinstance(path, dict) or set(path) != {"id", "allOf"}:
                raise CircuitContractError("exact Justification AND shape required")
            path_id = _text(path["id"], label="justification ID")
            if path_id in justification_ids:
                raise CircuitContractError("duplicate justification within claim")
            justification_ids.add(path_id)
            edges = path["allOf"]
            if not isinstance(edges, list) or not 1 <= len(edges) <= 8:
                raise CircuitContractError("bounded nonempty evidence AND list required")
            refs_in_path: set[str] = set()
            for edge in edges:
                if not isinstance(edge, dict) or set(edge) != {"evidenceRef", "workflowName"}:
                    raise CircuitContractError("evidence requires exact Owner ref and workflow")
                ref = _text(edge["evidenceRef"], label="Owner evidence reference")
                workflow = _text(edge["workflowName"], label="GitHub workflow name")
                if _RUN_REF.fullmatch(ref) is None or ref not in snapshot["referenceRefs"]:
                    raise CircuitContractError(
                        "GitHub run evidence must already be referenced in current Host Work"
                    )
                if ref in refs_in_path:
                    raise CircuitContractError("duplicate evidence in same AND clause")
                refs_in_path.add(ref)
                if ref in required and required[ref] != workflow:
                    raise CircuitContractError("conflicting workflow assertions for same Owner run")
                required[ref] = workflow
    if len(required) > 32:
        raise CircuitContractError("too many distinct Owner proof reads")
    return work_ref, rev, snapshot, can_commit, repo, claims, required


def _native_git_head(repo_dir: Path) -> str:
    try:
        r = subprocess.run(
            ["git", "--no-replace-objects", "-C", str(repo_dir), "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            timeout=12,
            check=True,
        )
    except (OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
        raise CircuitContractError("native Git HEAD unavailable") from exc
    head = r.stdout.strip()
    if _SHA.fullmatch(head) is None:
        raise CircuitContractError("native Git HEAD not an immutable commit object ID")
    return head


def _github_run(
    *,
    repo: str,
    run_ref: str,
    runner: Callable[..., Any] = subprocess.run,
) -> dict[str, Any]:
    run_id = _RUN_REF.fullmatch(run_ref)
    if run_id is None:
        raise CircuitContractError("invalid GitHub run reference")
    # Read-only official GitHub CLI interface; never run actions, rerun jobs or
    # accept a caller-supplied response as Owner's attestation.
    cmd = [
        "gh",
        "run",
        "view",
        run_id.group(1),
        "--repo",
        repo,
        "--json",
        "databaseId,headSha,status,conclusion,workflowName,url",
    ]
    try:
        response = runner(cmd, capture_output=True, text=True, timeout=20, check=False)
        if response.returncode != 0 or len(response.stdout) > 131072:
            raise ValueError("GitHub owner response unavailable")
        obj = json.loads(response.stdout)
        if not isinstance(obj, dict) or obj.get("databaseId") != int(run_id.group(1)):
            raise ValueError("GitHub run identity mismatch")
        url = obj.get("url")
        if url != f"https://github.com/{repo}/actions/runs/{run_id.group(1)}":
            raise ValueError("GitHub run repository or URL mismatch")
        return {
            "evidenceRef": run_ref,
            "runId": int(run_id.group(1)),
            "url": url,
            "headSha": obj.get("headSha"),
            "workflowName": obj.get("workflowName"),
            "status": obj.get("status"),
            "conclusion": obj.get("conclusion"),
            "readStanding": "GITHUB_OWNER_READ_SUCCESS",
        }
    except OSError, ValueError, json.JSONDecodeError, subprocess.TimeoutExpired:
        return {
            "evidenceRef": run_ref,
            "runId": int(run_id.group(1)),
            "url": None,
            "headSha": None,
            "workflowName": None,
            "status": None,
            "conclusion": None,
            "readStanding": "OWNER_UNAVAILABLE_OR_IDENTITY_MISMATCH",
        }


def project_github_owner_justifications(
    *,
    work: dict[str, Any],
    contract: dict[str, Any],
    git_repo: Path,
) -> dict[str, Any]:
    """Perform bounded native Git/Owner reads and project proof-support actions."""
    local_sha = _native_git_head(git_repo)
    work_ref, rev, snapshot, can_commit, repo, claims, requirements = _contract(
        work=work, contract=contract, local_source_cut=local_sha
    )
    observations: dict[str, dict[str, Any]] = {
        ref: _github_run(repo=repo, run_ref=ref) for ref in sorted(requirements)
    }
    states: dict[str, str] = {}
    evidence_rows: list[dict[str, Any]] = []
    for ref, workflow in sorted(requirements.items()):
        found = observations[ref]
        status = "OWNER_UNKNOWN"
        if found["readStanding"] == "GITHUB_OWNER_READ_SUCCESS":
            if found["headSha"] != local_sha:
                status = "SOURCE_MISMATCH"
            elif found["workflowName"] != workflow:
                status = "WORKFLOW_MISMATCH"
            elif found["status"] == "completed" and found["conclusion"] == "success":
                status = "MATCHED_CHECK_SUCCESS"
            elif found["status"] == "completed":
                status = "CHECK_NOT_SUCCESSFUL"
            else:
                status = "CHECK_NOT_COMPLETE"
        states[ref] = status
        evidence_rows.append(
            {
                "evidenceRef": ref,
                "requiredWorkflow": workflow,
                "ownerReadStanding": found["readStanding"],
                "qualification": status,
                "observedHeadSha": found["headSha"],
                "observedWorkflow": found["workflowName"],
                "observedRunStatus": found["status"],
                "observedConclusion": found["conclusion"],
                "ownerUrl": found["url"],
            }
        )
    results: list[dict[str, Any]] = []
    actions: list[str] = []
    counts = {"EVIDENCE_REQUIREMENTS_SATISFIED": 0, "UNKNOWN": 0}
    for claim in claims:
        paths = []
        for path in claim["anyOf"]:
            qualifications = [states[edge["evidenceRef"]] for edge in path["allOf"]]
            complete = all(q == "MATCHED_CHECK_SUCCESS" for q in qualifications)
            paths.append(
                {
                    "justificationId": path["id"],
                    "standing": "ALL_OWNER_CHECKS_MATCHED"
                    if complete
                    else "NOT_ALL_OWNER_CHECKS_MATCHED",
                    "evidenceRefs": [edge["evidenceRef"] for edge in path["allOf"]],
                    "qualifications": qualifications,
                }
            )
        accepted = any(path["standing"] == "ALL_OWNER_CHECKS_MATCHED" for path in paths)
        outcome = "EVIDENCE_REQUIREMENTS_SATISFIED" if accepted else "UNKNOWN"
        counts[outcome] += 1
        action = (
            "CONSUME_EXISTING_EXACT_GITHUB_CHECK_RESULT"
            if accepted
            else "QUALIFY_OWNER_CHECK_NOT_AUTOMATIC_RERUN"
        )
        results.append(
            {
                "claimId": claim["id"],
                "consumerRef": work_ref,
                "supportStanding": outcome,
                "agentDecision": action,
                "justifications": paths,
                "domainClaimVerified": False,
                "automaticVerifierExecution": False,
            }
        )
        actions.append(
            f"{_GENERATED_PREFIX}{claim['id']}: "
            + (
                "read matching completed GitHub workflow evidence for exact SourceCut; "
                "do not rerun this same check by default"
                if accepted
                else "existing Owner run does not fully match current evidence requirements; "
                "resolve missing/failed/mismatched Owner evidence before scoped rerun"
            )
        )

    proposed: dict[str, Any] | None = None
    if can_commit and len(actions) <= 64 and all(len(x) <= 4096 for x in actions):
        retained = [
            action for action in snapshot["nextActions"] if not action.startswith(_GENERATED_PREFIX)
        ]
        if len(retained) + len(actions) <= 128:
            proposed = {key: snapshot[key] for key in _HOST_SNAPSHOT_FIELDS}
            proposed["nextActions"] = retained + actions
    return {
        "schemaVersion": 1,
        "kind": "ordivon.agent-host-github-justification-projection",
        "truthRole": "owner-live-workflow-status-not-program-or-domain-correctness",
        "repo": repo,
        "targetSourceCut": local_sha,
        "workRef": work_ref,
        "expectedRevision": rev,
        "basisDigest": canonical_digest({"contract": contract, "workRef": work_ref}),
        "evidence": evidence_rows,
        "claims": results,
        "summary": {
            "exactWorkflowRequirementsSatisfied": counts["EVIDENCE_REQUIREMENTS_SATISFIED"],
            "unknownOrNotMatching": counts["UNKNOWN"],
            "newVerificationJobsCreated": 0,
        },
        "proposedWorkSnapshot": proposed,
        "proposedHostCommitEligible": proposed is not None,
        "nonClaims": [
            "GitHub reports workflow completion for exact SHA, not domain or software correctness.",
            "GitHub CLI owner read is not a cryptographic attestation of a built artifact.",
            "Justification contracts are consumer-declared, not Owner-certified dependency closure.",
            "No unchanged-readset inference, installed state, live Security grant or external effect is certified.",
            "No Runtime job, GitHub rerun, Host CAS write, or independent Principal action occurs.",
        ],
    }
