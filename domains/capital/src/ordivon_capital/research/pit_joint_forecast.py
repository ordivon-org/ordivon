"""Point-in-time joint scenario evidence for an existing Capital optimizer.

Research-only: no orders, no probabilities from future revisions, no paper ledger.
This module does not own market data ingestion or economic optimization.

The historical empirical law is a baseline, not an independently calibrated
conditional forecasting model. It retains joint cross-asset outcomes instead
of multiplying marginal ETF distributions (which destroys co-crash dependence).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from collections import Counter
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, date, datetime
from fractions import Fraction
from pathlib import Path
from typing import Any


class PointInTimeError(ValueError):
    """Invalid provenance, inaccessible future observation, or data contract."""


def _utc(instant: datetime) -> datetime:
    if instant.tzinfo is None or instant.utcoffset() is None:
        raise PointInTimeError("information time must include UTC offset")
    return instant.astimezone(UTC)


def _finite_positive(x: float) -> bool:
    return isinstance(x, (int, float)) and math.isfinite(x) and x > 0


@dataclass(frozen=True)
class PriceVintage:
    asset: str
    session: date
    published_at: datetime
    adjusted_close: float
    raw_source_sha256: str
    source_standing: str

    def __post_init__(self) -> None:
        if not self.asset or not self.asset.strip():
            raise PointInTimeError("asset identity is required")
        t = _utc(self.published_at)
        if t.date() < self.session:
            raise PointInTimeError("market value cannot be published before its session")
        if not _finite_positive(self.adjusted_close):
            raise PointInTimeError("positive finite adjusted close required")
        if len(self.raw_source_sha256) != 64 or any(
            char not in "0123456789abcdef" for char in self.raw_source_sha256
        ):
            raise PointInTimeError("exact source SHA256 required")
        if self.source_standing not in (
            "SECONDARY_VENDOR_NOT_ATTESTED",
            "PROVIDER_ORIGIN_VERIFIED",
        ):
            raise PointInTimeError("explicit source standing required")


def _exact_price_ratio(after: PriceVintage, before: PriceVintage) -> Fraction:
    """Exact rational equality for serialized positive finite price observations.

    A float quotient is only a numerical solver value, not a categorical
    scenario identity: e.g. 90/100 and 89.1/99 represent the same return.
    """
    ratio = Fraction(str(after.adjusted_close)) / Fraction(str(before.adjusted_close))
    try:
        solver_value = float(ratio)
    except OverflowError as exc:
        raise PointInTimeError("gross return exceeds finite solver range") from exc
    if not _finite_positive(solver_value):
        raise PointInTimeError("gross return is outside positive finite solver range")
    return ratio


@dataclass(frozen=True)
class JointScenario:
    probability: float
    gross_returns: tuple[float, ...]
    history_count: int


@dataclass(frozen=True)
class EmpiricalJointForecast:
    assets: tuple[str, ...]
    as_of_utc: str
    valuation_session: str
    training_return_count: int
    excluded_incomplete_intervals: int
    scenarios: tuple[JointScenario, ...]
    training_sessions: tuple[str, ...]
    source_digests: tuple[str, ...]
    standing: str = "PAST_ONLY_EMPIRICAL_JOINT_BASELINE_NOT_CALIBRATED"
    conditioning: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        result = {
            "assets": list(self.assets),
            "as_of_utc": self.as_of_utc,
            "valuation_session": self.valuation_session,
            "training_return_count": self.training_return_count,
            "excluded_incomplete_intervals": self.excluded_incomplete_intervals,
            "scenarios": [
                {
                    "probability": s.probability,
                    "gross_returns": list(s.gross_returns),
                    "history_count": s.history_count,
                }
                for s in self.scenarios
            ],
            "training_sessions": list(self.training_sessions),
            "source_digests": list(self.source_digests),
            "standing": self.standing,
        }
        if self.conditioning is not None:
            result["conditioning"] = self.conditioning
        return result


def point_in_time_prices(
    records: Sequence[PriceVintage], *, as_of: datetime
) -> dict[tuple[str, date], PriceVintage]:
    """Latest revision published by the exact decision instant, per price cell.

    A later revision of old data may be used only *after* its publication.
    Source hashes remain tied to the selected versions. Equal-time
    contradictory revisions are rejected; no implicit winner is invented.
    """
    instant = _utc(as_of)
    selected: dict[tuple[str, date], PriceVintage] = {}
    for record in records:
        when = _utc(record.published_at)
        if when > instant:
            continue
        key = (record.asset, record.session)
        previous = selected.get(key)
        if previous is None or _utc(previous.published_at) < when:
            selected[key] = record
        elif _utc(previous.published_at) == when and record != previous:
            raise PointInTimeError("contradictory versions with identical publication time")
    return selected


def empirical_joint_forecast(
    *,
    records: Sequence[PriceVintage],
    assets: Sequence[str],
    valuation_sessions: Sequence[date],
    as_of: datetime,
    valuation_session: date,
    forecast_method: str = "empirical",
) -> EmpiricalJointForecast:
    """Past-only joint monthly returns on declared month-end valuation sessions.

    Never forward-fills missing prices. If historical interval endpoints are
    incomplete, excludes the interval with an explicit count. The valuation
    session itself must have all assets, or estimation fails closed.
    """
    instant = _utc(as_of)
    if forecast_method not in ("empirical", "lagged_knn"):
        raise PointInTimeError("forecast_method must be empirical or lagged_knn")
    names = tuple(assets)
    if not names or len(names) != len(set(names)) or any(not x for x in names):
        raise PointInTimeError("unique nonempty assets required")
    sessions = tuple(valuation_sessions)
    if len(sessions) < 2 or any(
        (right.year * 12 + right.month) - (left.year * 12 + left.month) != 1
        for left, right in zip(sessions, sessions[1:])
    ):
        raise PointInTimeError(
            "consecutive monthly valuation endpoints required; daily/weekly returns cannot fund a monthly multistage model"
        )
    if valuation_session not in sessions or valuation_session > instant.date():
        raise PointInTimeError("valuation session unavailable on declared calendar")
    last = sessions.index(valuation_session)
    if last == 0:
        raise PointInTimeError("training requires completed past intervals")
    by_key = point_in_time_prices(records, as_of=instant)
    if any((a, valuation_session) not in by_key for a in names):
        raise PointInTimeError("current valuation missing a published asset price")
    included: list[tuple[Fraction, ...]] = []
    included_indices: list[int] = []
    used_sessions: list[str] = []
    digests: set[str] = set()
    excluded = 0
    for j in range(1, last + 1):
        older, newer = sessions[j - 1], sessions[j]
        pairs = [(by_key.get((a, older)), by_key.get((a, newer))) for a in names]
        if any(before is None or after is None for before, after in pairs):
            excluded += 1
            continue
        gross = tuple(_exact_price_ratio(after, before) for before, after in pairs)
        if not all(_finite_positive(float(g)) for g in gross):
            raise PointInTimeError("nonfinite joint return")
        included.append(gross)
        included_indices.append(j)
        used_sessions.append(newer.isoformat())
        for before, after in pairs:
            digests.add(before.raw_source_sha256)
            digests.add(after.raw_source_sha256)
    if not included:
        raise PointInTimeError("no complete observed one-month joint returns")
    selected = included
    standing = "PAST_ONLY_EMPIRICAL_JOINT_BASELINE_NOT_CALIBRATED"
    conditioning = None
    if forecast_method == "lagged_knn":
        # Training pairs (r_t, r_{t+1}) must be observed and consecutive.
        if included_indices[-1] != last:
            raise PointInTimeError("latest conditioning return not fully published")
        transitions = [
            (included[i], included[i + 1], used_sessions[i + 1])
            for i in range(len(included) - 1)
            if included_indices[i + 1] == included_indices[i] + 1
        ]
        if len(transitions) < 2:
            raise PointInTimeError("lagged_knn requires two complete lagged transitions")
        query = tuple(math.log(float(g)) for g in included[-1])
        ranked = sorted(
            (
                math.fsum((math.log(float(current[j])) - query[j]) ** 2 for j in range(len(query))),
                i,
            )
            for i, (current, _, _) in enumerate(transitions)
        )
        neighbors = math.isqrt(len(transitions))
        neighbors += neighbors * neighbors < len(transitions)
        chosen = ranked[:neighbors]
        selected = [transitions[i][1] for _, i in chosen]
        conditioning = {
            "method": "lagged_knn_log_joint_returns",
            "conditioning_session": used_sessions[-1],
            "eligible_historical_transitions": len(transitions),
            "neighbor_count": neighbors,
            "selected_outcome_sessions": [transitions[i][2] for _, i in chosen],
            "selection_standing": "SQRT_SAMPLE_HEURISTIC_NOT_CALIBRATED",
        }
        standing = "PAST_ONLY_LAGGED_KNN_JOINT_NOT_CALIBRATED"
    # Group duplicate exact joint realizations: consuming multistage policy
    # rejects duplicate indistinguishable children to prevent fake foresight.
    counts = Counter(selected)
    n = len(selected)
    scenarios = tuple(
        JointScenario(count / n, tuple(float(g) for g in vector), count)
        for vector, count in sorted(counts.items())
    )
    if not math.isclose(math.fsum(s.probability for s in scenarios), 1.0, abs_tol=1e-12):
        raise PointInTimeError("empirical probability mass is not normalized")
    return EmpiricalJointForecast(
        assets=names,
        as_of_utc=instant.isoformat(),
        valuation_session=valuation_session.isoformat(),
        training_return_count=len(included),
        excluded_incomplete_intervals=excluded,
        scenarios=scenarios,
        training_sessions=tuple(used_sessions),
        source_digests=tuple(sorted(digests)),
        standing=standing,
        conditioning=conditioning,
    )


def weighted_energy_score(
    *, forecasts: Sequence[JointScenario], realized_gross: Sequence[float]
) -> float:
    """Proper multivariate energy score, smaller is better.

    ES(F,y) = E||X-y|| - 1/2 E||X-X'||; this is a diagnostic
    for prequential evaluation, not a magic acceptance threshold.
    """
    outcome = tuple(realized_gross)
    if not outcome or any(not _finite_positive(x) for x in outcome):
        raise PointInTimeError("actual realized outcome must be positive and finite")
    if not forecasts or any(
        len(s.gross_returns) != len(outcome)
        or not math.isfinite(s.probability)
        or s.probability <= 0
        or any(not _finite_positive(x) for x in s.gross_returns)
        for s in forecasts
    ):
        raise PointInTimeError("valid full-dimensional probabilistic forecast required")
    if not math.isclose(math.fsum(s.probability for s in forecasts), 1.0, abs_tol=1e-12):
        raise PointInTimeError("forecast probability mass must sum to one")
    norm = lambda x, y: math.sqrt(math.fsum((a - b) ** 2 for a, b in zip(x, y, strict=True)))
    first = math.fsum(s.probability * norm(s.gross_returns, outcome) for s in forecasts)
    second = 0.5 * math.fsum(
        a.probability * b.probability * norm(a.gross_returns, b.gross_returns)
        for a in forecasts
        for b in forecasts
    )
    return max(0.0, first - second)


def weighted_variogram_score(
    *, forecasts: Sequence[JointScenario], realized_gross: Sequence[float]
) -> float:
    """Proper pairwise dependency score (p=1), not strictly proper alone."""
    outcome = tuple(realized_gross)
    if len(outcome) < 2 or any(not _finite_positive(x) for x in outcome):
        raise PointInTimeError("variogram requires two positive finite assets")
    if (
        not forecasts
        or any(
            len(f.gross_returns) != len(outcome)
            or not math.isfinite(f.probability)
            or f.probability <= 0
            or any(not _finite_positive(g) for g in f.gross_returns)
            for f in forecasts
        )
        or not math.isclose(math.fsum(f.probability for f in forecasts), 1.0, abs_tol=1e-12)
    ):
        raise PointInTimeError("valid normalized joint forecast required")
    return math.fsum(
        (
            abs(outcome[i] - outcome[j])
            - math.fsum(
                f.probability * abs(f.gross_returns[i] - f.gross_returns[j]) for f in forecasts
            )
        )
        ** 2
        for i in range(len(outcome))
        for j in range(i + 1, len(outcome))
    )


def prequential_energy_evaluation(
    *,
    records: Sequence[PriceVintage],
    assets: Sequence[str],
    valuation_sessions: Sequence[date],
    decision_instants: Mapping[date, datetime],
    evaluation_as_of: datetime,
    forecast_method: str = "empirical",
) -> tuple[dict[str, Any], ...]:
    """Score truly frozen past-only distributions after next prices are public.

    Each (valuation session, decision instant) is an explicit ex-ante
    commitment. Outcomes are evaluated later, never fed into the forecast.
    The forecast and its decision-time price remain strictly frozen at t.
    Realized gross returns are measured from BOTH endpoint prices selected
    as of evaluation_as_of, so post-decision split/dividend back-adjustments
    do not spuriously create a gain or loss by mixing price-normalization
    bases. Decision versus evaluation reference revisions are separately
    disclosed; authenticated corporate-action and total-return semantics
    still belong to Markets, not this retrospective research component.
    """
    evaluated_at = _utc(evaluation_as_of)
    calendar = tuple(valuation_sessions)
    if len(calendar) < 2 or any(
        (right.year * 12 + right.month) - (left.year * 12 + left.month) != 1
        for left, right in zip(calendar, calendar[1:])
    ):
        raise PointInTimeError("evaluation requires consecutive monthly valuation endpoints")
    results = []
    names = tuple(assets)
    final_market = point_in_time_prices(records, as_of=evaluated_at)
    for valuation_session, decision_at in sorted(decision_instants.items()):
        t = _utc(decision_at)
        if t >= evaluated_at:
            raise PointInTimeError("outcome evaluation must occur after decision")
        if valuation_session not in calendar:
            raise PointInTimeError("decision session absent from monthly valuation calendar")
        ix = calendar.index(valuation_session)
        if ix >= len(calendar) - 1:
            raise PointInTimeError("no next session defined for evaluation")
        next_session = calendar[ix + 1]
        distribution = empirical_joint_forecast(
            records=records,
            assets=names,
            valuation_sessions=calendar,
            as_of=t,
            valuation_session=valuation_session,
            forecast_method=forecast_method,
        )
        frozen_market = point_in_time_prices(records, as_of=t)
        realized = []
        reference_revision_evidence = []
        for asset in names:
            frozen_before = frozen_market.get((asset, valuation_session))
            evaluation_before = final_market.get((asset, valuation_session))
            evaluation_after = final_market.get((asset, next_session))
            if frozen_before is None or evaluation_before is None or evaluation_after is None:
                raise PointInTimeError("next-session market outcome not yet published")
            # Never divide a post-event adjusted close by a PRE-event vintage
            # adjusted close: corporate-action back-adjustments can generate
            # fake realized gains/losses across incompatible price bases.
            # Freeze the forecast at t; measure both realized endpoints from
            # the common evaluation-as-of snapshot, never from mixed clocks.
            realized.append(float(_exact_price_ratio(evaluation_after, evaluation_before)))
            reference_revision_evidence.append(
                {
                    "asset": asset,
                    "frozen_reference_close": frozen_before.adjusted_close,
                    "evaluation_reference_close": evaluation_before.adjusted_close,
                    "evaluation_outcome_close": evaluation_after.adjusted_close,
                    "reference_revision_factor": (
                        evaluation_before.adjusted_close / frozen_before.adjusted_close
                    ),
                    "reference_revised_since_decision": evaluation_before != frozen_before,
                    "frozen_reference_source_sha256": frozen_before.raw_source_sha256,
                    "evaluation_reference_source_sha256": evaluation_before.raw_source_sha256,
                    "evaluation_outcome_source_sha256": evaluation_after.raw_source_sha256,
                    "frozen_reference_source_standing": frozen_before.source_standing,
                    "evaluation_reference_source_standing": evaluation_before.source_standing,
                    "evaluation_outcome_source_standing": evaluation_after.source_standing,
                    "frozen_reference_published_at": _utc(frozen_before.published_at).isoformat(),
                    "evaluation_reference_published_at": _utc(
                        evaluation_before.published_at
                    ).isoformat(),
                    "evaluation_outcome_published_at": _utc(
                        evaluation_after.published_at
                    ).isoformat(),
                }
            )
        result = {
            "valuation_session": valuation_session.isoformat(),
            "decision_time": t.isoformat(),
            "evaluation_as_of": evaluated_at.isoformat(),
            "outcome_session": next_session.isoformat(),
            "realized_joint_gross": realized,
            "realized_price_basis": "EVALUATION_AS_OF_BOTH_ENDPOINTS_ADJUSTED",
            "reference_revision_evidence": reference_revision_evidence,
            "training_n": distribution.training_return_count,
            "forecast_method": forecast_method,
            "variogram_score": (
                weighted_variogram_score(forecasts=distribution.scenarios, realized_gross=realized)
                if len(names) > 1
                else None
            ),
            "energy_score": weighted_energy_score(
                forecasts=distribution.scenarios, realized_gross=realized
            ),
            "frozen_forecast_sha256": hashlib.sha256(
                json.dumps(distribution.to_dict(), sort_keys=True, separators=(",", ":")).encode()
            ).hexdigest(),
            "standing": "PREQUENTIAL_SCORE_ON_CALLER_SUPPLIED_VINTAGES",
        }
        results.append(result)
    return tuple(results)


def compare_pit_prequential_forecasts(
    *,
    records: Sequence[PriceVintage],
    assets: Sequence[str],
    valuation_sessions: Sequence[date],
    decision_instants: Mapping[date, datetime],
    evaluation_as_of: datetime,
    baseline_method: str = "empirical",
    candidate_method: str = "lagged_knn",
) -> dict[str, Any]:
    """Paired, same-clock, independent retrospective loss observations.

    Reuses the existing strict historical release-time cuts and proper energy
    score. The output is descriptive: a loss difference is NOT a Diebold-Mariano
    p-value, a Hansen-SPA correction, or evidence of economic alpha.

    Positive candidate-minus-baseline loss means worse candidate scoring.
    A historical experiment remains caller-supplied, not an externally
    authenticated precommitted prospective trial.
    """
    kwargs = dict(
        records=records,
        assets=assets,
        valuation_sessions=valuation_sessions,
        decision_instants=decision_instants,
        evaluation_as_of=evaluation_as_of,
    )
    reference = prequential_energy_evaluation(**kwargs, forecast_method=baseline_method)
    candidate = prequential_energy_evaluation(**kwargs, forecast_method=candidate_method)
    if not reference or len(reference) != len(candidate):
        raise PointInTimeError("paired evaluation requires common realized periods")
    pairs: list[dict[str, Any]] = []
    for before, after in zip(reference, candidate, strict=True):
        identity = (
            "valuation_session",
            "decision_time",
            "evaluation_as_of",
            "outcome_session",
            "realized_joint_gross",
            "realized_price_basis",
            "reference_revision_evidence",
        )
        if any(before[key] != after[key] for key in identity):
            raise PointInTimeError(
                "models must use identical ex-ante decision and realized outcome"
            )
        delta = after["energy_score"] - before["energy_score"]
        b_variogram, a_variogram = before["variogram_score"], after["variogram_score"]
        pairs.append(
            {
                "decision_time": before["decision_time"],
                "valuation_session": before["valuation_session"],
                "outcome_session": before["outcome_session"],
                "realized_joint_gross": before["realized_joint_gross"],
                "realized_price_basis": before["realized_price_basis"],
                "reference_revision_evidence": before["reference_revision_evidence"],
                "baseline_forecast_sha256": before["frozen_forecast_sha256"],
                "candidate_forecast_sha256": after["frozen_forecast_sha256"],
                "baseline_energy": before["energy_score"],
                "candidate_energy": after["energy_score"],
                "candidate_minus_baseline_energy": delta,
                "candidate_minus_baseline_variogram": (
                    None
                    if b_variogram is None or a_variogram is None
                    else a_variogram - b_variogram
                ),
            }
        )
    return {
        "standing": "PAIRED_PREQUENTIAL_DESCRIPTIVE_NO_SIGNIFICANCE_OR_ALPHA",
        "effectStanding": "READ_ONLY_NO_TRADE_NO_ACCOUNTING",
        "baselineMethod": baseline_method,
        "candidateMethod": candidate_method,
        "matchedEvaluationCount": len(pairs),
        "meanCandidateMinusBaselineEnergy": (
            math.fsum(row["candidate_minus_baseline_energy"] for row in pairs) / len(pairs)
        ),
        "perEvaluation": pairs,
        "limitations": [
            "Caller-supplied historical timestamps are not independently attested.",
            "Realized adjusted-price ratios use both endpoints at evaluation_as_of; Markets must attest their common corporate-action/total-return basis, never inferred executable fills.",
            "Descriptive energy loss differentials are not a serial-dependence-adjusted Diebold-Mariano inference or multiple-model SPA test.",
            "No optimal leverage, confidence level, statistical significance or prospective alpha is asserted.",
        ],
    }


def make_one_step_optimizer_contract(
    forecast: EmpiricalJointForecast,
    *,
    gamma: float,
    initial_margin: Sequence[float],
    turnover_cost: Sequence[float],
    scenario_maintenance: Sequence[Sequence[float]],
    cash_gross: float,
    debt_gross: float,
) -> dict[str, Any]:
    """Exact current multistage_policy JSON schema, without guessed inputs.

    This creates a one-step *research* information tree. Future model states,
    broker quotes and investor preferences must all be supplied by owners.
    """
    n = len(forecast.assets)
    margins, costs = tuple(initial_margin), tuple(turnover_cost)
    if (
        len(margins) != n
        or len(costs) != n
        or any(not math.isfinite(m) or not 0 < m <= 1 for m in margins)
        or any(not math.isfinite(k) or k < 0 for k in costs)
    ):
        raise PointInTimeError("provider initial margin and turnover terms required")
    if (
        not _finite_positive(gamma)
        or not _finite_positive(cash_gross)
        or not _finite_positive(debt_gross)
        or debt_gross < cash_gross
    ):
        raise PointInTimeError("finite caller risk preference and valid rates required")
    maintenance = tuple(tuple(row) for row in scenario_maintenance)
    if len(maintenance) != len(forecast.scenarios) or any(
        len(row) != n or any(not math.isfinite(m) or m < 0 or m > 1 for m in row)
        for row in maintenance
    ):
        raise PointInTimeError("scenario-by-asset broker maintenance matrix required")
    nodes = [
        {
            "id": "root",
            "parent": None,
            "t": 0,
            "conditional_probability": 1.0,
            "initial_margin": list(margins),
            "turnover_cost": list(costs),
            "risky_gross": [],
            "maintenance": [],
            "cash_gross": 1.0,
            "debt_gross": 1.0,
            "terminal": False,
        }
    ]
    for j, (scenario, m) in enumerate(zip(forecast.scenarios, maintenance, strict=True)):
        nodes.append(
            {
                "id": f"scenario_{j}",
                "parent": "root",
                "t": 1,
                "conditional_probability": scenario.probability,
                "risky_gross": list(scenario.gross_returns),
                "cash_gross": cash_gross,
                "debt_gross": debt_gross,
                "maintenance": list(m),
                "initial_margin": [],
                "turnover_cost": [],
                "terminal": True,
            }
        )
    return {"gamma": gamma, "nodes": nodes}


def from_json_payload(payload: Mapping[str, Any]) -> dict[str, Any]:
    """Produce a reproducible, zero-authority optimizer contract plus evidence."""
    expected = {
        "as_of",
        "valuation_session",
        "assets",
        "valuation_sessions",
        "prices",
        "economic_contract",
    }
    if set(payload) not in (expected, expected | {"forecast_method"}):
        raise PointInTimeError("expected exact data and economic-contract input fields")

    def record(raw: Mapping[str, Any]) -> PriceVintage:
        return PriceVintage(
            asset=raw["asset"],
            session=date.fromisoformat(raw["session"]),
            published_at=datetime.fromisoformat(raw["published_at"]),
            adjusted_close=float(raw["adjusted_close"]),
            raw_source_sha256=raw["raw_source_sha256"],
            source_standing=raw["source_standing"],
        )

    forecast = empirical_joint_forecast(
        records=[record(x) for x in payload["prices"]],
        assets=payload["assets"],
        valuation_sessions=[date.fromisoformat(s) for s in payload["valuation_sessions"]],
        as_of=datetime.fromisoformat(payload["as_of"]),
        valuation_session=date.fromisoformat(payload["valuation_session"]),
        forecast_method=payload.get("forecast_method", "empirical"),
    )
    econ = payload["economic_contract"]
    required = {"gamma", "initial_margin", "turnover_cost", "cash_gross", "debt_gross"}
    if set(econ) == required | {"scenario_maintenance"}:
        model_terms = dict(econ)
    elif set(econ) == required | {"maintenance_by_asset"}:
        # An explicit broker contract shared by all outcomes is a natural
        # shorthand, independent of the number of forecast scenarios.
        # Never infer this contract from historical returns or a default.
        model_terms = {key: econ[key] for key in required}
        model_terms["scenario_maintenance"] = [
            econ["maintenance_by_asset"] for _ in forecast.scenarios
        ]
    else:
        raise PointInTimeError(
            "economic contract requires explicit scenario_maintenance "
            "or maintenance_by_asset plus funding, costs and gamma"
        )
    tree = make_one_step_optimizer_contract(forecast, **model_terms)
    canonical = json.dumps(payload, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return {
        "standing": (
            "HISTORICAL_POINT_IN_TIME_EMPIRICAL_RESEARCH_ONLY"
            if payload.get("forecast_method", "empirical") == "empirical"
            else "HISTORICAL_POINT_IN_TIME_CONDITIONAL_RESEARCH_ONLY"
        ),
        "effects": "NONE_NO_TRADE_NO_ACCOUNTING",
        "optimizer_input": tree,
        "forecast_evidence": forecast.to_dict(),
        "input_sha256": hashlib.sha256(canonical.encode("utf-8")).hexdigest(),
        "limitations": [
            "Both empirical and lagged-neighbor distributions are uncalibrated research baselines, not independently validated conditional probabilities.",
            "Provider adjusted prices and release timestamps require independent authority verification.",
            "Monthly valuation after published close is not an executable same-close fill.",
            "No real broker liquidation or live account funding is implied.",
        ],
    }



def _solve_generated_research_tree(
    result: Mapping[str, Any], *, allocation_standing: str
) -> dict[str, Any]:
    """Consume the existing Portfolio solver with one shared typed tree adapter.

    Forecast provenance and optimizer inputs remain separately inspectable;
    this helper never modifies a brokerage account or an Accounting ledger.
    """
    import dataclasses

    from ordivon_capital.portfolio.multistage_policy import (
        InformationNode,
        MultistageProblem,
        solve_multistage,
    )

    contract = result["optimizer_input"]
    vectors = {"risky_gross", "maintenance", "initial_margin", "turnover_cost"}
    nodes = tuple(
        InformationNode(
            **{
                key: tuple(value) if key in vectors else value
                for key, value in raw.items()
            }
        )
        for raw in contract["nodes"]
    )
    solution = solve_multistage(
        MultistageProblem(
            gamma=contract["gamma"],
            nodes=nodes,
            terminal_liabilities_r=contract.get("terminal_liabilities_r"),
        )
    )
    return {
        **result,
        "conditional_allocation": dataclasses.asdict(solution),
        "allocation_standing": allocation_standing,
    }


def solve_pit_payload(payload: Mapping[str, Any]) -> dict[str, Any]:
    """Research-to-Portfolio native consumer, retaining the one-step API.

    Caller-supplied past-visible returns, utility, margin and financing terms
    are uncalibrated economic inputs, not verified market truth or trade consent.
    """
    return _solve_generated_research_tree(
        from_json_payload(payload),
        allocation_standing="CONDITIONAL_UNCALIBRATED_ONE_STEP_RESEARCH",
    )



def main() -> int:
    parser = argparse.ArgumentParser(
        description="Read-only PIT research to existing Capital optimizer"
    )
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--mode", choices=("one-step", "monthly-tree"), default="one-step")
    parser.add_argument(
        "--solve", action="store_true",
        help="solve the supplied conditional finite research tree with the native Portfolio optimizer",
    )
    args = parser.parse_args()
    try:
        payload = json.loads(args.input.read_text(encoding="utf-8"))
        if args.mode == "monthly-tree":
            from ordivon_capital.research.pit_monthly_paths import from_multiperiod_json_payload

            result = from_multiperiod_json_payload(payload)
            outcome = (
                _solve_generated_research_tree(
                    result,
                    allocation_standing=(
                        "STRUCTURAL_HISTORICAL_PATH_POLICY_NUMERIC_NOT_PREDICTIVE"
                    ),
                )
                if args.solve
                else result
            )
        elif args.solve:
            outcome = solve_pit_payload(payload)
        else:
            outcome = from_json_payload(payload)
    except (PointInTimeError, ValueError, TypeError, KeyError) as e:
        parser.error(f"incomplete point-in-time market/economic contract: {e}")
    print(json.dumps(outcome, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
