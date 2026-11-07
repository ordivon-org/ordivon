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
from dataclasses import dataclass
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence


class PointInTimeError(ValueError):
    """Invalid provenance, inaccessible future observation, or data contract."""


def _utc(instant: datetime) -> datetime:
    if instant.tzinfo is None or instant.utcoffset() is None:
        raise PointInTimeError("information time must include UTC offset")
    return instant.astimezone(timezone.utc)


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

    def to_dict(self) -> dict[str, Any]:
        return {
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
) -> EmpiricalJointForecast:
    """Past-only joint monthly returns on declared month-end valuation sessions.

    Never forward-fills missing prices. If historical interval endpoints are
    incomplete, excludes the interval with an explicit count. The valuation
    session itself must have all assets, or estimation fails closed.
    """
    instant = _utc(as_of)
    names = tuple(assets)
    if not names or len(names) != len(set(names)) or any(not x for x in names):
        raise PointInTimeError("unique nonempty assets required")
    sessions = tuple(valuation_sessions)
    if len(sessions) < 2 or any(
        (right.year * 12 + right.month) - (left.year * 12 + left.month) != 1
        for left, right in zip(sessions, sessions[1:])
    ):
        raise PointInTimeError("consecutive monthly valuation endpoints required; daily/weekly returns cannot fund a monthly multistage model")
    if valuation_session not in sessions or valuation_session > instant.date():
        raise PointInTimeError("valuation session unavailable on declared calendar")
    last = sessions.index(valuation_session)
    if last == 0:
        raise PointInTimeError("training requires completed past intervals")
    by_key = point_in_time_prices(records, as_of=instant)
    if any((a, valuation_session) not in by_key for a in names):
        raise PointInTimeError("current valuation missing a published asset price")
    included: list[tuple[float, ...]] = []
    used_sessions: list[str] = []
    digests: set[str] = set()
    excluded = 0
    for j in range(1, last + 1):
        older, newer = sessions[j - 1], sessions[j]
        pairs = [(by_key.get((a, older)), by_key.get((a, newer))) for a in names]
        if any(before is None or after is None for before, after in pairs):
            excluded += 1
            continue
        gross = tuple(
            after.adjusted_close / before.adjusted_close
            for before, after in pairs
        )
        if not all(_finite_positive(g) for g in gross):
            raise PointInTimeError("nonfinite joint return")
        included.append(gross)
        used_sessions.append(newer.isoformat())
        for before, after in pairs:
            digests.add(before.raw_source_sha256)
            digests.add(after.raw_source_sha256)
    if not included:
        raise PointInTimeError("no complete observed one-month joint returns")
    # Group duplicate exact joint realizations: consuming multistage policy
    # rejects duplicate indistinguishable children to prevent fake foresight.
    counts = Counter(included)
    n = len(included)
    scenarios = tuple(
        JointScenario(count / n, vector, count)
        for vector, count in sorted(counts.items())
    )
    if not math.isclose(math.fsum(s.probability for s in scenarios), 1.0, abs_tol=1e-12):
        raise PointInTimeError("empirical probability mass is not normalized")
    return EmpiricalJointForecast(
        assets=names,
        as_of_utc=instant.isoformat(),
        valuation_session=valuation_session.isoformat(),
        training_return_count=n,
        excluded_incomplete_intervals=excluded,
        scenarios=scenarios,
        training_sessions=tuple(used_sessions),
        source_digests=tuple(sorted(digests)),
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
        or not math.isfinite(s.probability) or s.probability <= 0
        or any(not _finite_positive(x) for x in s.gross_returns)
        for s in forecasts
    ):
        raise PointInTimeError("valid full-dimensional probabilistic forecast required")
    if not math.isclose(math.fsum(s.probability for s in forecasts), 1.0, abs_tol=1e-12):
        raise PointInTimeError("forecast probability mass must sum to one")
    norm = lambda x, y: math.sqrt(math.fsum((a - b)**2 for a, b in zip(x, y, strict=True)))
    first = math.fsum(s.probability * norm(s.gross_returns, outcome) for s in forecasts)
    second = .5 * math.fsum(
        a.probability * b.probability * norm(a.gross_returns, b.gross_returns)
        for a in forecasts for b in forecasts
    )
    return max(0.0, first - second)



