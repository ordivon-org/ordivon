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
        lambda repo, *args: old_declaration if PREVIOUS in args[1] else new_declaration,
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
        lambda repo, *args: old if PREVIOUS in args[1] else new,
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
