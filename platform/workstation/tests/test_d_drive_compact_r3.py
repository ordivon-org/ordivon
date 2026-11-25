from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROVIDER = ROOT / "workstation/providers/d_drive_compact"
GATE = PROVIDER / "d_drive_compact_gate_r3.py"
CONTROLLER = PROVIDER / "DDriveOfflineCompactR3.ps1"
AUTHORIZER = PROVIDER / "DDriveCompactAuthorizeR4.ps1"
RUNNER = PROVIDER / "DDriveCompactRunR3.ps1"


def load_gate():
    spec = importlib.util.spec_from_file_location("d_drive_compact_gate_r3", GATE)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_gate_uses_lightweight_status_for_drain_and_full_doctor_once_after_quiescence():
    text = GATE.read_text(encoding="utf-8")
    assert '"registry-status"' in text
    assert "time.monotonic()" in text
    assert "seq 1 900" not in text
    assert text.count("full_doctor(") == 2  # definition + exactly one call site
    assert text.index("doctor = full_doctor") > text.index("drain_deadline =")


def test_quiescent_requires_all_owner_native_counts_zero():
    gate = load_gate()
    zero = {
        "activeReservations": 0,
        "heldReservations": 0,
        "jobsActive": 0,
        "nonterminalAttempts": 0,
        "recoveryRequired": 0,
    }
    assert gate.is_quiescent(zero)
    for key in zero:
        sample = dict(zero)
        sample[key] = 1
        assert not gate.is_quiescent(sample)


def test_pause_pressure_restores_only_previously_active_timer_and_never_replays_service(monkeypatch):
    gate = load_gate()
    calls = []
    snapshots = iter((
        {"timerState": "active", "timerEnablement": "enabled", "serviceState": "active"},
        {"timerState": "active", "timerEnablement": "enabled", "serviceState": "inactive"},
    ))

    def fake_run(argv, *, timeout, check=False):
        calls.append((tuple(argv), timeout, check))
        return gate.subprocess.CompletedProcess(argv, 0, stdout="", stderr="")

    monotonic_values = iter((0.0, 0.0, 2.0))
    monkeypatch.setattr(gate, "run", fake_run)
    monkeypatch.setattr(gate, "pressure_snapshot", lambda: next(snapshots))
    monkeypatch.setattr(gate, "service_state", lambda unit: "activating" if unit == gate.PRESSURE_SERVICE else "inactive")
    monkeypatch.setattr(gate.time, "monotonic", lambda: next(monotonic_values))
    monkeypatch.setattr(gate.time, "sleep", lambda _seconds: None)

    try:
        gate.pause_pressure(1.0)
    except gate.GateFailure as exc:
        assert exc.reason_code == "PRESSURE_RECLAIM_DID_NOT_QUIESCE"
    else:
        raise AssertionError("pause_pressure should fail when pressure service never quiesces")

    assert calls[0][0] == ("/usr/bin/systemctl", "stop", gate.PRESSURE_TIMER)
    assert calls[-1][0] == ("/usr/bin/systemctl", "start", gate.PRESSURE_TIMER)
    assert all(call[0] != ("/usr/bin/systemctl", "start", "--no-block", gate.PRESSURE_SERVICE) for call in calls)


def test_restore_pressure_leaves_disabled_inactive_policy_untouched(monkeypatch):
    gate = load_gate()
    calls = []
    monkeypatch.setattr(gate, "run", lambda argv, *, timeout, check=False: calls.append(tuple(argv)))
    monkeypatch.setattr(gate, "pressure_snapshot", lambda: {"timerState": "inactive", "timerEnablement": "disabled", "serviceState": "inactive"})
    observed = gate.restore_pressure({"timerState": "inactive", "timerEnablement": "disabled", "serviceState": "inactive"})
    assert observed["timerState"] == "inactive"
    assert observed["timerEnablement"] == "disabled"
    assert calls == []


def test_gate_has_explicit_terminal_reason_codes_and_atomic_receipts():
    text = GATE.read_text(encoding="utf-8")
    for code in (
        "DRAIN_DEADLINE_EXCEEDED",
        "STATUS_PROBE_FAILED",
        "INTEGRITY_REJECTED",
        "FSTRIM_FAILED",
        "HANDOFF_BINDING_MISMATCH",
        "READY_HOLD_EXPIRED",
        "UNEXPECTED_GATE_FAILURE",
    ):
        assert code in text
    assert "os.replace(tmp, path)" in text
    assert "os.fsync(f.fileno())" in text
    assert 'open("wb")' in text


