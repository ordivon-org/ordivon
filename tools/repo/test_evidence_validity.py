"""Evidence-reuse consumer tests: no owner jobs, CI replays or fake claims."""

from __future__ import annotations

import importlib.util
import itertools
from pathlib import Path
from unittest.mock import Mock

import pytest

SOURCE = Path(__file__).with_name("evidence_validity.py")
SPEC = importlib.util.spec_from_file_location("evidence_validity", SOURCE)
assert SPEC is not None and SPEC.loader is not None
module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(module)

PREVIOUS = "a" * 40
CURRENT = "b" * 40
GOOD = {
    "id": 101,
    "name": "root-verification",
    "head_sha": CURRENT,
    "app": {"slug": "github-actions"},
    "status": "completed",
    "conclusion": "success",
    "completed_at": "2026-11-14T00:00:00Z",
    "details_url": "https://github.com/ordivon-org/ordivon/actions/runs/3",
}


class FixtureGh:
    def __init__(self, rows: dict[str, list[dict]]):
        self.rows = rows
        self.calls: list[str] = []

    def api(self, endpoint: str):
        self.calls.append(endpoint)
        sha = endpoint.split("/commits/", 1)[1].split("/", 1)[0]
        page = int(endpoint.rsplit("&page=", 1)[1])
        records = self.rows.get(sha, [])
        return {
            "total_count": len(records),
            "check_runs": records[(page - 1) * 100 : page * 100],
        }


@pytest.fixture(autouse=True)
def source_id(monkeypatch):
    # Unit tests assert provider and decision logic. One external read-only
    # smoke uses actual Git objects and live GitHub metadata separately.
    monkeypatch.setattr(module, "_exact_commit", lambda sha: sha)
    monkeypatch.setattr(module, "require_ancestral_source_cuts", lambda *a: None)


def provider(row: dict | None = None, *, previous: list[dict] | None = None):
    return FixtureGh({CURRENT: [row] if row else [], PREVIOUS: previous or []})


def test_actual_current_pass_is_reused_without_rescheduling(monkeypatch):
    selection = Mock(side_effect=AssertionError("must not select or rerun native CI"))
    monkeypatch.setattr(module.convergence_plan, "build_plan", selection)
    gh = provider(dict(GOOD))
    result = module.decide(
        repo=module.DEFAULT_REPOSITORY,
        current_sha=CURRENT,
        prior_sha=PREVIOUS,
        github=gh,
    )
    assert result["disposition"] == "REUSE_CURRENT_RECEIPT"
    assert result["existingCheckReceiptReusable"] is True
    assert result["proofReuseAdmissible"] is False
    assert result["reuseScope"] == "EXACT_COMMIT_NAMED_PROVIDER_CHECK_OUTCOME"
    assert result["currentEvidence"]["checkRunId"] == GOOD["id"]
    assert len(gh.calls) == 1
    selection.assert_not_called()


@pytest.mark.parametrize(
    "new_status,new_conclusion,expected",
    [
        ("in_progress", None, "OBSERVE_EXISTING_RUN"),
        ("queued", None, "OBSERVE_EXISTING_RUN"),
        ("completed", "failure", "INVESTIGATE_EXISTING_RESULT"),
        ("completed", "cancelled", "INVESTIGATE_EXISTING_RESULT"),
        ("completed", "skipped", "INVESTIGATE_EXISTING_RESULT"),
    ],
)
def test_pending_failed_or_skipped_check_never_recurs_as_pass(
    monkeypatch, new_status, new_conclusion, expected
):
    monkeypatch.setattr(
        module.convergence_plan,
        "build_plan",
        Mock(side_effect=AssertionError("never schedule old PASS over new run")),
    )
    current = dict(GOOD, status=new_status, conclusion=new_conclusion)
    old = dict(GOOD, id=95, head_sha=PREVIOUS)
    result = module.decide(
        repo=module.DEFAULT_REPOSITORY,
        current_sha=CURRENT,
        prior_sha=PREVIOUS,
        github=provider(current, previous=[old]),
    )
    assert result["disposition"] == expected
    assert result["proofReuseAdmissible"] is False


def test_later_failed_rerun_overrides_older_success():
    gh = provider()
    newer_failure = dict(GOOD, id=110, conclusion="failure")
    gh.rows[CURRENT] = [dict(GOOD), newer_failure]
    result = module.decide(
        repo=module.DEFAULT_REPOSITORY, current_sha=CURRENT, github=gh
    )
    assert result["currentEvidence"]["checkRunId"] == 110
    assert result["disposition"] == "INVESTIGATE_EXISTING_RESULT"
    assert not result["proofReuseAdmissible"]


def test_fake_app_or_mismatching_check_identity_cannot_grant_reuse():
    gh = provider(dict(GOOD, app={"slug": "untrusted-robot"}))
    result = module.decide(
        repo=module.DEFAULT_REPOSITORY, current_sha=CURRENT, github=gh
    )
    assert result["disposition"] == "UNKNOWN_NO_ACCEPTED_EVIDENCE"
    assert not result["proofReuseAdmissible"]
    gh.rows[CURRENT] = [dict(GOOD, head_sha=PREVIOUS)]
    with pytest.raises(ValueError, match="contradicts"):
        module.decide(repo=module.DEFAULT_REPOSITORY, current_sha=CURRENT, github=gh)


