from __future__ import annotations

import json
from pathlib import Path
import sys
from types import SimpleNamespace
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts import browser_harness_windows_real_chrome as W  # noqa: E402


def _proc(value, rc=0):
    return SimpleNamespace(returncode=rc, stdout=json.dumps(value), stderr="")


def _owner_status():
    return {
        "healthy": True,
        "packages": {"exact": True, "browserHarnessVersion": "0.1.13"},
        "python": {
            "providerVenvWindows": (
                r"C:\Users\test\AppData\Local\Ordivon\External\jev-ultrafast"
                r"\rev\.venv\Scripts\python.exe"
            )
        },
    }


def test_ready_when_chrome_consent_and_exact_harness_exist():
    value = {
        "browserHarnessPresent": True,
        "chromeRunning": True,
        "chromeVersion": "154.0.8037.58",
        "devToolsActivePortPresent": True,
        "cdpPort": 9222,
        "cdpEndpointReady": True,
        "doctorExitCode": 0,
        "doctor": {
            "version": "0.1.13",
            "healthy": True,
            "daemon": {"alive": True, "browser_ready": True},
        },
    }
    with (
        mock.patch.object(W, "_workstation_status", return_value=_owner_status()),
        mock.patch.object(W, "WINDOWS_POWERSHELL", mock.Mock(is_file=mock.Mock(return_value=True))),
        mock.patch.object(W.subprocess, "run", return_value=_proc(value)),
    ):
        got = W._probe()
    assert got["ready"] is True
    assert got["standing"] == "READY"
    assert got["executionTarget"] == "windows_native"
    assert got["windowsAuthority"] == "active_user"


def test_consent_missing_is_human_gate_not_auto_mutation():
    value = {
        "browserHarnessPresent": True,
        "chromeRunning": True,
        "chromeVersion": "154.0.8037.58",
        "devToolsActivePortPresent": False,
        "cdpPort": None,
        "cdpEndpointReady": False,
        "doctorExitCode": 1,
        "doctor": {
            "version": "0.1.13",
            "healthy": False,
            "daemon": {"alive": False, "browser_ready": False},
        },
    }
    with (
        mock.patch.object(W, "_workstation_status", return_value=_owner_status()),
        mock.patch.object(W, "WINDOWS_POWERSHELL", mock.Mock(is_file=mock.Mock(return_value=True))),
        mock.patch.object(W.subprocess, "run", return_value=_proc(value)),
    ):
        got = W._probe()
    assert got["ready"] is False
    assert got["standing"] == "HUMAN_REMOTE_DEBUGGING_REQUIRED"


def test_stale_devtools_active_port_is_not_ready():
    value = {
        "browserHarnessPresent": True,
        "chromeRunning": True,
        "chromeVersion": "154.0.8037.58",
        "devToolsActivePortPresent": True,
        "cdpPort": 9222,
        "cdpEndpointReady": False,
        "doctorExitCode": 1,
        "doctor": {
            "version": "0.1.13",
            "healthy": False,
            "daemon": {"alive": False, "browser_ready": False},
        },
    }
    with (
        mock.patch.object(W, "_workstation_status", return_value=_owner_status()),
        mock.patch.object(W, "WINDOWS_POWERSHELL", mock.Mock(is_file=mock.Mock(return_value=True))),
        mock.patch.object(W.subprocess, "run", return_value=_proc(value)),
    ):
        got = W._probe()
    assert got["ready"] is False
    assert got["standing"] == "DEVTOOLS_ENDPOINT_UNAVAILABLE"
    assert got["humanRemoteDebuggingConsentPresent"] is True
    assert got["cdpEndpointReady"] is False


def test_workstation_status_timeout_is_typed_hold():
    command = mock.Mock()
    command.is_file.return_value = True
    with mock.patch.object(
        W.subprocess,
        "run",
        side_effect=W.subprocess.TimeoutExpired(["status"], 12),
    ):
        status = W._workstation_status(command)
    assert status == {"healthy": False, "standing": "WORKSTATION_STATUS_TIMEOUT"}


def test_probe_preserves_workstation_timeout_standing():
    with mock.patch.object(
        W,
        "_workstation_status",
        return_value={"healthy": False, "standing": "WORKSTATION_STATUS_TIMEOUT"},
    ):
        got = W._probe()
    assert got["ready"] is False
    assert got["standing"] == "WORKSTATION_STATUS_TIMEOUT"


def test_workstation_owner_must_be_exact():
    bad = _owner_status()
    bad["packages"]["exact"] = False
    with mock.patch.object(W, "_workstation_status", return_value=bad):
        got = W._probe()
    assert got["ready"] is False
    assert got["standing"] == "WORKSTATION_PROVIDER_UNHEALTHY"


def test_exact_version_is_fenced():
    value = {
        "browserHarnessPresent": True,
        "chromeRunning": True,
        "chromeVersion": "154",
        "devToolsActivePortPresent": True,
        "cdpPort": 9222,
        "cdpEndpointReady": True,
        "doctorExitCode": 0,
        "doctor": {
            "version": "0.1.14",
            "healthy": True,
            "daemon": {"alive": True, "browser_ready": True},
        },
    }
    with (
        mock.patch.object(W, "_workstation_status", return_value=_owner_status()),
        mock.patch.object(W, "WINDOWS_POWERSHELL", mock.Mock(is_file=mock.Mock(return_value=True))),
        mock.patch.object(W.subprocess, "run", return_value=_proc(value)),
    ):
        got = W._probe()
    assert got["ready"] is False
    assert got["standing"] == "BROWSER_HARNESS_VERSION_MISMATCH"
