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
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from io import StringIO
from os import environ
from pathlib import Path

from ..governance.policy_decision import PolicyDecisionError, enforce_non_live
from ..portfolio.strategic_contribution import plan_strategic_contribution
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


def _native_usd_minor(raw: object) -> int:
    """Exact cents, never floating point or rounded inferred execution costs."""
    if type(raw) is not str:
        raise ValueError("native execution economics disagree")
    try:
        cents = Decimal(raw) * 100
    except InvalidOperation as exc:
        raise ValueError("native execution economics disagree") from exc
    if not cents.is_finite() or cents != cents.to_integral_value():
        raise ValueError("native execution economics disagree")
    return int(cents)


def _admit_paper_mandate(
    path: Path, *, symbol: str, horizon: int, buys_minor: int,
    starting_cash: int, protected_cash: int,
) -> dict:
    """Compose existing Portfolio capital-plan and Governance nonlive gates.

    A caller-declared Paper portfolio label is NOT a real broker principal.
    The repo's actual policy source, not an input file provided by the
    caller, decides whether NON_LIVE effects are currently permitted.
    """
    raw = path.read_bytes()
    mandate = json.loads(raw)
    expected = {
        "schemaVersion", "kind", "portfolioRef", "lane",
        "externalFinancialWritesAllowed", "maxHorizonSessions",
        "allocationRequest",
    }
    if (
        type(mandate) is not dict or set(mandate) != expected
        or type(mandate["schemaVersion"]) is not int
        or mandate["schemaVersion"] != 1
        or mandate["kind"] != "ordivon.finance.portfolio.paper-simulation-mandate"
        or mandate["lane"] != "NON_LIVE"
        or mandate["externalFinancialWritesAllowed"] is not False
        or type(mandate["maxHorizonSessions"]) is not int
        or mandate["maxHorizonSessions"] not in (5, 20)
        or horizon > mandate["maxHorizonSessions"]
        or type(mandate["portfolioRef"]) is not str
        or re.fullmatch(r"paper-[a-z0-9][a-z0-9-]{2,47}", mandate["portfolioRef"]) is None
    ):
        raise ValueError("Paper portfolio mandate is not simulation-only or in scope")
    # Existing Portfolio makes a projection, never investment advice or
    # execution permission. The amount is the maximum simulated sleeve,
    # not an additional deposit to the initial Paper cash.
    plan = plan_strategic_contribution(mandate["allocationRequest"])
    if (
        plan["standing"] != "READ_ONLY_PROJECTION"
        or plan["executionAuthorized"] is not False
        or plan["currency"] != "USD"
        or mandate["allocationRequest"]["cashMinor"] != starting_cash
        or plan["protectedReserveMinor"] != protected_cash
        or plan["contributionMinor"] != starting_cash - protected_cash
        or plan["allocationsMinor"].get(symbol, 0) < buys_minor
    ):
        raise ValueError("Paper fill exceeds the caller-declared Portfolio capital envelope")
    # Reuse the current repo's sole Governance decision point; no new
    # authorization system and no user-supplied policy override.
    repo = Path(__file__).resolve().parents[3]
    try:
        gate = enforce_non_live(repo, repo / "config/execution_policy.json")
    except PolicyDecisionError as exc:
        raise ValueError("current Governance policy denied Paper nonlive effects") from exc
    if (
        gate["standing"] != "NON_LIVE_POLICY_ALLOWED"
        or gate["externalFinancialWritesAllowed"] is not False
        or gate["allowExternalWrite"] is not False
    ):
        raise ValueError("current Governance policy does not allow Paper nonlive effects")
    return {
        "paper_portfolio_ref": mandate["portfolioRef"],
        "paper_mandate_sha256": _digest(raw),
        "nonlive_policy_standing": gate["standing"],
        "portfolio_plan_standing": plan["standing"],
    }