def test_partial_provider_listing_is_not_a_pass():
    class Truncated:
        def api(self, endpoint):
            page = int(endpoint.rsplit("&page=", 1)[1])
            return {"total_count": 101, "check_runs": [dict(GOOD)] if page == 1 else []}

    with pytest.raises(ValueError, match="truncated"):
        module.decide(
            repo=module.DEFAULT_REPOSITORY,
            current_sha=CURRENT,
            github=Truncated(),
        )


def test_complete_multi_page_check_run_listing():
    gh = provider()
    gh.rows[CURRENT] = [{"name": "other-check", "id": i} for i in range(1, 101)] + [
        dict(GOOD, id=110)
    ]
    result = module.decide(
        repo=module.DEFAULT_REPOSITORY, current_sha=CURRENT, github=gh
    )
    assert result["disposition"] == "REUSE_CURRENT_RECEIPT"
    assert len(gh.calls) == 2


def test_cross_sha_prior_pass_uses_native_owner_impact_not_false_reuse(monkeypatch):
    native = {
        "changedPaths": ["services/gateway/src/ordivon_gateway/mcp_server.py"],
        "verificationOwners": ["gateway", "harness"],
        "queueVerifyTasks": ["gateway:verify", "harness:queue"],
        "proofReuseAdmissible": False,
    }
    called = Mock(return_value=native)
    monkeypatch.setattr(module.convergence_plan, "build_plan", called)
    past = dict(GOOD, id=93, head_sha=PREVIOUS)
    result = module.decide(
        repo=module.DEFAULT_REPOSITORY,
        current_sha=CURRENT,
        prior_sha=PREVIOUS,
        github=provider(previous=[past]),
    )
    assert result["disposition"] == "SOURCE_AFFECTED"
    assert result["sourceImpact"]["queueVerifyTasks"] == native["queueVerifyTasks"]
    assert result["proofReuseAdmissible"] is False
    called.assert_called_once_with(base=PREVIOUS, head=CURRENT)


def test_no_known_source_impact_does_not_prove_cross_cut_reuse(monkeypatch):
    monkeypatch.setattr(
        module.convergence_plan,
        "build_plan",
        lambda **kw: {
            "changedPaths": [],
            "verificationOwners": [],
            "queueVerifyTasks": [],
        },
    )
    past = dict(GOOD, head_sha=PREVIOUS)
    result = module.decide(
        repo=module.DEFAULT_REPOSITORY,
        current_sha=CURRENT,
        prior_sha=PREVIOUS,
        github=provider(previous=[past]),
    )
    assert result["disposition"] == "UNKNOWN_CROSS_CUT_READSET"
    assert not result["proofReuseAdmissible"]


def test_absent_or_unqualified_prior_check_does_not_spawn_ci(monkeypatch):
    monkeypatch.setattr(
        module.convergence_plan, "build_plan", Mock(side_effect=AssertionError)
    )
    actual = module.decide(
        repo=module.DEFAULT_REPOSITORY,
        current_sha=CURRENT,
        prior_sha=PREVIOUS,
        github=provider(),
    )
    assert actual["disposition"] == "UNKNOWN_NO_ACCEPTED_EVIDENCE"


def test_nonancestor_or_invalid_impact_stays_unknown(monkeypatch):
    past = dict(GOOD, head_sha=PREVIOUS)
    monkeypatch.setattr(
        module.convergence_plan,
        "build_plan",
        Mock(side_effect=ValueError("not comparable source cuts")),
    )
    result = module.decide(
        repo=module.DEFAULT_REPOSITORY,
        current_sha=CURRENT,
        prior_sha=PREVIOUS,
        github=provider(previous=[past]),
    )
    assert result["disposition"] == "UNKNOWN_SOURCE_RELATION"
    assert not result["proofReuseAdmissible"]


def test_future_state_space_bound_enforces_reuse_only_on_current_success():
    statuses = ("ABSENT", "IN_PROGRESS", "PASS", "NOT_PASS")
    for now, past, affected in itertools.product(statuses, statuses, (False, True)):

        def check(standing, sha):
            if standing == "ABSENT":
                return None
            return {
                "headSha": sha,
                "status": (
                    "completed" if standing in {"PASS", "NOT_PASS"} else "in_progress"
                ),
                "conclusion": "success" if standing == "PASS" else "failure",
            }

        impact = {
            "changedPaths": ["services/gateway/foo.py"] if affected else [],
            "verificationOwners": ["gateway"] if affected else [],
            "queueVerifyTasks": ["gateway:verify"] if affected else [],
        }
        decision = module._decision(
            current_sha=CURRENT,
            prior_sha=PREVIOUS,
            check_name="root-verification",
            current_check=check(now, CURRENT),
            prior_check=check(past, PREVIOUS),
            source_impact=impact,
        )
        assert decision["proofReuseAdmissible"] is False
        assert decision["existingCheckReceiptReusable"] is (now == "PASS")
        if now != "PASS":
            assert decision["reuseScope"] is None
        if now == "ABSENT" and past == "PASS":
            assert decision["disposition"] in {
                "SOURCE_AFFECTED",
                "UNKNOWN_CROSS_CUT_READSET",
            }


