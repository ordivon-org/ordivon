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
                if (
                    not isinstance(edge, dict)
                    or not {"evidenceRef", "workflowName"} <= set(edge)
                    or not set(edge) <= {"evidenceRef", "workflowName", "requiredJobs"}
                ):
                    raise CircuitContractError(
                        "evidence requires exact Owner ref, workflow and optional requiredJobs"
                    )
                if "requiredJobs" in edge:
                    jobs = edge["requiredJobs"]
                    if not isinstance(jobs, list) or not 1 <= len(jobs) <= 16:
                        raise CircuitContractError("requiredJobs must be nonempty and bounded")
                    job_names: set[str] = set()
                    for job in jobs:
                        if not isinstance(job, dict) or set(job) != {"name", "requiredSteps"}:
                            raise CircuitContractError("required job has invalid shape")
                        name = _text(job["name"], label="required job name")
                        if name in job_names:
                            raise CircuitContractError("duplicate required job")
                        job_names.add(name)
                        steps = job["requiredSteps"]
                        if not isinstance(steps, list) or not 1 <= len(steps) <= 24:
                            raise CircuitContractError("requiredSteps must be nonempty and bounded")
                        validated = [_text(step, label="required step name") for step in steps]
                        if len(set(validated)) != len(validated):
                            raise CircuitContractError("duplicate required step")
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
        "databaseId,headSha,status,conclusion,workflowName,url,jobs",
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
            # The original GitHub API owns the job/step observations. A
            # missing/truncated jobs payload cannot satisfy a scoped check.
            "jobs": obj.get("jobs")
            if isinstance(obj.get("jobs"), list) and len(obj["jobs"]) <= 256
            else None,
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
            "jobs": None,
            "readStanding": "OWNER_UNAVAILABLE_OR_IDENTITY_MISMATCH",
        }