def run_simulated_paper(
    dsn: str, *, study: Path, predictions: Path, native: Path, sessions: Path,
    mandate: Path | None = None,
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

    # A valid terminal net amount DOES NOT prove the individual native
    # execution events were faithfully projected. False buy/sell prices can
    # cancel economically; source each event to native Nautilus fill report
    # exposed by the same genuine producer, not to account summary alone.
    native_claims = outcome.get("native_fill_claims")
    if type(native_claims) is not list or len(native_claims) != fills:
        raise ValueError("native execution economics disagree")
    actual_fills = [
        {
            "side": side,
            "fill_id": fill.fill_id,
            "symbol": fill.symbol,
            "shares": fill.shares,
            "price_minor": fill.price_minor,
            "fee_minor": fill.fee_minor,
            "filled_at": fill.filled_at,
        }
        for day in decoded
        for side, values in (("BUY", day.buys), ("SELL", day.sells))
        for fill in values
    ]
    try:
        claimed = [
            {
                "side": claim["side"],
                # Reuse the mature Nautilus→Paper bridge's account-scoped ID,
                # rather than mistaking the raw native trade_id for Paper ID.
                "fill_id": f'nautilus-paper:SIM-001:{claim["fill_id"]}',
                "symbol": claim["symbol"],
                "shares": claim["shares"],
                "price_minor": claim["price_minor"],
                "fee_minor": claim["fee_minor"],
                "filled_at": datetime.fromisoformat(claim["filled_at"]),
            }
            for claim in native_claims
        ]
    except (TypeError, ValueError, KeyError) as exc:
        raise ValueError("native execution economics disagree") from exc
    if (
        sorted(claimed, key=lambda r: (r["side"], r["fill_id"]))
        != sorted(actual_fills, key=lambda r: (r["side"], r["fill_id"]))
        or any(
            (type(row["shares"]) is not int
             or type(row["price_minor"]) is not int
             or type(row["fee_minor"]) is not int
             or row["filled_at"].utcoffset() is None)
            for row in claimed
        )
        or outcome.get("native_order_count") != (1 if fills == 0 else 2)
        or outcome.get("no_entry_cancelled_exit_suppressed") is not (fills == 0)
        or _native_usd_minor(outcome.get("fee_total"))
            != sum(row["fee_minor"] for row in actual_fills)
        or _native_usd_minor(outcome.get("net_cash_gain_usd"))
            != state.cash_minor - 1_000_000
    ):
        raise ValueError("native execution economics disagree")
    if fills == 2:
        buy = next(row for row in actual_fills if row["side"] == "BUY")
        sell = next(row for row in actual_fills if row["side"] == "SELL")
        if (
            buy["shares"] != 1 or sell["shares"] != 1
            or _native_usd_minor(outcome.get("buy_price")) != buy["price_minor"]
            or _native_usd_minor(outcome.get("sell_price")) != sell["price_minor"]
        ):
            raise ValueError("native execution economics disagree")
    elif outcome.get("buy_price") is not None or outcome.get("sell_price") is not None:
        raise ValueError("native execution economics disagree")

    # The account is derived, NEVER mapped from a user/broker account string.
    evidence = {
        "standing": "SIMULATION_ONLY_CALLER_DECLARED",
        "native_account": "SIM-001",
        "model_study_sha256": model_digest,
        "prediction_sha256": pred_digest,
        "native_result_sha256": outcome_digest,
        "sessions_sha256": days_digest,
    }
    if mandate is not None:
        evidence.update(_admit_paper_mandate(
            mandate,
            symbol=symbol,
            horizon=hold,
            buys_minor=sum(
                fill.cost_minor for day in decoded for fill in day.buys
            ),
            starting_cash=decoded[0].contribution_minor,
            protected_cash=decoded[0].reserve_contribution_minor,
        ))
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
        **({
            "portfolioRef": evidence["paper_portfolio_ref"],
            "portfolioMandateStanding": "SIMULATION_ONLY_PORTFOLIO_PLAN_BOUND",
        } if mandate is not None else {}),
        "effect": "PG_PAPER_SIMULATION_ONLY",
    }


def main() -> int:
    cli = argparse.ArgumentParser(description=__doc__)
    for name in ("study", "predictions", "native", "sessions"):
        cli.add_argument("--" + name, type=Path, required=True)
    cli.add_argument("--mandate", type=Path, help=(
        "Optional caller-declared Paper capital mandate, validated against "
        "current Portfolio and Governance nonlive policy. Not a live PortfolioIntent."
    ))
    args = cli.parse_args()
    try:
        result = run_simulated_paper(
            environ.get("ORDIVON_CAPITAL_PAPER_PG_DSN", ""),
            study=args.study, predictions=args.predictions,
            native=args.native, sessions=args.sessions,
            mandate=args.mandate,
        )
    except (ValueError, KeyError, TypeError, OSError) as exc:
        cli.exit(1, f"simulation Paper batch refused: {exc}\n")
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