def test_invalid_repo_and_check_name_refuse_injection():
    for value in ("../../x", "owner/repo?token=secret", "", "a/b/c"):
        with pytest.raises(ValueError, match="repository"):
            module.decide(repo=value, current_sha=CURRENT, github=provider())
    with pytest.raises(ValueError, match="name"):
        module.decide(
            repo=module.DEFAULT_REPOSITORY,
            current_sha=CURRENT,
            check_name="",
            github=provider(),
        )


def test_sibling_git_tips_do_not_admit_impact_evolution(monkeypatch):
    prior = dict(GOOD, head_sha=PREVIOUS)

    def refuse_ancestry(*args):
        raise ValueError("sourceCut ancestry not established")

    monkeypatch.setattr(module, "require_ancestral_source_cuts", refuse_ancestry)
    monkeypatch.setattr(
        module.convergence_plan,
        "build_plan",
        Mock(side_effect=AssertionError("must not compare sibling tips")),
    )
    result = module.decide(
        repo=module.DEFAULT_REPOSITORY,
        current_sha=CURRENT,
        prior_sha=PREVIOUS,
        github=provider(previous=[prior]),
    )
    assert result["disposition"] == "UNKNOWN_SOURCE_RELATION"
    assert result["proofReuseAdmissible"] is False


def test_success_with_missing_provenance_cannot_be_reused():
    variants = (
        {"completed_at": None},
        {"completed_at": "not-a-time"},
        {"completed_at": "2026-11-14T00:00:00"},
        {"details_url": "http://github.com/ordivon-org/ordivon/actions/runs/1"},
        {"details_url": "https://other.example/ordivon-org/ordivon/actions/runs/1"},
    )
    for fields in variants:
        check = dict(GOOD, **fields)
        with pytest.raises(ValueError, match="provenance|completion time"):
            module.decide(
                repo=module.DEFAULT_REPOSITORY,
                current_sha=CURRENT,
                github=provider(check),
            )


def test_duplicated_provider_page_id_fails_closed():
    gh = provider()
    gh.rows[CURRENT] = [dict(GOOD), dict(GOOD)]
    with pytest.raises(ValueError, match="duplicate"):
        module.decide(
            repo=module.DEFAULT_REPOSITORY,
            current_sha=CURRENT,
            github=gh,
        )


def test_other_repo_with_matching_git_oid_is_not_a_valid_issuer():
    with pytest.raises(ValueError, match="canonical Ordivon"):
        module.decide(repo="untrusted/repo", current_sha=CURRENT, github=provider())


def test_existing_nonpass_never_needs_older_provider_lookup():
    class CurrentOnly:
        calls = 0

        def api(self, endpoint):
            self.calls += 1
            if PREVIOUS in endpoint:
                raise AssertionError("current failure must not depend on old provider")
            return {
                "total_count": 1,
                "check_runs": [dict(GOOD, status="in_progress", conclusion=None)],
            }

    github = CurrentOnly()
    result = module.decide(
        repo=module.DEFAULT_REPOSITORY,
        current_sha=CURRENT,
        prior_sha=PREVIOUS,
        github=github,
    )
    assert result["disposition"] == "OBSERVE_EXISTING_RUN"
    assert github.calls == 1


def test_formal_source_delta_unchanged_despite_unrelated_source_change(monkeypatch):
    declaration = "SOURCE_FILES = ('tools/formal/verify.py', 'a/source.lean')"
    monkeypatch.setattr(module, "git_native", lambda repo, *args: declaration)
    tree = {
        "tools/formal/verify.py": "100644:blob:" + "1" * 40,
        "a/source.lean": "100644:blob:" + "2" * 40,
    }
    monkeypatch.setattr(module, "current_tree", lambda repo, sha: dict(tree))
    result = module.declared_formal_source_delta(
        repo=Path("/unused"),
        prior_sha=PREVIOUS,
        current_sha=CURRENT,
    )
    assert result["standing"] == "UNCHANGED_DECLARED_SOURCE_INPUTS"
    assert result["declaredSourceReadsetComparisonComplete"]
    assert result["changedDeclaredPaths"] == []
    assert result["proofReuseAdmissible"] is False