def test_windows_controller_submits_systemd_owner_instead_of_holding_wsl_transport():
    text = CONTROLLER.read_text(encoding="utf-8")
    assert "/usr/bin/systemd-run" in text
    assert "Start-Process" not in text
    assert "--shutdown" in text
    assert "--terminate" not in text
    assert "Get-VHD -Path $vhdPath" in text
    assert "if($vhd.Attached)" in text
    assert "Test-VhdExclusiveOpen" in text
    assert "Optimize-VHD -Path $vhdPath -Mode Full" in text



def test_windows_r3_receipt_distinguishes_sparse_allocated_bytes_from_file_size() -> None:
    """Do not conflate a sparse VHDX logical size with NTFS allocated bytes."""
    text = CONTROLLER.read_text(encoding="utf-8")
    assert "GetCompressedFileSizeW" in text
    assert "vhdAllocatedBytes" in text
    assert "reclaimedAllocatedVhdBytes" in text
    assert "$before.vhdAllocatedBytes-$afterCompact.vhdAllocatedBytes" in text
    assert "reclaimedVolumeBytes" in text
    assert "Optimize-VHD -Path $vhdPath -Mode Full" in text


def test_windows_recovery_preserves_pressure_policy_instead_of_enabling_it():
    text = CONTROLLER.read_text(encoding="utf-8")
    assert "enable --now $pressureTimer" not in text
    assert "start --no-block $pressureService" not in text
    assert "pressureTimerEnablementExpected" in text
    assert "Start-ControlPlane $r.pressureBefore" in text


def test_windows_controller_builds_systemd_unit_as_one_argument_and_separates_executable():
    text = CONTROLLER.read_text(encoding="utf-8")
    assert "$unitArg = ('--unit={0}' -f $unitName)" in text
    assert "'/usr/bin/systemd-run',$unitArg,'--collect','--property=Type=exec','--','/usr/bin/python3'" in text
    assert "'--unit='+$unitName" not in text
    assert "$ErrorActionPreference='Continue'" in text
    assert "gate-submit.json" in text
    assert 'Gate unit left active state before READY' not in text
    assert 'Gate unit is not active while READY is consumed' not in text
    assert 'Gate unit lost before offline handoff' not in text


def test_authorization_binds_exact_maintenance_ready_and_code_digests():
    text = AUTHORIZER.read_text(encoding="utf-8")
    for token in (
        "maintenanceId",
        "readySha256",
        "gateSha256",
        "controllerSha256",
        "expiresAtUtc",
        "compactAuthorized",
    ):
        assert token in text
    assert "systemctl is-active" not in text
    assert "READY_HELD" in text
    assert "gateStateSha256" in text
    assert "readyHoldSeconds" in text


def test_runner_uses_unique_transaction_and_separate_authorizer_task():
    text = RUNNER.read_text(encoding="utf-8")
    assert "NewGuid" in text
    assert "active-request.json" in text
    assert "expiresAtUnixMs" in text
    assert "Ordivon-DDrive-Compact-Authorize" in text
    assert "Start-ScheduledTask" in text



def test_windows_json_receipts_are_utf8_without_bom():
    for path in (CONTROLLER, AUTHORIZER, RUNNER):
        text = path.read_text(encoding="utf-8")
        assert "System.Text.UTF8Encoding($false)" in text
        assert "[System.IO.File]::Open" in text
        assert "$stream.Flush($true)" in text
        atomic_line = next(line for line in text.splitlines() if line.startswith("function Atomic-Json"))
        assert "Set-Content" not in atomic_line


def test_runner_rejects_stale_request_and_rebinds_authorizer_instance():
    text = RUNNER.read_text(encoding="utf-8")
    assert "active-request already exists before new R3 transaction" in text
    assert "Get-ScheduledTask -TaskName $authorizerTask" in text
    assert "Stop-ScheduledTask -TaskName $authorizerTask" in text
    assert "stale authorizer instance did not stop" in text
    assert "$authBefore=(Get-ScheduledTaskInfo -TaskName $authorizerTask).LastRunTime" in text
    assert "fresh authorizer instance did not start" in text

