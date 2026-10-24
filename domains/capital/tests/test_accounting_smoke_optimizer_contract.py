"""ACTUAL SQLite smoke consumers must perform the same effects under Python -O.

Both native scripts create only private temporary SQLite databases and never
contact providers or touch external financial accounts.
"""
import json
import os
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]

SMOKES = [
    (
        "run-sqlite-accounting-durable-restart-smoke-r1",
        "PASS_SQLITE_DURABLE_RESTART_RECONCILIATION",
    ),
    (
        "run-nonlive-capital-effect-matrix",
        "PASS_NONLIVE_EFFECT_TO_CAPITAL_RESTART_MATRIX",
    ),
]


def run_actual_script(script_name: str, *, optimized: bool):
    env = dict(
        os.environ,
        PYTHONOPTIMIZE="1" if optimized else "0",
        PYTHONDONTWRITEBYTECODE="1",
    )
    return subprocess.run(
        [str(ROOT / "scripts" / script_name)],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
        timeout=35,
        check=False,
    )


@pytest.mark.parametrize("name,expected_standing", SMOKES)
def test_real_sqlite_restart_smoke_has_identical_normal_and_optimized_effects(
    name, expected_standing,
):
    normal = run_actual_script(name, optimized=False)
    assert normal.returncode == 0, normal.stdout + normal.stderr
    optimized = run_actual_script(name, optimized=True)
    assert optimized.returncode == 0, optimized.stdout + optimized.stderr

    a = json.loads(normal.stdout)
    b = json.loads(optimized.stdout)
    assert b == a, "Python -O changed SQLite effects, replay, or reconciliation"
    assert a["standing"] == expected_standing
    assert a["externalFinancialWriteAttempted"] is False
    if name == "run-nonlive-capital-effect-matrix":
        assert a["exactConsumeReplayStatus"] == "EXISTS"
        assert a["scenarios"]["FILL"]["ledgerReconciliation"] == "MATCH"
        assert a["scenarios"]["UNKNOWN_AFTER_SUBMISSION"]["debitsPending"] == 100
    else:
        assert a["exactReservationReplayStatus"] == "EXISTS"
        assert a["terminalReconciliation"] == "MATCH"
        assert a["staleLedgerReconciliation"] == "LEDGER_INCOMPLETE_NO_REPAIR"