def test_formal_source_delta_exact_change_and_declaration_change(monkeypatch):
    old_declaration = "SOURCE_FILES = ('tools/formal/verify.py', 'a/source.lean')"
    new_declaration = (
        "SOURCE_FILES = ('tools/formal/verify.py', 'a/source.lean', 'new/model.lean')"
    )
    monkeypatch.setattr(
        module,
        "git_native",
        lambda repo, *args: old_declaration if PREVIOUS in args[2] else new_declaration,
    )

    def tree(repo, sha):
        if sha == PREVIOUS:
            return {
                "tools/formal/verify.py": "100644:blob:" + "1" * 40,
                "a/source.lean": "100644:blob:" + "2" * 40,
                "new/model.lean": "100644:blob:" + "3" * 40,
            }
        return {
            "tools/formal/verify.py": "100644:blob:" + "9" * 40,
            "a/source.lean": "100644:blob:" + "4" * 40,
            "new/model.lean": "100644:blob:" + "3" * 40,
        }

    monkeypatch.setattr(module, "current_tree", tree)
    result = module.declared_formal_source_delta(
        repo=Path("/unused"),
        prior_sha=PREVIOUS,
        current_sha=CURRENT,
    )
    assert result["standing"] == "CHANGED_DECLARED_SOURCE_INPUTS"
    assert result["declarationChanged"]
    assert result["changedDeclaredPaths"] == ["a/source.lean", "tools/formal/verify.py"]
    assert result["proofReuseAdmissible"] is False


def test_formal_declaration_refuses_arbitrary_dynamic_code(monkeypatch):
    monkeypatch.setattr(
        module,
        "git_native",
        lambda repo, *args: "SOURCE_FILES = tuple(__import__('os').listdir('/'))",
    )
    with pytest.raises(ValueError, match="literal"):
        module._formal_declared_files(Path("/unused"), PREVIOUS)


def test_formal_readset_refuses_nonregular_git_object(monkeypatch):
    monkeypatch.setattr(
        module,
        "git_native",
        lambda repo, *args: "SOURCE_FILES = ('tools/formal/verify.py',)",
    )
    monkeypatch.setattr(
        module,
        "current_tree",
        lambda repo, sha: {"tools/formal/verify.py": "120000:blob:" + "1" * 40},
    )
    with pytest.raises(ValueError, match="non-regular"):
        module.declared_formal_source_delta(
            repo=Path("/unused"),
            prior_sha=PREVIOUS,
            current_sha=CURRENT,
        )


def test_formal_readset_requires_native_ancestry(monkeypatch):
    monkeypatch.setattr(
        module,
        "require_ancestral_source_cuts",
        Mock(side_effect=ValueError("sibling tip")),
    )
    with pytest.raises(ValueError, match="sibling"):
        module.declared_formal_source_delta(
            repo=Path("/unused"),
            prior_sha=PREVIOUS,
            current_sha=CURRENT,
        )


def test_failed_formal_delta_cannot_erase_successful_github_receipt(monkeypatch):
    monkeypatch.setattr(
        module,
        "declared_formal_source_delta",
        Mock(side_effect=ValueError("unqualified unrelated git input")),
    )
    result = module.decide_with_optional_formal_source_delta(
        repo=module.DEFAULT_REPOSITORY,
        current_sha=CURRENT,
        prior_sha=PREVIOUS,
        check_name="root-verification",
        include_formal_source_delta=True,
        github=provider(dict(GOOD)),
    )
    assert result["disposition"] == "REUSE_CURRENT_RECEIPT"
    assert result["existingCheckReceiptReusable"] is True
    assert (
        result["formalDeclaredSourceDelta"]["standing"]
        == "UNKNOWN_DECLARED_SOURCE_INPUTS"
    )
    assert result["formalDeclaredSourceDelta"]["proofReuseAdmissible"] is False


def test_newly_declared_formal_file_is_affected_not_unqualified(monkeypatch):
    old = "SOURCE_FILES = ('tools/formal/verify.py',)"
    new = "SOURCE_FILES = ('tools/formal/verify.py', 'new/proof.lean')"
    monkeypatch.setattr(
        module,
        "git_native",
        lambda repo, *args: old if PREVIOUS in args[2] else new,
    )
    monkeypatch.setattr(
        module,
        "current_tree",
        lambda repo, sha: {
            "tools/formal/verify.py": "100644:blob:"
            + ("1" * 40 if sha == PREVIOUS else "2" * 40),
            **(
                {} if sha == PREVIOUS else {"new/proof.lean": "100644:blob:" + "3" * 40}
            ),
        },
    )
    result = module.declared_formal_source_delta(
        repo=Path("/unused"),
        prior_sha=PREVIOUS,
        current_sha=CURRENT,
    )
    assert result["standing"] == "CHANGED_DECLARED_SOURCE_INPUTS"
    assert "new/proof.lean" in result["changedDeclaredPaths"]
    assert result["proofReuseAdmissible"] is False


def _synthetic_formal_report():
    names = ("tools/formal/verify.py", "proof.lean")
    report = {
        "kind": "source-scoped-native-formal-toolchain-check",
        "sourceCut": PREVIOUS,
        "status": "PASS",
        "sourceQualification": "EXACT_GIT_BLOBS_CHECKED_PRE_AND_POST",
        "toolQualification": "MISE_RESOLVED_EXECUTABLE_SHA256_PRE_AND_POST",
        "proofReuseAdmissible": False,
        "sourceBlobs": {names[0]: "1" * 40, names[1]: "2" * 40},
        "probes": [{"probe": "Lean kernel R2.1", "result": "PASS", "rc": 0}],
        "count": 1,
        "toolBinaries": {
            name: {
                "path": "/opt/verified/" + name,
                "version": "1.0",
                "sha256": "a" * 64,
            }
            for name in (
                "lean",
                "z3",
                "cvc5",
                "verus",
                "dafny",
                "kani",
                "quint",
                "alloy",
            )
        },
    }
    return names, report


