#!/usr/bin/env python3
"""Read-only Agent decision on existing GitHub checks and native source impact.

This is NOT a verifier, evidence database, execution admission/PDP, or a
cross-SourceCut proof-reuse engine. A successful Check Run is only evidence
that that named check finished successfully at its exact Git commit.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

import convergence_plan
from ci_telemetry import Gh
from source_history_legos import require_ancestral_source_cuts

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
    if prior_sha and prior_sha != current_sha and _standing(current) != "PASS":
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


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", default=DEFAULT_REPOSITORY)
    parser.add_argument("--current-sha", required=True)
    parser.add_argument("--prior-sha")
    parser.add_argument("--check-name", default="root-verification")
    args = parser.parse_args()
    try:
        result = decide(
            repo=args.repo,
            current_sha=args.current_sha,
            prior_sha=args.prior_sha,
            check_name=args.check_name,
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
