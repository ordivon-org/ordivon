"""Tests for Ordivon Verify CLI skeleton.

Covers: command dispatch, status mapping, JSON output, exit codes,
error handling, and checker integration (mocked).
"""

from __future__ import annotations

import json
import subprocess
import sys
from unittest.mock import MagicMock

from ordivon_verify import (
    run_check,
    determine_status,
    build_report,
    status_to_exit_code,
    parse_args,
    main,
)
from ordivon_verify.runner import CHECKER_SCRIPTS, ALL_CHECKS


# ── Unit: status_to_exit_code ────────────────────────────────────────────


def test_status_ready_exit_0():
    assert status_to_exit_code("READY") == 0


def test_status_blocked_exit_1():
    assert status_to_exit_code("BLOCKED") == 1


def test_status_degraded_exit_2():
    assert status_to_exit_code("DEGRADED") == 2


def test_status_needs_review_exit_2():
    assert status_to_exit_code("NEEDS_REVIEW") == 2


def test_status_unknown_exit_1():
    assert status_to_exit_code("UNKNOWN") == 1


# ── Unit: determine_status ───────────────────────────────────────────────


def test_determine_status_all_pass():
    results = [
        {"id": "receipts", "status": "PASS", "exit_code": 0},
        {"id": "debt", "status": "PASS", "exit_code": 0},
    ]
    assert determine_status(results) == "READY"


def test_determine_status_one_fail():
    results = [
        {"id": "receipts", "status": "PASS", "exit_code": 0},
        {"id": "debt", "status": "FAIL", "exit_code": 1},
    ]
    assert determine_status(results) == "BLOCKED"


def test_determine_status_all_fail():
    results = [
        {"id": "receipts", "status": "FAIL", "exit_code": 1},
        {"id": "debt", "status": "FAIL", "exit_code": 1},
    ]
    assert determine_status(results) == "BLOCKED"


# ── Unit: build_report ───────────────────────────────────────────────────


def test_build_report_json_fields():
    results = [
        {
            "id": "receipts",
            "label": "Receipt Integrity",
            "status": "PASS",
            "exit_code": 0,
            "stdout": "All checks pass.",
            "stderr": "",
        },
    ]
    report = build_report(results, "all", "/root/test", None)
    assert report["tool"] == "ordivon-verify"
    assert report["schema_version"] == "0.1"
    assert report["status"] == "READY"
    assert report["mode"] == "all"
    assert report["root"] == "/root/test"
    assert len(report["checks"]) == 1
    assert report["checks"][0]["id"] == "receipts"
    assert report["checks"][0]["status"] == "PASS"
    assert "hard_failures" in report
    assert "warnings" in report
    assert "disclaimer" in report


def test_build_report_with_failures():
    results = [
        {
            "id": "receipts",
            "label": "Receipt Integrity",
            "status": "PASS",
            "exit_code": 0,
            "stdout": "ok",
            "stderr": "",
        },
        {
            "id": "debt",
            "label": "Verification Debt",
            "status": "FAIL",
            "exit_code": 1,
            "stdout": "",
            "stderr": "overdue debt",
        },
    ]
    report = build_report(results, "all", "/root/test", None)
    assert report["status"] == "BLOCKED"
    assert len(report["hard_failures"]) == 1
    assert report["hard_failures"][0]["check"] == "debt"


# ── Unit: parse_args ─────────────────────────────────────────────────────


def test_parse_args_default_to_all():
    """Default (no command) should have command=None, handled by main as 'all'."""
    args = parse_args([])
    assert args.command is None


def test_parse_args_all():
    args = parse_args(["all"])
    assert args.command == "all"


def test_parse_args_receipts():
    args = parse_args(["receipts"])
    assert args.command == "receipts"


def test_parse_args_debt():
    args = parse_args(["debt"])
    assert args.command == "debt"


def test_parse_args_gates():
    args = parse_args(["gates"])
    assert args.command == "gates"


def test_parse_args_docs():
    args = parse_args(["docs"])
    assert args.command == "docs"


def test_parse_args_json_flag():
    args = parse_args(["all", "--json"])
    assert args.command == "all"
    assert args.json is True


# ── Integration: run_check (mocked subprocess) ────────────────────────────


