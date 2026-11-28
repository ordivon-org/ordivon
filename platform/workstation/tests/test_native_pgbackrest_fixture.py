"""Finite lifecycle obligations and injected native command outcomes."""
from __future__ import annotations

import subprocess

import pytest
from native_pgbackrest_fixture import PrivatePostmasters, run_private


class NativeCommands:
    def __init__(self, outcomes):
        self.outcomes = list(outcomes)
        self.calls = []

    def __call__(self, *args, **kwargs):
        self.calls.append((args[2], args[-1]))
        action, outcome = self.outcomes.pop(0)
        assert args[-1] == action
        if isinstance(outcome, Exception):
            raise outcome
        if kwargs.get("check", True) and outcome:
            raise subprocess.CalledProcessError(outcome, args)
        return subprocess.CompletedProcess(args, outcome, "", "")


def fixture(tmp_path, outcomes):
    root = tmp_path / "private"
    root.mkdir()
    for name in ("primary", "other", "socket"):
        (root / name).mkdir()
    run = NativeCommands(outcomes)
    return root, PrivatePostmasters(root, run), run


def test_cleanup_requires_native_stopped_result(tmp_path):
    root, life, run = fixture(tmp_path, [
        ("start", 0), ("status", 0), ("stop", 0), ("status", 3),
    ])
    life.start(root / "primary", root / "socket", 12345)
    life.cleanup()
    assert not root.exists() and not life.attempts and not run.outcomes


def test_partial_start_is_recorded_before_dispatch(tmp_path):
    root, life, run = fixture(tmp_path, [
        ("start", subprocess.TimeoutExpired("pg_ctl", 45)),
        ("status", 0), ("stop", 0), ("status", 3),
    ])
    with pytest.raises(subprocess.TimeoutExpired):
        life.start(root / "primary", root / "socket", 12345)
    assert root / "primary" in life.attempts
    life.cleanup()
    assert not root.exists() and not run.outcomes


@pytest.mark.parametrize("status", [3, 4, 1])
def test_failed_start_without_qualified_stop_preserves_root(tmp_path, status):
    root, life, run = fixture(tmp_path, [("start", 1), ("status", status)])
    with pytest.raises(subprocess.CalledProcessError):
        life.start(root / "primary", root / "socket", 12345)
    with pytest.raises(ExceptionGroup, match="private fixture retained"):
        life.cleanup()
    assert root.exists() and root / "primary" in life.attempts and not run.outcomes


@pytest.mark.parametrize("status", [0, 4, 1])
def test_stop_success_alone_is_not_qualified(tmp_path, status):
    root, life, run = fixture(tmp_path, [
        ("start", 0), ("status", 0), ("stop", 0), ("status", status),
    ])
    life.start(root / "primary", root / "socket", 12345)
    with pytest.raises(ExceptionGroup, match="private fixture retained"):
        life.cleanup()
    assert root.exists() and root / "primary" in life.attempts and not run.outcomes


def test_absent_server_with_pid_file_is_not_qualified(tmp_path):
    root, life, run = fixture(tmp_path, [("start", 0), ("status", 3)])
    life.start(root / "primary", root / "socket", 12345)
    (root / "primary" / "postmaster.pid").write_text("123")
    with pytest.raises(ExceptionGroup, match="private fixture retained"):
        life.cleanup()
    assert root.exists() and not run.outcomes


def test_stop_failure_does_not_abandon_other_acquisitions(tmp_path):
    root, life, run = fixture(tmp_path, [
        ("start", 0), ("start", 0), ("status", 0), ("stop", 1),
        ("status", 0), ("stop", 0), ("status", 3),
    ])
    life.start(root / "primary", root / "socket", 12345)
    life.start(root / "other", root / "socket", 12346)
    with pytest.raises(ExceptionGroup, match="private fixture retained"):
        life.cleanup()
    assert root.exists() and set(life.attempts) == {root / "other"}
    assert not run.outcomes
    assert (root / "primary", "stop") in run.calls


def test_foreign_directory_rejected_before_dispatch(tmp_path):
    root, life, run = fixture(tmp_path, [])
    foreign = tmp_path / "foreign"
    foreign.mkdir()
    with pytest.raises(ValueError, match="owned fixture"):
        life.start(foreign, root / "socket", 12345)
    with pytest.raises(ValueError, match="not acquired"):
        life.stop(foreign)
    assert not run.calls and foreign.exists()


def test_sanitized_native_command_after_user_switch(monkeypatch):
    calls = []
    def capture(args, **kwargs):
        calls.append((args, kwargs))
        return subprocess.CompletedProcess(args, 0, "", "")
    monkeypatch.setenv("PGBACKREST_REPO1_PATH", "/not-a-fixture")
    monkeypatch.setenv("PGHOST", "not-a-fixture")
    monkeypatch.setattr(subprocess, "run", capture)
    run_private("/usr/bin/pgbackrest", "--config=/private/config", "info")
    args, kwargs = calls[0]
    assert args[:6] == ["sudo", "-u", "postgres", "/usr/bin/env", "-i", "PATH=/usr/bin:/bin"]
    assert args[8:] == ["/usr/bin/pgbackrest", "--config=/private/config", "info"]
    assert kwargs["check"] is True
