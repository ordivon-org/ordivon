#!/usr/bin/env python3
"""Read-only Agent admission: original GitHub CI receipt + existing source impact.

Does not run a verifier, mutate evidence, or turn SOURCE into installed/physical truth.
For existing archived Harness claims use its independent check_evidence.py contract.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]
REPOSITORY = "ordivon-org/ordivon"
sys.path.insert(0, str(ROOT / "tools/repo"))
import affected_owners  # noqa: E402
import convergence_plan  # noqa: E402

_GIT_SHA = re.compile(r"^[a-f0-9]{40}$")


def _git(*args: str) -> str:
    result = subprocess.run(
        ["git", "--no-replace-objects", *args],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.strip()


def _github(path: str) -> dict[str, Any]:
    result = subprocess.run(
        ["gh", "api", "-X", "GET", f"repos/{REPOSITORY}/{path}"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
        timeout=30,
    )
    data = json.loads(result.stdout)
    if not isinstance(data, dict):
        raise ValueError("GitHub API response is not a JSON object")
    return data


def _source_cut(value: object) -> str:
    if not isinstance(value, str) or _GIT_SHA.fullmatch(value) is None:
        raise ValueError("GitHub source identity is not an exact lowercase Git commit")
    return value


def _official_ci_at_cut(checks: dict[str, Any], source_cut: str) -> tuple[str, list[dict[str, str]]]:
    rows = checks.get("check_runs")
    count = checks.get("total_count")
    if not isinstance(rows, list) or not isinstance(count, int) or count != len(rows):
        # >100 jobs, truncated pages, malformed, or missing evidence -> UNKNOWN.
        return "UNKNOWN_CHECK_SET", []
    seen: set[tuple[str, str]] = set()
    selected: list[dict[str, str]] = []
    for row in rows:
        if not isinstance(row, dict):
            return "UNKNOWN_CHECK_SET", []
        app = row.get("app")
        app_name = app.get("slug") if isinstance(app, dict) else None
        name = row.get("name")
        if (
            app_name not in ("github-actions", "github-advanced-security")
            or not isinstance(name, str)
            or not name
            or row.get("head_sha") != source_cut
        ):
            return "UNKNOWN_CHECK_SET", []
        identity = (app_name, name)
        if identity in seen:
            # Re-run or overlapping workflow: do not cherry-pick an old PASS.
            return "AMBIGUOUS_CHECK_RUNS", []
        seen.add(identity)
        selected.append(
            {
                "name": name,
                "app": app_name,
                "status": str(row.get("status", "")),
                "conclusion": str(row.get("conclusion", "")),
                "url": str(row.get("details_url", "")),
            }
        )
    root = [r for r in selected if r["app"] == "github-actions" and r["name"] == "root-verification"]
    if len(root) != 1:
        return "NO_ROOT_VERIFICATION_RECEIPT", selected
    if any(r["status"] != "completed" or r["conclusion"] != "success" for r in selected):
        return "INCOMPLETE_OR_FAILED_CHECKS", selected
    return "EXACT_CUT_SOURCE_CI_PASS", selected


def _native_root_workflow_matches(root_check: dict[str, str], source_cut: str) -> bool:
    """Qualify GH's actual required CI job/run, not any check with same name."""
    match = re.fullmatch(
        r"https://github[.]com/ordivon-org/ordivon/actions/runs/([0-9]+)/job/([0-9]+)",
        root_check.get("url", ""),
    )
    if match is None:
        return False
    run_id, job_id = map(int, match.groups())
    job = _github(f"actions/jobs/{job_id}")
    run = _github(f"actions/runs/{run_id}")
    return (
        job.get("id") == job_id
        and job.get("run_id") == run_id
        and job.get("name") == "root-verification"
        and job.get("workflow_name") == "Monorepo Required"
        and job.get("head_sha") == source_cut
        and job.get("status") == "completed"
        and job.get("conclusion") == "success"
        and run.get("id") == run_id
        and run.get("name") == "Monorepo Required"
        and run.get("path") == ".github/workflows/ci.yml"
        and run.get("head_sha") == source_cut
        and run.get("status") == "completed"
        and run.get("conclusion") == "success"
    )