def _qualify_job_steps(
    *,
    owner_run: dict[str, Any],
    required_jobs: list[dict[str, Any]],
) -> tuple[str, list[dict[str, Any]]]:
    """Check exact required job and step names, NOT all possible CI coverage.

    A workflow with successful top-level conclusion can still have skipped
    steps. Unobserved/ambiguous job-step evidence never counts as success.
    """
    job_data = owner_run.get("jobs")
    if not isinstance(job_data, list):
        return "OWNER_JOB_SCOPE_UNKNOWN", []
    observations: list[dict[str, Any]] = []
    standing = "MATCHED_CHECK_SUCCESS"
    for required in required_jobs:
        name = required["name"]
        matched_jobs = [
            row for row in job_data if isinstance(row, dict) and row.get("name") == name
        ]
        if len(matched_jobs) != 1:
            observations.append(
                {
                    "jobName": name,
                    "jobId": None,
                    "jobStatus": None,
                    "jobConclusion": None,
                    "steps": [],
                }
            )
            standing = "REQUIRED_JOB_MISSING_OR_AMBIGUOUS"
            continue
        job = matched_jobs[0]
        # A job is identified by its original provider job ID, not the
        # caller-declared job name alone.
        job_id = job.get("databaseId")
        valid_job_id = type(job_id) is int and job_id > 0
        steps_data = job.get("steps")
        found_steps: list[dict[str, Any]] = []
        matched = (
            valid_job_id
            and job.get("status") == "completed"
            and job.get("conclusion") == "success"
            and isinstance(steps_data, list)
        )
        for requested_step in required["requiredSteps"]:
            matches = [
                step
                for step in (steps_data if isinstance(steps_data, list) else [])
                if isinstance(step, dict) and step.get("name") == requested_step
            ]
            if len(matches) == 1:
                step = matches[0]
                found_steps.append(
                    {
                        "stepName": requested_step,
                        "status": step.get("status")
                        if isinstance(step.get("status"), str)
                        else None,
                        "conclusion": step.get("conclusion")
                        if isinstance(step.get("conclusion"), str)
                        else None,
                    }
                )
                matched = (
                    matched
                    and step.get("status") == "completed"
                    and step.get("conclusion") == "success"
                )
            else:
                found_steps.append({"stepName": requested_step, "status": None, "conclusion": None})
                matched = False
        observations.append(
            {
                "jobName": name,
                "jobId": job_id if valid_job_id else None,
                "jobStatus": job.get("status") if isinstance(job.get("status"), str) else None,
                "jobConclusion": job.get("conclusion")
                if isinstance(job.get("conclusion"), str)
                else None,
                "steps": found_steps,
            }
        )
        if not matched:
            standing = "REQUIRED_JOB_OR_STEP_NOT_SUCCESSFUL"
    return standing, observations


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
            qualifications: list[str] = []
            scoped_rows: list[dict[str, Any]] = []
            for edge in path["allOf"]:
                ref = edge["evidenceRef"]
                qualification = states[ref]
                if "requiredJobs" in edge:
                    job_observations: list[dict[str, Any]] = []
                    if qualification == "MATCHED_CHECK_SUCCESS":
                        qualification, job_observations = _qualify_job_steps(
                            owner_run=observations[ref],
                            required_jobs=edge["requiredJobs"],
                        )
                    scoped_rows.append(
                        {
                            "evidenceRef": ref,
                            "requiredJobs": edge["requiredJobs"],
                            "qualification": qualification,
                            "jobObservations": job_observations,
                        }
                    )
                qualifications.append(qualification)
            complete = all(q == "MATCHED_CHECK_SUCCESS" for q in qualifications)
            path_row = {
                "justificationId": path["id"],
                "standing": "ALL_OWNER_CHECKS_MATCHED"
                if complete
                else "NOT_ALL_OWNER_CHECKS_MATCHED",
                "evidenceRefs": [edge["evidenceRef"] for edge in path["allOf"]],
                "qualifications": qualifications,
            }
            if scoped_rows:
                path_row["scopedJobEvidence"] = scoped_rows
            paths.append(path_row)
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
        scoped_requested = any("scopedJobEvidence" in path for path in paths)
        skipped_or_failed = any(
            detail["qualification"] == "REQUIRED_JOB_OR_STEP_NOT_SUCCESSFUL"
            for path in paths
            for detail in path.get("scopedJobEvidence", [])
        )
        if accepted:
            hint = (
                "required GitHub job/step Owner evidence matched at exact SourceCut; "
                "do not repeat this same check by default"
                if scoped_requested
                else "read matching completed GitHub workflow evidence for exact SourceCut; "
                "do not rerun this same check by default"
            )
        elif skipped_or_failed:
            hint = (
                "a consumer-required GitHub job/step was not successful (possibly skipped); "
                "inspect its original Owner observation, do not turn workflow GREEN into proof or rerun automatically"
            )
        else:
            hint = (
                "existing Owner run does not fully match current evidence requirements; "
                "resolve missing/failed/mismatched Owner evidence before scoped rerun"
            )
        actions.append(f"{_GENERATED_PREFIX}{claim['id']}: {hint}")

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
            "GitHub reports workflow/job/step completion for exact SHA, not domain or software correctness.",
            "GitHub CLI owner read is not a cryptographic attestation of a built artifact.",
            "GitHub job/step conclusion is post continue-on-error and may differ from underlying step outcome; the latter is not certified by gh run view jobs.",
            "Justification contracts are consumer-declared, not Owner-certified dependency closure.",
            "No unchanged-readset inference, installed state, live Security grant or external effect is certified.",
            "No Runtime job, GitHub rerun, Host CAS write, or independent Principal action occurs.",
        ],
    }


