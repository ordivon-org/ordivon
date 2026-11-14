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
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

import convergence_plan
from ci_telemetry import Gh
from source_history_legos import current_tree, require_ancestral_source_cuts
from source_history_legos import git as git_native

DEFAULT_REPOSITORY = "ordivon-org/ordivon"
REPO_PATTERN = re.compile(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+")
SHA_PATTERN = re.compile(r"(?:[0-9a-f]{40}|[0-9a-f]{64})")
MAX_CHECK_ROWS = 2000


def _exact_commit(sha: str) -> str:
    if not isinstance(sha, str) or not SHA_PATTERN.fullmatch(sha):
        raise ValueError("evidence SourceCut requires a literal full Git commit SHA")
    actual = convergence_plan._git("rev-parse", f"{sha}^{{commit}}")
    if actual != sha:
        raise ValueError("evidence SourceCut does not match native Git commit")
    return sha


def _provider_checks(gh: Gh, repo: str, sha: str) -> list[dict[str, Any]]:
    """Read all pages: a truncated or malformed listing grants no PASS."""
    rows: list[dict[str, Any]] = []
    page = 1
    while True:
        payload = gh.api(
            f"repos/{repo}/commits/{sha}/check-runs?per_page=100&page={page}"
        )
        if (
            not isinstance(payload, dict)
            or type(payload.get("total_count")) is not int
            or not isinstance(payload.get("check_runs"), list)
        ):
            raise ValueError("GitHub Check Runs provider response is incomplete")
        count = payload["total_count"]
        batch = payload["check_runs"]
        if count < 0 or count > MAX_CHECK_ROWS or len(batch) > 100:
            raise ValueError("GitHub Check Runs exceed bounded complete query")
        if not all(isinstance(row, dict) for row in batch):
            raise ValueError("malformed provider Check Run")
        rows.extend(batch)
        identifiers = [row.get("id") for row in rows]
        if any(
            type(identifier) is not int or identifier <= 0 for identifier in identifiers
        ) or len(set(identifiers)) != len(identifiers):
            raise ValueError(
                "GitHub provider Check Run IDs are incomplete or duplicate"
            )
        if len(rows) == count:
            return rows
        if len(rows) > count or not batch or page >= 20:
            raise ValueError("GitHub Check Runs listing is truncated or inconsistent")
        page += 1


def _select_check(
    rows: list[dict[str, Any]], *, sha: str, check_name: str
) -> dict[str, Any] | None:
    selected: list[dict[str, Any]] = []
    for row in rows:
        if row.get("name") != check_name:
            continue
        app = row.get("app")
        if not isinstance(app, dict) or app.get("slug") != "github-actions":
            continue
        if (
            row.get("head_sha") != sha
            or type(row.get("id")) is not int
            or row["id"] <= 0
            or row.get("status")
            not in {
                "queued",
                "in_progress",
                "completed",
                "pending",
                "requested",
                "waiting",
            }
        ):
            raise ValueError("GitHub Check Run contradicts its exact identity")
        selected.append(row)
    if not selected:
        return None
    # A rerun creates a later Check Run. Never use an older success when a
    # newer attempt is pending or has failed. Duplicate IDs are ambiguous.
    if len({row["id"] for row in selected}) != len(selected):
        raise ValueError("duplicate provider Check Run IDs")
    last = max(selected, key=lambda row: row["id"])
    if last["status"] == "completed" and last.get("conclusion") == "success":
        # A trusted check receipt needs temporal and URL provenance as well
        # as the provider's status; absent/malformed metadata is UNKNOWN.
        when = last.get("completed_at")
        url = last.get("details_url")
        if not isinstance(when, str) or not isinstance(url, str):
            raise ValueError("successful Check Run lacks temporal or URL provenance")
        try:
            instant = datetime.fromisoformat(when)
        except ValueError as exc:
            raise ValueError(
                "successful Check Run has invalid completion time"
            ) from exc
        parsed = urlsplit(url)
        if (
            instant.tzinfo is None
            or parsed.scheme != "https"
            or parsed.hostname != "github.com"
            or not parsed.path.startswith("/ordivon-org/ordivon/actions/")
        ):
            raise ValueError("successful Check Run has unqualified provenance")
    return {
        "checkRunId": last["id"],
        "checkName": check_name,
        "headSha": sha,
        "app": "github-actions",
        "status": last["status"],
        "conclusion": last.get("conclusion"),
        "completedAt": last.get("completed_at"),
        "detailsUrl": last.get("details_url"),
    }


def _standing(check: dict[str, Any] | None) -> str:
    if check is None:
        return "ABSENT"
    if check["status"] != "completed":
        return "IN_PROGRESS"
    return "PASS" if check["conclusion"] == "success" else "NOT_PASS"


def _decision(
    *,
    current_sha: str,
    prior_sha: str | None,
    check_name: str,
    current_check: dict[str, Any] | None,
    prior_check: dict[str, Any] | None,
    source_impact: dict[str, Any] | None,
) -> dict[str, Any]:
    now = _standing(current_check)
    previous = _standing(prior_check)
    selection = None
    if now == "PASS":
        disposition, next_op = "REUSE_CURRENT_RECEIPT", "consume-existing-check"
    elif now == "IN_PROGRESS":
        disposition, next_op = "OBSERVE_EXISTING_RUN", "inspect-existing-check"
    elif now == "NOT_PASS":
        disposition, next_op = "INVESTIGATE_EXISTING_RESULT", "inspect-existing-check"
    elif previous != "PASS":
        disposition, next_op = "UNKNOWN_NO_ACCEPTED_EVIDENCE", "find-real-evidence"
    elif source_impact is None:
        disposition, next_op = "UNKNOWN_SOURCE_RELATION", "inspect-source-lineage"
    else:
        # This is only native CI source selection; the proof's dynamic
        # readset and relevant environment are NOT established.
        selection = {
            "changedPaths": source_impact["changedPaths"],
            "verificationOwners": source_impact["verificationOwners"],
            "queueVerifyTasks": source_impact["queueVerifyTasks"],
        }
        if selection["queueVerifyTasks"]:
            disposition, next_op = (
                "SOURCE_AFFECTED",
                "inspect-affected-proof-obligations",
            )
        else:
            disposition, next_op = "UNKNOWN_CROSS_CUT_READSET", "inspect-proof-readset"
    return {
        "schemaVersion": 1,
        "kind": "ordivon.source-check-evidence-decision",
        "claim": {"kind": "GITHUB_ACTIONS_CHECK_RESULT", "name": check_name},
        "currentSourceCut": current_sha,
        "priorSourceCut": prior_sha,
        "disposition": disposition,
        "nextOperation": next_op,
        "currentEvidence": current_check,
        "priorEvidence": prior_check,
        "sourceImpact": selection,
        # A CI result can be reused as a check receipt, NOT as proof of
        # cross-SourceCut refinement or external consumer acceptance.
        "proofReuseAdmissible": False,
        "existingCheckReceiptReusable": disposition == "REUSE_CURRENT_RECEIPT",
        "reuseScope": (
            "EXACT_COMMIT_NAMED_PROVIDER_CHECK_OUTCOME"
            if disposition == "REUSE_CURRENT_RECEIPT"
            else None
        ),
        "nonClaims": [
            "A GitHub Check Run success is not deployed Owner or domain acceptance.",
            "The source/Owner change selector does not prove a closed proof or dynamic consumer readset.",
            "Never reuse a historical PASS at a different Git SHA as a current PASS without independent closure.",
        ],
    }


def decide(
    *,
    repo: str,
    current_sha: str,
    prior_sha: str | None = None,
    check_name: str = "root-verification",
    github: Gh | None = None,
) -> dict[str, Any]:
    if not REPO_PATTERN.fullmatch(repo) or repo != DEFAULT_REPOSITORY:
        raise ValueError("GitHub repository must be the canonical Ordivon owner/name")
    if not check_name or len(check_name) > 128:
        raise ValueError("Check Run name must be nonempty and bounded")
    current_sha = _exact_commit(current_sha)
    if prior_sha is not None:
        prior_sha = _exact_commit(prior_sha)
    gh = github or Gh(repo)
    current = _select_check(
        _provider_checks(gh, repo, current_sha),
        sha=current_sha,
        check_name=check_name,
    )
    past = None
    # A current pending/failed result already determines this Check Run's
    # standing. Do not query an older provider result that could error and
    # falsely obscure a real current failure or in-flight Job.
    if prior_sha and prior_sha != current_sha and _standing(current) == "ABSENT":
        past = _select_check(
            _provider_checks(gh, repo, prior_sha),
            sha=prior_sha,
            check_name=check_name,
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
            require_ancestral_source_cuts(Path.cwd(), prior_sha, current_sha)
            impact = convergence_plan.build_plan(base=prior_sha, head=current_sha)
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
    prior_sha = _exact_commit(prior_sha)
    current_sha = _exact_commit(current_sha)
    require_ancestral_source_cuts(repo, prior_sha, current_sha)
    old = _formal_declared_files(repo, prior_sha)
    new = _formal_declared_files(repo, current_sha)
    prior_tree = current_tree(repo, prior_sha)
    current = current_tree(repo, current_sha)
    all_paths = sorted(set(old) | set(new))
    if any(
        not prior_tree.get(path, "").startswith(("100644:blob:", "100755:blob:"))
        for path in old
    ) or any(
        not current.get(path, "").startswith(("100644:blob:", "100755:blob:"))
        for path in new
    ):
        raise ValueError("formal declared readset has missing/non-regular Git members")
    changed = [path for path in all_paths if prior_tree.get(path) != current.get(path)]
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
    source_sha = _exact_commit(source_sha)
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
            for probe in probes
        )
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
        "proofReuseAdmissible": False,
    }