def test_architecture_doc_forbids_r2_failure_modes():
    text = (ROOT / "docs/D_DRIVE_OFFLINE_MAINTENANCE_R3.md").read_text(encoding="utf-8")
    assert "full Runtime Doctor polling" in text
    assert "systemd transient service" in text
    assert "monotonic deadline" in text
    assert "temp + fsync + atomic replace" in text


def test_windows_json_receipts_are_bomless_durable_atomic_commits():
    for path in (CONTROLLER, AUTHORIZER, RUNNER):
        text = path.read_text(encoding="utf-8")
        assert "System.Text.UTF8Encoding($false)" in text
        assert "$stream.Flush($true)" in text
        assert "Move-Item -Force $tmp $Path" in text
        atomic = text.split("function Atomic-Json", 1)[1].split("}", 1)[0]
        assert "Set-Content" not in atomic


def test_windows_controller_only_recovers_after_offline_effect_ownership_begins():
    text = CONTROLLER.read_text(encoding="utf-8")
    assert "$offlineEffectStarted=$false" in text
    assert "$offlineEffectStarted=$true" in text
    assert "if($offlineEffectStarted)" in text
    assert "recoveryAttempted=$recoveryAttempted" in text
    assert text.index("$offlineEffectStarted=$true") < text.index("--shutdown")


def test_windows_recovery_does_not_shadow_powershell_host_variable():
    text = CONTROLLER.read_text(encoding="utf-8")
    assert "$host=" not in text
    assert "$hostState=" in text
    assert "host=$hostState" in text


def test_run_r3_suppresses_cross_agent_recovery_during_active_request():
    text = RUNNER.read_text(encoding="utf-8")
    assert "Ordivon WSL Control Plane Recovery" in text
    assert "Disable-ScheduledTask" in text
    assert "Stop-ScheduledTask" in text
    assert "Enable-ScheduledTask" in text
    assert "recoveryTaskSuppressed" in text
    assert text.index("Atomic-Json $request $req") < text.index("Disable-ScheduledTask")
    assert text.index("Enable-ScheduledTask") < text.index("Remove-Item -LiteralPath $request")


def test_legacy_gate_refuses_pg_runtime_before_pressure_or_trim(tmp_path, monkeypatch):
    """An old registry/lock cannot authorize the current PG runtime's shutdown."""
    import argparse
    import json

    gate = load_gate()
    monkeypatch.setattr(gate, "parse_args", lambda: argparse.Namespace(
        maintenance_id="synthetic-maintenance", unit_name="synthetic-gate",
        transaction_root=tmp_path, pressure_wait_seconds=1,
    ))
    monkeypatch.setattr(gate.signal, "signal", lambda *args: None)
    calls = []

    def run(argv, *, timeout, check=False):
        calls.append(tuple(argv))
        return gate.subprocess.CompletedProcess(argv, 0, stdout="123\n", stderr="")

    def forbidden_pressure(*args):
        calls.append(("PRESSURE_EFFECT",))
        raise AssertionError("legacy gate reached a physical effect")

    monkeypatch.setattr(gate, "run", run)
    monkeypatch.setattr(gate.os, "readlink", lambda path: "/usr/local/libexec/ordivon/ordivon-runtime-pg")
    monkeypatch.setattr(gate, "pause_pressure", forbidden_pressure)
    assert gate.main() == 42
    terminal = json.loads((tmp_path / "gate-terminal.json").read_text())
    assert terminal["reasonCode"] == "RUNTIME_AUTHORITY_UNSUPPORTED"
    assert terminal["phase"] == "AUTHORITY_PREFLIGHT"
    assert not (tmp_path / "ready.json").exists()
    assert all(call[0] == "/usr/bin/systemctl" and "show" in call for call in calls)


