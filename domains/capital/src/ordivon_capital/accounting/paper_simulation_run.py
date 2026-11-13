"""Resume an exact simulated native run through the EXISTING PostgreSQL Paper ledger.

The source files are caller-supplied, retrospective and NOT market PIT/rights
evidence. The dedicated Paper database is the only mutable financial effect.
No broker, order adapter, position engine, or second account ledger is defined.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from datetime import date
from io import StringIO
from os import environ
from pathlib import Path

from .paper_close import decode_session, value_session
from .postgres_paper_close import (
    PostgresPaperClose,
    read_committed_paper_close,
    read_latest_committed_paper_close,
)


def _digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _read(path: Path) -> tuple[dict | list, str]:
    raw = path.read_bytes()
    return json.loads(raw), _digest(raw)


def run_simulated_paper(
    dsn: str, *, study: Path, predictions: Path, native: Path, sessions: Path,
) -> dict:
    """Preflight complete simulation identity BEFORE creating any PG schema or row.

    An interrupted batch may have committed a prefix: exact retry resumes
    using PostgresPaperClose's existing per-session serializable transactions.
    Neither batch atomicity nor independent model-result signature is claimed.
    """
    model, model_digest = _read(study)
    pred_bytes = predictions.read_bytes()
    pred_digest = _digest(pred_bytes)
    outcome, outcome_digest = _read(native)
    days_raw, days_digest = _read(sessions)

    if type(outcome) is not dict or outcome.get("paper_sessions_sha256") != days_digest:
        raise ValueError("serialized Paper sessions differ from original native simulation")
    if (
        outcome.get("model_study_sha256") != model_digest
        or outcome.get("model_prediction_sha256") != pred_digest
        or outcome.get("native_account") != "SIM-001"
    ):
        raise ValueError("Qlib/native model and account co-artifacts disagree")
    if (
        type(model) is not dict or type(outcome) is not dict
        or type(model.get("forecast")) is not dict
        or type(model.get("signal_quality")) is not dict
        or model.get("qlib_prediction_sha256") != pred_digest
        or model.get("portfolio_target") is not None
        or model.get("forecast", {}).get("point_in_time_eligible") is not False
        or model.get("signal_quality", {}).get("exit_price_kind") != "next_open"
        or model.get("signal_quality", {}).get("matches_native_fixed_holding_exit_event") is not True
        or model.get("forecast", {}).get("native_strategy_exit_event_matches_target") is not True
    ):
        raise ValueError("unqualified caller-supplied Qlib simulation study")
    if (
        outcome.get("standing") != "SIMULATION_ONLY_NON_PIT_NOT_CAPITAL_AUTHORIZED"
        or outcome.get("research_horizon_signal_source") != "native_Qlib_0.9.7_OOS_score"
        or outcome.get("test_counterfactual_score_intervention") is not False
        or outcome.get("historical_point_in_time_qualified") is not False
        or outcome.get("portfolio_automatic_execution_authorized") is not False
        or outcome.get("portfolio_intent_admitted") is not False
        or outcome.get("real_broker_or_PG_effect") != "NONE"
        or outcome.get("Qlib_target_vs_native_exit_event_identical") is not True
        or outcome.get("positions_closed") is not True
        or outcome.get("receivable_settled") is not True
        or outcome.get("native_open_position_count") != 0
    ):
        raise ValueError("native outcome not an eligible simulation-only terminal state")
    hold = outcome.get("horizon_complete_sessions")
    symbol = outcome.get("selected_instrument")
    if (type(hold) is not int or hold not in (5, 20)
            or hold != model["signal_quality"].get("holding_sessions")
            or symbol not in ("SPY", "QQQ", "IWM")
            or type(days_raw) is not list
            or not 2 <= len(days_raw) <= 32):
        raise ValueError("invalid native horizon or Paper session set")

    decision = outcome.get("research_model_sample_decision")
    try:
        decision_date = date.fromisoformat(decision)
        rows = [
            row for row in csv.DictReader(StringIO(pred_bytes.decode("utf-8")))
            if row.get("datetime") == decision_date.isoformat()
        ]
        if len(rows) != 3 or {r["instrument"] for r in rows} != {"SPY", "QQQ", "IWM"}:
            raise ValueError("native decision not present in original exact Qlib OOS snapshot")
        from math import isfinite

        scores = {
            row["instrument"]: float(next(
                value for key, value in row.items() if key not in ("datetime", "instrument")
            ))
            for row in rows
        }
        if not all(isfinite(v) for v in scores.values()):
            raise ValueError("nonfinite model decision score")
    except (TypeError, UnicodeError, StopIteration, OverflowError) as exc:
        raise ValueError("invalid Qlib OOS decision content") from exc
    expected_symbol = min(scores, key=lambda sym: (-scores[sym], sym))
    if expected_symbol != symbol:
        raise ValueError("native simulated instrument contradicts exact Qlib model output")

    # Preflight all economic events in the already-tested pure Paper model;
    # never commit a valid prefix before noticing a malformed final day.
    if any(type(day) is not dict for day in days_raw):
        raise ValueError("invalid Paper session rows")
    decoded = [decode_session(day) for day in days_raw]
    if (
        decoded[0].session != decision_date
        or len(decoded) != hold + 3
        or decoded[1].session.isoformat() != outcome.get("native_entry_session")
        or decoded[-2].session.isoformat() != outcome.get("native_exit_session")
    ):
        raise ValueError("native model decision, entry/exit and Paper dates disagree")
    if decoded[0].previous_session is not None or len({day.session for day in decoded}) != len(decoded):
        raise ValueError("simulation batch must start at an independent opening session")
    state = None
    for previous, day in zip([None, *decoded[:-1]], decoded, strict=True):
        if previous is not None and (
            day.previous_session != previous.session or day.session <= previous.session
        ):
            raise ValueError("simulation sessions are not in a strict predecessor chain")
        state = value_session(state, day)
    if state is None:
        raise ValueError("simulation has no Paper account head")
    fills = sum(len(day.buys) + len(day.sells) for day in decoded)
    if (
        (fills == 2 and (
            len(decoded[1].buys) != 1
            or len(decoded[-2].sells) != 1
            or any(day.buys for day in decoded[2:])
            or any(day.sells for day in decoded[:-2])
        ))
        or (fills == 0 and outcome.get("no_entry_cancelled_exit_suppressed") is not True)
    ):
        raise ValueError("native fill timing/zero-entry standing not preserved")
    if (
        fills != outcome.get("native_fill_count")
        or fills not in (0, 2)
        or (fills == 2 and (
            sum(len(day.buys) for day in decoded) != 1
            or sum(len(day.sells) for day in decoded) != 1
            or {fill.symbol for day in decoded for fill in (*day.buys, *day.sells)} != {symbol}
        ))
        or state.positions or state.pending or state.pending_sales
        or state.cash_minor != outcome.get("last_paper_cash_minor")
        or state.protected_minor != outcome.get("protected_cash_minor")
        or state.protected_minor != 900_000
        or decoded[0].contribution_minor != 1_000_000
        or decoded[0].reserve_contribution_minor != 900_000
        or any(day.contribution_minor or day.reserve_contribution_minor for day in decoded[1:])
        or (fills == 0 and state.cash_minor != 1_000_000)
    ):
        raise ValueError("native simulation and Paper batch economic identities disagree")

    # The account is derived, NEVER mapped from a user/broker account string.
    evidence = {
        "standing": "SIMULATION_ONLY_CALLER_DECLARED",
        "native_account": "SIM-001",
        "model_study_sha256": model_digest,
        "prediction_sha256": pred_digest,
        "native_result_sha256": outcome_digest,
        "sessions_sha256": days_digest,
    }
    key = "r3sim_" + _digest(
        json.dumps(evidence, sort_keys=True, separators=(",", ":")).encode()
    )[:40]
    if re.fullmatch(r"r3sim_[a-f0-9]{40}", key) is None:
        raise ValueError("invalid derived simulation account key")

    store = PostgresPaperClose(dsn)
    receipts = []
    for day in decoded:
        committed = store.close_session(key, day, simulation_evidence=evidence)
        if committed != read_committed_paper_close(dsn, key, day.session):
            raise RuntimeError("durable PG Paper receipt readback disagrees")
        if (committed.get("simulation_evidence") != evidence
                or committed.get("market_evidence", {}).get("standing")
                != "CALLER_SUPPLIED_MARKS"):
            raise RuntimeError("simulated evidence was silently promoted")
        receipts.append(committed)
    latest = read_latest_committed_paper_close(dsn, key)
    if latest != receipts[-1]:
        raise ValueError("simulation batch is no longer the current Paper account head")
    valuation = latest["valuation"]
    if (valuation["cash_minor"] != state.cash_minor
            or valuation["nav_minor"] != state.nav_minor
            or valuation["protected_minor"] != state.protected_minor):
        raise ValueError("native Paper economics differ from committed database head")

    return {
        "kind": "ordivon.finance.paper.simulation-batch-receipt",
        "standing": "SIMULATION_ONLY_RETROSPECTIVE_CALLER_SUPPLIED_MARKS",
        "accountKey": key,
        "realAccountMappingAuthorized": False,
        "historicalPITQualified": False,
        "brokerEffects": 0,
        "nativeInstrument": symbol,
        "horizonSessions": hold,
        "dailyCommittedCount": len(receipts),
        "dailyReceipts": [
            {"session": r["valuation"]["session"], "requestSha256": r["request_sha256"]}
            for r in receipts
        ],
        "finalCashMinor": valuation["cash_minor"],
        "finalNavMinor": valuation["nav_minor"],
        "protectedMinor": valuation["protected_minor"],
        "simulationEvidence": evidence,
        "effect": "PG_PAPER_SIMULATION_ONLY",
    }


def main() -> int:
    cli = argparse.ArgumentParser(description=__doc__)
    for name in ("study", "predictions", "native", "sessions"):
        cli.add_argument("--" + name, type=Path, required=True)
    args = cli.parse_args()
    try:
        result = run_simulated_paper(
            environ.get("ORDIVON_CAPITAL_PAPER_PG_DSN", ""),
            study=args.study, predictions=args.predictions,
            native=args.native, sessions=args.sessions,
        )
    except (ValueError, KeyError, TypeError, OSError) as exc:
        cli.exit(1, f"simulation Paper batch refused: {exc}\n")
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
