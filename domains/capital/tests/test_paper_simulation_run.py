"""Executable-model-to-durable-Paper boundary with no fake market credentials."""
from __future__ import annotations

import json
import os
from dataclasses import asdict
from datetime import date, datetime
from hashlib import sha256
from pathlib import Path

import psycopg
import pytest

from ordivon_capital.accounting.paper_close import (
    PaperBuy,
    PaperSell,
    PaperSession,
    value_session,
)
from ordivon_capital.accounting.paper_simulation_run import run_simulated_paper
from ordivon_capital.accounting.postgres_paper_close import read_latest_committed_paper_close


def _bundle(root: Path) -> dict[str, Path]:
    days = [
        date.fromisoformat(x)
        for x in (
            "2025-10-14", "2025-10-15", "2025-10-16", "2025-10-17",
            "2025-10-20", "2025-10-21", "2025-10-22", "2025-10-23",
        )
    ]
    buy = PaperBuy(
        "native-buy-one", "SPY", 1, 66_679, 1,
        datetime.fromisoformat("2025-10-14T16:01:00-04:00"),
        datetime.fromisoformat("2025-10-15T09:30:00-04:00"),
        days[2],
    )
    sell = PaperSell(
        "native-sell-one", "SPY", 1, 67_198, 1,
        datetime.fromisoformat("2025-10-21T16:01:00-04:00"),
        datetime.fromisoformat("2025-10-22T09:30:00-04:00"),
        days[7],
    )
    sessions = [PaperSession(days[0], None, 1_000_000, 900_000, {}, ())]
    sessions += [
        PaperSession(
            day, days[i-1], 0, 0,
            {"SPY": 66_600 + i * 100} if i < 6 else {},
            (buy,) if i == 1 else (),
            (sell,) if i == 6 else (),
        )
        for i, day in enumerate(days) if i != 0
    ]
    state = None
    for day in sessions:
        state = value_session(state, day)
    assert state is not None and state.cash_minor == 1_000_517
    pred = (
        b"datetime,instrument,score\n"
        b"2025-10-14,IWM,0.01\n2025-10-14,QQQ,0.02\n2025-10-14,SPY,0.03\n"
    )
    study = {
        "qlib_prediction_sha256": sha256(pred).hexdigest(),
        "portfolio_target": None,
        "forecast": {
            "point_in_time_eligible": False,
            "native_strategy_exit_event_matches_target": True,
        },
        "signal_quality": {
            "exit_price_kind": "next_open",
            "holding_sessions": 5,
            "matches_native_fixed_holding_exit_event": True,
        },
    }
    sessions_bytes = json.dumps(
        [asdict(day) for day in sessions],
        default=lambda v: v.isoformat(), indent=2, sort_keys=True,
    ).encode()
    result = {
        "model_study_sha256": sha256(json.dumps(study).encode()).hexdigest(),
        "model_prediction_sha256": sha256(pred).hexdigest(),
        "native_account": "SIM-001",
        "standing": "SIMULATION_ONLY_NON_PIT_NOT_CAPITAL_AUTHORIZED",
        "research_horizon_signal_source": "native_Qlib_0.9.7_OOS_score",
        "test_counterfactual_score_intervention": False,
        "historical_point_in_time_qualified": False,
        "portfolio_automatic_execution_authorized": False,
        "portfolio_intent_admitted": False,
        "real_broker_or_PG_effect": "NONE",
        "Qlib_target_vs_native_exit_event_identical": True,
        "positions_closed": True,
        "receivable_settled": True,
        "native_open_position_count": 0,
        "horizon_complete_sessions": 5,
        "selected_instrument": "SPY",
        "research_model_sample_decision": "2025-10-14",
        "native_entry_session": "2025-10-15",
        "native_exit_session": "2025-10-22",
        "native_fill_count": 2,
        "last_paper_cash_minor": state.cash_minor,
        "protected_cash_minor": 900_000,
        "paper_sessions_sha256": sha256(sessions_bytes).hexdigest(),
    }
    out = {}
    for name, content in (
        ("study", json.dumps(study).encode()),
        ("predictions", pred),
        ("native", json.dumps(result).encode()),
        ("sessions", sessions_bytes),
    ):
        target = root / (name + ".json" if name != "predictions" else name + ".csv")
        target.write_bytes(content)
        out[name] = target
    return out


class ReachedPostgres(Exception):
    pass


def test_native_batch_preflight_reaches_existing_ledger_only_for_coherent_inputs(
    tmp_path, monkeypatch,
):
    bundle = _bundle(tmp_path)
    import ordivon_capital.accounting.paper_simulation_run as runner

    def _reached(_dsn):
        raise ReachedPostgres("validated before first PG schema or transaction")

    monkeypatch.setattr(runner, "PostgresPaperClose", _reached)
    with pytest.raises(ReachedPostgres):
        run_simulated_paper("never-connect", **bundle)

    # Change a mid-hold close mark without changing final economic cash.
    sessions = json.loads(bundle["sessions"].read_text())
    sessions[3]["marks"]["SPY"] += 299
    bundle["sessions"].write_text(json.dumps(sessions))
    with pytest.raises(ValueError, match="serialized Paper sessions differ"):
        run_simulated_paper("never-connect", **bundle)

    # Restore sessions and tamper with the original model decision.
    bundle = _bundle(tmp_path)
    pred = bundle["predictions"].read_bytes().replace(b"SPY,0.03", b"SPY,-0.03")
    bundle["predictions"].write_bytes(pred)
    with pytest.raises(ValueError, match="model and account co-artifacts disagree"):
        run_simulated_paper("never-connect", **bundle)

    # Same study+CSV but fake native instrument cannot become a new account.
    bundle = _bundle(tmp_path)
    native = json.loads(bundle["native"].read_text())
    native["selected_instrument"] = "IWM"
    bundle["native"].write_text(json.dumps(native))
    with pytest.raises(ValueError, match="contradicts exact Qlib"):
        run_simulated_paper("never-connect", **bundle)

    bundle = _bundle(tmp_path)
    native = json.loads(bundle["native"].read_text())
    native["last_paper_cash_minor"] += 10
    bundle["native"].write_text(json.dumps(native))
    with pytest.raises(ValueError, match="economic identities disagree"):
        run_simulated_paper("never-connect", **bundle)


def test_paper_batch_real_postgres_restart_safe_run_identity_and_receipt(tmp_path):
    dsn = os.environ.get("ORDIVON_CAPITAL_PAPER_PG_TEST_DSN")
    if not dsn:
        pytest.skip("real disposable ordivon_paper PostgreSQL is required")
    # Confirm the test role before permitting this fixture to create any account.
    with psycopg.connect(dsn) as db:
        assert db.execute("SELECT current_database()").fetchone() == ("ordivon_paper",)
    bundle = _bundle(tmp_path)
    # Stable model and Native receipt hashes, distinct simulated principal/run per input.
    a = run_simulated_paper(dsn, **bundle)
    b = run_simulated_paper(dsn, **bundle)
    assert a == b
    assert a["dailyCommittedCount"] == 8
    assert a["finalCashMinor"] == 1_000_517
    assert a["protectedMinor"] == 900_000
    assert a["brokerEffects"] == 0
    head = read_latest_committed_paper_close(dsn, a["accountKey"])
    assert head is not None
    assert head["market_evidence"]["standing"] == "CALLER_SUPPLIED_MARKS"
    assert head["simulation_evidence"] == a["simulationEvidence"]
    # Independent test case itself gets unique source bytes: no external account mapping.
    assert a["accountKey"].startswith("r3sim_")
    assert a["realAccountMappingAuthorized"] is False