def prequential_energy_evaluation(
    *, records: Sequence[PriceVintage], assets: Sequence[str],
    valuation_sessions: Sequence[date],
    decision_instants: Mapping[date, datetime],
    evaluation_as_of: datetime,
) -> tuple[dict[str, Any], ...]:
    """Score truly frozen past-only distributions after next prices are public.

    Each (valuation session, decision instant) is an explicit ex-ante
    commitment. Outcomes are evaluated later, never fed into the forecast.
    The period gross is measured from the then-known valuation close to
    the subsequently available outcome close; adjusted-price revisions
    must be disclosed separately for exact total-return attribution.
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
        if ix >= len(calendar)-1:
            raise PointInTimeError("no next session defined for evaluation")
        next_session = calendar[ix+1]
        distribution = empirical_joint_forecast(
            records=records, assets=names, valuation_sessions=calendar,
            as_of=t, valuation_session=valuation_session,
        )
        frozen_market = point_in_time_prices(records, as_of=t)
        realized = []
        for asset in names:
            before = frozen_market.get((asset, valuation_session))
            after = final_market.get((asset, next_session))
            if before is None or after is None:
                raise PointInTimeError("next-session market outcome not yet published")
            realized.append(after.adjusted_close / before.adjusted_close)
        result = {
            "valuation_session": valuation_session.isoformat(),
            "decision_time": t.isoformat(),
            "evaluation_as_of": evaluated_at.isoformat(),
            "outcome_session": next_session.isoformat(),
            "realized_joint_gross": realized,
            "training_n": distribution.training_return_count,
            "energy_score": weighted_energy_score(
                forecasts=distribution.scenarios, realized_gross=realized
            ),
            "frozen_forecast_sha256": hashlib.sha256(json.dumps(
                distribution.to_dict(), sort_keys=True, separators=(",", ":")
            ).encode()).hexdigest(),
            "standing": "PREQUENTIAL_SCORE_ON_CALLER_SUPPLIED_VINTAGES",
        }
        results.append(result)
    return tuple(results)

def make_one_step_optimizer_contract(
    forecast: EmpiricalJointForecast, *, gamma: float,
    initial_margin: Sequence[float], turnover_cost: Sequence[float],
    scenario_maintenance: Sequence[Sequence[float]],
    cash_gross: float, debt_gross: float,
) -> dict[str, Any]:
    """Exact current multistage_policy JSON schema, without guessed inputs.

    This creates a one-step *research* information tree. Future model states,
    broker quotes and investor preferences must all be supplied by owners.
    """
    n = len(forecast.assets)
    margins, costs = tuple(initial_margin), tuple(turnover_cost)
    if (len(margins) != n or len(costs) != n or
        any(not math.isfinite(m) or not 0 < m <= 1 for m in margins) or
        any(not math.isfinite(k) or k < 0 for k in costs)):
        raise PointInTimeError("provider initial margin and turnover terms required")
    if not _finite_positive(gamma) or not _finite_positive(cash_gross) or not _finite_positive(debt_gross) or debt_gross < cash_gross:
        raise PointInTimeError("finite caller risk preference and valid rates required")
    maintenance = tuple(tuple(row) for row in scenario_maintenance)
    if len(maintenance) != len(forecast.scenarios) or any(
        len(row) != n or any(not math.isfinite(m) or m < 0 or m > 1 for m in row)
        for row in maintenance
    ):
        raise PointInTimeError("scenario-by-asset broker maintenance matrix required")
    nodes = [{
        "id": "root", "parent": None, "t": 0,
        "conditional_probability": 1.0,
        "initial_margin": list(margins), "turnover_cost": list(costs),
        "risky_gross": [], "maintenance": [],
        "cash_gross": 1.0, "debt_gross": 1.0,
        "terminal": False,
    }]
    for j, (scenario, m) in enumerate(zip(forecast.scenarios, maintenance, strict=True)):
        nodes.append({
            "id": f"scenario_{j}", "parent": "root", "t": 1,
            "conditional_probability": scenario.probability,
            "risky_gross": list(scenario.gross_returns),
            "cash_gross": cash_gross, "debt_gross": debt_gross,
            "maintenance": list(m), "initial_margin": [], "turnover_cost": [],
            "terminal": True,
        })
    return {"gamma": gamma, "nodes": nodes}


def from_json_payload(payload: Mapping[str, Any]) -> dict[str, Any]:
    """Produce a reproducible, zero-authority optimizer contract plus evidence."""
    expected = {"as_of", "valuation_session", "assets", "valuation_sessions", "prices", "economic_contract"}
    if set(payload) != expected:
        raise PointInTimeError("expected exact data and economic-contract input fields")
    def record(raw: Mapping[str, Any]) -> PriceVintage:
        return PriceVintage(
            asset=raw["asset"], session=date.fromisoformat(raw["session"]),
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
    )
    econ = payload["economic_contract"]
    if set(econ) != {"gamma", "initial_margin", "turnover_cost", "scenario_maintenance", "cash_gross", "debt_gross"}:
        raise PointInTimeError("economic contract requires exact explicit fields")
    tree = make_one_step_optimizer_contract(forecast, **econ)
    canonical = json.dumps(payload, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return {
        "standing": "HISTORICAL_POINT_IN_TIME_EMPIRICAL_RESEARCH_ONLY",
        "effects": "NONE_NO_TRADE_NO_ACCOUNTING",
        "optimizer_input": tree,
        "forecast_evidence": forecast.to_dict(),
        "input_sha256": hashlib.sha256(canonical.encode("utf-8")).hexdigest(),
        "limitations": [
            "Empirical joint distribution is an uncalibrated predictive baseline, not validated conditional probabilities.",
            "Provider adjusted prices and release timestamps require independent authority verification.",
            "Monthly valuation after published close is not an executable same-close fill.",
            "No real broker liquidation or live account funding is implied.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Read-only PIT research to existing Capital optimizer")
    parser.add_argument("--input", type=Path, required=True)
    args = parser.parse_args()
    try:
        outcome = from_json_payload(json.loads(args.input.read_text(encoding="utf-8")))
    except (PointInTimeError, ValueError, TypeError, KeyError) as e:
        parser.error(f"incomplete point-in-time market/economic contract: {e}")
    print(json.dumps(outcome, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