def test_legacy_authority_preflight_requires_stable_pid_and_real_carriers(tmp_path, monkeypatch):
    import pytest

    gate = load_gate()
    registry = tmp_path / "registry.sqlite3"
    lock = tmp_path / "admission.lock"
    registry.write_bytes(b"synthetic legacy identity")
    lock.write_bytes(b"")
    monkeypatch.setattr(gate, "REGISTRY_DB", registry)
    monkeypatch.setattr(gate, "ADMISSION_LOCK", lock)
    monkeypatch.setattr(gate.os, "readlink", lambda _: str(gate.LEGACY_RUNTIME_EXECUTABLE))

    def set_pids(*values):
        pids = iter(values)
        monkeypatch.setattr(gate, "run", lambda argv, **kwargs:
            gate.subprocess.CompletedProcess(argv, 0, stdout=next(pids), stderr=""))

    set_pids("123", "123")
    identity = gate.require_legacy_runtime_authority()
    assert identity == (123, (registry.stat().st_dev, registry.stat().st_ino),
                        (lock.stat().st_dev, lock.stat().st_ino))
    set_pids("123", "124")
    with pytest.raises(gate.GateFailure, match="changed during observation"):
        gate.require_legacy_runtime_authority()
    for invalid in ("0", "", "unknown"):
        set_pids(invalid)
        with pytest.raises(gate.GateFailure, match="MainPID"):
            gate.require_legacy_runtime_authority()
    lock.unlink()
    set_pids("123")
    with pytest.raises(gate.GateFailure) as caught:
        gate.require_legacy_runtime_authority()
    assert caught.value.reason_code == "RUNTIME_AUTHORITY_UNSUPPORTED"
    assert not lock.exists()


def test_quiescence_requires_complete_exact_nonnegative_integer_census():
    import pytest
    gate = load_gate()
    zero = {
        "activeReservations": 0,
        "heldReservations": 0,
        "jobsActive": 0,
        "nonterminalAttempts": 0,
        "recoveryRequired": 0,
    }
    assert gate.status_counts(zero) == zero
    assert gate.is_quiescent(zero)
    assert not gate.is_quiescent({})
    for key in zero:
        missing = dict(zero)
        del missing[key]
        assert not gate.is_quiescent(missing)
        with pytest.raises(ValueError):
            gate.status_counts(missing)
        for value in (False, "0", 0.0, None, -1):
            malformed = {**zero, key: value}
            assert not gate.is_quiescent(malformed)
            with pytest.raises(ValueError):
                gate.status_counts(malformed)


def test_doctor_requires_explicit_untruncated_empty_capacity_and_exact_counts(tmp_path, monkeypatch):
    import json

    import pytest

    gate = load_gate()
    valid = {
        "integrityCheck": "ok", "violationCount": 0,
        "summary": {
            "capacityHolders": [], "capacityHoldersTruncated": False,
            "recoveryRequiredAttempts": 0,
        },
    }

    def observe(payload):
        monkeypatch.setattr(gate, "run", lambda argv, **kwargs:
            gate.subprocess.CompletedProcess(argv, 0, stdout=json.dumps(payload), stderr=""))
        return gate.full_doctor(tmp_path / "doctor.json", 1)

    assert observe(valid) == valid
    for patch in ({"violationCount": False}, {"violationCount": "0"}):
        with pytest.raises(gate.GateFailure):
            observe({**valid, **patch})
    for key, value in (
        ("recoveryRequiredAttempts", False),
        ("recoveryRequiredAttempts", "0"),
        ("capacityHoldersTruncated", None),
        ("capacityHoldersTruncated", 0),
        ("capacityHoldersTruncated", True),
        ("capacityHolders", [{"id": "held"}]),
    ):
        with pytest.raises(gate.GateFailure):
            observe({**valid, "summary": {**valid["summary"], key: value}})
    summary = dict(valid["summary"])
    del summary["capacityHoldersTruncated"]
    with pytest.raises(gate.GateFailure):
        observe({**valid, "summary": summary})


def test_final_health_uses_same_complete_census_as_drain():
    gate = load_gate()
    valid = {key: 0 for key in (
        "activeReservations", "heldReservations", "jobsActive",
        "nonterminalAttempts", "recoveryRequired",
    )}
    assert gate.healthy_quiescent_runtime({"status": "healthy", "registry": valid})
    for key in valid:
        missing = dict(valid)
        del missing[key]
        for invalid in (missing, {**valid, key: 1}, {**valid, key: False}):
            assert not gate.healthy_quiescent_runtime({"status": "healthy", "registry": invalid})
    assert not gate.healthy_quiescent_runtime({"status": "unhealthy", "registry": valid})