def test_historical_formal_content_matches_exact_git_source_but_never_proof(
    monkeypatch,
):
    names, report = _synthetic_formal_report()
    monkeypatch.setattr(module, "_formal_declared_files", lambda repo, sha: names)
    monkeypatch.setattr(
        module,
        "current_tree",
        lambda repo, sha: {
            names[0]: "100644:blob:" + "1" * 40,
            names[1]: "100755:blob:" + "2" * 40,
        },
    )
    result = module.inspect_historical_formal_report(
        repo=Path("/repo"), source_sha=PREVIOUS, report=report
    )
    assert result["standing"] == "CONTENT_MATCHES_DECLARED_GIT_SOURCE"
    assert result["reportedProbeCount"] == 1
    assert result["reportedToolEntrypoints"] == 8
    assert result["artifactProvenance"] == "UNVERIFIED_LOCAL_INPUT"
    assert result["proofReuseAdmissible"] is False


def test_historical_formal_content_refuses_mutated_inputs_and_false_proof(monkeypatch):
    names, good = _synthetic_formal_report()
    monkeypatch.setattr(module, "_formal_declared_files", lambda repo, sha: names)
    monkeypatch.setattr(
        module,
        "current_tree",
        lambda repo, sha: {
            names[0]: "100644:blob:" + "1" * 40,
            names[1]: "100644:blob:" + "2" * 40,
        },
    )
    import copy

    for mutation in (
        {"sourceCut": CURRENT},
        {"status": "FAILED"},
        {"proofReuseAdmissible": True},
        {"count": 2},
        {"sourceBlobs": {names[0]: "1" * 40}},
        {"sourceBlobs": {names[0]: "1" * 40, names[1]: "3" * 40}},
        {"probes": [{"probe": "Lean", "result": "FAIL"}]},
        {"toolBinaries": {"z3": {"path": "x", "version": "v", "sha256": "a" * 64}}},
    ):
        altered = copy.deepcopy(good)
        altered.update(mutation)
        with pytest.raises(ValueError, match="historical Formal report"):
            module.inspect_historical_formal_report(
                repo=Path("/repo"), source_sha=PREVIOUS, report=altered
            )


def test_historical_formal_reader_refuses_symlink_and_large_file(monkeypatch, tmp_path):
    report = tmp_path / "receipt.json"
    report.write_text("{}", encoding="utf-8")
    (tmp_path / "link.json").symlink_to(report)
    with pytest.raises(ValueError, match="bounded regular file"):
        module.inspect_historical_formal_report_file(
            repo=tmp_path, source_sha=PREVIOUS, path=tmp_path / "link.json"
        )
    report.write_text("x" * 1048577, encoding="utf-8")
    with pytest.raises(ValueError, match="bounded regular file"):
        module.inspect_historical_formal_report_file(
            repo=tmp_path, source_sha=PREVIOUS, path=report
        )


def test_ci_formal_receipt_published_only_after_existing_scoped_validator():
    workflow = (
        Path(__file__).resolve().parents[2] / ".github/workflows/ci.yml"
    ).read_text()
    validation = (
        'print("Native Formal scoped verifier PASS; proof reuse remains unadmitted")'
    )
    publishing = "- name: Publish scoped native Formal evidence receipt"
    assert workflow.count(publishing) == 1
    assert workflow.index(validation) < workflow.index(publishing)
    selected = workflow.split(publishing, 1)[1].split("- name:", 1)[0]
    assert "if: steps.affected.outputs.formal == 'true'" in selected
    assert (
        "actions/upload-artifact@cf430e030ddbb5b0abf93d22962f4752f3646cd9" in selected
    )
    assert "name: ordivon-core-formal-" + chr(36) + "{{ github.sha }}" in selected
    assert "ordivon-core-formal-report.json" in selected
    assert "if-no-files-found: error" in selected


