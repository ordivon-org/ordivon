#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

META = Path(__file__).resolve().parents[2]
PLAN = META / "research/pressure-tests/claim-permission-maturity-gate-r1.json"
RECEIPT = META / "research/evidence/claim-permission-maturity-pressure-r1.json"
PAPER2_PROFILE = META / "research/profiles/paper2-live-r1.json"
PAPER1_REPO = Path("/root/projects/ordivon-research-v2")
PAPER2_REPO = Path("/root/projects/ordivon-paper2")
PAPER1_PERMISSION = PAPER1_REPO / (
    "papers/first_paper_r2_finite_family/publication_r3_descoped/"
    "reviewer_risk_r25/PAPER1_R25_CLAIM_PERMISSION_R1.json"
)
PAPER2_FILES = {
    "protocolBundle": (
        "campaigns/PAPER2_CORPUS_PROTOCOL_BUNDLE_R13.json",
        "sha256:f64ffb0c59de01db2dde4cab965d39945913fa29c25024ef27ed5412e8e59808",
    ),
    "statisticalPlan": (
        "campaigns/PAPER2_STATISTICAL_ANALYSIS_PLAN_R1.json",
        "sha256:3348acf90b0289360c7ed44bb4160b5aedfa95333d32f8e485986b5d7744ef02",
    ),
    "titleAbstractContract": (
        "campaigns/PAPER2_TITLE_ABSTRACT_SCREENING_CONTRACT_R55_R1.json",
        "sha256:3f2f2aaf98c64458544e5f636ad3fbd07d0fb774fb262d92c25965e1d1c98461",
    ),
    "dualCoderAssignment": (
        "campaigns/PAPER2_DUAL_CODER_ASSIGNMENT_MANIFEST_R57_R1.json",
        "sha256:b13f64ba0c8277ee5f98aa50841b6f1c1641992bf5dd08a6870bf1bd9303e208",
    ),
    "adjudicationCandidate": (
        "campaigns/paper2-r80/PAPER2_TA_ADJUDICATION_MANIFEST_R80_R1.json",
        "sha256:a0ed32dd25558085c8eb05e21746a0d4231047bcdbc14574625aa548e547adde",
    ),
    "postCoderPipeline": (
        "campaigns/PAPER2_TA_POST_CODER_PIPELINE_R58_R1.json",
        "sha256:65d661e4179270781cad772ff7f76bce7a2bce32f534a556fa3dd7647f64380a",
    ),
    "fulltextReadiness": (
        "screening/fulltext/FULLTEXT_ELIGIBILITY_READINESS_R1.json",
        "sha256:c705e7a7ff43401fb588bae2d9198203c35f5e180b7f67d9a11aecd55cefb709",
    ),
}


def fail(message: str) -> None:
    raise SystemExit(message)


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        fail(f"expected JSON object: {path}")
    return value


