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
    assert "Ordivon-DDrive-Compact-Authorize" in text
    assert "Start-ScheduledTask" in text


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