def test_run_check_pass(monkeypatch):
    """run_check returns PASS when subprocess exits 0."""
    mock_run = MagicMock()
    mock_run.returncode = 0
    mock_run.stdout = "All checks pass.\n"
    mock_run.stderr = ""

    def mock_subprocess_run(*args, **kwargs):
        return mock_run

    monkeypatch.setattr(subprocess, "run", mock_subprocess_run)
    result = run_check("receipts")
    assert result["status"] == "PASS"
    assert result["exit_code"] == 0
    assert result["id"] == "receipts"


def test_run_check_fail(monkeypatch):
    """run_check returns FAIL when subprocess exits non-zero."""
    mock_run = MagicMock()
    mock_run.returncode = 1
    mock_run.stdout = "Violation found.\n"
    mock_run.stderr = ""

    monkeypatch.setattr(subprocess, "run", lambda *args, **kwargs: mock_run)
    result = run_check("debt")
    assert result["status"] == "FAIL"
    assert result["exit_code"] == 1


def test_run_check_timeout(monkeypatch):
    """run_check handles subprocess timeout."""

    def mock_timeout(*args, **kwargs):
        raise subprocess.TimeoutExpired(cmd="test", timeout=60)

    monkeypatch.setattr(subprocess, "run", mock_timeout)
    result = run_check("gates")
    assert result["status"] == "FAIL"
    assert result["exit_code"] == -1
    assert "timed out" in result["stderr"].lower()


def test_run_check_exception(monkeypatch):
    """run_check handles unexpected exceptions."""

    def mock_exception(*args, **kwargs):
        raise OSError("file not found")

    monkeypatch.setattr(subprocess, "run", mock_exception)
    result = run_check("docs")
    assert result["status"] == "FAIL"
    assert result["exit_code"] == -1
    assert "file not found" in result["stderr"]


# ── Integration: main() with mocked run_check ────────────────────────────


def _mock_run_pass(check_id: str) -> dict:
    return {
        "id": check_id,
        "label": check_id,
        "status": "PASS",
        "exit_code": 0,
        "stdout": "All good.",
        "stderr": "",
    }


def _mock_run_fail(check_id: str) -> dict:
    return {
        "id": check_id,
        "label": check_id,
        "status": "FAIL",
        "exit_code": 1,
        "stdout": "",
        "stderr": "Found issues.",
    }


def test_main_all_passes(monkeypatch, capsys):
    """main(['all']) with all checks passing -> exit 0, status READY."""
    monkeypatch.setattr("ordivon_verify.runner.run_check", _mock_run_pass)
    exit_code = main(["all"])
    assert exit_code == 0
    captured = capsys.readouterr()
    assert "ORDIVON VERIFY" in captured.out
    assert "READY" in captured.out


def test_main_all_one_fail(monkeypatch, capsys):
    """main(['all']) with one check failing -> exit 1, status BLOCKED."""

    def mixed_run(check_id: str) -> dict:
        if check_id == "debt":
            return _mock_run_fail(check_id)
        return _mock_run_pass(check_id)

    monkeypatch.setattr("ordivon_verify.runner.run_check", mixed_run)
    exit_code = main(["all"])
    assert exit_code == 1
    captured = capsys.readouterr()
    assert "BLOCKED" in captured.out


def test_main_receipts_command(monkeypatch, capsys):
    """main(['receipts']) runs only receipts checker."""
    calls = []

    def track_run(check_id: str) -> dict:
        calls.append(check_id)
        return _mock_run_pass(check_id)

    monkeypatch.setattr("ordivon_verify.runner.run_check", track_run)
    exit_code = main(["receipts"])
    assert exit_code == 0
    assert calls == ["receipts"]


def test_main_debt_command(monkeypatch):
    """main(['debt']) runs only debt checker."""
    calls = []

    def track_run(check_id: str) -> dict:
        calls.append(check_id)
        return _mock_run_pass(check_id)

    monkeypatch.setattr("ordivon_verify.runner.run_check", track_run)
    exit_code = main(["debt"])
    assert exit_code == 0
    assert calls == ["debt"]


def test_main_gates_command(monkeypatch):
    """main(['gates']) runs only gates checker."""
    calls = []

    def track_run(check_id: str) -> dict:
        calls.append(check_id)
        return _mock_run_pass(check_id)

    monkeypatch.setattr("ordivon_verify.runner.run_check", track_run)
    exit_code = main(["gates"])
    assert exit_code == 0
    assert calls == ["gates"]


