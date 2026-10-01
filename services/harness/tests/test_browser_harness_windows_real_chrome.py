from __future__ import annotations

import json
from pathlib import Path
import sys
from types import SimpleNamespace
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts import browser_harness_windows_real_chrome as W


def _proc(value, rc=0):
    return SimpleNamespace(returncode=rc, stdout=json.dumps(value), stderr="")


def test_ready_when_chrome_consent_and_exact_harness_exist():
    value = {
        "browserHarnessPresent": True,
        "chromeRunning": True,
        "chromeVersion": "154.0.8037.58",
        "devToolsActivePortPresent": True,
        "doctorExitCode": 0,
        "doctor": {
            "version": "0.1.13",
            "healthy": True,
            "daemon": {"alive": True, "browser_ready": True},
        },
    }
    with (
        mock.patch.object(W, "WINDOWS_POWERSHELL", mock.Mock(is_file=mock.Mock(return_value=True))),
        mock.patch.object(W, "BROWSER_HARNESS_WSL", mock.Mock(is_file=mock.Mock(return_value=True))),
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
        "doctorExitCode": 1,
        "doctor": {
            "version": "0.1.13",
            "healthy": False,
            "daemon": {"alive": False, "browser_ready": False},
        },
    }
    with (
        mock.patch.object(W, "WINDOWS_POWERSHELL", mock.Mock(is_file=mock.Mock(return_value=True))),
        mock.patch.object(W, "BROWSER_HARNESS_WSL", mock.Mock(is_file=mock.Mock(return_value=True))),
        mock.patch.object(W.subprocess, "run", return_value=_proc(value)),
    ):
        got = W._probe()
    assert got["ready"] is False
    assert got["standing"] == "HUMAN_REMOTE_DEBUGGING_REQUIRED"


def test_exact_version_is_fenced():
    value = {
        "browserHarnessPresent": True,
        "chromeRunning": True,
        "chromeVersion": "154",
        "devToolsActivePortPresent": True,
        "doctorExitCode": 0,
        "doctor": {
            "version": "0.1.14",
            "healthy": True,
            "daemon": {"alive": True, "browser_ready": True},
        },
    }
    with (
        mock.patch.object(W, "WINDOWS_POWERSHELL", mock.Mock(is_file=mock.Mock(return_value=True))),
        mock.patch.object(W, "BROWSER_HARNESS_WSL", mock.Mock(is_file=mock.Mock(return_value=True))),
        mock.patch.object(W.subprocess, "run", return_value=_proc(value)),
    ):
        got = W._probe()
    assert got["ready"] is False
    assert got["standing"] == "BROWSER_HARNESS_VERSION_MISMATCH"
