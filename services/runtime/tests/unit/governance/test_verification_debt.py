"""Phase DG-6B: Verification Debt Ledger tests."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

CHECKER = Path(__file__).resolve().parents[3] / "scripts" / "check_verification_debt.py"


def _make_entry(**overrides) -> dict:
    base = {
        "debt_id": "VD-TEST-001",
        "opened_phase": "DG-6B",
        "category": "pre_existing_tooling_debt",
        "scope": "test scope",
        "description": "Test debt entry.",
        "risk": "Low risk for test.",
        "severity": "low",
        "introduced_by_current_phase": False,
        "owner": "test",
        "follow_up": "Test resolution.",
        "expires_before_phase": "DG-Z",
        "status": "open",
        "opened_at": "2026-04-30",
        "closed_at": None,
        "evidence": "test evidence",
        "notes": None,
    }
    base.update(overrides)
    return base


def _run_checker(entries: list[dict], env: dict = None) -> tuple[int, str]:
    import tempfile

    with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
        for e in entries:
            f.write(json.dumps(e) + "\n")
        tmp = f.name
    try:
        run_env = os.environ.copy()
        if env:
            run_env.update(env)
        result = subprocess.run(
            [sys.executable, str(CHECKER), tmp],
            capture_output=True,
            text=True,
            timeout=30,
            env=run_env,
        )
        return result.returncode, result.stdout
    finally:
        Path(tmp).unlink(missing_ok=True)


# ── Positive ──────────────────────────────────────────────────────────


def test_valid_debt_ledger_passes():
    exit_code, _ = _run_checker([_make_entry()])
    assert exit_code == 0


# ── Negative: JSON ────────────────────────────────────────────────────


def test_invalid_json_fails():
    import tempfile

    with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
        f.write("not json\n")
        tmp = f.name
    try:
        result = subprocess.run(
            [sys.executable, str(CHECKER), tmp],
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode != 0
    finally:
        Path(tmp).unlink(missing_ok=True)


# ── Negative: required fields ─────────────────────────────────────────


def test_missing_required_field_fails():
    e = _make_entry()
    del e["owner"]
    exit_code, _ = _run_checker([e])
    assert exit_code != 0


# ── Negative: duplicate ───────────────────────────────────────────────


def test_duplicate_debt_id_fails():
    exit_code, _ = _run_checker([_make_entry(debt_id="dup"), _make_entry(debt_id="dup")])
    assert exit_code != 0


# ── Negative: invalid category ────────────────────────────────────────


def test_invalid_category_fails():
    exit_code, _ = _run_checker([_make_entry(category="not_a_category")])
    assert exit_code != 0


# ── Negative: invalid severity ────────────────────────────────────────


def test_invalid_severity_fails():
    exit_code, _ = _run_checker([_make_entry(severity="critical")])
    assert exit_code != 0


# ── Negative: invalid status ──────────────────────────────────────────


def test_invalid_status_fails():
    exit_code, _ = _run_checker([_make_entry(status="unknown")])
    assert exit_code != 0


# ── Negative: open debt missing owner ─────────────────────────────────


def test_open_debt_missing_owner_fails():
    e = _make_entry(status="open")
    e["owner"] = None
    exit_code, _ = _run_checker([e])
    assert exit_code != 0


# ── Negative: open debt missing follow_up ─────────────────────────────


def test_open_debt_missing_follow_up_fails():
    e = _make_entry(status="open")
    e["follow_up"] = ""
    exit_code, _ = _run_checker([e])
    assert exit_code != 0


# ── Negative: open debt missing expiry ────────────────────────────────


def test_open_debt_missing_expiry_fails():
    e = _make_entry(status="open")
    e["expires_before_phase"] = None
    exit_code, _ = _run_checker([e])
    assert exit_code != 0


# ── Negative: overdue open debt fails ─────────────────────────────────


def test_overdue_open_debt_fails():
    e = _make_entry(status="open", expires_before_phase="2026-04-01")
    exit_code, _ = _run_checker([e], env={"REFERENCE_DATE": "2026-04-30"})
    assert exit_code != 0


# ── Positive: accepted_until not overdue ──────────────────────────────


def test_accepted_until_not_overdue_passes():
    e = _make_entry(status="accepted_until", expires_before_phase="2026-04-01")
    exit_code, _ = _run_checker([e], env={"REFERENCE_DATE": "2026-03-15"})
    assert exit_code == 0


# ── Positive: closed debt with closed_at ──────────────────────────────


def test_closed_debt_with_closed_at_passes():
    e = _make_entry(status="closed", closed_at="2026-04-30")
    exit_code, _ = _run_checker([e])
    assert exit_code == 0


# ── Summary counts ────────────────────────────────────────────────────


def test_summary_counts_correct():
    entries = [
        _make_entry(debt_id="a", status="open"),
        _make_entry(debt_id="b", status="closed", closed_at="2026-04-30"),
        _make_entry(debt_id="c", status="accepted_until"),
    ]
    exit_code, out = _run_checker(entries)
    assert exit_code == 0
    assert "Open:                      1" in out
    assert "Closed:                    1" in out
    assert "Accepted until:            1" in out
    assert "Ledger entries:" in out


# ── Checker never mutates ─────────────────────────────────────────────


def test_checker_never_mutates():
    import tempfile

    entries = [_make_entry()]
    with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
        for e in entries:
            f.write(json.dumps(e) + "\n")
        tmp = f.name
    try:
        subprocess.run(
            [sys.executable, str(CHECKER), tmp],
            capture_output=True,
            text=True,
            timeout=30,
        )
        with open(tmp) as f:
            content = json.loads(f.readline())
        assert content["debt_id"] == "VD-TEST-001"
    finally:
        Path(tmp).unlink(missing_ok=True)