def inspect_historical_formal_report_file(
    *, repo: Path, source_sha: str, path: Path
) -> dict[str, Any]:
    """Read bounded JSON downloaded from the official existing GitHub run."""
    if path.is_symlink() or not path.is_file() or path.stat().st_size > 1048576:
        raise ValueError("historical Formal report must be bounded regular file")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (ValueError, UnicodeError) as exc:
        raise ValueError("historical Formal report must contain valid JSON") from exc
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
    execution_sha = _exact_commit(execution_sha)
    candidate_sha = _exact_commit(candidate_sha)
    original = _formal_declared_files(repo, execution_sha)
    current = _formal_declared_files(repo, candidate_sha)
    old_tree = current_tree(repo, execution_sha)
    new_tree = current_tree(repo, candidate_sha)
    if any(
        not old_tree.get(path, "").startswith(("100644:blob:", "100755:blob:"))
        for path in original
    ) or any(
        not new_tree.get(path, "").startswith(("100644:blob:", "100755:blob:"))
        for path in current
    ):
        raise ValueError("Formal source comparison contains unqualified Git member")
    old_set = set(original)
    new_set = set(current)
    changed = [
        path
        for path in sorted(old_set | new_set)
        if (old_tree[path] if path in old_set else None)
        != (new_tree[path] if path in new_set else None)
    ]
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
) -> tuple[dict[str, Any], str, str]:
    """Select one actual Formal Artifact, not an artifact guessed from PR head.

    GitHub's pull_request workflow Check Run is tied to PR Head while
    github.sha/checked-out Formal SourceCut is a synthetic merge commit.
    Reconstruct the exact two-parent Git relationship before accepting
    the merge SourceCut as a historical execution context.
    """
    prefix = "ordivon-core-formal-"
    rows: list[dict[str, Any]] = []
    page = 1
    while True:
        payload = gh.api(
            f"repos/{repo}/actions/runs/{run_id}/artifacts?per_page=100&page={page}"
        )
        if (
            not isinstance(payload, dict)
            or type(payload.get("total_count")) is not int
            or not isinstance(payload.get("artifacts"), list)
        ):
            raise ValueError("historical Formal Artifact index unavailable")
        count = payload["total_count"]
        batch = payload["artifacts"]
        if (
            not (0 <= count <= 2000)
            or len(batch) > 100
            or any(not isinstance(row, dict) for row in batch)
        ):
            raise ValueError("historical Formal Artifact listing is invalid")
        rows.extend(batch)
        if len(rows) == count:
            break
        if len(rows) > count or not batch or page >= 20:
            raise ValueError("historical Formal Artifact listing is incomplete")
        page += 1
    identifiers = [row.get("id") for row in rows]
    if any(type(item) is not int or item <= 0 for item in identifiers) or (
        len(set(identifiers)) != len(identifiers)
    ):
        raise ValueError("historical Formal Artifact listing duplicates identities")
    matching = [
        row
        for row in rows
        if isinstance(row.get("name"), str) and row["name"].startswith(prefix)
    ]
    if len(matching) != 1:
        raise ValueError("historical Formal Artifact must have one exact producer")
    artifact = matching[0]
    actual_sha = artifact["name"][len(prefix) :]
    _exact_commit(actual_sha)
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
    if actual_sha == head_sha:
        relation = "DIRECT_WORKFLOW_HEAD"
    else:
        if run.get("event") != "pull_request":
            raise ValueError("non-PR workflow Artifact source differs from Head")
        prs = run.get("pull_requests")
        if not isinstance(prs, list) or len(prs) != 1 or not isinstance(prs[0], dict):
            raise ValueError("PR workflow lacks unique exact provenance")
        pr = prs[0]
        if (
            type(pr.get("number")) is not int
            or pr["number"] <= 0
            or not isinstance(pr.get("head"), dict)
            or not isinstance(pr.get("base"), dict)
            or pr["head"].get("sha") != head_sha
        ):
            raise ValueError("PR workflow Head SourceCut does not match provider")
        # Read the original Git commit object with native replace/graft guards.
        lineage = (
            git_native(
                git_repo,
                "--no-replace-objects",
                "rev-list",
                "--parents",
                "-n",
                "1",
                actual_sha,
            )
            .strip()
            .split()
        )
        if (
            len(lineage) != 3
            or lineage[0] != actual_sha
            or lineage[1] != pr["base"].get("sha")
            or lineage[2] != head_sha
        ):
            raise ValueError("PR synthetic merge parents mismatch original Run")
        relation = "PR_SYNTHETIC_MERGE_BASE_AND_HEAD"
    return artifact, actual_sha, relation


