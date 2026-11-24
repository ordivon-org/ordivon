"""R44 physical release readiness: a systemd Type=simple start is not app ready.

This pure/monkeypatched subset catches the real production false-rollback
counterexample without actually restarting a service in CI.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path
from types import ModuleType

import pytest

PACKAGING = Path(__file__).resolve().parents[1] / "packaging"
SHA_OLD = "a" * 40
SHA_NEW = "b" * 40


@pytest.fixture
def qualified(monkeypatch: pytest.MonkeyPatch) -> ModuleType:
    monkeypatch.syspath_prepend(str(PACKAGING))
    spec = importlib.util.spec_from_file_location(
        "gateway_running_release", PACKAGING / "check_running_release.py"
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _native_fixtures(
    module: ModuleType, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> tuple[Path, dict[str, str]]:
    prefix = tmp_path / "gateway"
    old = prefix / "releases" / SHA_OLD
    new = prefix / "releases" / SHA_NEW
    old.mkdir(parents=True)
    new.mkdir(parents=True)
    (prefix / "current").symlink_to(new)
    proc = tmp_path / "proc"
    (proc / "123").mkdir(parents=True)
    (proc / "123" / "cwd").symlink_to(new)
    monkeypatch.setattr(module, "PREFIX", prefix)
    monkeypatch.setattr(module, "PROC_ROOT", proc)
    props = {
        "ActiveState": "active",
        "SubState": "running",
        "User": "ordivon-gateway",
        "MainPID": "123",
    }
    monkeypatch.setattr(module, "_systemctl_value", lambda prop: props[prop])
    return new, props


def test_type_simple_active_before_pid_is_not_readiness(
    qualified: ModuleType, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    new, props = _native_fixtures(qualified, tmp_path, monkeypatch)
    props["MainPID"] = "0"
    assert qualified._source_and_process(new, 122) == (False, None, "SYSTEMD_PID_NOT_OBSERVED")
    monkeypatch.setattr(
        qualified, "_local_health", lambda: pytest.fail("must not probe before PID")
    )
    assert qualified.observe(SHA_NEW, 122, timeout_seconds=0)["status"] == "NO_GO"


def test_live_symlink_without_restarted_process_is_not_readiness(
    qualified: ModuleType, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    new, _ = _native_fixtures(qualified, tmp_path, monkeypatch)
    (qualified.PROC_ROOT / "123" / "cwd").unlink()
    (qualified.PROC_ROOT / "123" / "cwd").symlink_to(qualified.PREFIX / "releases" / SHA_OLD)
    assert qualified._source_and_process(new, 122)[2] == ("PROCESS_STILL_RUNNING_OTHER_SOURCECUT")


def test_reusing_old_pid_after_restart_is_not_new_process(
    qualified: ModuleType, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    new, _ = _native_fixtures(qualified, tmp_path, monkeypatch)
    assert qualified._source_and_process(new, 123) == (
        False,
        123,
        "PREVIOUS_PROCESS_STILL_OWNING_SERVICE",
    )


def test_exact_expected_current_release_required(
    qualified: ModuleType, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    new, _ = _native_fixtures(qualified, tmp_path, monkeypatch)
    assert qualified._source_and_process(new, 122)[0]
    (qualified.PREFIX / "current").unlink()
    (qualified.PREFIX / "current").symlink_to(qualified.PREFIX / "releases" / SHA_OLD)
    assert qualified._source_and_process(new, 122)[2] == "EXPECTED_SOURCECUT_NOT_CURRENT"


def test_systemd_service_user_changed_blocks_readiness(
    qualified: ModuleType, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    new, props = _native_fixtures(qualified, tmp_path, monkeypatch)
    props["User"] = "root"
    assert qualified._source_and_process(new, 122)[2] == "GATEWAY_SERVICE_IDENTITY_DRIFT"


def test_real_readiness_waits_for_pid_then_http_health_then_deny(
    qualified: ModuleType, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _native_fixtures(qualified, tmp_path, monkeypatch)
    states = iter(
        [
            (False, None, "SYSTEMD_PID_NOT_OBSERVED"),
            (True, 123, "CURRENT_PROCESS_MATCHES_EXPECTED_RELEASE"),
            (True, 123, "CURRENT_PROCESS_MATCHES_EXPECTED_RELEASE"),
        ]
    )
    monkeypatch.setattr(qualified, "_source_and_process", lambda *_: next(states))
    monkeypatch.setattr(qualified, "_local_health", lambda: True)
    monkeypatch.setattr(qualified, "_local_anonymous_denied", lambda: True)
    monkeypatch.setattr(qualified.time, "sleep", lambda _: None)
    timings = iter([0, 0, 0, 0, 0])
    monkeypatch.setattr(qualified.time, "monotonic", lambda: next(timings, 0))
    result = qualified.observe(SHA_NEW, 122, timeout_seconds=10)
    assert result["status"] == "READY"
    assert result["observedMainPid"] == 123
    assert result["attempts"] == 2
    assert result["localAnonymousMcpDenied"]
    assert result["authenticatedExternalAgentConsumer"] == "UNVERIFIED"


def test_no_false_ready_when_anonymous_mcp_denial_missing(
    qualified: ModuleType, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _native_fixtures(qualified, tmp_path, monkeypatch)
    monkeypatch.setattr(qualified, "_local_health", lambda: True)
    monkeypatch.setattr(qualified, "_local_anonymous_denied", lambda: False)
    result = qualified.observe(SHA_NEW, 122, timeout_seconds=0)
    assert result["status"] == "NO_GO"
    assert result["reason"] == "LOCAL_ANONYMOUS_DENIAL_NOT_PROVEN"


def test_no_false_ready_if_process_changes_between_canaries(
    qualified: ModuleType, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _native_fixtures(qualified, tmp_path, monkeypatch)
    observations = iter(
        [
            (True, 123, "CURRENT_PROCESS_MATCHES_EXPECTED_RELEASE"),
            (True, 124, "CURRENT_PROCESS_MATCHES_EXPECTED_RELEASE"),
        ]
    )
    monkeypatch.setattr(qualified, "_source_and_process", lambda *_: next(observations))
    monkeypatch.setattr(qualified, "_local_health", lambda: True)
    monkeypatch.setattr(qualified, "_local_anonymous_denied", lambda: True)
    result = qualified.observe(SHA_NEW, 122, timeout_seconds=0)
    assert result["status"] == "NO_GO"
    assert result["reason"] == "PID_CHANGED_DURING_CANARY"


@pytest.mark.parametrize(
    ("sha", "timeout"), [("abc", 1), ("g" * 40, 1), (SHA_NEW, -1), (SHA_NEW, 61)]
)
def test_invalid_release_or_unbounded_poll_rejected(
    qualified: ModuleType, sha: str, timeout: float
) -> None:
    with pytest.raises(ValueError):
        qualified.observe(sha, None, timeout_seconds=timeout)
