"""Red/green: QA-only cannot be promoted into durable consumer delivery.

These local Git fixtures test the verifier, not real Agent delivery or Runtime HELD.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path
import shutil
import subprocess

import pytest

ROOT = Path(__file__).resolve().parents[1]
TASK = ROOT / "evals/harness-edit-addressing-002"
SPEC = importlib.util.spec_from_file_location("independent_delivery_gate", TASK / "delivery_gate.py")
assert SPEC is not None and SPEC.loader is not None
GATE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GATE)
ORACLE = TASK / "oracle/feature_flags.py"
INVALID = TASK / "known-invalid/both-enabled.py"
MULTIREGION_TASK = ROOT / "evals/harness-edit-multiregion-003"
MULTIREGION_TASK_ID = "HARNESS-EDIT-MULTIREGION-003"
MULTIREGION_ORACLE = MULTIREGION_TASK / "oracle/pipeline.py"
MULTIREGION_COLLATERAL = MULTIREGION_TASK / "known-invalid/collateral.py"


def _git(repo: Path, *args: str) -> str:
    command = ["/usr/bin/git", "-C", str(repo), *args]
    result = subprocess.run(command, capture_output=True, text=True, check=True, timeout=10)
    return result.stdout.strip()


def _consumer_repo(
    tmp_path: Path, source: Path, filename: str = "feature_flags.py",
) -> tuple[Path, str]:
    repo = tmp_path / "independent-consumer-repository"
    repo.mkdir()
    _git(repo, "init", "-q")
    shutil.copyfile(source, repo / filename)
    _git(repo, "add", filename)
    _git(
        repo, "-c", "user.name=Consumer QA", "-c", "user.email=consumer@example.invalid",
        "commit", "-q", "-m", "deliver independently checked source",
    )
    return repo, _git(repo, "rev-parse", "HEAD")


def test_hidden_domain_qa_and_independent_git_delivery_pass(tmp_path: Path) -> None:
    candidate = tmp_path / "candidate.py"
    shutil.copyfile(ORACLE, candidate)
    repo, commit = _consumer_repo(tmp_path, candidate)
    result = GATE.qualify(candidate, repo, commit)
    assert result["domainQA"] == "passed"
    assert result["consumerGitByteReadback"] == "verified"
    assert result["consumerGitByteReadbackQualified"] is True
    assert result["finalUserDeliveryProven"] is False
    assert result["userAcknowledgement"] == "UNKNOWN"
    assert result["domainQATrials"] == 3


def test_public_pass_but_hidden_fail_cannot_deliver(tmp_path: Path) -> None:
    candidate = tmp_path / "candidate.py"
    shutil.copyfile(INVALID, candidate)
    repo, commit = _consumer_repo(tmp_path, candidate)
    with pytest.raises(GATE.DeliveryGateError, match="public/hidden"):
        GATE.qualify(candidate, repo, commit)


def test_domain_qa_pass_with_unpersisted_candidate_is_rejected(tmp_path: Path) -> None:
    candidate = tmp_path / "candidate.py"
    shutil.copyfile(ORACLE, candidate)
    repo, commit = _consumer_repo(tmp_path, INVALID)
    with pytest.raises(GATE.DeliveryGateError, match="does not match"):
        GATE.qualify(candidate, repo, commit)


def test_mutable_git_branch_name_cannot_replace_exact_commit(tmp_path: Path) -> None:
    candidate = tmp_path / "candidate.py"
    shutil.copyfile(ORACLE, candidate)
    repo, _ = _consumer_repo(tmp_path, candidate)
    with pytest.raises(GATE.DeliveryGateError, match="immutable full Git commit"):
        GATE.qualify(candidate, repo, "HEAD")


def test_symlink_candidate_is_not_accepted(tmp_path: Path) -> None:
    candidate = tmp_path / "candidate.py"
    shutil.copyfile(ORACLE, candidate)
    link = tmp_path / "link.py"
    link.symlink_to(candidate)
    repo, commit = _consumer_repo(tmp_path, candidate)
    with pytest.raises(GATE.DeliveryGateError, match="ordinary source file"):
        GATE.qualify(link, repo, commit)


def test_agent_tree_cannot_self_certify_as_external_consumer(tmp_path: Path) -> None:
    candidate = tmp_path / "candidate.py"
    shutil.copyfile(ORACLE, candidate)
    with pytest.raises(GATE.DeliveryGateError, match="same tree"):
        GATE.qualify(candidate, tmp_path, "a" * 40)


def test_multiregion_two_separated_edits_are_qa_passed_and_git_readable(tmp_path: Path) -> None:
    candidate = tmp_path / "candidate.py"
    shutil.copyfile(MULTIREGION_ORACLE, candidate)
    repo, commit = _consumer_repo(tmp_path, candidate, "pipeline.py")
    result = GATE.qualify(candidate, repo, commit, task_id=MULTIREGION_TASK_ID)
    assert result["taskId"] == MULTIREGION_TASK_ID
    assert result["consumerPath"] == "pipeline.py"
    assert result["domainQATrials"] == 3
    assert result["consumerGitByteReadbackQualified"] is True
    assert result["finalUserDeliveryProven"] is False
    assert result["userAcknowledgement"] == "UNKNOWN"


def test_multiregion_public_pass_hidden_collateral_fail_is_not_delivery(tmp_path: Path) -> None:
    candidate = tmp_path / "candidate.py"
    shutil.copyfile(MULTIREGION_COLLATERAL, candidate)
    repo, commit = _consumer_repo(tmp_path, candidate, "pipeline.py")
    with pytest.raises(GATE.DeliveryGateError, match="public/hidden"):
        GATE.qualify(candidate, repo, commit, task_id=MULTIREGION_TASK_ID)


@pytest.mark.parametrize("known_invalid", ["timeout-only.py", "retry-only.py"])
def test_multiregion_missing_one_edit_is_not_delivery(
    tmp_path: Path, known_invalid: str,
) -> None:
    candidate = tmp_path / "candidate.py"
    shutil.copyfile(MULTIREGION_TASK / "known-invalid" / known_invalid, candidate)
    repo, commit = _consumer_repo(tmp_path, candidate, "pipeline.py")
    with pytest.raises(GATE.DeliveryGateError, match="public/hidden"):
        GATE.qualify(candidate, repo, commit, task_id=MULTIREGION_TASK_ID)


def test_multiregion_qa_correct_but_git_commit_stale_is_not_delivery(tmp_path: Path) -> None:
    candidate = tmp_path / "candidate.py"
    shutil.copyfile(MULTIREGION_ORACLE, candidate)
    repo, commit = _consumer_repo(tmp_path, MULTIREGION_COLLATERAL, "pipeline.py")
    with pytest.raises(GATE.DeliveryGateError, match="does not match"):
        GATE.qualify(candidate, repo, commit, task_id=MULTIREGION_TASK_ID)


def test_multiregion_wrong_delivered_source_target_is_rejected(tmp_path: Path) -> None:
    candidate = tmp_path / "candidate.py"
    shutil.copyfile(MULTIREGION_ORACLE, candidate)
    repo, commit = _consumer_repo(tmp_path, candidate, "pipeline.py")
    with pytest.raises(GATE.DeliveryGateError, match="task's edited source file"):
        GATE.qualify(
            candidate, repo, commit, delivered_path="feature_flags.py",
            task_id=MULTIREGION_TASK_ID,
        )


def test_unknown_task_id_does_not_load_arbitrary_qa(tmp_path: Path) -> None:
    candidate = tmp_path / "candidate.py"
    shutil.copyfile(MULTIREGION_ORACLE, candidate)
    repo, commit = _consumer_repo(tmp_path, candidate, "pipeline.py")
    with pytest.raises(GATE.DeliveryGateError, match="unsupported"):
        GATE.qualify(candidate, repo, commit, task_id="../../evil")


def test_candidate_mutating_after_last_qa_must_not_be_qualified(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The tested bytes must be those actually recovered from consumer Git."""
    candidate = tmp_path / "candidate.py"
    shutil.copyfile(ORACLE, candidate)
    # The consumer has a stale/collateral revision B, not QA-passed oracle A.
    repo, commit = _consumer_repo(tmp_path, INVALID)
    qa = GATE._task_qa()
    original = qa.run_candidate
    calls = 0

    def mutate_after_last_original_qa(label: str, source: Path) -> dict:
        nonlocal calls
        outcome = original(label, source)
        calls += 1
        if calls == qa.validate_task()["reproducibility"]["cleanRebuildTrials"]:
            # Simulate an Agent edit interleaving after QA success but before
            # the gate binds Git delivery bytes. No threads or sleeps.
            shutil.copyfile(INVALID, candidate)
        return outcome

    monkeypatch.setattr(qa, "run_candidate", mutate_after_last_original_qa)
    monkeypatch.setattr(GATE, "_task_qa", lambda task_id=GATE.TASK_ID: qa)
    with pytest.raises(GATE.DeliveryGateError, match="candidate changed during"):
        GATE.qualify(candidate, repo, commit)


