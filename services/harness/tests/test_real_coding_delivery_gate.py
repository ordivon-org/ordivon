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


def _git(repo: Path, *args: str) -> str:
    command = ["/usr/bin/git", "-C", str(repo), *args]
    result = subprocess.run(command, capture_output=True, text=True, check=True, timeout=10)
    return result.stdout.strip()


def _consumer_repo(tmp_path: Path, source: Path) -> tuple[Path, str]:
    repo = tmp_path / "independent-consumer-repository"
    repo.mkdir()
    _git(repo, "init", "-q")
    shutil.copyfile(source, repo / "feature_flags.py")
    _git(repo, "add", "feature_flags.py")
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
