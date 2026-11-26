#!/usr/bin/env python3
"""Read-only Agent decision on existing GitHub checks and native source impact.

This is NOT a verifier, evidence database, execution admission/PDP, or a
cross-SourceCut proof-reuse engine. A successful Check Run is only evidence
that that named check finished successfully at its exact Git commit.
"""

from __future__ import annotations

import argparse
import ast
import json
import re
import subprocess
from pathlib import Path
from typing import Any

import convergence_plan
from ci_telemetry import Gh
from evidence_check_decision import _decision, _standing
from evidence_formal_archive import (
    ARCHIVE_PROVENANCE,
    decode_report_json,
    download_formal_archive,
)
from evidence_github_checks import (
    CheckObservationError,
    _provider_checks,
    _select_check,
    bounded_provider_rows,
)
from evidence_source_policy import qualify_current_selector
from formal_github_origin import (
    KIND as ORIGIN_KIND,
)
from formal_github_origin import (
    ORIGIN_QUALIFICATION,
    artifact_identity,
    git_witness,
    qualify_origin,
)
from source_history_legos import current_tree, require_ancestral_source_cuts
from source_history_legos import git as git_native

DEFAULT_REPOSITORY = "ordivon-org/ordivon"
REPO_PATTERN = re.compile(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+")
SHA_PATTERN = re.compile(r"(?:[0-9a-f]{40}|[0-9a-f]{64})")


def _exact_commit(sha: str, *, repo: Path | None = None) -> str:
    if not isinstance(sha, str) or not SHA_PATTERN.fullmatch(sha):
        raise ValueError("evidence SourceCut requires a literal full Git commit SHA")
    actual = (
        convergence_plan._git("rev-parse", f"{sha}^{{commit}}")
        if repo is None
        else git_native(repo, "--no-replace-objects", "rev-parse", f"{sha}^{{commit}}").strip()
    )
    if actual != sha:
        raise ValueError("evidence SourceCut does not match native Git commit")
    return sha


def decide(
    *,
    repo: str,
    current_sha: str,
    prior_sha: str | None = None,
    check_name: str = "root-verification",
    github: Gh | None = None,
    git_repo: Path | None = None,
    current_workflow_run_id: int | None = None,
    prior_workflow_run_id: int | None = None,
) -> dict[str, Any]:
    if not REPO_PATTERN.fullmatch(repo) or repo != DEFAULT_REPOSITORY:
        raise ValueError("GitHub repository must be the canonical Ordivon owner/name")
    if not check_name or len(check_name) > 128:
        raise ValueError("Check Run name must be nonempty and bounded")
    current_sha = _exact_commit(current_sha, repo=git_repo)
    if prior_sha is not None:
        prior_sha = _exact_commit(prior_sha, repo=git_repo)
    gh = github or Gh(repo)
    current = _select_check(
        _provider_checks(gh, repo, current_sha),
        sha=current_sha,
        check_name=check_name, gh=gh, repo=repo,
        workflow_run_id=current_workflow_run_id,
    )
    past = None
    # A current pending/failed result already determines this Check Run's
    # standing. Do not query an older provider result that could error and
    # falsely obscure a real current failure or in-flight Job.
    if prior_sha and prior_sha != current_sha and _standing(current) == "ABSENT":
        past = _select_check(
            _provider_checks(gh, repo, prior_sha),
            sha=prior_sha,
            check_name=check_name, gh=gh, repo=repo,
            workflow_run_id=prior_workflow_run_id,
        )
    impact = None
    if (
        prior_sha is not None
        and prior_sha != current_sha
        and _standing(current) == "ABSENT"
        and _standing(past) == "PASS"
    ):
        try:
            # Use existing native Git ancestry check, not a sibling PR diff.
            source_repo = git_repo or Path.cwd()
            require_ancestral_source_cuts(source_repo, prior_sha, current_sha)
            # The existing selector reads the executing checkout and cwd.
            # Do not silently reinterpret an explicitly different source repo.
            if source_repo.resolve() != Path.cwd().resolve():
                raise ValueError("selector cwd differs from explicit source repository")
            qualify_current_selector(source_repo, current_sha)
            impact = convergence_plan.build_plan(base=prior_sha, head=current_sha)
            qualify_current_selector(source_repo, current_sha)
        except (ValueError, subprocess.CalledProcessError):
            # Nonancestral or unqualified selection is UNKNOWN, not "no hit".
            impact = None
    result = _decision(
        current_sha=current_sha,
        prior_sha=prior_sha,
        check_name=check_name,
        current_check=current,
        prior_check=past,
        source_impact=impact,
    )
    result["repository"] = repo
    return result


def _formal_declared_files(repo: Path, sha: str) -> tuple[str, ...]:
    """Parse the historical native Formal SOURCE_FILES, never execute it."""
    code = git_native(
        repo, "--no-replace-objects", "show", f"{sha}:tools/formal/verify.py"
    )
    source = ast.parse(code, filename=f"{sha}:tools/formal/verify.py")
    declarations = [
        stmt.value
        for stmt in source.body
        if isinstance(stmt, ast.Assign)
        and len(stmt.targets) == 1
        and isinstance(stmt.targets[0], ast.Name)
        and stmt.targets[0].id == "SOURCE_FILES"
    ]
    if len(declarations) != 1:
        raise ValueError("formal historical SOURCE_FILES is not uniquely declared")
    try:
        paths = ast.literal_eval(declarations[0])
    except (ValueError, TypeError, SyntaxError, MemoryError, RecursionError) as exc:
        raise ValueError(
            "formal SOURCE_FILES is not a native literal declaration"
        ) from exc
    if (
        not isinstance(paths, tuple)
        or not 1 <= len(paths) <= 1000
        or any(
            not isinstance(path, str)
            or not path
            or path.startswith("/")
            or ".." in Path(path).parts
            or "\\" in path
            for path in paths
        )
        or len(set(paths)) != len(paths)
        or "tools/formal/verify.py" not in paths
    ):
        raise ValueError("formal SOURCE_FILES does not declare a safe bounded set")
    return paths


def _formal_member_delta(
    repo: Path, prior_sha: str, current_sha: str
) -> tuple[tuple[str, ...], tuple[str, ...], list[str]]:
    """Compare declared members, not unrelated entries in the containing trees."""
    old = _formal_declared_files(repo, prior_sha)
    new = _formal_declared_files(repo, current_sha)
    old_tree = current_tree(repo, prior_sha)
    new_tree = current_tree(repo, current_sha)
    old_members = {path: old_tree.get(path) for path in old}
    new_members = {path: new_tree.get(path) for path in new}
    if any(
        value is None or not value.startswith(("100644:blob:", "100755:blob:"))
        for members in (old_members, new_members)
        for value in members.values()
    ):
        raise ValueError(
            "Formal source comparison contains unqualified Git member (missing/non-regular)"
        )
    changed = [
        path for path in sorted(old_members.keys() | new_members.keys())
        if old_members.get(path) != new_members.get(path)
    ]
    return old, new, changed


def declared_formal_source_delta(
    *,
    repo: Path,
    prior_sha: str,
    current_sha: str,
) -> dict[str, Any]:
    """Evidence about SOURCE_FILES Git members, NOT proof/toolchain reuse.

    Reuse the existing Formal producer's literal declaration at BOTH
    cuts, and the native immutable Git source-history membership query.
    Dynamic tool/loader, environment and consumer closure stay UNKNOWN.
    """
    prior_sha = _exact_commit(prior_sha, repo=repo)
    current_sha = _exact_commit(current_sha, repo=repo)
    require_ancestral_source_cuts(repo, prior_sha, current_sha)
    old, new, changed = _formal_member_delta(repo, prior_sha, current_sha)
    return {
        "schemaVersion": 1,
        "kind": "ordivon.formal-declared-git-readset-delta",
        "producer": "tools/formal/verify.py::SOURCE_FILES",
        "sourceCuts": {"prior": prior_sha, "current": current_sha},
        "standing": (
            "UNCHANGED_DECLARED_SOURCE_INPUTS"
            if not changed and old == new
            else "CHANGED_DECLARED_SOURCE_INPUTS"
        ),
        "priorDeclaredPaths": len(old),
        "currentDeclaredPaths": len(new),
        "changedDeclaredPaths": changed,
        "declarationChanged": old != new,
        "declaredSourceReadsetComparisonComplete": True,
        "proofReuseAdmissible": False,
        "unresolved": [
            "No verifier/toolchain dynamic input equivalence attested",
            "No qualified previously executed proof receipt was consumed",
            "No installed/physical consumer or environmental assumption equivalence",
        ],
    }


def inspect_historical_formal_report(
    *, repo: Path, source_sha: str, report: dict[str, Any]
) -> dict[str, Any]:
    """Bind local historical report contents to immutable Git inputs only.

    This checks content consistency, NOT the claimed CI artifact's
    authenticity, verifier execution, domain correctness or toolchain
    equivalence. Those remain separate proof obligations.
    """
    source_sha = _exact_commit(source_sha, repo=repo)
    if not isinstance(report, dict) or report.get("kind") != (
        "source-scoped-native-formal-toolchain-check"
    ):
        raise ValueError("invalid native Formal report kind")
    if report.get("sourceCut") != source_sha or report.get("status") != "PASS":
        raise ValueError("historical Formal report source/status mismatch")
    if (
        report.get("proofReuseAdmissible") is not False
        or report.get("sourceQualification") != "EXACT_GIT_BLOBS_CHECKED_PRE_AND_POST"
        or report.get("toolQualification")
        != "MISE_RESOLVED_EXECUTABLE_SHA256_PRE_AND_POST"
    ):
        raise ValueError("historical Formal report qualification unsupported")
    files = _formal_declared_files(repo, source_sha)
    blobs = report.get("sourceBlobs")
    if not isinstance(blobs, dict) or set(blobs) != set(files):
        raise ValueError("historical Formal report source membership mismatch")
    tree = current_tree(repo, source_sha)
    for path in files:
        oid = blobs[path]
        if not isinstance(oid, str) or tree.get(path) not in (
            "100644:blob:" + oid,
            "100755:blob:" + oid,
        ):
            raise ValueError("historical Formal report source blob mismatch")
    probes = report.get("probes")
    if (
        not isinstance(probes, list)
        or not probes
        or type(report.get("count")) is not int
        or report["count"] != len(probes)
        or any(
            not isinstance(probe, dict)
            or probe.get("result") != "PASS"
            or not isinstance(probe.get("probe"), str)
            or not probe["probe"].strip()
            or probe["probe"] != probe["probe"].strip()
            for probe in probes
        )
        or len({probe["probe"] for probe in probes}) != len(probes)
    ):
        raise ValueError("historical Formal report probe inventory invalid")
    tools = report.get("toolBinaries")
    if not isinstance(tools, dict) or set(tools) != {
        "lean",
        "z3",
        "cvc5",
        "verus",
        "dafny",
        "kani",
        "quint",
        "alloy",
    }:
        raise ValueError("historical Formal report tool inventory mismatch")
    for record in tools.values():
        if (
            not isinstance(record, dict)
            or any(
                not isinstance(record.get(field), str) or not record[field]
                for field in ("path", "version", "sha256")
            )
            or not re.fullmatch(r"[0-9a-f]{64}", record["sha256"])
        ):
            raise ValueError("historical Formal report tool provenance invalid")
    # Retain the original source producer's finite *observations* for an
    # optional read-only comparison; do not promote them into a full readset.
    resources = report.get("toolResources")
    z3 = report.get("z3ObservedElfDependencies")
    valid_resources = (
        isinstance(resources, dict)
        and set(resources) == {"alloyAppJar", "alloyJvm"}
        and all(
            isinstance(row, dict)
            and isinstance(row.get("path"), str)
            and row["path"].startswith("/")
            and isinstance(row.get("sha256"), str)
            and re.fullmatch(r"[0-9a-f]{64}", row["sha256"]) is not None
            for row in resources.values()
        )
    )
    valid_z3 = (
        isinstance(z3, dict)
        and isinstance(z3.get("scope"), str)
        and z3["scope"].startswith("linux-elf64-")
        and z3.get("entrypointSha256") == tools["z3"]["sha256"]
        and isinstance(z3.get("interpreterPath"), str)
        and z3["interpreterPath"].startswith("/")
        and isinstance(z3.get("resolvedLibraries"), dict)
        and bool(z3["resolvedLibraries"])
        and all(
            isinstance(path, str)
            and path.startswith("/")
            and isinstance(digest, str)
            and re.fullmatch(r"[0-9a-f]{64}", digest) is not None
            for path, digest in z3["resolvedLibraries"].items()
        )
    )
    tool_snapshot = (
        {
            "toolBinaries": tools,
            "toolResources": resources,
            "z3ObservedElfDependencies": z3,
        }
        if valid_resources and valid_z3
        else None
    )
    return {
        "schemaVersion": 1,
        "kind": "ordivon.historical-formal-receipt-content-binding",
        "sourceCut": source_sha,
        "standing": "CONTENT_MATCHES_DECLARED_GIT_SOURCE",
        "declaredSourcePaths": len(files),
        "reportedProbeCount": len(probes),
        "reportedToolEntrypoints": len(tools),
        "artifactProvenance": "UNVERIFIED_LOCAL_INPUT",
        "runtimeAndToolchainEquivalence": "UNKNOWN",
        "originalObservedToolInputs": tool_snapshot,
        "proofReuseAdmissible": False,
    }


def inspect_historical_formal_report_file(
    *, repo: Path, source_sha: str, path: Path
) -> dict[str, Any]:
    """Read bounded JSON downloaded from the official existing GitHub run."""
    if path.is_symlink() or not path.is_file() or path.stat().st_size > 1048576:
        raise ValueError("historical Formal report must be bounded regular file")
    payload = decode_report_json(path.read_bytes())
    return inspect_historical_formal_report(
        repo=repo,
        source_sha=source_sha,
        report=payload,
    )


def compare_formal_execution_inputs_to_candidate(
    *,
    repo: Path,
    execution_sha: str,
    candidate_sha: str,
) -> dict[str, Any]:
    """Compare two immutable Formal input snapshots, not Git ancestry.

    An actual PR synthetic merge is often NOT ancestor of PR Head; exact
    Git input equivalence is distinct from historical proof reuse.
    """
    execution_sha = _exact_commit(execution_sha, repo=repo)
    candidate_sha = _exact_commit(candidate_sha, repo=repo)
    original, current, changed = _formal_member_delta(
        repo, execution_sha, candidate_sha
    )
    return {
        "schemaVersion": 1,
        "kind": "ordivon.formal-execution-inputs-vs-candidate",
        "executionSourceCut": execution_sha,
        "candidateSourceCut": candidate_sha,
        "comparisonBasis": "TWO_IMMUTABLE_GIT_SNAPSHOTS_NOT_TEMPORAL_PROOF",
        "standing": (
            "UNCHANGED_DECLARED_SOURCE_INPUTS"
            if not changed and original == current
            else "CHANGED_DECLARED_SOURCE_INPUTS"
        ),
        "priorDeclaredPaths": len(original),
        "candidateDeclaredPaths": len(current),
        "changedDeclaredPaths": changed,
        "declaredSourceReadsetComparisonComplete": True,
        "proofReuseAdmissible": False,
        "unresolved": [
            "Toolchain, libraries, environment, time and external assumptions not compared",
            "Scope is only the native Formal declared Git SOURCE_FILES",
            "No implementation/physical consumer refinement proof",
        ],
    }


def _workflow_formal_artifact(
    *,
    gh: Gh,
    repo: str,
    run_id: str,
    head_sha: str,
    run: dict[str, Any],
    git_repo: Path,
) -> tuple[dict[str, Any], str, str, dict[str, Any] | None]:
    """Select one actual Formal Artifact, not an artifact guessed from PR head.

    GitHub's pull_request workflow Check Run is tied to PR Head while
    github.sha/checked-out Formal SourceCut is a synthetic merge commit.
    Reconstruct the exact two-parent Git relationship before accepting
    the merge SourceCut as a historical execution context.
    """
    attempt = run.get("run_attempt", 1)
    rows = bounded_provider_rows(
        gh, f"repos/{repo}/actions/runs/{run_id}/artifacts",
        key="artifacts", label="historical Formal Artifact",
    )
    matching = []
    for row in rows:
        identity = artifact_identity(row.get("name"))
        if identity is not None and (
            identity[1] == attempt or (attempt == 1 and identity[1] is None)
        ):
            matching.append((row, identity[0]))
    if not matching and attempt != 1:
        raise CheckObservationError(
            "UNKNOWN_FORMAL_ARTIFACT_ATTEMPT",
            "no original Formal artifact for the exact current workflow attempt",
        )
    if len(matching) != 1:
        raise ValueError("historical Formal Artifact must have one exact producer")
    artifact, actual_sha = matching[0]
    _exact_commit(actual_sha, repo=git_repo)
    workflow = artifact.get("workflow_run")
    if (
        artifact.get("expired") is not False
        or not isinstance(workflow, dict)
        or workflow.get("id") != int(run_id)
        or workflow.get("head_sha") != head_sha
        or type(artifact.get("size_in_bytes")) is not int
        or not 0 < artifact["size_in_bytes"] <= 1048576
        or not isinstance(artifact.get("digest"), str)
        or re.fullmatch(r"sha256:[0-9a-f]{64}", artifact["digest"]) is None
    ):
        raise ValueError("historical Formal Artifact provenance is unqualified")
    witness = None
    if actual_sha == head_sha:
        relation = "DIRECT_WORKFLOW_HEAD"
    else:
        if run.get("event") != "pull_request":
            raise ValueError("non-PR workflow Artifact source differs from Head")
        prs = run.get("pull_requests")
        if not isinstance(prs, list) or len(prs) > 1:
            raise ValueError("PR workflow lacks unique exact provenance")
        lineage = (
            git_native(git_repo, "--no-replace-objects", "rev-list",
                       "--parents", "-n", "1", actual_sha).strip().split()
        )
        if len(lineage) != 3 or lineage[0] != actual_sha or lineage[2] != head_sha:
            raise ValueError("PR synthetic merge parents mismatch original Run")
        if not prs:
            # GitHub can drop PR associations after a PR is merged. Preserve
            # independently qualified archive/content and Git parent facts,
            # but do NOT promote the missing original base attestation.
            relation = "PR_SYNTHETIC_MERGE_HEAD_MATCH_BASE_UNATTESTED"
        else:
            pr = prs[0]
            if (
                not isinstance(pr, dict)
                or type(pr.get("number")) is not int or pr["number"] <= 0
                or not isinstance(pr.get("head"), dict)
                or not isinstance(pr.get("base"), dict)
                or pr["head"].get("sha") != head_sha
            ):
                raise ValueError("PR workflow Head SourceCut does not match provider")
            if lineage[1] != pr["base"].get("sha"):
                raise ValueError("PR synthetic merge parents mismatch original Run")
            relation = "PR_SYNTHETIC_MERGE_BASE_AND_HEAD"
        witness = {
            "observedBase": lineage[1], "observedHead": lineage[2],
            "providerBaseAttested": relation == "PR_SYNTHETIC_MERGE_BASE_AND_HEAD",
        }
    return artifact, actual_sha, relation, witness


def _origin_producer_job(gh, repo, run_id, attempt, head_sha):
    """Independently observe the actual publication step in the same Attempt."""
    jobs = bounded_provider_rows(
        gh, f"repos/{repo}/actions/runs/{run_id}/attempts/{attempt}/jobs",
        key="jobs", label="Formal producer Attempt Jobs",
    )
    matches = [job for job in jobs if job.get("name") == "repo-preflight"]
    if len(matches) != 1:
        raise ValueError("original Formal producer Attempt Job not unique")
    job = matches[0]
    steps = job.get("steps")
    if (
        job.get("run_id") != int(run_id) or job.get("run_attempt") != attempt
        or job.get("head_sha") != head_sha or job.get("status") != "completed"
        or job.get("conclusion") != "success" or not isinstance(steps, list)
        or job.get("check_run_url") != f"https://api.github.com/repos/{repo}/check-runs/{job['id']}"
    ):
        raise ValueError("original Formal producer Attempt Job identity mismatch")
    publications = [step for step in steps if isinstance(step, dict)
                    and step.get("name") == "Publish scoped native Formal evidence receipt"]
    if len(publications) != 1 or (
        publications[0].get("status"), publications[0].get("conclusion")
    ) != ("completed", "success"):
        raise ValueError("original Formal artifact publication step not successful")
    return job["id"]


def fetch_original_formal_report(
    *,
    repo: str,
    source_sha: str,
    github: Gh | None = None,
    candidate_sha: str | None = None,
    workflow_run_id: int | None = None,
) -> dict[str, Any]:
    """Read the native immutable Artifact ID and verify archive digest, then Git content.

    No generic proof permission or verification dispatch. Historical PR
    source binding and toolchain/consumer applicability remain independent.
    """
    source_sha = _exact_commit(source_sha)
    if repo != DEFAULT_REPOSITORY:
        raise ValueError("historical Formal report requires canonical repository")
    gh = github or Gh(repo)
    check = _select_check(
        _provider_checks(gh, repo, source_sha),
        sha=source_sha,
        check_name="root-verification", gh=gh, repo=repo,
        workflow_run_id=workflow_run_id,
    )
    if _standing(check) != "PASS":
        raise ValueError("historical Formal report requires prior successful check")
    run_id = str(check["workflowRunId"])
    attempt = check["workflowRunAttempt"]
    endpoint = f"repos/{repo}/actions/runs/{run_id}"

    def original_run():
        run = gh.api(endpoint)
        if (
            not isinstance(run, dict) or run.get("id") != int(run_id)
            or run.get("head_sha") != source_sha
            or not isinstance(run.get("repository"), dict)
            or run["repository"].get("full_name") != repo
            or run.get("check_suite_id") != check["checkSuiteId"]
            or run.get("run_attempt") != attempt
            or run.get("path") != ".github/workflows/ci.yml"
        ):
            raise ValueError("historical Formal workflow run SourceCut mismatch")
        return run

    run = original_run()
    artifact, execution_sha, source_relation, source_witness = _workflow_formal_artifact(
        gh=gh,
        repo=repo,
        run_id=run_id,
        head_sha=source_sha,
        run=run,
        git_repo=Path.cwd(),
    )
    name = artifact["name"]
    payload = download_formal_archive(repo, artifact)
    identity = artifact_identity(name)
    assert identity is not None
    origin = None
    producer_job_id = None
    if identity[1] is not None:
        origin = payload.get("githubExecutionOrigin")
        if not isinstance(origin, dict):
            raise CheckObservationError(
                "UNKNOWN_FORMAL_ARTIFACT_ATTEMPT",
                "attempt-specific name lacks original execution origin",
            )
        try:
            inputs = git_witness(Path.cwd(), execution_sha, origin.get("workflowSha"))
            qualify_origin(
                origin, source_cut=execution_sha, provider_head=source_sha,
                run_id=run_id, attempt=attempt, event_name=run.get("event"),
                git_inputs=inputs,
            )
            if (run.get("event") == "pull_request" and run.get("pull_requests")
                    and run["pull_requests"][0]["number"] != origin["pullRequestNumber"]):
                raise ValueError("original event PR number contradicts provider")
            producer_job_id = _origin_producer_job(gh, repo, run_id, attempt, source_sha)
        except (ValueError, KeyError, OSError, subprocess.SubprocessError) as exc:
            raise CheckObservationError(
                "UNKNOWN_FORMAL_ARTIFACT_ATTEMPT",
                "attempt-specific artifact origin or native producer job unqualified",
            ) from exc
        if source_relation == "PR_SYNTHETIC_MERGE_HEAD_MATCH_BASE_UNATTESTED":
            source_relation = "PR_SYNTHETIC_MERGE_CAPTURED_EVENT_BASE_AND_HEAD"
        if source_witness is not None:
            source_witness["producerEventCaptured"] = True
    result = inspect_historical_formal_report(
        repo=Path.cwd(), source_sha=execution_sha, report=payload,
    )
    original_run()
    result["originalCheckRunId"] = check["checkRunId"]
    result["originalWorkflowRunId"] = run_id
    result["originalWorkflowRunAttempt"] = attempt
    result["githubArtifactName"] = name
    result["githubArtifactId"] = artifact["id"]
    result["githubArtifactArchiveDigest"] = artifact["digest"]
    result["requestedWorkflowHeadSha"] = source_sha
    result["verifiedExecutionSourceCut"] = execution_sha
    result["sourceRelationship"] = source_relation
    if source_witness is not None:
        result["sourceRelationshipWitness"] = source_witness
    result["artifactProvenance"] = ARCHIVE_PROVENANCE
    result["archiveQualification"] = "EXACT_ARTIFACT_ID_SHA256_AND_SIZE"
    if origin is not None:
        result["githubExecutionOrigin"] = origin
        result["originQualification"] = ORIGIN_QUALIFICATION
        result["originalArtifactProducerJobId"] = producer_job_id
    if source_relation == "PR_SYNTHETIC_MERGE_HEAD_MATCH_BASE_UNATTESTED":
        result["sourceRelationshipObligation"] = "RECOVER_ORIGINAL_PROVIDER_PR_BASE_ATTESTATION"
    if candidate_sha is not None:
        result["executionInputsVsCandidate"] = (
            compare_formal_execution_inputs_to_candidate(
                repo=Path.cwd(),
                execution_sha=execution_sha,
                candidate_sha=candidate_sha,
            )
        )
    return result


def decide_with_optional_formal_source_delta(
    *,
    repo: str,
    current_sha: str,
    prior_sha: str | None,
    check_name: str,
    include_formal_source_delta: bool,
    github: Gh | None = None,
    git_repo: Path | None = None,
    current_workflow_run_id: int | None = None,
    prior_workflow_run_id: int | None = None,
) -> dict[str, Any]:
    """GitHub provider uncertainty does not erase immutable Git source evidence.

    A candidate SourceCut may exist locally before being pushed to GitHub.
    That yields no current provider Check Run, but original Formal Artifact
    and two original Git snapshots remain independently inspectable.
    """
    current_sha = _exact_commit(current_sha, repo=git_repo)
    if prior_sha is not None:
        prior_sha = _exact_commit(prior_sha, repo=git_repo)
    if repo != DEFAULT_REPOSITORY or not check_name or len(check_name) > 128:
        raise ValueError("unqualified repository or Check Run name")
    try:
        decision = decide(
            repo=repo,
            current_sha=current_sha,
            prior_sha=prior_sha,
            check_name=check_name,
            github=github,
            git_repo=git_repo,
            current_workflow_run_id=current_workflow_run_id,
            prior_workflow_run_id=prior_workflow_run_id,
        )
    except (
        OSError,
        ValueError,
        subprocess.CalledProcessError,
        json.JSONDecodeError,
    ) as exc:
        decision = {
            "schemaVersion": 1,
            "kind": "ordivon.source-check-evidence-decision",
            "repository": repo,
            "currentSourceCut": current_sha,
            "priorSourceCut": prior_sha,
            "disposition": "UNKNOWN_CURRENT_CHECK_PROVIDER",
            "nextOperation": (
                {
                    "UNKNOWN_AMBIGUOUS_WORKFLOW_CONTEXT": "select-explicit-workflow-run-id",
                    "UNKNOWN_REQUESTED_WORKFLOW_CONTEXT": "inspect-requested-workflow-run",
                    "UNKNOWN_CHECK_SUITE_COVERAGE": "inspect-native-check-suite-coverage",
                    "UNKNOWN_WORKFLOW_ATTEMPT_CHECK": "inspect-native-workflow-attempt",
                    "UNKNOWN_WORKFLOW_CONTEXT": "inspect-native-workflow-identity",
                }.get(exc.reason, "inspect-current-provider-when-published")
                if isinstance(exc, CheckObservationError)
                else "inspect-current-provider-when-published"
            ),
            "existingCheckReceiptReusable": False,
            "proofReuseAdmissible": False,
            "currentApplicability": "UNKNOWN_EXTERNAL_ASSUMPTIONS",
            "currentSecurityStanding": "NOT_ASSESSED_BY_CHECK_RECEIPT",
            "errorType": type(exc).__name__,
            "providerQualification": (
                exc.reason if isinstance(exc, CheckObservationError) else "UNKNOWN_PROVIDER_OR_SOURCE"
            ),
            "nonClaims": [
                "Missing current GitHub Check Run is not an execution failure",
                "Immutable local Git and prior Artifact evidence are independent",
            ],
        }
        if isinstance(exc, CheckObservationError) and exc.contexts:
            decision["observedWorkflowContexts"] = exc.contexts[:32]
            decision["observedWorkflowContextCount"] = len(exc.contexts)
            decision["observedWorkflowContextsComplete"] = len(exc.contexts) <= 32
    if not include_formal_source_delta:
        return decision
    if prior_sha is None:
        raise ValueError("--formal-source-delta requires --prior-sha")
    try:
        decision["formalDeclaredSourceDelta"] = declared_formal_source_delta(
            repo=git_repo or Path.cwd(),
            prior_sha=prior_sha,
            current_sha=current_sha,
        )
    except (ValueError, OSError, subprocess.CalledProcessError, SyntaxError) as exc:
        decision["formalDeclaredSourceDelta"] = {
            "schemaVersion": 1,
            "kind": "ordivon.formal-declared-git-readset-delta",
            "standing": "UNKNOWN_DECLARED_SOURCE_INPUTS",
            "declaredSourceReadsetComparisonComplete": False,
            "proofReuseAdmissible": False,
            "errorType": type(exc).__name__,
        }
    return decision


def observe_current_formal_tool_inputs(
    *, repo: Path, target_source_cut: str
) -> dict[str, Any]:
    """Native Formal producer pre/post tool observations without its main().

    Unlike a hermetic action manifest, this leaves plugins, dlopen, imports,
    host time and model→implementation refinement explicitly UNKNOWN.
    """
    import importlib.util

    target_source_cut = _exact_commit(target_source_cut)
    if repo.resolve() != Path.cwd().resolve():
        raise ValueError("Formal observer needs current Git repository")
    source = repo / "tools/formal/verify.py"
    if not source.is_file() or source.is_symlink():
        raise ValueError("missing or symlinked native Formal producer")
    expected = git_native(
        repo,
        "--no-replace-objects",
        "rev-parse",
        target_source_cut + ":tools/formal/verify.py",
    ).strip()
    actual = git_native(repo, "hash-object", "--no-filters", "--", str(source)).strip()
    if actual != expected:
        raise ValueError("unqualified local Formal producer source")
    spec = importlib.util.spec_from_file_location(
        "ordivon_formal_readonly_observer", source
    )
    if spec is None or spec.loader is None:
        raise ValueError("Formal producer import unavailable")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    source_before = module.qualified_source_cut()
    if source_before.get("gitHead") != target_source_cut:
        raise ValueError("current source differs from observed target")
    tools_before = module.qualified_tool_binaries()
    alloy_before = module.qualified_alloy_runtime_resources(
        tools_before["alloy"]["path"]
    )
    z3_before = module.observed_z3_elf_dependencies(Path(tools_before["z3"]["path"]))
    if z3_before.get("entrypointSha256") != tools_before["z3"]["sha256"]:
        raise ValueError("Z3 loader and executable conflict")
    if (
        module.qualified_source_cut() != source_before
        or module.qualified_tool_binaries() != tools_before
        or module.qualified_alloy_runtime_resources(tools_before["alloy"]["path"])
        != alloy_before
        or module.observed_z3_elf_dependencies(Path(tools_before["z3"]["path"]))
        != z3_before
    ):
        raise ValueError("current inputs changed during read-only observation")
    return {
        "kind": "ordivon.native-formal-tool-input-observation",
        "sourceCut": target_source_cut,
        "tools": {
            "toolBinaries": tools_before,
            "toolResources": alloy_before,
            "z3ObservedElfDependencies": z3_before,
        },
        "scope": "ONE_LOCAL_ENVIRONMENT_PRE_POST_NO_SOLVER",
        "proofReuseAdmissible": False,
    }


def compare_original_formal_tool_inputs(
    *,
    historical_receipt: dict[str, Any] | None,
    current_observation: dict[str, Any],
    target_source_cut: str,
) -> dict[str, Any]:
    """Only compare qualified original observations with finite current subset."""
    target_source_cut = _exact_commit(target_source_cut)
    result = {
        "kind": "ordivon.scoped-formal-tool-input-comparison",
        "targetSourceCut": target_source_cut,
        "standing": "UNKNOWN_TOOL_INPUT_OBSERVATION",
        "changedObservedInputs": [],
        "changedObservedFields": {},
        "proofReuseAdmissible": False,
        "fullReadsetClosed": False,
        "unresolved": [
            "Lean OLEAN, plugins, dlopen and arbitrary dynamic/child-process inputs",
            "Non-hermetic host/time assumptions and model-to-code/consumer refinement",
        ],
    }
    if (
        not isinstance(historical_receipt, dict)
        or historical_receipt.get("artifactProvenance")
        != ARCHIVE_PROVENANCE
        or historical_receipt.get("archiveQualification") != "EXACT_ARTIFACT_ID_SHA256_AND_SIZE"
        or current_observation.get("kind")
        != "ordivon.native-formal-tool-input-observation"
        or current_observation.get("sourceCut") != target_source_cut
        or current_observation.get("scope")
        != "ONE_LOCAL_ENVIRONMENT_PRE_POST_NO_SOLVER"
        or current_observation.get("proofReuseAdmissible") is not False
    ):
        return result
    old = historical_receipt.get("originalObservedToolInputs")
    new = current_observation.get("tools")
    if not isinstance(old, dict) or not isinstance(new, dict):
        return result
    changed: list[str] = []
    changed_fields: dict[str, list[str]] = {}
    for family, members in (
        (
            "toolBinaries",
            {"lean", "z3", "cvc5", "verus", "dafny", "kani", "quint", "alloy"},
        ),
        ("toolResources", {"alloyAppJar", "alloyJvm"}),
    ):
        prev, now = old.get(family), new.get(family)
        if (
            not isinstance(prev, dict)
            or set(prev) != members
            or not isinstance(now, dict)
            or set(now) != members
        ):
            return result
        for name in sorted(members):
            a, b = prev[name], now[name]
            keys = (
                ("path", "sha256", "version")
                if family == "toolBinaries"
                else ("path", "sha256")
            )
            if (
                not isinstance(a, dict)
                or not isinstance(b, dict)
                or not all(
                    isinstance(a.get(k), str)
                    and bool(a[k])
                    and isinstance(b.get(k), str)
                    and bool(b[k])
                    for k in keys
                )
            ):
                return result
            fields_changed = [k for k in keys if a[k] != b[k]]
            if fields_changed:
                item = family + "." + name
                changed.append(item)
                changed_fields[item] = fields_changed
    prev, now = (
        old.get("z3ObservedElfDependencies"),
        new.get("z3ObservedElfDependencies"),
    )
    if not isinstance(prev, dict) or not isinstance(now, dict):
        return result
    fields = ("scope", "entrypointSha256", "interpreterPath", "resolvedLibraries")
    if any(k not in prev or k not in now for k in fields):
        return result
    for key in fields:
        if prev[key] != now[key]:
            item = "z3ObservedElfDependencies." + key
            changed.append(item)
            changed_fields[item] = [key]
    result["standing"] = (
        "MATCHED_SCOPED_TOOL_OBSERVATIONS"
        if not changed
        else "CHANGED_SCOPED_TOOL_OBSERVATIONS"
    )
    result["changedObservedInputs"] = changed
    result["changedObservedFields"] = changed_fields
    result["nextOperation"] = (
        "inspect-changed-selected-tool-input-fields"
        if changed
        else "qualify-unobserved-dynamic-proof-dependencies"
    )
    return result


# This is a pure Claim-to-Evidence *projection*, not a verifier or Job gate.
# Only the known source-input consumer is admitted. Adding new Claim kinds
# requires native evidence, semantics and independent negative controls.
FORMAL_SOURCE_INPUT_CLAIM = "FORMAL_DECLARED_GIT_INPUTS_EQUAL"
FORMAL_PROOF_APPLICABILITY_CLAIM = "FORMAL_PROOF_APPLICABLE_TO_TARGET"
FORMAL_SOURCE_INPUT_CONSUMER = "agent:formal-declared-source-impact"


def _qualified_artifact_attempt(evidence, execution_cut):
    try:
        identity = artifact_identity(evidence.get("githubArtifactName"))
    except ValueError:
        return False
    attempt = evidence.get("originalWorkflowRunAttempt")
    if identity is None or identity[0] != execution_cut or type(attempt) is not int or attempt < 1:
        return False
    if identity[1] is None:
        return attempt == 1 and evidence.get("originQualification") is None
    origin = evidence.get("githubExecutionOrigin")
    producer = evidence.get("originalArtifactProducerJobId")
    return (
        identity[1] == attempt
        and evidence.get("originQualification") == ORIGIN_QUALIFICATION
        and type(producer) is int and producer > 0
        and isinstance(origin, dict) and origin.get("kind") == ORIGIN_KIND
        and origin.get("sourceCut") == execution_cut
        and type(origin.get("runAttempt")) is int and origin["runAttempt"] == attempt
        and type(origin.get("runId")) is int
        and str(origin["runId"]) == evidence.get("originalWorkflowRunId")
        and origin.get("eventHead") == evidence.get("requestedWorkflowHeadSha")
    )


def assess_formal_evidence_claim(
    *,
    claim_kind: str,
    consumer_ref: str,
    target_source_cut: str,
    historical_receipt: dict[str, Any] | None,
    tool_input_comparison: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Decide one typed, bounded Claim from an already inspected official receipt.

    This has no IO. The producer/official-Git/Artifact qualification is
    performed by fetch_original_formal_report; never pass arbitrary
    external JSON and call the result a qualified attestation.
    """
    if claim_kind not in {
        FORMAL_SOURCE_INPUT_CLAIM,
        FORMAL_PROOF_APPLICABILITY_CLAIM,
    }:
        raise ValueError("unknown scoped Claim kind")
    if not isinstance(target_source_cut, str) or not SHA_PATTERN.fullmatch(
        target_source_cut
    ):
        raise ValueError("scoped Claim requires exact target Git SHA")
    claim = {
        "claimKind": claim_kind,
        "consumerRef": consumer_ref,
        "targetSourceCut": target_source_cut,
    }
    assessment: dict[str, Any] = {
        "schemaVersion": 1,
        "kind": "ordivon.typed-claim-evidence-applicability",
        "claim": claim,
        "decision": "UNKNOWN",
        "claimSupported": False,
        "proofReuseAdmissible": False,
        "physicalExecutionAuthorized": False,
        "verificationTaskDispatched": False,
        "evidenceRefs": [],
        "unresolvedObligations": [],
        "nextOperation": "inspect-existing-qualified-evidence",
        "truthBoundary": (
            "Only the original Formal declared Git input equality fact is "
            "decidable here; no mathematical proof, toolchain equivalence, "
            "model-to-implementation refinement, installed currentness or "
            "Runtime Job admission is asserted."
        ),
    }
    if consumer_ref != FORMAL_SOURCE_INPUT_CONSUMER:
        assessment["decision"] = "UNKNOWN_CONSUMER_SCOPE"
        assessment["unresolvedObligations"] = [
            {
                "kind": "QUALIFY_CONSUMER_SCOPE",
                "reason": "No evidence argument connects the requested consumer to the source-input claim",
            }
        ]
        return assessment
    if not isinstance(historical_receipt, dict):
        assessment["decision"] = "UNKNOWN_NO_HISTORICAL_REPORT"
        assessment["unresolvedObligations"] = [
            {
                "kind": "LOCATE_QUALIFIED_PRODUCER_EVIDENCE",
                "reason": "Read the existing official report; do not reexecute the Formal tools",
            }
        ]
        return assessment
    evidence = historical_receipt
    delta = evidence.get("executionInputsVsCandidate")
    if not isinstance(delta, dict):
        assessment["decision"] = "UNKNOWN_NO_SOURCE_COMPARISON"
        assessment["unresolvedObligations"] = [
            {
                "kind": "COMPARE_DECLARED_GIT_INPUTS",
                "reason": "Use the original execution SourceCut, not only PR Head",
            }
        ]
        return assessment
    execution_cut = evidence.get("verifiedExecutionSourceCut")
    relationship = evidence.get("sourceRelationship")
    witness = evidence.get("sourceRelationshipWitness")
    partial_pr_binding = (
        relationship == "PR_SYNTHETIC_MERGE_HEAD_MATCH_BASE_UNATTESTED"
        and isinstance(witness, dict)
        and witness.get("providerBaseAttested") is False
        and isinstance(witness.get("observedBase"), str)
        and SHA_PATTERN.fullmatch(witness["observedBase"]) is not None
        and isinstance(witness.get("observedHead"), str)
        and SHA_PATTERN.fullmatch(witness["observedHead"]) is not None
        and witness["observedHead"] == evidence.get("requestedWorkflowHeadSha")
        and evidence.get("sourceRelationshipObligation") == "RECOVER_ORIGINAL_PROVIDER_PR_BASE_ATTESTATION"
    )
    captured_pr_binding = (
        relationship == "PR_SYNTHETIC_MERGE_CAPTURED_EVENT_BASE_AND_HEAD"
        and isinstance(witness, dict)
        and witness.get("providerBaseAttested") is False
        and witness.get("producerEventCaptured") is True
        and evidence.get("originQualification") == ORIGIN_QUALIFICATION
        and isinstance(evidence.get("githubExecutionOrigin"), dict)
        and evidence["githubExecutionOrigin"].get("event") == "pull_request"
        and witness.get("observedBase") == evidence["githubExecutionOrigin"].get("eventBase")
        and witness.get("observedHead") == evidence["githubExecutionOrigin"].get("eventHead")
        and evidence["githubExecutionOrigin"].get("sourceParents") == [
            witness.get("observedBase"), witness.get("observedHead"),
        ]
    )
    metadata_qualified = (
        evidence.get("standing") == "CONTENT_MATCHES_DECLARED_GIT_SOURCE"
        and evidence.get("artifactProvenance")
        == ARCHIVE_PROVENANCE
        and evidence.get("archiveQualification") == "EXACT_ARTIFACT_ID_SHA256_AND_SIZE"
        and _qualified_artifact_attempt(evidence, execution_cut)
        and isinstance(evidence.get("githubArtifactArchiveDigest"), str)
        and re.fullmatch(r"sha256:[0-9a-f]{64}", evidence["githubArtifactArchiveDigest"]) is not None
        and evidence.get("sourceCut") == execution_cut
        and isinstance(execution_cut, str)
        and SHA_PATTERN.fullmatch(execution_cut) is not None
        and delta.get("executionSourceCut") == execution_cut
        and delta.get("candidateSourceCut") == target_source_cut
        and delta.get("comparisonBasis")
        == "TWO_IMMUTABLE_GIT_SNAPSHOTS_NOT_TEMPORAL_PROOF"
        and delta.get("declaredSourceReadsetComparisonComplete") is True
        and delta.get("proofReuseAdmissible") is False
        and evidence.get("proofReuseAdmissible") is False
        and type(evidence.get("originalCheckRunId")) is int
        and evidence["originalCheckRunId"] > 0
        and type(evidence.get("githubArtifactId")) is int
        and evidence["githubArtifactId"] > 0
        and (
            relationship in ("DIRECT_WORKFLOW_HEAD", "PR_SYNTHETIC_MERGE_BASE_AND_HEAD")
            or partial_pr_binding or captured_pr_binding
        )
        and type(delta.get("priorDeclaredPaths")) is int
        and type(delta.get("candidateDeclaredPaths")) is int
        and delta["priorDeclaredPaths"] > 0
        and delta["candidateDeclaredPaths"] > 0
    )
    if not metadata_qualified:
        assessment["decision"] = "UNKNOWN_UNQUALIFIED_EVIDENCE_BINDING"
        assessment["unresolvedObligations"] = [
            {
                "kind": "QUALIFY_ORIGINAL_EVIDENCE_BINDING",
                "reason": "Historical Check Run, Artifact, SourceCut and compare scope are inconsistent",
            }
        ]
        return assessment
    assessment["evidenceRefs"] = [
        {
            "kind": (
                "GITHUB_ARTIFACT_ARCHIVE_CONTENT_ONLY"
                if partial_pr_binding else "GITHUB_ORIGINAL_FORMAL_ARTIFACT"
            ),
            "checkRunId": evidence["originalCheckRunId"],
            "artifactId": evidence["githubArtifactId"],
            "executionSourceCut": execution_cut,
        }
    ]
    standing = delta.get("standing")
    changed = delta.get("changedDeclaredPaths")
    if (
        not isinstance(changed, list)
        or any(
            not isinstance(path, str) or not path or len(path) > 1024
            for path in changed
        )
        or len(set(changed)) != len(changed)
    ):
        assessment["decision"] = "UNKNOWN_SOURCE_CHANGE_WITNESS"
        assessment["unresolvedObligations"] = [
            {"kind": "QUALIFY_SOURCE_CHANGE_WITNESS"}
        ]
        return assessment
    if standing == "UNCHANGED_DECLARED_SOURCE_INPUTS" and (
        changed or delta["priorDeclaredPaths"] != delta["candidateDeclaredPaths"]
    ):
        assessment["decision"] = "UNKNOWN_CONTRADICTORY_SOURCE_CHANGE_WITNESS"
        assessment["unresolvedObligations"] = [
            {"kind": "RECONCILE_DECLARED_SOURCE_COMPARISON"}
        ]
        return assessment
    if standing == "CHANGED_DECLARED_SOURCE_INPUTS" and not changed:
        assessment["decision"] = "UNKNOWN_CONTRADICTORY_SOURCE_CHANGE_WITNESS"
        assessment["unresolvedObligations"] = [
            {"kind": "RECONCILE_DECLARED_SOURCE_COMPARISON"}
        ]
        return assessment
    if standing not in {
        "UNCHANGED_DECLARED_SOURCE_INPUTS",
        "CHANGED_DECLARED_SOURCE_INPUTS",
    }:
        assessment["decision"] = "UNKNOWN_SOURCE_INPUT_STANDING"
        return assessment
    assessment["declaredSourceInputStanding"] = standing
    assessment["changedDeclaredPaths"] = changed
    if partial_pr_binding:
        assessment["decision"] = "UNKNOWN_ORIGINAL_PR_BASE_ATTESTATION"
        assessment["nextOperation"] = "recover-original-provider-pr-base-attestation"
        assessment["unresolvedObligations"] = [
            {
                "kind": "RECOVER_ORIGINAL_PROVIDER_PR_BASE_ATTESTATION",
                "observedGitParents": witness,
                "reason": "Archive content and Git source comparison are qualified, but original provider Base association is absent",
            }
        ]
        if changed:
            assessment["unresolvedObligations"].append({
                "kind": "INSPECT_CHANGED_FORMAL_DECLARED_INPUTS", "paths": changed,
                "reason": "Independent two-snapshot source change witness; not proof failure",
            })
        return assessment
    if claim_kind == FORMAL_SOURCE_INPUT_CLAIM:
        if standing == "UNCHANGED_DECLARED_SOURCE_INPUTS":
            assessment["decision"] = "SUPPORTED_SCOPED_SOURCE_INPUT_FACT"
            assessment["claimSupported"] = True
            assessment["nextOperation"] = (
                "consume-original-declared-source-input-equality"
            )
        else:
            assessment["decision"] = "CONTRADICTED_SCOPED_SOURCE_INPUT_FACT"
            assessment["unresolvedObligations"] = [
                {
                    "kind": "INSPECT_CHANGED_FORMAL_DECLARED_INPUTS",
                    "paths": changed,
                    "reason": "Input equality is false; this is not necessarily a counterexample to the Formal theorem",
                }
            ]
            assessment["nextOperation"] = "inspect-only-changed-declared-source-inputs"
        return assessment
    # The stronger Claim is deliberately not granted by static Git equality.
    assessment["decision"] = (
        "UNKNOWN_UNCLOSED_PROOF_ASSUMPTIONS"
        if standing == "UNCHANGED_DECLARED_SOURCE_INPUTS"
        else "AFFECTED_PROOF_SOURCE_INPUTS"
    )
    assessment["unresolvedObligations"] = (
        [
            {
                "kind": "INSPECT_CHANGED_FORMAL_DECLARED_INPUTS",
                "paths": changed,
            }
        ]
        if changed
        else []
    ) + [
        {"kind": "QUALIFY_EXECUTION_TOOLCHAIN_AND_DYNAMIC_DEPENDENCIES"},
        {"kind": "QUALIFY_MODEL_IMPLEMENTATION_CONSUMER_REFINEMENT"},
    ]
    # A qualified mismatch is a *new obligation*, never a counterexample to
    # the mathematical theorem or a grant to execute its verifier.
    compared = tool_input_comparison
    if (
        isinstance(compared, dict)
        and compared.get("kind") == "ordivon.scoped-formal-tool-input-comparison"
        and compared.get("targetSourceCut") == target_source_cut
        and compared.get("standing") == "CHANGED_SCOPED_TOOL_OBSERVATIONS"
        and compared.get("proofReuseAdmissible") is False
        and compared.get("fullReadsetClosed") is False
        and isinstance(compared.get("changedObservedFields"), dict)
        and bool(compared["changedObservedFields"])
        and all(
            isinstance(key, str)
            and key
            and isinstance(fields, list)
            and bool(fields)
            and all(isinstance(field, str) and field for field in fields)
            for key, fields in compared["changedObservedFields"].items()
        )
    ):
        assessment["unresolvedObligations"].insert(
            0,
            {
                "kind": "INSPECT_CHANGED_SELECTED_FORMAL_TOOL_INPUTS",
                "changedObservedFields": compared["changedObservedFields"],
            },
        )
        assessment["decision"] = (
            "AFFECTED_PROOF_SOURCE_AND_TOOL_INPUTS"
            if changed
            else "AFFECTED_PROOF_TOOL_INPUTS"
        )
        assessment["nextOperation"] = "inspect-exact-formal-tool-input-differences"
    else:
        assessment["nextOperation"] = "inspect-missing-proof-premises-not-full-replay"
    return assessment


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", default=DEFAULT_REPOSITORY)
    parser.add_argument("--current-sha", required=True)
    parser.add_argument("--prior-sha")
    parser.add_argument("--current-workflow-run-id", type=int,
                        help="explicit native Workflow Run identity for current Check Run")
    parser.add_argument("--prior-workflow-run-id", type=int,
                        help="explicit native Workflow Run identity for prior Check Run/Artifact")
    parser.add_argument("--check-name", default="root-verification")
    parser.add_argument(
        "--formal-source-delta",
        action="store_true",
        help="also inspect the native Formal declared Git source-readset delta",
    )
    parser.add_argument(
        "--historical-formal-report",
        type=Path,
        help="locally downloaded Formal report JSON; source binding only",
    )
    parser.add_argument(
        "--fetch-historical-formal-report",
        action="store_true",
        help="read existing GitHub Check Run and original published Formal report via gh CLI",
    )
    parser.add_argument(
        "--claim-kind",
        choices=(FORMAL_SOURCE_INPUT_CLAIM, FORMAL_PROOF_APPLICABILITY_CLAIM, "BOTH"),
        help="optional typed Claim (or BOTH in one artifact read); only source equality can be supported",
    )
    parser.add_argument(
        "--consumer-ref",
        default=FORMAL_SOURCE_INPUT_CONSUMER,
        help="exact scoped consumer of the typed Claim",
    )
    parser.add_argument(
        "--compare-current-formal-tool-inputs",
        action="store_true",
        help="observe selected tool entrypoints and scoped resources without any solver",
    )
    args = parser.parse_args()
    try:
        result = decide_with_optional_formal_source_delta(
            repo=args.repo,
            current_sha=args.current_sha,
            prior_sha=args.prior_sha,
            check_name=args.check_name,
            include_formal_source_delta=args.formal_source_delta,
            current_workflow_run_id=args.current_workflow_run_id,
            prior_workflow_run_id=args.prior_workflow_run_id,
        )
        if (
            args.historical_formal_report is not None
            or args.fetch_historical_formal_report
        ):
            try:
                if not args.prior_sha or (
                    args.historical_formal_report is not None
                    and args.fetch_historical_formal_report
                ):
                    raise ValueError(
                        "historical Formal receipt needs one source and --prior-sha"
                    )
                if args.fetch_historical_formal_report:
                    report = fetch_original_formal_report(
                        repo=args.repo,
                        source_sha=args.prior_sha,
                        candidate_sha=args.current_sha,
                        workflow_run_id=args.prior_workflow_run_id,
                    )
                else:
                    report = inspect_historical_formal_report_file(
                        repo=Path.cwd(),
                        source_sha=args.prior_sha,
                        path=args.historical_formal_report,
                    )
                result["historicalFormalReceipt"] = report
            except (
                OSError,
                ValueError,
                subprocess.CalledProcessError,
                subprocess.TimeoutExpired,
            ) as exc:
                result["historicalFormalReceipt"] = {
                    "schemaVersion": 1,
                    "kind": "ordivon.historical-formal-receipt-content-binding",
                    "standing": "UNKNOWN_FORMAL_RECEIPT_CONTENT",
                    "proofReuseAdmissible": False,
                    "errorType": type(exc).__name__,
                    "receiptQualification": (
                        exc.reason if isinstance(exc, CheckObservationError)
                        else "UNKNOWN_ARCHIVE_OR_SOURCE_BINDING"
                    ),
                }
        if args.compare_current_formal_tool_inputs:
            try:
                if not args.fetch_historical_formal_report:
                    raise ValueError("original official Formal Artifact required")
                observed = observe_current_formal_tool_inputs(
                    repo=Path.cwd(),
                    target_source_cut=args.current_sha,
                )
                result["formalToolInputComparison"] = (
                    compare_original_formal_tool_inputs(
                        historical_receipt=result.get("historicalFormalReceipt"),
                        current_observation=observed,
                        target_source_cut=args.current_sha,
                    )
                )
            except (
                ValueError,
                OSError,
                subprocess.SubprocessError,
                ImportError,
                KeyError,
                AttributeError,
            ) as exc:
                result["formalToolInputComparison"] = {
                    "kind": "ordivon.scoped-formal-tool-input-comparison",
                    "standing": "UNKNOWN_CURRENT_TOOL_OBSERVATION",
                    "proofReuseAdmissible": False,
                    "fullReadsetClosed": False,
                    "errorType": type(exc).__name__,
                }
        if args.claim_kind == "BOTH":
            # One original GitHub Artifact fetch, two distinct Claim decisions.
            result["claimAssessments"] = [
                assess_formal_evidence_claim(
                    claim_kind=claim_kind,
                    consumer_ref=args.consumer_ref,
                    target_source_cut=args.current_sha,
                    historical_receipt=result.get("historicalFormalReceipt"),
                    tool_input_comparison=result.get("formalToolInputComparison"),
                )
                for claim_kind in (
                    FORMAL_SOURCE_INPUT_CLAIM,
                    FORMAL_PROOF_APPLICABILITY_CLAIM,
                )
            ]
        elif args.claim_kind is not None:
            result["claimAssessment"] = assess_formal_evidence_claim(
                claim_kind=args.claim_kind,
                consumer_ref=args.consumer_ref,
                target_source_cut=args.current_sha,
                historical_receipt=result.get("historicalFormalReceipt"),
                tool_input_comparison=result.get("formalToolInputComparison"),
            )
    except (
        OSError,
        ValueError,
        subprocess.CalledProcessError,
        json.JSONDecodeError,
    ) as exc:
        result = {
            "schemaVersion": 1,
            "kind": "ordivon.source-check-evidence-decision",
            "disposition": "UNKNOWN_PROVIDER_OR_SOURCE",
            "proofReuseAdmissible": False,
            "nextOperation": "inspect-provider-or-source",
            "errorType": type(exc).__name__,
        }
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
