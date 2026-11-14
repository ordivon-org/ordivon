"""Task-local real Owner workflow evidence, conservative TMS AND/OR support.

These tests exercise the newly introduced kernel only. Historical Rust/PG18/
Security proofs are not invalidated by this module.
"""

from __future__ import annotations

import copy
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from ordivon_composition import github_justification_r1 as owner
from ordivon_composition.cognitive_circuit_r1 import CircuitContractError, _validate_schema

SHA = "c9daf823040b2a9bd7f5543b778a68cd937bbd07"
OLDER = "9f5d3b466110c469b2ea587d01f824290849b96b"
REF_A = "github:run:43567631728"
REF_B = "github:run:43490396164"
REF_C = "github:run:43567631727"


def work():
    return {
        "kind": "ordivon.host-work",
        "workRef": "work:test:owner-justifications",
        "revision": 3,
        "state": "open",
        "snapshot": {
            "objective": "Avoid repeat GitHub Owner checks for same SHA",
            "frontier": "Native GitHub Owner proof required before handoff",
            "established": ["Previous source 9f5d has an official run"],
            "unresolved": ["Current SHA still needs exact owner check"],
            "rejected": [],
            "constraints": ["No full reruns"],
            "nextActions": ["Continue code review", "verification-justification:stale: outdated"],
            "referenceRefs": [REF_A, REF_B, REF_C],
        },
    }


def manifest():
    return {
        "kind": "ordivon.github-workflow-justification-contract",
        "repo": "ordivon-org/ordivon",
        "targetSourceCut": SHA,
        "claims": [
            {
                "id": "claim:required-check",
                "consumerRef": "work:test:owner-justifications",
                "anyOf": [
                    {
                        "id": "reason:old-run",
                        "allOf": [{"evidenceRef": REF_B, "workflowName": "Monorepo Required"}],
                    },
                    {
                        "id": "reason:new-run",
                        "allOf": [{"evidenceRef": REF_A, "workflowName": "Monorepo Required"}],
                    },
                ],
            }
        ],
    }


def fake_receipts(monkeypatch, results):
    monkeypatch.setattr(owner, "_native_git_head", lambda _repo: SHA)

    def read(*, repo, run_ref):
        assert repo == "ordivon-org/ordivon"
        return {
            "evidenceRef": run_ref,
            "runId": int(run_ref.split(":")[-1]),
            "url": f"https://github.com/{repo}/actions/runs/{run_ref.split(':')[-1]}",
            "headSha": SHA,
            "workflowName": "Monorepo Required",
            "status": "completed",
            "conclusion": "success",
            "readStanding": "GITHUB_OWNER_READ_SUCCESS",
            **results.get(run_ref, {}),
        }

    monkeypatch.setattr(owner, "_github_run", read)


def schema_path():
    return (
        Path(__file__).resolve().parents[1]
        / "src/ordivon_composition/schemas/agent-host-github-justification-v1.schema.json"
    )


def test_valid_new_sha_or_branch_outvotes_stale_sha_without_rerun(monkeypatch):
    fake_receipts(monkeypatch, {REF_B: {"headSha": OLDER}})
    w = work()
    result = owner.project_github_owner_justifications(
        work=w, contract=manifest(), git_repo=Path(".")
    )
    assert result["summary"]["exactWorkflowRequirementsSatisfied"] == 1
    assert result["summary"]["unknownOrNotMatching"] == 0
    assert result["summary"]["newVerificationJobsCreated"] == 0
    assert (
        result["evidence"][0]["qualification"] == "MATCHED_CHECK_SUCCESS"
        or result["evidence"][1]["qualification"] == "MATCHED_CHECK_SUCCESS"
    )
    assert {x["qualification"] for x in result["evidence"]} == {
        "MATCHED_CHECK_SUCCESS",
        "SOURCE_MISMATCH",
    }
    c = result["claims"][0]
    assert c["supportStanding"] == "EVIDENCE_REQUIREMENTS_SATISFIED"
    assert c["agentDecision"] == "CONSUME_EXISTING_EXACT_GITHUB_CHECK_RESULT"
    assert c["domainClaimVerified"] is False
    assert c["automaticVerifierExecution"] is False
    assert len(c["justifications"]) == 2
    assert {j["standing"] for j in c["justifications"]} == {
        "ALL_OWNER_CHECKS_MATCHED",
        "NOT_ALL_OWNER_CHECKS_MATCHED",
    }
    proposal = result["proposedWorkSnapshot"]
    assert proposal is not None
    assert proposal["established"] == w["snapshot"]["established"]
    assert proposal["referenceRefs"] == w["snapshot"]["referenceRefs"]
    assert proposal["unresolved"] == w["snapshot"]["unresolved"]
    assert proposal["nextActions"][0] == "Continue code review"
    assert not any("stale" in x for x in proposal["nextActions"])
    assert len(proposal["nextActions"]) == 2
    _validate_schema(result, schema_path(), "native owner justification")