def _original_and_consumer_git_roots(tmp_path: Path) -> tuple[Path, str, Path]:
    """Two physically distinct disposable Git repositories; source baseline is fixed."""
    original = tmp_path / "original-workspace"
    original.mkdir()
    _git(original, "init", "-q")
    (original / ".gitignore").write_text("ignored-unique.bin\n")
    (original / "feature_flags.py").write_text(
        "def alpha_enabled():\n    return False\n"
    )
    _git(original, "add", ".gitignore", "feature_flags.py")
    _git(
        original, "-c", "user.name=Origin", "-c", "user.email=origin@example.invalid",
        "commit", "-q", "-m", "original baseline",
    )
    baseline = _git(original, "rev-parse", "HEAD")
    (original / "feature_flags.py").write_bytes(ORACLE.read_bytes())
    (original / "unique result with spaces.bin").write_bytes(b"original\0unique\n")
    recipient = tmp_path / "actual-consumer-git"
    recipient.mkdir()
    _git(recipient, "init", "-q")
    return original, baseline, recipient


def _recipient_commit(repo: Path, original: Path, *names: str) -> str:
    for name in names:
        target = repo / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(original / name, target)
    _git(repo, "add", "-A")
    _git(
        repo, "-c", "user.name=Receiver",
        "-c", "user.email=receiver@example.invalid",
        "commit", "-q", "-m", "original receiver contents",
    )
    return _git(repo, "rev-parse", "HEAD")


