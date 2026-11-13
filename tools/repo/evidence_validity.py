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
    code = git_native(repo, "show", f"{sha}:tools/formal/verify.py")
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


def fetch_original_formal_report(
    *,
    repo: str,
    source_sha: str,
    github: Gh | None = None,
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
    name = "ordivon-core-formal-" + source_sha
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
            source_sha=source_sha,
            path=Path(directory) / "ordivon-core-formal-report.json",
        )
    result["originalCheckRunId"] = check["checkRunId"]
    result["originalWorkflowRunId"] = run_id
    result["githubArtifactName"] = name
    result["artifactProvenance"] = "GITHUB_RUN_DOWNLOAD_NOT_PROOF_EQUIVALENCE"
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
    """A missing Formal readset cannot erase a qualified GitHub check fact."""
    decision = decide(
        repo=repo,
        current_sha=current_sha,
        prior_sha=prior_sha,
        check_name=check_name,
        github=github,
    )
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