def fetch_original_formal_report(
    *,
    repo: str,
    source_sha: str,
    github: Gh | None = None,
    candidate_sha: str | None = None,
) -> dict[str, Any]:
    """Use original GitHub Check Run and official gh run download (read-only).

    There is no generic proof permission, no new Artifact REST downloader
    and no verification dispatch. Source-blobs are checked after download.
    """
    source_sha = _exact_commit(source_sha)
    if repo != DEFAULT_REPOSITORY:
        raise ValueError("historical Formal report requires canonical repository")
    gh = github or Gh(repo)
    check = _select_check(
        _provider_checks(gh, repo, source_sha),
        sha=source_sha,
        check_name="root-verification",
    )
    if _standing(check) != "PASS":
        raise ValueError("historical Formal report requires prior successful check")
    path = urlsplit(check["detailsUrl"]).path
    match = re.fullmatch(
        r"/ordivon-org/ordivon/actions/runs/([1-9][0-9]*)/job/[1-9][0-9]*",
        path,
    )
    if match is None:
        raise ValueError("historical Formal report run identity missing")
    run_id = match.group(1)
    # A Check Run's details URL must actually target this immutable Git
    # SourceCut's workflow run, not merely a plausible GitHub URL.
    run = gh.api(f"repos/{repo}/actions/runs/{run_id}")
    if (
        not isinstance(run, dict)
        or run.get("id") != int(run_id)
        or run.get("head_sha") != source_sha
        or not isinstance(run.get("repository"), dict)
        or run["repository"].get("full_name") != repo
    ):
        raise ValueError("historical Formal workflow run SourceCut mismatch")
    artifact, execution_sha, source_relation = _workflow_formal_artifact(
        gh=gh,
        repo=repo,
        run_id=run_id,
        head_sha=source_sha,
        run=run,
        git_repo=Path.cwd(),
    )
    name = artifact["name"]
    with tempfile.TemporaryDirectory(prefix="ordivon-formal-evidence-") as directory:
        subprocess.run(
            [
                "gh",
                "run",
                "download",
                run_id,
                "--repo",
                repo,
                "--name",
                name,
                "--dir",
                directory,
            ],
            capture_output=True,
            check=True,
            timeout=75,
        )
        result = inspect_historical_formal_report_file(
            repo=Path.cwd(),
            source_sha=execution_sha,
            path=Path(directory) / "ordivon-core-formal-report.json",
        )
    result["originalCheckRunId"] = check["checkRunId"]
    result["originalWorkflowRunId"] = run_id
    result["githubArtifactName"] = name
    result["githubArtifactId"] = artifact["id"]
    result["githubArtifactArchiveDigest"] = artifact["digest"]
    result["requestedWorkflowHeadSha"] = source_sha
    result["verifiedExecutionSourceCut"] = execution_sha
    result["sourceRelationship"] = source_relation
    result["artifactProvenance"] = "GITHUB_RUN_DOWNLOAD_NOT_PROOF_EQUIVALENCE"
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
) -> dict[str, Any]:
    """GitHub provider uncertainty does not erase immutable Git source evidence.

    A candidate SourceCut may exist locally before being pushed to GitHub.
    That yields no current provider Check Run, but original Formal Artifact
    and two original Git snapshots remain independently inspectable.
    """
    current_sha = _exact_commit(current_sha)
    if prior_sha is not None:
        prior_sha = _exact_commit(prior_sha)
    if repo != DEFAULT_REPOSITORY or not check_name or len(check_name) > 128:
        raise ValueError("unqualified repository or Check Run name")
    try:
        decision = decide(
            repo=repo,
            current_sha=current_sha,
            prior_sha=prior_sha,
            check_name=check_name,
            github=github,
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
            "nextOperation": "inspect-current-provider-when-published",
            "existingCheckReceiptReusable": False,
            "proofReuseAdmissible": False,
            "errorType": type(exc).__name__,
            "nonClaims": [
                "Missing current GitHub Check Run is not an execution failure",
                "Immutable local Git and prior Artifact evidence are independent",
            ],
        }
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