def test_git_origin_scope_requires_every_changed_and_untracked_byte(tmp_path: Path) -> None:
    origin, baseline, consumer = _original_and_consumer_git_roots(tmp_path)
    partial = _recipient_commit(consumer, origin, "feature_flags.py")
    with pytest.raises(GATE.DeliveryGateError, match="missing|omitted"):
        GATE.qualify_original_git_output_scope(origin, baseline, consumer, partial)
    # QA and selected source byte readback may pass while the untracked output
    # is the only surviving copy in the original Workspace.
    assert GATE.qualify(origin / "feature_flags.py", consumer, partial)[
        "consumerGitByteReadbackQualified"
    ] is True
    complete = _recipient_commit(
        consumer, origin, "feature_flags.py", "unique result with spaces.bin",
    )
    value = GATE.qualify_original_git_output_scope(
        origin, baseline, consumer, complete,
    )
    assert value["completeOriginalOutputSetReadbackQualified"] is True
    assert value["originalOutputSetStanding"] == "verified_test_scope"
    assert set(value["originalOutputPaths"]) == {
        "feature_flags.py", "unique result with spaces.bin",
    }
    assert value["finalUserDeliveryProven"] is False
    assert value["workspaceSourceFenced"] is False
    qualified = GATE.qualify(
        origin / "feature_flags.py", consumer, complete,
        original_workspace_repo=origin, original_base_commit=baseline,
    )
    assert qualified["completeOriginalOutputSetReadbackQualified"] is True
    assert qualified["domainQA"] == "passed"


def test_git_origin_scope_ignored_unique_output_requires_explicit_domain_decision(
    tmp_path: Path,
) -> None:
    origin, baseline, consumer = _original_and_consumer_git_roots(tmp_path)
    (origin / "ignored-unique.bin").write_bytes(b"sole-copy-ignored")
    commit = _recipient_commit(
        consumer, origin, "feature_flags.py", "unique result with spaces.bin",
        "ignored-unique.bin",
    )
    # Even copying it must not imply that it is the full output set: the
    # original ignored/worktree source needs a trusted retention decision.
    with pytest.raises(GATE.DeliveryGateError, match="ignored|UNKNOWN"):
        GATE.qualify_original_git_output_scope(origin, baseline, consumer, commit)


def test_git_origin_scope_rejects_source_mutation_after_consumer_commit(
    tmp_path: Path,
) -> None:
    origin, baseline, consumer = _original_and_consumer_git_roots(tmp_path)
    commit = _recipient_commit(
        consumer, origin, "feature_flags.py", "unique result with spaces.bin",
    )
    (origin / "unique result with spaces.bin").write_bytes(b"changed-source")
    with pytest.raises(GATE.DeliveryGateError, match="mismatch|does not match"):
        GATE.qualify_original_git_output_scope(origin, baseline, consumer, commit)


def test_git_origin_scope_rejects_symlink_untracked_or_deleted_original(
    tmp_path: Path,
) -> None:
    origin, baseline, consumer = _original_and_consumer_git_roots(tmp_path)
    commit = _recipient_commit(
        consumer, origin, "feature_flags.py", "unique result with spaces.bin",
    )
    (origin / "unique result with spaces.bin").unlink()
    (origin / "unique result with spaces.bin").symlink_to(
        tmp_path / "outside-root",
    )
    with pytest.raises(GATE.DeliveryGateError, match="symlink|ordinary"):
        GATE.qualify_original_git_output_scope(origin, baseline, consumer, commit)
    (origin / "unique result with spaces.bin").unlink()
    (origin / "feature_flags.py").unlink()
    with pytest.raises(GATE.DeliveryGateError, match="deleted|removed"):
        GATE.qualify_original_git_output_scope(origin, baseline, consumer, commit)


def test_git_origin_scope_without_provenance_never_qualifies_entire_run(
    tmp_path: Path,
) -> None:
    origin, baseline, consumer = _original_and_consumer_git_roots(tmp_path)
    commit = _recipient_commit(
        consumer, origin, "feature_flags.py", "unique result with spaces.bin",
    )
    value = GATE.qualify(origin / "feature_flags.py", consumer, commit)
    assert value["consumerGitByteReadbackQualified"] is True
    assert value["completeOriginalOutputSetReadbackQualified"] is False
    assert value["originalOutputSetStanding"] == "UNKNOWN"
    with pytest.raises(GATE.DeliveryGateError, match="both|baseline"):
        GATE.qualify(
            origin / "feature_flags.py", consumer, commit,
            original_workspace_repo=origin,
        )
    with pytest.raises(GATE.DeliveryGateError, match="immutable full Git"):
        GATE.qualify_original_git_output_scope(origin, "HEAD", consumer, commit)