def test_main_docs_command(monkeypatch):
    """main(['docs']) runs only docs checker."""
    calls = []

    def track_run(check_id: str) -> dict:
        calls.append(check_id)
        return _mock_run_pass(check_id)

    monkeypatch.setattr("ordivon_verify.runner.run_check", track_run)
    exit_code = main(["docs"])
    assert exit_code == 0
    assert calls == ["docs"]


def test_main_default_maps_to_all(monkeypatch):
    """main([]) — no args — defaults to 'all' and runs all checks."""
    calls = []

    def track_run(check_id: str) -> dict:
        calls.append(check_id)
        return _mock_run_pass(check_id)

    monkeypatch.setattr("ordivon_verify.runner.run_check", track_run)
    exit_code = main([])
    assert exit_code == 0
    assert calls == ALL_CHECKS


def test_main_json_output_all_pass(monkeypatch, capsys):
    """main(['all', '--json']) emits valid JSON with required fields."""
    monkeypatch.setattr("ordivon_verify.runner.run_check", _mock_run_pass)
    exit_code = main(["all", "--json"])
    assert exit_code == 0
    captured = capsys.readouterr()
    report = json.loads(captured.out)
    assert report["tool"] == "ordivon-verify"
    assert report["status"] == "READY"
    assert report["mode"] in ("all", "standard")  # auto-detects Ordivon-native
    assert len(report["checks"]) == 4
    assert report["hard_failures"] == []


def test_main_json_output_one_fail(monkeypatch, capsys):
    """main(['all', '--json']) with one failure -> status BLOCKED in JSON."""

    def mixed_run(check_id: str) -> dict:
        if check_id == "gates":
            return _mock_run_fail(check_id)
        return _mock_run_pass(check_id)

    monkeypatch.setattr("ordivon_verify.runner.run_check", mixed_run)
    exit_code = main(["all", "--json"])
    assert exit_code == 1
    captured = capsys.readouterr()
    report = json.loads(captured.out)
    assert report["status"] == "BLOCKED"
    assert len(report["hard_failures"]) == 1


def test_main_unknown_command(monkeypatch):
    """main(['unknown']) -> exit code 3."""
    exit_code = main(["unknown"])
    assert exit_code == 3


def test_main_runtime_exception(monkeypatch):
    """main where build_report unexpectedly raises -> exit 4."""

    def mock_run(*args, **kwargs):
        return {
            "id": "receipts",
            "label": "Receipt Integrity",
            "status": "PASS",
            "exit_code": 0,
            "stdout": "ok",
            "stderr": "",
        }

    monkeypatch.setattr("ordivon_verify.runner.run_check", mock_run)

    # Force an unexpected exception in build_report (called with --json)
    def boom_build(*args, **kwargs):
        raise RuntimeError("simulated crash in report builder")

    monkeypatch.setattr("ordivon_verify.cli.build_report", boom_build)
    exit_code = main(["all", "--json"])
    assert exit_code == 4


def test_main_no_shell_true(monkeypatch):
    """Verify that subprocess.run is called without shell=True."""
    calls = []

    def intercept(*args, **kwargs):
        calls.append(kwargs)
        mock = MagicMock()
        mock.returncode = 0
        mock.stdout = "ok"
        mock.stderr = ""
        return mock

    monkeypatch.setattr(subprocess, "run", intercept)
    main(["all"])
    for kw in calls:
        assert kw.get("shell", False) is False


# ── Verify no shell injection pattern ────────────────────────────────────


def test_run_check_uses_list_not_string(monkeypatch):
    """run_check passes a list (not a shell string) to subprocess.run."""
    calls = []

    def intercept(cmd, **kwargs):
        calls.append(cmd)
        mock = MagicMock()
        mock.returncode = 0
        mock.stdout = "ok"
        mock.stderr = ""
        return mock

    monkeypatch.setattr(subprocess, "run", intercept)
    run_check("receipts")
    assert len(calls) == 1
    # cmd should be a list (not a string)
    assert isinstance(calls[0], list)
    assert calls[0][0] == sys.executable


# ── Verify CHECKER_SCRIPTS paths exist ────────────────────────────────────


def test_all_checker_scripts_exist():
    """All configured checker scripts should be real files."""
    for check_id, path in CHECKER_SCRIPTS.items():
        assert path.exists(), f"Checker script missing: {path}"
