"""Historical PIT joint monthly path scenarios for the canonical Portfolio optimizer.

This is a research-only structural tree producer, not a calibrated forward
conditional law, an independent optimizer, a brokerage connector, or an
accounting system. Reuses the single PIT price vintage implementation.
"""

from __future__ import annotations

import hashlib
import json
import math
from collections import Counter
from collections.abc import Mapping, Sequence
from datetime import date, datetime
from typing import Any

from ordivon_capital.research.pit_joint_forecast import (
    PointInTimeError,
    PriceVintage,
    _exact_price_ratio,
    _finite_positive,
    _utc,
    point_in_time_prices,
)


def completed_monthly_sessions(
    trading_sessions: Sequence[date], *, as_of: datetime
) -> tuple[date, ...]:
    """Last *past* session of each completed month in source-owned calendar.

    Caller must provide its complete exchange calendar. A partial current
    calendar month is never silently treated as a finalized monthly return.
    """
    instant = _utc(as_of)
    sessions = tuple(trading_sessions)
    if not sessions or any(a >= b for a, b in zip(sessions, sessions[1:], strict=False)):
        raise PointInTimeError("strictly ordered exchange trading calendar required")
    out: dict[tuple[int, int], date] = {}
    for session in sessions:
        if (session.year, session.month) >= (instant.year, instant.month):
            continue
        out[(session.year, session.month)] = session
    return tuple(out[k] for k in sorted(out))


def historical_multiperiod_tree(
    *, records: Sequence[PriceVintage], assets: Sequence[str],
    trading_sessions: Sequence[date], as_of: datetime,
    horizon_months: int, gamma: float,
    initial_margin_by_stage: Sequence[Sequence[float]],
    turnover_cost_by_stage: Sequence[Sequence[float]],
    maintenance_by_stage: Sequence[Sequence[float]],
    cash_gross_by_stage: Sequence[float],
    debt_gross_by_stage: Sequence[float],
) -> dict[str, Any]:
    """Historical joint *monthly paths* as an input to existing multistage CRRA.

    Every overlapping historical H-month block is one equiprobable path.
    Equal observable prefixes are merged into information nodes; their
    empirical conditional branch frequencies are count(child)/count(parent).
    The caller must supply real stage-wise finance/broker constraints.

    This is a historical dependence-preserving *scenario tree baseline*, not
    an authenticated transition probability for future months. No temporal
    independence or hidden lookahead assumption is introduced.
    """
    instant = _utc(as_of)
    names = tuple(assets)
    if not names or len(names) != len(set(names)) or any(not a for a in names):
        raise PointInTimeError("unique assets required")
    if not isinstance(horizon_months, int) or isinstance(horizon_months, bool) or horizon_months < 1:
        raise PointInTimeError("positive integer month horizon required")
    if not _finite_positive(gamma):
        raise PointInTimeError("caller-supplied CRRA coefficient required")
    H, n = horizon_months, len(names)
    contracts = (initial_margin_by_stage, turnover_cost_by_stage, maintenance_by_stage)
    if any(len(rows) != H or any(len(v) != n for v in rows) for rows in contracts):
        raise PointInTimeError("complete stage-wise, asset-wise finance contracts required")
    if len(cash_gross_by_stage) != H or len(debt_gross_by_stage) != H:
        raise PointInTimeError("stage-wise financing contracts required")
    for stage in range(H):
        if any(not isinstance(v, (int, float)) or not math.isfinite(v) or not 0 < v <= 1
               for v in initial_margin_by_stage[stage]):
            raise PointInTimeError("valid initial broker margin required")
        if any(not isinstance(v, (int, float)) or not math.isfinite(v) or v < 0
               for v in turnover_cost_by_stage[stage]):
            raise PointInTimeError("valid cost schedule required")
        if any(not isinstance(v, (int, float)) or not math.isfinite(v) or not 0 <= v <= 1
               for v in maintenance_by_stage[stage]):
            raise PointInTimeError("valid maintenance schedule required")
        c, b = cash_gross_by_stage[stage], debt_gross_by_stage[stage]
        if not _finite_positive(c) or not _finite_positive(b) or b < c:
            raise PointInTimeError("cash and borrow gross returns required")
    months = completed_monthly_sessions(trading_sessions, as_of=instant)
    if len(months) <= H:
        raise PointInTimeError("insufficient completed monthly observations")
    prices = point_in_time_prices(records, as_of=instant)
    monthly: list[tuple[date, tuple[float, ...] | None]] = []
    source_digests: set[str] = set()
    for before, after in zip(months, months[1:], strict=False):
        cells = [(prices.get((asset, before)), prices.get((asset, after))) for asset in names]
        if any(a is None or b is None for a, b in cells):
            monthly.append((after, None))
            continue
        gross = tuple(_exact_price_ratio(b, a) for a, b in cells)
        if not all(x > 0 and math.isfinite(float(x)) for x in gross):
            raise PointInTimeError("invalid monthly joint gross returns")
        monthly.append((after, gross))
        for a, b in cells:
            source_digests.add(a.raw_source_sha256)
            source_digests.add(b.raw_source_sha256)
    if not monthly or monthly[-1][1] is None:
        raise PointInTimeError("latest completed monthly return unavailable")
    windows = []
    for j in range(len(monthly) - H + 1):
        segment = monthly[j:j + H]
        if all(v is not None for _, v in segment):
            windows.append(tuple(v for _, v in segment))
    if not windows:
        raise PointInTimeError("no historical H-month contiguous joint paths")

    path_counts = Counter(windows)
    prefix_counts: Counter[tuple[tuple[float, ...], ...]] = Counter()
    for path, count in path_counts.items():
        for k in range(1, H + 1):
            prefix_counts[path[:k]] += count
    total = len(windows)
    # Exact observed returns are not a validated predictive state variable.
    # With continuous returns a unique prefix can identify one historical
    # next period and create spurious perfect foresight in an in-sample tree.
    successor_sets: dict[tuple[tuple[float, ...], ...], set[tuple[float, ...]]] = {}
    for path in path_counts:
        for level in range(1, H):
            successor_sets.setdefault(path[:level], set()).add(path[level])
    degenerate_prefix_count = sum(len(v) == 1 for v in successor_sets.values())
    nodes: list[dict[str, Any]] = [
        {"id": "root", "parent": None, "t": 0, "conditional_probability": 1.0,
         "risky_gross": [], "maintenance": [], "cash_gross": 1.0, "debt_gross": 1.0,
         "initial_margin": list(initial_margin_by_stage[0]),
         "turnover_cost": list(turnover_cost_by_stage[0]), "terminal": False}
    ]
    ids: dict[tuple[tuple[float, ...], ...], str] = {(): "root"}
    # Sort prefixes by their *observed* history; no unrelated terminal
    # annotation can distinguish an earlier decision.
    for level in range(1, H + 1):
        prefixes = sorted(k for k in prefix_counts if len(k) == level)
        for index, prefix in enumerate(prefixes):
            parent = prefix[:-1]
            gross = prefix[-1]
            id_ = f"month_{level}_node_{index}"
            count = prefix_counts[prefix]
            denom = total if not parent else prefix_counts[parent]
            terminal = level == H
            nodes.append({
                "id": id_, "parent": ids[parent], "t": level,
                "conditional_probability": count / denom,
                "risky_gross": [float(v) for v in gross],
                "maintenance": list(maintenance_by_stage[level - 1]),
                "cash_gross": cash_gross_by_stage[level - 1],
                "debt_gross": debt_gross_by_stage[level - 1],
                "initial_margin": [] if terminal else list(initial_margin_by_stage[level]),
                "turnover_cost": [] if terminal else list(turnover_cost_by_stage[level]),
                "terminal": terminal,
            })
            ids[prefix] = id_
    return {
        "standing": "STRUCTURAL_HISTORICAL_PATH_TREE_NOT_PREDICTIVE_ADMISSIBLE",
        "effects": "NONE_NO_TRADE_NO_ACCOUNTING",
        "optimizer_input": {"gamma": gamma, "nodes": nodes},
        "forecast_evidence": {
            "as_of_utc": instant.isoformat(), "assets": list(names),
            "horizon_months": H, "completed_months": len(months),
            "path_count": total, "distinct_paths": len(path_counts),
            "tree_node_count": len(nodes),
            "post_observation_states": len(successor_sets),
            "single_successor_states": degenerate_prefix_count,
            "predictive_recursion": "NOT_IDENTIFIED_UNCALIBRATED_EXACT_HISTORY_PREFIXES",
            "excluded_incomplete_paths": len(monthly) - H + 1 - total,
            "source_digests": sorted(source_digests),
            "standing": "HISTORICAL_EMPIRICAL_NOT_PROSPECTIVE_VALIDATION",
        },
        "limitations": [
            "Full H-month historical windows preserve observed serial dependence, but do not identify future conditional transition laws.",
            "Unique exact-return prefixes can imply deterministic known continuations and severe in-sample policy foresight bias.",
            "Optimizer input is only a structural consumer fixture until a separately calibrated prospective state-transition model is supplied.",
        ],
    }