def test_fetch_original_formal_report_uses_github_run_and_native_gh(monkeypatch):
    names, report = _synthetic_formal_report()
    check = dict(
        GOOD,
        head_sha=PREVIOUS,
        details_url=("https://github.com/ordivon-org/ordivon/actions/runs/731/job/101"),
    )

    class VerifiedRunProvider:
        def __init__(self):
            self.queries = []

        def api(self, endpoint):
            self.queries.append(endpoint)
            if "/commits/" in endpoint:
                return {"total_count": 1, "check_runs": [check]}
            if endpoint == "repos/ordivon-org/ordivon/actions/runs/731":
                return {
                    "id": 731,
                    "head_sha": PREVIOUS,
                    "repository": {"full_name": module.DEFAULT_REPOSITORY},
                }
            assert endpoint == (
                "repos/ordivon-org/ordivon/actions/runs/731/artifacts?per_page=100&page=1"
            )
            return {
                "total_count": 1,
                "artifacts": [
                    {
                        "id": 19,
                        "name": "ordivon-core-formal-" + PREVIOUS,
                        "size_in_bytes": 321,
                        "expired": False,
                        "digest": "sha256:" + "a" * 64,
                        "workflow_run": {"id": 731, "head_sha": PREVIOUS},
                    }
                ],
            }

    provider = VerifiedRunProvider()
    monkeypatch.setattr(module, "_formal_declared_files", lambda repo, sha: names)
    monkeypatch.setattr(
        module,
        "current_tree",
        lambda repo, sha: {
            names[0]: "100644:blob:" + "1" * 40,
            names[1]: "100644:blob:" + "2" * 40,
        },
    )
    cmds = []

    def download(cmd, **kwargs):
        cmds.append(cmd)
        assert kwargs["check"] is True and kwargs["timeout"] == 75
        directory = Path(cmd[cmd.index("--dir") + 1])
        (directory / "ordivon-core-formal-report.json").write_text(
            __import__("json").dumps(report), encoding="utf-8"
        )
        return Mock(returncode=0)

    monkeypatch.setattr(module.subprocess, "run", download)
    result = module.fetch_original_formal_report(
        repo=module.DEFAULT_REPOSITORY,
        source_sha=PREVIOUS,
        github=provider,
    )
    assert result["standing"] == "CONTENT_MATCHES_DECLARED_GIT_SOURCE"
    assert result["originalCheckRunId"] == 101
    assert result["originalWorkflowRunId"] == "731"
    assert result["githubArtifactName"] == "ordivon-core-formal-" + PREVIOUS
    assert result["proofReuseAdmissible"] is False
    assert result["artifactProvenance"] == "GITHUB_RUN_DOWNLOAD_NOT_PROOF_EQUIVALENCE"
    assert cmds[0][:4] == ["gh", "run", "download", "731"]
    assert result["sourceRelationship"] == "DIRECT_WORKFLOW_HEAD"
    assert result["githubArtifactId"] == 19
    assert len(provider.queries) == 3


def test_fetch_formal_report_rejects_mismatched_provider_run_before_download(
    monkeypatch,
):
    check = dict(
        GOOD,
        head_sha=PREVIOUS,
        details_url=("https://github.com/ordivon-org/ordivon/actions/runs/731/job/101"),
    )

    class WrongRun:
        def api(self, endpoint):
            if "/commits/" in endpoint:
                return {"total_count": 1, "check_runs": [check]}
            return {
                "id": 731,
                "head_sha": CURRENT,
                "repository": {"full_name": module.DEFAULT_REPOSITORY},
            }

    monkeypatch.setattr(
        module.subprocess,
        "run",
        Mock(side_effect=AssertionError("must not download wrong run")),
    )
    with pytest.raises(ValueError, match="workflow run SourceCut mismatch"):
        module.fetch_original_formal_report(
            repo=module.DEFAULT_REPOSITORY,
            source_sha=PREVIOUS,
            github=WrongRun(),
        )


def test_fetch_formal_report_requires_prior_success_before_download(monkeypatch):
    monkeypatch.setattr(
        module.subprocess,
        "run",
        Mock(side_effect=AssertionError("must not download unverified run")),
    )
    with pytest.raises(ValueError, match="prior successful check"):
        module.fetch_original_formal_report(
            repo=module.DEFAULT_REPOSITORY,
            source_sha=PREVIOUS,
            github=provider(),
        )


def test_real_pr_merge_formal_artifact_needs_both_exact_git_parents(monkeypatch):
    names, report = _synthetic_formal_report()
    merge_sha = "c" * 40
    base_sha = "d" * 40
    report["sourceCut"] = merge_sha
    original = dict(
        GOOD,
        head_sha=PREVIOUS,
        details_url="https://github.com/ordivon-org/ordivon/actions/runs/731/job/101",
    )

    class PrProvider:
        def api(self, endpoint):
            if "/commits/" in endpoint:
                return {"total_count": 1, "check_runs": [original]}
            if endpoint.endswith("/actions/runs/731"):
                return {
                    "id": 731,
                    "head_sha": PREVIOUS,
                    "event": "pull_request",
                    "repository": {"full_name": module.DEFAULT_REPOSITORY},
                    "pull_requests": [
                        {
                            "number": 2182,
                            "head": {"sha": PREVIOUS},
                            "base": {"sha": base_sha},
                        }
                    ],
                }
            assert endpoint.endswith("/actions/runs/731/artifacts?per_page=100&page=1")
            return {
                "total_count": 1,
                "artifacts": [
                    {
                        "id": 222,
                        "name": "ordivon-core-formal-" + merge_sha,
                        "size_in_bytes": 321,
                        "expired": False,
                        "digest": "sha256:" + "a" * 64,
                        "workflow_run": {"id": 731, "head_sha": PREVIOUS},
                    }
                ],
            }

    monkeypatch.setattr(module, "_formal_declared_files", lambda repo, sha: names)
    monkeypatch.setattr(
        module,
        "current_tree",
        lambda repo, sha: {
            names[0]: "100644:blob:" + "1" * 40,
            names[1]: "100644:blob:" + "2" * 40,
        },
    )
    monkeypatch.setattr(
        module,
        "git_native",
        lambda repo, *args: merge_sha + " " + base_sha + " " + PREVIOUS + chr(10),
    )

    def download(cmd, **kwargs):
        assert "--name" in cmd
        assert cmd[cmd.index("--name") + 1] == "ordivon-core-formal-" + merge_sha
        out = Path(cmd[cmd.index("--dir") + 1])
        (out / "ordivon-core-formal-report.json").write_text(
            __import__("json").dumps(report), encoding="utf-8"
        )
        return Mock(returncode=0)

    monkeypatch.setattr(module.subprocess, "run", download)
    result = module.fetch_original_formal_report(
        repo=module.DEFAULT_REPOSITORY,
        source_sha=PREVIOUS,
        github=PrProvider(),
    )
    assert result["requestedWorkflowHeadSha"] == PREVIOUS
    assert result["verifiedExecutionSourceCut"] == merge_sha
    assert result["sourceRelationship"] == "PR_SYNTHETIC_MERGE_BASE_AND_HEAD"
    assert result["sourceCut"] == merge_sha
    assert result["proofReuseAdmissible"] is False

    def wrong_parents(repo, *args):
        return merge_sha + " " + "e" * 40 + " " + PREVIOUS + chr(10)

    monkeypatch.setattr(module, "git_native", wrong_parents)
    monkeypatch.setattr(
        module.subprocess,
        "run",
        Mock(side_effect=AssertionError("must not download unqualified merge")),
    )
    with pytest.raises(ValueError, match="synthetic merge parents mismatch"):
        module.fetch_original_formal_report(
            repo=module.DEFAULT_REPOSITORY,
            source_sha=PREVIOUS,
            github=PrProvider(),
        )