# This is a pure Claim-to-Evidence *projection*, not a verifier or Job gate.
# Only the known source-input consumer is admitted. Adding new Claim kinds
# requires native evidence, semantics and independent negative controls.
FORMAL_SOURCE_INPUT_CLAIM = "FORMAL_DECLARED_GIT_INPUTS_EQUAL"
FORMAL_PROOF_APPLICABILITY_CLAIM = "FORMAL_PROOF_APPLICABLE_TO_TARGET"
FORMAL_SOURCE_INPUT_CONSUMER = "agent:formal-declared-source-impact"


def assess_formal_evidence_claim(
    *,
    claim_kind: str,
    consumer_ref: str,
    target_source_cut: str,
    historical_receipt: dict[str, Any] | None,
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
    metadata_qualified = (
        evidence.get("standing") == "CONTENT_MATCHES_DECLARED_GIT_SOURCE"
        and evidence.get("artifactProvenance")
        == "GITHUB_RUN_DOWNLOAD_NOT_PROOF_EQUIVALENCE"
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
        and evidence.get("githubArtifactName") == "ordivon-core-formal-" + execution_cut
        and isinstance(evidence.get("sourceRelationship"), str)
        and evidence["sourceRelationship"]
        in {
            "DIRECT_WORKFLOW_HEAD",
            "PR_SYNTHETIC_MERGE_BASE_AND_HEAD",
        }
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
            "kind": "GITHUB_ORIGINAL_FORMAL_ARTIFACT",
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
    assessment["nextOperation"] = "inspect-missing-proof-premises-not-full-replay"
    return assessment


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", default=DEFAULT_REPOSITORY)
    parser.add_argument("--current-sha", required=True)
    parser.add_argument("--prior-sha")
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
    args = parser.parse_args()
    try:
        result = decide_with_optional_formal_source_delta(
            repo=args.repo,
            current_sha=args.current_sha,
            prior_sha=args.prior_sha,
            check_name=args.check_name,
            include_formal_source_delta=args.formal_source_delta,
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
                }
        if args.claim_kind == "BOTH":
            # One original GitHub Artifact fetch, two distinct Claim decisions.
            result["claimAssessments"] = [
                assess_formal_evidence_claim(
                    claim_kind=claim_kind,
                    consumer_ref=args.consumer_ref,
                    target_source_cut=args.current_sha,
                    historical_receipt=result.get("historicalFormalReceipt"),
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