def _native_harness_claim(claim_id: str, target_cut: str) -> dict[str, Any]:
    """Compose the ORIGINAL Harness query; no copied currentness rules."""
    native_cut = _source_cut(_git("rev-parse", "HEAD"))
    if target_cut != native_cut:
        return {
            "claimId": claim_id,
            "standing": "NOT_EVALUATED_DIFFERENT_CHECKOUT_SOURCE_CUT",
            "sourceCut": native_cut,
            "evidenceCurrent": False,
        }
    script = ROOT / "services/harness/scripts/check_evidence.py"
    result = subprocess.run(
        [sys.executable, str(script), "--query-claim", claim_id],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
        timeout=50,
    )
    try:
        typed = json.loads(result.stdout)
    except json.JSONDecodeError:
        return {"claimId": claim_id, "standing": "UNKNOWN_NATIVE_CHECKER_RESPONSE", "evidenceCurrent": False}
    if (
        not isinstance(typed, dict)
        or typed.get("claimId") != claim_id
        or typed.get("sourceCut") != target_cut
        or typed.get("evidenceCurrent") not in (True, False)
        or (result.returncode != 0 and typed.get("evidenceCurrent") is True)
    ):
        return {"claimId": claim_id, "standing": "UNKNOWN_NATIVE_CHECKER_RESPONSE", "evidenceCurrent": False}
    return typed