def test_unqualified_artifact_missing_duplicate_expired_or_wrong_run_is_not_reused(
    monkeypatch,
):
    check = dict(
        GOOD,
        head_sha=PREVIOUS,
        details_url="https://github.com/ordivon-org/ordivon/actions/runs/731/job/101",
    )
    valid = {
        "id": 30,
        "name": "ordivon-core-formal-" + PREVIOUS,
        "size_in_bytes": 300,
        "expired": False,
        "digest": "sha256:" + "a" * 64,
        "workflow_run": {"id": 731, "head_sha": PREVIOUS},
    }

    class FixtureProvider:
        def __init__(self, rows):
            self.rows = rows

        def api(self, endpoint):
            if "/commits/" in endpoint:
                return {"total_count": 1, "check_runs": [check]}
            if endpoint.endswith("/actions/runs/731"):
                return {
                    "id": 731,
                    "head_sha": PREVIOUS,
                    "repository": {"full_name": module.DEFAULT_REPOSITORY},
                }
            return {"total_count": len(self.rows), "artifacts": self.rows}

    monkeypatch.setattr(
        module.subprocess,
        "run",
        Mock(side_effect=AssertionError("must not download unqualified artifact")),
    )
    variants = [
        [],
        [dict(valid), dict(valid, id=31)],
        [dict(valid, expired=True)],
        [dict(valid, workflow_run={"id": 999, "head_sha": PREVIOUS})],
        [dict(valid, workflow_run={"id": 731, "head_sha": CURRENT})],
        [dict(valid, digest="sha256:bad")],
        [dict(valid, size_in_bytes=9999999)],
        [dict(valid, name="ordivon-core-formal-" + "f" * 40)],
    ]
    for variant in variants:
        with pytest.raises(ValueError):
            module.fetch_original_formal_report(
                repo=module.DEFAULT_REPOSITORY,
                source_sha=PREVIOUS,
                github=FixtureProvider(variant),
            )


def test_original_formal_merge_and_head_snapshot_green_never_grants_proof(monkeypatch):
    original = "c" * 40
    candidate = "b" * 40
    files = ("tools/formal/verify.py", "formal/source.lean")
    monkeypatch.setattr(module, "_formal_declared_files", lambda repo, sha: files)
    tree = {
        files[0]: "100644:blob:" + "1" * 40,
        files[1]: "100644:blob:" + "2" * 40,
    }
    monkeypatch.setattr(module, "current_tree", lambda repo, sha: dict(tree))
    monkeypatch.setattr(
        module,
        "require_ancestral_source_cuts",
        Mock(side_effect=AssertionError("PR synthetic merge is not ancestor of Head")),
    )
    result = module.compare_formal_execution_inputs_to_candidate(
        repo=Path("/repo"),
        execution_sha=original,
        candidate_sha=candidate,
    )
    assert result["standing"] == "UNCHANGED_DECLARED_SOURCE_INPUTS"
    assert result["changedDeclaredPaths"] == []
    assert result["comparisonBasis"] == (
        "TWO_IMMUTABLE_GIT_SNAPSHOTS_NOT_TEMPORAL_PROOF"
    )
    assert result["proofReuseAdmissible"] is False