def combine_github_justification_with_source_impact(
    *,
    workflow_result: dict[str, Any],
    git_source_delta: dict[str, Any],
    source_readset_evidence: dict[str, Any],
) -> dict[str, Any]:
    """Conjoin *separate* Owner facts and C04 impact, not their authorities.

    Git source delta MUST already be requalified by the existing native Git
    caller. Readsets are caller/Agent declared and never certify negative,
    dynamic or environment closure. We can avoid an *identical* GitHub workflow
    rerun after matching a current successful Owner result; we CANNOT infer
    domain applicability from either the workflow status or C04's graph.
    """
    from .verification_impact import select_source_readset_impacts

    impact = select_source_readset_impacts(
        git_source_delta=git_source_delta,
        source_readset_evidence=source_readset_evidence,
    )
    if impact["sourceCut"] != workflow_result["targetSourceCut"]:
        raise CircuitContractError("Git/Owner/Work applicability SourceCut mismatch")
    claim_ids = [c["claimId"] for c in workflow_result["claims"]]
    impacted = {row["id"]: row["standing"] for row in impact["selection"]["standingByObligation"]}
    if set(impacted) != set(claim_ids) or len(impacted) != len(claim_ids):
        raise CircuitContractError(
            "every consumer Claim needs exactly one C04 readset obligation with same id"
        )
    decisions: list[dict[str, Any]] = []
    generated: list[str] = []
    for c in workflow_result["claims"]:
        identity = c["claimId"]
        standing = impacted[identity]
        support = c["supportStanding"]
        if support == "UNKNOWN":
            next_action = "LOCATE_CURRENT_OWNER_RESULT_BEFORE_SCOPED_RECHECK"
            guidance = "query matching current Owner check before any scoped verifier decision"
        elif standing == "RECHECK_REQUIRED":
            next_action = "CURRENT_WORKFLOW_ALREADY_CHECKED_QUALIFY_DOMAIN"
            guidance = "current exact workflow already completed; do not repeat it just because an input changed; qualify domain/readset separately"
        elif standing == "UNKNOWN":
            next_action = "CURRENT_WORKFLOW_KNOWN_READSET_UNKNOWN"
            guidance = "current exact workflow completed, but dynamic/negative source dependency closure is unknown; qualify dependencies"
        elif standing == "REUSE_CANDIDATE":
            next_action = "CURRENT_WORKFLOW_KNOWN_DOMAIN_UNCERTIFIED"
            guidance = (
                "current exact workflow completed; C04 candidate alone is no domain acceptance"
            )
        else:
            raise CircuitContractError("unexpected C04 impact standing")
        decisions.append(
            {
                "claimId": identity,
                "ownerWorkflowStanding": support,
                "sourceImpactStanding": standing,
                "agentDecision": next_action,
                "domainProofApplicability": "UNKNOWN_NOT_OWNER_CERTIFIED",
                "ownerCertifiedReadsetClosure": False,
                "domainClaimVerified": False,
                "automaticVerifierExecution": False,
            }
        )
        generated.append(f"{_GENERATED_PREFIX}{identity}: {guidance}")

    # Both paths remain nonauthoritative; source/owner *address* matching is
    # the only certified scope. Never encode source-readset 'complete=True'
    # as an Owner verified fact. Reuse existing CAS proposal and prefix
    # replacement; do not fork a second Work write engine.
    proposal = workflow_result["proposedWorkSnapshot"]
    if proposal is not None:
        retained = [a for a in proposal["nextActions"] if not a.startswith(_GENERATED_PREFIX)]
        if len(retained) + len(generated) <= 128 and all(len(a) <= 4096 for a in generated):
            proposal["nextActions"] = retained + generated
        else:
            proposal = None
    workflow_result["proposedWorkSnapshot"] = proposal
    workflow_result["proposedHostCommitEligible"] = proposal is not None
    workflow_result["sourceApplicability"] = {
        "sourceCut": impact["sourceCut"],
        "queryPrefix": impact["queryPrefix"],
        "impactBasisDigest": impact["selection"]["basisDigest"],
        "membershipClosureQualification": impact["membershipClosureQualification"],
        "readsetDependencyQualification": impact["readsetDependencyQualification"],
        "gitRequalifiedByCaller": True,
        "ownerCertifiedReadsetClosure": False,
        "domainProofApplicabilityCertified": False,
        "wholeSuiteRerunRequested": False,
        "claims": decisions,
    }
    workflow_result["nonClaims"].append(
        "The Git report was independently requalified by the CLI; caller readset completeness and domain/negative/environment dependency closure remain UNKNOWN."
    )
    return workflow_result