def from_multiperiod_json_payload(payload: Mapping[str, Any]) -> dict[str, Any]:
    """Strict JSON adapter: never create a caller-owned broker/utility value."""
    expected = {"as_of", "assets", "trading_sessions", "prices", "economic_contract", "horizon_months"}
    if set(payload) != expected:
        raise PointInTimeError("expected exact monthly market/economic fields")
    rows = [PriceVintage(
        asset=x["asset"], session=date.fromisoformat(x["session"]),
        published_at=datetime.fromisoformat(x["published_at"]),
        adjusted_close=float(x["adjusted_close"]),
        raw_source_sha256=x["raw_source_sha256"],
        source_standing=x["source_standing"],
    ) for x in payload["prices"]]
    economic = payload["economic_contract"]
    expected_econ = {"gamma", "initial_margin_by_stage", "turnover_cost_by_stage",
                     "maintenance_by_stage", "cash_gross_by_stage", "debt_gross_by_stage"}
    if set(economic) != expected_econ:
        raise PointInTimeError("missing or invented stage-wise economic inputs")
    result = historical_multiperiod_tree(
        records=rows, assets=payload["assets"],
        trading_sessions=[date.fromisoformat(d) for d in payload["trading_sessions"]],
        as_of=datetime.fromisoformat(payload["as_of"]),
        horizon_months=payload["horizon_months"], **economic,
    )
    canonical = json.dumps(payload, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    result["input_sha256"] = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    return result
