"""Pure decision over observed Check Run outcomes and source impact.

A named provider outcome is not current security, installation, or proof
applicability. No effects or provider requests are issued here.
"""

from __future__ import annotations

from typing import Any


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
        "currentApplicability": "UNKNOWN_EXTERNAL_ASSUMPTIONS",
        "currentSecurityStanding": "NOT_ASSESSED_BY_CHECK_RECEIPT",
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