def test_original_formal_source_snapshot_red_for_blob_mode_and_membership(monkeypatch):
    original = "c" * 40
    candidate = "b" * 40
    old_files = ("tools/formal/verify.py", "proof.lean", "removed.lean")
    new_files = ("tools/formal/verify.py", "proof.lean", "added.lean")
    monkeypatch.setattr(
        module,
        "_formal_declared_files",
        lambda repo, sha: old_files if sha == original else new_files,
    )
    old_tree = {
        old_files[0]: "100644:blob:" + "1" * 40,
        old_files[1]: "100644:blob:" + "2" * 40,
        old_files[2]: "100644:blob:" + "3" * 40,
    }
    new_tree = {
        new_files[0]: "100644:blob:" + "1" * 40,
        new_files[1]: "100755:blob:" + "2" * 40,
        new_files[2]: "100644:blob:" + "4" * 40,
    }
    monkeypatch.setattr(
        module,
        "current_tree",
        lambda repo, sha: old_tree if sha == original else new_tree,
    )
    result = module.compare_formal_execution_inputs_to_candidate(
        repo=Path("/repo"),
        execution_sha=original,
        candidate_sha=candidate,
    )
    assert result["standing"] == "CHANGED_DECLARED_SOURCE_INPUTS"
    assert result["changedDeclaredPaths"] == [
        "added.lean",
        "proof.lean",
        "removed.lean",
    ]
    assert result["proofReuseAdmissible"] is False


def test_formal_original_snapshot_refuses_nonregular_or_missing_git_member(monkeypatch):
    original, candidate = "c" * 40, "b" * 40
    filenames = ("tools/formal/verify.py",)
    monkeypatch.setattr(module, "_formal_declared_files", lambda repo, sha: filenames)
    monkeypatch.setattr(
        module,
        "current_tree",
        lambda repo, sha: {
            filenames[0]: "120000:blob:" + "1" * 40
            if sha == original
            else "100644:blob:" + "1" * 40
        },
    )
    with pytest.raises(ValueError, match="unqualified Git member"):
        module.compare_formal_execution_inputs_to_candidate(
            repo=Path("/repo"),
            execution_sha=original,
            candidate_sha=candidate,
        )


def test_historical_formal_declaration_uses_original_git_blob_not_replace_overlay(
    monkeypatch,
):
    calls = []

    def original_git(repo, *args):
        calls.append(args)
        return "SOURCE_FILES = ('tools/formal/verify.py',)"

    monkeypatch.setattr(module, "git_native", original_git)
    files = module._formal_declared_files(Path("/repo"), PREVIOUS)
    assert files == ("tools/formal/verify.py",)
    assert calls == [
        ("--no-replace-objects", "show", PREVIOUS + ":tools/formal/verify.py")
    ]


def test_historical_formal_declaration_resists_actual_git_replace_ref(tmp_path):
    """Native Git replacement ref must not rewrite an older proof readset."""
    import subprocess

    repo = tmp_path / "source_repo"
    repo.mkdir()

    def git(*argv):
        return subprocess.check_output(
            ["git", "-C", str(repo), *argv],
            text=True,
            stderr=subprocess.PIPE,
        ).strip()

    git("init", "--quiet")
    git("config", "user.name", "Evidence Test")
    git("config", "user.email", "evidence-test@example.invalid")
    formal = repo / "tools/formal/verify.py"
    formal.parent.mkdir(parents=True)
    formal.write_text("SOURCE_FILES = ('tools/formal/verify.py', 'old.lean')\n")
    git("add", ".")
    git("commit", "--quiet", "-m", "Old Formal input declaration")
    original = git("rev-parse", "HEAD")
    formal.write_text("SOURCE_FILES = ('tools/formal/verify.py', 'new.lean')\n")
    git("add", ".")
    git("commit", "--quiet", "-m", "Changed Formal input declaration")
    newer = git("rev-parse", "HEAD")
    git("replace", original, newer)
    assert "new.lean" in git("show", original + ":tools/formal/verify.py")
    assert module._formal_declared_files(repo, original) == (
        "tools/formal/verify.py",
        "old.lean",
    )


def test_unpushed_candidate_github_unknown_does_not_erase_original_readset(
    monkeypatch,
):
    import subprocess

    monkeypatch.setattr(
        module,
        "decide",
        Mock(side_effect=subprocess.CalledProcessError(1, "gh api")),
    )
    original = {
        "standing": "UNCHANGED_DECLARED_SOURCE_INPUTS",
        "proofReuseAdmissible": False,
        "declaredSourceReadsetComparisonComplete": True,
    }
    monkeypatch.setattr(
        module,
        "declared_formal_source_delta",
        Mock(return_value=original),
    )
    result = module.decide_with_optional_formal_source_delta(
        repo=module.DEFAULT_REPOSITORY,
        current_sha=CURRENT,
        prior_sha=PREVIOUS,
        check_name="root-verification",
        include_formal_source_delta=True,
        github=provider(),
    )
    assert result["disposition"] == "UNKNOWN_CURRENT_CHECK_PROVIDER"
    assert result["existingCheckReceiptReusable"] is False
    assert result["proofReuseAdmissible"] is False
    assert result["formalDeclaredSourceDelta"] is original
    assert result["formalDeclaredSourceDelta"]["standing"] == (
        "UNCHANGED_DECLARED_SOURCE_INPUTS"
    )