def test_and_requires_every_owner_check_and_no_boolean_false_inference(monkeypatch):
    fake_receipts(monkeypatch, {REF_C: {"status": "in_progress", "conclusion": None}})
    m = manifest()
    m["claims"][0]["anyOf"] = [
        {
            "id": "reason:both",
            "allOf": [
                {"evidenceRef": REF_A, "workflowName": "Monorepo Required"},
                {"evidenceRef": REF_C, "workflowName": "Monorepo Required"},
            ],
        }
    ]
    got = owner.project_github_owner_justifications(work=work(), contract=m, git_repo=Path("."))
    assert got["claims"][0]["supportStanding"] == "UNKNOWN"
    assert got["claims"][0]["agentDecision"] == "QUALIFY_OWNER_CHECK_NOT_AUTOMATIC_RERUN"
    assert (
        next(e for e in got["evidence"] if e["evidenceRef"] == REF_C)["qualification"]
        == "CHECK_NOT_COMPLETE"
    )
    assert got["summary"]["newVerificationJobsCreated"] == 0
    _validate_schema(got, schema_path(), "TMS AND unfinished")


def test_owner_check_failure_not_claim_refutation(monkeypatch):
    fake_receipts(monkeypatch, {REF_A: {"conclusion": "failure"}})
    m = manifest()
    m["claims"][0]["anyOf"] = m["claims"][0]["anyOf"][1:]
    got = owner.project_github_owner_justifications(work=work(), contract=m, git_repo=Path("."))
    assert got["evidence"][0]["qualification"] == "CHECK_NOT_SUCCESSFUL"
    assert got["claims"][0]["supportStanding"] == "UNKNOWN"
    assert got["claims"][0]["domainClaimVerified"] is False


def test_missing_run_owner_response_is_unknown_and_requires_qualification(monkeypatch):
    fake_receipts(
        monkeypatch,
        {
            REF_A: {
                "readStanding": "OWNER_UNAVAILABLE_OR_IDENTITY_MISMATCH",
                "headSha": None,
                "workflowName": None,
                "status": None,
                "conclusion": None,
                "url": None,
            }
        },
    )
    m = manifest()
    m["claims"][0]["anyOf"] = m["claims"][0]["anyOf"][1:]
    got = owner.project_github_owner_justifications(work=work(), contract=m, git_repo=Path("."))
    assert got["evidence"][0]["qualification"] == "OWNER_UNKNOWN"
    assert got["claims"][0]["supportStanding"] == "UNKNOWN"


def test_caller_cannot_invent_owner_evidence_or_another_consumer(monkeypatch):
    fake_receipts(monkeypatch, {})
    m = manifest()
    m["claims"][0]["consumerRef"] = "work:unrelated:consumer"
    with pytest.raises(CircuitContractError, match="exact current Host Work"):
        owner.project_github_owner_justifications(work=work(), contract=m, git_repo=Path("."))
    m = manifest()
    m["claims"][0]["anyOf"][1]["allOf"][0]["evidenceRef"] = "github:run:99999999"
    with pytest.raises(CircuitContractError, match="already be referenced"):
        owner.project_github_owner_justifications(work=work(), contract=m, git_repo=Path("."))


def test_user_supplied_sha_cannot_claim_newer_source_implicitly(monkeypatch):
    fake_receipts(monkeypatch, {})
    m = manifest()
    m["targetSourceCut"] = OLDER
    with pytest.raises(CircuitContractError, match="current native Git"):
        owner.project_github_owner_justifications(work=work(), contract=m, git_repo=Path("."))