def assess(*, pr: int, owner: str, target: str = "HEAD", harness_claim: str | None = None) -> dict[str, Any]:
    owner_names = {item.name for item in affected_owners.OWNERS}
    if owner not in owner_names:
        raise ValueError("unknown natural verification Owner")
    if pr < 1:
        raise ValueError("PR must be a positive integer")
    pull = _github(f"pulls/{pr}")
    head = pull.get("head")
    base = pull.get("base")
    if not isinstance(head, dict) or not isinstance(base, dict):
        raise ValueError("missing official PR head/base")
    proof_cut = _source_cut(head.get("sha"))
    base_cut = _source_cut(base.get("sha"))
    if head.get("repo", {}).get("full_name") != REPOSITORY or base.get("repo", {}).get("full_name") != REPOSITORY:
        raise ValueError("source PR is not from the exact expected GitHub repository")
    if target != "HEAD" and _GIT_SHA.fullmatch(target) is None:
        raise ValueError("target revision must be HEAD or an exact Git commit")
    target_cut = _source_cut(_git("rev-parse", f"{target}^{{commit}}"))
    for cut in (proof_cut, base_cut):
        if _git("cat-file", "-t", cut) != "commit":
            raise ValueError("original PR Git revision not available in local immutable source")
    checks = _github(f"commits/{proof_cut}/check-runs?per_page=100")
    receipt, jobs = _official_ci_at_cut(checks, proof_cut)
    root_check = next(
        (x for x in jobs if x["name"] == "root-verification" and x["app"] == "github-actions"),
        None,
    )
    if receipt == "EXACT_CUT_SOURCE_CI_PASS" and (
        root_check is None or not _native_root_workflow_matches(root_check, proof_cut)
    ):
        receipt = "UNKNOWN_ROOT_WORKFLOW_IDENTITY"

    # This is an existing canonical OWNER consumer selection projection,
    # not an authenticated record of every CI child Job's executed task list.
    original = convergence_plan.build_plan(base=base_cut, head=proof_cut)
    selection = owner in original["verificationOwners"]
    changed: list[str] = []
    new_owner_affected: bool | None = None
    source = "UNRELATED_OR_UNQUALIFIED_SOURCE_CUT"
    if target_cut == proof_cut:
        source = "EXACT_GIT_CUT"
        new_owner_affected = False
    else:
        ancestor = subprocess.run(
            ["git", "--no-replace-objects", "merge-base", "--is-ancestor", proof_cut, target_cut],
            cwd=ROOT,
            capture_output=True,
            check=False,
        )
        if ancestor.returncode == 0:
            changed = list(affected_owners.changed_paths(proof_cut, target_cut))
            if changed:
                impact = convergence_plan.build_plan(base=proof_cut, head=target_cut)
                new_owner_affected = owner in impact["verificationOwners"]
                source = "ANCESTOR_SOURCE_OWNER_IMPACT_PROJECTION"
            else:
                new_owner_affected = False
                source = "UNCHANGED_GIT_CONTENT_AT_DESCENDANT"
    if receipt != "EXACT_CUT_SOURCE_CI_PASS":
        decision = "RECEIPT_UNKNOWN_OR_NOT_PASSED"
        action = "INSPECT_ORIGINAL_CI_RECEIPT_BEFORE_RUNNING_TESTS"
    elif target_cut == proof_cut:
        decision = "EXACT_CUT_CI_OBSERVED"
        action = "REUSE_OFFICIAL_SOURCE_CI_RESULT_AT_THIS_CUT_NO_DUPLICATE_RUN"
    elif new_owner_affected is False:
        decision = "SCOPED_SOURCE_NO_OWNER_RECHECK"
        action = "REUSE_HISTORICAL_SOURCE_OBSERVATION_CHECK_OTHER_PREMISES"
    elif new_owner_affected is True:
        decision = "CHANGED_CONSUMER_INPUT"
        action = "CHECK_FOR_NEW_TARGET_RECEIPT_ELSE_RUN_SELECTED_NATIVE_OWNER_TASK"
    else:
        decision = "UNKNOWN_SOURCE_RELATION"
        action = "QUALIFY_MISSING_SOURCE_RELATION_NOT_BLANKET_REPLAY"
    return {
        "schemaVersion": 1,
        "kind": "ordivon.runtime-agent-evidence-admission",
        "consumerOwner": owner,
        "originalPr": pr,
        "originalBaseCut": base_cut,
        "originalProofCut": proof_cut,
        "targetSourceCut": target_cut,
        "originalReceipt": receipt,
        "officialCheckCount": len(jobs),
        "originalRootCheck": root_check,
        "originalOwnerInCurrentSelectorProjection": selection,
        "sourceRelation": source,
        "newOwnerAffected": new_owner_affected,
        "changedTrackedGitPaths": changed,
        "decision": decision,
        "recommendedAction": action,
        "proofReuseAdmissible": False,
        "installedStanding": "UNKNOWN",
        "runtimeCallStanding": "UNKNOWN",
        "harnessClaim": (_native_harness_claim(harness_claim, target_cut) if harness_claim is not None else None),
        "harnessArchivedEvidenceStanding": (
            "NATIVE_CHECKER_COMPOSED_SEPARATE_TRUTH"
            if harness_claim is not None
            else "NOT_ASSESSED_BY_THIS_SOURCE_CI_RECEIPT"
        ),
        "truthBoundary": (
            "GitHub read-only exact-head CI check-run observation and canonical current "
            "source Owner impact ONLY. It cannot certify historical Harness evidence, "
            "closed dynamic readsets, model-to-code refinement, production installation "
            "or Agent physical execution. No verifier was invoked."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pr", type=int, required=True)
    parser.add_argument("--owner", required=True)
    parser.add_argument("--target", default="HEAD", help="exact local target revision (default HEAD)")
    parser.add_argument("--harness-claim", help="also ask the existing Harness evidence checker (read-only)")
    args = parser.parse_args()
    try:
        report = assess(pr=args.pr, owner=args.owner, target=args.target, harness_claim=args.harness_claim)
    except (ValueError, OSError, json.JSONDecodeError, subprocess.SubprocessError) as exc:
        print(
            json.dumps(
                {
                    "schemaVersion": 1,
                    "kind": "ordivon.runtime-agent-evidence-admission",
                    "decision": "UNKNOWN_EVIDENCE_UNAVAILABLE",
                    "error": str(exc),
                    "proofReuseAdmissible": False,
                },
                sort_keys=True,
            )
        )
        return 2
    print(json.dumps(report, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