def sha256(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def git_head(repo: Path) -> str:
    cp = subprocess.run(
        ["git", "-C", str(repo), "rev-parse", "HEAD"], capture_output=True, text=True
    )
    if cp.returncode:
        fail(f"cannot resolve HEAD: {repo}: {cp.stderr}")
    return cp.stdout.strip()


def git_clean(repo: Path) -> bool:
    cp = subprocess.run(
        ["git", "-C", str(repo), "status", "--porcelain=v1"],
        capture_output=True,
        text=True,
    )
    if cp.returncode:
        fail(f"cannot read git status: {repo}: {cp.stderr}")
    return not cp.stdout.strip()


def derive() -> dict[str, Any]:
    plan = load(PLAN)
    cases = {row["study"]: row for row in plan["cases"]}
    paper1_head = git_head(PAPER1_REPO)
    paper2_head = git_head(PAPER2_REPO)
    if paper1_head != cases["paper1-study"]["sourceRevision"]:
        fail("Paper1 source revision moved; re-evaluate maturity pressure")
    if paper2_head != cases["paper2-independent-study"]["sourceRevision"]:
        fail("Paper2 source revision moved; re-evaluate maturity pressure")
    if not git_clean(PAPER1_REPO) or not git_clean(PAPER2_REPO):
        fail("Study repository dirty; maturity pressure cannot omit current bytes")

    p1 = load(PAPER1_PERMISSION)
    if (
        sha256(PAPER1_PERMISSION)
        != "sha256:d012d8765f39585aca781abbe892c21cf6c1d9838de977cbb85daa5738fef82f"
    ):
        fail("Paper1 ClaimPermission bytes drifted")
    if p1.get("status") != "PASS_PAPER1_R25_STUDY_OWNED_CLAIM_PERMISSION_R1":
        fail("Paper1 owner-native ClaimPermission no longer passes")
    if p1.get("studyOwner") != "paper1-study":
        fail("Paper1 ClaimPermission owner drifted")
    if p1.get("scienceState", {}).get("scienceStanding") != "FREEZE_SCIENCE":
        fail("Paper1 science is not frozen")
    if p1.get("admission", {}).get("sharedExecutablePolicy") != "NOT_ADMITTED":
        fail("Paper1 artifact silently promoted shared policy")
    if len(p1.get("claims", [])) != 9:
        fail("Paper1 exact claim count drifted")

    p2_profile = load(PAPER2_PROFILE)
    if p2_profile["studyAuthority"]["sourceRepo"] != str(PAPER2_REPO):
        fail("Paper2 shared profile source repo drifted")
    if p2_profile["studyAuthority"]["sourceRevision"] != paper2_head:
        fail("Paper2 profile no longer binds current authority")
    axes = p2_profile["stateAxes"]
    expected_axes = {
        "inference": "ACTIVE_ELIGIBILITY_AND_SYNTHESIS_NOT_CLOSED",
        "claims": "PUBLICATION_CLAIMSET_NOT_PROJECTED",
        "review": "SCREENING_AND_ADJUDICATION_ACTIVE",
        "publication": "NOT_IN_PUBLICATION_QUALIFICATION_PHASE",
    }
    for axis, expected in expected_axes.items():
        if axes[axis]["state"] != expected:
            fail(f"Paper2 maturity axis moved: {axis}={axes[axis]['state']!r}")

    p2: dict[str, dict[str, Any]] = {}
    bindings: dict[str, dict[str, str]] = {}
    for name, (rel, expected_digest) in PAPER2_FILES.items():
        path = PAPER2_REPO / rel
        if sha256(path) != expected_digest:
            fail(f"Paper2 authority file drifted: {name}")
        p2[name] = load(path)
        bindings[name] = {"path": rel, "digest": expected_digest}

    if (
        p2["protocolBundle"].get("status")
        != "CONTROLLER_FROZEN_PRE_OUTCOME_PENDING_G2_R9_REVALIDATION"
    ):
        fail("Paper2 protocol bundle no longer pre-outcome pending")
    sap = p2["statisticalPlan"]
    if sap.get("status") != "CONTROLLER_FROZEN_PRE_OUTCOME":
        fail("Paper2 statistical plan no longer pre-outcome frozen")
    ceilings = sap.get("claim_ceiling", [])
    if not isinstance(ceilings, list) or len(ceilings) < 3:
        fail("Paper2 future claim ceiling missing")

    ta = p2["titleAbstractContract"]
    if (
        ta.get("phase") != "title_abstract"
        or ta.get("status") != "FROZEN_FOR_INDEPENDENT_DUAL_CODING"
    ):
        fail("Paper2 title/abstract phase boundary drifted")
    if (
        ta.get("claim_boundary")
        != "No focal claim coding occurs at title/abstract phase."
    ):
        fail("Paper2 title/abstract claim boundary weakened")

    dual = p2["dualCoderAssignment"]
    if dual.get("status") != "READY_WAITING_DISTINCT_CODERS":
        fail("Paper2 dual-coder admission state moved")
    if dual.get("adjudication_before_two_seals") != "FORBIDDEN":
        fail("Paper2 adjudication-before-two-seals boundary weakened")
    if dual.get("cross_coder_visibility_before_seal") != "FORBIDDEN":
        fail("Paper2 cross-coder visibility boundary weakened")
    if dual.get("controller_can_count_as_independent_coder") is not False:
        fail("Paper2 controller independence boundary weakened")

    adjud = p2["adjudicationCandidate"]
    if (
        adjud.get("standing")
        != "FINAL_CANDIDATE_PENDING_FROZEN_R58_ADJUDICATION_VALIDATOR"
    ):
        fail("Paper2 adjudication candidate unexpectedly became final authority")
    if p2["postCoderPipeline"].get("status") != "FROZEN_READY_PRE_CODER_OUTPUT":
        fail("Paper2 post-coder pipeline contract drifted")
    scientific_boundary = p2["fulltextReadiness"].get("scientific_boundary", "")
    if "makes no full-text eligibility decisions" not in scientific_boundary:
        fail("Paper2 fulltext readiness scientific boundary weakened")

    return {
        "schemaVersion": 1,
        "kind": "ordivon.research.claim-permission-maturity-pressure-evidence",
        "id": "claim-permission-maturity-pressure-r1",
        "standing": "PASS_CLAIM_PERMISSION_MATURITY_GATE_PRESSURE_R1",
        "truthRole": "cross-study-maturity-pressure-not-shared-scientific-policy",
        "candidateRule": plan["candidateRule"],
        "cases": {
            "paper1": {
                "sourceRevision": paper1_head,
                "claimCount": 9,
                "scienceStanding": "FREEZE_SCIENCE",
                "ownerNativeClaimPermission": "PASS_PAPER1_R25_STUDY_OWNED_CLAIM_PERMISSION_R1",
                "disposition": "MATURE_OWNER_NATIVE_CLAIM_PERMISSION_EXISTS",
            },
            "paper2": {
                "sourceRevision": paper2_head,
                "protocolStanding": p2["protocolBundle"]["status"],
                "statisticalPlanStanding": sap["status"],
                "titleAbstractStanding": ta["status"],
                "adjudicationCandidateStanding": adjud["standing"],
                "fulltextScientificBoundary": scientific_boundary,
                "profileAxes": expected_axes,
                "disposition": "NOT_MATURE_FOR_SCIENTIFIC_CLAIM_PERMISSION",
                "reason": "Outcome, eligibility, and synthesis authority is not closed and the active title/abstract contract forbids focal claim coding; a prospective claim ceiling is not an outcome-bearing claim permission.",
            },
        },
        "paper2Bindings": bindings,
        "pressureResult": {
            "maturityGate": "SUPPORTED_BY_ONE_MATURE_AND_ONE_PRE_OUTCOME_STUDY",
            "preOutcomeProtocolCanDefineFutureCeilings": True,
            "preOutcomeProtocolIsClaimPermission": False,
            "sharedExecutableClaimPermission": "NOT_ADMITTED",
            "crossStudyPromotionEligible": False,
        },
        "nonClaims": plan["nonClaims"],
    }


def main() -> int:
    derived = derive()
    encoded = json.dumps(derived, indent=2, ensure_ascii=False, sort_keys=True) + "\n"
    if RECEIPT.exists():
        recorded = load(RECEIPT)
        if recorded != derived:
            fail(
                "recorded maturity-pressure receipt drifted from current Study authorities"
            )
    else:
        RECEIPT.write_text(encoded, encoding="utf-8")
    print(encoded, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