def test_malformed_or_duplicate_justifications_rejected(monkeypatch):
    fake_receipts(monkeypatch, {})
    m = manifest()
    m["claims"][0]["anyOf"] = m["claims"][0]["anyOf"] * 2
    with pytest.raises(CircuitContractError, match="duplicate justification"):
        owner.project_github_owner_justifications(work=work(), contract=m, git_repo=Path("."))
    m = manifest()
    m["claims"][0]["anyOf"][0]["allOf"][0]["workflowName"] = "Monorepo Required\n"
    with pytest.raises(CircuitContractError, match="canonical"):
        owner.project_github_owner_justifications(work=work(), contract=m, git_repo=Path("."))


def test_terminal_work_or_nonlegacy_work_proposes_no_cas(monkeypatch):
    fake_receipts(monkeypatch, {})
    w = work()
    w["state"] = "completed"
    got = owner.project_github_owner_justifications(work=w, contract=manifest(), git_repo=Path("."))
    assert not got["proposedHostCommitEligible"] and got["proposedWorkSnapshot"] is None
    w = work()
    w["snapshot"]["engagement"] = {"phase": "submitted"}
    got = owner.project_github_owner_justifications(work=w, contract=manifest(), git_repo=Path("."))
    assert not got["proposedHostCommitEligible"]


def test_native_gh_owner_identity_and_repo_query_reject_forgery():
    def fake_good(args, **kwargs):
        assert args[:3] == ["gh", "run", "view"]
        assert "--repo" in args and kwargs["timeout"] == 20
        return SimpleNamespace(
            returncode=0,
            stdout=json.dumps(
                {
                    "databaseId": 43567631728,
                    "headSha": SHA,
                    "status": "completed",
                    "conclusion": "success",
                    "workflowName": "Monorepo Required",
                    "url": "https://github.com/ordivon-org/ordivon/actions/runs/43567631728",
                }
            ),
        )

    good = owner._github_run(repo="ordivon-org/ordivon", run_ref=REF_A, runner=fake_good)
    assert good["readStanding"] == "GITHUB_OWNER_READ_SUCCESS"

    def fake_forged(args, **kwargs):
        value = json.loads(fake_good(args, **kwargs).stdout)
        value["url"] = "https://github.com/other/repo/actions/runs/43567631728"
        return SimpleNamespace(returncode=0, stdout=json.dumps(value))

    bad = owner._github_run(repo="ordivon-org/ordivon", run_ref=REF_A, runner=fake_forged)
    assert bad["readStanding"] == "OWNER_UNAVAILABLE_OR_IDENTITY_MISMATCH"


def test_schema_rejects_claim_truth_owner_forgery_and_wrong_decision(monkeypatch):
    fake_receipts(monkeypatch, {})
    result = owner.project_github_owner_justifications(
        work=work(), contract=manifest(), git_repo=Path(".")
    )
    for path, change in [
        ("domain", lambda p: p["claims"][0].update(domainClaimVerified=True)),
        ("jobs", lambda p: p["summary"].update(newVerificationJobsCreated=1)),
        (
            "status",
            lambda p: p["claims"][0].update(
                agentDecision="QUALIFY_OWNER_CHECK_NOT_AUTOMATIC_RERUN"
            ),
        ),
        ("headsha", lambda p: p.update(targetSourceCut=SHA + "\n")),
        ("nocas", lambda p: p.update(proposedWorkSnapshot=None)),
    ]:
        tampered = copy.deepcopy(result)
        change(tampered)
        with pytest.raises(CircuitContractError):
            _validate_schema(tampered, schema_path(), path)


def test_real_native_git_head_is_exact_commit_id(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    import subprocess

    subprocess.run(["git", "init", "-q", str(repo)], check=True)
    subprocess.run(
        ["git", "-C", str(repo), "config", "user.email", "test@example.invalid"], check=True
    )
    subprocess.run(["git", "-C", str(repo), "config", "user.name", "Test"], check=True)
    (repo / "README").write_text("real git\n")
    subprocess.run(["git", "-C", str(repo), "add", "."], check=True)
    subprocess.run(["git", "-C", str(repo), "commit", "-qm", "first"], check=True)
    import re

    assert re.fullmatch(r"[0-9a-f]{40}|[0-9a-f]{64}", owner._native_git_head(repo))
